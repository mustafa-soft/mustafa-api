from flask import Flask, jsonify, request
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GSM_API_URL = "https://api2-gsm.elbroos.com/"
GSM_API_KEY = "BXVzdGFmYW9wZW44OEBnbWFpbC5jb206MWE4MjY5YTUwZTFkZmVhNDcyNGZmMTlkMjMyMTQ1ZWI="

@app.route('/', methods=['GET'])
def home_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mustafa Soft - لوحة التحكم الشاملة</title>
        <style>
            body {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: Tahoma, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                max-width: 650px;
                width: 100%;
            }
            .card {
                background-color: #1e293b;
                border: 2px solid #3b82f6;
                padding: 25px;
                border-radius: 14px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                text-align: center;
                margin-bottom: 20px;
            }
            h1 { color: #60a5fa; font-size: 24px; margin-bottom: 5px; }
            p { color: #94a3b8; font-size: 13px; margin-bottom: 15px; }
            .status {
                display: inline-block;
                background-color: #065f46;
                color: #34d399;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .section-title {
                color: #38bdf8;
                font-size: 14px;
                margin: 15px 0 10px 0;
                text-align: right;
                border-bottom: 1px solid #334155;
                padding-bottom: 5px;
            }
            .btn-grid {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 10px;
            }
            .btn {
                background-color: #2563eb;
                color: white;
                padding: 10px;
                border-radius: 8px;
                text-decoration: none;
                font-size: 12px;
                font-weight: bold;
                transition: background 0.3s;
                display: block;
                text-align: center;
            }
            .btn:hover { background-color: #1d4ed8; }
            .btn-tool {
                background-color: #1e293b;
                border: 1px solid #38bdf8;
                color: #38bdf8;
            }
            .btn-tool:hover {
                background-color: #38bdf8;
                color: #0f172a;
            }
            .imei-box {
                margin-top: 15px;
                background: #0f172a;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #334155;
            }
            .imei-input {
                width: 70%;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #475569;
                background: #1e293b;
                color: white;
                font-size: 13px;
            }
            .imei-btn {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 9px 15px;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
            }
            .imei-btn:hover { background-color: #059669; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>Mustafa Soft Services</h1>
                <p>بوابة خدمات الصيانة وبرمجيات الهواتف الذكية</p>
                <div class="status">● السيرفر متصل ويعمل (Live)</div>
                
                <div class="section-title">أدوات السوفتوير والتفعيل الرسمية</div>
                <div class="btn-grid">
                    <a href="/tool/chimera" class="btn btn-tool" target="_blank">Chimera Tool</a>
                    <a href="/tool/unlocktool" class="btn btn-tool" target="_blank">UnlockTool</a>
                    <a href="/tool/trtools" class="btn btn-tool" target="_blank">TRTools Pro</a>
                    <a href="/tool/eft" class="btn btn-tool" target="_blank">EFT Pro</a>
                    <a href="/tool/umt" class="btn btn-tool" target="_blank">UMT Pro</a>
                    <a href="/tool/pandora" class="btn btn-tool" target="_blank">Pandora Box</a>
                </div>

                <div class="section-title">فحص الأجهزة (IMEI)</div>
                <div class="imei-box">
                    <form action="/check-imei" method="GET" target="_blank">
                        <input type="text" name="imei" class="imei-input" placeholder="أدخل رقم الـ IMEI هنا..." required>
                        <button type="submit" class="imei-btn">فحص</button>
                    </form>
                </div>

                <div class="section-title">إدارة الحساب والسيرفر</div>
                <div class="btn-grid" style="grid-template-columns: 1fr 1fr;">
                    <a href="/account-info" class="btn" style="background-color: #334155;" target="_blank">معلومات الحساب</a>
                    <a href="/services-list" class="btn" style="background-color: #334155;" target="_blank">قائمة الخدمات</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def call_gsm_api(action_name):
    try:
        target_url = f"{GSM_API_URL}?key={GSM_API_KEY}&action={action_name}"
        response = requests.get(target_url, timeout=15)
        try:
            res_data = response.json()
        except:
            res_data = response.text
        return {
            "status": "success",
            "gsm_status_code": response.status_code,
            "response_data": res_data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.route('/tool/<tool_name>', methods=['GET'])
def get_tool_info(tool_name):
    return jsonify({
        "status": "success",
        "tool": tool_name.upper(),
        "service": f"Mustafa Soft Reseller Service for {tool_name.upper()}",
        "message": "الخدمة متوفرة وجاهزة للتفعيل والتجديد"
    })

@app.route('/account-info', methods=['GET'])
def account_info():
    return jsonify(call_gsm_api("account_info"))

@app.route('/services-list', methods=['GET'])
def services_list():
    return jsonify(call_gsm_api("get_services"))

@app.route('/check-imei', methods=['GET'])
def check_imei():
    imei_number = request.args.get('imei', 'Not Provided')
    # محاولة الاتصال بـ API الفحص الخارجي
    api_result = call_gsm_api(f"imei_service&imei={imei_number}")
    
    return jsonify({
        "checked_imei": imei_number,
        "api_connection": api_result,
        "note": "إذا ظهر خطأ 403، فهذا يؤكد أن حسابك يحتاج إلى تفعيل الرصيد أو باقة الموزعين من لوحة تحكم المزود لكي يستجيب لطلبات الـ IMEI."
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
