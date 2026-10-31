from flask import Flask, jsonify
import datetime
import os

app = Flask(__name__)

@app.route('/')
def home():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return jsonify({
            "api": "mustafa-api-1.onrender.com",
            "frontend": "mustafa-soft.vercel.app",
            "galle_connected": False,
            "status": "Mustafa GSM API is Running ✅",
            "time": str(datetime.datetime.now())
        })

@app.route('/api')
def api():
    return jsonify({
        "api": "mustafa-api-1.onrender.com",
        "frontend": "mustafa-soft.vercel.app",
        "galle_connected": False,
        "status": "Mustafa GSM API is Running ✅",
        "time": str(datetime.datetime.now())
    })

if __name__ == '__main__':
    app.run()
