from fastapi import FastAPI, Header, Request
import os, requests, base64, json

app = FastAPI()

# التوكن حقك من الصورة - بيقراهو من Render
BEARER = os.getenv("GALLE_API_TOK") or os.getenv("GALLE_TOKEN") or os.getenv("GALLE_API_TOKEN")
BASE_URL = "https://api.galleunlockers.com" # أو رابط Dhru Fusion بتاعك

# نخزنو مؤقت - في الإنتاج استخدم DB
ORDERS_DB = {}

@app.get("/")
def home():
    return {
        "status": "Running",
        "store": "mustafa-soft.com",
        "galle_connected": bool(BEARER),
        "tools_live": 15,
        "security": "HTTPS + Bearer in server secrets only"
    }

@app.get("/products")
def get_products():
    # الـ products بترجع keys هي الـ product_id الرقمية
    # data.products.123.name ...
    headers = {"Authorization": f"Bearer {BEARER}"}
    r = requests.get(f"{BASE_URL}/api/products", headers=headers, timeout=20)
    return r.json()

@app.post("/order")
def place_order(product_id: str, quantity: int = 1, reference_id: str = "", order_fields_json: dict = {}, confirm_paid_order: str = "NO"):
    """
    الحماية: ما بننفذ طلب مدفوع الا لو confirm_paid_order == YES
    """
    if confirm_paid_order != "YES":
        return {"status": "error", "code": 400, "message": "Set confirm_paid_order=YES to place real paid order"}

    headers = {"Authorization": f"Bearer {BEARER}", "Content-Type": "application/json"}
    payload = {
        "product_id": product_id, # المفتاح الرقمي من data.products
        "quantity": quantity,
        "reference_id": reference_id, # لازم Unique لكل طلب
        "order_fields_json": order_fields_json or {}, # {} لو مافي حقول اضافية
        "feedback_url": "https://mustafa-api-1.onrender.com/callback"
    }
    r = requests.post(f"{BASE_URL}/api/order", headers=headers, json=payload, timeout=30)
    
    # نطبق قاعدة Error handling: نفحص HTTP و JSON status
    try:
        data = r.json()
        if data.get("status") != "success":
             return {"status": "error", "http_code": r.status_code, "details": data}
        return data
    except:
        return {"status": "error", "http": r.status_code, "text": r.text}

@app.post("/callback")
async def receive_feedback(request: Request):
    body = await request.json()
    # {"reference_id": "...", "order_id": "D...", "status": "success", "replay": "base64..."}
    ref = body.get("reference_id")
    order_uuid = body.get("order_id")
    
    # فك الـ replay كنص غير موثوق
    replay_text = ""
    try:
        replay_text = base64.b64decode(body.get("replay","")).decode(errors="ignore")
    except:
        pass

    ORDERS_DB[ref or order_uuid] = body

    # المهم: لازم ترجع 200 سريع وتتأكد براك بـ GET /order قبل التسليم
    # هنا بنعمل التحقق
    # GET /order?order_uuid=D...
    return {"status": "received"}

@app.get("/order/{order_uuid}")
def get_order(order_uuid: str):
    headers = {"Authorization": f"Bearer {BEARER}"}
    r = requests.get(f"{BASE_URL}/api/order/{order_uuid}", headers=headers, timeout=20)
    return r.json()
