# behavior_reader.py
from SPS import supabase
from datetime import datetime, timedelta, UTC
import time

def read_behavior_data(hours=24, retries=3, delay=2):
    """
    يقرأ جميع سجلات user_behavior خلال آخر (hours) ساعة.
    يشمل كل الأعمدة بدون استثناء.
    نظام احترافي مع:
    - إعادة محاولة عند فشل الاتصال (Retry)
    - ترتيب دقيق لضمان ثبات النتائج
    - قراءة مرنة حسب المدة
    """

    cutoff_time = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()

    for attempt in range(1, retries + 1):
        try:
            # قراءة جميع الأعمدة كاملة "*"
            response = (
                supabase.table("user_behavior")
                .select("*")
                .gte("created_at", cutoff_time)
                .order("created_at", desc=True)
                .order("id", desc=True)   # ترتيب إضافي لثبات البيانات
                .execute()
            )

            data = response.data or []

            print(f"✅ تمت القراءة بنجاح | السجلات: {len(data)} | المحاولة: {attempt}")
            return data

        except Exception as e:
            print(f"⚠️ خطأ في المحاولة {attempt}: {e}")
            if attempt < retries:
                print(f"🔄 إعادة المحاولة بعد {delay} ثانية...")
                time.sleep(delay)
            else:
                print("❌ فشل بعد استنفاد كل المحاولات.")
                return []

if __name__ == "__main__":
    behaviors = read_behavior_data()
    for row in behaviors[:3]:
        print(row)
