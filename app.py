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
.header{{width:100%;max-width:1100px;background:linear-gradient(135deg,#1a233a 0%,#0f172a 100%);border:1px solid #1e3a5f;border-radius:20px;padding:30px;margin-bottom:20px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.5)}}
.logo{{font-size:42px;font-weight:800;background:linear-gradient(90deg,#00d4ff,#0ea5e9,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}}
.subtitle{{color:#94a3b8;font-size:15px;margin-bottom:20px}}
.status-badge{{display:inline-flex;align-items:center;gap:8px;background:#0f281e;border:1px solid #10b981;color:#10b981;padding:8px 18px;border-radius:50px;font-weight:700;font-size:14px}}
.dot{{width:10px;height:10px;background:#10b981;border-radius:50%;animation:pulse 2s infinite}}
@keyframes pulse{{0%{{box-shadow:0 0 0 0 rgba(16,185,129,0.7)}}70%{{box-shadow:0 0 0 10px rgba(16,185,129,0)}}100%{{box-shadow:0 0 0 0 rgba(16,185,129,0)}}}}
.grid{{width:100%;max-width:1100px;display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-bottom:20px}}
.card{{background:#111b2f;border:1px solid #1e3a5f;border-radius:16px;padding:20px;transition:all 0.3s}}
.card:hover{{border-color:#0ea5e9;transform:translateY(-3px);box-shadow:0 10px 30px rgba(14,165,233,0.2)}}
.card h3{{color:#e2e8f0;margin-bottom:8px;font-size:16px;display:flex;align-items:center;gap:8px}}
.card p{{color:#94a3b8;font-size:13px;margin-bottom:12px;line-height:1.6}}
.btn{{display:inline-block;background:linear-gradient(90deg,#0ea5e9,#6366f1);color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;transition:all 0.3s;width:100%;text-align:center}}
.btn:hover{{transform:scale(1.02);box-shadow:0 5px 20px rgba(99,102,241,0.4)}}
.btn-outline{{background:transparent;border:1px solid #1e3a5f;color:#94a3b8}}
.btn-outline:hover{{border-color:#0ea5e9;color:#fff}}
.routes{{width:100%;max-width:1100px;background:#0f172a;border:1px solid #1e3a5f;border-radius:16px;padding:25px}}
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
<div class="subtitle">Chimera Tool & UnlockTool & TSM Tool & Haafedk & Octopus & EFT & Pandora & Z3X - Reseller API</div>
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
<h3>⚙️ TSM Tool</h3>
<p>تفعيل رسمي - 3 / 6 / 12 شهر<br>أداة TSM Pro - شاومي و MTK</p>
<a href="/tsmtool" class="btn">عرض TSM Tool API</a>
</div>
<div class="card">
<h3>👑 Haafedk</h3>
<p>تفعيل رسمي - أدوات هفيدك<br>FRP, Huawei, Samsung</p>
<a href="/haafedk" class="btn">عرض Haafedk API</a>
</div>
<div class="card">
<h3>🐙 Octopus</h3>
<p>تفعيل رسمي - Octopus Box<br>LG, Samsung - فلاش و فك شفرة</p>
<a href="/octopus" class="btn" style="background:linear-gradient(90deg,#f59e0b,#ef4444)">عرض Octopus API</a>
</div>
<div class="card">
<h3>⚡ EFT Pro</h3>
<p>تفعيل رسمي - EFT Dongle<br>MTK, SPD, Qualcomm - الأفضل</p>
<a href="/eft" class="btn" style="background:linear-gradient(90deg,#10b981,#06b6d4)">عرض EFT API</a>
</div>
<div class="card">
<h3>📦 Pandora Box</h3>
<p>تفعيل رسمي - Pandora Tool<br>MTK, Unlock, FRP, Repair</p>
<a href="/pandora" class="btn" style="background:linear-gradient(90deg,#8b5cf6,#ec4899)">عرض Pandora API</a>
</div>
<div class="card">
<h3>🔴 Z3X Box</h3>
<p>تفعيل رسمي - Z3X Samsung Tool Pro<br>LG, Samsung - أقوى أداة</p>
<a href="/z3x" class="btn" style="background:linear-gradient(90deg,#dc2626,#991b1b)">عرض Z3X API</a>
</div>
<div class="card">
<h3>✅ Verify System</h3>
<p>نظام التحقق للموزعين<br>8 أدوات Ready ✅</p>
<a href="/chimera/verify" class="btn">تحقق Chimera</a>
</div>
</div>
<div class="routes">
<h2>📡 Available API Routes - 8 Tools Live</h2>
<div class="route-item"><span class="route-path">/chimera</span><span class="route-desc">Chimera Reseller Info</span></div>
<div class="route-item"><span class="route-path">/chimera/verify</span><span class="route-desc">Verify Chimera</span></div>
<div class="route-item"><span class="route-path">/unlocktool</span><span class="route-desc">UnlockTool Reseller Info</span></div>
<div class="route-item"><span class="route-path">/unlocktool/verify</span><span class="route-desc">Verify UnlockTool</span></div>
<div class="route-item"><span class="route-path">/tsmtool</span><span class="route-desc">TSM Tool Reseller Info</span></div>
<div class="route-item"><span class="route-path">/tsmtool/verify</span><span class="route-desc">Verify TSM Tool</span></div>
<div class="route-item"><span class="route-path">/haafedk</span><span class="route-desc">Haafedk Reseller Info</span></div>
<div class="route-item"><span class="route-path">/haafedk/verify</span><span class="route-desc">Verify Haafedk</span></div>
<div class="route-item"><span class="route-path">/octopus</span><span class="route-desc">Octopus Box Reseller 🆕</span></div>
<div class="route-item"><span class="route-path">/octopus/verify</span><span class="route-desc">Verify Octopus 🆕</span></div>
<div class="route-item"><span class="route-path">/eft</span><span class="route-desc">EFT Pro Reseller 🆕</span></div>
<div class="route-item"><span class="route-path">/eft/verify</span><span class="route-desc">Verify EFT 🆕</span></div>
<div class="route-item"><span class="route-path">/pandora</span><span class="route-desc">Pandora Box Reseller 🆕</span></div>
<div class="route-item"><span class="route-path">/z3x</span><span class="route-desc">Z3X Box Reseller 🆕🆕</span></div>
<div class="route-item"><span class="route-path">/z3x/verify</span><span class="route-desc">Verify Z3X 🆕🆕</span></div>
<div class="route-item"><span class="route-path">/pandora/verify</span><span class="route-desc">Verify Pandora 🆕</span></div>
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
    return get_html_page("API Home", "API is Running ✅ - 8 Tools - mustafa-soft")

@app.route('/chimera')
def chimera():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/chimera",
            "status": "Ready to be reseller for Chimera Tool",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest()
        })
    extra = f"""<div style='margin-top:15px;padding:20px;background:#111b2f;border-radius:12px;border:1px solid #1e3a5f'>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:left;direction:ltr;font-family:monospace;font-size:13px'>
    <div><span style='color:#64748b'>Reseller:</span><br><span style='color:#0ea5e9;font-weight:700'>mustafa-soft</span></div>
    <div><span style='color:#64748b'>Email:</span><br><span style='color:#fff'>{RESELLER_EMAIL}</span></div>
    <div><span style='color:#64748b'>Status:</span><br><span style='color:#10b981'>Ready for Chimera ✅</span></div>
    <div><span style='color:#64748b'>API:</span><br><span style='color:#0ea5e9'>mustafa-api-1.onrender.com</span></div>
    </div>
    </div>"""
    return get_html_page("Chimera Tool", "Chimera Tool Ready 🔧✅", extra)

@app.route('/chimera/verify')
def verify_chimera():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "chimera", "email": RESELLER_EMAIL})

@app.route('/unlocktool')
def unlocktool():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/unlocktool",
            "status": "Ready to be reseller for UnlockTool",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest()
        })
    extra = f"""<div style='margin-top:15px;padding:20px;background:#111b2f;border-radius:12px;border:1px solid #1e3a5f'>
    <div>UnlockTool Ready</div>
    </div>"""
    return get_html_page("UnlockTool", "UnlockTool Ready 🔓✅", extra)

@app.route('/unlocktool/verify')
def verify_unlocktool():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "unlocktool", "email": RESELLER_EMAIL})

@app.route('/tsmtool')
def tsmtool():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/tsmtool",
            "status": "Ready to be reseller for TSM Tool",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest()
        })
    return get_html_page("TSM Tool", "TSM Tool Ready ⚙️✅", "")

@app.route('/tsmtool/verify')
def verify_tsmtool():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "tsmtool", "email": RESELLER_EMAIL})

@app.route('/haafedk')
def haafedk():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/haafedk",
            "status": "Ready to be reseller for Haafedk Tools",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest(),
            "tools": ["Haafedk MTK", "Haafedk Samsung", "Haafedk Huawei", "Haafedk FRP"]
        })
    return get_html_page("Haafedk Tools", "Haafedk Ready 👑✅", "")

@app.route('/haafedk/verify')
def verify_haafedk():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "haafedk", "email": RESELLER_EMAIL})

@app.route('/octopus')
def octopus():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/octopus",
            "status": "Ready to be reseller for Octopus Box",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest(),
            "tools": ["Octopus LG", "Octopus Samsung", "Octopus FRP", "Octopus Huawei"]
        })
    return get_html_page("Octopus Box", "Octopus Box Ready 🐙✅", "")

@app.route('/octopus/verify')
def verify_octopus():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "octopus", "email": RESELLER_EMAIL})

@app.route('/eft')
def eft():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/eft",
            "status": "Ready to be reseller for EFT Pro Dongle",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest(),
            "tools": ["EFT MTK", "EFT SPD", "EFT Qualcomm", "EFT Apple"]
        })
    return get_html_page("EFT Pro", "EFT Pro Ready ⚡✅", "")

@app.route('/eft/verify')
def verify_eft():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "eft", "email": RESELLER_EMAIL})

@app.route('/pandora')
def pandora():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/pandora",
            "status": "Ready to be reseller for Pandora Box",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest(),
            "tools": ["Pandora MTK", "Pandora SPD", "Pandora FRP", "Pandora Network Unlock"]
        })
    return get_html_page("Pandora Box", "Pandora Box Ready 📦✅", "")

@app.route('/pandora/verify')
def verify_pandora():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "pandora", "email": RESELLER_EMAIL})

@app.route('/z3x')
def z3x():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME,
            "email": RESELLER_EMAIL,
            "api_url": "https://mustafa-api-1.onrender.com/z3x",
            "status": "Ready to be reseller for Z3X Box - Samsung Tool Pro",
            "website": "https://mustafa-soft.vercel.app/",
            "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest(),
            "tools": ["Z3X Samsung Tool Pro", "Z3X LG Tool", "Z3X Samsung Activation", "Z3X LG Activation"]
        })
    return get_html_page("Z3X Box", "Z3X Box Ready 🔴✅", "")

@app.route('/z3x/verify')
def verify_z3x():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "z3x", "email": RESELLER_EMAIL})

@app.route('/activate')
@app.route('/check')
@app.route('/verify')
@app.route('/api')
def extra_routes():
    return get_html_page("API Status", "All Routes Working ✅ - 8 Tools Live")

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
        "unlocktool_ready": True,
        "tsmtool_ready": True,
        "haafedk_ready": True,
        "octopus_ready": True,
        "eft_ready": True,
        "pandora_ready": True,
        "z3x_ready": True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
