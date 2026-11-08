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
    token: str = Field(..., min_length=10, max_length=5000)


@router.get("/health")
def health():
    return {
        "ok": True,
        "redis": REDIS,
        "supplier": bool(GALLE_URL and GALLE_KEY),
        "telegram": bool(TG_TOKEN and TG_CHAT),
        "admin": bool(ADMIN_SECRET),
        "imei_unlock": IU_ENABLED,
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
    payload = read_token(body.token)
    product = find_product(payload.get("p"))
    if not product:
        raise HTTPException(status_code=404, detail="Product no longer available")

    if product.get("supplier") == "iu":
        return {
            "ok": True,
            "manual": True,
            "supplier": "imei-unlock.net",
            "service_id": product["id"].replace("iu-", "", 1),
            "service": product["name"],
            "quantity": int(payload.get("q") or 1),
            "fields": payload.get("f") or {},
            "note": "نفّذ هذا الطلب يدويًا من لوحة imei-unlock.net بعد تأكيد الدفع.",
        }

    h = token_hash(body.token)
    ref_id = "ms-" + h[:24]
    if not lock(f"place:{ref_id}", 600):
        raise HTTPException(status_code=409, detail="Already submitted, check the supplier panel")

    order_obj = dict(payload.get("f") or {})
    order_obj.update(
        {
            "feedback_url": f"{public_base(request)}/callback",
            "reference_id": ref_id,
            "Quantity": int(payload.get("q") or 1),
        }
    )
    pid = product["id"]
    req_body = [{"product_id": int(pid) if pid.isdigit() else pid, "fields": [order_obj]}]

    try:
        resp = fusion("POST", "/order", body=req_body, timeout=ORDER_TIMEOUT, write=True)
    except OrderUnknown:
        notify(f"نتيجة غير معروفة للطلب {ref_id}. لا تعد الإرسال، راجع لوحة المورد بهذا المرجع.")
        return JSONResponse(
            status_code=202,
            content={
                "ok": False,
                "unknown": True,
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

    notify(f"أُرسل للمورد: {ref_id}\norder_uuid: {item.get('order_uuid')}")
    return {
        "ok": True,
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
    if status in ("success", "rejected") and lock(f"cb:{order_id}:{status}", 3600):
        notify(f"تحديث الطلب {ref}\nالحالة: {status}\nالرد: {str(d.get('replay') or '')[:600]}")
    return {"ok": True}


# ------------------ صفحة بسيطة للتنفيذ ------------------
ADMIN_HTML = r"""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mustafa Soft Admin</title>
<style>
body{font-family:sans-serif;max-width:640px;margin:16px auto;padding:0 12px}
input,textarea,button{width:100%;box-sizing:border-box;padding:10px;margin:6px 0;font-size:16px}
button{background:#111;color:#fff;border:0;border-radius:8px}
pre{white-space:pre-wrap;word-break:break-all;background:#f3f3f3;padding:10px;border-radius:8px}
</style></head><body>
<h3>تنفيذ الطلبات</h3>
<input id="k" type="password" placeholder="Admin key">
<button onclick="call('GET','account')">الرصيد</button>
<textarea id="t" rows="4" placeholder="الصق رمز الطلب من تيليجرام"></textarea>
<button onclick="place()">تنفيذ عند المورد (بعد تأكيد الدفع)</button>
<input id="u" placeholder="order_uuid">
<button onclick="status()">حالة طلب</button>
<pre id="o"></pre>
<script>
const base=location.pathname.replace(/\/+$/,'');
async function call(m,p,b){
  const o=document.getElementById('o');o.textContent='...';
  try{
    const r=await fetch(base+'/'+p,{method:m,headers:{'Content-Type':'application/json','X-Admin-Key':document.getElementById('k').value.trim()},body:b?JSON.stringify(b):undefined});
    const j=await r.json().catch(()=>({}));
    o.textContent=r.status+'\n'+JSON.stringify(j,null,2);
  }catch(e){o.textContent='خطأ اتصال';}
}
function place(){
  const t=document.getElementById('t').value.trim();
  if(!t)return;
  if(!confirm('تنفيذ الطلب وخصم الرصيد؟'))return;
  call('POST','place',{token:t});
}
function status(){
  call('GET','status?uuid='+encodeURIComponent(document.getElementById('u').value.trim()));
}
</script></body></html>"""


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(ADMIN_HTML)


app.include_router(router)
app.include_router(router, prefix="/api")
