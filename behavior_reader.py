# behavior_reader.py
from SPS import conn

def read_behavior_data():
    """
    يقرأ بيانات المستخدمين من جدول user_behavior خلال آخر 24 ساعة فقط.
    ويعيدها على شكل قائمة من القواميس (dictionaries).
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, product_id, section_id, action_type,
                   action_value, action_score, confidence, created_at, updated_at
            FROM user_behavior
            WHERE created_at >= NOW() - INTERVAL '1 DAY'
            ORDER BY created_at DESC;
        """)
        rows = cursor.fetchall()

        # تحويل النتائج إلى قائمة قواميس
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        return data

    except Exception as e:
        print(f"❌ خطأ أثناء قراءة جدول السلوك: {e}")
        return []
