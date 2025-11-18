# main.py — FINAL VERSION
from SPS import db
import traceback
import time

def load_and_run_modules():
    supa = db()

    modules = supa.table("python_modules") \
                  .select("*") \
                  .eq("active", True) \
                  .order("sort_order") \
                  .execute().data

    print(f"\n🟦 تحميل {len(modules)} ملف Python افتراضي…")

    for module in modules:
        print(f"▶ تشغيل الملف: {module['filename']}")
        code = module['code']

        try:
            exec(code, globals())  # ← دمج وتشغيل الملف داخل المشروع
            print(f"✔ تم تنفيذ {module['filename']} بنجاح\n")

        except Exception:
            print(f"❌ خطأ أثناء تشغيل {module['filename']}:")
            print(traceback.format_exc())

def auto_loop():
    print("🔥 النظام يعمل… الملفات تأتي من Supabase فقط.")
    print("🔄 أي ملف تضيفه في الجدول سيتم تشغيله تلقائيًا.")
    while True:
        load_and_run_modules()
        time.sleep(3)

if __name__ == "__main__":
    auto_loop()
