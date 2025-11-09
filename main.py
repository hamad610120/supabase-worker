# main.py
import time
from behavior_reader import read_behavior_data
from ai_recommendations import generate_recommendations
from display_manager import update_display_table

def run_full_cycle():
    """
    تشغيل النظام الذكي كاملًا:
    1. قراءة السلوك.
    2. توليد التوصيات.
    3. تحديث العرض النهائي.
    """
    print("🚀 بدء التشغيل الكامل للنظام الذكي...")
    time.sleep(1)

    print("\n📊 الخطوة 1: قراءة بيانات السلوك...")
    behaviors = read_behavior_data()
    print(f"✅ تم جلب {len(behaviors)} سجل من السلوك.\n")

    print("🧠 الخطوة 2: إنشاء التوصيات الذكية...")
    generate_recommendations()
    print("✅ تم توليد التوصيات بنجاح.\n")

    print("🎨 الخطوة 3: تحديث جدول العرض النهائي...")
    update_display_table()
    print("✅ تم تحديث جدول العرض بنجاح.\n")

    print("🌟 النظام الذكي اكتمل بنجاح ✅")


if __name__ == "__main__":
    run_full_cycle()
