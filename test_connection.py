import os
from supabase import create_client, Client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ Missing environment variables.")
else:
    try:
        supabase: Client = create_client(url, key)
        data = supabase.table("user_behavior").select("*").limit(1).execute()
        print("✅ Connected successfully to Supabase!")
        print(f"✅ Fetched rows: {len(data.data)}")
    except Exception as e:
        print("❌ Connection failed:")
        print(str(e))
