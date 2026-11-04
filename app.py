
from fastapi import FastAPI, Query
import os, requests

app = FastAPI()

# من صورتك
USERNAME = "mustafaopen88@gmail.com"
API_KEY = os.getenv("GALLE_API_TOK") or os.getenv("GALLE_API_TOKEN") or os.getenv("GALLE_TOKEN") or ""
# الرابط الصح من صورتك الأخيرة
LEGACY_BASE = "https://galleunlock.legacy-api.io"

# الرابط الجديد Bearer (لو عايز تجربو)
NEW_BASE = "https://api.galleunlockers.com"

@app.get("/")
def home():
    return {
        "status": "Running ✅",
        "store": "mustafa-soft.com",
        "legacy_endpoint": LEGACY_BASE,
        "username": USERNAME,
        "key_found": bool(API_KEY),
        "key_len": len(API_KEY),
        "message": "Legacy API is ready!",
        "endpoints": ["/account", "/products", "/order?imei=xxx&service_id=yyy"]
    }

def legacy_call(action, extra_params=None):
    if not API_KEY:
        return {"error": "API Key missing in Render Env GALLE_API_TOK"}
    params = {
        "username": USERNAME,
        "key": API_KEY,
        "action": action
    }
    if extra_params:
        params.update(extra_params)
    try:
        # معظم Legacy APIs بتقبل GET
        r = requests.get(LEGACY_BASE, params=params, timeout=30)
        # حاول تفسر كـ JSON
        try:
            j = r.json()
            return {"http": r.status_code, "url": r.url, "data": j}
        except:
            return {"http": r.status_code, "url": r.url, "text": r.text[:5000]}
    except Exception as e:
        return {"error": str(e), "url": LEGACY_BASE}

@app.get("/account")
def account():
    # action=accountinfo هو الصح في Legacy
    return legacy_call("accountinfo")

@app.get("/products")
@app.get("/services")
def services():
    # imeiservicelist = خدمات IMEI + Server
    # حسب README Dhru
    result = legacy_call("imeiservicelist")
    return result

@app.get("/server-services")
def server_services():
    return legacy_call("serverservicelist")

@app.get("/order")
def place_order(imei: str = Query(None), service_id: str = Query(None), serviceid: str = Query(None)):
    sid = service_id or serviceid
    if not imei or not sid:
        return {"error": "Use /order?imei=3534...&service_id=123"}
    return legacy_call("placeimeiorder", {"serviceid": sid, "imei": imei})

@app.get("/get-order")
def get_order(orderid: str = Query(None)):
    if not orderid:
        return {"error": "Use /get-order?orderid=12345"}
    return legacy_call("getimeiorder", {"orderid": orderid})

@app.get("/debug")
def debug():
    # بجرب كم action عشان نعرف الشغال
    actions = ["accountinfo", "imeiservicelist", "getservices", "services"]
    results = {}
    for act in actions:
        results[act] = legacy_call(act)
    return results
