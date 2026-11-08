import os
import re
import time
import uuid
import hmac
import json
import hashlib
import logging

import requests
from fastapi import FastAPI, APIRouter, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mustafa-api")

app = FastAPI(title="Mustafa Soft API")


# ---------------------------------------------------------------
# الإعدادات (Environment Variables في Vercel)
# ---------------------------------------------------------------
def env(name, default=""):
    return (os.getenv(name) or default).strip()


def env_float(name, default):
    try:
        return float(env(name, str(default)))
    except ValueError:
        return float(default)


def env_json(name, default):
    raw = env(name)
    if not raw:
        return default
    try:
        val = json.loads(raw)
        return val if val else default
    except ValueError:
        log.warning("invalid JSON in %s", name)
        return default


GALLE_URL = env("GALLE_API_URL").rstrip("/")
GALLE_KEY = next(
    (v for v in (env("GALLE_API_TOK"), env("GALLE_API_TOKEN"), env("GALLE_TOKEN")) if v),
    "",
)
GALLE_PRODUCTS_PATH = env("GALLE_PRODUCTS_PATH", "/products")
GALLE_ORDER_PATH = env("GALLE_ORDER_PATH", "/orders")
ADMIN_SECRET = env("ADMIN_SECRET")
ALLOWED_ORIGIN = env("ALLOWED_ORIGIN", "https://mustafa-soft.com").rstrip("/")

UP_URL = env("UPSTASH_REDIS_REST_URL").rstrip("/")
UP_TOKEN = env("UPSTASH_REDIS_REST_TOKEN")
REDIS = bool(UP_URL and UP_TOKEN)

TG_TOKEN = env("TELEGRAM_BOT_TOKEN")
TG_CHAT = env("TELEGRAM_CHAT_ID")

MARKUP_FIXED = env_float("MARKUP_FIXED", 0)
MARKUP_TIERS = env_json("MARKUP_TIERS", [[2, 35], [10, 20], [30, 12], [1e12, 8]])
MARKUP_CATEGORIES = env_json("MARKUP_CATEGORIES", {})
TIME_OVERRIDES = env_json("TIME_OVERRIDES", {})
TIME_RULES = env_json(
    "TIME_RULES",
    [[["honor frp", "offline) fast"], "1-7 ساعات (قد تتأخر بعض الحالات)"]],
)

# السماح بالدومين مع www وبدونه
_origins = {ALLOWED_ORIGIN}
if "://www." in ALLOWED_ORIGIN:
    _origins.add(ALLOWED_ORIGIN.replace("://www.", "://"))
else:
    _origins.add(ALLOWED_ORIGIN.replace("://", "://www.", 1))

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(_origins),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)


# ---------------------------------------------------------------
# التخزين (Upstash Redis، أو الذاكرة لو مش متضبط)
# ---------------------------------------------------------------
HKEY = "ms:o"
_mem_orders = {}
_mem_hits = {}
_mem_locks = {}
_cache = {}
CACHE_TTL = 300


def _redis(cmd):
    r = requests.post(
        UP_URL,
        json=cmd,
        headers={"Authorization": f"Bearer {UP_TOKEN}"},
        timeout=8,
    )
    r.raise_for_status()
    return r.json().get("result")


def rcall(cmd):
    try:
        return _redis(cmd)
    except Exception as e:
        log.error("redis error: %s", e)
        raise HTTPException(status_code=503, detail="Storage unavailable")


def order_get(ref):
    if not REDIS:
        return _mem_orders.get(ref)
    raw = rcall(["HGET", HKEY, ref])
    return json.loads(raw) if raw else None


def order_set(o):
    if not REDIS:
        _mem_orders[o["ref"]] = o
        return
    rcall(["HSET", HKEY, o["ref"], json.dumps(o, ensure_ascii=False)])


def order_all():
    if not REDIS:
        return list(_mem_orders.values())
    res = rcall(["HGETALL", HKEY]) or []
    return [json.loads(v) for v in res[1::2]]


def lock(key, ttl):
    if not REDIS:
        now = time.time()
        if _mem_locks.get(key, 0) > now:
            return False
        _mem_locks[key] = now + ttl
        return True
    return rcall(["SET", f"ms:lock:{key}", "1", "NX", "EX", str(ttl)]) == "OK"


