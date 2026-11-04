from fastapi import FastAPI
import os
import requests

app = FastAPI()

# قراءة التوكن من اي متغير انت كاتبو
GALLE_TOKEN = (
    os.getenv("GALLE_API_TOKEN") or 
    os.getenv("GALLE_API_TOK") or 
    os.getenv("GALLE_API_TOK_") or
    os.getenv("GALLE_API_TOKEN_") or
    ""
)
GALLE_URL = os.getenv("GALLE_API_URL") or "https://api.galleunlockers.com"
# لو كاتب الرابط مع - 
if not GALLE_URL or "galle" not in GALLE_URL:
    GALLE_URL = os.getenv("GALLE-API-URL") or "https://api.galleunlockers.com"

@app.get("/")
def home():
    galle_ok = False
    info = {}
    if GALLE_TOKEN and len(GALLE_TOKEN) > 20:
        try:
            headers = {"Authorization": f"Bearer {GALLE_TOKEN}"}
            r = requests.get(f"{GALLE_URL}/api/user/me", headers=headers, timeout=10)
            if r.status_code == 200:
                galle_ok = True
                info = r.json()
            else:
                info = {"http_code": r.status_code, "response": r.text[:300]}
        except Exception as e:
            info = {"error": str(e)}
    else:
        info = {"error": "GALLE_TOKEN not found or too short"}

    return {
        "status": "Running",
        "store": "mustafa-soft.com",
        "galle_connected": galle_ok,
        "tools_live": 15,
        "email_galle": "mustafaopen88@gmail.com",
        "debug": info
    }

@app.get("/services")
def services():
    if not GALLE_TOKEN:
        return {"error": "Token missing"}
    try:
        headers = {"Authorization": f"Bearer {GALLE_TOKEN}"}
        r = requests.get(f"{GALLE_URL}/api/services", headers=headers, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/docs-check")
def docs_check():
    return {"message": "API is live", "token_len": len(GALLE_TOKEN) if GALLE_TOKEN else 0}
