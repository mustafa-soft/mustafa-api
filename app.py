from fastapi import FastAPI
import os
import requests

app = FastAPI()

GALLE_TOKEN = os.getenv("GALLE_API_TOKEN") or os.getenv("GALLE_API_TOKEN") or os.getenv("GALLE_API_TOK") 
# بنحاول نقرا اي واحد من المتغيرات الكتبتها
# الأفضل تستخدم GALLE_API_TOKEN
GALLE_URL = "https://api.galleunlockers.com"

# نحاول نقرا التوكن الصح من الصورة
for key in ["GALLE_API_TOKEN", "GALLE_API_TOK", "GALLE_API_TOK..."]:
    if os.getenv(key):
        GALLE_TOKEN = os.getenv(key)

# لو ما لقيناهو بالحلقة الفوق، استخدم المتغير الموجود
if not GALLE_TOKEN:
    GALLE_TOKEN = os.getenv("GALLE_API_TOK") or os.getenv("GALLE_API_TOKEN")

@app.get("/")
def home():
    headers = {"Authorization": f"Bearer {GALLE_TOKEN}"}
    try:
        r = requests.get(f"{GALLE_URL}/api/user/me", headers=headers, timeout=10)
        galle_ok = r.status_code == 200
        balance = r.json() if galle_ok else {}
    except:
        galle_ok = False
        balance = {}

    return {
        "status": "Running",
        "store": "mustafa-soft.com",
        "galle_connected": galle_ok,
        "tools_live": 15,
        "email_galle": "mustafaopen88@gmail.com",
        "balance_info": balance
    }

@app.get("/services")
def services():
    headers = {"Authorization": f"Bearer {GALLE_TOKEN}"}
    try:
        r = requests.get(f"{GALLE_URL}/api/services", headers=headers, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
