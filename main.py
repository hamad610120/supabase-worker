# main.py
import time
from behavior_reader import read_behavior_data
from ai_prediction_engine import process_all_predictions
from display_controller import rebuild_display
from SPS import supabase


def get_all_users():
    """
    جلب جميع المستخدمين الذين لديهم سلوك في user_behavior
    """
    try:
        res = supabase.table("user_behavior") \
            .select("user_id") \
            .not_.is_("user_id", None) \
            .execute()

        users = {r["user_id"] for r in res.data if r.get("user_id")}
        return list(users)

    except Exception as e:
        print(f"❌ خطأ في جلب المستخدمين: {e}")
        return []


def run_full_cycle():
    """
    يشغّل النظام الذكي الكامل لكل المستخدمين:
    1) إنشاء توقعات الذكاء
    2) بناء عرض smart_display لكل مستخدم
    """

    print("\n🚀 بدء دورة جديدة للنظام الذكي...\n")

    # 1) تشغيل ذكاء 42
    print("🧠 تشغيل محرك الذكاء (AI Prediction Engine)...")
    process_all_predictions()
    print("✅ تم إنشاء التوقعات الذكية.\n")

    # 2) جلب المستخدمين
    print("👤 جلب المستخدمين...")
    users = get_all_users()
    print(f"🔢 عدد المستخدمين: {len(users)}")

    # 3) بناء شاشة العرض لكل مستخدم
    for uid in users:
        print(f"\n🎨 بناء شاشة العرض للمستخدم: {uid}")
        rebuild_display(uid)

    print("\n🌟 اكتملت الدورة بنجاح.")
    print("------------------------------------------------------")


if __name__ == "__main__":
    print("⚙️ تشغيل النظام الذكي كل 5 دقائق...\n")

    while True:
        run_full_cycle()
        print("\n⏳ انتظار 5 دقائق قبل الدورة التالية...\n")
        time.sleep(300)
