from flask import Flask, jsonify
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
    # إرجاع رد JSON مباشر عند فتح رابط الـ API
    return jsonify({
        "status": "online",
        "message": "Mustafa API is running securely",
        "author": "Mustafa GS"
    })

@app.route('/api')
def api():
    return jsonify({"status": "Mustafa GS"})

if __name__ == '__main__':
    app.run(debug=True)
