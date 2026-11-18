import os
import re
import time
import hmac
import json
import base64
import hashlib
from urllib.parse import urlparse
import logging
import requests
try:
    import bcrypt
except ImportError:
    bcrypt = None
from fastapi import FastAPI, APIRouter, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mustafa-api")
app = FastAPI(title="Mustafa Soft API")
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
GALLE_KEY = next((v for v in (env("GALLE_API_TOK"), env("GALLE_API_TOKEN"), env("GALLE_TOKEN")) if v), "")
IU_URL = env("IMEI_UNLOCK_API_URL").rstrip("/")
IU_USER = env("IMEI_UNLOCK_USERNAME")
IU_KEY = env("IMEI_UNLOCK_API_KEY")
IU_PROXY_URL = env("IMEI_UNLOCK_PROXY_URL").rstrip("/")
IU_PROXY_KEY = env("IMEI_UNLOCK_PROXY_KEY")
IU_ENABLED = bool(IU_USER and IU_KEY and (IU_URL or (IU_PROXY_URL and IU_PROXY_KEY)))
L2U_URL = env("L2U_API_URL").rstrip("/")
L2U_USER = env("L2U_USERNAME")
L2U_KEY = env("L2U_API_KEY")
L2U_ENABLED = bool(L2U_URL and L2U_USER and L2U_KEY)
IMS_URL = env("IMEISERVER_API_URL").rstrip("/")
IMS_USER = env("IMEISERVER_USERNAME")
IMS_KEY = env("IMEISERVER_API_KEY")
IMS_ENABLED = bool(IMS_URL and IMS_USER and IMS_KEY)
# --- imeiveserver.com (Dhru Fusion) ---
VE_URL = env("IMEI_VE_SERVER_API_URL").rstrip("/") or "https://imeiveserver.com"
VE_USER = env("IMEI_VE_SERVER_USERNAME")
VE_KEY = env("IMEI_VE_SERVER_API_KEY")
VE_ENABLED = bool(VE_USER and VE_KEY)
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
TIME_RULES = env_json("TIME_RULES", [[["honor frp", "offline) fast"], "1-7 ساعات (قد تتأخر بعض الحالات)"]])
_origins = {ALLOWED_ORIGIN}
if "://www." in ALLOWED_ORIGIN:
    _origins.add(ALLOWED_ORIGIN.replace("://www.", "://"))
else:
    _origins.add(ALLOWED_ORIGIN.replace("://", "://www.", 1))
app.add_middleware(CORSMiddleware, allow_origins=sorted(_origins), allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "X-Admin-Key"])
_mem_hits = {}
_mem_locks = {}
_cache = {}
CACHE_TTL = 300
def _redis(cmd):
    r = requests.post(UP_URL, json=cmd, headers={"Authorization": f"Bearer {UP_TOKEN}"}, timeout=8)
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
def require_admin(x_admin_key: str = Header("")):
    key = x_admin_key.strip()
    if not ADMIN_SECRET or not hmac.compare_digest(key.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")
class OrderUnknown(Exception):
    pass
def fusion(method, path, params=None, body=None, timeout=30, write=False):
    if not GALLE_KEY or not GALLE_URL:
        raise HTTPException(status_code=503, detail="Supplier not configured")
    try:
        r = requests.request(method, f"{GALLE_URL}{path}", headers={"Authorization": f"Bearer {GALLE_KEY}", "Accept": "application/json"}, params=params, json=body, timeout=timeout)
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
        raise HTTPException(status_code=502, detail=f"Provider returned HTTP {r.status_code} (not JSON)")
    if r.status_code >= 400 or data.get("status") != "success":
        code = data.get("code")
        status = r.status_code if r.status_code >= 400 else (code if isinstance(code, int) and code >= 400 else 400)
        msg = data.get("message") or "Provider error"
        headers = {}
        if r.headers.get("Retry-After"):
            headers["Retry-After"] = r.headers["Retry-After"]
        if status in (401, 402, 403):
            log.error("supplier auth/balance error: HTTP %s", status)
            raise HTTPException(status_code=502, detail=f"Supplier auth/balance error (HTTP {status}): {msg}")
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
        items.append({"id": str(pid), "name": p.get("name", ""), "type": p.get("type", ""), "category_id": cid, "category": cat_name, "cost": cost, "price": markup_price(cost, cid, cat_name), "time": time_text(pid, p.get("name", ""), p.get("time", "")), "fields": fields, "supplier": "galle"})
    return d.get("currency", "USD"), list(categories.values()), items
def _num(v):
    m = re.search(r"\d+(?:\.\d+)?", str(v if v is not None else ""))
    return float(m.group()) if m else 0.0
def iu_call(action, timeout=30):
    use_proxy = bool(IU_PROXY_URL and IU_PROXY_KEY)
    try:
        if use_proxy:
            relay = IU_PROXY_URL if IU_PROXY_URL.lower().endswith(".php") else IU_PROXY_URL + "/iu"
            r = requests.post(relay, data={"username": IU_USER, "apiaccesskey": IU_KEY, "action": action}, headers={"X-Proxy-Key": IU_PROXY_KEY}, timeout=timeout)
        else:
            url = IU_URL if IU_URL.lower().endswith(".php") else IU_URL + "/api/index.php"
            r = requests.post(url, data={"username": IU_USER, "apiaccesskey": IU_KEY, "action": action, "requestformat": "JSON"}, timeout=timeout)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="imei-unlock proxy unreachable" if use_proxy else "imei-unlock unreachable")
    try:
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except ValueError:
        raise HTTPException(status_code=502, detail=f"imei-unlock returned HTTP {r.status_code} (not JSON)")
    if use_proxy and data.get("error"):
        raise HTTPException(status_code=502, detail=f"imei-unlock proxy error (HTTP {r.status_code}): {data.get('error')}")
    err = data.get("ERROR")
    if err:
        msg = err[0].get("MESSAGE") if isinstance(err, list) and err and isinstance(err[0], dict) else str(err)[:200]
        raise HTTPException(status_code=502, detail=f"imei-unlock error: {msg}")
    return data
