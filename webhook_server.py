# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL + FLUSH)
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

        # 🔴 طباعة البيانات الخام (إجباري مع flush)
        print("📦 RAW PAYLOAD FROM WATI ↓↓↓", flush=True)
        print(data, flush=True)

        whatsapp_number = None
        message_text = None

        # ---------- شكل 1 ----------
        if "message" in data and isinstance(data["message"], dict):
            msg = data["message"]
            whatsapp_number = msg.get("from") or msg.get("waId")
            message_text = msg.get("text")

        # ---------- شكل 2 ----------
        if not whatsapp_number and "messages" in data and isinstance(data["messages"], list):
            msg = data["messages"][0]
            whatsapp_number = msg.get("from") or msg.get("waId")
            message_text = msg.get("text") or msg.get("body")

        # ---------- شكل 3 (fallback) ----------
        whatsapp_number = (
            whatsapp_number
            or data.get("whatsappNumber")
            or data.get("from")
            or data.get("phone")
        )
        message_text = (
            message_text
            or data.get("messageText")
            or data.get("text")
            or data.get("body")
        )

        if not whatsapp_number or not message_text:
            print("⚠️ MESSAGE RECEIVED BUT COULD NOT PARSE CONTENT", flush=True)
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
