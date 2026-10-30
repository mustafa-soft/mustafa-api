from flask import Flask, render_template_string
import os
import requests

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>حساب Elbroos - SHRU Cloud</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }
        .card { background: #1e293b; padding: 25px; border-radius: 12px; max-width: 700px; margin: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h2 { color: #38bdf8; margin-top: 0; }
        .status { padding: 8px 12px; border-radius: 6px; display: inline-block; font-weight: bold; margin-bottom: 15px; }
        .success { background: #065f46; color: #34d399; }
        .error { background: #7f1d1d; color: #f87171; }
        pre { background: #0f172a; padding: 15px; border-radius: 8px; color: #38bdf8; overflow-x: auto; text-align: left; direction: ltr; font-size: 13px; max-height: 300px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>لوحة حساب Elbroos (SHRU Cloud)</h2>
        <div class="status {% if status_code == 200 %}success{% else %}error{% endif %}">
            كود الحالة: {{ status_code }}
        </div>
        <h3>استجابة النظام:</h3>
        <pre>{{ response_data }}</pre>
    </div>
</body>
</html>
"""

@app.route('/check-account', methods=['GET'])
def check_account():
    try:
        API_KEY = os.environ.get('GSM_API_KEY') or os.environ.get('ELBROOS_API_TOKEN')
        if not API_KEY:
            return render_template_string(HTML_TEMPLATE, status_code=400, response_data="خطأ: مفتاح API غير موجود في متغيرات البيئة.")

        BASE_URL = os.environ.get('GSM_API_URL') or os.environ.get('ELBROOS_BASE_URL', 'https://api-gsm.elbroos.com')
        
        # المسار الصحيح المأخوذ من وثائق Swagger في الصورة
        url = f"{BASE_URL.rstrip('/')}/api/shru"
        
        # الهيكل الدقيق حسب وثائق SHRU Cloud
        payload = {
            "action": "account_info"
        }
        
        # تمرير المفتاح عبر الـ Headers والـ Body لضمان القبول الكامل
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY.strip()}",
            "api-key": API_KEY.strip()
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        try:
            res_json = response.json()
            formatted_res = str(res_json)
        except:
            formatted_res = response.text

        return render_template_string(HTML_TEMPLATE, status_code=response.status_code, response_data=formatted_res)

    except Exception as e:
        return render_template_string(HTML_TEMPLATE, status_code=500, response_data=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
