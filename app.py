from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "Mustafa API is Live!",
        "message": "Connected to Chimera Tool Ready",
        "url": "https://mustafa-api-1.onrender.com"
    })

@app.route('/api/create-activation', methods=['GET', 'POST'])
def create_activation():
    data = request.get_json() or {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '12 months')
    return jsonify({
        "status": "success",
        "email": email,
        "duration": duration,
        "chimera_ready": True
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
    return jsonify({"verified": True, "ready": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
