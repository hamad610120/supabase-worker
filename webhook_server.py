# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL)
# ===============================

from flask import Flask, request, jsonify
import datetime
import os
import SPS  # Supabase connection

app = Flask(__name__)

# ---------------------------------
# Health Check (Render)
# ---------------------------------
@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200


# ---------------------------------
# WATI Webhook Endpoint
# ---------------------------------
@app.route("/webhook", methods=["POST"])
def receive_webhook():
    try:
        data = request.json or {}

        print("📩 WEBHOOK RECEIVED")
        print(data)

        # Extract WhatsApp number
        whatsapp_number = (
            data.get("whatsappNumber")
            or data.get("phone")
            or data.get("from")
            or data.get("contact", {}).get("phone")
        )

        # Extract message text
        message_text = (
            data.get("message")
            or data.get("text")
            or data.get("messageText")
            or data.get("body")
        )

        if not whatsapp_number or not message_text:
            print("⚠️ Missing whatsapp_number or message_text")
            return jsonify({"status": "ignored"}), 200

        supa = SPS.db()

        # Save message to database
        supa.table("incoming_messages").insert({
            "whatsapp_number": str(whatsapp_number),
            "message_text": str(message_text),
            "source": "wati",
            "received_at": datetime.datetime.utcnow().isoformat()
        }).execute()

        print(f"✅ SAVED MESSAGE FROM {whatsapp_number}: {message_text}")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return jsonify({"status": "error"}), 500


# ---------------------------------
# Run Server (Render compatible)
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