def unlock(key):
    if not REDIS:
        _mem_locks.pop(key, None)
        return
    try:
        _redis(["DEL", f"ms:lock:{key}"])
    except Exception:
        pass


def rate_ok(ip, limit=30):
    """الحد الأقصى للطلبات في الساعة لكل IP. لو Redis وقع نسمح بدل ما نوقف الموقع."""
    if REDIS:
        try:
            k = f"ms:rl:{ip}"
            _redis(["SET", k, "0", "EX", "3600", "NX"])
            return int(_redis(["INCR", k])) <= limit
        except Exception as e:
            log.error("rate limit redis error: %s", e)
            return True
    now = time.time()
    hits = [t for t in _mem_hits.get(ip, []) if now - t < 3600]
    ok = len(hits) < limit
    hits.append(now)
    _mem_hits[ip] = hits
    return ok


def client_ip(request: Request):
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------
# الحماية
# ---------------------------------------------------------------
def require_admin(x_admin_key: str = Header("")):
    key = x_admin_key.strip()
    if not ADMIN_SECRET or not hmac.compare_digest(key.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------
# الاتصال بالمورد GalleUnlockers
# ---------------------------------------------------------------
def galle(method, path, params=None, body=None, timeout=25):
    if not GALLE_KEY or not GALLE_URL:
        raise HTTPException(status_code=503, detail="Supplier not configured")
    try:
        r = requests.request(
            method,
            f"{GALLE_URL}{path}",
            headers={"Authorization": f"Bearer {GALLE_KEY}", "Accept": "application/json"},
            params=params,
            json=body,
            timeout=timeout,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Provider unreachable")
    try:
        data = r.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail=f"Provider returned HTTP {r.status_code} (not JSON)",
        )
    if r.status_code >= 400 or (isinstance(data, dict) and data.get("status") == "error"):
        msg = data.get("message") if isinstance(data, dict) else None
        raise HTTPException(
            status_code=r.status_code if r.status_code >= 400 else 400,
            detail=msg or "Provider error",
        )
    return data


def products_raw(product_id=None):
    key = product_id or "all"
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]

    data = None
    if REDIS and not product_id:
        try:
            raw = _redis(["GET", "ms:products"])
            if raw:
                data = json.loads(raw)
        except Exception:
            data = None

    if data is None:
        path = f"{GALLE_PRODUCTS_PATH}/{product_id}" if product_id else GALLE_PRODUCTS_PATH
        data = galle("GET", path)
        if REDIS and not product_id:
            try:
                _redis(["SET", "ms:products", json.dumps(data), "EX", str(CACHE_TTL)])
            except Exception:
                pass

    _cache[key] = (now, data)
    return data


# ---------------------------------------------------------------
# تجهيز المنتجات (الأسعار + المدة)
# ---------------------------------------------------------------
def _pick(d, *names, default=None):
    for n in names:
        for k in (n, n.lower(), n.upper()):
            if k in d and d[k] not in (None, ""):
                return d[k]
    return default


def _extract_list(data):
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for k in ("data", "products", "services", "result", "SUCCESS"):
            if k in data:
                return _extract_list(data[k])
        out = []
        for v in data.values():
            if isinstance(v, (list, dict)):
                out.extend(_extract_list(v))
        return out
    return []


def markup_price(cost, category=""):
    pct = None
    if category and category in MARKUP_CATEGORIES:
        pct = float(MARKUP_CATEGORIES[category])
    else:
        for limit, p in MARKUP_TIERS:
            if cost <= float(limit):
                pct = float(p)
                break
        if pct is None:
            pct = 8.0
    return round(cost * (1 + pct / 100) + MARKUP_FIXED, 2)


def time_text(pid, name, original):
    if str(pid) in TIME_OVERRIDES:
        return TIME_OVERRIDES[str(pid)]
    low = (name or "").lower()
    for keywords, text in TIME_RULES:
        if any(k in low for k in keywords):
            return text
    return original or ""


