# smart_recommender.py
# ✅ نسخة مستقرة ومناسبة لـ Render
# تعمل على مراقبة جدول user_behavior وترشيح المنتجات

import os
import time
from supabase import create_client

# ==============================
# تهيئة الاتصال بـ Supabase
# ==============================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL أو SUPABASE_KEY غير موجودين في المتغيرات البيئية")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Connected successfully to Supabase!")

# ==============================
# دالة تنظيف النصوص من الرموز غير ASCII
# ==============================
def clean_text(text):
    if not text:
        return ""
    return ''.join(c for c in text if ord(c) < 128)

# ==============================
# دالة تجلب أحدث سلوك للمستخدمين
# ==============================
def get_latest_behaviors(limit=10):
    try:
        data = supabase.table("user_behavior").select("*").order("created_at", desc=True).limit(limit).execute()
        print(f"✅ Fetched {len(data.data)} recent behaviors")
        return data.data
    except Exception as e:
        print("❌ Error while fetching user_behavior table:")
        print(str(e).encode('utf-8', errors='ignore').decode('utf-8'))
        return []

# ==============================
# دالة ترشيح المنتجات للمستخدمين بناءً على السلوك
# ==============================
def recommend_products_for_user(user_id):
    try:
        behaviors = supabase.table("user_behavior").select("*").eq("user_id", user_id).limit(10).execute()
        if not behaviors.data:
            print(f"⚠️ No behaviors found for user {user_id}")
            return []

        recommended = []
        for b in behaviors.data:
            action_type = clean_text(b.get("action_type", ""))
            section_id = b.get("section_id", None)

            # خوارزمية ترشيح تجريبية بسيطة
            if section_id:
                products = supabase.table("products").select("*").eq("section_id", section_id).limit(3).execute()
                for p in products.data:
                    recommended.append(p)

        print(f"✅ Recommended {len(recommended)} products for user {user_id}")
        return recommended
    except Exception as e:
        print("❌ Error in recommendation process:")
        print(str(e).encode('utf-8', errors='ignore').decode('utf-8'))
        return []

# ==============================
# الحلقة الرئيسية (تعمل بشكل دائم)
# ==============================
if __name__ == "__main__":
    print("🚀 Smart Recommender is running...")

    while True:
        try:
            behaviors = get_latest_behaviors(limit=5)
            for b in behaviors:
                user_id = b.get("user_id")
                if user_id:
                    recommend_products_for_user(user_id)
            time.sleep(10)  # ⏱️ يحدث كل 10 ثوانٍ
        except Exception as e:
            print("⚠️ Unexpected error:", e)
            time.sleep(15)
