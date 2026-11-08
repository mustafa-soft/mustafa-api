import os
import time
import uuid
import hmac
import base64
import json
import re
import zlib
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
# الإعدادات (كلها من Environment Variables في Vercel)
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

# ---------------------------------------------------------------
# الموردين: لعرض الرصيد لكل مورد في لوحة الإدارة
# key_env: اسم متغير المفتاح الأساسي
# alt_key_envs: أسماء بديلة للمفتاح (يتم تجربتها بالترتيب)
# user_env: متغير اسم المستخدم (اختياري)
# ---------------------------------------------------------------
SUPPLIERS = [
    {
        "name": "GalleUnlockers",
        "url_env": "GALLE_API_URL",
        "key_env": "GALLE_API_TOK",
        "alt_key_envs": ["GALLE_API_TOKEN", "GALLE_TOKEN"],
        "user_env": None,
    },
    {
        "name": "imei-unlock.net",
        "url_env": "IMEI_UNLOCK_API_URL",
        "key_env": "IMEI_UNLOCK_API_KEY",
        "alt_key_envs": [],
        "user_env": "IMEI_UNLOCK_USERNAME",
    },
]

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
# الاتصال بالمزوّد (Dhru Fusion Pro Reseller API) - GalleUnlockers
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


def supplier_balance(s):
    """يجيب رصيد مورد واحد. لو فشل يرجّع خطأ بدل ما يوقف اللوحة كلها."""
    base = (os.getenv(s["url_env"]) or "").rstrip("/")
    key = next(
        (
            (os.getenv(n) or "").strip()
            for n in [s["key_env"]] + s.get("alt_key_envs", [])
            if (os.getenv(n) or "").strip()
        ),
        "",
    )
    if not base or not key:
        return {"error": "غير مضبوط في Vercel"}
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    params = None
    if s.get("user_env"):
        user = (os.getenv(s["user_env"]) or "").strip()
        if not user:
            return {"error": f"{s['user_env']} غير مضبوط"}
        params = {"username": user}  # عدّلها حسب وثائق المورد
    try:
        r = requests.get(f"{base}/account", headers=headers, params=params, timeout=10)
        data = r.json()
    except Exception:
        return {"error": "تعذر الاتصال بالمورد"}
    if r.status_code >= 400 or (isinstance(data, dict) and data.get("status") == "error"):
        msg = data.get("message") if isinstance(data, dict) else None
        return {"error": msg or f"HTTP {r.status_code}"}
    d = data.get("data", data) if isinstance(data, dict) else {}
    return {"balance": d.get("balance"), "currency": d.get("currency")}


# كاش بسيط للمنتجات (5 دقائق)
_cache = {}
CACHE_TTL = 300


def cached_products(product_id=None):
    key = f"products:{product_id or 'all'}"
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    data = None
    if REDIS and not product_id:
        try:
            raw = _redis(["GET", "ms:products"])
            if raw:
                data = json.loads(zlib.decompress(base64.b64decode(raw)))
        except Exception:
            data = None
    if data is None:
        params = {"product_id": product_id} if product_id else None
        data = call_api("GET", "/products", params=params)
        if REDIS and not product_id:
            try:
                blob = base64.b64encode(zlib.compress(json.dumps(data, ensure_ascii=False).encode(), 6)).decode()
                _redis(["SET", "ms:products", blob, "EX", str(CACHE_TTL)])
            except Exception:
                pass
    _cache[key] = (now, data)
    return data


# ---------------------------------------------------------------
# الكتالوج العام (بأسعار البيع فقط، بدون سعر الجملة)
# ---------------------------------------------------------------
def _json_env(name, default):
    try:
        return json.loads(os.getenv(name) or "") or default
    except ValueError:
        return default


# شرائح الهامش حسب تكلفة الوحدة: [[الحد الأعلى للتكلفة، نسبة الربح %]]
MARKUP_TIERS = _json_env("MARKUP_TIERS", [[2, 35], [10, 20], [30, 12], [1e12, 8]])
# استثناء لأقسام معينة (رقم القسم: نسبة). مثال: {"C1946": 15}
MARKUP_CATEGORIES = _json_env("MARKUP_CATEGORIES", {})
# نص مدة مخصص لخدمات معينة (رقم الخدمة: نص)
TIME_OVERRIDES = _json_env("TIME_OVERRIDES", {})
# قواعد مدة حسب الاسم (كل الكلمات يجب أن توجد في اسم الخدمة): [[كلمات], نص]
TIME_RULES = _json_env(
    "TIME_RULES",
    [[["honor frp", "offline) fast"], "1-7 ساعات (قد تتأخر بعض الحالات)"]],
)


def rule_time(name):
    n = (name or "").lower()
    for kws, text in TIME_RULES:
        if all(k.lower() in n for k in kws):
            return text
    return None


def sale_price(cost, cid=None):
    try:
        c = float(cost)
    except (TypeError, ValueError):
        return None
    pct = MARKUP_CATEGORIES.get(str(cid))
    if pct is None:
        pct = MARKUP_TIERS[-1][1]
        for limit, p in MARKUP_TIERS:
            if c < float(limit):
                pct = p
                break
    return round(c * (1 + float(pct) / 100.0) + MARKUP_FIXED, 2)


def build_catalog():
    raw = cached_products()
    data = raw.get("data") if isinstance(raw, dict) else None
    data = data or {}
    categories = data.get("categories") or {}
    currency = data.get("currency")
    items = []
    for pid, p in (data.get("products") or {}).items():
        price = sale_price(p.get("price"), p.get("cid"))
        if price is None:
            continue
        cid = p.get("cid")
        fields = [
            {k: f[k] for k in ("type", "name", "required", "min", "max") if k in f}
            for f in (p.get("fields") or [])
            if isinstan
