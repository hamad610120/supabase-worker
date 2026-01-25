# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL LOCKED)
# ===============================

from flask import Flask, request, jsonify
from datetime import datetime, timezone
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

        whatsapp_number = data.get("waId")
        if not whatsapp_number:
            return jsonify({"status": "ignored"}), 200

        # ===============================
        # Detect message type
        # ===============================
        message_type = None
        message_text = None
        selected_payload = None

        # Button reply (treated as list)
        if data.get("buttonReply"):
            message_type = "list"
            selected_payload = data["buttonReply"].get("payload")

        # List reply
        elif data.get("listReply"):
            message_type = "list"
            selected_payload = data["listReply"].get("id")

        # Plain text
        else:
            message_type = "text"
            message_text = data.get("text")

        # ===============================
        # Prepare insert data (STRICT)
        # ===============================
        insert_data = {
            "whatsapp_number": whatsapp_number,
            "message_type": message_type,      # text | list
            "message_text": message_text,      # only if text
            "selected_payload": selected_payload,  # only if list
            "processed": False,
            "sent": False,
            "source": "wati",
            "received_at": datetime.now(timezone.utc).isoformat()
        }

        print("📝 INSERT DATA ↓↓↓")
        print(insert_data)

        # ===============================
        # Insert into incoming_messages
        # ===============================
        supa = SPS.db()
        supa.table("incoming_messages").insert(insert_data).execute()

        print(
            f"✅ SAVED | from={whatsapp_number} "
            f"| type={message_type} "
            f"| payload={selected_payload}"
        )

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:")
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
