from flask import Flask, jsonify, request
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GSM_API_URL = "https://api2-gsm.elbroos.com/"
GSM_API_KEY = "BXVzdGFmYW9wZW44OEBnbWFpbC5jb206MWE4MjY5YTUwZTFkZmVhNDcyNGZmMTlkMjMyMTQ1ZWI="

@app.route('/', methods=['GET'])
def home():
    # تصميم واجهة ويب خفيفة وشيك للموقع بدل الشاشة البيضاء
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mustafa Soft API</title>
        <style>
            body {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: Tahoma, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background-color: #1e293b;
                border: 2px solid #3b82f6;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }
            h1 { color: #60a5fa; font-size: 24px; margin-bottom: 10px; }
            p { color: #94a3b8; font-size: 14px; margin-bottom: 20px; }
            .status {
                display: inline-block;
                background-color: #065f46;
                color: #34d399;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            a {
                display: inline-block;
                margin-top: 20px;
                background-color: #3b82f6;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                transition: background 0.3s;
            }
            a:hover { background-color: #2563eb; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Mustafa Soft API</h1>
            <p>نظام إدارة خدمات وربط الـ API يعمل بكفاءة عالية</p>
            <div class="status">● السيرفر متصل ويعمل (Live)</div>
            <br>
            <a href="/test-gsm" target="_blank">فحص اتصال GSM API</a>
        </div>
    </body>
    </html>
    """
    return html_content

@app.route('/test-gsm', methods=['GET'])
def test_gsm():
    try:
        target_url = f"{GSM_API_URL}?key={GSM_API_KEY}&action=account_info"
        response = requests.get(target_url, timeout=15)
        
        try:
            res_data = response.json()
        except:
            res_data = response.text

        return jsonify({
            "status": "success",
            "gsm_status_code": response.status_code,
            "response_data": res_data,
            "note": "الحالة 403 تعني أن المفتاح بحاجة لتفعيل الرصيد أو باقة الموزعين من لوحة تحكم المزود."
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
