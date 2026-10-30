from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# اعتماد المتغيرات الخاصة بـ DHRU Fusion Pro بدقة
API_KEY = (
    os.environ.get('GSM_API_KEY') or 
    os.environ.get('ELBROOS_API_TOKEN')
)

BASE_URL = os.environ.get('GSM_API_URL') or os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com/api/reseller/v1')

if API_KEY:
    API_KEY = API_KEY.strip()

@app.route('/check-account', methods=['GET'])
def check_account():
    try:
        if not API_KEY:
            return jsonify({
                'status': 'error',
                'message': 'API Key is missing in environment variables!'
            }), 400

        # نظام DHRU Fusion Pro يقبل المفتاح غالباً عبر ترويسة Authorization أو كمعامل، 
        # وسنجرب الترويسة القياسية للنظام أو Bearer
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.get(f'{BASE_URL}/account', headers=headers)
        
        try:
            res_data = response.json()
        except:
            res_data = {"raw_text": response.text}

        return jsonify({
            'status_code': response.status_code,
            'dhru_response': res_data
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
