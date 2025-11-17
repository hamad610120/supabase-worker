# display_controller.py
from SPS import supabase
from datetime import datetime, UTC


# -----------------------------------------------------------
# 1) جلب قواعد التحكم (display_control_rules)
# -----------------------------------------------------------
def get_display_rules():
    try:
        res = (
            supabase.table("display_control_rules")
            .select("*")
            .eq("is_active", True)
            .order("priority", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"❌ خطأ في جلب قواعد التحكم: {e}")
        return []


# -----------------------------------------------------------
# 2) جلب توقعات الذكاء من model_predictions
# -----------------------------------------------------------
def get_ai_predictions(user_id):
    try:
        res = (
            supabase.table("model_predictions")
            .select("*")
            .eq("user_id", user_id)
            .order("prediction_score", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"❌ خطأ في جلب توقعات AI: {e}")
        return []


# -----------------------------------------------------------
# 3) جلب بيانات المنتج من جدول products
# -----------------------------------------------------------
def get_product_info(product_id):
    try:
        res = (
            supabase.table("products")
            .select("id, name, image, price, description, notes")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except:
        return None


# -----------------------------------------------------------
# 4) تطبيق القواعد على نتائج الذكاء
# -----------------------------------------------------------
def apply_rules_to_ai(ai_list, rules, user_id):
    final_list = []

    for rule in rules:

        # 4.1 — إخفاء المنتج
        if rule["action"] == "hide" and rule.get("product_id"):
            ai_list = [x for x in ai_list if x["product_id"] != rule["product_id"]]

        # 4.2 — تجاهل الذكاء بالكامل (override)
        if rule["action"] == "override":
            print("⚠️ override مفعّل → استخدام منتجاتك فقط")
            return build_manual_injection(rule, user_id)

        # 4.3 — inject → حقن منتجات إضافية
        if rule["action"] == "inject":
            inject_list = rule.get("meta", {}).get("recommend", [])
            for pid in inject_list:
                final_list.append({
                    "user_id": user_id,
                    "product_id": pid,
                    "priority": rule["priority"],
                    "source": "RULE",
                    "rule_or_ai_type": "inject"
                })

        # 4.4 — boost → رفع أولوية منتج
        if rule["action"] == "boost" and rule.get("product_id"):
            for x in ai_list:
                if x["product_id"] == rule["product_id"]:
                    x["prediction_score"] = float(x["prediction_score"]) + 0.5

        # 4.5 — replace → استبدال منتج
        if rule["action"] == "replace" and rule.get("product_id"):
            new_pid = rule.get("meta", {}).get("new_product")
            for x in ai_list:
                if x["product_id"] == rule["product_id"]:
                    x["product_id"] = new_pid

    # إضافة نتائج AI بعد تطبيق القواعد
    for x in ai_list:
        final_list.append({
            "user_id": user_id,
            "product_id": x["product_id"],
            "section_id": x.get("section_id"),
            "priority": int(float(x["prediction_score"]) * 100),
            "source": "AI",
            "rule_or_ai_type": x["prediction_type"]
        })

    return final_list


# -----------------------------------------------------------
# 5) في حالة override: استخدم قائمة توصيات ثابتة
# -----------------------------------------------------------
def build_manual_injection(rule, user_id):
    rows = []
    inject_list = rule.get("meta", {}).get("recommend", [])

    for pid in inject_list:
        rows.append({
            "user_id": user_id,
            "product_id": pid,
            "section_id": rule.get("section_id"),
            "priority": rule["priority"],
            "source": "RULE_ONLY",
            "rule_or_ai_type": rule["action"]
        })

    return rows


# -----------------------------------------------------------
# 6) كتابة النتائج النهائية إلى smart_display
# -----------------------------------------------------------
def write_to_smart_display(rows, user_id):
    try:
        # حذف العرض القديم لهذا المستخدم فقط
        supabase.table("smart_display") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()

        # إضافة العرض الجديد
        if rows:
            supabase.table("smart_display").insert(rows).execute()

        print(f"✅ تم تحديث smart_display للمستخدم {user_id} بعدد {len(rows)} عنصر.")

    except Exception as e:
        print(f"❌ خطأ في تحديث smart_display: {e}")


# -----------------------------------------------------------
# 7) الوظيفة الرئيسية لبناء العرض
# -----------------------------------------------------------
def rebuild_display(user_id):
    print(f"🚀 إعادة بناء شاشة العرض للمستخدم {user_id}...")

    # 1) جلب توقعات AI
    ai_list = get_ai_predictions(user_id)

    # 2) جلب القواعد
    rules = get_display_rules()

    # 3) دمج الاثنين
    rows = apply_rules_to_ai(ai_list, rules, user_id)

    # 4) جلب بيانات المنتج وإضافة معلومات كاملة
    final_rows = []

    for r in rows:
        product = get_product_info(r["product_id"])

        final_rows.append({
            "user_id": user_id,
            "product_id": r["product_id"],
            "section_id": r.get("section_id"),
            "priority": r["priority"],
            "source": r["source"],
            "rule_or_ai_type": r["rule_or_ai_type"],

            # معلومات المنتج
            "product_name": product["name"] if product else None,
            "product_image": product["image"] if product else None,
            "price": product["price"] if product else None,
            "description": product["description"] if product else None,
            "notes": product["notes"] if product else None,

            "created_at": datetime.now(UTC).isoformat()
        })

    # 5) كتابة النتائج النهائية
    write_to_smart_display(final_rows, user_id)

    return final_rows


# -----------------------------------------------------------
# 8) اختبار سريع
# -----------------------------------------------------------
if __name__ == "__main__":
    test_user = "978fb3cf-8ef6-4661-9d62-1056c7dfad53"
    rebuild_display(test_user)
