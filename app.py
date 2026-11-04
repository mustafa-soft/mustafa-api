
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os, requests, json, re

app = FastAPI(title="Mustafa Soft - Galle Connected LIVE")

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
    if extra:
        p.update(extra)
    try:
        r = requests.get(LEGACY_BASE, params=p, timeout=40)
        txt = r.text
        # 1. حاول JSON مباشر
        try:
            j = r.json()
            return j
        except:
            pass
        # 2. Galle Legacy بيرجع أحيانا SUCCESS<json> أو ALL OK<json>
        # نبحث عن أول { 
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except:
                return {"raw_json_string": m.group(0)[:3000], "full_text": txt[:2000]}
        # 3. لو فقط ALL OK
        if "ALL OK" in txt or "SUCCESS" in txt:
            return {"status": "success", "message": txt[:1000], "http": r.status_code}
        return {"raw": txt[:4000], "http": r.status_code}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def home():
    return {
        "status": "LIVE ✅",
        "message": "Legacy API is ready!",
        "store": "mustafa-soft.com",
        "galle": "Connected - ALL OK!",
        "username": USERNAME,
        "key_exists": bool(API_KEY),
        "endpoints": {
            "/account": "رصيدك وبياناتك",
            "/products": "كل خدمات Galle الـ 15",
            "/order?imei=XXX&service_id=YYY": "ارسال طلب فك شفرة",
            "/get-order?orderid=XXX": "متابعة الطلب"
        }
    }

@app.get("/account")
def account():
    res = call_legacy("accountinfo")
    return res

@app.get("/products")
def products():
    # نجيب كل الخدمات
    imei_list = call_legacy("imeiservicelist")
    server_list = call_legacy("serverservicelist")
    
    # ننظف البيانات لو جات في شكل raw
    return {
        "status": "ALL OK",
        "imei_services": imei_list,
        "server_services": server_list,
        "count_imei": len(imei_list) if isinstance(imei_list, list) else "check inside",
        "count_server": len(server_list) if isinstance(server_list, list) else "check inside"
    }

@app.get("/order")
def place_order(imei: str = Query(..., description="IMEI الجهاز"), service_id: str = Query(..., description="ID الخدمة من /products")):
    return call_legacy("placeimeiorder", {"serviceid": service_id, "imei": imei})

@app.get("/get-order")
def get_order(orderid: str = Query(...)):
    return call_legacy("getimeiorder", {"orderid": orderid})

@app.get("/hostinger-code")
def hostinger_code():
    return {
        "php_for_mustafa_soft_com": """
<?php
// ضع هذا في mustafa-soft.com - صفحة الخدمات
$api_url = "https://mustafa-api-1.onrender.com/products";
$json = file_get_contents($api_url);
$data = json_decode($json, true);

$services = $data['imei_services'];
if(isset($services['SERVICES']) ) $services = $services['SERVICES'];
if(isset($services['services']) ) $services = $services['services'];

foreach($services as $s){
    echo "<div class='service-card'>";
    echo "<h3>".$s['SERVICE_NAME']."</h3>";
    echo "<p>السعر: $".$s['SERVICE_PRICE']." - المدة: ".$s['SERVICE_TIME']."</p>";
    echo "<a href='/order?service_id=".$s['SERVICE_ID']."'>اطلب الان</a>";
    echo "</div>";
}
?>
        """
    }
