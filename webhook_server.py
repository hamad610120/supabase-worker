# ===============================
# webhook_server.py
# WATI Webhook Receiver (REFACTORED - RECEIVE ONLY)
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
        # Detect message type
        # ===============================
        message_type = "text"
        message_text = None
        selected_list_id = None

        # 🔘 Button reply (treated as list)
        if data.get("buttonReply"):
            message_type = "list"
            selected_list_id = data["buttonReply"].get("payload")

        # 📋 List reply
        elif data.get("listReply"):
            message_type = "list"
            selected_list_id = data["listReply"].get("id")

        # 📝 Plain text
        else:
            message_type = "text"
            message_text = data.get("text")

        # ===============================
        # Effective list id logic
        # ===============================
        if message_type == "list" and selected_list_id:
            effective_list_id = selected_list_id
        else:
            effective_list_id = "TEXT_ANY"

        # ===============================
        # Save incoming message
        # ===============================
        supa = SPS.db()

        supa.table("incoming_messages").insert({
            "whatsapp_number": whatsapp_number,
            "message_type": message_type,          # text | list
            "message_text": message_text,          # only if text
            "selected_option": selected_list_id,   # only if list
            "effective_list_id": effective_list_id,
            "record_type": "user",
            "sent": False,
            "source": "wati",
            "received_at": datetime.datetime.now(datetime.UTC).isoformat()
        }).execute()

        print(
            f"✅ RECEIVED | from={whatsapp_number} "
            f"| type={message_type} "
            f"| effective_list_id={effective_list_id}"
        )

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return jsonify({"status": "error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
