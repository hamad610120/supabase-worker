from SPS import run_sql
import time

print("🚀 العامل متصل بقاعدة Supabase ويعمل الآن بشكل دائم...")

while True:
    try:
        # استعلام بسيط للتحقق من الاتصال
        result = run_sql("SELECT NOW();")
        print("🕒 الوقت الحالي من قاعدة البيانات:", result[0]['now'])
    except Exception as e:
        print("❌ خطأ:", e)

    # انتظر 10 ثوانٍ قبل التكرار التالي
    time.sleep(10)
