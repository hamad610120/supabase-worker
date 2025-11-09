# behavior_reader.py
from SPS import supabase

def read_behavior_data():
    """
    يقرأ بيانات المستخدمين من جدول user_behavior خلال آخر 24 ساعة فقط.
    """
    try:
        response = supabase.table("user_behavior") \
            .select("*") \
            .gte("created_at", "now() - interval '1 day'") \
            .order("created_at", desc=True) \
            .execute()

        data = response.data
        print(f"✅ تم جلب {len(data)} سجل من جدول السلوك.")
        return data

    except Exception as e:
        print(f"❌ خطأ أثناء قراءة جدول السلوك: {e}")
        return []

# اختبار سريع عند التشغيل المباشر
if __name__ == "__main__":
    behaviors = read_behavior_data()
    for b in behaviors[:3]:  # عرض أول 3 سجلات فقط للتجربة
        print(b)
