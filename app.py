from flask import Flask, jsonify, request
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GSM_API_URL = "https://api2-gsm.elbroos.com/"
GSM_API_KEY = "BXVzdGFmYW9wZW44OEBnbWFpbC5jb206MWE4MjY5YTUwZTFkZmVhNDcyNGZmMTlkMjMyMTQ1ZWI="

@app.route('/test-gsm', methods=['GET'])
def test_gsm():
    try:
        target_url = f"{GSM_API_URL}?key={GSM_API_KEY}"
        response = requests.get(target_url, timeout=15)
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
