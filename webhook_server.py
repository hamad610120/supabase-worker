# ===============================
# webhook_server.py
# WATI Receiver + Sender (FINAL FIXED)
# ===============================

from flask import Flask, request, jsonify
from datetime import datetime, timezone
import requests
import SPS  # Supabase connection

app = Flask(__name__)

# ===============================
# Supabase
# ===============================
def supa():
    return SPS.db()

# ===============================
# Health
# ===============================
@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200

# ===============================
# Settings
# ===============================
def get_setting(key):
    res = (
        supa()
        .table("system_settings")
        .select("value")
        .eq("key", key)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise Exception(f"Missing system setting: {key}")
    return res.data[0]["value"]

# ===============================
# Mark processed
# ===============================
def mark_processed(msg_id, note, sent=True):
    supa().table("incoming_messages").update({
        "processed": True,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "source": note,
        "sent": sent
    }).eq("id", msg_id).execute()

# ===============================
# WATI Senders
# ===============================
def send_text(phone, text):
    base = get_setting("wati_api_base_url")
    tenant = get_setting("wati_tenant_id")
    token = get_setting("wati_api_token")

    url = f"{base}/{tenant}/api/v1/sendSessionMessage/{phone}"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    params = {"messageText": text}

    requests.post(url, headers=headers, params=params, timeout=15)

def send_list(phone, title, button, rows):
    base = get_setting("wati_api_base_url")
    tenant = get_setting("wati_tenant_id")
    token = get_setting("wati_api_token")
    endpoint = get_setting("wati_send_endpoint")

    url = f"{base}/{tenant}{endpoint}"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    payload = {
        "whatsappNumber": phone,
        "body": title,
        "buttonText": button,
        "sections": [
            {
                "title": title,
                "rows": rows
            }
        ]
    }

    requests.post(url, headers=headers, json=payload, timeout=15)

# ===============================
# Resolver
# ===============================
def resolve_effective_list_id(message_type, text, payload):
    if message_type == "list" and payload:
        return payload
    return "TEXT_ANY"

# ===============================
# Menu Map Resolver
# ===============================
def get_action(effective_list_id, message_type):
    res = (
        supa()
        .table("whatsapp_menu_map")
        .select("*")
        .eq("is_active", True)
        .eq("input_type", message_type)
        .or_(f"list_id.eq.{effective_list_id},list_id.like.order_*")
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None

# ===============================
# Data Providers (Invoices)
# ===============================
def get_invoices_list(phone, limit=20):
    res = (
        supa()
        .table("z_bill_credit_details")
        .select("bill_no,bill_ser,bill_type,bill_total,currency")
        .eq("customer_phone", phone)
        .order("bill_no", desc=True)
        .limit(limit)
        .execute()
    )

    rows = res.data or []
    seen = set()
    result = []

    for r in rows:
        key = f"{r['bill_no']}_{r['bill_ser']}"
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "id": f"inv_{r['bill_no']}_{r['bill_ser']}",
            "title": f"فاتورة #{r['bill_no']} ({r['bill_type']})",
            "description": f"{r['bill_total']} {r['currency']}"
        })

    return result

def get_invoice_details(phone, bill_no, bill_ser):
    res = (
        supa()
        .table("z_bill_credit_details")
        .select("item_name,item_qty,item_total,bill_total,currency")
        .eq("bill_no", bill_no)
        .eq("bill_ser", bill_ser)
        .eq("customer_phone", phone)
        .execute()
    )

    rows = res.data or []
    if not rows:
        return None

    lines = [
        "🧾 *تفاصيل الفاتورة*",
        f"رقم الفاتورة: {bill_no}",
        f"السيريال: {bill_ser}",
        "------------------"
    ]

    for r in rows:
        lines.append(
            f"- {r['item_name']} × {r['item_qty']} = {r['item_total']} {r['currency']}"
        )

    lines.append(
        f"\n*الإجمالي:* {rows[0]['bill_total']} {rows[0]['currency']}"
    )

    return "\n".join(lines)

# ===============================
# Execution Engine (FIXED)
# ===============================
def execute_action(action, phone, msg_id, effective_list_id):
    action_type = action["action_type"]
    response = action["response_format"]
    entity = action["entity_type"]
    query = action["query_key"]

    # ---------- SEND LIST ----------
    if action_type == "send_list" and response == "list":

        # Root services
        if query == "services_root":
            send_list(
                phone,
                "اختر الخدمة المطلوبة:",
                "قائمة الخدمات",
                [
                    {"id": "service_orders", "title": "📦 طلباتي"},
                    {"id": "service_invoices", "title": "🧾 فواتيري"},
                    {"id": "service_account", "title": "💳 كشف حسابي"}
                ]
            )
            mark_processed(msg_id, "ROOT_MENU_SENT")
            return

        # Invoices list
        if entity == "invoices" and query == "last_invoices_by_phone":
            rows = get_invoices_list(phone, action.get("limit_count") or 20)
            if not rows:
                send_text(phone, action["error_message"])
                mark_processed(msg_id, "NO_INVOICES", sent=False)
                return

            send_list(phone, "🧾 فواتيرك", "اختر الفاتورة", rows)
            mark_processed(msg_id, "INVOICES_LIST_SENT")
            return

    # ---------- EXECUTE ----------
    if action_type == "execute":

        # Invoice details
        if entity == "invoices" and effective_list_id.startswith("inv_"):
            try:
                _, bill_no, bill_ser = effective_list_id.split("_", 2)
            except Exception:
                send_text(phone, "❌ اختيار غير صحيح")
                mark_processed(msg_id, "INVALID_INVOICE", sent=False)
                return

            text = get_invoice_details(phone, bill_no, bill_ser)
            if not text:
                send_text(phone, action["error_message"])
                mark_processed(msg_id, "NO_INVOICE_DETAILS", sent=False)
                return

            send_text(phone, text)
            mark_processed(msg_id, "INVOICE_DETAILS_SENT")
            return

        # Default execute
        send_text(phone, action.get("success_message") or "✅ تم التنفيذ")
        mark_processed(msg_id, "EXECUTED")
        return

    # ---------- FALLBACK ----------
    send_text(phone, "⚠️ الخدمة غير متاحة")
    mark_processed(msg_id, "NO_ACTION", sent=False)

# ===============================
# Webhook
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json or {}
        wa = data.get("waId")
        if not wa:
            return jsonify({"status": "ignored"}), 200

        message_type = "text"
        message_text = None
        selected_payload = None

        if data.get("buttonReply"):
            message_type = "list"
            selected_payload = data["buttonReply"].get("payload")

        elif data.get("listReply"):
            message_type = "list"
            selected_payload = data["listReply"].get("id")

        else:
            message_text = data.get("text")

        effective_list_id = resolve_effective_list_id(
            message_type, message_text, selected_payload
        )

        res = supa().table("incoming_messages").insert({
            "whatsapp_number": wa,
            "message_type": message_type,
            "message_text": message_text,
            "selected_payload": selected_payload,
            "effective_list_id": effective_list_id,
            "record_type": "user",
            "sent": False,
            "source": "wati",
            "received_at": datetime.now(timezone.utc).isoformat()
        }).execute()

        msg_id = res.data[0]["id"]

        action = get_action(effective_list_id, message_type)
        if not action:
            send_text(wa, "اختر الخدمة المطلوبة:")
            mark_processed(msg_id, "NO_MATCH", sent=False)
            return jsonify({"status": "ok"}), 200

        execute_action(action, wa, msg_id, effective_list_id)
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# ===============================
# Run
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
