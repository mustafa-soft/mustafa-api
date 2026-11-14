import os
import re
import time
import hmac
import json
import base64
import hashlib
import logging

import requests
from fastapi import FastAPI, APIRouter, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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
IU_URL = env("IMEI_UNLOCK_API_URL").rstrip("/")
IU_USER = env("IMEI_UNLOCK_USERNAME")
IU_KEY = env("IMEI_UNLOCK_API_KEY")
IU_ENABLED = bool(IU_URL and IU_USER and IU_KEY)
ADMIN_SECRET = env("ADMIN_SECRET")
ALLOWED_ORIGIN = env("ALLOWED_ORIGIN", "https://mustafa-soft.com").rstrip("/")
PUBLIC_URL = env("PUBLIC_URL").rstrip("/")
ORDER_TIMEOUT = env_float("GALLE_ORDER_TIMEOUT", 60)

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
# Redis اختياري (للكاش والقفل وحد الطلبات). بدونه يشتغل بالذاكرة.
# الطلبات نفسها ما بتتخزن: كل طلب بيوصلك على تيليجرام برمز موقّع.
# ---------------------------------------------------------------
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


def lock(key, ttl):
    if REDIS:
        try:
            return _redis(["SET", f"ms:lock:{key}", "1", "NX", "EX", str(ttl)]) == "OK"
        except Exception as e:
            log.error("redis lock error: %s", e)
    now = time.time()
    if _mem_locks.get(key, 0) > now:
        return False
    _mem_locks[key] = now + ttl
    return True


def unlock(key):
    _mem_locks.pop(key, None)
    if REDIS:
        try:
            _redis(["DEL", f"ms:lock:{key}"])
        except Exception:
            pass


def rate_ok(ip, limit=30):
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


def public_base(request: Request):
    if PUBLIC_URL:
        return PUBLIC_URL
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"https://{host}"


# ---------------------------------------------------------------
# سجل الطلبات (يحتاج Redis؛ بدونه تعمل اللوحة بالرمز فقط)
# ---------------------------------------------------------------
HKEY = "ms:o"
ORDER_CODE_RE = re.compile(r"^MS-[0-9A-F]{8}$")


def order_save(rec):
    if not REDIS:
        return
    try:
        _redis(["HSET", HKEY, rec["code"], json.dumps(rec, ensure_ascii=False)])
        _redis(["EXPIRE", HKEY, "5184000"])
    except Exception as e:
        log.error("order save failed: %s", type(e).__name__)


def order_load(code):
    if not REDIS or not ORDER_CODE_RE.match(code or ""):
        return None
    try:
        raw = _redis(["HGET", HKEY, code])
        return json.loads(raw) if raw else None
    except Exception:
        return None


def order_list():
    if not REDIS:
        return []
    try:
        res = _redis(["HGETALL", HKEY]) or []
    except Exception:
        return []
    out = []
    for v in res[1::2]:
        try:
            out.append(json.loads(v))
        except ValueError:
            pass
    out.sort(key=lambda o: o.get("t", 0), reverse=True)
    return out


# ---------------------------------------------------------------
# الحماية
# ---------------------------------------------------------------
def require_admin(x_admin_key: str = Header("")):
    key = x_admin_key.strip()
    if not ADMIN_SECRET or not hmac.compare_digest(key.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------
# Dhru Fusion Pro Reseller API
# GET /account | GET /products | POST /order | GET /order?order_uuid=
# ---------------------------------------------------------------
class OrderUnknown(Exception):
    """انقطع الاتصال أو الرد غير مفهوم أثناء إرسال طلب: النتيجة مجهولة، لا تعيد الإرسال."""


def fusion(method, path, params=None, body=None, timeout=30, write=False):
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
        if write:
            raise OrderUnknown("request failed")
        raise HTTPException(status_code=502, detail="Provider unreachable")

    try:
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except ValueError:
        if write and (r.status_code < 400 or r.status_code >= 500):
            raise OrderUnknown("invalid response")
        raise HTTPException(
            status_code=502,
            detail=f"Provider returned HTTP {r.status_code} (not JSON)",
        )

    # بعض أخطاء التحقق ترجع HTTP 201 مع status=error، فنفحص الاثنين
    if r.status_code >= 400 or data.get("status") != "success":
        code = data.get("code")
        status = r.status_code if r.status_code >= 400 else (
            code if isinstance(code, int) and code >= 400 else 400
        )
        msg = data.get("message") or "Provider error"
        headers = {}
        if r.headers.get("Retry-After"):
            headers["Retry-After"] = r.headers["Retry-After"]
        if status in (401, 402, 403):
            log.error("supplier auth/balance error: HTTP %s", status)
            raise HTTPException(
                status_code=502,
                detail=f"Supplier auth/balance error (HTTP {status}): {msg}",
            )
        raise HTTPException(status_code=status, detail=msg, headers=headers or None)
    return data


def products_raw():
    now = time.time()
    hit = _cache.get("all")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]

    data = None
    if REDIS:
        try:
            raw = _redis(["GET", "ms:products"])
            if raw:
                data = json.loads(raw)
        except Exception:
            data = None

    if data is None:
        data = fusion("GET", "/products")
        if REDIS:
            try:
                _redis(["SET", "ms:products", json.dumps(data), "EX", str(CACHE_TTL)])
            except Exception:
                pass

    _cache["all"] = (now, data)
    return data


# ---------------------------------------------------------------
# تجهيز المنتجات (الأسعار + المدة)
# ---------------------------------------------------------------
def markup_price(cost, cid="", cat_name=""):
    pct = None
    for k in (cid, cat_name):
        if k and k in MARKUP_CATEGORIES:
            pct = float(MARKUP_CATEGORIES[k])
            break
    if pct is None:
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


def catalog_galle():
    """يرجع (العملة، الأقسام، المنتجات) من رد المورد: data.products مفتاحها رقم المنتج."""
    raw = products_raw()
    d = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    cats_raw = d.get("categories") if isinstance(d.get("categories"), dict) else {}
    prods_raw = d.get("products") if isinstance(d.get("products"), dict) else {}

    categories = {}
    for cid, c in cats_raw.items():
        if isinstance(c, dict):
            categories[str(cid)] = {"id": str(cid), "name": c.get("name", ""), "type": c.get("type", "")}

    items = []
    for pid, p in prods_raw.items():
        if not isinstance(p, dict):
            continue
        cid = str(p.get("cid") or ((p.get("cids") or [""])[0]))
        cat_name = categories.get(cid, {}).get("name", "")
        try:
            cost = float(p.get("price") or 0)
        except (TypeError, ValueError):
            cost = 0.0
        fields = p.get("fields") if isinstance(p.get("fields"), list) else []
        items.append(
            {
                "id": str(pid),
                "name": p.get("name", ""),
                "type": p.get("type", ""),
                "category_id": cid,
                "category": cat_name,
                "cost": cost,
                "price": markup_price(cost, cid, cat_name),
                "time": time_text(pid, p.get("name", ""), p.get("time", "")),
                "fields": fields,
                "supplier": "galle",
            }
        )
    return d.get("currency", "USD"), list(categories.values()), items


# ---------------------------------------------------------------
# imei-unlock.net (Dhru Fusion الكلاسيكي): imeiservicelist
# يتفعّل فقط لو المتغيرات الثلاثة IMEI_UNLOCK_* موجودة في Vercel
# ---------------------------------------------------------------
def _num(v):
    m = re.search(r"\d+(?:\.\d+)?", str(v if v is not None else ""))
    return float(m.group()) if m else 0.0


def iu_call(action, timeout=30):
    url = IU_URL if IU_URL.lower().endswith(".php") else IU_URL + "/api/index.php"
    try:
        r = requests.post(
            url,
            data={
                "username": IU_USER,
                "apiaccesskey": IU_KEY,
                "action": action,
                "requestformat": "JSON",
            },
            timeout=timeout,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="imei-unlock unreachable")
    try:
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail=f"imei-unlock returned HTTP {r.status_code} (not JSON)",
        )
    err = data.get("ERROR")
    if err:
        msg = err[0].get("MESSAGE") if isinstance(err, list) and err and isinstance(err[0], dict) else str(err)[:200]
        raise HTTPException(status_code=502, detail=f"imei-unlock error: {msg}")
    return data


def catalog_iu():
    now = time.time()
    hit = _cache.get("iu")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]

    data = iu_call("imeiservicelist")
    succ = data.get("SUCCESS")
    first = succ[0] if isinstance(succ, list) and succ else (succ if isinstance(succ, dict) else {})
    lst = first.get("LIST") or {}
    groups = lst.values() if isinstance(lst, dict) else lst

    items = []
    for g in groups:
        if not isinstance(g, dict):
            continue
        gname = str(g.get("GROUPNAME") or "")
        gtype = "server" if "server" in str(g.get("GROUPTYPE") or "").lower() else "imei"
        svcs = g.get("SERVICES") or {}
        for sv in (svcs.values() if isinstance(svcs, dict) else svcs):
            if not isinstance(sv, dict) or sv.get("SERVICEID") in (None, ""):
                continue
            sid = str(sv["SERVICEID"])
            cost = _num(sv.get("CREDIT"))
            cid = "iu-" + gname
            fields = []
            if gtype == "imei":
                fields.append({"type": "imei", "name": "IMEI", "required": True})
            custom = sv.get("Requires.Custom")
            if isinstance(custom, list):
                for c in custom:
                    if not isinstance(c, dict):
                        continue
                    nm = c.get("fieldname") or c.get("description")
                    if nm:
                        fields.append(
                            {
                                "type": str(c.get("fieldtype") or "text").lower(),
                                "name": str(nm),
                                "required": str(c.get("required")).lower() in ("1", "true", "yes"),
                            }
                        )
            name = str(sv.get("SERVICENAME") or "")
            items.append(
                {
                    "id": "iu-" + sid,
                    "name": name,
                    "type": gtype,
                    "category_id": cid,
                    "category": gname,
                    "cost": cost,
                    "price": markup_price(cost, cid, gname),
                    "time": time_text("iu-" + sid, name, str(sv.get("TIME") or "")),
                    "fields": fields,
                    "supplier": "iu",
                }
            )
    _cache["iu"] = (now, items)
    return items


def catalog():
    """يدمج خدمات GalleUnlockers مع imei-unlock.net (لو مفعّل). فشل مورد لا يوقف الآخر."""
    currency, cats, items = "USD", [], []
    try:
        currency, cats, items = catalog_galle()
    except HTTPException as e:
        if not IU_ENABLED:
            raise
        log.error("galle catalog failed: %s", e.detail)
    if IU_ENABLED:
        try:
            items = items + catalog_iu()
        except HTTPException as e:
            log.error("imei-unlock catalog failed: %s", e.detail)
    return currency, cats, items


def find_product(pid):
    _, _, items = catalog()
    return next((i for i in items if i["id"] == str(pid)), None)


# ---------------------------------------------------------------
# تيليجرام
# ---------------------------------------------------------------
def notify(text):
    if not (TG_TOKEN and TG_CHAT):
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": text[:4000]},
            timeout=8,
        )
        if r.status_code != 200:
            try:
                desc = r.json().get("description")
            except ValueError:
                desc = ""
            log.error("telegram failed: HTTP %s %s", r.status_code, desc)
        return r.status_code == 200
    except Exception as e:
        log.error("telegram request error: %s", type(e).__name__)
        return False


# ---------------------------------------------------------------
# رمز الطلب الموقّع (بدل تخزين الطلبات)
# ---------------------------------------------------------------
def _sign(data):
    return hmac.new(ADMIN_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:32]


def make_token(payload):
    raw = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    return f"{raw}.{_sign(raw)}"


def read_token(token):
    token = (token or "").strip()
    if not ADMIN_SECRET or "." not in token:
        raise HTTPException(status_code=400, detail="Bad token")
    raw, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(raw)):
        raise HTTPException(status_code=400, detail="Bad token")
    try:
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
    except Exception:
        raise HTTPException(status_code=400, detail="Bad token")
    if time.time() - int(payload.get("t", 0)) > 7 * 86400:
        raise HTTPException(status_code=400, detail="Token expired")
    return payload


