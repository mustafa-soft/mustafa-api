from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "Mustafa GSM API is Running ✅",
        "message": "Connected to Chimera Tool Ready",
        "url": "https://mustafa-api-1.onrender.com"
    })

@app.route('/chimera')
def chimera():
    username = "mustafa-soft"
    hash_val = hashlib.md5(username.encode()).hexdigest()
    return jsonify({
        "reseller": username,
        "md5_hash": hash_val,
        "api_url": "https://mustafa-api-1.onrender.com",
        "status": "Ready to be reseller for Chimera Tool"
    })

@app.route('/chimera/verify')
def verify():
    return jsonify({"verified": True, "ready": True, "reseller": "mustafa-soft"})

@app.route('/api/create-activation', methods=['GET', 'POST'])
def create_activation():
    data = request.get_json() or {} if request.is_json else request.args.to_dict() if request.args else {}
    if not data:
        try:
            data = request.get_json(force=True) or {}
        except:
            data = {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '12 months')
    return jsonify({
        "status": "success",
        "message": f"تم استلام طلب تفعيل {duration}",
        "email": email,
        "note": "سيتم التفعيل يدويا من لوحة الموزع - تواصل واتساب 0900287738",
        "chimera_ready": True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
