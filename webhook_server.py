# ======================================================
# webhook_server.py
# WATI Receiver + Sender (SIMPLE & FINAL)
# ======================================================

from flask import Flask, request, jsonify
from datetime import datetime, timezone
import requests
import SPS  # Supabase connection

app = Flask(__name__)

# ======================================================
# Supabase
# ======================================================
def supa():
    return SPS.db()

# ======================================================
# Health
# ======================================================
@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200

# ======================================================
# Settings
# ======================================================
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

# ======================================================
# Mark processed
# ======================================================
def mark_processed(msg_id, note, sent=True):
    supa().table("incoming_messages").update({
        "processed": True,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "source": note,
        "sent": sent
    }).eq("id", msg_id).execute()

# ======================================================
# WATI Senders (FIXED)
# ======================================================
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

    url = f"{base}/{tenant}/api/v1/sendInteractiveListMessage"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    payload = {
        "body": title,
        "buttonText": button,
        "sections": [
            {
                "title": title,
                "rows": rows
            }
        ]
    }

    requests.post(
        url,
        headers=headers,
        params={"whatsappNumber": phone},
        json=payload,
        timeout=15
    )

# ======================================================
# DATA – INVOICES
# ======================================================
def get_invoices_list(phone, limit=20):
    res = (
        supa()
        .table("z_bill_credit_summary")
        .select("bill_no,bill_ser,bill_total,currency")
        .eq("customer_code",
            supa()
            .table("Z_CUSTOMER_ORDER_DETAILS")
            .select("customer_code")
            .eq("customer_phone", phone)
            .limit(1)
            .execute()
            .data[0]["customer_code"]
        )
        .order("bill_no", desc=True)
        .limit(limit)
        .execute()
    )

    rows = res.data or []
    return [
        {
            "id": f"inv_{r['bill_no']}_{r['bill_ser']}",
            "title": f"فاتورة {r['bill_no']}",
            "description": f"{r['bill_total']} {r['currency']}"
        }
        for r in rows
    ]

def get_invoice_text(bill_no, bill_ser):
    res = (
        supa()
        .table("z_bill_credit_summary")
        .select("bill_no,bill_type,bill_statement,bill_total,currency")
        .eq("bill_no", bill_no)
        .eq("bill_ser", bill_ser)
        .limit(1)
        .execute()
    )

    if not res.data:
        return "❌ الفاتورة غير موجودة"

    r = res.data[0]
    return (
        f"🧾 فاتورة رقم: {r['bill_no']}\n"
        f"النوع: {r['bill_type']}\n"
        f"البيان: {r['bill_statement']}\n"
        f"الإجمالي: {r['bill_total']} {r['currency']}"
    )

# ======================================================
# DATA – ORDERS
# ======================================================
def get_orders_list(phone, limit=20):
    res = (
        supa()
        .table("Z_CUSTOMER_ORDER_DETAILS")
        .select("order_no,order_total")
        .eq("customer_phone", phone)
        .order("order_no", desc=True)
        .limit(limit)
        .execute()
    )

    seen = set()
    rows = []
    for r in res.data or []:
        if r["order_no"] in seen:
            continue
        seen.add(r["order_no"])
        rows.append({
            "id": f"order_{r['order_no']}",
            "title": f"طلب {r['order_no']}",
            "description": f"{r['order_total']}"
        })
    return rows

def get_order_text(order_no):
    res = (
        supa()
        .table("Z_CUSTOMER_ORDER_DETAILS")
        .select("item_name,qty,unit_price,line_total")
        .eq("order_no", order_no)
        .execute()
    )

    if not res.data:
        return "❌ الطلب غير موجود"

    lines = [f"📦 تفاصيل الطلب رقم {order_no}", "-" * 20]
    total = 0
    for r in res.data:
        lines.append(
            f"{r['item_name']} × {r['qty']} = {r['line_total']}"
        )
        total += float(r["line_total"])

    lines.append("-" * 20)
    lines.append(f"الإجمالي: {total}")
    return "\n".join(lines)

# ======================================================
# WEBHOOK – FINAL LOGIC
# ======================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}
    wa = data.get("waId")
    if not wa:
        return jsonify({"status": "ignored"}), 200

    selected = None
    if data.get("listReply"):
        selected = data["listReply"]["id"]

    # save message
    res = supa().table("incoming_messages").insert({
        "whatsapp_number": wa,
        "message_type": "list" if selected else "text",
        "selected_payload": selected,
        "record_type": "user",
        "sent": False,
        "source": "wati",
        "received_at": datetime.now(timezone.utc).isoformat()
    }).execute()
    msg_id = res.data[0]["id"]

    # ================= TEXT → ROOT MENU =================
    if not selected:
        send_list(
            wa,
            "اختر الخدمة المطلوبة:",
            "الخدمات",
            [
                {"id": "service_invoices", "title": "🧾 فواتيري"},
                {"id": "service_orders", "title": "📦 طلباتي"},
                {"id": "service_account", "title": "💳 حسابي"}
            ]
        )
        mark_processed(msg_id, "ROOT_MENU")
        return jsonify({"status": "ok"}), 200

    # ================= INVOICES =================
    if selected == "service_invoices":
        rows = get_invoices_list(wa)
        send_list(wa, "🧾 فواتيري", "اختر فاتورة", rows)
        mark_processed(msg_id, "INVOICES_LIST")
        return jsonify({"status": "ok"}), 200

    if selected.startswith("inv_"):
        _, bill_no, bill_ser = selected.split("_", 2)
        send_text(wa, get_invoice_text(bill_no, bill_ser))
        mark_processed(msg_id, "INVOICE_DETAILS")
        return jsonify({"status": "ok"}), 200

    # ================= ORDERS =================
    if selected == "service_orders":
        rows = get_orders_list(wa)
        send_list(wa, "📦 طلباتي", "اختر طلب", rows)
        mark_processed(msg_id, "ORDERS_LIST")
        return jsonify({"status": "ok"}), 200

    if selected.startswith("order_"):
        order_no = selected.replace("order_", "")
        send_text(wa, get_order_text(order_no))
        mark_processed(msg_id, "ORDER_DETAILS")
        return jsonify({"status": "ok"}), 200

    # ================= ACCOUNT =================
    if selected == "service_account":
        send_text(wa, "💳 كشف الحساب سيتم تفعيله لاحقًا")
        mark_processed(msg_id, "ACCOUNT")
        return jsonify({"status": "ok"}), 200

    send_text(wa, "⚠️ خيار غير معروف")
    mark_processed(msg_id, "UNKNOWN", sent=False)
    return jsonify({"status": "ok"}), 200

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