def token_hash(token):
    return hashlib.sha1(token.strip().encode()).hexdigest()


def first_item(d):
    while isinstance(d, list) and d:
        d = d[0]
    return d if isinstance(d, dict) else {}


# ---------------------------------------------------------------
# الـ Endpoints (تشتغل على / وعلى /api)
# ---------------------------------------------------------------
router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UUID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


class RequestIn(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=64)
    values: dict = Field(default_factory=dict)
    quantity: int = Field(1, ge=1, le=100000)


class PlaceIn(BaseModel):
    token: str = Field("", max_length=5000)
    code: str = Field("", max_length=20)


@router.get("/health")
def health():
    return {
        "ok": True,
        "redis": REDIS,
        "supplier": bool(GALLE_URL and GALLE_KEY),
        "telegram": bool(TG_TOKEN and TG_CHAT),
        "admin": bool(ADMIN_SECRET),
        "imei_unlock": IU_ENABLED,
        # تشخيص مؤقت: احذف السطور الثلاثة بعد ما تنتهي
        "admin_len": len(ADMIN_SECRET),
        "env": env("VERCEL_ENV"),
        "commit": env("VERCEL_GIT_COMMIT_SHA")[:7],
    }


@router.get("/catalog")
def catalog_route(limit: int = 200, offset: int = 0, q: str = ""):
    """الواجهة تنادي: /catalog?limit=200&offset=0 وتتوقع {total, items}."""
    currency, _, items = catalog()
    ql = q.strip().lower()
    if ql:
        items = [i for i in items if ql in (i["name"] or "").lower()]
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    page = items[offset:offset + limit]
    return {
        "currency": currency,
        "total": len(items),
        "items": [{k: v for k, v in i.items() if k not in ("cost", "supplier")} for i in page],
    }


def build_fields(product, values):
    """يبني حقول المورد من schema المنتج. حقل quantity يُعامل كحدود للكمية."""
    lowered = {str(k).lower(): v for k, v in (values or {}).items()}
    out = {}
    qmin, qmax = 1, 1
    for f in product.get("fields") or []:
        if not isinstance(f, dict) or not f.get("name"):
            continue
        name = str(f["name"])
        ftype = str(f.get("type") or "").lower()
        if ftype == "quantity":
            try:
                qmin = max(1, int(f.get("min") or 1))
                qmax = int(f.get("max") or 100000)
            except (TypeError, ValueError):
                pass
            continue
        val = lowered.get(name.lower())
        val = str(val).strip() if val is not None else ""
        if f.get("required") and not val:
            raise HTTPException(status_code=422, detail=f"Missing field: {name}")
        if val:
            if len(val) > 200:
                raise HTTPException(status_code=422, detail=f"Field too long: {name}")
            if ftype == "email" and not EMAIL_RE.match(val):
                raise HTTPException(status_code=422, detail="Invalid email")
            out[name] = val
    return out, qmin, qmax


@router.post("/request")
def create_request(body: RequestIn, request: Request):
    """طلب الزبون: يُسجَّل ويصلك على تيليجرام. التنفيذ عند المورد بعد تأكيد الدفع من /admin."""
    if not (ADMIN_SECRET and TG_TOKEN and TG_CHAT):
        raise HTTPException(status_code=503, detail="Server not configured")
    ip = client_ip(request)
    if not rate_ok(ip):
        raise HTTPException(status_code=429, detail="Too many requests, try later")

    product = find_product(body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    fields, qmin, qmax = build_fields(product, body.values)
    if not (qmin <= body.quantity <= qmax):
        raise HTTPException(status_code=422, detail=f"Quantity must be {qmin}-{qmax}")

    dedupe = hashlib.sha1(
        json.dumps([product["id"], fields, body.quantity], sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    if not lock(f"new:{dedupe}", 60):
        raise HTTPException(status_code=409, detail="Duplicate request, wait a minute")

    payload = {
        "p": product["id"],
        "n": product["name"],
        "f": fields,
        "q": body.quantity,
        "pr": product["price"],
        "t": int(time.time()),
    }
    token = make_token(payload)
    code = "MS-" + token_hash(token)[:8].upper()
    total = round(product["price"] * body.quantity, 2)
    lines = "\n".join(f"{k}: {v}" for k, v in fields.items()) or "-"

    sent = notify(
        f"طلب جديد {code}\n"
        f"الخدمة: {product['name']}\n"
        f"المورد: {'imei-unlock.net (تنفيذ يدوي)' if product.get('supplier') == 'iu' else 'GalleUnlockers'}\n"
        f"الكمية: {body.quantity}\n"
        f"الإجمالي: ${total}\n"
        f"{lines}\n\n"
        f"بعد تأكيد الدفع الصق الرمز في /admin:\n{token}"
    )
    if not sent:
        unlock(f"new:{dedupe}")
        raise HTTPException(status_code=502, detail="Could not deliver the request")

    order_save(
        {
            "code": code,
            "pid": product["id"],
            "name": product["name"],
            "supplier": product.get("supplier"),
            "fields": fields,
            "q": body.quantity,
            "total": total,
            "t": payload["t"],
            "status": "pending",
            "token": token,
        }
    )
    return {"ok": True, "ref": code, "price": total}


@router.get("/selftest")
def selftest(k: str = ""):
    """فحص سريع: افتحه /selftest?k=ADMIN_SECRET. يرسل رسالة تجريبية لتيليجرام ويعرض سبب الفشل."""
    if not ADMIN_SECRET or not hmac.compare_digest(k.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")
    out = {"telegram_configured": bool(TG_TOKEN and TG_CHAT)}
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": "selftest ok"},
            timeout=8,
        )
        j = r.json()
        out["telegram"] = {"ok": bool(j.get("ok")), "http": r.status_code, "description": j.get("description")}
    except Exception as e:
        out["telegram"] = {"ok": False, "error": type(e).__name__}
    if IU_ENABLED:
        try:
            out["imei_unlock_services"] = len(catalog_iu())
        except HTTPException as e:
            out["imei_unlock_error"] = e.detail
    else:
        out["imei_unlock"] = "not configured"
    try:
        _, _, items = catalog()
        out["catalog_items"] = len(items)
        out["sample_product_id"] = items[0]["id"] if items else None
    except HTTPException as e:
        out["catalog_error"] = {"http": e.status_code, "detail": e.detail}
    return out


# ------------------ الأدمن ------------------
@router.post("/admin/place", dependencies=[Depends(require_admin)])
def admin_place(body: PlaceIn, request: Request):
    """ينفّذ الطلب عند المورد (يخصم من رصيدك). استخدمه بعد تأكيد الدفع فقط."""
    token = (body.token or "").strip()
    if not token and body.code:
        rec0 = order_load(body.code.strip().upper())
        if not rec0:
            raise HTTPException(status_code=404, detail="Order not found")
        token = rec0.get("token") or ""
    if not token:
        raise HTTPException(status_code=422, detail="token or code required")

    payload = read_token(token)
    product = find_product(payload.get("p"))
    if not product:
        raise HTTPException(status_code=404, detail="Product no longer available")

    code = "MS-" + token_hash(token)[:8].upper()
    qty = int(payload.get("q") or 1)
    rec = order_load(code) or {
        "code": code,
        "pid": product["id"],
        "name": product["name"],
        "supplier": product.get("supplier"),
        "fields": payload.get("f") or {},
        "q": qty,
        "total": round(float(payload.get("pr") or 0) * qty, 2),
        "t": int(payload.get("t") or time.time()),
        "status": "pending",
        "token": token,
    }

    if product.get("supplier") == "iu":
        rec["status"] = "manual"
        order_save(rec)
        return {
            "ok": True,
            "manual": True,
            "code": code,
            "supplier": "imei-unlock.net",
            "service_id": product["id"].replace("iu-", "", 1),
            "service": product["name"],
            "quantity": qty,
            "fields": payload.get("f") or {},
            "note": "نفّذ هذا الطلب يدويًا من لوحة imei-unlock.net بعد تأكيد الدفع.",
        }

    h = token_hash(token)
    ref_id = "ms-" + h[:24]
    if not lock(f"place:{ref_id}", 600):
        raise HTTPException(status_code=409, detail="Already submitted, check the supplier panel")

    order_obj = dict(payload.get("f") or {})
    order_obj.update(
        {
            "feedback_url": f"{public_base(request)}/callback",
            "reference_id": ref_id,
            "Quantity": qty,
        }
    )
    pid = product["id"]
    req_body = [{"product_id": int(pid) if pid.isdigit() else pid, "fields": [order_obj]}]

    try:
        resp = fusion("POST", "/order", body=req_body, timeout=ORDER_TIMEOUT, write=True)
    except OrderUnknown:
        rec.update(status="unknown", reference_id=ref_id)
        order_save(rec)
        notify(f"نتيجة غير معروفة للطلب {ref_id}. لا تعد الإرسال، راجع لوحة المورد بهذا المرجع.")
        return JSONResponse(
            status_code=202,
            content={
                "ok": False,
                "unknown": True,
                "code": code,
                "reference_id": ref_id,
                "detail": "Outcome unknown. Do NOT retry. Check the supplier panel with this reference_id.",
            },
        )
    except HTTPException:
        unlock(f"place:{ref_id}")
        raise

    item = first_item(resp.get("data"))
    if item.get("status") == "error":
        unlock(f"place:{ref_id}")
        raise HTTPException(status_code=400, detail=item.get("message") or item.get("replay") or "Rejected")

    rec.update(
        status="sent",
        reference_id=ref_id,
        order_uuid=item.get("order_uuid"),
        amount=item.get("amount"),
    )
    order_save(rec)
    notify(f"أُرسل للمورد: {ref_id}\norder_uuid: {item.get('order_uuid')}")
    return {
        "ok": True,
        "code": code,
        "reference_id": ref_id,
        "order_uuid": item.get("order_uuid"),
        "amount": item.get("amount"),
        "currency": item.get("currency_code"),
        "note": item.get("note"),
    }


@router.get("/admin/status", dependencies=[Depends(require_admin)])
def admin_status(uuid: str = ""):
    if not UUID_RE.match(uuid):
        raise HTTPException(status_code=422, detail="Invalid order_uuid")
    data = fusion("GET", "/order", params={"order_uuid": uuid})
    return data.get("data")


@router.get("/admin/account", dependencies=[Depends(require_admin)])
def admin_account():
    d = (fusion("GET", "/account").get("data") or {})
    return {"currency": d.get("currency"), "balance": d.get("balance"), "name": d.get("name")}


@router.get("/admin/orders", dependencies=[Depends(require_admin)])
def admin_orders():
    out = [{k: v for k, v in o.items() if k != "token"} for o in order_list()[:100]]
    return {"storage": REDIS, "orders": out}


@router.post("/admin/orders/{code}/mark", dependencies=[Depends(require_admin)])
def admin_mark(code: str, status: str = "dismissed"):
    code = code.strip().upper()
    if status not in ("done", "dismissed"):
        raise HTTPException(status_code=422, detail="Invalid status")
    rec = order_load(code)
    if not rec:
        raise HTTPException(status_code=404, detail="Order not found")
    rec["status"] = status
    order_save(rec)
    return {"ok": True}


# ------------------ إشعار المورد (feedback_url) ------------------
@router.post("/callback")
def callback(payload: dict):
    """المورد يرسل هنا عند success/rejected. لا يوجد توقيع، فنتحقق من الحالة بـ GET /order قبل أي إجراء."""
    order_id = str(payload.get("order_id") or "")
    ref = str(payload.get("reference_id") or "")[:60]
    if not UUID_RE.match(order_id):
        return {"ok": False}
    try:
        data = fusion("GET", "/order", params={"order_uuid": order_id})
    except HTTPException:
        return {"ok": False}
    d = data.get("data") if isinstance(data.get("data"), dict) else {}
    status = d.get("status")
    if status in ("success", "rejected") and ref.startswith("ms-") and len(ref) >= 11:
        rec = order_load("MS-" + ref[3:11].upper())
        if rec:
            rec["status"] = status
            rec["replay"] = str(d.get("replay") or "")[:600]
            order_save(rec)
    if status in ("success", "rejected") and lock(f"cb:{order_id}:{status}", 3600):
        notify(f"تحديث الطلب {ref}\nالحالة: {status}\nالرد: {str(d.get('replay') or '')[:600]}")
    return {"ok": True}


# ------------------ صفحة بسيطة للتنفيذ ------------------
ADMIN_HTML = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>لوحة Mustafa Soft</title>
<style>
:root{--bg:#f4f6f9;--card:#fff;--ink:#0f172a;--mute:#64748b;--line:#e2e8f0;--btn:#0f172a;--btnt:#fff;--ok:#166534;--okb:#dcfce7;--warn:#92400e;--warnb:#fef3c7;--err:#991b1b;--errb:#fee2e2;--info:#1e40af;--infob:#dbeafe;--mutb:#f1f5f9}
@media(prefers-color-scheme:dark){:root{--bg:#0b1120;--card:#111a2e;--ink:#e5e7eb;--mute:#94a3b8;--line:#22304a;--btn:#e5e7eb;--btnt:#0b1120;--ok:#86efac;--okb:#14532d;--warn:#fcd34d;--warnb:#422006;--err:#fca5a5;--errb:#450a0a;--info:#93c5fd;--infob:#172554;--mutb:#1b2740}}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans Arabic",sans-serif;padding-bottom:40px}
[hidden]{display:none!important}
.wrap{max-width:720px;margin:0 auto;padding:12px}
.top{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:4px 0 10px}
.top h1{font-size:19px;margin:0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.chip{font-size:12px;padding:2px 10px;border-radius:99px;background:var(--mutb);color:var(--mute)}
.chip.ok{background:var(--okb);color:var(--ok)}
.chip.bad{background:var(--errb);color:var(--err)}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin-bottom:12px}
.card h2{font-size:15px;margin:0 0 8px}
input,textarea{width:100%;border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--ink);font:inherit;font-size:16px;padding:12px;margin:6px 0}
textarea{min-height:110px;direction:ltr;text-align:left;font-family:ui-monospace,Menlo,monospace;font-size:13px}
input.ltr{direction:ltr;text-align:left}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:46px;padding:0 18px;border:0;border-radius:12px;background:var(--btn);color:var(--btnt);font:inherit;font-weight:600;font-size:15px;cursor:pointer}
.btn.block{width:100%;margin-top:6px}
.btn.sec{background:var(--mutb);color:var(--ink)}
.btn.dang{background:var(--errb);color:var(--err)}
.btn.sm{min-height:38px;padding:0 14px;font-size:14px}
.btn:disabled{opacity:.5}
.row{display:flex;gap:8px;flex-wrap:wrap}
.row .btn{flex:1}
.tabs{display:flex;gap:6px;margin-bottom:12px;background:var(--mutb);padding:4px;border-radius:14px}
.tab{flex:1;border:0;background:transparent;color:var(--mute);font:inherit;font-weight:600;font-size:14px;padding:10px 4px;border-radius:10px;cursor:pointer}
.tab.on{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.12)}
.filters{display:flex;gap:6px;margin-bottom:10px;overflow-x:auto}
.fl{border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit;font-size:13px;padding:6px 14px;border-radius:99px;white-space:nowrap;cursor:pointer}
.fl.on{background:var(--btn);color:var(--btnt);border-color:var(--btn)}
.order .head{display:flex;justify-content:space-between;align-items:center;gap:8px}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:13px;direction:ltr}
.name{font-weight:600;margin:6px 0 2px;direction:auto}
.mut{color:var(--mute);font-size:13px}
.badge{font-size:12px;font-weight:600;padding:2px 10px;border-radius:99px}
.badge.ok{background:var(--okb);color:var(--ok)}
.badge.warn{background:var(--warnb);color:var(--warn)}
.badge.err{background:var(--errb);color:var(--err)}
.badge.info{background:var(--infob);color:var(--info)}
.badge.mute{background:var(--mutb);color:var(--mute)}
.kv{margin:8px 0;border:1px solid var(--line);border-radius:12px;overflow:hidden}
.kv div{display:flex;justify-content:space-between;gap:10px;padding:8px 10px;border-bottom:1px solid var(--line);font-size:14px}
.kv div:last-child{border-bottom:0}
.kv span:first-child{color:var(--mute);flex:none}
.kv span:last-child{direction:ltr;text-align:left;word-break:break-all}
.note{padding:10px 12px;border-radius:12px;font-size:14px;margin:8px 0}
.note.ok{background:var(--okb);color:var(--ok)}
.note.warn{background:var(--warnb);color:var(--warn)}
.note.err{background:var(--errb);color:var(--err)}
.note.info{background:var(--infob);color:var(--info)}
.bal{font-size:26px;font-weight:700;direction:ltr;text-align:right}
.empty{text-align:center;color:var(--mute);padding:26px 8px}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:flex-end;justify-content:center;z-index:50}
.sheet{background:var(--card);width:100%;max-width:720px;border-radius:20px 20px 0 0;padding:16px 16px calc(16px + env(safe-area-inset-bottom));max-height:88vh;overflow:auto}
.sheet h3{margin:0 0 8px;font-size:17px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--btn);color:var(--btnt);padding:10px 18px;border-radius:99px;font-size:14px;z-index:60}
.err-t{color:var(--err);font-size:14px;min-height:20px}
label.chk{display:flex;gap:8px;align-items:center;font-size:14px;margin:6px 0;color:var(--mute)}
label.chk input{width:auto;margin:0}
</style>
</head>
<body>
<div class="wrap">

