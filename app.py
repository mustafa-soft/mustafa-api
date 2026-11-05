import os
import time
import uuid
import hmac
import logging

import requests
from fastapi import FastAPI, Query, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mustafa-api")

app = FastAPI(title="Mustafa Soft API")

# ---------------------------------------------------------------
# الإعدادات (كلها من Environment Variables في Render)
# ---------------------------------------------------------------
BASE_URL = (os.getenv("GALLE_API_URL") or "").rstrip("/")
API_TOKEN = (
    os.getenv("GALLE_API_TOK")
    or os.getenv("GALLE_API_TOKEN")
    or os.getenv("GALLE_TOKEN")
    or ""
).strip()
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://mustafa-soft.com")
PUBLIC_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")


def _env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return float(default)


# هامش الربح: سعر البيع = سعر الجملة × (1 + النسبة/100) + مبلغ ثابت
MARKUP_PERCENT = _env_float("MARKUP_PERCENT", "20")
MARKUP_FIXED = _env_float("MARKUP_FIXED", "0")

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
    if not API_TOKEN or not BASE_URL:
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
        log.warning("non-json from provider: %s", r.status_code)
        raise HTTPException(
            status_code=502,
            detail=f"Provider returned HTTP {r.status_code} (not JSON)",
        )

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
# الكتالوج العام (بأسعار البيع فقط، بدون سعر الجملة)
# ---------------------------------------------------------------
def sale_price(cost):
    try:
        c = float(cost)
    except (TypeError, ValueError):
        return None
    return round(c * (1 + MARKUP_PERCENT / 100.0) + MARKUP_FIXED, 2)


def build_catalog():
    raw = cached_products()
    data = raw.get("data") if isinstance(raw, dict) else None
    data = data or {}
    categories = data.get("categories") or {}
    currency = data.get("currency")
    items = []
    for pid, p in (data.get("products") or {}).items():
        price = sale_price(p.get("price"))
        if price is None:
            continue
        cid = p.get("cid")
        fields = [
            {k: f[k] for k in ("type", "name", "required", "min", "max") if k in f}
            for f in (p.get("fields") or [])
            if isinstance(f, dict)
        ]
        items.append(
            {
                "id": pid,
                "name": p.get("name"),
                "type": p.get("type"),
                "category_id": cid,
                "category": (categories.get(cid) or {}).get("name"),
                "price": price,
                "currency": currency,
                "time": p.get("time"),
                "fields": fields,
            }
        )
    return currency, items


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
        <p><a href="/catalog?limit=20" style="color:#facc15;">/catalog - كتالوج الخدمات</a></p>
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


@app.get("/catalog")
def catalog(
    q: str | None = Query(None, max_length=60),
    category_id: str | None = Query(None, pattern=r"^[0-9A-Za-z_-]{1,40}$"),
    type: str | None = Query(None, pattern=r"^[a-z]{1,20}$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    currency, items = build_catalog()
    if q:
        needle = q.lower()
        items = [i for i in items if needle in (i["name"] or "").lower()]
    if category_id:
        items = [i for i in items if i["category_id"] == category_id]
    if type:
        items = [i for i in items if i["type"] == type]
    total = len(items)
    return {
        "currency": currency,
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": items[offset : offset + limit],
    }


# ---- مسارات الإدارة (محمية) ----
@app.get("/account", dependencies=[Depends(require_admin)])
def account():
    return call_api("GET", "/account")


@app.get("/products", dependencies=[Depends(require_admin)])
def products(product_id: str | None = Query(None, pattern=r"^[0-9A-Za-z-]{1,64}$")):
    # يعرض بيانات المزوّد الخام بأسعار الجملة: للإدارة فقط
    return cached_products(product_id)


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
