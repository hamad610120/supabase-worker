# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL)
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

        message_type = data.get("type")
        message_text = data.get("text")
        payload = None

        # ===============================
        # 🔘 Button reply
        # ===============================
        if data.get("buttonReply"):
            payload = data["buttonReply"].get("payload")

        # ===============================
        # 📋 List reply
        # ===============================
        elif data.get("listReply"):
            payload = data["listReply"].get("id")

        # ===============================
        # 📝 Text message (no payload)
        # ===============================
        else:
            print("ℹ️ Text or unsupported type received (no payload)")

        supa = SPS.db()

        supa.table("incoming_messages").insert({
            "whatsapp_number": whatsapp_number,
            "message_type": message_type,
            "message_text": message_text,
            "selected_payload": payload,
            "record_type": "user",
            "sent": False,
            "source": "wati",
            "received_at": datetime.datetime.now(datetime.UTC).isoformat()
        }).execute()

        print(f"✅ RECEIVED | from={whatsapp_number} | payload={payload}")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return jsonify({"status": "error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
