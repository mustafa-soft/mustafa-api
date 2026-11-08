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
# كل مورد: اسم للعرض، متغير الرابط، متغير المفتاح، ومتغير اسم المستخدم (اختياري)
# ---------------------------------------------------------------
SUPPLIERS = [
    {
        "name": "GalleUnlockers",
        "url_env": "GALLE_API_URL",
        "key_env": "GALLE_API_TOK",
        "user_env": None,
    },
    {
        "name": "imei-unlock.net",
        "url_env": "IMEI_UNLOCK_API_URL",
        "key_env": "IMEI_UNLOCK_API_KEY",
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
    key = (os.getenv(s["key_env"]) or "").strip()
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
                "time": TIME_OVERRIDES.get(str(pid)) or rule_time(p.get("name")) or p.get("time"),
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
        "storage": "redis" if REDIS else "memory",
        "platform": "vercel" if os.getenv("VERCEL") else "other",
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


@app.get("/admin/balances", dependencies=[Depends(require_admin)])
def balances():
    return [{"name": s["name"], **supplier_balance(s)} for s in SUPPLIERS]


@app.get("/products", dependencies=[Depends(require_admin)])
def products(product_id: str | None = Query(None, pattern=r"^[0-9A-Za-z-]{1,64}$")):
    # يعرض بيانات المزوّد الخام بأسعار الجملة: للإدارة فقط
    return cached_products(product_id)


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


# ---------------------------------------------------------------
# الطلبات: العميل يسجّل طلبًا، وأنت تؤكد الدفع ثم تنفّذه من /admin
# ---------------------------------------------------------------
ORDERS_FILE = os.getenv("ORDERS_FILE", "/tmp/orders.json")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
UP_URL = os.getenv("UPSTASH_REDIS_REST_URL", "").rstrip("/")
UP_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
REDIS = bool(UP_URL and UP_TOKEN)
HKEY = "ms:o"  # hash: الحقل = رقم الطلب، القيمة = بيانات الطلب
_mem, _mem_hits = {}, {}  # بديل للتجربة المحلية فقط


def _redis(cmd):
    r = requests.post(UP_URL, json=cmd, headers={"Authorization": f"Bearer {UP_TOKEN}"}, timeout=8)
    r.raise_for_status()
    return r.json().get("result")


def _r(cmd):
    try:
        return _redis(cmd)
    except Exception:
        raise HTTPException(status_code=503, detail="Storage unavailable")


def o_get(ref):
    if not REDIS:
        return _mem.get(ref)
    raw = _r(["HGET", HKEY, ref])
    return json.loads(raw) if raw else None


def o_set(o):
    if not REDIS:
        _mem[o["ref"]] = o
        return
    _r(["HSET", HKEY, o["ref"], json.dumps(o, ensure_ascii=False)])


def o_all():
    if not REDIS:
        return list(_mem.values())
    res = _r(["HGETALL", HKEY]) or []
    if not res:  # ترحيل لمرة واحدة من التخزين القديم
        old = _r(["GET", "ms:orders"])
        if old:
            orders = json.loads(old)
            for o in orders.values():
                o_set(o)
            return list(orders.values())
    return [json.loads(v) for v in res[1::2]]


def lock(ref, ttl=120):
    """قفل مشترك بين كل النسخ: يمنع تنفيذ الطلب مرتين."""
    if not REDIS:
        return True
    return _r(["SET", f"ms:lock:{ref}", "1", "NX", "EX", str(ttl)]) == "OK"


def unlock(ref):
    if REDIS:
        try:
            _redis(["DEL", f"ms:lock:{ref}"])
        except Exception:
            pass


def rate_ok(ip):
    if REDIS:
        k = f"ms:rl:{ip}"
        _r(["SET", k, "0", "EX", "3600", "NX"])
        return int(_r(["INCR", k])) <= 10
    now = time.time()
    hits = [t for t in _mem_hits.get(ip, []) if now - t < 3600]
    ok = len(hits) < 10
    hits.append(now)
    _mem_hits[ip] = hits
    return ok


def notify(text):
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": text},
            timeout=10,
        )
    except requests.RequestException:
        pass  # لا نسجّل الخطأ حتى لا يظهر التوكن في اللوجات


def get_product(pid):
    raw = cached_products()
    data = (raw.get("data") if isinstance(raw, dict) else None) or {}
    p = (data.get("products") or {}).get(str(pid))
    if not p:
        raise HTTPException(status_code=404, detail="Service not found")
    return p


def check_fields(p, values, qty):
    clean, has_qty = {}, False
    for f in p.get("fields") or []:
        if not isinstance(f, dict):
            continue
        name = f.get("name")
        if (f.get("type") or "").lower() == "quantity":
            has_qty = True
            try:
                lo, hi = int(f.get("min") or 1), int(f.get("max") or 100000)
            except ValueError:
                lo, hi = 1, 100000
            if not lo <= qty <= hi:
                raise HTTPException(status_code=422, detail=f"Quantity must be {lo}-{hi}")
            continue
        v = (values.get(name) or "").strip()
        if f.get("required") and not v:
            raise HTTPException(status_code=422, detail=f"Missing {name}")
        if v:
            if len(v) > 100:
                raise HTTPException(status_code=422, detail=f"{name} too long")
            if (f.get("type") == "imei" or str(name).lower() == "imei") and not re.fullmatch(r"\d{15}", v):
                raise HTTPException(status_code=422, detail="IMEI must be 15 digits")
            clean[name] = v
    if not has_qty and qty != 1:
        raise HTTPException(status_code=422, detail="Quantity must be 1")
    return clean, has_qty


class RequestIn(BaseModel):
    product_id: str = Field(pattern=r"^[0-9A-Za-z-]{1,64}$")
    values: dict[str, str] = Field(default_factory=dict)
    quantity: int = Field(default=1, ge=1, le=100000)


@app.post("/request")
def create_request(item: RequestIn, request: Request):
    fwd = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")
    if not rate_ok(fwd.split(",")[0].strip()):
        raise HTTPException(status_code=429, detail="Too many requests")
    if REDIS and int(_r(["HLEN", HKEY]) or 0) >= 5000:
        raise HTTPException(status_code=503, detail="Busy, try later")
    p = get_product(item.product_id)
    clean, has_qty = check_fields(p, item.values, item.quantity)
    cost = float(p.get("price") or 0)
    unit = sale_price(cost, p.get("cid"))
    if unit is None:
        raise HTTPException(status_code=503, detail="Price unavailable")
    if unit <= 0 or cost <= 0:
        raise HTTPException(status_code=422, detail="Service not available for ordering")
    ref = "ms-" + uuid.uuid4().hex[:20]
    order = {
        "ref": ref, "created": time.time(), "product_id": str(item.product_id), "name": p.get("name"),
        "fields": clean, "has_qty": has_qty, "qty": item.quantity,
        "total": round(unit * item.quantity, 2), "cost": round(cost * item.quantity, 2),
        "status": "pending", "error": None, "uuid": None, "provider": None,
    }
    o_set(order)
    notify(f"طلب جديد {ref}\n{order['name']}\nالكمية: {item.quantity}\nالإجمالي: ${order['total']}\n{clean}")
    return {"ref": ref, "total": order["total"], "status": "pending"}


@app.get("/admin/orders", dependencies=[Depends(require_admin)])
def admin_orders():
    now, out = time.time(), []
    for o in o_all():
        if o["status"] == "sending" and now - o.get("sent_at", now) > 300:
            o["status"] = "unknown"
            o["error"] = "انقطع التنفيذ دون رد. تحقق من حسابك عند GalleUnlockers قبل أي إعادة."
            o_set(o)
        out.append(o)
    return sorted(out, key=lambda o: o["created"], reverse=True)[:200]


@app.post("/admin/orders/{ref}/execute", dependencies=[Depends(require_admin)])
def admin_execute(ref: str):
    if not PUBLIC_URL.startswith("https://"):
        raise HTTPException(status_code=503, detail="PUBLIC_URL (https) is not configured")
    if not lock(ref, 120):
        raise HTTPException(status_code=409, detail="Order is being processed")
    try:
        o = o_get(ref)
        if not o:
            raise HTTPException(status_code=404, detail="Order not found")
        if o["status"] != "pending":
            raise HTTPException(status_code=409, detail=f"Order is {o['status']}")
        o["status"], o["sent_at"] = "sending", time.time()
        o_set(o)  # نحفظ الحالة قبل الاتصال بالمزوّد، فلا يتكرر التنفيذ حتى لو انقطع الرد
        fields = dict(o["fields"])
        fields.update({"feedback_url": f"{PUBLIC_URL}/callback", "reference_id": ref})
        if o["has_qty"]:
            fields["Quantity"] = o["qty"]
        pid = o["product_id"]
        payload = [{"product_id": int(pid) if pid.isdigit() else pid, "fields": [fields]}]
        try:
            res = call_api("POST", "/order", body=payload, timeout=55)
        except HTTPException as e:
            # رفض واضح من المزوّد: يرجع للانتظار. غير ذلك: النتيجة مجهولة فلا نكرر تلقائيًا
            o["status"] = "pending" if 400 <= e.status_code < 500 else "unknown"
            o["error"] = str(e.detail)
            o_set(o)
            raise
        o["status"], o["provider"], o["error"] = "submitted", res, None
        try:
            o["uuid"] = res["data"][0][0]["order_uuid"]
        except (KeyError, IndexError, TypeError):
            pass
        o_set(o)
        return o
    finally:
        unlock(ref)


@app.post("/admin/orders/{ref}/reject", dependencies=[Depends(require_admin)])
def admin_reject(ref: str):
    if not lock(ref, 30):
        raise HTTPException(status_code=409, detail="Order is being processed")
    try:
        o = o_get(ref)
        if not o or o["status"] not in ("pending", "unknown"):
            raise HTTPException(status_code=409, detail="Cannot reject")
        o["status"] = "rejected"
        o_set(o)
        return o
    finally:
        unlock(ref)


@app.get("/admin/orders/{ref}/refresh", dependencies=[Depends(require_admin)])
def admin_refresh(ref: str):
    o = o_get(ref)
    if not o or not o.get("uuid"):
        raise HTTPException(status_code=404, detail="No provider order yet")
    res = call_api("GET", "/order", params={"order_uuid": o["uuid"]})
    if not lock(ref, 30):
        raise HTTPException(status_code=409, detail="Order is being processed")
    try:
        o = o_get(ref) or o
        o["provider"] = res
        o_set(o)
        return o
    finally:
        unlock(ref)


ADMIN_HTML = r"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>لوحة الإدارة</title>
<style>body{font-family:system-ui,sans-serif;background:#F8FAFC;color:#0F172A;margin:0;padding:16px;max-width:860px;margin-inline:auto;overflow-wrap:anywhere;word-break:break-word}input,button{font:inherit;padding:10px 14px;border-radius:10px;border:1px solid #CBD5E1}button{background:#0F172A;color:#fff;border:0;cursor:pointer;margin:4px 0 0 6px}button.g{background:#E2E8F0;color:#0F172A}.c{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:14px;margin:10px 0}.m{color:#64748B;font-size:13px}.s{display:inline-block;padding:2px 10px;border-radius:99px;background:#E2E8F0;font-size:12px}.e{color:#B91C1C;font-size:13px}[hidden]{display:none!important}pre{max-width:100%;overflow-wrap:anywhere;white-space:pre-wrap;direction:ltr;text-align:left;font-size:12px;background:#F1F5F9;padding:8px;border-radius:8px;margin:6px 0}</style></head><body>
<h1>لوحة الإدارة</h1>
<div id="login" class="c"><input id="key" type="password" placeholder="كلمة سر الإدارة" autocomplete="off"><button id="go">دخول</button><p class="m" id="msg"></p></div>
<div id="app" hidden>
<div class="c"><div class="m">أرصدة الموردين</div><div id="bal">...</div><button class="g" id="rf">تحديث</button></div>
<h2>الطلبات</h2><div id="list"></div></div>
<script>
let K='';const $=i=>document.getElementById(i);
const ST={pending:'بانتظار تأكيد الدفع',sending:'جاري الإرسال',submitted:'تم الإرسال للمزوّد',unknown:'نتيجة غير مؤكدة: تحقق من المورد',rejected:'مرفوض'};
async function api(p,m){const r=await fetch(p,{method:m||'GET',headers:{'X-Admin-Key':K}});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(typeof d.detail==='string'?d.detail:r.status);return d}
function el(t,c,x){const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
async function load(){
  try{
    const bs=await api('/admin/balances');
    $('bal').innerHTML='';
    bs.forEach(b=>$('bal').append(el('div','',b.error
      ? b.name+': '+b.error
      : b.name+': '+(b.balance??'?')+' '+(b.currency||''))));
  }catch(e){$('bal').textContent='تعذر قراءة الأرصدة: '+e.message}
  const os=await api('/admin/orders');const L=$('list');L.innerHTML='';
  if(!os.length)L.append(el('p','m','لا توجد طلبات بعد.'));
  os.forEach(o=>{
    const c=el('div','c');c.append(el('b','',o.name),el('div','m',new Date(o.created*1000).toLocaleString('ar')+' | '+o.ref));
    c.append(el('pre','',Object.entries(o.fields).map(([k,v])=>k+': '+v).join('\n')+'\nالكمية: '+o.qty));
    c.append(el('div','',`الإجمالي: $${o.total} | تكلفتك: $${o.cost} | ربحك: $${(o.total-o.cost).toFixed(2)}`));
    c.append(el('span','s',ST[o.status]||o.status));
    if(o.error)c.append(el('div','e',o.error));
    const act=(t,fn,g)=>{const b=el('button',g?'g':'',t);b.onclick=async()=>{b.disabled=true;try{await fn()}catch(e){alert(e.message)}load()};c.append(b)};
    if(o.status==='pending')act('أكدت الدفع، نفّذ الآن',()=>confirm('سيتم خصم التكلفة من رصيدك. متأكد من استلام الدفع؟')?api('/admin/orders/'+o.ref+'/execute','POST'):0);
    if(o.status==='pending'||o.status==='unknown')act('رفض',()=>api('/admin/orders/'+o.ref+'/reject','POST'),1);
    if(o.uuid)act('تحديث الحالة',()=>api('/admin/orders/'+o.ref+'/refresh'),1);
    if(o.provider&&o.uuid){const st=(o.provider.data&&o.provider.data.status)||'';if(st)c.append(el('div','m','حالة المزوّد: '+st))}
    if(o.status==='submitted')c.append(el('div','m','رد المزوّد: '+((o.provider&&o.provider.message)||'-')+(o.uuid?'':' | لا يوجد رقم متابعة، راجع الطلب في المورد')));
    L.append(c)})}
$('go').onclick=async()=>{K=$('key').value;try{await api('/admin/orders');$('login').hidden=true;$('app').hidden=false;load()}catch(e){$('msg').textContent='كلمة السر غير صحيحة'}};
$('rf').onclick=load;
</script></body></html>"""


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return ADMIN_HTML
