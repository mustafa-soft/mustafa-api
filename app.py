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

def verify_resp(tool):
    return jsonify({
        "verified": True, "ready": True,
        "reseller": RESELLER_NAME, "tool": tool,
        "email": RESELLER_EMAIL,
        "auto": bool(GSM_API_KEY),
        "gsm_api": GSM_API_URL, "login": GSM_LOGIN
    })

@app.route('/')
def home():
    return jsonify({
        "status": "AUTO ON ✅" if GSM_API_KEY else "AUTO OFF",
        "reseller": RESELLER_NAME, "tools": 15,
        "gsm_api": GSM_API_URL, "auto": bool(GSM_API_KEY)
    })

@app.route('/chimera/verify')
def v_chimera(): return verify_resp("chimera")
@app.route('/unlocktool/verify')
def v_unlocktool(): return verify_resp("unlocktool")
@app.route('/tsmtool/verify')
def v_tsm(): return verify_resp("tsmtool")
@app.route('/haafedk/verify')
def v_haaf(): return verify_resp("haafedk")
@app.route('/octopus/verify')
def v_oct(): return verify_resp("octopus")
@app.route('/eft/verify')
def v_eft(): return verify_resp("eft")
@app.route('/pandora/verify')
def v_pan(): return verify_resp("pandora")
@app.route('/z3x/verify')
def v_z3x(): return verify_resp("z3x")
@app.route('/sigma/verify')
def v_sig(): return verify_resp("sigma")
@app.route('/muslimodin/verify')
def v_mus(): return verify_resp("muslimodin")
@app.route('/tfttool/verify')
def v_tft(): return verify_resp("tfttool")
@app.route('/skunlocker/verify')
def v_sk(): return verify_resp("skunlocker")
@app.route('/dft/verify')
def v_dft(): return verify_resp("dft")
@app.route('/services/verify')
def v_ser(): return verify_resp("services")
@app.route('/xiaomitool/verify')
def v_xia(): return verify_resp("xiaomitool")

@app.route('/api/create-activation', methods=['GET','POST'])
def create_activation():
    data = request.get_json() or request.args.to_dict() if request.args else {}
    try:
        if not data: data = request.get_json(force=True) or {}
    except: data = {}
    email = data.get('email','test@gmail.com')
    tool = data.get('tool','chimera')
    duration = data.get('duration','12 months')

    # TRY AUTO → api2-gsm.elbroos.com
    if GSM_API_KEY:
        headers = {"Authorization": f"Bearer {GSM_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "email": email, "tool": tool, "duration": duration,
            "api_key": GSM_API_KEY, "key": GSM_API_KEY,
            "login": GSM_LOGIN, "reseller": RESELLER_NAME
        }
        for endpoint in ["/api/activation", "/api/place_order", "/api/create-order", "/api/order"]:
            url = GSM_API_URL.rstrip('/') + endpoint
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=12)
                if r.status_code in [200,201]:
                    try: j = r.json()
                    except: j = {"raw": r.text[:500]}
                    return jsonify({
                        "status":"success","auto":True,
                        "message": f"تم تفعيل {tool} اتوماتك ✅",
                        "email":email,"tool":tool,"endpoint":url,
                        "elbroos_response":j
                    })
            except: continue

    # FALLBACK MANUAL
    return jsonify({
        "status":"success","auto":False,
        "env_key_present": bool(GSM_API_KEY),
        "message": f"تم استلام {tool} - واتساب 0900287738",
        "email":email,"tool":tool,
        "whatsapp_url": f"https://wa.me/249900287738?text=طلب {tool} {duration} - {email}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
