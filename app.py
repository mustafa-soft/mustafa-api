from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# جلب الـ Token من متغيرات البيئة على Render
ELBROOS_API_TOKEN = os.environ.get('ELBROOS_API_TOKEN')
BASE_URL = os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com/api/reseller/v1')

@app.route('/check-account', methods=['GET'])
def check_account():
    try:
        headers = {
            'Authorization': f'Bearer {ELBROOS_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # إرسال طلب POST إلى الـ API الخاص بـ Elbroos
        response = requests.post(f'{BASE_URL}/account', headers=headers, json={})
        
        # إرجاع النتيجة
        return jsonify({
            'status': 'success',
            'data': response.json()
        }), response.status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
