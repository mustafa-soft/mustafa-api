from flask import Flask, jsonify
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "api": "mustafa-api-1.onrender.com",
        "frontend": "mustafa-soft.vercel.app",
        "galle_connected": False,
        "status": "Mustafa GSM API is Running ✅",
        "time": str(datetime.datetime.now())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
