# main.py
import time
from SPS import supabase
from behavior_reader import read_behavior_data
from ai_recommendations import generate_recommendations
from display_controller import rebuild_display
from datetime import datetime


# -------------------------------------------------------------------
# 1) جلب جميع المستخدمين من جدول users
# -------------------------------------------------------------------
def get_all_users():
    try:
        res = supabase.table("users").select("id").execute()
        return [u["id"] for u in res.data] if res.data else []
    except Exception as e:
        print(f"❌ خطأ في جلب المستخدمين: {e}")
        return []


# -------------------------------------------------------------------
# 2) تسجيل دخول المستخدم (للذكاء)
# -------------------------------------------------------------------
def log_user_session_start(user_id):
    try:
        supabase.table("user_behavior").insert({
            "user_id": user_id,
            "notes": "session_start",
            "created_at": datetime.now().isoformat()
        }).execute()
        print(f"📌 تم تسجيل session_start للمستخدم: {user_id}")
    except Exception as e:
        print(f"❌ خطأ في تسجيل session_start: {e}")


# -------------------------------------------------------------------
# 3) الدورة الكاملة لكل مستخدم
# -------------------------------------------------------------------
def run_full_cycle(user_id):
    print(f"\n🚀 بدء دورة النظام لمستخدم: {user_id}\n")

    # تسجيل دخول
    log_user_session_start(user_id)

    # قراءة سلوك المستخدم
    print("📊 قراءة بيانات السلوك...")
    behaviors = read_behavior_data()
    print(f"📊 تم جلب {len(behaviors)} سجل.\n")

    # إنشاء التوصيات
    print("🧠 إنشاء التوصيات...")
    generate_recommendations()
    print("🧠 تم إنشاء التوقعات.\n")

    # بناء العرض الذكي
    print("🎨 تحديث شاشة العرض...")
    rows = rebuild_display(user_id)
    print(f"🎨 تم بناء عرض للمستخدم {user_id} — عدد العناصر: {len(rows)}\n")

    print("------------------------------------------------------------")


# -------------------------------------------------------------------
# 4) تشغيل كل 5 دقائق لجميع المستخدمين
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("⚙️ تشغيل النظام الذكي لجميع المستخدمين كل 5 دقائق...\n")

    while True:
        users = get_all_users()

        if not users:
            print("⚠️ لا يوجد مستخدمين في جدول users!\n")
        else:
            print(f"👥 عدد المستخدمين: {len(users)}\n")

        for uid in users:
            run_full_cycle(uid)

        print("\n⏳ انتظار 5 دقائق قبل الدورة التالية...\n")
        time.sleep(300)
