from supabase import create_client, Client
import time, random
from datetime import datetime, timedelta
import traceback

# ✅ إعداد الاتصال الآمن مع Supabase عبر API الرسمي
SUPABASE_URL = "https://xnyzgnfiqczxlzuocttt.supabase.co"
SUPABASE_KEY = "ضع هنا مفتاحك السري من Supabase (service_role أو anon)"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ تم الاتصال بـ Supabase API بنجاح")

# إعداد زمن التحديث
INTERVAL = 15  # كل 15 ثانية يتحقق من السلوك الجديد
last_check = datetime.utcnow() - timedelta(seconds=INTERVAL)

# 🔄 الحلقة الرئيسية
while True:
    try:
        # 1️⃣ جلب أحدث السلوكيات الجديدة
        behaviors = supabase.table("user_behavior") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute().data or []

        if behaviors:
            print(f"🟢 تم العثور على {len(behaviors)} سلوك جديد.")
            for b in behaviors:
                user_id = b.get("user_id")
                section_id = b.get("section_id")
                product_id = b.get("product_id")
                base_score = float(b.get("action_score") or 0.5)

                # 2️⃣ اختيار منتجات عشوائية من نفس القسم
                products = supabase.table("smart_products_view") \
                    .select("id, name, price, image, section_id") \
                    .eq("is_active", True) \
                    .eq("section_id", section_id) \
                    .neq("id", product_id) \
                    .order("updated_at", desc=True) \
                    .limit(5) \
                    .execute().data or []

                if not products:
                    print(f"⚠️ لا توجد منتجات متاحة في القسم {section_id}")
                    continue

                print(f"✨ إنشاء توصيات جديدة للمستخدم {user_id}:")
                for p in products:
                    new_score = round(base_score * random.uniform(0.4, 1.0), 2)
                    reason = f"نظام تجريبي: ترشيح ديناميكي - {p['name']}"

                    # 3️⃣ إضافة التوصية إلى user_recommendations
                    supabase.table("user_recommendations").insert({
                        "user_id": user_id,
                        "product_id": p["id"],
                        "section_id": section_id,
                        "reason": reason,
                        "score": new_score
                    }).execute()

                    print(f"  ✅ رشّح المنتج {p['id']} ({p['name']}) بدرجة {new_score}")

                    # 4️⃣ تحديث بيانات المنتج في smart_products_view
                    current = supabase.table("smart_products_view").select("recommendation_score, smart_rank").eq("id", p["id"]).execute().data
                    if current:
                        old_score = current[0].get("recommendation_score") or 0
                        total_score = old_score + new_score
                        smart_rank = round(total_score / 10, 2)

                        supabase.table("smart_products_view").update({
                            "recommendation_score": total_score,
                            "smart_rank": smart_rank,
                            "is_recommended": True,
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", p["id"]).execute()

                print("🔁 تم إنشاء توصيات مختلفة ومحدثة لهذا المستخدم.\n")

        else:
            print("... لا توجد أحداث جديدة حالياً")

        # 5️⃣ تحديث وقت الفحص
        last_check = datetime.utcnow()

    except Exception as e:
        print("❌ خطأ أثناء التنفيذ:", e)
        traceback.print_exc()

    # الانتظار قبل التحقق التالي
    time.sleep(INTERVAL)
