import os
import re
import time
import uuid
import hmac
import json
import base64
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
# قراءة آمنة للإعدادات (من Environment Variables في Vercel)
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
ADMIN_SECRET = env("ADMIN_SECRET")
ALLOWED_ORIGIN = env("ALLOWED_ORIGIN", "https://mustafa-soft.com")
PUBLIC_URL = (env("PUBLIC_URL") or env("RENDER_EXTERNAL_URL")).rstrip("/")

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

# الموردين لعرض الأرصدة
SUPPLIERS = [
    {
        "name": "GalleUnlockers",
        "url_env": "GALLE_API_URL",
        "key_envs": ["GALLE_API_TOK", "GALLE_API_TOKEN", "GALLE_TOKEN"],
        "user_env": None,
    },
    {
        "name": "imei-unlock.net",
        "url_env": "IMEI_UNLOCK_API_URL",
        "key_envs": ["IMEI_UNLOCK_API_KEY"],
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
# التخزين (Upstash Redis، ومخزن مؤقت في الذاكرة لو مش متضبط)
# ---------------------------------------------------------------
HKEY = "ms:o"
_mem_orders = {}
_mem_hits = {}
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
    except Exception:
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
    if not res:  # ترحيل من التخزين القديم لمرة واحدة
        old = rcall(["GET", "ms:orders"])
        if old:
            orders = json.loads(old)
            for o in orders.values():
                order_set(o)
            return list(orders.values())
    return [json.loads(v) for v in res[1::2]]


def lock(ref, ttl):
    if not REDIS:
        return True
    return rcall(["SET", f"ms:lock:{ref}", "1", "NX", "EX", str(ttl)]) == "OK"


def unlock(ref):
    if REDIS:
        try:
            _redis(["DEL", f"ms:lock:{ref}"])
        except Exception:
            pass


def rate_ok(ip):
    if REDIS:
        k = f"ms:rl:{ip}"
        rcall(["SET", k, "0", "EX", "3600", "NX"])
        return int(rcall(["INCR", k])) <= 10
    now = time.time()
    hits = [t for t in _mem_hits.get(ip, []) if now - t < 3600]
    ok = len(hits) < 10
    hits.append(now)
    _mem_hits[ip] = hits
    return ok


# ---------------------------------------------------------------
# الحماية
# ---------------------------------------------------------------
def require_admin(x_admin_key: str = Header("")):
    if not ADMIN_SECRET or not hmac.compare_digest(
        x_admin_key.encode(), ADMIN_SECRET.encode()
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------
# الاتصال بـGalleUnlockers (Dhru Fusion API)
# ---------------------------------------------------------------
def galle(method, path, params=None, body=None, timeout=30):
    if not GALLE_KEY or not GALLE_URL:
        raise HTTPException(status_code=503, detail="Supplier not configured")
    try:
        r = requests.request(
            method,
            f"{GALL
