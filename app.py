from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

API_KEY = (
    os.environ.get('GSM_API_KEY') or 
    os.environ.get('ELBROOS_API_TOKEN')
)
if API_KEY:
    API_KEY = API_KEY.strip()

# رابط DHRU Fusion Pro الأساسي
BASE_URL = os.environ.get('GSM_API_URL') or os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com')

@app.route('/check-account', methods=['GET'])
def check_account():
    try:
        if not API_KEY:
            return jsonify({'status': 'error', 'message': 'API Key is missing!'}), 400

        # الطريقة الرسمية لنظام DHRU Fusion Pro لجلب معلومات الحساب
        payload = {
            'api_access_key': API_KEY,
            'action': 'accountinfo'
        }
        
        # DHRU Fusion يستقبل الطلبات غالباً عبر POST أو GET مع الـ action
        response = requests.post(f'{BASE_URL}/index.php', data=payload)
        
        try:
            res_data = response.json()
        except:
            res_data = {"raw_text": response.text}

        return jsonify({
            'status_code': response.status_code,
            'dhru_account_info': res_data
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
