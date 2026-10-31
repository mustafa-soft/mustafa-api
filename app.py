from flask import Flask, send_from_directory, jsonify
import os, datetime
app = Flask(__name__)
@app.route('/')
def home():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return 'index.html not found!'
@app.route('/api')
def api():
    return jsonify({"status":"Mustafa GSM API is Running ✅","frontend":"mustafa-soft.vercel.app","time":str(datetime.datetime.now())})
