from flask import Flask, render_template_string
import os
import requests

app = Flask(__name__)

API_KEY = (
    os.environ.get('GSM_API_KEY') or 
    os.environ.get('ELBROOS_API_TOKEN')
)

BASE_URL = os.environ.get('GSM_API_URL') or os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>فحص حساب Elbroos</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; max-width: 600px; margin: auto; }
        pre { background: #0f172a; padding: 15px; border-radius: 5px; color: #38bdf8; overflow-x: auto; text-align: left; direction: ltr; font-size: 13px; }
        .alert { background: #7f1d1d; color: #f87171; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تقرير الاتصال بـ Elbroos</h2>
        <p><strong>كود الحالة:</strong> {{ status_code }}</p>
        {% if is_html %}
        <div class="alert">تنبيه: الاستجابة عبارة عن صفحة HTML (تسجيل دخول)، مما يعني أن رابط الـ API غير صحيح أو ناقص. يرجى التأكد من رابط الـ API المخصص للموزعين من لوحة تحكم Elbroos.</div>
        {% endif %}
        <h3>الاستجابة:</h3>
        <pre>{{ response_text }}</pre>
    </div>
</body>
</html>
"""

@app.route('/check-account', methods=['GET'])
def check_account():
    if not API_KEY:
        return render_template_string(HTML_TEMPLATE, status_code=0, response_text="Error: API Key is missing.", is_html=True)

    # محاولة الاتصال عبر رابط الـ API الرسمي لـ DHRU
    url = f"{BASE_URL.rstrip('/')}/api.php"
    params = {
        'api_access_key': API_KEY.strip(),
        'action': 'accountinfo',
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        res_text = response.text
        status_code = response.status_code
        is_html = "<html" in res_text.lower()
    except Exception as e:
        res_text = str(e)
        status_code = 500
        is_html = True

    return render_template_string(HTML_TEMPLATE, status_code=status_code, response_text=res_text, is_html=is_html)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
