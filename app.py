import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# التوثيق ورابط الـ API الصحيح
GSM_API_URL = "https://api2-gsm.elbroos.com/"
GSM_API_KEY = "BXVzdGFmYW9wZW44OEBnbWFpbC5jb206MWE4MjY5YTUwZTFkZmVhNDcyNGZmMTlkMjMyMTQ1ZWI="

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
            "Authorization": f"Basic {GSM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(GSM_API_URL, headers=headers, timeout=15)
        
        try:
            res_data = response.json()
        except:
            res_data = response.text

        return jsonify({
            "status": "success",
            "gsm_status_code": response.status_code,
            "response_data": res_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

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
