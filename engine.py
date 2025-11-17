# ============================================================
#  engine.py — المحرك الذكي المركزي
#  ينفّذ أي أمر تكتبه في جدول system_commands
# ============================================================

import time
import traceback
import json
from datetime import datetime, UTC
from SPS import supabase


# ============================================================
# جلب الأوامر المعلقة من جدول system_commands
# ============================================================

def fetch_pending_commands():
    try:
        res = (
            supabase.table("system_commands")
            .select("*")
            .eq("status", "pending")
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"❌ خطأ في قراءة system_commands: {e}")
        return []


# ============================================================
# تحديث حالة المهمة في القاعدة
# ============================================================

def update_command_status(cmd_id, status, result=None):
    try:
        supabase.table("system_commands").update({
            "status": status,
            "result": result,
            "executed_at": datetime.now(UTC).isoformat()
        }).eq("id", cmd_id).execute()
    except Exception as e:
        print(f"❌ خطأ في تحديث حالة الأمر {cmd_id}: {e}")


# ============================================================
# تنفيذ الأمر — يعتمد على العمود (command)
# ============================================================

def execute_command(cmd):
    cmd_id = cmd["id"]
    command_text = cmd["command"]   # ← ← ← هذا هو التعديل الصحيح

    print("\n--------------------------------------------------")
    print(f"🧠 تنفيذ أمر جديد:")
    print(f"📌 ID: {cmd_id}")
    print(f"📄 النص: {command_text}")
    print("--------------------------------------------------")

    try:
        result = process_natural_command(command_text)
        update_command_status(cmd_id, "done", result)
        print("✅ تم التنفيذ بنجاح.\n")

    except Exception as e:
        error_message = f"{e}\n{traceback.format_exc()}"
        update_command_status(cmd_id, "failed", error_message)
        print(f"❌ فشل التنفيذ: {error_message}\n")



# ============================================================
# الذكاء الأساسي — تفسير النص وتنفيذ الإجراء المناسب
# ============================================================

def process_natural_command(text):

    t = text.strip().lower()

    # ---- 1) تحليل السلوك ----
    if "سلوك" in t or "behavior" in t:
        return analyze_behavior_and_generate_predictions()

    # ---- 2) بناء display الذكي ----
    if "عرض" in t or "display" in t:
        return rebuild_smart_display_for_all_users()

    # ---- 3) مسح جداول ----
    if "حذف" in t or "مسح" in t or "reset" in t:
        return clear_tables_from_text(t)

    # ---- 4) SQL مباشر ----
    if "sql:" in t:
        raw_sql = t.replace("sql:", "").strip()
        return execute_raw_sql(raw_sql)

    # ---- 5) ذكاء عام ----
    return general_ai_interpretation(text)



# ============================================================
# (A) تحليل السلوك وإنشاء التوصيات
# ============================================================

def analyze_behavior_and_generate_predictions():

    behaviors = (
        supabase.table("user_behavior")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    ).data

    if not behaviors:
        return "⚠️ لا يوجد بيانات سلوك"

    results = []
    for b in behaviors:
        score = float(b.get("action_score", 0))
        confidence = float(b.get("confidence", 0))
        final_score = round((score * 0.7) + (confidence * 0.3), 3)

        supabase.table("ai_recommendations").insert({
            "user_id": b["user_id"],
            "product_id": b.get("product_id"),
            "score": final_score,
            "created_at": datetime.now(UTC).isoformat()
        }).execute()

        results.append(final_score)

    return f"✔ تم تحليل {len(results)} سجل وإنشاء توصيات."



# ============================================================
# (B) بناء smart_display لكل المستخدمين
# ============================================================

def rebuild_smart_display_for_all_users():

    users = (
        supabase.table("user_behavior")
        .select("user_id")
        .execute()
    ).data

    user_ids = {u["user_id"] for u in users}
    count = 0

    for uid in user_ids:
        supabase.table("smart_display").insert({
            "user_id": uid,
            "product_id": "AUTO",
            "priority": 100,
            "source": "SYSTEM",
            "created_at": datetime.now(UTC).isoformat()
        }).execute()
        count += 1

    return f"✔ تم إنشاء عرض لـ {count} مستخدم."



# ============================================================
# (C) مسح جداول
# ============================================================

def clear_tables_from_text(text):

    if "التوصيات" in text or "recommendations" in text:
        supabase.table("ai_recommendations").delete().neq("id", "").execute()
        return "✔ تم مسح جدول التوصيات"

    if "العرض" in text or "display" in text:
        supabase.table("smart_display").delete().neq("id", "").execute()
        return "✔ تم مسح جدول smart_display"

    return "⚠️ لم يتم العثور على جدول للمسح"



# ============================================================
# (D) SQL مباشر
# ============================================================

def execute_raw_sql(sql):
    try:
        supabase.rpc("exec_sql", {"query": sql}).execute()
        return f"✔ SQL Executed: {sql}"
    except Exception as e:
        return f"SQL Error: {e}"



# ============================================================
# (E) ذكاء عام
# ============================================================

def general_ai_interpretation(text):
    return f"🤖 تمت قراءة الأمر، وسيتم دعم هذا النوع قريباً: {text}"



# ============================================================
# Loop الرئيسي
# ============================================================

def start_engine():
    print("\n🚀 محرك الذكاء بدأ العمل...")

    while True:
        commands = fetch_pending_commands()

        if commands:
            print(f"\n📌 تم العثور على {len(commands)} أوامر جديدة.")
            for cmd in commands:
                execute_command(cmd)
        else:
            print("⏳ لا يوجد أوامر جديدة. الانتظار...")

        time.sleep(5)


if __name__ == "__main__":
    start_engine()
