from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"

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
.header{{width:100%;max-width:900px;background:linear-gradient(135deg,#1a233a 0%,#0f172a 100%);border:1px solid #1e3a5f;border-radius:20px;padding:30px;margin-bottom:20px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.5)}}
.logo{{font-size:42px;font-weight:800;background:linear-gradient(90deg,#00d4ff,#0ea5e9,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}}
.subtitle{{color:#94a3b8;font-size:16px;margin-bottom:20px}}
.status-badge{{display:inline-flex;align-items:center;gap:8px;background:#0f281e;border:1px solid #10b981;color:#10b981;padding:8px 18px;border-radius:50px;font-weight:700;font-size:14px}}
.dot{{width:10px;height:10px;background:#10b981;border-radius:50%;animation:pulse 2s infinite}}
@keyframes pulse{{0%{{box-shadow:0 0 0 0 rgba(16,185,129,0.7)}}70%{{box-shadow:0 0 0 10px rgba(16,185,129,0)}}100%{{box-shadow:0 0 0 0 rgba(16,185,129,0)}}}}
.grid{{width:100%;max-width:900px;display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-bottom:20px}}
.card{{background:#111b2f;border:1px solid #1e3a5f;border-radius:16px;padding:20px;transition:all 0.3s}}
.card:hover{{border-color:#0ea5e9;transform:translateY(-3px);box-shadow:0 10px 30px rgba(14,165,233,0.2)}}
.card h3{{color:#e2e8f0;margin-bottom:8px;font-size:16px;display:flex;align-items:center;gap:8px}}
.card p{{color:#94a3b8;font-size:13px;margin-bottom:12px;line-height:1.6}}
.btn{{display:inline-block;background:linear-gradient(90deg,#0ea5e9,#6366f1);color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;transition:all 0.3s;width:100%;text-align:center}}
.btn:hover{{transform:scale(1.02);box-shadow:0 5px 20px rgba(99,102,241,0.4)}}
.btn-outline{{background:transparent;border:1px solid #1e3a5f;color:#94a3b8}}
.btn-outline:hover{{border-color:#0ea5e9;color:#fff}}
.routes{{width:100%;max-width:900px;background:#0f172a;border:1px solid #1e3a5f;border-radius:16px;padding:25px}}
.routes h2{{font-size:18px;margin-bottom:15px;color:#e2e8f0}}
.route-item{{display:flex;justify-content:space-between;align-items:center;padding:12px;background:#111b2f;border-radius:10px;margin-bottom:10px;border:1px solid transparent;transition:all 0.2s}}
.route-item:hover{{border-color:#1e3a5f;background:#162032}}
.route-path{{font-family:monospace;color:#0ea5e9;font-weight:600}}
.route-desc{{color:#64748b;font-size:12px}}
.footer{{margin-top:30px;text-align:center;color:#475569;font-size:12px}}
.footer a{{color:#0ea5e9;text-decoration:none;font-weight:700}}
</style>
</head>
<body>
<div class="header">
<div class="logo">Mustafa Soft</div>
<div class="subtitle">Chimera Tool & UnlockTool - Reseller API</div>
<div class="status-badge"><span class="dot"></span> {status_text}</div>
<div style="margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<a href="https://mustafa-soft.vercel.app/" class="btn" style="width:auto;padding:12px 25px">🌐 الموقع الرسمي</a>
<a href="https://wa.me/249900287738" class="btn btn-outline" style="width:auto;padding:12px 25px">💬 واتساب: 0900287738</a>
</div>
</div>
<div class="grid">
<div class="card">
<h3>🔧 Chimera Tool</h3>
<p>تفعيل رسمي - 3 / 6 / 12 شهر<br>أداة صيانة هواتف احترافية</p>
<a href="/chimera" class="btn">عرض Chimera API</a>
</div>
<div class="card">
<h3>🔓 UnlockTool</h3>
<p>تفعيل رسمي - 3 / 6 / 12 شهر<br>فك شفرة وإزالة FRP</p>
<a href="/unlocktool" class="btn">عرض UnlockTool API</a>
</div>
<div class="card">
<h3>✅ Verify System</h3>
<p>نظام التحقق للموزعين<br>Chimera + UnlockTool Ready</p>
<a href="/chimera/verify" class="btn">تحقق Chimera</a>
</div>
</div>
<div class="routes">
<h2>📡 Available API Routes</h2>
<div class="route-item"><span class="route-path">/chimera</span><span class="route-desc">Chimera Reseller Info</span></div>
<div class="route-item"><span class="route-path">/chimera/verify</span><span class="route-desc">Verify Chimera</span></div>
<div class="route-item"><span class="route-path">/unlocktool</span><span class="route-desc">UnlockTool Reseller Info</span></div>
<div class="route-item"><span class="route-path">/unlocktool/verify</span><span class="route-desc">Verify UnlockTool</span></div>
<div class="route-item"><span class="route-path">/api/create-activation</span><span class="route-desc">Create Activation Order</span></div>
<div class="route-item"><span class="route-path">/activate, /check, /verify, /api</span><span class="route-desc">All Working ✅</span></div>
{extra_content}
</div>
<div class="footer">
<p>© 2025 Mustafa Soft - All Rights Reserved</p>
<p style="margin-top:5px">Reseller: <strong>mustafa-soft</strong> | Email: {RESELLER_EMAIL}</p>
<p style="margin-top:8px"><a href="https://mustafa-soft.vercel.app/">mustafa-soft.vercel.app</a> | <a href="https://mustafa-api-1.onrender.com">mustafa-api-1.onrender.com</a></p>
</div>
</body>
</html>
"""

@app.route('/')
def home():
    return get_html_page("API Home", "API is Running ✅ - mustafa-soft")

@app.route('/chimera')
def chimera():
    username = RESELLER_NAME
    hash_val = hashlib.md5(username.encode()).hexdigest()
    if request.args.get('format') == 'json':
        return jsonify({"reseller": username, "md5_hash": hash_val, "api_url": "https://mustafa-api-1.onrender.com", "status": "Ready to be reseller for Chimera Tool"})
    extra = f"<div style='margin-top:15px;padding:15px;background:#111b2f;border-radius:10px;font-family:monospace;font-size:12px;color:#0ea5e9'>Reseller: mustafa-soft<br>MD5: {hash_val}<br>API: https://mustafa-api-1.onrender.com</div>"
    return get_html_page("Chimera Tool", "Chimera Ready ✅", extra)

@app.route('/chimera/verify')
def verify_chimera():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "chimera"})

@app.route('/unlocktool')
def unlocktool():
    return jsonify({
        "reseller": RESELLER_NAME,
        "email": RESELLER_EMAIL,
        "api_url": "https://mustafa-api-1.onrender.com/unlocktool",
        "status": "Ready to be reseller for UnlockTool",
        "website": "https://mustafa-soft.vercel.app/"
    })

@app.route('/activate')
@app.route('/check')
@app.route('/verify')
@app.route('/api')
def extra_routes():
    return get_html_page("API Status", "All Routes Working ✅ - Mustafa GSM API Running")

@app.route('/unlocktool/verify')
def verify_unlocktool():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "unlocktool", "email": RESELLER_EMAIL})

@app.route('/api/create-activation', methods=['GET', 'POST'])
def create_activation():
    data = request.get_json() or {} if request.is_json else request.args.to_dict() if request.args else {}
    if not data:
        try:
            data = request.get_json(force=True) or {}
        except:
            data = {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '12 months')
    tool = data.get('tool', 'chimera')
    return jsonify({
        "status": "success",
        "message": f"تم استلام طلب تفعيل {tool} - {duration}",
        "email": email,
        "tool": tool,
        "note": "سيتم التفعيل يدويا - واتساب 0900287738",
        "chimera_ready": True,
        "unlocktool_ready": True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