<div class="top"><h1>لوحة Mustafa Soft</h1><button class="btn sec sm" id="logout" hidden>خروج</button></div>
<div class="chips" id="chips"></div>

<!-- تسجيل الدخول -->
<div id="login" class="card">
  <h2>الدخول</h2>
  <input id="key" type="password" class="ltr" placeholder="Admin key" autocomplete="off" autocapitalize="off" spellcheck="false">
  <label class="chk"><input type="checkbox" id="rem"> تذكّرني على هذا الجهاز</label>
  <div class="err-t" id="lerr"></div>
  <button class="btn block" id="lbtn">دخول</button>
</div>

<!-- التطبيق -->
<div id="app" hidden>

  <div class="card">
    <h2>رصيد GalleUnlockers</h2>
    <div class="bal" id="bal">...</div>
    <div class="mut" id="balname"></div>
    <button class="btn sec sm" id="balbtn" style="margin-top:8px">تحديث</button>
  </div>

  <div class="tabs">
    <button class="tab on" data-t="orders">الطلبات</button>
    <button class="tab" data-t="token">تنفيذ برمز</button>
    <button class="tab" data-t="status">حالة طلب</button>
  </div>

  <!-- الطلبات -->
  <div id="t-orders">
    <div class="filters" id="filters">
      <button class="fl on" data-f="todo">تحتاج إجراء</button>
      <button class="fl" data-f="done">المنتهية</button>
      <button class="fl" data-f="all">الكل</button>
    </div>
    <button class="btn sec block" id="oref" style="margin:0 0 10px">تحديث القائمة</button>
    <div id="olist"></div>
  </div>

  <!-- تنفيذ برمز -->
  <div id="t-token" hidden>
    <div class="card">
      <h2>الصق رسالة تيليجرام (أو الرمز)</h2>
      <textarea id="ptxt" placeholder="الصق الرسالة كاملة، والرمز بيتلقط تلقائيًا"></textarea>
      <div id="pprev"></div>
      <button class="btn block" id="pgo" disabled>تنفيذ</button>
    </div>
  </div>

  <!-- حالة طلب -->
  <div id="t-status" hidden>
    <div class="card">
      <h2>حالة طلب عند المورد</h2>
      <input id="uuid" class="ltr" placeholder="order_uuid" autocomplete="off" autocapitalize="off" spellcheck="false">
      <div class="row" id="hist"></div>
      <button class="btn block" id="sgo">فحص الحالة</button>
      <div id="sres"></div>
    </div>
  </div>

</div>
</div>

<script>
const root=location.pathname.replace(/\/+$/,'').replace(/\/admin$/,'');
const $=id=>document.getElementById(id);
const ST={pending:['بانتظار التنفيذ','warn'],sent:['أُرسل للمورد','info'],manual:['تنفيذ يدوي','warn'],unknown:['نتيجة مجهولة','err'],success:['ناجح','ok'],rejected:['مرفوض','err'],done:['تم','ok'],dismissed:['متجاهَل','mute']};
const TODO=['pending','manual','unknown'];
const LBL={order_uuid:'رقم الطلب عند المورد',amount:'المبلغ',currency:'العملة',note:'ملاحظة',reference_id:'المرجع',detail:'التفاصيل',service:'الخدمة',service_id:'رقم الخدمة',quantity:'الكمية',fields:'الحقول',supplier:'المورد',code:'الكود',status:'الحالة',replay:'الرد',date:'التاريخ',date_completed:'تاريخ الإنجاز'};
let KEY=sessionStorage.getItem('ms_k')||localStorage.getItem('ms_k')||'';
let ORDERS=[],FILTER='todo',PARSED=null,STORAGE=true;

function h(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e}
function toast(t){const e=h('div','toast',t);document.body.appendChild(e);setTimeout(()=>e.remove(),1800)}
function ago(ts){const s=Math.max(0,Math.floor(Date.now()/1000-ts));if(s<60)return 'الآن';if(s<3600)return 'قبل '+Math.floor(s/60)+' د';if(s<86400)return 'قبل '+Math.floor(s/3600)+' س';return 'قبل '+Math.floor(s/86400)+' يوم'}
function copy(t){
  const done=()=>toast('تم النسخ');
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,()=>fb())}else fb();
  function fb(){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');done()}catch(e){toast('انسخ يدويًا')}a.remove()}
}
function val(v){if(v==null)return '-';if(typeof v==='object')return Object.entries(v).map(([k,x])=>k+': '+x).join('\n')||'-';return String(v)}
function kv(obj,skip){
  const box=h('div','kv');
  Object.entries(obj).forEach(([k,v])=>{
    if(skip&&skip.includes(k))return;
    const r=h('div');r.append(h('span',null,LBL[k]||k),h('span',null,val(v)));box.appendChild(r);
  });
  return box;
}

async function api(method,path,body){
  let r,j={};
  try{
    r=await fetch(root+path,{method,headers:{'Content-Type':'application/json','X-Admin-Key':KEY},body:body?JSON.stringify(body):undefined});
  }catch(e){return {ok:false,status:0,data:{detail:'تعذر الاتصال بالسيرفر'}}}
  try{j=await r.json()}catch(e){}
  return {ok:r.ok,status:r.status,data:j};
}
async function call(method,path,body){
  const r=await api(method,path,body);
  if(r.status===401){logout();$('lerr').textContent='انتهت الجلسة أو كلمة السر غير صحيحة'}
  return r;
}

/* ---------- الدخول ---------- */
function logout(){
  KEY='';sessionStorage.removeItem('ms_k');localStorage.removeItem('ms_k');
  $('app').hidden=true;$('login').hidden=false;$('logout').hidden=true;$('key').value='';
}
async function login(){
  const k=$('key').value.trim();if(!k)return;
  KEY=k;$('lerr').textContent='';$('lbtn').disabled=true;
  const r=await api('GET','/admin/account');
  $('lbtn').disabled=false;
  if(r.status===401){KEY='';$('lerr').textContent='كلمة السر غير صحيحة';return}
  if(r.status===0){KEY='';$('lerr').textContent='تعذر الاتصال بالسيرفر';return}
  sessionStorage.setItem('ms_k',KEY);
  if($('rem').checked)localStorage.setItem('ms_k',KEY);
  enter(r);
}
function enter(first){
  $('login').hidden=true;$('app').hidden=false;$('logout').hidden=false;
  showBalance(first||null);loadOrders();
}

