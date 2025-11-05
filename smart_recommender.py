from SPS import run_sql
import time
import random
from datetime import datetime, timedelta

print("🤖 النظام الذكي التجريبي بدأ المراقبة والترشيح الديناميكي ...")

INTERVAL = 15  # عدد الثواني بين كل تحديث
last_check = datetime.utcnow() - timedelta(seconds=INTERVAL)

while True:
    try:
        # الخطوة 1️⃣: جلب أحدث سلوك جديد
        q_behavior = f"""
        SELECT *
        FROM user_behavior
        WHERE created_at > '{last_check.isoformat()}'
        ORDER BY created_at DESC;
        """
        behaviors = run_sql(q_behavior) or []

        if behaviors:
            print(f"🟢 تم العثور على {len(behaviors)} سلوك جديد.")
            for b in behaviors:
                user_id = b['user_id']
                section_id = b['section_id']
                product_id = b['product_id']
                base_score = float(b.get('action_score') or 0.5)

                # الخطوة 2️⃣: اختيار منتجات مختلفة كل مرة للمستخدم
                q_products = f"""
                SELECT id, name, price, image, section_id
                FROM smart_products_view
                WHERE is_active = true
                  AND section_id = '{section_id}'
                  AND id != '{product_id}'
                ORDER BY RANDOM()
                LIMIT 5;
                """
                products = run_sql(q_products) or []

                if not products:
                    print(f"⚠️ لا توجد منتجات متاحة للقسم {section_id}")
                    continue

                print(f"✨ ترشيح منتجات جديدة للمستخدم {user_id} من القسم {section_id}:")
                for p in products:
                    new_score = round(base_score * random.uniform(0.4, 1.0), 2)
                    reason = f"نظام تجريبي: ترشيح ديناميكي - {p['name']}"
                    q_insert = f"""
                    INSERT INTO user_recommendations (user_id, product_id, section_id, reason, score, created_at)
                    VALUES ('{user_id}', '{p['id']}', '{section_id}', '{reason}', {new_score}, now());
                    """
                    run_sql(q_insert)
                    print(f"  ✅ رشّح المنتج {p['id']} ({p['name']}) بدرجة {new_score}")

                    # الخطوة 3️⃣: تحديث نقاط المنتج الذكي
                    q_update = f"""
                    UPDATE smart_products_view
                    SET recommendation_score = COALESCE(recommendation_score,0) + {new_score},
                        smart_rank = ROUND((COALESCE(recommendation_score,0)+{new_score})/10, 2),
                        is_recommended = true,
                        updated_at = now()
                    WHERE id = '{p['id']}';
                    """
                    run_sql(q_update)

                print("🔁 تم إنشاء ترشيحات مختلفة ومحدثة لهذا المستخدم.\n")

        else:
            print("... لا توجد تفاعلات جديدة حالياً")

        # الخطوة 4️⃣: تحديث وقت المراقبة
        last_check = datetime.utcnow()
        time.sleep(INTERVAL)

    except Exception as e:
        print("❌ خطأ أثناء التنفيذ:", e)
        time.sleep(10)
