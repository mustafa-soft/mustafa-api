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
        <title>Mustafa Soft - GSM Dashboard</title>
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
                max-width: 600px;
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
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            .btn {
                background-color: #2563eb;
                color: white;
                padding: 12px;
                border-radius: 8px;
                text-decoration: none;
                font-size: 13px;
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
            .btn-secondary {
                background-color: #334155;
                border: 1px solid #475569;
                color: #e2e8f0;
            }
            .btn-secondary:hover { background-color: #475569; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>Mustafa Soft Services</h1>
                <p>بوابة خدمات السوفتوير والتفعيل الرسمية</p>
                <div class="status">● السيرفر متصل ويعمل (Live)</div>
                
                <div class="section-title">أدوات البرمجيات والتفعيل (Software Tools)</div>
                <div class="btn-grid">
                    <a href="/tool/chimera" class="btn btn-tool" target="_blank">Chimera Tool</a>
                    <a href="/tool/unlocktool" class="btn btn-tool" target="_blank">UnlockTool</a>
                    <a href="/tool/trtools" class="btn btn-tool" target="_blank">TRTools Pro</a>
                    <a href="/tool/eft" class="btn btn-tool" target="_blank">EFT Pro</a>
                    <a href="/tool/umt" class="btn btn-tool" target="_blank">UMT Pro</a>
                    <a href="/tool/pandora" class="btn btn-tool" target="_blank">Pandora Box</a>
                </div>

                <div class="section-title">خدمات السيرفر والـ API</div>
                <div class="btn-grid">
                    <a href="/test-gsm" class="btn" target="_blank">فحص اتصال GSM</a>
                    <a href="/account-info" class="btn" target="_blank">معلومات الحساب</a>
                    <a href="/services-list" class="btn btn-secondary" target="_blank">قائمة الخدمات</a>
                    <a href="/check-imei" class="btn btn-secondary" target="_blank">فحص IMEI</a>
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

@app.route('/test-gsm', methods=['GET'])
def test_gsm():
    return jsonify(call_gsm_api("test"))

@app.route('/account-info', methods=['GET'])
def account_info():
    return jsonify(call_gsm_api("account_info"))

@app.route('/services-list', methods=['GET'])
def services_list():
    return jsonify(call_gsm_api("get_services"))

@app.route('/check-imei', methods=['GET'])
def check_imei():
    return jsonify(call_gsm_api("imei_service"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