_TRUE = ("1", "true", "yes", "on", "y")
def _truthy(v):
    return str(v).strip().lower() in _TRUE
def first_success(j):
    succ = j.get("SUCCESS") if isinstance(j, dict) else None
    if isinstance(succ, list) and succ and isinstance(succ[0], dict):
        return succ[0]
    return succ if isinstance(succ, dict) else {}
def parse_dhru_services(data, prefix, supplier):
    lst = first_success(data).get("LIST") or {}
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
            sid = prefix + str(sv["SERVICEID"])
            cost = _num(sv.get("CREDIT"))
            cid = prefix + gname
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
                        fields.append({"type": str(c.get("fieldtype") or "text").lower(), "name": str(nm), "required": _truthy(c.get("required"))})
            qmax = int(_num(sv.get("MAXQNT")))
            if qmax > 1:
                fields.append({"type": "quantity", "name": "Quantity", "min": max(1, int(_num(sv.get("MINQNT")))), "max": qmax})
            name = str(sv.get("SERVICENAME") or "")
            items.append({"id": sid, "name": name, "type": gtype, "category_id": cid, "category": gname, "cost": cost, "price": markup_price(cost, cid, gname), "time": time_text(sid, name, str(sv.get("TIME") or "")), "fields": fields, "supplier": supplier})
    return items
def catalog_iu():
    now = time.time()
    hit = _cache.get("iu")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    items = parse_dhru_services(iu_call("imeiservicelist"), "iu-", "iu")
    _cache["iu"] = (now, items)
    return items

def _webx_auth():
    if bcrypt is None:
        raise HTTPException(status_code=503, detail="bcrypt not installed (add 'bcrypt' to requirements.txt)")
    raw = (IMS_USER + IMS_KEY).encode()[:72]
    h = bcrypt.hashpw(raw, bcrypt.gensalt(rounds=10))
    return h.replace(b"$2b$", b"$2y$", 1).decode()
def _webx_errors(j):
    errs = j.get("errors")
    if isinstance(errs, dict):
        errs = list(errs.values())
    parts = []
    for e in errs if isinstance(errs, list) else [errs]:
        parts.append(", ".join(str(x) for x in e) if isinstance(e, (list, tuple)) else str(e))
    return "; ".join(parts)[:200]
