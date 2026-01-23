# ===============================
# webhook_server.py
# WATI Webhook Receiver (SAFE VERSION)
# ===============================

from flask import Flask, request, jsonify
import datetime
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
        # Detect message
        # ===============================
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
            message_type = "text"
            message_text = data.get("text")

        # ===============================
        # Save incoming message
        # ===============================
        supa = SPS.db()

        insert_data = {
            "whatsapp_number": whatsapp_number,
            "message_type": message_type,
            "message_text": message_text,
            "selected_payload": selected_payload,
            "record_type": "user",
            "sent": False,
            "source": "wati",
            "received_at": datetime.datetime.utcnow().isoformat()
        }

        print("📝 INSERT DATA ↓↓↓")
        print(insert_data)

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
