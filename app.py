from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# البحث عن المتغير بأكثر من احتمال لاسم المفتاح لتجنب أي خطأ في الحفظ على Render
ELBROOS_API_TOKEN = (
    os.environ.get('ELBROOS_API_TOKEN') or 
    os.environ.get('ELBROOS_API_KEY') or
    os.environ.get('ELBROOS_TOKEN')
)

BASE_URL = os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com/api/reseller/v1')

@app.route('/check-account', methods=['GET'])
def check_account():
    try:
        if not ELBROOS_API_TOKEN:
            return jsonify({
                'status': 'error',
                'message': 'Token is missing! Please check the Environment Variables names on Render.'
            }), 400

        headers = {
            'Authorization': f'Bearer {ELBROOS_API_TOKEN}',
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
            'elbroos_response': res_data
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
