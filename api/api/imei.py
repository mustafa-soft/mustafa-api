import requests
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# يفضل وضع اسم المستخدم والمفتاح في إعدادات Vercel (Environment Variables)
# ولا تكتبهما مباشرة في الكود لحماية حسابك.
USERNAME = os.environ.get("IMEI_USERNAME", "ضع_اسم_المستخدم_هنا")
API_KEY = os.environ.get("IMEI_API_KEY", "ضع_مفتاح_API_هنا")
API_URL = "https://www.imeiserver.com/dhru"

def send_dhru_request(action, extra_data=None):
    """دالة لإرسال الطلبات إلى imeiserver"""
    payload = {
        "username": USERNAME,
        "apiaccesskey": API_KEY,
        "action": action,
        "apiversion": "8.1",
        "requestformat": "JSON"
    }
    
    if extra_data:
        payload.update(extra_data)

    try:
        # إرسال الطلب
        response = requests.post(API_URL, data=payload, timeout=30)
        return response.json() # تحويل الرد إلى JSON
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# 1. مسار لمعرفة الرصيد (مثال)
# ==========================================
@app.route('/api/balance', methods=['GET'])
def get_balance():
    result = send_dhru_request("getbalance")
    return jsonify(result)

# ==========================================
# 2. مسار لجلب الخدمات
# ==========================================
@app.route('/api/services', methods=['GET'])
def get_services():
    result = send_dhru_request("getservices")
    return jsonify(result)

# ==========================================
# 3. مسار لطلب فك قفل IMEI (مثال)
# ==========================================
@app.route('/api/check-imei', methods=['POST'])
def check_imei():
    data = request.json # استقبال البيانات من موقعك (الواجهة الأمامية)
    
    service_id = data.get("service")
    imei_number = data.get("imei")
    
    if not service_id or not imei_number:
        return jsonify({"error": "يرجى إرسال service و imei"}), 400

    # إرسال الطلب لموقع imeiserver
    result = send_dhru_request("placeorder", {
        "service": service_id,
        "imei": imei_number
    })
    
    return jsonify(result)
