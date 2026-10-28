import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# قراءة المتغيرات مع طباعتها للتاكد
GSM_API_URL = os.environ.get('GSM_API_URL')
GSM_API_KEY = os.environ.get('GSM_API_KEY')

print(f"DEBUG URL: {GSM_API_URL}")
print(f"DEBUG KEY: {GSM_API_KEY}")

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Mustafa Soft API",
        "message": "Backend is running successfully!"
    })

@app.route('/test-gsm', methods=['GET'])
def test_gsm():
    # لو المتغيرات فاضية، هنرجع القيمة اللي السيرفر شايفها عشان نعرف المشكلة فين بالظبط
    if not GSM_API_URL or not GSM_API_KEY:
        return jsonify({
            "status": "error",
            "message": "Environment variables are missing!",
            "debug_url": GSM_API_URL,
            "debug_key": "Exists" if GSM_API_KEY else "Missing"
        }), 400
    
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
