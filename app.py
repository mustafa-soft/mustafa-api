SUPPLIERS = [
    {"name": "GalleUnlockers", "url_env": "GALLE_API_URL", "key_env": "GALLE_API_TOK"},
    {"name": "imei-unlock.net", "url_env": "IMEI_UNLOCK_API_URL", "key_env": "IMEI_UNLOCK_API_KEY"},
]

def supplier_balance(s):
    base = (os.getenv(s["url_env"]) or "").rstrip("/")
    key = (os.getenv(s["key_env"]) or "").strip()
    if not base or not key:
        return {"error": "غير مضبوط في Vercel"}
    try:
        r = requests.get(
            f"{base}/account",  # غيّر المسار حسب وثائق المورد
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            timeout=10,
        )
        data = r.json()
        d = data.get("data", data)
        return {"balance": d.get("balance"), "currency": d.get("currency")}
    except Exception:
        return {"error": "تعذر الاتصال بالمورد"}

@app.get("/admin/balances", dependencies=[Depends(require_admin)])
def balances():
    return [{"name": s["name"], **supplier_balance(s)} for s in SUPPLIERS]
