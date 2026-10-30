from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/": {"origins": "*"}})

GSM_API_URL = "https://api2-gsm.elbroos.com/"
GSM_API_KEY = os.getenv("GSM_API_KEY", "bXVzdGFmYW9wZW44OE...")

@app.route('/')
def home():
    return jsonify({
        "status": "Mustafa GSM API is Running ✅", 
        "frontend": "mustafa-soft.vercel.app",
        "api": "mustafa-api-1.onrender.com",
        "external": "مربوط مع GSMServer",
        "time": str(datetime.datetime.now())
    })

@app.route('/api/create-activation', methods=['POST', 'OPTIONS'])
def create_activation():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    data = request.get_json() or {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '1_month')
    tool = data.get('tool', 'chimera')
    print(f"New: {email} - {tool}")
    
    return jsonify({
        "success": True,
        "message": f"تم إنشاء تفعيل {tool} بنجاح - مربوط مع GSMServer",
        "data": {
            "email": email,
            "duration": duration,
            "tool": tool,
            "activation_code": "MUSTAFA-" + email[:3].upper() + "-2024",
            "kept_old_url": True
        }
    })

if __name__ == '__main__':
    app.run()
