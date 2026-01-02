# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL + TEXT COMMANDS)
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
# WATI Webhook Endpoint
# ---------------------------------
@app.route("/webhook", methods=["POST"])
def receive_webhook():
    try:
        data = request.json or {}

        print("📩 WEBHOOK RECEIVED")
        print(data)

        # -----------------------------
        # WhatsApp Number
        # -----------------------------
        whatsapp_number = (
            data.get("whatsappNumber")
            or data.get("phone")
            or data.get("from")
            or data.get("waId")
            or data.get("contact", {}).get("phone")
        )

        if not whatsapp_number:
            print("⚠️ Missing whatsapp number")
            return jsonify({"status": "ignored"}), 200

        message_type = None
        event_key = None
        message_text = None

        supa = SPS.db()

        # =============================
        # 1️⃣ TEXT MESSAGE
        # =============================
        if data.get("messageType") == "text":
            message_type = "text"
            message_text = (
                data.get("text", {}).get("body")
                or data.get("message")
                or data.get("messageText")
                or ""
            ).strip()

            # 🔎 search in text_commands
            cmd = (
                supa.table("text_commands")
                .select("event_key")
                .eq("keyword", message_text)
                .eq("active", True)
                .limit(1)
                .execute()
            )

            if cmd.data:
                event_key = cmd.data[0]["event_key"]
            else:
                event_key = "start"

        # =============================
        # 2️⃣ BUTTON CLICK
        # =============================
        elif (
            data.get("messageType") == "interactive"
            and data.get("interactive", {}).get("type") == "button_reply"
        ):
            message_type = "button"
            event_key = data["interactive"]["button_reply"]["id"]
            message_text = "[button]"

        else:
            print("⚠️ Unsupported message type")
            return jsonify({"status": "ignored"}), 200

        # -----------------------------
        # Save to incoming_messages
        # -----------------------------
        supa.table("incoming_messages").insert({
            "whatsapp_number": str(whatsapp_number),
            "message_type": message_type,
            "event_key": event_key,
            "message_text": message_text,
            "source": "wati",
            "processed": False,
            "received_at": datetime.datetime.utcnow().isoformat()
        }).execute()

        print(
            f"✅ SAVED | type={message_type} | event={event_key} | from={whatsapp_number}"
        )

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return jsonify({"status": "error"}), 500


# ---------------------------------
# Run Server
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
