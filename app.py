from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"

@app.route('/')
def home():
    return jsonify({
        "status": "Mustafa GSM API is Running",
        "message": "Chimera + UnlockTool Ready",
        "url": "https://mustafa-api-1.onrender.com",
        "tools": ["chimera", "unlocktool"]
    })

@app.route('/chimera')
def chimera():
    username = RESELLER_NAME
    hash_val = hashlib.md5(username.encode()).hexdigest()
    return jsonify({
        "reseller": username,
        "md5_hash": hash_val,
        "api_url": "https://mustafa-api-1.onrender.com",
        "status": "Ready to be reseller for Chimera Tool"
    })

@app.route('/chimera/verify')
def verify_chimera():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "chimera"})

@app.route('/unlocktool')
def unlocktool():
    return jsonify({
        "reseller": RESELLER_NAME,
        "email": RESELLER_EMAIL,
        "api_url": "https://mustafa-api-1.onrender.com/unlocktool",
        "status": "Ready to be reseller for UnlockTool",
        "website": "https://taupe-squirrel-26ced9.netlify.app/"
    })

@app.route('/unlocktool/verify')
def verify_unlocktool():
    return jsonify({
        "verified": True, 
        "ready": True, 
        "reseller": RESELLER_NAME,
        "tool": "unlocktool",
        "email": RESELLER_EMAIL
    })

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
    tool = data.get('tool', 'chimera')
    return jsonify({
        "status": "success",
        "message": f"Received activation request {tool} - {duration}",
        "email": email,
        "tool": tool,
        "note": "Will be activated manually from reseller panel - WhatsApp 0900287738",
        "chimera_ready": True,
        "unlocktool_ready": True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
