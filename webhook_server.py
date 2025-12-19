# ===============================
# webhook_server.py
# WATI Webhook Receiver
# ===============================

from flask import Flask, request, jsonify
import datetime
import SPS  # اتصال Supabase

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def receive_webhook():
    try:
        data = request.json

        print("📩 WEBHOOK RECEIVED")
        print(data)

        # استخراج البيانات الأساسية من WATI
        whatsapp_number = (
            data.get("whatsappNumber")
            or data.get("phone")
            or data.get("from")
        )

        message_text = (
            data.get("message")
            or data.get("text")
            or data.get("messageText")
        )

        if not whatsapp_number or not message_text:
            print("⚠️ Missing whatsapp_number or message_text")
            return jsonify({"status": "ignored"}), 200

        supa = SPS.db()

        # حفظ الرسالة في جدول incoming_messages
        supa.table("incoming_messages").insert({
            "whatsapp_number": str(whatsapp_number),
            "message_text": str(message_text),
            "source": "wati",
            "received_at": datetime.datetime.utcnow().isoformat()
        }).execute()

        print(f"✅ SAVED MESSAGE FROM {whatsapp_number}")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return jsonify({"status": "error"}), 500


if __name__ == "__main__":
    # Render يحدد PORT تلقائيًا
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
