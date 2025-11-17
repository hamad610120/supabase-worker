# ============================================================
#  engine.py — المحرك الذكي المركزي
#  نظام ذكاء شامل ينفذ أي أمر تكتبه في جدول system_commands
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
# مشغّل الأوامر — ينفّذ أي أمر مكتوب في command_text
# ============================================================

def execute_command(cmd):
    cmd_id = cmd["id"]
    command_text = cmd["command_text"]

    print("\n--------------------------------------------------")
    print(f"🧠 تنفيذ أمر جديد:")
    print(f"📌 ID: {cmd_id}")
    print(f"📄 النص: {command_text}")
    print("--------------------------------------------------")

    try:
        # ================================================
        #  هنا الذكاء الحقيقي — يتم تحليل نص الأمر وتنفيذه
        # ================================================

        result = process_natural_command(command_text)

        # النجاح
        update_command_status(cmd_id, "done", result)
        print("✅ تم التنفيذ بنجاح.\n")

    except Exception as e:
        error_message = f"{e}\n{traceback.format_exc()}"
        update_command_status(cmd_id, "failed", error_message)
        print(f"❌ فشل التنفيذ: {error_message}\n")


# ============================================================
# الذكاء الأساسي لمعالجة النص وتحويله لأمر فعلي
# ============================================================

def process_natural_command(text):
    """
    يستقبل نص بشري عادي مثل:
    (حلل السلوك وأضف التوصيات)
    ويحوّله إلى وظيفة فعلية.
    """

    t = text.strip().lower()

    # --------------------------------------------------------
    # 1) تحليل السلوك → user_behavior
    # --------------------------------------------------------
    if "سلوك" in t or "behavior" in t:
        return analyze_behavior_and_generate_predictions()

    # --------------------------------------------------------
    # 2) بناء smart_display
    # --------------------------------------------------------
    if "عرض" in t or "display" in t:
        return rebuild_smart_display_for_all_users()

    # --------------------------------------------------------
    # 3) تنظيف جدول – reset / clear
    # --------------------------------------------------------
    if "حذف" in t or "reset" in t or "مسح" in t:
        return clear_tables_from_text(t)

    # --------------------------------------------------------
    # 4) أمر SQL مباشر
    # --------------------------------------------------------
    if "sql:" in t:
        raw_sql = t.replace("sql:", "").strip()
        return execute_raw_sql(raw_sql)

    # --------------------------------------------------------
    # 5) أي أمر عام
    # --------------------------------------------------------
    return general_ai_interpretation(text)



# ============================================================
# (A) تحليل السلوك وإنشاء التوقعات
# ============================================================

def analyze_behavior_and_generate_predictions():
    behaviors = (
        supabase.table("user_behavior")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    ).data

    if not behaviors:
        return "⚠️ لا يوجد بيانات سلوك."

    # تحليل بسيط مبدئي
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

        results.append({
            "user_id": b["user_id"],
            "product_id": b.get("product_id"),
            "score": final_score
        })

    return f"تم تحليل {len(results)} سلوك وإنشاء توصيات."


# ============================================================
# (B) بناء smart_display لكل المستخدمين
# ============================================================

def rebuild_smart_display_for_all_users():
    print("🔄 إعادة بناء smart_display لكل المستخدمين...")

    # جلب المستخدمين من جدول السلوك
    users = (
        supabase.table("user_behavior")
        .select("user_id")
        .execute()
    ).data

    user_ids = {u["user_id"] for u in users}

    total = 0
    for uid in user_ids:
        supabase.table("smart_display").insert({
            "user_id": uid,
            "product_id": "AUTO",
            "priority": 100,
            "source": "SYSTEM",
            "created_at": datetime.now(UTC).isoformat()
        }).execute()
        total += 1

    return f"تم إنشاء عرض لعدد {total} مستخدم."


# ============================================================
# (C) مسح جداول حسب النص
# ============================================================

def clear_tables_from_text(text):
    if "التوصيات" in text or "recommendations" in text:
        supabase.table("ai_recommendations").delete().neq("id", "").execute()
        return "تم مسح جدول التوصيات."

    if "العرض" in text or "display" in text:
        supabase.table("smart_display").delete().neq("id", "").execute()
        return "تم مسح جدول smart_display."

    return "لم يتم العثور على جدول للمسح."


# ============================================================
# (D) تنفيذ SQL مباشر
# ============================================================

def execute_raw_sql(sql):
    try:
        res = supabase.rpc("exec_sql", {"query": sql}).execute()
        return f"SQL executed: {sql}"
    except Exception as e:
        return f"SQL error: {e}"


# ============================================================
# (E) ذكاء عام لأي أمر آخر
# ============================================================

def general_ai_interpretation(text):
    """
    مستقبلًا يمكننا ربطه بـ GPT.
    الآن نعيد نص توضيحي فقط.
    """
    return f"🤖 تم استقبال الأمر، لكن لا يوجد إجراء محدد له بعد: {text}"


# ============================================================
# المشغّل الرئيسي — يعمل للأبد
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

        time.sleep(5)  # يعمل كل 5 ثوانٍ


if __name__ == "__main__":
    start_engine()
