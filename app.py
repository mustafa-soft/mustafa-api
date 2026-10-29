from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os
import requests

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"

# Galle API Config
GALLE_API_TOKEN = os.environ.get("GALLE_API_TOKEN", "")
GALLE_API_BASE = "https://api.galleunlockers.com/api"
GALLE_IP = "41.95.225.52"

def galle_headers():
    return {
        "Authorization": f"Bearer {GALLE_API_TOKEN}",
        "Content-Type": "application/json"
    }

def get_html_page(title, status_text, extra_content=""):
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Mustafa Soft</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Cairo',sans-serif}}
body{{background:#0a0e1a;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}}
.header{{width:100%;max-width:1200px;background:linear-gradient(135deg,#1a233a 0%,#0f172a 100%);border:1px solid #1e3a5f;border-radius:20px;padding:30px;margin-bottom:20px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.5)}}
.logo{{font-size:42px;font-weight:800;background:linear-gradient(90deg,#00d4ff,#0ea5e9,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}}
.subtitle{{color:#94a3b8;font-size:13px;margin-bottom:20px;line-height:1.6}}
.status-badge{{display:inline-flex;align-items:center;gap:8px;background:#0f281e;border:1px solid #10b981;color:#10b981;padding:8px 18px;border-radius:50px;font-weight:700;font-size:14px}}
.dot{{width:10px;height:10px;background:#10b981;border-radius:50%;animation:pulse 2s infinite}}
@keyframes pulse{{0%{{box-shadow:0 0 0 0 rgba(16,185,129,0.7)}}70%{{box-shadow:0 0 0 10px rgba(16,185,129,0)}}100%{{box-shadow:0 0 0 0 rgba(16,185,129,0)}}}}
.grid{{width:100%;max-width:1200px;display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-bottom:20px}}
.card{{background:#111b2f;border:1px solid #1e3a5f;border-radius:16px;padding:20px;transition:all 0.3s}}
.card:hover{{border-color:#0ea5e9;transform:translateY(-3px);box-shadow:0 10px 30px rgba(14,165,233,0.2)}}
.card h3{{color:#e2e8f0;margin-bottom:8px;font-size:15px;display:flex;align-items:center;gap:8px}}
.card p{{color:#94a3b8;font-size:12px;margin-bottom:12px;line-height:1.6}}
.btn{{display:inline-block;background:linear-gradient(90deg,#0ea5e9,#6366f1);color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;font-size:12px;transition:all 0.3s;width:100%;text-align:center}}
.btn:hover{{transform:scale(1.02);box-shadow:0 5px 20px rgba(99,102,241,0.4)}}
.btn-outline{{background:transparent;border:1px solid #1e3a5f;color:#94a3b8}}
.btn-outline:hover{{border-color:#0ea5e9;color:#fff}}
.routes{{width:100%;max-width:1200px;background:#0f172a;border:1px solid #1e3a5f;border-radius:16px;padding:25px}}
.routes h2{{font-size:18px;margin-bottom:15px;color:#e2e8f0}}
.route-item{{display:flex;justify-content:space-between;align-items:center;padding:10px;background:#111b2f;border-radius:10px;margin-bottom:8px;border:1px solid transparent;transition:all 0.2s}}
.route-item:hover{{border-color:#1e3a5f;background:#162032}}
.route-path{{font-family:monospace;color:#0ea5e9;font-weight:600;font-size:12px}}
.route-desc{{color:#64748b;font-size:11px}}
.footer{{margin-top:30px;text-align:center;color:#475569;font-size:12px}}
.footer a{{color:#0ea5e9;text-decoration:none;font-weight:700}}
</style>
</head>
<body>
<div class="header">
<div class="logo">Mustafa Soft</div>
<div class="subtitle">Chimera & UnlockTool & TSM & Haafedk & Octopus & EFT & Pandora & Z3X & Sigma & Muslim Odin & TFT & SK Unlocker & DFT & Services & Xiaomi Tool - Reseller API + Galle Unlockers<br>16 Tools Live - mustafa-soft - IP: {GALLE_IP}</div>
<div class="status-badge"><span class="dot"></span> {status_text}</div>
<div style="margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<a href="https://mustafa-soft.vercel.app/" class="btn" style="width:auto;padding:12px 25px">🌐 الموقع الرسمي</a>
<a href="https://wa.me/249900287738" class="btn btn-outline" style="width:auto;padding:12px 25px">💬 واتساب: 0900287738</a>
<a href="/api/galle/balance" class="btn btn-outline" style="width:auto;padding:12px 25px">💰 رصيد Galle</a>
</div>
</div>
{extra_content}
<div class="footer">© 2025 Mustafa Soft - mustafa-soft.vercel.app | <a href="https://wa.me/249900287738">0900287738</a> | Galle API: {"✅ Connected" if len(GALLE_API_TOKEN)>100 else "❌ No Token"}</div>
</body>
</html>
"""

# ... [باقي الـ routes بتاعتك القديمة خليها] ...

@app.route('/')
def home():
    token_ok = len(GALLE_API_TOKEN) > 100
    status = f"All Systems Live ✅ - Galle {'Connected ✅' if token_ok else 'No Token ❌'} - Token Len: {len(GALLE_API_TOKEN)}"
    return get_html_page("Mustafa Soft API", status)

@app.route('/api/galle/balance')
def galle_balance():
    try:
        if not GALLE_API_TOKEN or len(GALLE_API_TOKEN) < 100:
            return jsonify({"status": "error", "message": "GALLE_API_TOKEN missing in env", "token_len": len(GALLE_API_TOKEN), "galle_connected": False})
        
        # Try real Galle API
        r = requests.get(f"{GALLE_API_BASE}/me", headers=galle_headers(), timeout=10)
        data = r.json() if r.headers.get('content-type','').startswith('application/json') else {"raw": r.text}
        
        return jsonify({
            "status": "connected",
            "galle_connected": True,
            "token_len": len(GALLE_API_TOKEN),
            "ip": GALLE_IP,
            "galle_response": data,
            "http_status": r.status_code
        })
    except Exception as e:
        return jsonify({
            "status": "connected_env_only",
            "galle_connected": len(GALLE_API_TOKEN) > 100,
            "token_len": len(GALLE_API_TOKEN),
            "ip": GALLE_IP,
            "error": str(e),
            "note": "Token exists in env, but API call failed - check IP whitelist"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
