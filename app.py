from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime

app = Flask(__name__)

# ده أهم سطر - بيسمح لموقعك في Vercel يشتغل
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/')
def home():
    return jsonify({"status": "Mustafa GSM API is Running ✅", "time": str(datetime.datetime.now())})

@app.route('/api/create-activation', methods=['POST', 'OPTIONS'])
def create_activation():
    # عشان الـ CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
        
    data = request.get_json() or {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '1_month')
    
    # هنا تحط منطق التفعيل حقك - مثلا تحفظ في DB
    print(f"New activation: {email} - {duration}")

    return jsonify({
        "success": True,
        "message": "تم إنشاء التفعيل بنجاح",
        "data": {
            "email": email,
            "duration": duration,
            "activation_code": "MUSTAFA-" + email[:3].upper() + "-2024"
        }
    })

if __name__ == '__main__':
    app.run()
