import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# حط رابط الـ API ومفتاح التفعيل هنا مباشرة مؤقتاً للتجربة
GSM_API_URL = "حط_رابط_الـ_api_هنا"
GSM_API_KEY = "حط_مفتاح_التفعيل_هنا"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Mustafa Soft API",
        "message": "Backend is running successfully!"
    })

@app.route('/test-gsm', methods=['GET'])
def test_gsm():
    try:
        headers = {
            "Authorization": f"Bearer {GSM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(GSM_API_URL, headers=headers, timeout=15)
        
        return jsonify({
            "status": "success",
            "gsm_status_code": response.status_code,
            "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
