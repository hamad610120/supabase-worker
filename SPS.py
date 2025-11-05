import psycopg2
import psycopg2.extras

def run_sql(query):
    conn = psycopg2.connect(
        host="db.xnyzgnfiqczxlzuocttt.supabase.co",
        database="postgres",
        user="postgres",
        password="HAMAD@0096626148759610120",   # ← ضع هنا كلمة المرور التي نسختها من الصورة
        port="5432"
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    if query.strip().lower().startswith("select"):
        result = cur.fetchall()
    else:
        conn.commit()
        result = None
    cur.close()
    conn.close()
    return result

print("✅ Connected successfully")