/* ---------- الصحة والرصيد ---------- */
async function loadHealth(){
  const box=$('chips');box.textContent='';
  try{
    const r=await fetch(root+'/health');const d=await r.json();
    const add=(t,ok)=>box.appendChild(h('span','chip '+(ok?'ok':'bad'),t));
    add('السيرفر',d.ok);add('المورد',d.supplier);add('تيليجرام',d.telegram);
    add('التخزين',d.redis);add('imei-unlock',d.imei_unlock);
    if(d.commit)box.appendChild(h('span','chip','v '+d.commit));
    STORAGE=!!d.redis;
  }catch(e){box.appendChild(h('span','chip bad','لا يوجد اتصال'))}
}
async function showBalance(r){
  $('bal').textContent='...';$('balname').textContent='';
  if(!r)r=await call('GET','/admin/account');
  if(r.ok){
    $('bal').textContent=(r.data.balance!=null?r.data.balance:'-')+' '+(r.data.currency||'');
    $('balname').textContent=r.data.name||'';
  }else{
    $('bal').textContent='تعذر جلب الرصيد';
    $('balname').textContent=val(r.data.detail);
  }
}

/* ---------- نتيجة العملية ---------- */
function sheet(build){
  const ov=h('div','ov'),sh=h('div','sheet');
  ov.appendChild(sh);ov.onclick=e=>{if(e.target===ov)ov.remove()};
  build(sh,()=>ov.remove());document.body.appendChild(ov);
}
function showResult(r){
  const d=r.data||{};let kind='ok',head='تم بنجاح';
  if(r.status===202||d.unknown){kind='warn';head='نتيجة غير معروفة'}
  else if(d.manual){kind='warn';head='نفّذ الطلب يدويًا'}
  else if(!r.ok){kind='err';head='فشل ('+r.status+')'}
  sheet((sh,close)=>{
    sh.appendChild(h('h3',null,head));
    if(!r.ok&&r.status!==202)sh.appendChild(h('div','note err',val(d.detail)));
    else{
      if(d.unknown)sh.appendChild(h('div','note warn','لا تعد الإرسال. راجع لوحة المورد بالمرجع قبل أي إجراء.'));
      if(d.manual)sh.appendChild(h('div','note warn',d.note||'نفّذ الطلب من لوحة المورد.'));
      sh.appendChild(kv(d,['ok','manual','unknown','note','detail']));
    }
    if(d.order_uuid){const b=h('button','btn sec block','نسخ رقم الطلب');b.onclick=()=>copy(d.order_uuid);sh.appendChild(b)}
    const c=h('button','btn block','إغلاق');c.onclick=close;sh.appendChild(c);
  });
}

/* ---------- التنفيذ ---------- */
function confirmRun(title,rows,label,run){
  sheet((sh,close)=>{
    sh.appendChild(h('h3',null,'تأكيد التنفيذ'));
    sh.appendChild(h('div','note warn','سيُنفَّذ الطلب عند المورد ويُخصم من رصيدك. تأكد أن الزبون دفع.'));
    sh.appendChild(kv(Object.assign({service:title},rows)));
    const go=h('button','btn block',label);
    go.onclick=async()=>{go.disabled=true;go.textContent='جاري التنفيذ...';close();const r=await run();showResult(r);loadOrders();showBalance()};
    const no=h('button','btn sec block','إلغاء');no.onclick=close;
    sh.append(go,no);
  });
}
function rememberUuid(u,n){
  if(!u)return;
  let a=[];try{a=JSON.parse(localStorage.getItem('ms_hist')||'[]')}catch(e){}
  a=a.filter(x=>x.u!==u);a.unshift({u:u,n:n||'',t:Math.floor(Date.now()/1000)});
  try{localStorage.setItem('ms_hist',JSON.stringify(a.slice(0,15)))}catch(e){}
}
async function place(body,name){
  const r=await call('POST','/admin/place',body);
  if(r.ok&&r.data.order_uuid)rememberUuid(r.data.order_uuid,name);
  return r;
}

/* ---------- الطلبات ---------- */
async function loadOrders(){
  $('olist').textContent='';$('olist').appendChild(h('div','empty','جاري التحميل...'));
  const r=await call('GET','/admin/orders');
  if(!r.ok){$('olist').textContent='';$('olist').appendChild(h('div','note err','تعذر جلب الطلبات: '+val(r.data.detail)));return}
  STORAGE=!!r.data.storage;ORDERS=r.data.orders||[];renderOrders();
}
function renderOrders(){
  const box=$('olist');box.textContent='';
  if(!STORAGE){box.appendChild(h('div','note info','التخزين (Redis) غير مفعّل، فلن تظهر الطلبات هنا. استخدم تبويب "تنفيذ برمز" والصق رسالة تيليجرام.'));return}
  const list=ORDERS.filter(o=>FILTER==='all'||(FILTER==='todo'?TODO.includes(o.status):!TODO.includes(o.status)));
  if(!list.length){box.appendChild(h('div','empty','لا توجد طلبات هنا'));return}
  list.forEach(o=>box.appendChild(orderCard(o)));
}
function orderCard(o){
  const c=h('div','card order');
  const st=ST[o.status]||[o.status,'mute'];
  const hd=h('div','head');hd.append(h('span','mono',o.code),h('span','badge '+st[1],st[0]));
  c.appendChild(hd);
  c.appendChild(h('div','name',o.name||''));
  c.appendChild(h('div','mut','الكمية '+(o.q||1)+' • الإجمالي $'+(o.total!=null?o.total:'-')+' • '+ago(o.t||0)+(o.supplier==='iu'?' • imei-unlock':'')));
  if(o.fields&&Object.keys(o.fields).length)c.appendChild(kv(o.fields));
  if(o.order_uuid){const r=h('div','mut','رقم المورد: '+o.order_uuid);c.appendChild(r)}
  if(o.replay)c.appendChild(h('div','note '+(o.status==='success'?'ok':'err'),o.replay));
  if(o.status==='unknown')c.appendChild(h('div','note warn','لا تعد الإرسال قبل مراجعة لوحة المورد بالمرجع '+(o.reference_id||'')+'.'));
  const row=h('div','row');
  if(o.status==='pending'){
    const g=h('button','btn',o.supplier==='iu'?'تنفيذ (يدوي)':'تنفيذ');
    g.onclick=()=>confirmRun(o.name,{quantity:o.q||1,total:'$'+o.total},'تنفيذ الآن',()=>place({code:o.code},o.name));
    const d=h('button','btn dang','تجاهل');d.onclick=()=>mark(o.code,'dismissed');
    row.append(g,d);
  }else if(o.status==='manual'||o.status==='unknown'){
    const m=h('button','btn','تم التنفيذ');m.onclick=()=>mark(o.code,'done');
    const d=h('button','btn dang','تجاهل');d.onclick=()=>mark(o.code,'dismissed');
    row.append(m,d);
  }else if(o.order_uuid){
    const s=h('button','btn sec','فحص الحالة');s.onclick=()=>{$('uuid').value=o.order_uuid;tab('status');checkStatus()};
    const cp=h('button','btn sec','نسخ الرقم');cp.onclick=()=>copy(o.order_uuid);
    row.append(s,cp);
  }
  if(row.childNodes.length)c.appendChild(row);
  return c;
}
async function mark(code,status){
  const r=await call('POST','/admin/orders/'+encodeURIComponent(code)+'/mark?status='+status);
  if(r.ok){toast('تم');loadOrders()}else toast('تعذر: '+val(r.data.detail));
}

/* ---------- تنفيذ برمز ---------- */
function decodeTok(t){
  let raw=t.split('.')[0].replace(/-/g,'+').replace(/_/g,'/');
  raw+='='.repeat((4-raw.length%4)%4);
  const bin=atob(raw);
  const bytes=Uint8Array.from(bin,c=>c.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}
function parseTok(){
  const txt=$('ptxt').value;const box=$('pprev');
  box.textContent='';PARSED=null;$('pgo').disabled=true;
  if(!txt.trim())return;
  const m=txt.match(/[A-Za-z0-9_-]{16,}\.[0-9a-f]{32}/);
  if(!m){box.appendChild(h('div','note err','ما لقيت رمز صالح في النص.'));return}
  let p;
  try{p=decodeTok(m[0])}catch(e){box.appendChild(h('div','note err','الرمز تالف.'));return}
  const q=p.q||1;
  box.appendChild(kv({service:p.n||p.p,quantity:q,total:'$'+(Math.round((p.pr||0)*q*100)/100),fields:p.f||{},date:ago(p.t||0)}));
  if(Date.now()/1000-(p.t||0)>7*86400){box.appendChild(h('div','note err','الرمز منتهي (أقدم من 7 أيام).'));return}
  if(String(p.p||'').startsWith('iu-'))box.appendChild(h('div','note warn','خدمة من imei-unlock: التنفيذ يدوي من لوحتهم.'));
  PARSED={tok:m[0],name:p.n||'',q:q,total:'$'+(Math.round((p.pr||0)*q*100)/100)};
  $('pgo').disabled=false;
}

/* ---------- حالة طلب ---------- */
function renderHist(){
  const box=$('hist');box.textContent='';
  let a=[];try{a=JSON.parse(localStorage.getItem('ms_hist')||'[]')}catch(e){}
  a.slice(0,6).forEach(x=>{
    const b=h('button','btn sec sm',(x.n||x.u).slice(0,18));b.onclick=()=>{$('uuid').value=x.u;checkStatus()};box.appendChild(b);
  });
}
async function checkStatus(){
  const u=$('uuid').value.trim();const out=$('sres');out.textContent='';
  if(!u)return;
  out.appendChild(h('div','mut','جاري الفحص...'));
  const r=await call('GET','/admin/status?uuid='+encodeURIComponent(u));
  out.textContent='';
  if(!r.ok){out.appendChild(h('div','note err',val(r.data.detail)));return}
  const d=r.data||{};
  const stt=ST[d.status]||[d.status||'-','info'];
  out.appendChild(h('div','note '+stt[1],'الحالة: '+stt[0]));
  out.appendChild(kv(d,['status']));
}

/* ---------- تبويبات ---------- */
function tab(n){
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('on',b.dataset.t===n));
  ['orders','token','status'].forEach(x=>$('t-'+x).hidden=(x!==n));
  if(n==='status')renderHist();
}

/* ---------- ربط الأحداث ---------- */
$('lbtn').onclick=login;
$('key').addEventListener('keydown',e=>{if(e.key==='Enter')login()});
$('logout').onclick=logout;
$('balbtn').onclick=()=>showBalance();
$('oref').onclick=loadOrders;
$('ptxt').addEventListener('input',parseTok);
$('pgo').onclick=()=>{
  if(!PARSED)return;
  const p=PARSED;
  confirmRun(p.name,{quantity:p.q,total:p.total},'تنفيذ الآن',()=>place({token:p.tok},p.name));
};
$('sgo').onclick=checkStatus;
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>tab(b.dataset.t));
document.querySelectorAll('.fl').forEach(b=>b.onclick=()=>{
  FILTER=b.dataset.f;document.querySelectorAll('.fl').forEach(x=>x.classList.toggle('on',x===b));renderOrders();
});

