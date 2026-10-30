from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "Mustafa GSM API is Running ✅"})

@app.route('/api/create-activation', methods=['POST'])
def create_activation():
    data = request.get_json() or {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '12')

    # هنا تربط لاحقا مع لوحة الموزع الرسمي
    return jsonify({
        "status": "success",
        "message": f"تم استلام طلب تفعيل {duration} شهر",
        "email": email,
        "note": "سيتم التفعيل يدويا من لوحة الموزع"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
