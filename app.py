from flask import Flask, send_from_directory, jsonify
from flask_talisman import Talisman
import os, datetime

app = Flask(__name__)

# إعداد سياسة أمان المحتوى لضمان تقييم A+
csp = {
    'default-src': ["'self'"]
}

Talisman(app, content_security_policy=csp)

@app.route('/')
def home():
    # إعادة عرض واجهة موقعك الطبيعية على Vercel
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return 'index.html not found!'

@app.route('/api')
def api():
    # جعل الـ JSON يظهر عند الدخول على مسار /api
    return jsonify({
        "status": "online",
        "message": "Mustafa API is running securely",
        "author": "Mustafa GS"
    })

if __name__ == '__main__':
    app.run(debug=True)
