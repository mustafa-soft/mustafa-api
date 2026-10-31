from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime, os

app = Flask(__name__)
CORS(app)

GALLE_URL = os.getenv("GALLE_API_URL", "https://api.galleunlockers.com")
GALLE_TOKEN = os.getenv("GALLE_API_TOKEN", "")

@app.route('/')
def home():
    return jsonify({
        "status": "Mustafa GSM API is Running ✅",
        "frontend": "mustafa-soft.vercel.app",
        "api": "mustafa-api-1.onrender.com",
        "galle_connected": bool(GALLE_TOKEN),
        "time": str(datetime.datetime.now())
    })

@app.route('/dashboard')
def dashboard():
    token_short = GALLE_TOKEN[:10] + "..." if GALLE_TOKEN else "غير موجود"
    return f"""
    <html dir='rtl' style='font-family:sans-serif;background:#0a0f1e;color:#fff;padding:20px'>
    <h1 style='color:#00ffa6'>⚡ Mustafa Soft API Dashboard</h1>
    <p>✅ API: mustafa-api-1.onrender.com</p>
    <p>✅ Frontend: mustafa-soft.vercel.app</p>
    <p>🔗 Galle URL: {GALLE_URL}</p>
    <p>🔑 Token: {token_short}</p>
    <hr>
    <h3>📦 الأوامر:</h3>
    <ul>
      <li>GET / - حالة الـ API</li>
      <li>GET /dashboard - هذه الواجهة</li>
      <li>POST /api/create-activation - تفعيل Chimera</li>
    </ul>
    <p>آخر طلب: Chimera لـ Adrr@gmail.com - 149$ - بنكك 5769269</p>
    <p style='color:#00ffa6'>الموقع شغال تمام ✅</p>
    </html>
    """

@app.route('/api/create-activation', methods=['POST','OPTIONS'])
def create():
    if request.method == 'OPTIONS': return jsonify(ok=True)
    data = request.get_json() or {}
    return jsonify(success=True, message=f"تم {data.get('tool','chimera')} لـ {data.get('email')}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))
