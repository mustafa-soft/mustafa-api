from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"
GSM_API_KEY = os.environ.get("GSM_API_KEY", "")
GSM_API_URL = os.environ.get("GSM_API_URL", "https://api2-gsm.elbroos.com/")
GSM_LOGIN = "mustafaopen88@gmail.com"

def get_html_page(title, status_text):
    return f"<html><head><title>{title}</title></head><body><h1>{status_text} - AUTO {'ON ✅' if GSM_API_KEY else 'OFF'}</h1><p>15 Tools Live</p></body></html>"

def make_json(tool, msg, prods):
    return jsonify({"tool": tool, "status": "Ready", "message": msg, "products": prods, "reseller": RESELLER_NAME, "auto": bool(GSM_API_KEY)})

@app.route('/')
def home(): return get_html_page("Mustafa Soft", f"AUTO {'ON' if GSM_API_KEY else 'OFF'} - 15 Tools")
@app.route('/chimera/verify')
def verify_chimera(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "chimera", "email": RESELLER_EMAIL, "auto": bool(GSM_API_KEY)})
@app.route('/unlocktool/verify')
def verify_unlocktool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "unlocktool", "email": RESELLER_EMAIL})

# ... باقي الـ 13 أداة نفس الشي (تقدر تترك القديم) ...

@app.route('/api/create-activation', methods=['GET','POST'])
def create_activation():
    data = request.get_json() or request.args.to_dict() if request.args else {}
    try:
        if not data: data = request.get_json(force=True) or {}
    except: data = {}
    email = data.get('email', 'test@gmail.com')
    tool = data.get('tool', 'chimera')
    duration = data.get('duration', '12 months')

    # AUTO MODE
    if GSM_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GSM_API_KEY}", "Content-Type": "application/json"}
            payload = {"email": email, "tool": tool, "duration": duration, "key": GSM_API_KEY, "login": GSM_LOGIN}
            url = GSM_API_URL.rstrip('/') + '/api/activation'
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            if r.status_code in [200, 201]:
                return jsonify({"status":"success","auto":True,"message":f"تم تفعيل {tool} اتوماتك ✅","email":email,"tool":tool})
        except Exception as e:
            print(f"Auto failed: {e}")

    return jsonify({"status":"success","auto":False,"message":f"تم استلام {tool} - واتساب 0900287738","email":email,"env_key": bool(GSM_API_KEY)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
