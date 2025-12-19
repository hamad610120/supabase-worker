# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL - WATI PAYLOAD FIXED)
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

        print("📦 RAW PAYLOAD FROM WATI ↓↓↓", flush=True)
        print(data, flush=True)

        # ✅ استخراج صحيح حسب Payload الحقيقي
        whatsapp_number = data.get("waId")
        message_text = data.get("text")

        if not whatsapp_number or not message_text:
            print("⚠️ MESSAGE RECEIVED BUT MISSING waId OR text", flush=True)
            return jsonify({"status": "ignored"}), 200

        supa = SPS.db()

        supa.table("incoming_messages").insert({
            "whatsapp_number": str(whatsapp_number),
            "message_text": str(message_text),
            "source": "wati",
            "received_at": datetime.datetime.utcnow().isoformat()
        }).execute()

        print(
            f"✅ SAVED MESSAGE FROM {whatsapp_number}: {message_text}",
            flush=True
        )

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e, flush=True)
        return jsonify({"status": "error"}), 500


# ---------------------------------
# Run Server (Render compatible)
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
