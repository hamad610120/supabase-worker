# display_manager.py
from SPS import supabase

def update_display_table():
    """
    يقرأ من جدول ai_recommendations ويرتب المنتجات حسب أعلى Score
    ويحدث جدول ai_display تلقائيًا.
    """
    try:
        # جلب كل التوصيات
        response = supabase.table("ai_recommendations").select("*").order("score", desc=True).execute()
        data = response.data or []

        if not data:
            print("⚠️ لا توجد توصيات لتحديث العرض.")
            return

        print(f"✅ تم جلب {len(data)} توصية لتحديث العرض.")

        # تحديث جدول العرض بناءً على الترتيب
        for index, item in enumerate(data, start=1):
            product_id = item.get("product_id")
            score = item.get("score")

            # التحقق هل المنتج موجود
            existing = supabase.table("ai_display").select("*").eq("product_id", product_id).execute()

            if existing.data:
                # تحديث الترتيب الحالي
                supabase.table("ai_display").update({
                    "score": score,
                    "rank": index,
                    "updated_at": "now()"
                }).eq("product_id", product_id).execute()
            else:
                # إدخال منتج جديد في جدول العرض
                supabase.table("ai_display").insert({
                    "product_id": product_id,
                    "score": score,
                    "rank": index
                }).execute()

        print("✅ تم تحديث جدول العرض بنجاح وفقًا لأعلى التوصيات.")

    except Exception as e:
        print(f"❌ خطأ أثناء تحديث جدول العرض: {e}")


if __name__ == "__main__":
    update_display_table()
