from flask import Flask, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
@app.route('/')
def home():
    return jsonify({"status": "Mustafa API is running!"})
@app.route('/api/create-activation', methods=['POST'])
def create_activation():
    data = request.get_json() or {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '1 month')
    return jsonify({"status": "success","message": f"تم استلام طلب {duration}","email": email})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
