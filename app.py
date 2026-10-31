from flask import Flask, send_from_directory, jsonify
from flask_talisman import Talisman
import os, datetime

app = Flask(__name__)

# إعداد سياسة أمان المحتوى لتصبح خضراء وتحصل على A+
csp = {
    'default-src': ["'self'"]
}

Talisman(app, content_security_policy=csp)

@app.route('/')
def home():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return 'index.html not found!'

@app.route('/api')
def api():
    return jsonify({"status":"Mustafa GS"})

if __name__ == '__main__':
    app.run(debug=True)