def webx_call(route="", params=None, method="GET", timeout=30, write=False):
    base = IMS_URL if "://" in IMS_URL else "https://" + IMS_URL
    base = base.rstrip("/")
    if base.lower().endswith("/dhru"):
        base = base[:-5]
    url = f"{base}/api/{route}"
    p = dict(params or {})
    p["username"] = IMS_USER
    headers = {"Accept": "application/json", "Auth-Key": _webx_auth()}
    try:
        if method == "POST":
            r = requests.post(url, data=p, headers=headers, timeout=timeout)
        else:
            r = requests.get(url, params=p, headers=headers, timeout=timeout)
    except requests.RequestException:
        if write:
            raise OrderUnknown("request failed")
        raise HTTPException(status_code=502, detail="imeiserver unreachable")
    try:
        j = r.json()
        if not isinstance(j, (dict, list)):
            raise ValueError("unexpected body")
    except ValueError:
        if write and (r.status_code < 400 or r.status_code >= 500):
            raise OrderUnknown("invalid response")
        raise HTTPException(status_code=502, detail=f"imeiserver returned HTTP {r.status_code} (not JSON)")
    if isinstance(j, dict) and j.get("errors"):
        raise HTTPException(status_code=502, detail=f"imeiserver error: {_webx_errors(j)}")
    if r.status_code >= 500 and write:
        raise OrderUnknown("server error")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"imeiserver HTTP {r.status_code}")
    return j
def _label(x):
    if isinstance(x, dict):
        return str(x.get("name") or x.get("label") or x.get("title") or "")
    return str(x or "")
def _webx_extra_fields(raw):
    items = list(raw.values()) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
    out = []
    for d in items:
        if not isinstance(d, dict):
            continue
        nm = str(d.get("label") or d.get("name") or d.get("key") or "")
        if nm:
            out.append({"type": "text", "name": nm, "required": _truthy(d.get("required"))})
    return out
def parse_webx_services(data, kind):
    if isinstance(data, dict):
        inner = data.get("data") if isinstance(data.get("data"), (list, dict)) else data
        services = list(inner.values()) if isinstance(inner, dict) else inner
    else:
        services = data
    items = []
    for sv in services or []:
        if not isinstance(sv, dict) or sv.get("id") in (None, ""):
            continue
        sid = f"ims-{kind}-{sv['id']}"
        cost = _num(sv.get("credits"))
        name = str(sv.get("name") or "")
        cat = _label(sv.get("category")) or _label(sv.get("group")) or ("IMEIServer IMEI" if kind == "i" else "IMEIServer Server")
        cid = "ims-" + cat
        extra = _webx_extra_fields(sv.get("fields"))
        fields = ([{"type": "imei", "name": "IMEI", "required": True}] if kind == "i" else []) + extra
        items.append({"id": sid, "name": name, "type": "imei" if kind == "i" else "server", "category_id": cid, "category": cat, "cost": cost, "price": markup_price(cost, cid, cat), "time": time_text(sid, name, str(sv.get("time") or "")), "fields": fields, "supplier": "ims", "auto": not extra})
    return items
def catalog_ims():
    now = time.time()
    hit = _cache.get("ims")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    items, last_err = [], None
    for route, kind in (("imei-services", "i"), ("server-services", "s")):
        try:
            raw = webx_call(route)
        except HTTPException as e:
            last_err = e
            log.error("imeiserver %s failed: %s", route, e.detail)
            continue
        part = parse_webx_services(raw, kind)
        if part:
            lst = raw.get("data") if isinstance(raw, dict) and isinstance(raw.get("data"), list) else raw
            first = (list(lst.values()) if isinstance(lst, dict) else lst)
            if first and "ims_sample" not in _cache:
                _cache["ims_sample"] = first[0]
        items += part
    if not items and last_err:
        raise last_err
    _cache["ims"] = (now, items)
    return items
def _webx_status(uuid, j):
    try:
        st = int(j.get("status"))
    except (TypeError, ValueError, AttributeError):
        st = None
    status = {4: "success", 3: "rejected", 2: "rejected"}.get(st, "sent")
    resp = j.get("response") if isinstance(j, dict) else ""
    replay = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
    if status in ("success", "rejected"):
        _apply_final(uuid, status, replay)
    return {"status": status, "replay": replay, "code_status": st}
