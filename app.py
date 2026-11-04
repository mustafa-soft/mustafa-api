
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os, requests, json, re

app = FastAPI(title="Mustafa Soft - LIVE - ALL OK")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USERNAME = "mustafaopen88@gmail.com"
API_KEY = os.getenv("GALLE_API_TOK") or os.getenv("GALLE_API_TOKEN") or os.getenv("GALLE_TOKEN") or ""
LEGACY_BASE = "https://galleunlock.legacy-api.io"

def call_legacy(action, extra=None):
    p = {"username": USERNAME, "key": API_KEY, "action": action}
    if extra: p.update(extra)
    try:
        r = requests.get(LEGACY_BASE, params=p, timeout=40)
        txt = r.text
        # نحاول نفك JSON
        try:
            j = r.json()
            return j
        except:
            pass
        # ندور على JSON داخل النص
        matches = re.findall(r'\{.*?\}', txt, re.DOTALL)
        for m in reversed(matches):
            try:
                if len(m) > 20:
                    return json.loads(m)
            except:
                continue
        # لو فيه SERVICES
        if "SUCCESS" in txt or "ALL OK" in txt:
            # أحيانا الرد بيكون SUCCESS[...] أو فيه XML
            if "[" in txt and "]" in txt:
                try:
                    arr_match = re.search(r'\[.*\]', txt, re.DOTALL)
                    if arr_match:
                        return json.loads(arr_match.group(0))
                except:
                    pass
            return {"status": "success", "message": "ALL OK!", "raw_text": txt[:4000], "http": 200}
        return {"raw": txt[:5000], "http": r.status_code}
    except Exception as e:
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html dir="rtl" style="font-family: Cairo, sans-serif; background:#0f172a; color:white; text-align:center; padding:30px;">
    <h1>✅ Legacy API is ready!</h1>
    <h2 style="color:#22c55e;">ALL OK! - ربط تمام يا مصطفى!</h2>
    <p>mustafa-soft.com مربوط مع GalleUnlockers بنجاح</p>
    <div style="background:#1e293b; padding:20px; border-radius:12px; margin:20px;">
        <p>👉 <a href="/account" style="color:#38bdf8;">/account - رصيدك</a></p>
        <p>👉 <a href="/products" style="color:#38bdf8;">/products - كل الخدمات الـ15</a></p>
        <p>👉 <a href="/products-view" style="color:#facc15; font-weight:bold;">/products-view - عرض جميل لموقعك</a></p>
    </div>
    <p style="color:#94a3b8;">mustafaopen88@gmail.com | السودان</p>
    </html>
    """

@app.get("/account")
def account():
    return call_legacy("accountinfo")

@app.get("/products")
def products():
    imei = call_legacy("imeiservicelist")
    server = call_legacy("serverservicelist")
    return {"status": "ALL OK", "imei_services": imei, "server_services": server}

@app.get("/products-view", response_class=HTMLResponse)
def products_view():
    data_imei = call_legacy("imeiservicelist")
    data_server = call_legacy("serverservicelist")
    
    # نحاول نستخرج الليستة
    services = []
    for src in [data_imei, data_server]:
        if isinstance(src, dict):
            if "SERVICES" in src: services.extend(src["SERVICES"] if isinstance(src["SERVICES"], list) else [src["SERVICES"]])
            elif "services" in src: services.extend(src["services"])
            elif "raw_text" in src:
                # نحاول نفسر raw_text
                txt = src["raw_text"]
                try:
                    # Galle legacy بيرجع أحيانا format غريب
                    j = json.loads(re.search(r'\{.*\}', txt, re.DOTALL).group(0))
                    if isinstance(j, dict) and "SERVICES" in j:
                        services.extend(j["SERVICES"])
                except:
                    pass
        elif isinstance(src, list):
            services.extend(src)
    
    html_services = ""
    if services:
        for s in services[:100]:
            if isinstance(s, dict):
                name = s.get("SERVICE_NAME") or s.get("service_name") or s.get("name") or "خدمة"
                price = s.get("SERVICE_PRICE") or s.get("price") or "0"
                time = s.get("SERVICE_TIME") or s.get("time") or ""
                sid = s.get("SERVICE_ID") or s.get("id") or ""
                html_services += f"<div style='background:#1e293b; margin:10px; padding:15px; border-radius:10px; text-align:right;'><b>{name}</b><br>السعر: ${price} | المدة: {time}<br><small>ID: {sid}</small></div>"
    else:
        # لو ما قدرنا نفسر، نعرض الخام
        html_services = f"<pre style='background:#1e293b; padding:20px; overflow:auto; text-align:left; direction:ltr;'>{json.dumps({'imei': data_imei, 'server': data_server}, ensure_ascii=False, indent=2)[:8000]}</pre><p>الـ API شغال ALL OK لكن شكل البيانات محتاج تنسيق - تواصل مع Galle للدوكمنت</p>"
    
    return f"""
    <html dir="rtl" style="font-family: sans-serif; background:#0f172a; color:white; padding:20px;">
    <h1 style="text-align:center;">🔓 خدمات Mustafa Soft - GalleUnlockers</h1>
    <h3 style="text-align:center; color:#22c55e;">✅ ALL OK! - متصل</h3>
    {html_services}
    </html>
    """

@app.get("/order")
def order(imei: str = Query(...), service_id: str = Query(...)):
    return call_legacy("placeimeiorder", {"serviceid": service_id, "imei": imei})
