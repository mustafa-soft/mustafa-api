from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

ELBROOS_API_TOKEN = (
    os.environ.get('ELBROOS_API_TOKEN') or 
    os.environ.get('ELBROOS_API_KEY') or
    os.environ.get('ELBROOS_TOKEN')
)

# تنظيف المفتاح من أي مسافات مخفية في البداية أو النهاية
if ELBROOS_API_TOKEN:
    ELBROOS_API_TOKEN = ELBROOS_API_TOKEN.strip()

BASE_URL = os.environ.get('ELBROOS_BASE_URL', 'https://api2-gsm.elbroos.com/api/reseller/v1')

@app.route('/check-account', methods=['GET'])
def check_account():
    try:
        if not ELBROOS_API_TOKEN:
            return jsonify({
                'status': 'error',
                'message': 'Token is missing!'
            }), 400

        # قائمة بالتنسيقات المحتملة للترويسة
        attempts = [
            {'Authorization': f'Bearer {ELBROOS_API_TOKEN}'},
            {'Authorization': ELBROOS_API_TOKEN},
            {'token': ELBROOS_API_TOKEN},
            {'X-API-KEY': ELBROOS_API_TOKEN}
        ]

        results = []
        for header_auth in attempts:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                **header_auth
            }
            res = requests.get(f'{BASE_URL}/account', headers=headers)
            try:
                data = res.json()
            except:
                data = res.text

            results.append({
                'header_used': list(header_auth.keys())[0],
                'status_code': res.status_code,
                'response': data
            })
            
            # إذا نجح أي طلب (كود الاستجابة 200) نعيد النتيجة فوراً
            if res.status_code == 200 and isinstance(data, dict) and data.get('status') != 'error':
                return jsonify({
                    'status': 'success',
                    'working_format': header_auth,
                    'data': data
                }), 200

        return jsonify({
            'status': 'test_completed',
            'results': results
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