def normalize(p):
    pid = _pick(p, "id", "serviceid", "product_id")
    name = _pick(p, "name", "servicename", "title", default="")
    category = _pick(p, "category", "groupname", "group", default="")
    try:
        cost = float(_pick(p, "price", "credit", "cost", default=0))
    except (TypeError, ValueError):
        cost = 0.0
    return {
        "id": str(pid),
        "name": name,
        "category": category,
        "description": _pick(p, "description", "info", default=""),
        "cost": cost,
        "price": markup_price(cost, category),
        "time": time_text(pid, name, _pick(p, "time", "delivery_time", default="")),
    }


def catalog():
    items = [normalize(p) for p in _extract_list(products_raw())]
    return [i for i in items if i["id"] and i["id"] != "None"]


# ---------------------------------------------------------------
# إشعارات تيليجرام
# ---------------------------------------------------------------
def notify(text):
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": text},
            timeout=6,
        )
    except Exception as e:
        log.warning("telegram failed: %s", e)


# ---------------------------------------------------------------
# الـ Endpoints (تشتغل على / وعلى /api)
# ---------------------------------------------------------------
router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OrderIn(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=64)
    email: str = Field(..., min_length=5, max_length=120)
    quantity: int = Field(1, ge=1, le=1)


@router.get("/health")
def health():
    return {
        "ok": True,
        "redis": REDIS,
        "supplier": bool(GALLE_URL and GALLE_KEY),
        "telegram": bool(TG_TOKEN and TG_CHAT),
    }


@router.get("/products")
def list_products():
    items = catalog()
    # لا نكشف سعر التكلفة للزوار
    return [{k: v for k, v in i.items() if k != "cost"} for i in items]


@router.post("/order")
def create_order(body: OrderIn, request: Request):
    ip = client_ip(request)
    if not rate_ok(ip):
        raise HTTPException(status_code=429, detail="Too many requests, try later")

    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Invalid email")

    product = next((p for p in catalog() if p["id"] == body.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # منع التكرار (نفس الإيميل ونفس المنتج خلال دقيقة)
    dedupe = hashlib.sha1(f"{email}|{product['id']}".encode()).hexdigest()
    if not lock(dedupe, 60):
        raise HTTPException(status_code=409, detail="Duplicate order, wait a minute")

    ref = uuid.uuid4().hex[:12]
    try:
        # عدّل المسار/الحقول هنا حسب توثيق المورد لو مختلفة
        supplier = galle(
            "POST",
            GALLE_ORDER_PATH,
            body={"product_id": product["id"], "email": email, "reference": ref},
        )
    except HTTPException:
        unlock(dedupe)
        raise

    order = {
        "ref": ref,
        "product_id": product["id"],
        "product": product["name"],
        "email": email,
        "price": product["price"],
        "cost": product["cost"],
        "status": "pending",
        "ip": ip,
        "created": int(time.time()),
        "supplier": supplier,
    }
    try:
        order_set(order)
    except HTTPException:
        log.error("order %s sent to supplier but storage failed", ref)

    notify(f"طلب جديد {ref}\n{product['name']}\n{email}\n${product['price']}")
    return {"ok": True, "ref": ref, "price": product["price"]}


@router.get("/order/{ref}")
def order_status(ref: str):
    o = order_get(ref)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return {k: o.get(k) for k in ("ref", "product", "status", "price", "created")}


@router.get("/admin/orders", dependencies=[Depends(require_admin)])
def admin_orders():
    orders = order_all()
    orders.sort(key=lambda o: o.get("created", 0), reverse=True)
    return orders


@router.get("/debug/raw")
def debug_raw(k: str = "", path: str = ""):
    """تشخيص مؤقت: افتحه هكذا /debug/raw?k=ADMIN_SECRET&path=/products
    احذفه بعد ما تنتهي من الضبط."""
    if not ADMIN_SECRET or not hmac.compare_digest(k.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")
    p = path or GALLE_PRODUCTS_PATH
    if not p.startswith("/"):
        p = "/" + p
    try:
        data = galle("GET", p)
    except HTTPException as e:
        return {"path": p, "error": e.status_code, "detail": e.detail}
    text = json.dumps(data, ensure_ascii=False)
    return {
        "path": p,
        "type": type(data).__name__,
        "keys": list(data.keys())[:20] if isinstance(data, dict) else None,
        "length": len(text),
        "sample": text[:1200],
    }


app.include_router(router)
app.include_router(router, prefix="/api")
