from flask import Flask, render_template_string
import os
import requests

app = Flask(__name__)

API_KEY = (
    os.environ.get('GSM_API_KEY') or 
    os.environ.get('ELBROOS_API_TOKEN')
)
if API_KEY:
    API_KEY = API_KEY.strip()

BASE_URL = os.environ.get('GSM_API_URL') or os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>حساب Elbroos - DHRU Fusion Pro</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); width: 90%; max-width: 550px; text-align: center; }
        h2 { color: #38bdf8; margin-bottom: 15px; }
        .status { padding: 10px; border-radius: 8px; margin-bottom: 15px; font-weight: bold; }
        .success { background: #065f46; color: #34d399; }
        .error { background: #7f1d1d; color: #f87171; }
        pre { background: #0f172a; padding: 15px; border-radius: 8px; text-align: left; direction: ltr; overflow-x: auto; color: #e2e8f0; font-size: 13px; max-height: 250px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>لوحة حساب Elbroos</h2>
        <div class="status {% if status_code == 200 and not is_html %}success{% else %}error{% endif %}">
            حالة الاتصال: {{ status_code }}
        </div>
        <pre>{{ response_data }}</pre>
    </div>
</body>
</html>
"""

@app.route('/check-account', methods=['GET'])
def check_account():
    try:
        if not API_KEY:
            return render_template_string(HTML_TEMPLATE, status_code=400, response_data="Error: API Key is missing in environment variables!", is_html=True)

        # إعدادات طلب DHRU Fusion Pro الرسمية
        url = f"{BASE_URL.rstrip('/')}/includes/api.php"
        payload = {
            'api_access_key': API_KEY,
            'action': 'accountinfo'
        }
        
        # تنفيذ طلب POST لنظام DHRU
        response = requests.post(url, data=payload, timeout=10)
        
        # فحص الاستجابة
        try:
            res_data = response.json()
            is_html = False
        except:
            res_data = response.text
            is_html = "<html" in res_data.lower()
            
            # إذا كان المسار بحاجة لتجربة api.php مباشرة
            if is_html:
                alt_url = f"{BASE_URL.rstrip('/')}/api.php"
                res_alt = requests.post(alt_url, data=payload, timeout=10)
                try:
                    res_data = res_alt.json()
                    response = res_alt
                    is_html = False
                except:
                    pass

        return render_template_string(HTML_TEMPLATE, status_code=response.status_code, response_data=res_data, is_html=is_html)

    except Exception as e:
        return render_template_string(HTML_TEMPLATE, status_code=500, response_data=str(e), is_html=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
