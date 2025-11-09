# SPS.py
import psycopg2
import psycopg2.extras

# إنشاء الاتصال بقاعدة البيانات مرة واحدة فقط
conn = psycopg2.connect(
    host="db.xnyzgnfiqczxlzuocttt.supabase.co",
    database="postgres",
    user="postgres",
    password="HAMAD@0096626148759610120",
    port="5432"
)

# تفعيل القواميس عند القراءة (نتائج منظمة)
conn.autocommit = True

print("✅ Connected successfully")
