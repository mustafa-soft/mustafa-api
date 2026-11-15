from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# جلب البيانات السرية من إعدادات Vercel (Environment Variables)
USERNAME = os.environ.get("IMEI_USERNAME")
API_KEY = os.environ.get("IMEI_API_KEY")
API_URL = "https://www.imeiserver.com/dhru"

def send_dhru_request(action, extra_data=None):
    """دالة داخلية لإرسال الطلبات إلى imeiserver"""
    if not USERNAME or not API_KEY:
        return {"error": "لم يتم إعداد اسم المستخدم أو مفتاح API في إعدادات Vercel"}

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
        response = requests.post(API_URL, data=payload, timeout=30)
        return response.json()
    except Exception as e:
        return {"error": f"حدث خطأ أثناء الاتصال: {str(e)}"}

# ==========================================
# 1. مسار لمعرفة الرصيد
# الرابط: /api/imei?action=balance
# ==========================================
@app.route('/api/imei', methods=['GET', 'POST'])
def handle_imei():
    # استقبال البيانات من الواجهة الأمامية (موقعك)
    if request.method == 'POST':
        data = request.json
    else:
        data = request.args

    action = data.get("action", "getbalance") # الافتراضي هو جلب الرصيد

    # --------------------------------------------------
    # جلب الرصيد
    if action == "getbalance":
        result = send_dhru_request("getbalance")
        return jsonify(result)

    # --------------------------------------------------
    # جلب الخدمات
    elif action == "getservices":
        result = send_dhru_request("getservices")
        return jsonify(result)

    # --------------------------------------------------
    # إنشاء طلب (فك قفل IMEI)
    elif action == "placeorder":
        service_id = data.get("service")
        imei_number = data.get("imei")
        
        if not service_id or not imei_number:
            return jsonify({"error": "يرجى إرسال service و imei"}), 400

        result = send_dhru_request("placeorder", {
            "service": service_id,
            "imei": imei_number
        })
        return jsonify(result)

    else:
        return jsonify({"error": "الأمر (action) غير معروف"}), 400
