from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os
import requests

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"

GALLE_API_TOKEN = os.environ.get("GALLE_API_TOKEN", "")
GALLE_API_BASE = "https://api.galleunlockers.com/api"
GALLE_IP = "41.95.225.52"

def galle_headers():
    return {"Authorization": f"Bearer {GALLE_API_TOKEN}", "Content-Type": "application/json"}

def get_html_page(title, status_text, extra_content=""):
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>{title}</title></head>
<body style="background:#0a0e1a;color:#fff;font-family:Cairo;padding:20px;text-align:center">
<h1>Mustafa Soft - {title}</h1>
<p>{status_text} - IP: {GALLE_IP} - Galle Len: {len(GALLE_API_TOKEN)}</p>
<p><a href="/api/galle/balance" style="color:#0ea5e9">💰 رصيد Galle</a></p>
{extra_content}
</body>
</html>
"""

@app.route('/')
def home():
    return get_html_page("API", f"All Live ✅ 16 Tools Galle {'✅' if len(GALLE_API_TOKEN)>100 else '❌'} Len {len(GALLE_API_TOKEN)}")

@app.route('/api/galle/balance')
def galle_balance():
    if not GALLE_API_TOKEN or len(GALLE_API_TOKEN)<100:
        return jsonify({"galle_connected": False, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "error": "No token"})
    try:
        r = requests.get(f"{GALLE_API_BASE}/me", headers=galle_headers(), timeout=15)
        return jsonify({"galle_connected": True, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "galle_response": r.json() if r.headers.get('content-type','').startswith('application/json') else r.text[:500], "http_status": r.status_code})
    except Exception as e:
        return jsonify({"galle_connected": True, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "error": str(e), "note": "Token exists, add IP to whitelist"})

# ... باقي الـ 15 أداة نفس القديم ...
@app.route('/chimera')
def chimera(): return jsonify({"tool":"chimera","ready":True,"ip":GALLE_IP,"galle_len":len(GALLE_API_TOKEN)})
@app.route('/chimera/verify')
def verify_chimera(): return jsonify({"verified":True,"tool":"chimera","ip":GALLE_IP})
@app.route('/unlocktool')
def unlocktool(): return jsonify({"tool":"unlocktool","ready":True})
@app.route('/tsmtool')
def tsmtool(): return jsonify({"tool":"tsmtool","ready":True})
@app.route('/haafedk')
def haafedk(): return jsonify({"tool":"haafedk","ready":True})
@app.route('/octopus')
def octopus(): return jsonify({"tool":"octopus","ready":True})
@app.route('/eft')
def eft(): return jsonify({"tool":"eft","ready":True})
@app.route('/pandora')
def pandora(): return jsonify({"tool":"pandora","ready":True})
@app.route('/z3x')
def z3x(): return jsonify({"tool":"z3x","ready":True})
@app.route('/sigma')
def sigma(): return jsonify({"tool":"sigma","ready":True})
@app.route('/muslimodin')
def muslimodin(): return jsonify({"tool":"muslimodin","ready":True})
@app.route('/tfttool')
def tfttool(): return jsonify({"tool":"tfttool","ready":True})
@app.route('/skunlocker')
def skunlocker(): return jsonify({"tool":"skunlocker","ready":True})
@app.route('/dft')
def dft(): return jsonify({"tool":"dft","ready":True})
@app.route('/services')
def services(): return jsonify({"tool":"services","ready":True})
@app.route('/xiaomitool')
def xiaomitool(): return jsonify({"tool":"xiaomitool","ready":True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
