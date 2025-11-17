# ai_recommendations.py
from SPS import supabase
from behavior_reader import read_behavior_data


def calculate_score(action_score, confidence, views_count, clicks_count):
    """
    دالة لحساب درجة الذكاء (smart_score) بناءً على بيانات السلوك.
    """
    try:
        score = (float(action_score) * 0.6) + \
                (float(confidence) * 0.3) + \
                ((clicks_count + 1) / (views_count + 1) * 0.1)

        return round(score, 3)
    except Exception:
        return 0.0


def generate_recommendations():
    """
    ينشئ أو يحدث جدول ai_recommendations في Supabase.
    """
    try:
        behaviors = read_behavior_data()
        if not behaviors:
            print("⚠️ لا توجد بيانات سلوك لتحليلها.")
            return

        for b in behaviors:

            # -------------------------------------------------------------
            # 🚫 1) تجاهل أي سجل ليس له product_id (منع الخطأ 100%)
            # -------------------------------------------------------------
            if not b.get("product_id"):
                # مثل session_start أو سلوك ليس له منتج
                continue

            user_id = b.get("user_id")
            product_id = b.get("product_id")

            score = calculate_score(
                b.get("action_score", 0),
                b.get("confidence", 0),
                b.get("views_count", 0),
                b.get("clicks_count", 0)
            )

            # تحقق إذا كانت التوصية موجودة
            existing = (
                supabase.table("ai_recommendations")
                .select("*")
                .eq("user_id", user_id)
                .eq("product_id", product_id)
                .execute()
            )

            if existing.data:
                # تحديث التوصية القديمة
                supabase.table("ai_recommendations").update({
                    "score": score,
                    "updated_at": "now()"
                }).eq("user_id", user_id).eq("product_id", product_id).execute()

            else:
                # إنشاء توصية جديدة
                supabase.table("ai_recommendations").insert({
                    "user_id": user_id,
                    "product_id": product_id,
                    "score": score,
                    "notes": "Generated automatically from user_behavior",
                }).execute()

        print("✅ تم إنشاء أو تحديث توصيات الذكاء بنجاح.")

    except Exception as e:
        print(f"❌ خطأ أثناء إنشاء التوصيات: {e}")


if __name__ == "__main__":
    generate_recommendations()
