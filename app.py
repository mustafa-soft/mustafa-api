import os
import json
import time
import hmac
import html

import requests
from fastapi import FastAPI, Query, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(title="Mustafa Soft API")

# ---------------------------------------------------------------
# الإعدادات (كلها من Environment Variables في Render)
# ---------------------------------------------------------------
USERNAME = os.getenv("LEGACY_USERNAME", "")
API_KEY = (
    os.getenv("GALLE_API_TOK")
    or os.getenv("GALLE_API_TOKEN")
    or os.getenv("GALLE_TOKEN")
    or ""
)
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://mustafa-soft.com")
LEGACY_BASE = "https://galleunlock.legacy-api.io"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)


# ---------------------------------------------------------------
# الحماية: أي endpoint حساس يطلب هيدر X-Admin-Key
# ---------------------------------------------------------------
def require_admin(x_admin_key: str = Header("")):
    if not ADMIN_SECRET or not hmac.compare_digest(x_admin_key, ADMIN_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------
# الاتصال بالمزوّد
# ---------------------------------------------------------------
def call_legacy(action, extra=None):
    if not USERNAME or not API_KEY:
        raise HTTPException(status_code=503, detail="Server is not configured")

    params = {"username": USERNAME, "key": API_KEY, "action": action}
    if extra:
        params.update(extra)

    try:
        r = requests.get(LEGACY_BASE, params=params, timeout=20)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Provider unreachable")

    try:
        return r.json()
    except ValueError:
        return {"raw": r.text[:2000], "http": r.status_code}


# كاش بسيط للخدمات (5 دقائق) لتقليل الطلبات وتسريع الصفحة
_cache = {}
CACHE_TTL = 300


def cached_call(action):
    now = time.time()
    hit = _cache.get(action)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    data = call_legacy(action)
    _cache[action] = (now, data)
    return data


# ---------------------------------------------------------------
# الصفحات والـ Endpoints
# ---------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html dir="rtl" style="font-family: Cairo, sans-serif; background:#0f172a; color:white; text-align:center; padding:30px;">
    <h1>Mustafa Soft API</h1>
    <p style="color:#22c55e;">السيرفر شغال</p>
    <div style="background:#1e293b; padding:20px; border-radius:12px; margin:20px;">
        <p><a href="/health" style="color:#38bdf8;">/health - حالة الاتصال</a></p>
        <p><a href="/products-view" style="color:#facc15;">/products-view - عرض الخدمات</a></p>
    </div>
    </html>
    """


@app.get("/health")
def health():
    return {
        "server": "ok",
        "configured": bool(USERNAME and API_KEY),
        "admin_protected": bool(ADMIN_SECRET),
    }


@app.get("/account", dependencies=[Depends(require_admin)])
def account():
    return call_legacy("accountinfo")


@app.get("/products")
def products():
    return {
        "imei_services": cached_call("imeiservicelist"),
        "server_services": cached_call("serverservicelist"),
    }


@app.get("/products-view", response_class=HTMLResponse)
def products_view():
    data = {
        "imei": cached_call("imeiservicelist"),
        "server": cached_call("serverservicelist"),
    }
    text = json.dumps(data, ensure_ascii=False, indent=2)[:8000]
    safe = html.escape(text)  # يمنع ثغرة XSS
    return f"""
    <html dir="rtl" style="font-family: sans-serif; background:#0f172a; color:white; padding:20px;">
    <h1 style="text-align:center;">خدمات Mustafa Soft</h1>
    <pre style="background:#1e293b; padding:20px; overflow:auto; text-align:left; direction:ltr;">{safe}</pre>
    </html>
    """


@app.post("/order", dependencies=[Depends(require_admin)])
def order(
    imei: str = Query(..., pattern=r"^\d{15}$"),
    service_id: str = Query(..., pattern=r"^\d{1,10}$"),
):
    return call_legacy("placeimeiorder", {"serviceid": service_id, "imei": imei})
