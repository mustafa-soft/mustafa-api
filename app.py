import os
import json
import time
import uuid
import hmac
import html
import logging

import requests
from fastapi import FastAPI, Query, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

log = logging.getLogger("mustafa-api")

app = FastAPI(title="Mustafa Soft API")

# ---------------------------------------------------------------
# الإعدادات (كلها من Environment Variables في Render)
# ---------------------------------------------------------------
BASE_URL = (os.getenv("GALLE_API_URL") or "https://api.galleunlockers.com").rstrip("/")
API_TOKEN = (
    os.getenv("GALLE_API_TOK")
    or os.getenv("GALLE_API_TOKEN")
    or os.getenv("GALLE_TOKEN")
    or ""
).strip()
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://mustafa-soft.com")
# عنوان استقبال نتيجة الأوردر (لازم HTTPS). Render بيوفّر RENDER_EXTERNAL_URL تلقائيًا
PUBLIC_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)


# ---------------------------------------------------------------
# الحماية
# ---------------------------------------------------------------
def require_admin(x_admin_key: str = Header("")):
    if not ADMIN_SECRET or not hmac.compare_digest(x_admin_key, ADMIN_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------
# الاتصال بالمزوّد (Dhru Fusion Pro Reseller API)
# ---------------------------------------------------------------
def call_api(method, path, params=None, body=None, timeout=30):
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="Server is not configured")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }
    try:
        r = requests.request(
            method,
            f"{BASE_URL}{path}",
            headers=headers,
            params=params,
            json=body,
            timeout=timeout,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Provider unreachable")

    try:
        data = r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Invalid response from provider")

    # بعض أخطاء الأوردر ترجع 2xx مع status=error، فلازم نفحص الاتنين
    if r.status_code >= 400 or (isinstance(data, dict) and data.get("status") == "error"):
        message = data.get("message") if isinstance(data, dict) else None
        raise HTTPException(
            status_code=r.status_code if r.status_code >= 400 else 400,
            detail=message or "Provider error",
        )
    return data


# كاش بسيط للمنتجات (5 دقائق)
_cache = {}
CACHE_TTL = 300


def cached_products(product_id=None):
    key = f"products:{product_id or 'all'}"
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    params = {"product_id": product_id} if product_id else None
    data = call_api("GET", "/products", params=params)
    _cache[key] = (now, data)
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
        <p><a href="/health" style="color:#38bdf8;">/health - حالة الإعدادات</a></p>
        <p><a href="/products-view" style="color:#facc15;">/products-view - عرض الخدمات</a></p>
    </div>
    </html>
    """


@app.get("/health")
def health():
    return {
        "server": "ok",
        "configured": bool(API_TOKEN and BASE_URL),
        "admin_protected": bool(ADMIN_SECRET),
        "callback_ready": bool(PUBLIC_URL.startswith("https://")),
    }


@app.get("/account", dependencies=[Depends(require_admin)])
def account():
    return call_api("GET", "/account")


@app.get("/products")
def products(product_id: str | None = Query(None, pattern=r"^[0-9A-Za-z-]{1,64}$")):
    return cached_products(product_id)


@app.get("/products-view", response_class=HTMLResponse)
def products_view():
    text = json.dumps(cached_products(), ensure_ascii=False, indent=2)[:8000]
    safe = html.escape(text)  # يمنع ثغرة XSS
    return f"""
    <html dir="rtl" style="font-family: sans-serif; background:#0f172a; color:white; padding:20px;">
    <h1 style="text-align:center;">خدمات Mustafa Soft</h1>
    <pre style="background:#1e293b; padding:20px; overflow:auto; text-align:left; direction:ltr;">{safe}</pre>
    </html>
    """


class OrderIn(BaseModel):
    product_id: str = Field(pattern=r"^[0-9A-Za-z-]{1,64}$")
    imei: str = Field(pattern=r"^\d{15}$")
    quantity: int = Field(default=1, ge=1, le=100)


@app.post("/order", dependencies=[Depends(require_admin)])
def order(item: OrderIn):
    if not PUBLIC_URL.startswith("https://"):
        raise HTTPException(status_code=503, detail="PUBLIC_URL (https) is not configured")

    reference_id = "ms-" + uuid.uuid4().hex[:24]
    payload = [
        {
            "product_id": int(item.product_id) if item.product_id.isdigit() else item.product_id,
            "fields": [
                {
                    "IMEI": item.imei,
                    "feedback_url": f"{PUBLIC_URL}/callback",
                    "reference_id": reference_id,
                    "Quantity": item.quantity,
                }
            ],
        }
    ]
    result = call_api("POST", "/order", body=payload, timeout=120)
    return {"reference_id": reference_id, "result": result}


@app.get("/order-status", dependencies=[Depends(require_admin)])
def order_status(order_uuid: str = Query(..., pattern=r"^[0-9A-Za-z,-]{1,500}$")):
    return call_api("GET", "/order", params={"order_uuid": order_uuid})


@app.post("/callback")
async def callback(request: Request):
    # إشعار فقط: لا نثق فيه. تأكد من الحالة النهائية عبر /order-status قبل تسليم أي خدمة.
    try:
        data = await request.json()
        log.info("callback ref=%s status=%s", data.get("reference_id"), data.get("status"))
    except Exception:
        pass
    return {"ok": True}
