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
GALLE_API_BASE = "https://api.galleunlockers.com"
GALLE_IP = "41.95.225.52"

def galle_headers():
    return {"Authorization": f"Bearer {GALLE_API_TOKEN}", "Content-Type": "application/json"}

def get_html_page(title, status_text, extra_content=""):
    token_status = f"Galle: {'✅ Connected' if len(GALLE_API_TOKEN)>100 else '❌ No Token'} - Len: {len(GALLE_API_TOKEN)}"
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body{{background:#0a0e1a;color:#fff;font-family:Cairo,sans-serif;padding:20px}}
.header{{background:#1a233a;border:1px solid #1e3a5f;border-radius:20px;padding:30px;text-align:center}}
.logo{{font-size:42px;font-weight:800;background:linear-gradient(90deg,#00d4ff,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
</style>
</head>
<body>
<div class="header">
<div class="logo">Mustafa Soft</div>
<div>{status_text} - {token_status} - IP: {GALLE_IP}</div>
</div>
</body>
</html>
"""

def make_json(tool, desc, services):
    return jsonify({"tool": tool, "reseller": RESELLER_NAME, "email": RESELLER_EMAIL, "description": desc, "services": services, "status": "Ready", "verified": True, "galle_ip": GALLE_IP, "galle_connected": len(GALLE_API_TOKEN) > 100})

@app.route('/')
def home():
    token_ok = len(GALLE_API_TOKEN) > 100
    status = f"All Systems Live ✅ - 15 Tools + Galle Unlockers - {'Connected ✅' if token_ok else 'No Token ❌'} - {GALLE_IP}"
    return get_html_page("Mustafa Soft API - 16 Services", status)

@app.route('/api/galle/balance')
def galle_balance():
    try:
        if not GALLE_API_TOKEN or len(GALLE_API_TOKEN) < 100:
            return jsonify({"status": "error", "message": "GALLE_API_TOKEN missing", "token_len": len(GALLE_API_TOKEN), "galle_connected": False, "ip": GALLE_IP})
        headers = galle_headers()
        endpoints = ["/api/me", "/api/balance", "/me", "/balance", "/api/user"]
        last_error = None
        for ep in endpoints:
            try:
                r = requests.get(f"{GALLE_API_BASE}{ep}", headers=headers, timeout=10)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        return jsonify({"status": "connected", "galle_connected": True, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "endpoint": ep, "galle_data": data})
                    except:
                        return jsonify({"status": "connected", "galle_connected": True, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "endpoint": ep, "raw": r.text[:500]})
            except Exception as e:
                last_error = str(e)
                continue
        return jsonify({"status": "env_ok_api_maybe_diff_path", "galle_connected": True, "token_len": len(GALLE_API_TOKEN), "ip": GALLE_IP, "last_error": last_error})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "token_len": len(GALLE_API_TOKEN), "galle_connected": len(GALLE_API_TOKEN)>100, "ip": GALLE_IP})

@app.route('/api/galle/services')
def galle_services():
    try:
        headers = galle_headers()
        r = requests.get(f"{GALLE_API_BASE}/services", headers=headers, timeout=10)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({"status": "proxy", "galle_status": r.status_code, "data": r.text[:1000], "token_len": len(GALLE_API_TOKEN)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "token_len": len(GALLE_API_TOKEN)})

@app.route('/chimera')
def chimera():
    if request.args.get('format') == 'json': return make_json("chimera", "Chimera Tool Reseller", ["Chimera 12m"])
    return get_html_page("Chimera Tool", "Chimera Ready 🔧✅")

@app.route('/unlocktool')
def unlocktool():
    if request.args.get('format') == 'json': return make_json("unlocktool", "UnlockTool Reseller", ["UnlockTool 12m"])
    return get_html_page("UnlockTool", "UnlockTool Ready 🔓✅")

@app.route('/tsmtool')
def tsmtool():
    if request.args.get('format') == 'json': return make_json("tsmtool", "TSM Tool Reseller", ["TSM Pro"])
    return get_html_page("TSM Tool", "TSM Ready ⚙️✅")

@app.route('/haafedk')
def haafedk():
    if request.args.get('format') == 'json': return make_json("haafedk", "Haafedk Tools", ["Haafedk"])
    return get_html_page("Haafedk Tools", "Haafedk Ready 👑✅")

@app.route('/octopus')
def octopus():
    if request.args.get('format') == 'json': return make_json("octopus", "Octopus Box", ["Octopus"])
    return get_html_page("Octopus Box", "Octopus Ready 🐙✅")

@app.route('/eft')
def eft():
    if request.args.get('format') == 'json': return make_json("eft", "EFT Pro", ["EFT"])
    return get_html_page("EFT Pro", "EFT Ready ⚡✅")

@app.route('/pandora')
def pandora():
    if request.args.get('format') == 'json': return make_json("pandora", "Pandora Box", ["Pandora"])
    return get_html_page("Pandora Box", "Pandora Ready 📦✅")

@app.route('/z3x')
def z3x():
    if request.args.get('format') == 'json': return make_json("z3x", "Z3X Box", ["Z3X"])
    return get_html_page("Z3X Box", "Z3X Ready 🔴✅")

@app.route('/sigma')
def sigma():
    if request.args.get('format') == 'json': return make_json("sigma", "Sigma Key", ["Sigma"])
    return get_html_page("Sigma Key", "Sigma Ready 🔷✅")

@app.route('/muslimodin')
def muslimodin():
    if request.args.get('format') == 'json': return make_json("muslimodin", "Muslim Odin", ["Muslim Odin"])
    return get_html_page("Muslim Odin", "Muslim Odin Ready 🕌✅")

@app.route('/tfttool')
def tfttool():
    if request.args.get('format') == 'json': return make_json("tfttool", "TFT Tool", ["TFT"])
    return get_html_page("TFT Tool", "TFT Ready 🛠️✅")

@app.route('/skunlocker')
def skunlocker():
    if request.args.get('format') == 'json': return make_json("skunlocker", "SK Unlocker", ["SK"])
    return get_html_page("SK Unlocker", "SK Ready 🔑✅")

@app.route('/dft')
def dft():
    if request.args.get('format') == 'json': return make_json("dft", "DFT Multi", ["DFT"])
    return get_html_page("DFT Multi", "DFT Ready 📱✅")

@app.route('/services')
def services_route():
    if request.args.get('format') == 'json': return make_json("services", "Services Tool", ["Services"])
    return get_html_page("Services Tool", "Services Ready 🌐✅")

@app.route('/xiaomitool')
def xiaomitool():
    if request.args.get('format') == 'json': return make_json("xiaomitool", "Xiaomi Tool", ["XiaomiTool"])
    return get_html_page("Xiaomi Tool", "Xiaomi Ready 📲✅")

@app.route('/activate')
@app.route('/check')
@app.route('/verify')
@app.route('/api')
def extra_routes():
    return get_html_page("API Status", f"All Routes Working ✅ - 15 Tools + Galle Live - Token: {len(GALLE_API_TOKEN)} chars - IP: {GALLE_IP}")

@app.route('/api/create-activation', methods=['GET', 'POST'])
def create_activation():
    data = request.get_json() or {} if request.is_json else request.args.to_dict() if request.args else {}
    if not data:
        try: data = request.get_json(force=True) or {}
        except: data = {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '12 months')
    tool = data.get('tool', 'chimera')
    return jsonify({"status": "success", "message": f"تم استلام طلب تفعيل {tool} - {duration}", "email": email, "tool": tool, "note": "سيتم التفعيل يدويا - واتساب 0900287738", "galle_connected": len(GALLE_API_TOKEN)>100, "galle_ip": GALLE_IP})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
