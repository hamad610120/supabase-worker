# ===============================
# webhook_server.py
# FINAL – LOCKED FOREVER
# ===============================

from flask import Flask, request, jsonify
from datetime import datetime, timezone
import SPS

app = Flask(__name__)


@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200


@app.route("/webhook", methods=["POST"])
def receive_webhook():
    data = request.json or {}

    whatsapp_number = (
        data.get("waId")
        or data.get("wa_id")
        or data.get("whatsapp_number")
    )

    if not whatsapp_number:
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

    insert_data = {
        "whatsapp_number": str(whatsapp_number),
        "message_type": message_type,
        "message_text": message_text,
        "selected_payload": selected_payload,
        "effective_list_id": selected_payload if message_type == "list" else "TEXT",
        "record_type": "user",
        "source": None,
        "sent": False,
        "processed": False,
        "received_at": datetime.now(timezone.utc).isoformat()
    }

    supa = SPS.db()
    supa.table("incoming_messages").insert(insert_data).execute()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
