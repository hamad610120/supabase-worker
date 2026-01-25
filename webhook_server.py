# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL LOCKED – TABLE COMPATIBLE)
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
        # Prepare insert data (MATCH TABLE)
        # ===============================
        insert_data = {
            "whatsapp_number": str(whatsapp_number),
            "message_type": message_type,              # text | list
            "message_text": message_text,              # only if text
            "selected_payload": selected_payload,      # only if list

            # REQUIRED BY TABLE
            "effective_list_id": selected_payload if message_type == "list" else "TEXT_ANY",
            "record_type": "user",

            # DEFAULT FLAGS
            "source": "wati",
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
