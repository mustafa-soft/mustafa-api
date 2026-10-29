from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

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
<div class="subtitle">Chimera & UnlockTool & TSM & Haafedk & Octopus & EFT & Pandora & Z3X & Sigma & Muslim Odin & TFT & SK Unlocker & DFT & Services & Xiaomi Tool - Reseller API<br>15 Tools Live - mustafa-soft</div>
<div class="status-badge"><span class="dot"></span> {status_text}</div>
<div style="margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<a href="https://mustafa-soft.vercel.app/" class="btn" style="width:auto;padding:12px 25px">🌐 الموقع الرسمي</a>
<a href="https://wa.me/249900287738" class="btn btn-outline" style="width:auto;padding:12px 25px">💬 واتساب: 0900287738</a>
</div>
</div>
<div class="grid">
<div class="card"><h3>🔧 Chimera Tool</h3><p>تفعيل رسمي - 3 / 6 / 12 شهر<br>صيانة هواتف احترافية</p><a href="/chimera" class="btn">عرض Chimera API</a></div>
<div class="card"><h3>🔓 UnlockTool</h3><p>تفعيل رسمي - 3 / 6 / 12 شهر<br>فك شفرة و FRP</p><a href="/unlocktool" class="btn">عرض UnlockTool API</a></div>
<div class="card"><h3>⚙️ TSM Tool</h3><p>تفعيل رسمي - TSM Pro<br>شاومي و MTK</p><a href="/tsmtool" class="btn">عرض TSM API</a></div>
<div class="card"><h3>👑 Haafedk</h3><p>تفعيل رسمي - هفيدك<br>FRP, Huawei, Samsung</p><a href="/haafedk" class="btn">عرض Haafedk API</a></div>
<div class="card"><h3>🐙 Octopus</h3><p>Octopus Box - LG, Samsung<br>فلاش و فك شفرة</p><a href="/octopus" class="btn" style="background:linear-gradient(90deg,#f59e0b,#ef4444)">عرض Octopus API</a></div>
<div class="card"><h3>⚡ EFT Pro</h3><p>EFT Dongle - MTK, SPD<br>Qualcomm - الأفضل</p><a href="/eft" class="btn" style="background:linear-gradient(90deg,#10b981,#06b6d4)">عرض EFT API</a></div>
<div class="card"><h3>📦 Pandora Box</h3><p>Pandora Tool - MTK<br>Unlock, FRP, Repair</p><a href="/pandora" class="btn" style="background:linear-gradient(90deg,#8b5cf6,#ec4899)">عرض Pandora API</a></div>
<div class="card"><h3>🔴 Z3X Box</h3><p>Z3X Samsung Tool Pro<br>LG, Samsung - أقوى أداة</p><a href="/z3x" class="btn" style="background:linear-gradient(90deg,#dc2626,#991b1b)">عرض Z3X API</a></div>
<div class="card"><h3>🔷 Sigma Key</h3><p>Sigma Plus - Huawei<br>MTK, Qualcomm, FRP</p><a href="/sigma" class="btn" style="background:linear-gradient(90deg,#2563eb,#1e40af)">عرض Sigma API</a></div>
<div class="card"><h3>🕌 Muslim Odin</h3><p>Muslim Odin Tool<br>Samsung FRP, Flash</p><a href="/muslimodin" class="btn" style="background:linear-gradient(90deg,#059669,#047857)">عرض Muslim Odin API</a></div>
<div class="card"><h3>🛠️ TFT Tool</h3><p>TFT / Try Tool<br>Unlock, FRP, Xiaomi</p><a href="/tfttool" class="btn" style="background:linear-gradient(90deg,#ea580c,#c2410c)">عرض TFT API</a></div>
<div class="card"><h3>🔑 SK Unlocker</h3><p>SK Unlocker - FRP<br>Factory Reset, MDM</p><a href="/skunlocker" class="btn" style="background:linear-gradient(90deg,#0891b2,#0e7490)">عرض SK API</a></div>
<div class="card"><h3>📱 DFT Multi</h3><p>DFT Android Multi Tool<br>MTK, SPD, Qualcomm</p><a href="/dft" class="btn" style="background:linear-gradient(90deg,#7c3aed,#6d28d9)">عرض DFT API</a></div>
<div class="card"><h3>🌐 Services Tool</h3><p>GServices - Xiaomi<br>Auth, FRP, Mi Account</p><a href="/services" class="btn" style="background:linear-gradient(90deg,#db2777,#be185d)">عرض Services API</a></div>
<div class="card"><h3>📲 Xiaomi Tool</h3><p>XiaomiTool V2 / XTM<br>Auth Bypass, FRP, Flash</p><a href="/xiaomitool" class="btn" style="background:linear-gradient(90deg,#f59e0b,#d97706)">عرض Xiaomi API</a></div>
<div class="card"><h3>✅ Verify System</h3><p>نظام التحقق للموزعين<br>15 أدوات Ready ✅</p><a href="/chimera/verify" class="btn">تحقق Chimera</a></div>
</div>
<div class="routes">
<h2>📡 Available API Routes - 15 Tools Live</h2>
<div class="route-item"><span class="route-path">/chimera</span><span class="route-desc">Chimera Reseller Info</span></div>
<div class="route-item"><span class="route-path">/chimera/verify</span><span class="route-desc">Verify Chimera</span></div>
<div class="route-item"><span class="route-path">/unlocktool</span><span class="route-desc">UnlockTool</span></div>
<div class="route-item"><span class="route-path">/unlocktool/verify</span><span class="route-desc">Verify UnlockTool</span></div>
<div class="route-item"><span class="route-path">/tsmtool</span><span class="route-desc">TSM Tool</span></div>
<div class="route-item"><span class="route-path">/tsmtool/verify</span><span class="route-desc">Verify TSM</span></div>
<div class="route-item"><span class="route-path">/haafedk</span><span class="route-desc">Haafedk</span></div>
<div class="route-item"><span class="route-path">/haafedk/verify</span><span class="route-desc">Verify Haafedk</span></div>
<div class="route-item"><span class="route-path">/octopus</span><span class="route-desc">Octopus Box 🆕</span></div>
<div class="route-item"><span class="route-path">/octopus/verify</span><span class="route-desc">Verify Octopus</span></div>
<div class="route-item"><span class="route-path">/eft</span><span class="route-desc">EFT Pro 🆕</span></div>
<div class="route-item"><span class="route-path">/eft/verify</span><span class="route-desc">Verify EFT</span></div>
<div class="route-item"><span class="route-path">/pandora</span><span class="route-desc">Pandora Box 🆕</span></div>
<div class="route-item"><span class="route-path">/pandora/verify</span><span class="route-desc">Verify Pandora</span></div>
<div class="route-item"><span class="route-path">/z3x</span><span class="route-desc">Z3X Box 🔴</span></div>
<div class="route-item"><span class="route-path">/z3x/verify</span><span class="route-desc">Verify Z3X</span></div>
<div class="route-item"><span class="route-path">/sigma</span><span class="route-desc">Sigma Key 🔷 NEW</span></div>
<div class="route-item"><span class="route-path">/sigma/verify</span><span class="route-desc">Verify Sigma</span></div>
<div class="route-item"><span class="route-path">/muslimodin</span><span class="route-desc">Muslim Odin 🕌 NEW</span></div>
<div class="route-item"><span class="route-path">/muslimodin/verify</span><span class="route-desc">Verify Muslim Odin</span></div>
<div class="route-item"><span class="route-path">/tfttool</span><span class="route-desc">TFT / Try Tool 🛠️ NEW</span></div>
<div class="route-item"><span class="route-path">/tfttool/verify</span><span class="route-desc">Verify TFT</span></div>
<div class="route-item"><span class="route-path">/skunlocker</span><span class="route-desc">SK Unlocker 🔑 NEW</span></div>
<div class="route-item"><span class="route-path">/skunlocker/verify</span><span class="route-desc">Verify SK</span></div>
<div class="route-item"><span class="route-path">/dft</span><span class="route-desc">DFT Multi 📱 NEW</span></div>
<div class="route-item"><span class="route-path">/dft/verify</span><span class="route-desc">Verify DFT</span></div>
<div class="route-item"><span class="route-path">/services</span><span class="route-desc">Services Tool 🌐 NEW</span></div>
<div class="route-item"><span class="route-path">/services/verify</span><span class="route-desc">Verify Services</span></div>
<div class="route-item"><span class="route-path">/xiaomitool</span><span class="route-desc">Xiaomi Tool 📲 NEW</span></div>
<div class="route-item"><span class="route-path">/xiaomitool/verify</span><span class="route-desc">Verify Xiaomi</span></div>
</div>
<div class="footer">Mustafa Soft - 15 Tools API - mustafa-soft.vercel.app - 0900287738</div>
</body>
</html>
"""
    return get_html_page(title, status_text, extra_content)

# Helper to create json response
def make_json(tool_name, status_text, tools_list):
    return jsonify({
        "reseller": RESELLER_NAME,
        "email": RESELLER_EMAIL,
        "api_url": f"https://mustafa-api-1.onrender.com/{tool_name}",
        "status": status_text,
        "website": "https://mustafa-soft.vercel.app/",
        "md5_hash": hashlib.md5(RESELLER_NAME.encode()).hexdigest(),
        "tools": tools_list
    })

@app.route('/')
def index():
    return get_html_page("Mustafa Soft API", "API is Running ✅ - 15 Tools - mustafa-soft")

@app.route('/chimera')
def chimera():
    if request.args.get('format') == 'json':
        return make_json("chimera", "Ready to be reseller for Chimera Tool", ["Chimera Samsung", "Chimera Huawei", "Chimera Xiaomi"])
    return get_html_page("Chimera Tool", "Chimera Tool Ready 🔧✅", "")
@app.route('/chimera/verify')
def verify_chimera(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "chimera", "email": RESELLER_EMAIL})

@app.route('/unlocktool')
def unlocktool():
    if request.args.get('format') == 'json': return make_json("unlocktool", "Ready to be reseller for UnlockTool", ["UnlockTool FRP", "UnlockTool Flash"])
    return get_html_page("UnlockTool", "UnlockTool Ready 🔓✅", "")
@app.route('/unlocktool/verify')
def verify_unlocktool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "unlocktool", "email": RESELLER_EMAIL})

@app.route('/tsmtool')
def tsmtool():
    if request.args.get('format') == 'json': return make_json("tsmtool", "Ready to be reseller for TSM Tool", ["TSM Xiaomi", "TSM MTK"])
    return get_html_page("TSM Tool", "TSM Tool Ready ⚙️✅", "")
@app.route('/tsmtool/verify')
def verify_tsmtool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "tsmtool", "email": RESELLER_EMAIL})

@app.route('/haafedk')
def haafedk():
    if request.args.get('format') == 'json': return make_json("haafedk", "Ready to be reseller for Haafedk Tools", ["Haafedk MTK", "Haafedk Samsung"])
    return get_html_page("Haafedk Tools", "Haafedk Ready 👑✅", "")
@app.route('/haafedk/verify')
def verify_haafedk(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "haafedk", "email": RESELLER_EMAIL})

@app.route('/octopus')
def octopus():
    if request.args.get('format') == 'json': return make_json("octopus", "Ready to be reseller for Octopus Box", ["Octopus LG", "Octopus Samsung", "Octopus FRP"])
    return get_html_page("Octopus Box", "Octopus Box Ready 🐙✅", "")
@app.route('/octopus/verify')
def verify_octopus(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "octopus", "email": RESELLER_EMAIL})

@app.route('/eft')
def eft():
    if request.args.get('format') == 'json': return make_json("eft", "Ready to be reseller for EFT Pro Dongle", ["EFT MTK", "EFT SPD", "EFT Qualcomm", "EFT Apple"])
    return get_html_page("EFT Pro", "EFT Pro Ready ⚡✅", "")
@app.route('/eft/verify')
def verify_eft(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "eft", "email": RESELLER_EMAIL})

@app.route('/pandora')
def pandora():
    if request.args.get('format') == 'json': return make_json("pandora", "Ready to be reseller for Pandora Box", ["Pandora MTK", "Pandora SPD", "Pandora FRP"])
    return get_html_page("Pandora Box", "Pandora Box Ready 📦✅", "")
@app.route('/pandora/verify')
def verify_pandora(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "pandora", "email": RESELLER_EMAIL})

@app.route('/z3x')
def z3x():
    if request.args.get('format') == 'json': return make_json("z3x", "Ready to be reseller for Z3X Box - Samsung Tool Pro", ["Z3X Samsung Tool Pro", "Z3X LG Tool"])
    return get_html_page("Z3X Box", "Z3X Box Ready 🔴✅", "")
@app.route('/z3x/verify')
def verify_z3x(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "z3x", "email": RESELLER_EMAIL})

# NEW 7 TOOLS
@app.route('/sigma')
def sigma():
    if request.args.get('format') == 'json': return make_json("sigma", "Ready to be reseller for Sigma Key - Sigma Plus", ["Sigma Huawei", "Sigma MTK", "Sigma Qualcomm", "Sigma FRP"])
    return get_html_page("Sigma Key", "Sigma Key Ready 🔷✅", "")
@app.route('/sigma/verify')
def verify_sigma(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "sigma", "email": RESELLER_EMAIL})

@app.route('/muslimodin')
def muslimodin():
    if request.args.get('format') == 'json': return make_json("muslimodin", "Ready to be reseller for Muslim Odin Tool", ["Muslim Odin Samsung", "Muslim Odin FRP", "Muslim Odin Flash"])
    return get_html_page("Muslim Odin", "Muslim Odin Ready 🕌✅", "")
@app.route('/muslimodin/verify')
def verify_muslimodin(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "muslimodin", "email": RESELLER_EMAIL})

@app.route('/tfttool')
def tfttool():
    if request.args.get('format') == 'json': return make_json("tfttool", "Ready to be reseller for TFT Tool - Try Tool", ["TFT MTK", "TFT Qualcomm", "TFT Xiaomi", "TFT FRP"])
    return get_html_page("TFT Tool", "TFT Tool Ready 🛠️✅", "")
@app.route('/tfttool/verify')
def verify_tfttool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "tfttool", "email": RESELLER_EMAIL})

@app.route('/skunlocker')
def skunlocker():
    if request.args.get('format') == 'json': return make_json("skunlocker", "Ready to be reseller for SK Unlocker Tool", ["SK FRP", "SK MDM", "SK Factory Reset"])
    return get_html_page("SK Unlocker", "SK Unlocker Ready 🔑✅", "")
@app.route('/skunlocker/verify')
def verify_skunlocker(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "skunlocker", "email": RESELLER_EMAIL})

@app.route('/dft')
def dft():
    if request.args.get('format') == 'json': return make_json("dft", "Ready to be reseller for DFT Android Multi Tool", ["DFT MTK", "DFT SPD", "DFT Qualcomm", "DFT Samsung"])
    return get_html_page("DFT Multi", "DFT Multi Ready 📱✅", "")
@app.route('/dft/verify')
def verify_dft(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "dft", "email": RESELLER_EMAIL})

@app.route('/services')
def services():
    if request.args.get('format') == 'json': return make_json("services", "Ready to be reseller for Services Tool - Xiaomi Services", ["Services Xiaomi Auth", "Services FRP", "Services Mi Account"])
    return get_html_page("Services Tool", "Services Tool Ready 🌐✅", "")
@app.route('/services/verify')
def verify_services(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "services", "email": RESELLER_EMAIL})

@app.route('/xiaomitool')
def xiaomitool():
    if request.args.get('format') == 'json': return make_json("xiaomitool", "Ready to be reseller for Xiaomi Tool V2 - XTM Tool", ["Xiaomi Auth", "Xiaomi FRP", "Xiaomi Flash", "Xiaomi Mi Account"])
    return get_html_page("Xiaomi Tool", "Xiaomi Tool Ready 📲✅", "")
@app.route('/xiaomitool/verify')
def verify_xiaomitool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "xiaomitool", "email": RESELLER_EMAIL})

@app.route('/activate')
@app.route('/check')
@app.route('/verify')
@app.route('/api')
def extra_routes():
    return get_html_page("API Status", "All Routes Working ✅ - 15 Tools Live")

@app.route('/api/create-activation', methods=['GET', 'POST'])
def create_activation():
    data = request.get_json() or {} if request.is_json else request.args.to_dict() if request.args else {}
    if not data:
        try: data = request.get_json(force=True) or {}
        except: data = {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '12 months')
    tool = data.get('tool', 'chimera')
    return jsonify({
        "status": "success",
        "message": f"تم استلام طلب تفعيل {tool} - {duration}",
        "email": email,
        "tool": tool,
        "note": "سيتم التفعيل يدويا - واتساب 0900287738",
        "chimera_ready": True, "unlocktool_ready": True, "tsmtool_ready": True, "haafedk_ready": True,
        "octopus_ready": True, "eft_ready": True, "pandora_ready": True, "z3x_ready": True,
        "sigma_ready": True, "muslimodin_ready": True, "tfttool_ready": True, "skunlocker_ready": True,
        "dft_ready": True, "services_ready": True, "xiaomitool_ready": True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
import os
import requests
from flask import jsonify, request

# أضف هذا الـ Route فقط بجانب الكود الحالي الخاص بواجهتك
@app.route('/api/order', methods=['POST'])
def send_order():
    data = request.json
    tool_name = data.get('toolName', 'أداة غير محددة')
    user_phone = data.get('phone', '0900287738') # رقمك الظاهر في الواجهة
    
    # بيانات البوت (يفضل ضبطها في Environment Variables على Render)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'ضع_توكن_البوت_هنا')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'ضع_آيدي_الشات_هنا')
    
    message = f"🚨 طلب تفعيل جديد!\n\n🛠️ الأداة: {tool_name}\n📞 الهاتف: {user_phone}"
    
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        return jsonify({"success": True, "message": "تم الإرسال بنجاح"}), 200
    else:
        return jsonify({"success": False, "error": "فشل الإرسال"}), 500
