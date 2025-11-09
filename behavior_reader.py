# behavior_reader.py
from SPS import supabase
from datetime import datetime, timedelta, UTC

def read_behavior_data():
    """
    يقرأ بيانات المستخدمين من جدول user_behavior خلال آخر 24 ساعة فقط.
    """
    try:
        # نحسب التاريخ من بايثون (بصيغة UTC الحديثة)
        cutoff_time = (datetime.now(UTC) - timedelta(days=1)).isoformat()

        response = (
            supabase.table("user_behavior")
            .select("*")
            .gte("created_at", cutoff_time)
            .order("created_at", desc=True)
            .execute()
        )

        data = response.data or []
        print(f"✅ تم جلب {len(data)} سجل من جدول السلوك.")
        return data

    except Exception as e:
        print(f"❌ خطأ أثناء قراءة جدول السلوك: {e}")
        return []

if __name__ == "__main__":
    behaviors = read_behavior_data()
    for b in behaviors[:3]:
        print(b)
