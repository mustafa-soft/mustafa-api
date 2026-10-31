
from flask import Flask, jsonify, send_from_directory
import datetime
import os

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api')
def api():
    return jsonify({
        "api": "mustafa-api-1.onrender.com",
        "frontend": "mustafa-soft.vercel.app",
        "galle_connected": False,
        "status": "Mustafa GSM API is Running ✅",
        "time": str(datetime.datetime.now())
    })

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

# For Vercel
# app = app
