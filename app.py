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
    token_ok = len(GALLE_API_TOKEN) > 100
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
<style>
body{{background:#0a0e1a;color:#fff;font-family:Cairo;padding:20px}}
.header{{background:#1a233a;padding:30px;border-radius:20px;text-align:center}}
.btn{{background:linear-gradient(90deg,#0ea5e9,#6366f1);color:#fff;padding:12px 25px;border-radius:10px;text-decoration:none;display:inline-block;margin:5px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:20px 0}}
.card{{background:#111b2f;border:1px solid #1e3a5f;border-radius:16px;padding:20px}}
</style>
</head>
<body>
<div class="header">
<h1>Mustafa Soft - 15 Tools + Galle</h1>
<div>IP: {GALLE_IP} | Galle: {"Connected Len "+str(len(GALLE_API_TOKEN)) if token_ok else "No Token"} | {status_text}</div>
<div style="margin-top:20px">
<a href="/api/galle/balance" class="btn">💰 رصيد Galle</a>
<a href="https://mustafa-soft.vercel.app/" class="btn">🌐 الموقع</a>
</div>
</div>
{extra_content}
</body>
</html>
"""

def make_json(tool, msg, products):
    return jsonify({"tool": tool, "reseller": RESELLER_NAME, "status": msg, "products": products, "galle_connected": len(GALLE_API_TOKEN)>100})

@app.route('/')
def home():
    token_ok = len(GALLE_API_TOKEN) > 100
    status = f"All Systems Live ✅ - 15 Tools + Galle {'Connected ✅ Len:'+str(len(GALLE_API_TOKEN)) if token_ok else 'No Token ❌'} - IP {GALLE_IP}"
    cards = "<div class='grid'>"
    for name in ["Chimera","UnlockTool","TSM","Haafedk","Octopus","EFT","Pandora","Z3X","Sigma","Muslim Odin","TFT","SK","DFT","Services","Xiaomi","Galle"]:
        cards += f"<div class='card'><h3>{name}</h3><a href='/api/galle/balance' class='btn'>Check</a></div>"
    cards += "</div>"
    return get_html_page("Mustafa Soft API", status, cards)

@app.route('/api/galle/balance')
def galle_balance():
    try:
        if not GALLE_API_TOKEN or len(GALLE_API_TOKEN) < 100:
            return jsonify({"status": "error", "message": "GALLE_API_TOKEN missing", "token_len": len(GALLE_API_TOKEN), "galle_connected": False, "ip": GALLE_IP}})
        r = requests.get(f"{GALLE_API_BASE}/me", headers=galle_headers(), timeout=15)
        try: data = r.json()
        except: data = {"raw": r.text[:500]}
        return jsonify({"status": "connected", "galle_connected": True, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "http_status": r.status_code, "galle_data": data}})
    except Exception as e:
        return jsonify({"status": "token_exists_but_api_error", "galle_connected": len(GALLE_API_TOKEN)>100, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "error": str(e)}})

@app.route('/chimera')
def chimera(): return get_html_page("Chimera", "Chimera Ready ✅")
@app.route('/chimera/verify')
def verify_chimera(): return jsonify({"verified": True, "reseller": RESELLER_NAME})

@app.route('/unlocktool')
def unlocktool(): return get_html_page("UnlockTool", "Ready ✅")
@app.route('/tsmtool')
def tsmtool(): return get_html_page("TSM", "Ready ✅")
@app.route('/haafedk')
def haafedk(): return get_html_page("Haafedk", "Ready ✅")
@app.route('/octopus')
def octopus(): return get_html_page("Octopus", "Ready ✅")
@app.route('/eft')
def eft(): return get_html_page("EFT", "Ready ✅")
@app.route('/pandora')
def pandora(): return get_html_page("Pandora", "Ready ✅")
@app.route('/z3x')
def z3x(): return get_html_page("Z3X", "Ready ✅")
@app.route('/sigma')
def sigma(): return get_html_page("Sigma", "Ready ✅")
@app.route('/muslimodin')
def muslimodin(): return get_html_page("Muslim Odin", "Ready ✅")
@app.route('/tfttool')
def tfttool(): return get_html_page("TFT", "Ready ✅")
@app.route('/skunlocker')
def skunlocker(): return get_html_page("SK", "Ready ✅")
@app.route('/dft')
def dft(): return get_html_page("DFT", "Ready ✅")
@app.route('/services')
def services_route(): return get_html_page("Services", "Ready ✅")
@app.route('/xiaomitool')
def xiaomitool(): return get_html_page("Xiaomi", "Ready ✅")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
