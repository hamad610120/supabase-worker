# ============================================================
#  engine.py — Ultra AI Engine
#  ذكاء صناعي خارق يتحكم بالكامل عبر جدول system_commands
# ============================================================

import time, traceback, json, uuid
from datetime import datetime, UTC
from SPS import supabase


# ============================================================
# 1) READ PENDING COMMANDS
# ============================================================

def fetch_pending_commands():
    try:
        q = (
            supabase.table("system_commands")
            .select("*")
            .eq("status", "pending")
            .order("created_at", desc=False)
            .execute()
        )
        return q.data or []
    except:
        return []


# ============================================================
# 2) UPDATE STATUS
# ============================================================

def update_status(cmd_id, status, result="", error=""):
    supabase.table("system_commands").update({
        "status": status,
        "result": result,
        "error_log": error,
        "executed_at": datetime.now(UTC).isoformat()
    }).eq("id", cmd_id).execute()


# ============================================================
# 3) EXECUTE COMMAND
# ============================================================

def execute_command(cmd):
    cmd_id = cmd["id"]
    text = cmd["command"]

    print("\n------------------------------------------------")
    print("🧠 تنفيذ أمر جديد")
    print("ID:", cmd_id)
    print("نص الأمر:", text)
    print("------------------------------------------------")

    try:
        result = process(text)
        update_status(cmd_id, "done", json.dumps(result))
        print("✔ تنفيذ ناجح")
    except Exception as e:
        update_status(cmd_id, "failed", "", traceback.format_exc())
        print("❌ فشل:", e)


# ============================================================
# 4) MAIN INTERPRETER
# ============================================================

def process(text):
    t = text.strip().lower()

    # ========================================================
    # (D) python execution
    # ========================================================
    if t.startswith("python:"):
        code = text.replace("python:", "", 1)
        return exec_python_code(code)

    # ========================================================
    # (A) SQL COMMANDS
    # ========================================================
    if "create table" in t:
        return exec_sql(text)

    if "alter table" in t:
        return exec_sql(text)

    if "drop table" in t:
        return exec_sql(text)

    if "insert into" in t:
        return exec_sql(text)

    if "truncate" in t:
        return exec_sql(text)

    if t.startswith("sql:"):
        return exec_sql(text.replace("sql:", ""))

    # ========================================================
    # (B) AI Intelligence
    # ========================================================
    if "سلوك" in t:
        return analyze_behavior()

    if "توصيات" in t:
        return generate_recommendations()

    if "عرض" in t:
        return build_smart_display()

    if "منتجات مهملة" in t:
        return detect_ignored_products()

    if "منتجات حارة" in t:
        return detect_hot_products()

    if "افضل اقسام" in t:
        return detect_top_sections()

    if "عميل خامل" in t:
        return detect_inactive_users()

    if "ملف العميل" in t:
        return customer_profile()

    # ========================================================
    # (C) SYSTEM CONTROL
    # ========================================================
    if "اعادة تشغيل" in t:
        return {"restart": True}

    if "نسخ احتياطي" in t:
        return backup_table()

    if "مسح" in t and "جدول" in t:
        return clear_table(text)

    # Default:
    return {"message": "🤖 أمر غير معروف وسيتم دعمه لاحقاً", "command": text}



# ============================================================
# A — SQL EXECUTION
# ============================================================

def exec_sql(query):
    try:
        res = supabase.rpc("exec_sql", {"query": query}).execute()
        return {"sql": "done", "query": query}
    except Exception as e:
        return {"sql_error": str(e), "query": query}


# ============================================================
# D — Python EXEC
# ============================================================

def exec_python_code(code):
    local_env = {}
    try:
        exec(code, {}, local_env)
        return {"python_result": local_env}
    except Exception as e:
        return {"python_error": str(e)}

# ============================================================
# B — AI BLOCK (placeholder)
# ============================================================

def analyze_behavior():
    return {"ai": "Behavior analyzed (placeholder)"}

def generate_recommendations():
    return {"ai": "Recommendations generated (placeholder)"}

def build_smart_display():
    return {"ai": "Smart Display built (placeholder)"}

def detect_ignored_products():
    return {"ai": "Ignored products detected"}

def detect_hot_products():
    return {"ai": "Hot products detected"}

def detect_top_sections():
    return {"ai": "Top sections detected"}

def customer_profile():
    return {"ai": "Customer profile generated"}

def detect_inactive_users():
    return {"ai": "Inactive users detected"}



# ============================================================
# LOOP
# ============================================================

def start_engine():
    print("\n🚀 Ultra AI Engine Started…")

    while True:
        commands = fetch_pending_commands()

        if commands:
            print(f"🚨 وجدنا {len(commands)} أوامر جديدة")
            for cmd in commands:
                execute_command(cmd)
        else:
            print("… لا يوجد أوامر – ننتظر")

        time.sleep(5)


if __name__ == "__main__":
    start_engine()