loadHealth();
if(KEY){
  (async()=>{
    const r=await api('GET','/admin/account');
    if(r.status===401||r.status===0){logout()}else enter(r);
  })();
}
</script>
</body>
</html>
"""


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(ADMIN_HTML)


app.include_router(router)
app.include_router(router, prefix="/api")
import os
import re
import time
import hmac
import json
import base64
import hashlib
import logging

import requests
from fastapi import FastAPI, APIRouter, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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
IU_URL = env("IMEI_UNLOCK_API_URL").rstrip("/")
IU_USER = env("IMEI_UNLOCK_USERNAME")
IU_KEY = env("IMEI_UNLOCK_API_KEY")
IU_ENABLED = bool(IU_URL and IU_USER and IU_KEY)
ADMIN_SECRET = env("ADMIN_SECRET")
ALLOWED_ORIGIN = env("ALLOWED_ORIGIN", "https://mustafa-soft.com").rstrip("/")
PUBLIC_URL = env("PUBLIC_URL").rstrip("/")
ORDER_TIMEOUT = env_float("GALLE_ORDER_TIMEOUT", 60)

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
# Redis اختياري (للكاش والقفل وحد الطلبات). بدونه يشتغل بالذاكرة.
# الطلبات نفسها ما بتتخزن: كل طلب بيوصلك على تيليجرام برمز موقّع.
# ---------------------------------------------------------------
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


def lock(key, ttl):
    if REDIS:
        try:
            return _redis(["SET", f"ms:lock:{key}", "1", "NX", "EX", str(ttl)]) == "OK"
        except Exception as e:
            log.error("redis lock error: %s", e)
    now = time.time()
    if _mem_locks.get(key, 0) > now:
        return False
    _mem_locks[key] = now + ttl
    return True


def unlock(key):
    _mem_locks.pop(key, None)
    if REDIS:
        try:
            _redis(["DEL", f"ms:lock:{key}"])
        except Exception:
            pass


def rate_ok(ip, limit=30):
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


def public_base(request: Request):
    if PUBLIC_URL:
        return PUBLIC_URL
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"https://{host}"


# ---------------------------------------------------------------
# سجل الطلبات (يحتاج Redis؛ بدونه تعمل اللوحة بالرمز فقط)
# ---------------------------------------------------------------
HKEY = "ms:o"
ORDER_CODE_RE = re.compile(r"^MS-[0-9A-F]{8}$")


def order_save(rec):
    if not REDIS:
        return
    try:
        _redis(["HSET", HKEY, rec["code"], json.dumps(rec, ensure_ascii=False)])
        _redis(["EXPIRE", HKEY, "5184000"])
    except Exception as e:
        log.error("order save failed: %s", type(e).__name__)


def order_load(code):
    if not REDIS or not ORDER_CODE_RE.match(code or ""):
        return None
    try:
        raw = _redis(["HGET", HKEY, code])
        return json.loads(raw) if raw else None
    except Exception:
        return None


def order_list():
    if not REDIS:
        return []
    try:
        res = _redis(["HGETALL", HKEY]) or []
    except Exception:
        return []
    out = []
    for v in res[1::2]:
        try:
            out.append(json.loads(v))
        except ValueError:
            pass
    out.sort(key=lambda o: o.get("t", 0), reverse=True)
    return out


# ---------------------------------------------------------------
# الحماية
# ---------------------------------------------------------------
def require_admin(x_admin_key: str = Header("")):
    key = x_admin_key.strip()
    if not ADMIN_SECRET or not hmac.compare_digest(key.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------
# Dhru Fusion Pro Reseller API
# GET /account | GET /products | POST /order | GET /order?order_uuid=
# ---------------------------------------------------------------
class OrderUnknown(Exception):
    """انقطع الاتصال أو الرد غير مفهوم أثناء إرسال طلب: النتيجة مجهولة، لا تعيد الإرسال."""


def fusion(method, path, params=None, body=None, timeout=30, write=False):
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
        if write:
            raise OrderUnknown("request failed")
        raise HTTPException(status_code=502, detail="Provider unreachable")

    try:
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except ValueError:
        if write and (r.status_code < 400 or r.status_code >= 500):
            raise OrderUnknown("invalid response")
        raise HTTPException(
            status_code=502,
            detail=f"Provider returned HTTP {r.status_code} (not JSON)",
        )

    # بعض أخطاء التحقق ترجع HTTP 201 مع status=error، فنفحص الاثنين
    if r.status_code >= 400 or data.get("status") != "success":
        code = data.get("code")
        status = r.status_code if r.status_code >= 400 else (
            code if isinstance(code, int) and code >= 400 else 400
        )
        msg = data.get("message") or "Provider error"
        headers = {}
        if r.headers.get("Retry-After"):
            headers["Retry-After"] = r.headers["Retry-After"]
        if status in (401, 402, 403):
            log.error("supplier auth/balance error: HTTP %s", status)
            raise HTTPException(
                status_code=502,
                detail=f"Supplier auth/balance error (HTTP {status}): {msg}",
            )
        raise HTTPException(status_code=status, detail=msg, headers=headers or None)
    return data


def products_raw():
    now = time.time()
    hit = _cache.get("all")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]

    data = None
    if REDIS:
        try:
            raw = _redis(["GET", "ms:products"])
            if raw:
                data = json.loads(raw)
        except Exception:
            data = None

    if data is None:
        data = fusion("GET", "/products")
        if REDIS:
            try:
                _redis(["SET", "ms:products", json.dumps(data), "EX", str(CACHE_TTL)])
            except Exception:
                pass

    _cache["all"] = (now, data)
    return data


# ---------------------------------------------------------------
# تجهيز المنتجات (الأسعار + المدة)
# ---------------------------------------------------------------
def markup_price(cost, cid="", cat_name=""):
    pct = None
    for k in (cid, cat_name):
        if k and k in MARKUP_CATEGORIES:
            pct = float(MARKUP_CATEGORIES[k])
            break
    if pct is None:
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


def catalog_galle():
    """يرجع (العملة، الأقسام، المنتجات) من رد المورد: data.products مفتاحها رقم المنتج."""
    raw = products_raw()
    d = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    cats_raw = d.get("categories") if isinstance(d.get("categories"), dict) else {}
    prods_raw = d.get("products") if isinstance(d.get("products"), dict) else {}

    categories = {}
    for cid, c in cats_raw.items():
        if isinstance(c, dict):
            categories[str(cid)] = {"id": str(cid), "name": c.get("name", ""), "type": c.get("type", "")}

    items = []
    for pid, p in prods_raw.items():
        if not isinstance(p, dict):
            continue
        cid = str(p.get("cid") or ((p.get("cids") or [""])[0]))
        cat_name = categories.get(cid, {}).get("name", "")
        try:
            cost = float(p.get("price") or 0)
        except (TypeError, ValueError):
            cost = 0.0
        fields = p.get("fields") if isinstance(p.get("fields"), list) else []
        items.append(
            {
                "id": str(pid),
                "name": p.get("name", ""),
                "type": p.get("type", ""),
                "category_id": cid,
                "category": cat_name,
                "cost": cost,
                "price": markup_price(cost, cid, cat_name),
                "time": time_text(pid, p.get("name", ""), p.get("time", "")),
                "fields": fields,
                "supplier": "galle",
            }
        )
    return d.get("currency", "USD"), list(categories.values()), items


# ---------------------------------------------------------------
# imei-unlock.net (Dhru Fusion الكلاسيكي): imeiservicelist
# يتفعّل فقط لو المتغيرات الثلاثة IMEI_UNLOCK_* موجودة في Vercel
# ---------------------------------------------------------------
def _num(v):
    m = re.search(r"\d+(?:\.\d+)?", str(v if v is not None else ""))
    return float(m.group()) if m else 0.0


def iu_call(action, timeout=30):
    url = IU_URL if IU_URL.lower().endswith(".php") else IU_URL + "/api/index.php"
    try:
        r = requests.post(
            url,
            data={
                "username": IU_USER,
                "apiaccesskey": IU_KEY,
                "action": action,
                "requestformat": "JSON",
            },
            timeout=timeout,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="imei-unlock unreachable")
    try:
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail=f"imei-unlock returned HTTP {r.status_code} (not JSON)",
        )
    err = data.get("ERROR")
    if err:
        msg = err[0].get("MESSAGE") if isinstance(err, list) and err and isinstance(err[0], dict) else str(err)[:200]
        raise HTTPException(status_code=502, detail=f"imei-unlock error: {msg}")
    return data


def catalog_iu():
    now = time.time()
    hit = _cache.get("iu")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]

    data = iu_call("imeiservicelist")
    succ = data.get("SUCCESS")
    first = succ[0] if isinstance(succ, list) and succ else (succ if isinstance(succ, dict) else {})
    lst = first.get("LIST") or {}
    groups = lst.values() if isinstance(lst, dict) else lst

    items = []
    for g in groups:
        if not isinstance(g, dict):
            continue
        gname = str(g.get("GROUPNAME") or "")
        gtype = "server" if "server" in str(g.get("GROUPTYPE") or "").lower() else "imei"
        svcs = g.get("SERVICES") or {}
        for sv in (svcs.values() if isinstance(svcs, dict) else svcs):
            if not isinstance(sv, dict) or sv.get("SERVICEID") in (None, ""):
                continue
            sid = str(sv["SERVICEID"])
            cost = _num(sv.get("CREDIT"))
            cid = "iu-" + gname
            fields = []
            if gtype == "imei":
                fields.append({"type": "imei", "name": "IMEI", "required": True})
            custom = sv.get("Requires.Custom")
            if isinstance(custom, list):
                for c in custom:
                    if not isinstance(c, dict):
                        continue
                    nm = c.get("fieldname") or c.get("description")
                    if nm:
                        fields.append(
                            {
                                "type": str(c.get("fieldtype") or "text").lower(),
                                "name": str(nm),
                                "required": str(c.get("required")).lower() in ("1", "true", "yes"),
                            }
                        )
            name = str(sv.get("SERVICENAME") or "")
            items.append(
                {
                    "id": "iu-" + sid,
                    "name": name,
                    "type": gtype,
                    "category_id": cid,
                    "category": gname,
                    "cost": cost,
                    "price": markup_price(cost, cid, gname),
                    "time": time_text("iu-" + sid, name, str(sv.get("TIME") or "")),
                    "fields": fields,
                    "supplier": "iu",
                }
            )
    _cache["iu"] = (now, items)
    return items


def catalog():
    """يدمج خدمات GalleUnlockers مع imei-unlock.net (لو مفعّل). فشل مورد لا يوقف الآخر."""
    currency, cats, items = "USD", [], []
    try:
        currency, cats, items = catalog_galle()
    except HTTPException as e:
        if not IU_ENABLED:
            raise
        log.error("galle catalog failed: %s", e.detail)
    if IU_ENABLED:
        try:
            items = items + catalog_iu()
        except HTTPException as e:
            log.error("imei-unlock catalog failed: %s", e.detail)
    return currency, cats, items


def find_product(pid):
    _, _, items = catalog()
    return next((i for i in items if i["id"] == str(pid)), None)


# ---------------------------------------------------------------
# تيليجرام
# ---------------------------------------------------------------
def notify(text):
    if not (TG_TOKEN and TG_CHAT):
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": text[:4000]},
            timeout=8,
        )
        if r.status_code != 200:
            try:
                desc = r.json().get("description")
            except ValueError:
                desc = ""
            log.error("telegram failed: HTTP %s %s", r.status_code, desc)
        return r.status_code == 200
    except Exception as e:
        log.error("telegram request error: %s", type(e).__name__)
        return False


# ---------------------------------------------------------------
# رمز الطلب الموقّع (بدل تخزين الطلبات)
# ---------------------------------------------------------------
def _sign(data):
    return hmac.new(ADMIN_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:32]


def make_token(payload):
    raw = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    return f"{raw}.{_sign(raw)}"


def read_token(token):
    token = (token or "").strip()
    if not ADMIN_SECRET or "." not in token:
        raise HTTPException(status_code=400, detail="Bad token")
    raw, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(raw)):
        raise HTTPException(status_code=400, detail="Bad token")
    try:
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
    except Exception:
        raise HTTPException(status_code=400, detail="Bad token")
    if time.time() - int(payload.get("t", 0)) > 7 * 86400:
        raise HTTPException(status_code=400, detail="Token expired")
    return payload


def token_hash(token):
    return hashlib.sha1(token.strip().encode()).hexdigest()


def first_item(d):
    while isinstance(d, list) and d:
        d = d[0]
    return d if isinstance(d, dict) else {}


# ---------------------------------------------------------------
# الـ Endpoints (تشتغل على / وعلى /api)
# ---------------------------------------------------------------
router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UUID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


class RequestIn(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=64)
    values: dict = Field(default_factory=dict)
    quantity: int = Field(1, ge=1, le=100000)


class PlaceIn(BaseModel):
    token: str = Field("", max_length=5000)
    code: str = Field("", max_length=20)


@router.get("/health")
def health():
    return {
        "ok": True,
        "redis": REDIS,
        "supplier": bool(GALLE_URL and GALLE_KEY),
        "telegram": bool(TG_TOKEN and TG_CHAT),
        "admin": bool(ADMIN_SECRET),
        "imei_unlock": IU_ENABLED,
        # تشخيص مؤقت: احذف السطور الثلاثة بعد ما تنتهي
        "admin_len": len(ADMIN_SECRET),
        "env": env("VERCEL_ENV"),
        "commit": env("VERCEL_GIT_COMMIT_SHA")[:7],
    }


@router.get("/catalog")
def catalog_route(limit: int = 200, offset: int = 0, q: str = ""):
    """الواجهة تنادي: /catalog?limit=200&offset=0 وتتوقع {total, items}."""
    currency, _, items = catalog()
    ql = q.strip().lower()
    if ql:
        items = [i for i in items if ql in (i["name"] or "").lower()]
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    page = items[offset:offset + limit]
    return {
        "currency": currency,
        "total": len(items),
        "items": [{k: v for k, v in i.items() if k not in ("cost", "supplier")} for i in page],
    }


def build_fields(product, values):
    """يبني حقول المورد من schema المنتج. حقل quantity يُعامل كحدود للكمية."""
    lowered = {str(k).lower(): v for k, v in (values or {}).items()}
    out = {}
    qmin, qmax = 1, 1
    for f in product.get("fields") or []:
        if not isinstance(f, dict) or not f.get("name"):
            continue
        name = str(f["name"])
        ftype = str(f.get("type") or "").lower()
        if ftype == "quantity":
            try:
                qmin = max(1, int(f.get("min") or 1))
                qmax = int(f.get("max") or 100000)
            except (TypeError, ValueError):
                pass
            continue
        val = lowered.get(name.lower())
        val = str(val).strip() if val is not None else ""
        if f.get("required") and not val:
            raise HTTPException(status_code=422, detail=f"Missing field: {name}")
        if val:
            if len(val) > 200:
                raise HTTPException(status_code=422, detail=f"Field too long: {name}")
            if ftype == "email" and not EMAIL_RE.match(val):
                raise HTTPException(status_code=422, detail="Invalid email")
            out[name] = val
    return out, qmin, qmax


@router.post("/request")
def create_request(body: RequestIn, request: Request):
    """طلب الزبون: يُسجَّل ويصلك على تيليجرام. التنفيذ عند المورد بعد تأكيد الدفع من /admin."""
    if not (ADMIN_SECRET and TG_TOKEN and TG_CHAT):
        raise HTTPException(status_code=503, detail="Server not configured")
    ip = client_ip(request)
    if not rate_ok(ip):
        raise HTTPException(status_code=429, detail="Too many requests, try later")

    product = find_product(body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    fields, qmin, qmax = build_fields(product, body.values)
    if not (qmin <= body.quantity <= qmax):
        raise HTTPException(status_code=422, detail=f"Quantity must be {qmin}-{qmax}")

    dedupe = hashlib.sha1(
        json.dumps([product["id"], fields, body.quantity], sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    if not lock(f"new:{dedupe}", 60):
        raise HTTPException(status_code=409, detail="Duplicate request, wait a minute")

    payload = {
        "p": product["id"],
        "n": product["name"],
        "f": fields,
        "q": body.quantity,
        "pr": product["price"],
        "t": int(time.time()),
    }
    token = make_token(payload)
    code = "MS-" + token_hash(token)[:8].upper()
    total = round(product["price"] * body.quantity, 2)
    lines = "\n".join(f"{k}: {v}" for k, v in fields.items()) or "-"

    sent = notify(
        f"طلب جديد {code}\n"
        f"الخدمة: {product['name']}\n"
        f"المورد: {'imei-unlock.net (تنفيذ يدوي)' if product.get('supplier') == 'iu' else 'GalleUnlockers'}\n"
        f"الكمية: {body.quantity}\n"
        f"الإجمالي: ${total}\n"
        f"{lines}\n\n"
        f"بعد تأكيد الدفع الصق الرمز في /admin:\n{token}"
    )
    if not sent:
        unlock(f"new:{dedupe}")
        raise HTTPException(status_code=502, detail="Could not deliver the request")

    order_save(
        {
            "code": code,
            "pid": product["id"],
            "name": product["name"],
            "supplier": product.get("supplier"),
            "fields": fields,
            "q": body.quantity,
            "total": total,
            "t": payload["t"],
            "status": "pending",
            "token": token,
        }
    )
    return {"ok": True, "ref": code, "price": total}


@router.get("/selftest")
def selftest(k: str = ""):
    """فحص سريع: افتحه /selftest?k=ADMIN_SECRET. يرسل رسالة تجريبية لتيليجرام ويعرض سبب الفشل."""
    if not ADMIN_SECRET or not hmac.compare_digest(k.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")
    out = {"telegram_configured": bool(TG_TOKEN and TG_CHAT)}
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": "selftest ok"},
            timeout=8,
        )
        j = r.json()
        out["telegram"] = {"ok": bool(j.get("ok")), "http": r.status_code, "description": j.get("description")}
    except Exception as e:
        out["telegram"] = {"ok": False, "error": type(e).__name__}
    if IU_ENABLED:
        try:
            out["imei_unlock_services"] = len(catalog_iu())
        except HTTPException as e:
            out["imei_unlock_error"] = e.detail
    else:
        out["imei_unlock"] = "not configured"
    try:
        _, _, items = catalog()
        out["catalog_items"] = len(items)
        out["sample_product_id"] = items[0]["id"] if items else None
    except HTTPException as e:
        out["catalog_error"] = {"http": e.status_code, "detail": e.detail}
    return out


# ------------------ الأدمن ------------------
@router.post("/admin/place", dependencies=[Depends(require_admin)])
def admin_place(body: PlaceIn, request: Request):
    """ينفّذ الطلب عند المورد (يخصم من رصيدك). استخدمه بعد تأكيد الدفع فقط."""
    token = (body.token or "").strip()
    if not token and body.code:
        rec0 = order_load(body.code.strip().upper())
        if not rec0:
            raise HTTPException(status_code=404, detail="Order not found")
        token = rec0.get("token") or ""
    if not token:
        raise HTTPException(status_code=422, detail="token or code required")

    payload = read_token(token)
    product = find_product(payload.get("p"))
    if not product:
        raise HTTPException(status_code=404, detail="Product no longer available")

    code = "MS-" + token_hash(token)[:8].upper()
    qty = int(payload.get("q") or 1)
    rec = order_load(code) or {
        "code": code,
        "pid": product["id"],
        "name": product["name"],
        "supplier": product.get("supplier"),
        "fields": payload.get("f") or {},
        "q": qty,
        "total": round(float(payload.get("pr") or 0) * qty, 2),
        "t": int(payload.get("t") or time.time()),
        "status": "pending",
        "token": token,
    }

    if product.get("supplier") == "iu":
        rec["status"] = "manual"
        order_save(rec)
        return {
            "ok": True,
            "manual": True,
            "code": code,
            "supplier": "imei-unlock.net",
            "service_id": product["id"].replace("iu-", "", 1),
            "service": product["name"],
            "quantity": qty,
            "fields": payload.get("f") or {},
            "note": "نفّذ هذا الطلب يدويًا من لوحة imei-unlock.net بعد تأكيد الدفع.",
        }

    h = token_hash(token)
    ref_id = "ms-" + h[:24]
    if not lock(f"place:{ref_id}", 600):
        raise HTTPException(status_code=409, detail="Already submitted, check the supplier panel")

    order_obj = dict(payload.get("f") or {})
    order_obj.update(
        {
            "feedback_url": f"{public_base(request)}/callback",
            "reference_id": ref_id,
            "Quantity": qty,
        }
    )
    pid = product["id"]
    req_body = [{"product_id": int(pid) if pid.isdigit() else pid, "fields": [order_obj]}]

    try:
        resp = fusion("POST", "/order", body=req_body, timeout=ORDER_TIMEOUT, write=True)
    except OrderUnknown:
        rec.update(status="unknown", reference_id=ref_id)
        order_save(rec)
        notify(f"نتيجة غير معروفة للطلب {ref_id}. لا تعد الإرسال، راجع لوحة المورد بهذا المرجع.")
        return JSONResponse(
            status_code=202,
            content={
                "ok": False,
                "unknown": True,
                "code": code,
                "reference_id": ref_id,
                "detail": "Outcome unknown. Do NOT retry. Check the supplier panel with this reference_id.",
            },
        )
    except HTTPException:
        unlock(f"place:{ref_id}")
        raise

    item = first_item(resp.get("data"))
    if item.get("status") == "error":
        unlock(f"place:{ref_id}")
        raise HTTPException(status_code=400, detail=item.get("message") or item.get("replay") or "Rejected")

    rec.update(
        status="sent",
        reference_id=ref_id,
        order_uuid=item.get("order_uuid"),
        amount=item.get("amount"),
    )
    order_save(rec)
    notify(f"أُرسل للمورد: {ref_id}\norder_uuid: {item.get('order_uuid')}")
    return {
        "ok": True,
        "code": code,
        "reference_id": ref_id,
        "order_uuid": item.get("order_uuid"),
        "amount": item.get("amount"),
        "currency": item.get("currency_code"),
        "note": item.get("note"),
    }


@router.get("/admin/status", dependencies=[Depends(require_admin)])
def admin_status(uuid: str = ""):
    if not UUID_RE.match(uuid):
        raise HTTPException(status_code=422, detail="Invalid order_uuid")
    data = fusion("GET", "/order", params={"order_uuid": uuid})
    return data.get("data")


@router.get("/admin/account", dependencies=[Depends(require_admin)])
def admin_account():
    d = (fusion("GET", "/account").get("data") or {})
    return {"currency": d.get("currency"), "balance": d.get("balance"), "name": d.get("name")}


@router.get("/admin/orders", dependencies=[Depends(require_admin)])
def admin_orders():
    out = [{k: v for k, v in o.items() if k != "token"} for o in order_list()[:100]]
    return {"storage": REDIS, "orders": out}


@router.post("/admin/orders/{code}/mark", dependencies=[Depends(require_admin)])
def admin_mark(code: str, status: str = "dismissed"):
    code = code.strip().upper()
    if status not in ("done", "dismissed"):
        raise HTTPException(status_code=422, detail="Invalid status")
    rec = order_load(code)
    if not rec:
        raise HTTPException(status_code=404, detail="Order not found")
    rec["status"] = status
    order_save(rec)
    return {"ok": True}


# ------------------ إشعار المورد (feedback_url) ------------------
@router.post("/callback")
def callback(payload: dict):
    """المورد يرسل هنا عند success/rejected. لا يوجد توقيع، فنتحقق من الحالة بـ GET /order قبل أي إجراء."""
    order_id = str(payload.get("order_id") or "")
    ref = str(payload.get("reference_id") or "")[:60]
    if not UUID_RE.match(order_id):
        return {"ok": False}
    try:
        data = fusion("GET", "/order", params={"order_uuid": order_id})
    except HTTPException:
        return {"ok": False}
    d = data.get("data") if isinstance(data.get("data"), dict) else {}
    status = d.get("status")
    if status in ("success", "rejected") and ref.startswith("ms-") and len(ref) >= 11:
        rec = order_load("MS-" + ref[3:11].upper())
        if rec:
            rec["status"] = status
            rec["replay"] = str(d.get("replay") or "")[:600]
            order_save(rec)
    if status in ("success", "rejected") and lock(f"cb:{order_id}:{status}", 3600):
        notify(f"تحديث الطلب {ref}\nالحالة: {status}\nالرد: {str(d.get('replay') or '')[:600]}")
    return {"ok": True}


# ------------------ صفحة بسيطة للتنفيذ ------------------
ADMIN_HTML = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>لوحة Mustafa Soft</title>
<style>
:root{--bg:#f4f6f9;--card:#fff;--ink:#0f172a;--mute:#64748b;--line:#e2e8f0;--btn:#0f172a;--btnt:#fff;--ok:#166534;--okb:#dcfce7;--warn:#92400e;--warnb:#fef3c7;--err:#991b1b;--errb:#fee2e2;--info:#1e40af;--infob:#dbeafe;--mutb:#f1f5f9}
@media(prefers-color-scheme:dark){:root{--bg:#0b1120;--card:#111a2e;--ink:#e5e7eb;--mute:#94a3b8;--line:#22304a;--btn:#e5e7eb;--btnt:#0b1120;--ok:#86efac;--okb:#14532d;--warn:#fcd34d;--warnb:#422006;--err:#fca5a5;--errb:#450a0a;--info:#93c5fd;--infob:#172554;--mutb:#1b2740}}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans Arabic",sans-serif;padding-bottom:40px}
[hidden]{display:none!important}
.wrap{max-width:720px;margin:0 auto;padding:12px}
.top{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:4px 0 10px}
.top h1{font-size:19px;margin:0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.chip{font-size:12px;padding:2px 10px;border-radius:99px;background:var(--mutb);color:var(--mute)}
.chip.ok{background:var(--okb);color:var(--ok)}
.chip.bad{background:var(--errb);color:var(--err)}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin-bottom:12px}
.card h2{font-size:15px;margin:0 0 8px}
input,textarea{width:100%;border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--ink);font:inherit;font-size:16px;padding:12px;margin:6px 0}
textarea{min-height:110px;direction:ltr;text-align:left;font-family:ui-monospace,Menlo,monospace;font-size:13px}
input.ltr{direction:ltr;text-align:left}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:46px;padding:0 18px;border:0;border-radius:12px;background:var(--btn);color:var(--btnt);font:inherit;font-weight:600;font-size:15px;cursor:pointer}
.btn.block{width:100%;margin-top:6px}
.btn.sec{background:var(--mutb);color:var(--ink)}
.btn.dang{background:var(--errb);color:var(--err)}
.btn.sm{min-height:38px;padding:0 14px;font-size:14px}
.btn:disabled{opacity:.5}
.row{display:flex;gap:8px;flex-wrap:wrap}
.row .btn{flex:1}
.tabs{display:flex;gap:6px;margin-bottom:12px;background:var(--mutb);padding:4px;border-radius:14px}
.tab{flex:1;border:0;background:transparent;color:var(--mute);font:inherit;font-weight:600;font-size:14px;padding:10px 4px;border-radius:10px;cursor:pointer}
.tab.on{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.12)}
.filters{display:flex;gap:6px;margin-bottom:10px;overflow-x:auto}
.fl{border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit;font-size:13px;padding:6px 14px;border-radius:99px;white-space:nowrap;cursor:pointer}
.fl.on{background:var(--btn);color:var(--btnt);border-color:var(--btn)}
.order .head{display:flex;justify-content:space-between;align-items:center;gap:8px}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:13px;direction:ltr}
.name{font-weight:600;margin:6px 0 2px;direction:auto}
.mut{color:var(--mute);font-size:13px}
.badge{font-size:12px;font-weight:600;padding:2px 10px;border-radius:99px}
.badge.ok{background:var(--okb);color:var(--ok)}
.badge.warn{background:var(--warnb);color:var(--warn)}
.badge.err{background:var(--errb);color:var(--err)}
.badge.info{background:var(--infob);color:var(--info)}
.badge.mute{background:var(--mutb);color:var(--mute)}
.kv{margin:8px 0;border:1px solid var(--line);border-radius:12px;overflow:hidden}
.kv div{display:flex;justify-content:space-between;gap:10px;padding:8px 10px;border-bottom:1px solid var(--line);font-size:14px}
.kv div:last-child{border-bottom:0}
.kv span:first-child{color:var(--mute);flex:none}
.kv span:last-child{direction:ltr;text-align:left;word-break:break-all}
.note{padding:10px 12px;border-radius:12px;font-size:14px;margin:8px 0}
.note.ok{background:var(--okb);color:var(--ok)}
.note.warn{background:var(--warnb);color:var(--warn)}
.note.err{background:var(--errb);color:var(--err)}
.note.info{background:var(--infob);color:var(--info)}
.bal{font-size:26px;font-weight:700;direction:ltr;text-align:right}
.empty{text-align:center;color:var(--mute);padding:26px 8px}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:flex-end;justify-content:center;z-index:50}
.sheet{background:var(--card);width:100%;max-width:720px;border-radius:20px 20px 0 0;padding:16px 16px calc(16px + env(safe-area-inset-bottom));max-height:88vh;overflow:auto}
.sheet h3{margin:0 0 8px;font-size:17px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--btn);color:var(--btnt);padding:10px 18px;border-radius:99px;font-size:14px;z-index:60}
.err-t{color:var(--err);font-size:14px;min-height:20px}
label.chk{display:flex;gap:8px;align-items:center;font-size:14px;margin:6px 0;color:var(--mute)}
label.chk input{width:auto;margin:0}
</style>
</head>
<body>
<div class="wrap">

<div class="top"><h1>لوحة Mustafa Soft</h1><button class="btn sec sm" id="logout" hidden>خروج</button></div>
<div class="chips" id="chips"></div>

<!-- تسجيل الدخول -->
<div id="login" class="card">
  <h2>الدخول</h2>
  <input id="key" type="password" class="ltr" placeholder="Admin key" autocomplete="off" autocapitalize="off" spellcheck="false">
  <label class="chk"><input type="checkbox" id="rem"> تذكّرني على هذا الجهاز</label>
  <div class="err-t" id="lerr"></div>
  <button class="btn block" id="lbtn">دخول</button>
</div>

<!-- التطبيق -->
<div id="app" hidden>

  <div class="card">
    <h2>رصيد GalleUnlockers</h2>
    <div class="bal" id="bal">...</div>
    <div class="mut" id="balname"></div>
    <button class="btn sec sm" id="balbtn" style="margin-top:8px">تحديث</button>
  </div>

  <div class="tabs">
    <button class="tab on" data-t="orders">الطلبات</button>
    <button class="tab" data-t="token">تنفيذ برمز</button>
    <button class="tab" data-t="status">حالة طلب</button>
  </div>

  <!-- الطلبات -->
  <div id="t-orders">
    <div class="filters" id="filters">
      <button class="fl on" data-f="todo">تحتاج إجراء</button>
      <button class="fl" data-f="done">المنتهية</button>
      <button class="fl" data-f="all">الكل</button>
    </div>
    <button class="btn sec block" id="oref" style="margin:0 0 10px">تحديث القائمة</button>
    <div id="olist"></div>
  </div>

  <!-- تنفيذ برمز -->
  <div id="t-token" hidden>
    <div class="card">
      <h2>الصق رسالة تيليجرام (أو الرمز)</h2>
      <textarea id="ptxt" placeholder="الصق الرسالة كاملة، والرمز بيتلقط تلقائيًا"></textarea>
      <div id="pprev"></div>
      <button class="btn block" id="pgo" disabled>تنفيذ</button>
    </div>
  </div>

  <!-- حالة طلب -->
  <div id="t-status" hidden>
    <div class="card">
      <h2>حالة طلب عند المورد</h2>
      <input id="uuid" class="ltr" placeholder="order_uuid" autocomplete="off" autocapitalize="off" spellcheck="false">
      <div class="row" id="hist"></div>
      <button class="btn block" id="sgo">فحص الحالة</button>
      <div id="sres"></div>
    </div>
  </div>

</div>
</div>

<script>
const root=location.pathname.replace(/\/+$/,'').replace(/\/admin$/,'');
const $=id=>document.getElementById(id);
const ST={pending:['بانتظار التنفيذ','warn'],sent:['أُرسل للمورد','info'],manual:['تنفيذ يدوي','warn'],unknown:['نتيجة مجهولة','err'],success:['ناجح','ok'],rejected:['مرفوض','err'],done:['تم','ok'],dismissed:['متجاهَل','mute']};
const TODO=['pending','manual','unknown'];
const LBL={order_uuid:'رقم الطلب عند المورد',amount:'المبلغ',currency:'العملة',note:'ملاحظة',reference_id:'المرجع',detail:'التفاصيل',service:'الخدمة',service_id:'رقم الخدمة',quantity:'الكمية',fields:'الحقول',supplier:'المورد',code:'الكود',status:'الحالة',replay:'الرد',date:'التاريخ',date_completed:'تاريخ الإنجاز'};
let KEY=sessionStorage.getItem('ms_k')||localStorage.getItem('ms_k')||'';
let ORDERS=[],FILTER='todo',PARSED=null,STORAGE=true;

function h(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e}
function toast(t){const e=h('div','toast',t);document.body.appendChild(e);setTimeout(()=>e.remove(),1800)}
function ago(ts){const s=Math.max(0,Math.floor(Date.now()/1000-ts));if(s<60)return 'الآن';if(s<3600)return 'قبل '+Math.floor(s/60)+' د';if(s<86400)return 'قبل '+Math.floor(s/3600)+' س';return 'قبل '+Math.floor(s/86400)+' يوم'}
function copy(t){
  const done=()=>toast('تم النسخ');
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,()=>fb())}else fb();
  function fb(){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');done()}catch(e){toast('انسخ يدويًا')}a.remove()}
}
function val(v){if(v==null)return '-';if(typeof v==='object')return Object.entries(v).map(([k,x])=>k+': '+x).join('\n')||'-';return String(v)}
function kv(obj,skip){
  const box=h('div','kv');
  Object.entries(obj).forEach(([k,v])=>{
    if(skip&&skip.includes(k))return;
    const r=h('div');r.append(h('span',null,LBL[k]||k),h('span',null,val(v)));box.appendChild(r);
  });
  return box;
}

async function api(method,path,body){
  let r,j={};
  try{
    r=await fetch(root+path,{method,headers:{'Content-Type':'application/json','X-Admin-Key':KEY},body:body?JSON.stringify(body):undefined});
  }catch(e){return {ok:false,status:0,data:{detail:'تعذر الاتصال بالسيرفر'}}}
  try{j=await r.json()}catch(e){}
  return {ok:r.ok,status:r.status,data:j};
}
async function call(method,path,body){
  const r=await api(method,path,body);
  if(r.status===401){logout();$('lerr').textContent='انتهت الجلسة أو كلمة السر غير صحيحة'}
  return r;
}

/* ---------- الدخول ---------- */
function logout(){
  KEY='';sessionStorage.removeItem('ms_k');localStorage.removeItem('ms_k');
  $('app').hidden=true;$('login').hidden=false;$('logout').hidden=true;$('key').value='';
}
async function login(){
  const k=$('key').value.trim();if(!k)return;
  KEY=k;$('lerr').textContent='';$('lbtn').disabled=true;
  const r=await api('GET','/admin/account');
  $('lbtn').disabled=false;
  if(r.status===401){KEY='';$('lerr').textContent='كلمة السر غير صحيحة';return}
  if(r.status===0){KEY='';$('lerr').textContent='تعذر الاتصال بالسيرفر';return}
  sessionStorage.setItem('ms_k',KEY);
  if($('rem').checked)localStorage.setItem('ms_k',KEY);
  enter(r);
}
function enter(first){
  $('login').hidden=true;$('app').hidden=false;$('logout').hidden=false;
  showBalance(first||null);loadOrders();
}

/* ---------- الصحة والرصيد ---------- */
async function loadHealth(){
  const box=$('chips');box.textContent='';
  try{
    const r=await fetch(root+'/health');const d=await r.json();
    const add=(t,ok)=>box.appendChild(h('span','chip '+(ok?'ok':'bad'),t));
    add('السيرفر',d.ok);add('المورد',d.supplier);add('تيليجرام',d.telegram);
    add('التخزين',d.redis);add('imei-unlock',d.imei_unlock);
    if(d.commit)box.appendChild(h('span','chip','v '+d.commit));
    STORAGE=!!d.redis;
  }catch(e){box.appendChild(h('span','chip bad','لا يوجد اتصال'))}
}
async function showBalance(r){
  $('bal').textContent='...';$('balname').textContent='';
  if(!r)r=await call('GET','/admin/account');
  if(r.ok){
    $('bal').textContent=(r.data.balance!=null?r.data.balance:'-')+' '+(r.data.currency||'');
    $('balname').textContent=r.data.name||'';
  }else{
    $('bal').textContent='تعذر جلب الرصيد';
    $('balname').textContent=val(r.data.detail);
  }
}

/* ---------- نتيجة العملية ---------- */
function sheet(build){
  const ov=h('div','ov'),sh=h('div','sheet');
  ov.appendChild(sh);ov.onclick=e=>{if(e.target===ov)ov.remove()};
  build(sh,()=>ov.remove());document.body.appendChild(ov);
}
function showResult(r){
  const d=r.data||{};let kind='ok',head='تم بنجاح';
  if(r.status===202||d.unknown){kind='warn';head='نتيجة غير معروفة'}
  else if(d.manual){kind='warn';head='نفّذ الطلب يدويًا'}
  else if(!r.ok){kind='err';head='فشل ('+r.status+')'}
  sheet((sh,close)=>{
    sh.appendChild(h('h3',null,head));
    if(!r.ok&&r.status!==202)sh.appendChild(h('div','note err',val(d.detail)));
    else{
      if(d.unknown)sh.appendChild(h('div','note warn','لا تعد الإرسال. راجع لوحة المورد بالمرجع قبل أي إجراء.'));
      if(d.manual)sh.appendChild(h('div','note warn',d.note||'نفّذ الطلب من لوحة المورد.'));
      sh.appendChild(kv(d,['ok','manual','unknown','note','detail']));
    }
    if(d.order_uuid){const b=h('button','btn sec block','نسخ رقم الطلب');b.onclick=()=>copy(d.order_uuid);sh.appendChild(b)}
    const c=h('button','btn block','إغلاق');c.onclick=close;sh.appendChild(c);
  });
}

/* ---------- التنفيذ ---------- */
function confirmRun(title,rows,label,run){
  sheet((sh,close)=>{
    sh.appendChild(h('h3',null,'تأكيد التنفيذ'));
    sh.appendChild(h('div','note warn','سيُنفَّذ الطلب عند المورد ويُخصم من رصيدك. تأكد أن الزبون دفع.'));
    sh.appendChild(kv(Object.assign({service:title},rows)));
    const go=h('button','btn block',label);
    go.onclick=async()=>{go.disabled=true;go.textContent='جاري التنفيذ...';close();const r=await run();showResult(r);loadOrders();showBalance()};
    const no=h('button','btn sec block','إلغاء');no.onclick=close;
    sh.append(go,no);
  });
}
function rememberUuid(u,n){
  if(!u)return;
  let a=[];try{a=JSON.parse(localStorage.getItem('ms_hist')||'[]')}catch(e){}
  a=a.filter(x=>x.u!==u);a.unshift({u:u,n:n||'',t:Math.floor(Date.now()/1000)});
  try{localStorage.setItem('ms_hist',JSON.stringify(a.slice(0,15)))}catch(e){}
}
async function place(body,name){
  const r=await call('POST','/admin/place',body);
  if(r.ok&&r.data.order_uuid)rememberUuid(r.data.order_uuid,name);
  return r;
}

/* ---------- الطلبات ---------- */
async function loadOrders(){
  $('olist').textContent='';$('olist').appendChild(h('div','empty','جاري التحميل...'));
  const r=await call('GET','/admin/orders');
  if(!r.ok){$('olist').textContent='';$('olist').appendChild(h('div','note err','تعذر جلب الطلبات: '+val(r.data.detail)));return}
  STORAGE=!!r.data.storage;ORDERS=r.data.orders||[];renderOrders();
}
function renderOrders(){
  const box=$('olist');box.textContent='';
  if(!STORAGE){box.appendChild(h('div','note info','التخزين (Redis) غير مفعّل، فلن تظهر الطلبات هنا. استخدم تبويب "تنفيذ برمز" والصق رسالة تيليجرام.'));return}
  const list=ORDERS.filter(o=>FILTER==='all'||(FILTER==='todo'?TODO.includes(o.status):!TODO.includes(o.status)));
  if(!list.length){box.appendChild(h('div','empty','لا توجد طلبات هنا'));return}
  list.forEach(o=>box.appendChild(orderCard(o)));
}
function orderCard(o){
  const c=h('div','card order');
  const st=ST[o.status]||[o.status,'mute'];
  const hd=h('div','head');hd.append(h('span','mono',o.code),h('span','badge '+st[1],st[0]));
  c.appendChild(hd);
  c.appendChild(h('div','name',o.name||''));
  c.appendChild(h('div','mut','الكمية '+(o.q||1)+' • الإجمالي $'+(o.total!=null?o.total:'-')+' • '+ago(o.t||0)+(o.supplier==='iu'?' • imei-unlock':'')));
  if(o.fields&&Object.keys(o.fields).length)c.appendChild(kv(o.fields));
  if(o.order_uuid){const r=h('div','mut','رقم المورد: '+o.order_uuid);c.appendChild(r)}
  if(o.replay)c.appendChild(h('div','note '+(o.status==='success'?'ok':'err'),o.replay));
  if(o.status==='unknown')c.appendChild(h('div','note warn','لا تعد الإرسال قبل مراجعة لوحة المورد بالمرجع '+(o.reference_id||'')+'.'));
  const row=h('div','row');
  if(o.status==='pending'){
    const g=h('button','btn',o.supplier==='iu'?'تنفيذ (يدوي)':'تنفيذ');
    g.onclick=()=>confirmRun(o.name,{quantity:o.q||1,total:'$'+o.total},'تنفيذ الآن',()=>place({code:o.code},o.name));
    const d=h('button','btn dang','تجاهل');d.onclick=()=>mark(o.code,'dismissed');
    row.append(g,d);
  }else if(o.status==='manual'||o.status==='unknown'){
    const m=h('button','btn','تم التنفيذ');m.onclick=()=>mark(o.code,'done');
    const d=h('button','btn dang','تجاهل');d.onclick=()=>mark(o.code,'dismissed');
    row.append(m,d);
  }else if(o.order_uuid){
    const s=h('button','btn sec','فحص الحالة');s.onclick=()=>{$('uuid').value=o.order_uuid;tab('status');checkStatus()};
    const cp=h('button','btn sec','نسخ الرقم');cp.onclick=()=>copy(o.order_uuid);
    row.append(s,cp);
  }
  if(row.childNodes.length)c.appendChild(row);
  return c;
}
async function mark(code,status){
  const r=await call('POST','/admin/orders/'+encodeURIComponent(code)+'/mark?status='+status);
  if(r.ok){toast('تم');loadOrders()}else toast('تعذر: '+val(r.data.detail));
}

/* ---------- تنفيذ برمز ---------- */
function decodeTok(t){
  let raw=t.split('.')[0].replace(/-/g,'+').replace(/_/g,'/');
  raw+='='.repeat((4-raw.length%4)%4);
  const bin=atob(raw);
  const bytes=Uint8Array.from(bin,c=>c.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}
function parseTok(){
  const txt=$('ptxt').value;const box=$('pprev');
  box.textContent='';PARSED=null;$('pgo').disabled=true;
  if(!txt.trim())return;
  const m=txt.match(/[A-Za-z0-9_-]{16,}\.[0-9a-f]{32}/);
  if(!m){box.appendChild(h('div','note err','ما لقيت رمز صالح في النص.'));return}
  let p;
  try{p=decodeTok(m[0])}catch(e){box.appendChild(h('div','note err','الرمز تالف.'));return}
  const q=p.q||1;
  box.appendChild(kv({service:p.n||p.p,quantity:q,total:'$'+(Math.round((p.pr||0)*q*100)/100),fields:p.f||{},date:ago(p.t||0)}));
  if(Date.now()/1000-(p.t||0)>7*86400){box.appendChild(h('div','note err','الرمز منتهي (أقدم من 7 أيام).'));return}
  if(String(p.p||'').startsWith('iu-'))box.appendChild(h('div','note warn','خدمة من imei-unlock: التنفيذ يدوي من لوحتهم.'));
  PARSED={tok:m[0],name:p.n||'',q:q,total:'$'+(Math.round((p.pr||0)*q*100)/100)};
  $('pgo').disabled=false;
}

/* ---------- حالة طلب ---------- */
function renderHist(){
  const box=$('hist');box.textContent='';
  let a=[];try{a=JSON.parse(localStorage.getItem('ms_hist')||'[]')}catch(e){}
  a.slice(0,6).forEach(x=>{
    const b=h('button','btn sec sm',(x.n||x.u).slice(0,18));b.onclick=()=>{$('uuid').value=x.u;checkStatus()};box.appendChild(b);
  });
}
async function checkStatus(){
  const u=$('uuid').value.trim();const out=$('sres');out.textContent='';
  if(!u)return;
  out.appendChild(h('div','mut','جاري الفحص...'));
  const r=await call('GET','/admin/status?uuid='+encodeURIComponent(u));
  out.textContent='';
  if(!r.ok){out.appendChild(h('div','note err',val(r.data.detail)));return}
  const d=r.data||{};
  const stt=ST[d.status]||[d.status||'-','info'];
  out.appendChild(h('div','note '+stt[1],'الحالة: '+stt[0]));
  out.appendChild(kv(d,['status']));
}

/* ---------- تبويبات ---------- */
function tab(n){
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('on',b.dataset.t===n));
  ['orders','token','status'].forEach(x=>$('t-'+x).hidden=(x!==n));
  if(n==='status')renderHist();
}

/* ---------- ربط الأحداث ---------- */
$('lbtn').onclick=login;
$('key').addEventListener('keydown',e=>{if(e.key==='Enter')login()});
$('logout').onclick=logout;
$('balbtn').onclick=()=>showBalance();
$('oref').onclick=loadOrders;
$('ptxt').addEventListener('input',parseTok);
$('pgo').onclick=()=>{
  if(!PARSED)return;
  const p=PARSED;
  confirmRun(p.name,{quantity:p.q,total:p.total},'تنفيذ الآن',()=>place({token:p.tok},p.name));
};
$('sgo').onclick=checkStatus;
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>tab(b.dataset.t));
document.querySelectorAll('.fl').forEach(b=>b.onclick=()=>{
  FILTER=b.dataset.f;document.querySelectorAll('.fl').forEach(x=>x.classList.toggle('on',x===b));renderOrders();
});

loadHealth();
if(KEY){
  (async()=>{
    const r=await api('GET','/admin/account');
    if(r.status===401||r.status===0){logout()}else enter(r);
  })();
}
</script>
</body>
</html>
"""


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(ADMIN_HTML)


