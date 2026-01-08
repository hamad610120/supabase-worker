# ===============================
# webhook_server.py
# WATI Webhook Receiver (FINAL)
# ===============================

from flask import Flask, request, jsonify
import datetime
import os
import re
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

        print("📦 RAW PAYLOAD ↓↓↓")
        print(data)

        # -----------------------------
        # WhatsApp Number (WATI REAL)
        # -----------------------------
        whatsapp_number = data.get("waId")

        if not whatsapp_number:
            print("⚠️ Missing waId")
            return jsonify({"status": "ignored"}), 200

        message_type = None
        event_key = None
        message_text = None

        supa = SPS.db()

        # =============================
        # 1️⃣ TEXT MESSAGE (TEXT + BUTTON FROM WATI)
        # =============================
        if data.get("type") == "text":
            message_type = "text"

            # قراءة النص
            raw_text = (data.get("text") or "").strip()

            # تنظيف النص (إزالة الإيموجي والرموز)
            message_text = re.sub(r"[^\w\s]", "", raw_text).strip()

            # البحث في text_commands
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
        # 2️⃣ INTERACTIVE (غير مستخدم فعليًا في WATI)
        # =============================
        elif data.get("type") == "interactive" and data.get("interactiveData"):
            interactive = data.get("interactiveData")

            if interactive.get("reply"):
                message_type = "button"
                event_key = interactive["reply"].get("id")
                message_text = "[button]"

            elif interactive.get("listReply"):
                message_type = "list"
                event_key = interactive["listReply"].get("id")
                message_text = "[list]"

            else:
                print("⚠️ interactiveData بدون reply")
                return jsonify({"status": "ignored"}), 200

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
            "received_at": datetime.datetime.now(datetime.UTC).isoformat()
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
