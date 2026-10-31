from flask import Flask, send_from_directory, jsonify
from flask_talisman import Talisman  # <--- تضعها في الأعلى هنا
import os, datetime

app = Flask(__name__)
Talisman(app, content_security_policy=None)  # <--- تفعيلها هنا مباشرة تحت تعريف app

@app.route('/')
def home():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return 'index.html not found!'

@app.route('/api')
def api():
    return jsonify({"status":"Mustafa GS"})
