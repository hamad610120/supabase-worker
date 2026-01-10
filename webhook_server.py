# ===============================
# webhook_server.py
# WATI Webhook Receiver (PAYLOAD BASED)
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

        print("📦 RAW PAYLOAD ↓↓↓")
        print(data)

        # -----------------------------
        # WhatsApp Number
        # -----------------------------
        whatsapp_number = data.get("waId")
        if not whatsapp_number:
            print("⚠️ Missing waId")
            return jsonify({"status": "ignored"}), 200

        # -----------------------------
        # Extract payload (ONLY)
        # -----------------------------
        selected_payload = None
        message_type = data.get("type")

        # Button click
        if message_type == "button":
            selected_payload = data.get("payload")

        # List selection
        elif message_type == "list":
            selected_payload = data.get("payload")

        # Interactive (future / safety)
        elif message_type == "interactive":
            interactive = data.get("interactiveData") or {}
            if interactive.get("reply"):
                selected_payload = interactive["reply"].get("id")
            elif interactive.get("listReply"):
                selected_payload = interactive["listReply"].get("id")

        # Text messages → ignore logic, no payload
        else:
            print("ℹ️ Text or unsupported type received (no payload)")

        supa = SPS.db()

        # -----------------------------
        # Save incoming event
        # -----------------------------
        (
            supa.table("incoming_messages")
            .insert({
                "whatsapp_number": str(whatsapp_number),
                "selected_payload": selected_payload,
                "message_type": message_type,
                "source": "wati",
                "record_type": "user",
                "received_at": datetime.datetime.now(datetime.UTC).isoformat()
            })
            .execute()
        )

        print(
            f"✅ RECEIVED | from={whatsapp_number} | payload={selected_payload}"
        )

        # -----------------------------
        # Call decision engine (DB)
        # -----------------------------
        decision = (
            supa.rpc("apply_next_action", {"p_whatsapp": str(whatsapp_number)})
            .execute()
        )

        if not decision.data:
            print("⚠️ No action returned")
            return jsonify({"status": "ok"}), 200

        action = decision.data[0]

        print("🤖 NEXT ACTION ↓↓↓")
        print(action)

        # -------------------------------------------------
        # IMPORTANT:
        # We DO NOT send messages from here.
        # We only return the decision to the sender service.
        # -------------------------------------------------

        return jsonify({
            "status": "ok",
            "next_action": action
        }), 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return jsonify({"status": "error"}), 500


# ---------------------------------
# Run Server
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
