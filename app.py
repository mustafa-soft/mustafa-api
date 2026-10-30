from flask import Flask, render_template_string
import os
import requests
import traceback

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>فحص حساب Elbroos</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; max-width: 700px; margin: auto; }
        pre { background: #0f172a; padding: 15px; border-radius: 5px; color: #38bdf8; overflow-x: auto; text-align: left; direction: ltr; font-size: 12px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تشخيص الأخطاء - Elbroos</h2>
        <p><strong>كود الحالة:</strong> {{ status_code }}</p>
        <h3>التفاصيل أو الاستجابة:</h3>
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
            return render_template_string(HTML_TEMPLATE, status_code=400, response_data="خطأ: متغير البيئة للمفتاح (GSM_API_KEY) غير موجود في Render!")

        BASE_URL = os.environ.get('GSM_API_URL') or os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com')
        
        url = f"{BASE_URL.rstrip('/')}/api/index.php"
        payload = {
            'api_access_key': API_KEY.strip(),
            'action': 'accountinfo',
            'format': 'json'
        }

        response = requests.post(url, data=payload, timeout=15)
        return render_template_string(HTML_TEMPLATE, status_code=response.status_code, response_data=response.text)

    except Exception as e:
        err_msg = traceback.format_exc()
        return render_template_string(HTML_TEMPLATE, status_code=500, response_data=err_msg)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
