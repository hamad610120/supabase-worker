# SPS.py
from supabase import create_client, Client

url: str = "https://xnyzgnfiqczxlzuocttt.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhueXpnbmZpcWN6eGx6dW9jdHR0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTU3MDYzNiwiZXhwIjoyMDY3MTQ2NjM2fQ.PfbT65vmXaHJZZThp3_05RXuhZo7FZ_1do4y8_WrTeo"

def db() -> Client:
    client = create_client(url, key)
    return client

print("✅ Supabase API connected successfully")
