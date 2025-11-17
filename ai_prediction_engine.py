# ai_prediction_engine.py
from SPS import supabase
from datetime import datetime, timedelta, UTC
import uuid
import json
from collections import defaultdict

# ============================================================
# =============== 1. قراءة بيانات السلوك ======================
# ============================================================

def read_behavior(hours=24):
    cutoff_time = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
    response = (
        supabase.table("user_behavior")
        .select("*")
        .gte("created_at", cutoff_time)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


# ============================================================
# =============== 2. دالة عامة لكتابة التوقع =================
# ============================================================

def write_prediction(user_id, prediction_type, score, title, reason, product_id=None, section_id=None, metadata=None):

    payload = {
        "user_id": user_id,
        "product_id": product_id,
        "section_id": section_id,
        "prediction_type": prediction_type,
        "prediction_score": score,
        "prediction_title": title,
        "reason": reason,
        "metadata": metadata or {},
    }

    supabase.table("model_predictions").insert(payload).execute()



# ============================================================
# =============== 3. توقعات الاهتمام Interest ===============
# ============================================================

def interest_predictions(behaviors_by_user):

    for user_id, records in behaviors_by_user.items():

        section_interest = defaultdict(float)
        product_interest = defaultdict(float)

        for r in records:
            section_id = r["section_id"]
            product_id = r["product_id"]
            action = r["notes"]
            total = float(r.get("total_score", 0))

            if action == "click":
                score = 0.9
            elif action == "view_start":
                score = 0.5
            else:
                score = 0.3

            # تراكم الاهتمام
            section_interest[section_id] += score
            product_interest[product_id] += score

        # كتابة قسم
        for section_id, score in section_interest.items():
            write_prediction(
                user_id,
                "Interest_Section",
                min(score, 1.0),
                f"اهتمام عالي بالقسم {section_id}",
                "تحليل سلوك المستخدم",
                section_id=section_id
            )

        # كتابة منتج
        for product_id, score in product_interest.items():
            write_prediction(
                user_id,
                "Interest_Product",
                min(score, 1.0),
                f"اهتمام عالي بالمنتج {product_id}",
                "تحليل سلوك المستخدم",
                product_id=product_id
            )



# ============================================================
# =============== 4. توقعات الشراء Purchase ==================
# ============================================================

def purchase_predictions(behaviors_by_user):

    for user_id, records in behaviors_by_user.items():
        for r in records:

            action = r["notes"]
            product_id = r["product_id"]
            section_id = r["section_id"]

            if action == "purchase":
                write_prediction(
                    user_id, "Purchase_Now", 1.0,
                    "المستخدم قام بالشراء",
                    "سلوك شراء فعلي",
                    product_id=product_id,
                    section_id=section_id
                )

            elif action == "cart":
                write_prediction(
                    user_id, "Purchase_Intent", 0.8,
                    "احتمالية شراء عالية",
                    "المستخدم أضاف المنتج للسلة",
                    product_id=product_id
                )

            elif action == "click":
                write_prediction(
                    user_id, "Purchase_Possible", 0.6,
                    "احتمال شراء متوسط",
                    "ضغط المستخدم على المنتج",
                    product_id=product_id
                )

            elif action == "view_start":
                write_prediction(
                    user_id, "Purchase_Low", 0.3,
                    "احتمال شراء منخفض",
                    "مشاهدة فقط",
                    product_id=product_id
                )



# ============================================================
# =============== 5. توقعات التجاهل Ignore ===================
# ============================================================

def ignore_predictions(behaviors_by_user):
    for user_id, records in behaviors_by_user.items():

        view_counts = defaultdict(int)
        click_counts = defaultdict(int)

        for r in records:
            product_id = r["product_id"]
            action = r["notes"]

            if action == "view_start":
                view_counts[product_id] += 1
            if action == "click":
                click_counts[product_id] += 1

        for product_id, views in view_counts.items():
            clicks = click_counts.get(product_id, 0)

            if views >= 3 and clicks == 0:
                write_prediction(
                    user_id, "Ignore", 0.9,
                    "المستخدم تجاهل المنتج رغم كثرة المشاهدات",
                    "مشاهدات عالية بدون أي تفاعل",
                    product_id=product_id
                )



# ============================================================
# =============== 6. توقعات الارتداد Return ==================
# ============================================================

def return_predictions(behaviors_by_user):

    for user_id, records in behaviors_by_user.items():

        watch_times = defaultdict(int)
        for r in records:
            product_id = r["product_id"]
            action = r["notes"]

            if action == "view_start":
                watch_times[product_id] += 1

        for product_id, count in watch_times.items():
            if count >= 2:
                write_prediction(
                    user_id, "Return", 0.7,
                    "سيعود لهذا المنتج",
                    "تكرر المشاهدة",
                    product_id=product_id
                )



# ============================================================
# =============== 7. التوقعات السلوكية Behavior ==============
# ============================================================

def behavior_predictions(behaviors_by_user):

    for user_id, records in behaviors_by_user.items():

        clicks = 0
        views = 0
        purchases = 0

        for r in records:
            if r["notes"] == "click": clicks += 1
            if r["notes"] == "view_start": views += 1
            if r["notes"] == "purchase": purchases += 1

        meta = {"views": views, "clicks": clicks, "purchases": purchases}

        write_prediction(
            user_id, "Behavior_Profile", 1.0,
            "ملف سلوك المستخدم",
            "تحليل عام",
            metadata=meta
        )



# ============================================================
# ======== 8. توقعات مشابهة المستخدمين Similar Users =========
# ============================================================

def similar_user_predictions(behaviors_by_user):

    # نموذج بسيط (يمكن تطويره لاحقًا)
    for user_id, records in behaviors_by_user.items():
        write_prediction(
            user_id, "Similar_Users", 0.5,
            "مستخدمون يشبهون هذا المستخدم",
            "خوارزمية مشابهة مبدئية"
        )



# ============================================================
# ======== 9. أفضل المنتجات Top-N Recommendations ============
# ============================================================

def top_n_predictions(behaviors_by_user):

    for user_id, records in behaviors_by_user.items():

        score_by_product = defaultdict(float)

        for r in records:
            product_id = r["product_id"]
            action = r["notes"]

            if action == "click":
                score_by_product[product_id] += 0.9
            elif action == "view_start":
                score_by_product[product_id] += 0.4

        # أفضل المنتجات
        top_products = sorted(score_by_product.items(), key=lambda x: x[1], reverse=True)[:10]

        for product_id, score in top_products:
            write_prediction(
                user_id, "Top_Product",
                min(score, 1.0),
                f"منتج مفضل: {product_id}",
                "أفضل 10 منتجات",
                product_id=product_id
            )



# ============================================================
# =============== 10. توقعات التفاعل Engagement ==============
# ============================================================

def engagement_predictions(behaviors_by_user):

    for user_id, records in behaviors_by_user.items():
        for r in records:
            if r["notes"] == "click":
                write_prediction(
                    user_id, "Engagement_Click", 0.8,
                    "احتمالية تفاعل قوية",
                    "ضغط المستخدم على المنتج",
                    product_id=r["product_id"]
                )



# ============================================================
# =============== 11. مستقبل المستخدم Future =================
# ============================================================

def future_predictions(behaviors_by_user):

    for user_id, records in behaviors_by_user.items():

        write_prediction(
            user_id, "Future_Interest", 0.6,
            "اهتمام جديد سيظهر قريبًا",
            "تحليل زمن التفاعل"
        )



# ============================================================
# =============== 12. المحرّك الرئيسي ========================
# ============================================================

def process_all_predictions():

    print("🔄 قراءة بيانات السلوك…")
    behaviors = read_behavior()

    # تجميع السلوك حسب المستخدم
    behaviors_by_user = defaultdict(list)
    for r in behaviors:
        behaviors_by_user[r["user_id"]].append(r)

    print("✨ بدء إنشاء التوقعات…")

    interest_predictions(behaviors_by_user)
    purchase_predictions(behaviors_by_user)
    ignore_predictions(behaviors_by_user)
    return_predictions(behaviors_by_user)
    behavior_predictions(behaviors_by_user)
    similar_user_predictions(behaviors_by_user)
    top_n_predictions(behaviors_by_user)
    engagement_predictions(behaviors_by_user)
    future_predictions(behaviors_by_user)

    print("🔥 تم إنشاء جميع التوقعات بنجاح!")


if __name__ == "__main__":
    process_all_predictions()