def l2u_call(action, params=None, timeout=30, write=False):
    p = urlparse(L2U_URL if "://" in L2U_URL else "https://" + L2U_URL)
    url = f"{p.scheme}://{p.netloc}/public/api/index.php"
    data = {"username": L2U_USER, "apiaccesskey": L2U_KEY, "action": action, "requestformat": "JSON", "parameters": base64.b64encode(json.dumps(params).encode()).decode() if params else ""}
    try:
        r = requests.post(url, data=data, timeout=timeout)
    except requests.RequestException:
        if write:
            raise OrderUnknown("request failed")
        raise HTTPException(status_code=502, detail="lock2unlock unreachable")
    try:
        j = r.json()
        if not isinstance(j, dict):
            raise ValueError("not an object")
    except ValueError:
        if write and (r.status_code < 400 or r.status_code >= 500):
            raise OrderUnknown("invalid response")
        raise HTTPException(status_code=502, detail=f"lock2unlock returned HTTP {r.status_code} (not JSON)")
    err = j.get("ERROR")
    if err:
        msg = err[0].get("MESSAGE") if isinstance(err, list) and err and isinstance(err[0], dict) else str(err)[:200]
        raise HTTPException(status_code=502, detail=f"lock2unlock error: {str(msg)[:200]}")
    if r.status_code >= 500 and write:
        raise OrderUnknown("server error")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"lock2unlock HTTP {r.status_code}")
    return j
def catalog_l2u():
    now = time.time()
    hit = _cache.get("l2u")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    items = parse_dhru_services(l2u_call("imeiservicelist"), "l2-", "l2u")
    _cache["l2u"] = (now, items)
    return items
# --- imeiveserver (Dhru) ---
def ve_call(action, timeout=30, write=False):
    url = VE_URL if VE_URL.lower().endswith(".php") else VE_URL.rstrip("/") + "/api/index.php"
    try:
        r = requests.post(url, data={"username": VE_USER, "apiaccesskey": VE_KEY, "action": action, "requestformat": "JSON"}, timeout=timeout)
    except requests.RequestException:
        if write:
            raise OrderUnknown("request failed")
        raise HTTPException(status_code=502, detail="imeiveserver unreachable")
    try:
        j = r.json()
        if not isinstance(j, dict):
            raise ValueError("not an object")
    except ValueError:
        if write and (r.status_code < 400 or r.status_code >= 500):
            raise OrderUnknown("invalid response")
        raise HTTPException(status_code=502, detail=f"imeiveserver returned HTTP {r.status_code} (not JSON)")
    err = j.get("ERROR")
    if err:
        msg = err[0].get("MESSAGE") if isinstance(err, list) and err and isinstance(err[0], dict) else str(err)[:200]
        raise HTTPException(status_code=502, detail=f"imeiveserver error: {str(msg)[:200]}")
    return j
def catalog_ve():
    now = time.time()
    hit = _cache.get("ve")
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    items = parse_dhru_services(ve_call("imeiservicelist"), "ve-", "ve")
    _cache["ve"] = (now, items)
    return items
def catalog():
    extra = []
    for enabled, fn, label in ((IU_ENABLED, catalog_iu, "imei-unlock"), (L2U_ENABLED, catalog_l2u, "lock2unlock"), (IMS_ENABLED, catalog_ims, "imeiserver"), (VE_ENABLED, catalog_ve, "imeiveserver")):
        if not enabled:
            continue
        try:
            extra += fn()
        except HTTPException as e:
            log.error("%s catalog failed: %s", label, e.detail)
    others = IU_ENABLED or L2U_ENABLED or IMS_ENABLED or VE_ENABLED
    currency, cats, items = "USD", [], []
    try:
        currency, cats, items = catalog_galle()
    except HTTPException as e:
        if not others:
            raise
        log.error("galle catalog failed: %s", e.detail)
    return currency, cats, items + extra
def find_product(pid):
    _, _, items = catalog()
    return next((i for i in items if i["id"] == str(pid)), None)
def notify(text):
    if not (TG_TOKEN and TG_CHAT):
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id": TG_CHAT, "text": text[:4000]}, timeout=8)
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
def _sign(data):
    return hmac.new(ADMIN_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:32]
def make_token(payload):
    raw = base64.urlsafe_b64encode(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()).decode().rstrip("=")
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
    return {"ok": True, "redis": REDIS, "supplier": bool(GALLE_URL and GALLE_KEY), "telegram": bool(TG_TOKEN and TG_CHAT), "admin": bool(ADMIN_SECRET), "imei_unlock": IU_ENABLED, "lock2unlock": L2U_ENABLED, "imeiserver": IMS_ENABLED, "imeiveserver": VE_ENABLED, "env": env("VERCEL_ENV"), "commit": env("VERCEL_GIT_COMMIT_SHA")[:7]}
@router.get("/catalog")
def catalog_route(limit: int = 200, offset: int = 0, q: str = ""):
    currency, _, items = catalog()
    ql = q.strip().lower()
    if ql:
        items = [i for i in items if ql in (i["name"] or "").lower()]
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    page = items[offset:offset + limit]
    return {"currency": currency, "total": len(items), "items": [{k: v for k, v in i.items() if k not in ("cost", "supplier", "auto")} for i in page]}
