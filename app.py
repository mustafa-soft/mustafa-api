from flask import Flask, send_from_directory, jsonify
from flask_talisman import Talisman
import os

app = Flask(__name__)

# تفعيل الأمان لضمان تقييم A+
csp = {
    'default-src': ["'self'"]
}
Talisman(app, content_security_policy=csp)

@app.route('/')
def home():
    # التحقق من وجود ملف index.html لعرضه كواجهة للموقع
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return "Welcome! index.html not found, please upload your frontend file."

@app.route('/api')
def api():
    # الـ API الأساسي للبيانات بصيغة JSON
    return jsonify({
        "status": "online",
        "message": "Mustafa API is running securely",
        "author": "Mustafa GS"
    })

if __name__ == '__main__':
    app.run(debug=True)
