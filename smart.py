# smart.py
# ✅ يعرض جميع المنتجات بدون أي شروط
# المنتجات التي تبدأ بـ (ه / ع / 002) تظهر أولاً

import os
from supabase import create_client, Client

# ==============================
# الاتصال بقاعدة Supabase
# ==============================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ لم يتم العثور على SUPABASE_URL أو SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ تم الاتصال بقاعدة Supabase بنجاح!")

# ==============================
# المستخدم التجريبي
# ==============================
USER_ID = "076f112a-a5e1-4335-a7ec-b9da294875af"

# ==============================
# جلب وترتيب المنتجات
# ==============================
def fetch_and_sort_products():
    try:
        # جلب كل المنتجات من الجدول بدون أي شرط
        response = supabase.table("smart_products_view").select("*").execute()
        products = response.data or []

        if not products:
            print("⚠️ لا توجد منتجات في الجدول الذكي حالياً.")
            return

        # تقسيم المنتجات إلى أولوية وعادية
        priority = []  # تبدأ بـ (ه / ع / 002)
        normal = []    # باقي المنتجات

        for p in products:
            name = str(p.get("name", "")).strip()
            pid = str(p.get("id", "")).strip()
            if name.startswith("ه") or name.startswith("ع") or pid.startswith("002"):
                priority.append(p)
            else:
                normal.append(p)

        # دمج القائمتين (المميزة أولاً)
        sorted_products = priority + normal

        # عرض النتائج
        print(f"\n🧠 تم عرض وترتيب {len(sorted_products)} منتج:\n")
        for p in sorted_products:
            print(f"🛒 الاسم: {p.get('name')}")
            print(f"🆔 الرقم: {p.get('id')}")
            print(f"💰 السعر: {p.get('price')}")
            print(f"🖼️ الصورة: {p.get('image')}")
            print(f"📦 القسم: {p.get('section_id')}")
            print(f"📈 الذكاء: {p.get('smart_rank')}")
            print(f"⭐ أولوية؟ {'نعم' if p in priority else 'لا'}")
            print("—" * 60)

    except Exception as e:
        print("❌ خطأ أثناء جلب أو عرض المنتجات:")
        print(str(e))

# ==============================
# التشغيل الرئيسي
# ==============================
if __name__ == "__main__":
    print("🚀 بدأ النظام الذكي بعرض كل المنتجات ...")
    fetch_and_sort_products()
