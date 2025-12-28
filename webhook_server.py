# ===============================
# webhook_server.py
# Unified Webhook (WATI + META)
# FINAL - PRODUCTION READY
# ===============================

from flask import Flask, request, jsonify
import datetime
import os
import SPS  # Supabase connection

app = Flask(__name__)

# ---------------------------------
# Health Check
# ---------------------------------
@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200


# ---------------------------------
# Unified Webhook
# ---------------------------------
@app.route("/webhook", methods=["POST"])
def receive_webhook():
    data = request.json or {}
    supa = SPS.db()

    print("📦 RAW PAYLOAD ↓↓↓", flush=True)
    print(data, flush=True)

    # =====================================================
    # 1️⃣ WATI PAYLOAD
    # =====================================================
    if "waId" in data:
        try:
            whatsapp_number = data.get("waId")
            message_text = data.get("text")

            if whatsapp_number and message_text:
                supa.table("incoming_messages").insert({
                    "whatsapp_number": str(whatsapp_number),
                    "message_text": str(message_text),
                    "source": "wati",
                    "received_at": datetime.datetime.utcnow().isoformat()
                }).execute()

                print(
                    f"✅ WATI SAVED {whatsapp_number}: {message_text}",
                    flush=True
                )

            return jsonify({"status": "wati_ok"}), 200

        except Exception as e:
            print("❌ WATI ERROR:", e, flush=True)
            return jsonify({"status": "wati_error"}), 500

    # =====================================================
    # 2️⃣ META CLOUD API PAYLOAD
    # =====================================================
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        metadata = entry.get("metadata", {})
        messages = entry.get("messages", [])

        for msg in messages:
            whatsapp_number = msg.get("from")
            message_text = msg.get("text", {}).get("body")

            supa.table("incoming_messages_meta").insert({
                "phone_number_id": metadata.get("phone_number_id"),
                "display_phone_number": metadata.get("display_phone_number"),
                "whatsapp_number": whatsapp_number,
                "message_text": message_text,
                "message_id": msg.get("id"),
                "message_type": msg.get("type"),
                "source": "meta",
                "received_at": datetime.datetime.utcnow().isoformat(),
                "raw_payload": data
            }).execute()

            print(
                f"✅ META SAVED {whatsapp_number}: {message_text}",
                flush=True
            )

        return jsonify({"status": "meta_ok"}), 200

    except Exception as e:
        print("⚠️ UNKNOWN PAYLOAD:", e, flush=True)
        return jsonify({"status": "ignored"}), 200


# ---------------------------------
# Run Server (Render compatible)
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