def build_fields(product, values):
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
            if (ftype == "email" or name.lower() == "email") and not EMAIL_RE.match(val):
                raise HTTPException(status_code=422, detail="Invalid email")
            out[name] = val
    return out, qmin, qmax
@router.post("/request")
def create_request(body: RequestIn, request: Request):
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
    dedupe = hashlib.sha1(json.dumps([product["id"], fields, body.quantity], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if not lock(f"new:{dedupe}", 60):
        raise HTTPException(status_code=409, detail="Duplicate request, wait a minute")
    payload = {"p": product["id"], "n": product["name"], "f": fields, "q": body.quantity, "pr": product["price"], "t": int(time.time())}
    token = make_token(payload)
    code = "MS-" + token_hash(token)[:8].upper()
    total = round(product["price"] * body.quantity, 2)
    lines = "\n".join(f"{k}: {v}" for k, v in fields.items()) or "-"
    sent = notify(f"طلب جديد {code}\nالخدمة: {product['name']}\nالمورد: {({'iu': 'imei-unlock.net (تنفيذ يدوي)', 'ims': 'imeiserver.com (تنفيذ يدوي)', 'l2u': 'lock2unlock', 've': 'imeiveserver.com (تنفيذ يدوي)'}).get(product.get('supplier'), 'GalleUnlockers')}\nالكمية: {body.quantity}\nالإجمالي: ${total}\n{lines}\n\nبعد تأكيد الدفع الصق الرمز في /admin:\n{token}")
    if not sent:
        unlock(f"new:{dedupe}")
        raise HTTPException(status_code=502, detail="Could not deliver the request")
    order_save({"code": code, "pid": product["id"], "name": product["name"], "supplier": product.get("supplier"), "fields": fields, "q": body.quantity, "total": total, "t": payload["t"], "status": "pending", "token": token})
    return {"ok": True, "ref": code, "price": total}
@router.get("/selftest")
def selftest(k: str = "", fresh: int = 0):
    if not ADMIN_SECRET or not hmac.compare_digest(k.encode(), ADMIN_SECRET.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if fresh:
        _cache.clear()
    out = {"telegram_configured": bool(TG_TOKEN and TG_CHAT)}
    try:
        out["vercel_outbound_ip"] = requests.get("https://api.ipify.org", timeout=6).text.strip()[:45]
    except Exception:
        out["vercel_outbound_ip"] = "unknown"
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id": TG_CHAT, "text": "selftest ok"}, timeout=8)
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
    if L2U_ENABLED:
        try:
            out["lock2unlock_services"] = len(catalog_l2u())
        except HTTPException as e:
            out["lock2unlock_error"] = e.detail
    else:
        out["lock2unlock"] = "not configured"
    if IMS_ENABLED:
        try:
            ai = webx_call("")
            out["imeiserver_account"] = {k: ai.get(k) for k in ("balance", "currency")} if isinstance(ai, dict) else "?"
        except HTTPException as e:
            out["imeiserver_error"] = e.detail
        try:
            out["imeiserver_services"] = len(catalog_ims())
            out["imeiserver_sample"] = json.dumps(_cache.get("ims_sample"), ensure_ascii=False)[:700]
        except HTTPException as e:
            out["imeiserver_services_error"] = e.detail
    else:
        out["imeiserver"] = "not configured"
    if VE_ENABLED:
        try:
            out["imeiveserver_services"] = len(catalog_ve())
        except HTTPException as e:
            out["imeiveserver_error"] = e.detail
    else:
        out["imeiveserver"] = "not configured"
    try:
        _, _, items = catalog()
        out["catalog_items"] = len(items)
        out["sample_product_id"] = items[0]["id"] if items else None
    except HTTPException as e:
        out["catalog_error"] = {"http": e.status_code, "detail": e.detail}
    return out

def _place_l2u(rec, product, payload, token, code, qty):
    h = token_hash(token)
    ref_id = "ms-" + h[:24]
    if not lock(f"place:{ref_id}", 600):
        raise HTTPException(status_code=409, detail="Already submitted, check the supplier panel")
    key = str(int(h[:8], 16))
    sid = product["id"].replace("l2-", "", 1)
    fields_b64 = base64.b64encode(json.dumps(payload.get("f") or {}, ensure_ascii=False).encode()).decode()
    params = {key: {"ID": int(sid) if sid.isdigit() else sid, "QNT": qty, "CUSTOMFIELD": fields_b64}}
    def unknown():
        rec.update(status="unknown", reference_id=ref_id)
        order_save(rec)
        notify(f"نتيجة غير معروفة للطلب {ref_id}. لا تعد الإرسال، راجع لوحة lock2unlock بهذا المرجع.")
        return JSONResponse(status_code=202, content={"ok": False, "unknown": True, "code": code, "reference_id": ref_id, "detail": "Outcome unknown. Do NOT retry. Check the supplier panel."})
    try:
        resp = l2u_call("placebulkorder", params, timeout=ORDER_TIMEOUT, write=True)
    except OrderUnknown:
        return unknown()
    except HTTPException:
        unlock(f"place:{ref_id}")
        raise
    succ = resp.get("SUCCESS")
    item = None
    if isinstance(succ, dict):
        item = succ.get(key)
        if item is None and len(succ) == 1:
            item = next(iter(succ.values()))
    if not isinstance(item, dict):
        return unknown()
    if str(item.get("status")).lower() != "success":
        unlock(f"place:{ref_id}")
        raise HTTPException(status_code=400, detail=str(item.get("message") or "Rejected")[:200])
    uuid_ = f"l2-{item.get('referenceid')}"
    rec.update(status="sent", reference_id=ref_id, order_uuid=uuid_)
    order_save(rec)
    notify(f"أُرسل إلى lock2unlock: {ref_id}\nالرقم: {uuid_}")
    return {"ok": True, "code": code, "reference_id": ref_id, "order_uuid": uuid_, "note": item.get("message")}
def _place_ims(rec, product, payload, token, code, qty):
    h = token_hash(token)
    ref_id = "ms-" + h[:24]
    fields = payload.get("f") or {}
    kind = product["id"].split("-")[1]
    sid = product["id"].rsplit("-", 1)[1]
    data = {"service_id": sid, "comments": f"MS {code}"}
    if kind == "i":
        device = str(fields.get("IMEI") or "").strip()
        if not device:
            raise HTTPException(status_code=422, detail="IMEI missing")
        data["device"] = device
        route = "imei-orders"
    else:
        data["quantity"] = qty
        route = "server-orders"
    if not lock(f"place:{ref_id}", 600):
        raise HTTPException(status_code=409, detail="Already submitted, check the supplier panel")
    def unknown():
        rec.update(status="unknown", reference_id=ref_id)
        order_save(rec)
        notify(f"نتيجة غير معروفة للطلب {ref_id}. لا تعد الإرسال، راجع لوحة imeiserver.")
        return JSONResponse(status_code=202, content={"ok": False, "unknown": True, "code": code, "reference_id": ref_id, "detail": "Outcome unknown. Do NOT retry. Check the supplier panel."})
    try:
        resp = webx_call(route, data, "POST", timeout=ORDER_TIMEOUT, write=True)
    except OrderUnknown:
        return unknown()
    except HTTPException:
        unlock(f"place:{ref_id}")
        raise
    oid = resp.get("id") if isinstance(resp, dict) else None
    if not oid:
        return unknown()
    uuid_ = f"ims-{kind}-{oid}"
    rec.update(status="sent", reference_id=ref_id, order_uuid=uuid_)
    order_save(rec)
    notify(f"أُرسل إلى imeiserver: {ref_id}\nالرقم: {uuid_}")
    return {"ok": True, "code": code, "reference_id": ref_id, "order_uuid": uuid_, "note": resp.get("response") if isinstance(resp, dict) else None}
@router.post("/admin/place", dependencies=[Depends(require_admin)])
def admin_place(body: PlaceIn, request: Request):
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
    rec = order_load(code) or {"code": code, "pid": product["id"], "name": product["name"], "supplier": product.get("supplier"), "fields": payload.get("f") or {}, "q": qty, "total": round(float(payload.get("pr") or 0) * qty, 2), "t": int(payload.get("t") or time.time()), "status": "pending", "token": token}
    if rec.get("status") in ("sent", "success"):
        raise HTTPException(status_code=409, detail="Order already sent")
    if product.get("supplier") == "l2u":
        return _place_l2u(rec, product, payload, token, code, qty)
    if product.get("supplier") == "ims" and product.get("auto"):
        return _place_ims(rec, product, payload, token, code, qty)
    if product.get("supplier") in ("iu", "ims", "ve"):
        site = {"iu": "imei-unlock.net", "ims": "imeiserver.com", "ve": "imeiveserver.com"}[product["supplier"]]
        rec["status"] = "manual"
        order_save(rec)
        return {"ok": True, "manual": True, "code": code, "supplier": site, "service_id": product["id"].rsplit("-", 1)[1], "service": product["name"], "quantity": qty, "fields": payload.get("f") or {}, "note": f"نفّذ هذا الطلب يدويًا من لوحة {site} بعد تأكيد الدفع."}
    h = token_hash(token)
    ref_id = "ms-" + h[:24]
    if not lock(f"place:{ref_id}", 600):
        raise HTTPException(status_code=409, detail="Already submitted, check the supplier panel")
    order_obj = dict(payload.get("f") or {})
    order_obj.update({"feedback_url": f"{public_base(request)}/callback", "reference_id": ref_id, "Quantity": qty})
    pid = product["id"]
    req_body = [{"product_id": int(pid) if pid.isdigit() else pid, "fields": [order_obj]}]
    try:
        resp = fusion("POST", "/order", body=req_body, timeout=ORDER_TIMEOUT, write=True)
    except OrderUnknown:
        rec.update(status="unknown", reference_id=ref_id)
        order_save(rec)
        notify(f"نتيجة غير معروفة للطلب {ref_id}. لا تعد الإرسال، راجع لوحة المورد بهذا المرجع.")
        return JSONResponse(status_code=202, content={"ok": False, "unknown": True, "code": code, "reference_id": ref_id, "detail": "Outcome unknown. Do NOT retry. Check the supplier panel with this reference_id."})
    except HTTPException:
        unlock(f"place:{ref_id}")
        raise
    item = first_item(resp.get("data"))
    if item.get("status") == "error":
        unlock(f"place:{ref_id}")
        raise HTTPException(status_code=400, detail=item.get("message") or item.get("replay") or "Rejected")
    rec.update(status="sent", reference_id=ref_id, order_uuid=item.get("order_uuid"), amount=item.get("amount"))
    order_save(rec)
    notify(f"أُرسل للمورد: {ref_id}\norder_uuid: {item.get('order_uuid')}")
    return {"ok": True, "code": code, "reference_id": ref_id, "order_uuid": item.get("order_uuid"), "amount": item.get("amount"), "currency": item.get("currency_code"), "note": item.get("note")}
def _apply_final(uuid, status, replay):
    try:
        for o in order_list():
            if o.get("order_uuid") == uuid:
                o["status"] = status
                o["replay"] = str(replay or "")[:600]
                order_save(o)
                break
    except Exception as e:
        log.error("apply_final failed: %s", type(e).__name__)
def _dhru_status(uuid, item):
    try:
        code_status = int(item.get("STATUS"))
    except (TypeError, ValueError):
        code_status = None
    status = {4: "success", 3: "rejected"}.get(code_status, "sent")
    replay = item.get("CODE") or ""
    if status in ("success", "rejected"):
        _apply_final(uuid, status, replay)
    return {"status": status, "replay": replay, "code_status": code_status}
@router.get("/admin/status", dependencies=[Depends(require_admin)])
def admin_status(uuid: str = ""):
    if not UUID_RE.match(uuid):
        raise HTTPException(status_code=422, detail="Invalid order_uuid")
    if uuid.startswith("ims-"):
        if not IMS_ENABLED:
            raise HTTPException(status_code=503, detail="imeiserver not configured")
        parts = uuid.split("-")
        if len(parts) != 3 or parts[1] not in ("i", "s") or not parts[2].isdigit():
            raise HTTPException(status_code=422, detail="Use ims-i-<id> (IMEI) or ims-s-<id> (server)")
        route = ("imei-orders" if parts[1] == "i" else "server-orders") + "/" + parts[2]
        return _webx_status(uuid, webx_call(route))
    if uuid.startswith("l2-"):
        if not L2U_ENABLED:
            raise HTTPException(status_code=503, detail="lock2unlock not configured")
        ref = uuid[3:]
        j = l2u_call("getimeiorderbulk", {"1": {"ID": int(ref) if ref.isdigit() else ref}})
        entry = j.get("1") if isinstance(j.get("1"), dict) else {}
        return _dhru_status(uuid, first_success(entry))
    data = fusion("GET", "/order", params={"order_uuid": uuid})
    return data.get("data")
@router.get("/admin/account", dependencies=[Depends(require_admin)])
def admin_account():
    out = {"currency": None, "balance": None, "name": None}
    try:
        d = fusion("GET", "/account").get("data") or {}
        out.update(currency=d.get("currency"), balance=d.get("balance"), name=d.get("name"))
    except HTTPException as e:
        if not (L2U_ENABLED or IMS_ENABLED or VE_ENABLED):
            raise
        out["error"] = e.detail
    if L2U_ENABLED:
        try:
            ai = first_success(l2u_call("accountinfo")).get("AccountInfo") or {}
            out["extra"] = [{"name": "lock2unlock", "balance": ai.get("credit")}]
        except HTTPException as e:
            out["extra"] = [{"name": "lock2unlock", "balance": "خطأ: " + str(e.detail)[:60]}]
    if IMS_ENABLED:
        try:
            ai = webx_call("")
            bal = f"{ai.get('balance')} {ai.get('currency') or ''}".strip() if isinstance(ai, dict) else "-"
            out.setdefault("extra", []).append({"name": "imeiserver", "balance": bal})
        except HTTPException as e:
            out.setdefault("extra", []).append({"name": "imeiserver", "balance": "خطأ: " + str(e.detail)[:60]})
    if VE_ENABLED:
        try:
            ai = first_success(ve_call("accountinfo")).get("AccountInfo") or {}
            out.setdefault("extra", []).append({"name": "imeiveserver", "balance": ai.get("credit")})
        except HTTPException as e:
            out.setdefault("extra", []).append({"name": "imeiveserver", "balance": "خطأ: " + str(e.detail)[:60]})
    return out
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
@router.post("/callback")
def callback(payload: dict):
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
ADMIN_HTML = r"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>لوحة Mustafa Soft</title><style>body{font-family:system-ui;padding:16px;max-width:720px;margin:auto}input,textarea{width:100%;padding:12px;margin:6px 0;border:1px solid #ddd;border-radius:10px}button{padding:12px 18px;border:0;border-radius:10px;background:#0f172a;color:#fff;font-weight:700;width:100%;margin:6px 0}.card{border:1px solid #eee;border-radius:14px;padding:14px;margin:10px 0}.mono{font-family:monospace;direction:ltr}</style></head><body><h2>لوحة Mustafa Soft</h2><div class="card"><input id="key" type="password" placeholder="Admin key"><button onclick="login()">دخول</button><div id="msg"></div></div><div id="app" style="display:none"><div class="card"><b>الرصيد</b><div id="bal">...</div><button onclick="bal()">تحديث</button></div><div class="card"><b>تنفيذ برمز</b><textarea id="ptxt" placeholder="الصق رسالة تيليجرام"></textarea><button onclick="go()">تنفيذ</button><div id="prev"></div></div><div class="card"><b>الطلبات</b><button onclick="orders()">تحديث</button><div id="olist"></div></div></div><script>const root=location.pathname.replace(/\/+$/,'').replace(/\/admin$/,'');let KEY='';async function api(m,p,b){let r=await fetch(root+p,{method:m,headers:{'Content-Type':'application/json','X-Admin-Key':KEY},body:b?JSON.stringify(b):undefined});return {ok:r.ok,data:await r.json().catch(()=>({}))}}async function login(){KEY=document.getElementById('key').value.trim();let r=await api('GET','/admin/account');if(!r.ok){document.getElementById('msg').innerText='كلمة السر غلط';return}document.getElementById('app').style.display='block';bal();orders()}async function bal(){let r=await api('GET','/admin/account');document.getElementById('bal').innerText=JSON.stringify(r.data)}async function orders(){let r=await api('GET','/admin/orders');document.getElementById('olist').innerText=JSON.stringify(r.data.orders||[],null,2)}function decodeTok(t){let raw=t.split('.')[0].replace(/-/g,'+').replace(/_/g,'/');raw+='='.repeat((4-raw.length%4)%4);return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(raw),c=>c.charCodeAt(0))))}async function go(){let txt=document.getElementById('ptxt').value;let m=txt.match(/[A-Za-z0-9_-]{16,}\.[0-9a-f]{32}/);if(!m){alert('ما لقيت رمز');return}let p=decodeTok(m[0]);document.getElementById('prev').innerText=JSON.stringify(p,null,2);if(!confirm('تنفيذ '+p.n+' ؟'))return;let r=await api('POST','/admin/place',{token:m[0]});alert(JSON.stringify(r.data))}</script></body></html>"""
@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(ADMIN_HTML)
app.include_router(router)
app.include_router(router, prefix="/api")
