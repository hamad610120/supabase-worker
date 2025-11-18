import SPS
import traceback
import time

def load_and_run_modules():
    supa = SPS.db()   # ← استدعاء الدالة بشكل مباشر من الملف

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
            exec(code, globals())
            print(f"✔ تم تنفيذ {module['filename']} بنجاح\n")

        except Exception:
            print("❌ خطأ أثناء تشغيل الملف:")
            print(traceback.format_exc())

def auto_loop():
    print("🔥 النظام يعمل…")
    while True:
        load_and_run_modules()
        time.sleep(3)

if __name__ == "__main__":
    auto_loop()