app.include_router(router)
app.include_router(router, prefix="/api")
import urllib.request
import urllib.parse
import os
import json
from fastapi import HTTPException

# أضف هذا المسار الجديد في نهاية ملف index.py
@app.get("/api/fetch_services")
def get_unlock_services():
    username = os.environ.get('IMEI_UNLOCK_USERNAME')
    api_key = os.environ.get('IMEI_UNLOCK_API_KEY')
    api_url = os.environ.get('IMEI_UNLOCK_API_URL')

    if not username or not api_key or not api_url:
        raise HTTPException(status_code=500, detail="Missing environment variables")

    payload = urllib.parse.urlencode({
        'username': username,
        'apiaccesskey': api_key
    }).encode('utf-8')

    try:
        req = urllib.request.Request(api_url, data=payload)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            return json.loads(result) # FastAPI سيقوم بتحويلها إلى JSON تلقائياً
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
import urllib.request
import urllib.parse
import os
import json
from fastapi import HTTPException

@app.get("/api/fetch_new_services")
def get_new_services():
    username = os.environ.get('NEW_API_USERNAME')
    api_key = os.environ.get('NEW_API_KEY')
    api_url = os.environ.get('NEW_API_URL')

    if not username or not api_key or not api_url:
        raise HTTPException(status_code=500, detail="Missing environment variables")

    payload = urllib.parse.urlencode({
        'username': username,
        'apiaccesskey': api_key,
        'action': 'imeiservicelist',
        'requestformat': 'JSON'
    }).encode('utf-8')

    try:
        req = urllib.request.Request(api_url, data=payload)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
