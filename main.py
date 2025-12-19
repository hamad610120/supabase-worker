# ===============================
#  main.py
#  Full Intelligent Engine
#  By ChatGPT for Hamad
# ===============================

import time
import traceback
import socket
from threading import Thread
from multiprocessing import Process
import psycopg2
from psycopg2.extras import RealDictCursor

import SPS   # اتصال Supabase REST API

print("🚀 MAIN ENGINE STARTED…" )


# ===============================
# 1) IPv4 FIX for Render Worker
# ===============================
def force_ipv4(host):
    """Resolve Supabase host to IPv4 ONLY."""
    result = socket.getaddrinfo(host, None, socket.AF_INET)
    return result[0][4][0]


HOST = force_ipv4("db.xnyzgnfiqczxlzuocttt.supabase.co")
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "HAMAD@0096626148759610120"
DB_PORT = 5432


# ===============================
# 2) Direct PostgreSQL Connection
# ===============================
def pg_conn():
    return psycopg2.connect(
        host=HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        sslmode="require"
    )


# =========================================
# 3) EXECUTE AI_DYNAMIC_ENGINE SQL JOB
# =========================================
def execute_sql_job(job):
    sql = job["action_sql"]
    name = job["rule_name"]

    try:
        conn = pg_conn()
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()

        print(f"✔ SQL DONE: {name}")

    except Exception as e:
        print(f"❌ SQL ERROR in {name} → {e}")


# =========================================
# 4) READ + RUN ALL SQL JOBS (MULTI-PROCESS)
# =========================================
def run_dynamic_engine():
    try:
        conn = pg_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT *
            FROM ai_dynamic_engine
            WHERE enabled = TRUE
            ORDER BY run_order ASC;
        """)

        jobs = cur.fetchall()

        cur.close()
        conn.close()

        # تشغيل كل وظيفة في Process مستقل
        for job in jobs:
            p = Process(target=execute_sql_job, args=(job,))
            p.start()

    except Exception as e:
        print("❌ Dynamic Engine ERROR:", e)


# =========================================
# 5) LOAD & EXECUTE PYTHON MODULES (PLUGINS)
# =========================================
def load_and_run_modules():
    try:
        supa = SPS.db()

        modules = (
            supa.table("python_modules")
                .select("*")
                .eq("active", True)
                .order("sort_order")
                .execute()
                .data
        )

        print(f"\n🟦 Loading {len(modules)} Python modules…")

        for module in modules:
            name = module["filename"]
            code = module["code"]

            print(f"▶ Running module: {name}")

            try:
                exec(code, globals())
                print(f"✔ MODULE EXECUTED: {name}\n")

            except Exception:
                print(f"❌ ERROR in module {name}:")
                print(traceback.format_exc())

    except Exception as e:
        print("❌ Module Loader ERROR:", e)


# =========================================
# 6) THREAD LOOP → python_modules
# =========================================
def python_modules_loop():
    while True:
        load_and_run_modules()
        time.sleep(3)   # تحديث الموديولات كل 3 ثواني


# =========================================
# 7) THREAD LOOP → ai_dynamic_engine
# =========================================
def dynamic_engine_loop():
    while True:
        run_dynamic_engine()
        time.sleep(0.5)   # ← السرعة التي طلبتها


# =========================================
# 8) START THREADS
# =========================================
if __name__ == "__main__":
    print("🔥 Engine is running with Multi-Process + Multi-Thread…\n")

    Thread(target=python_modules_loop, daemon=True).start()
    Thread(target=dynamic_engine_loop, daemon=True).start()

    # Keep engine alive
    while True:
        time.sleep(1)