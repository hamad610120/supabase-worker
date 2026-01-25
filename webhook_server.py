# ===============================
# webhook_server.py
# WATI Webhook Receiver – PAYLOAD BASED (FINAL)
# ===============================

from flask import Flask, request, jsonify
from datetime import datetime, timezone
import traceback
import SPS  # Supabase connection

app = Flask(__name__)


@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200


@app.route("/webhook", methods=["POST"])
def receive_webhook():
    try:
        data = request.json or {}

        print("📦 RAW PAYLOAD ↓↓↓")
        print(data)

        # ===============================
        # Get WhatsApp number (safe)
        # ===============================
        whatsapp_number = (
            data.get("waId")
            or data.get("wa_id")
            or data.get("whatsapp_number")
        )

        if not whatsapp_number:
            print("⚠️ NO WHATSAPP NUMBER FOUND")
            return jsonify({"status": "ignored"}), 200

        # ===============================
        # Detect message type
        # ===============================
        message_type = "text"
        message_text = None
        selected_payload = None

        # Button reply → list
        if data.get("buttonReply"):
            message_type = "list"
            selected_payload = data["buttonReply"].get("payload")

        # List reply → list
        elif data.get("listReply"):
            message_type = "list"
            selected_payload = data["listReply"].get("id")

        # Plain text
        else:
            message_text = data.get("text")

        # ===============================
        # Resolve command_key (VERY IMPORTANT)
        # ===============================
        command_key = "MAIN_MENU"

        # إذا جاء payload → تفاصيل فاتورة
        if message_type == "list" and selected_payload:
            command_key = "INVOICE_DETAILS"

        # إذا نص
        elif message_type == "text" and message_text:
            txt = message_text.strip()

            if txt in ["فواتيري", "فواتير", "فواتيرى"]:
                command_key = "INVOICES"
            else:
                command_key = "MAIN_MENU"

        # ===============================
        # Prepare insert data
        # ===============================
        insert_data = {
            "whatsapp_number": str(whatsapp_number),
            "message_type": message_type,
            "message_text": message_text,
            "selected_payload": selected_payload,

            # REQUIRED BY TABLE
            "effective_list_id": selected_payload if message_type == "list" else "TEXT_ANY",
            "record_type": "user",

            # 🔑 KEY PART
            "source": command_key,

            # FLAGS
            "sent": False,
            "processed": False,
            "received_at": datetime.now(timezone.utc).isoformat()
        }

        print("📝 INSERT DATA ↓↓↓")
        print(insert_data)

        # ===============================
        # Insert into incoming_messages
        # ===============================
        supa = SPS.db()
        res = supa.table("incoming_messages").insert(insert_data).execute()

        print("✅ INSERT RESULT ↓↓↓")
        print(res)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR FULL TRACE:")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
