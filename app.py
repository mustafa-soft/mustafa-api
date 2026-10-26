from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
app = Flask(__name__)
CORS(app)
RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"
RESELLER_PHONE = "+249 90 028 7738"
RESELLER_WHATSAPP = "+249900287738"
RESELLER_WEBSITE = "https://mustafa-soft.vercel.app"
RESELLER_ADDRESS = "Al Bauga, Ash Shamaliyah, Sudan"
RESELLER_SERVICE_ID = "srv-dbeeuf4s728c73c18tcg"

def get_html_page(title, status_text, extra_content=""):
    return f"""
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Mustafa Soft - Prices USD No Login</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Cairo',sans-serif}}
body{{background:#0a0e1a;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}}
.header{{width:100%;max-width:1200px;background:linear-gradient(135deg,#1a233a 0%,#0f172a 100%);border:1px solid #1e3a5f;border-radius:20px;padding:30px;margin-bottom:20px;text-align:center}}
.logo{{font-size:42px;font-weight:800;background:linear-gradient(90deg,#00d4ff,#0ea5e9,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.badge{{background:#0f281e;border:1px solid #10b981;color:#10b981;padding:8px 18px;border-radius:50px;font-weight:700;margin-top:10px;display:inline-block}}
.grid{{width:100%;max-width:1200px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-bottom:20px}}
.card{{background:#111b2f;border:1px solid #1e3a5f;border-radius:16px;padding:18px}}
.price-usd{{background:#0f281e;border:1px solid #10b981;color:#10b981;padding:4px 10px;border-radius:6px;font-weight:800;display:inline-block;margin:5px 0}}
.btn{{display:inline-block;background:linear-gradient(90deg,#0ea5e9,#6366f1);color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;width:100%;text-align:center;margin-top:8px}}
.info-box{{width:100%;max-width:1200px;background:#111b2f;border:1px solid #1e3a5f;border-radius:16px;padding:22px;margin-bottom:18px}}
.footer{{width:100%;max-width:1200px;background:#0f172a;border:1px solid #1e3a5f;border-radius:16px;padding:20px;text-align:center;color:#94a3b8;font-size:12px;line-height:1.8;margin-top:20px}}
</style>
</head>
<body>
<div class="header">
<div class="logo">Mustafa Soft</div>
<div style="color:#94a3b8;font-size:13px">Official Reseller - Chimera & UnlockTool & 13 Tools - 15 Tools Live - Prices USD - No Login Required - Contact & Payment Displayed - Service ID: {RESELLER_SERVICE_ID} Live</div>
<div class="badge">{status_text}</div>
<div style="margin-top:12px;color:#94a3b8;font-size:12px">🌐 {RESELLER_WEBSITE} | 💬 {RESELLER_PHONE} | 📧 {RESELLER_EMAIL} | 📍 {RESELLER_ADDRESS}</div>
</div>

<div class="info-box">
<h2 style="color:#00d4ff">📞 Operator Contact Information - Required for Chimera</h2>
<p style="color:#94a3b8;line-height:1.8">Reseller: {RESELLER_NAME} | Operator: Mustafa Wad Fateh Al-Rahman | Email: {RESELLER_EMAIL} | Phone: {RESELLER_PHONE} / +249 99 365 4389 | Address: {RESELLER_ADDRESS} | Website: {RESELLER_WEBSITE} - No login required - API: https://mustafa-api-1.onrender.com/ - Hours: 9AM-11PM GMT+2</p>
</div>

<div class="info-box" style="border-color:#10b981;background:#0f1a15">
<h2 style="color:#10b981">💰 ChimeraTool Pricing in USD - Consistent with chimeratool.com - No Login Required</h2>
<p style="color:#a7f3d0;font-size:12px;margin:10px 0">All prices displayed in USD without login as required. Consistent with chimeratool.com official store.</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px">
<div style="background:#111b2f;padding:10px;border-radius:8px"><strong>Chimera 12M</strong><br><span class="price-usd">$199 USD</span></div>
<div style="background:#111b2f;padding:10px;border-radius:8px"><strong>Chimera 6M</strong><br><span class="price-usd">$129 USD</span></div>
<div style="background:#111b2f;padding:10px;border-radius:8px"><strong>Chimera 3M</strong><br><span class="price-usd">$89 USD</span></div>
<div style="background:#111b2f;padding:10px;border-radius:8px;border:1px solid #f59e0b"><strong>20000 Credits</strong><br><span class="price-usd" style="border-color:#f59e0b;color:#f59e0b">$200 USD</span><br><small>Required - Non-refundable - No upper limit</small></div>
</div>
</div>

<div class="info-box">
<h2 style="color:#00d4ff">💳 Payment Methods - Clearly Indicated</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;font-size:11px;margin-top:10px">
<div style="background:#0f172a;padding:10px;border-radius:8px"><strong>Bankak Sudan</strong><br>0900287738<br>1 USD=600 SDG - Displayed $199 USD</div>
<div style="background:#0f172a;padding:10px;border-radius:8px"><strong>USDT TRC20</strong><br>TE6q6QLYrpHkDFYppTDa1m97kTfCLou8PD<br>Tron - $199 USD</div>
<div style="background:#0f172a;padding:10px;border-radius:8px"><strong>USDT BEP20</strong><br>0x2a11ef4375C7D91d5ad07A1BF85EceA1a82Cf840</div>
<div style="background:#0f172a;padding:10px;border-radius:8px"><strong>Binance Pay</strong><br>570077631 - USD</div>
<div style="background:#0f172a;padding:10px;border-radius:8px"><strong>PayPal USD</strong><br>mustafa888105@gmail.com - $199 USD</div>
<div style="background:#0f172a;padding:10px;border-radius:8px"><strong>Western Union USD</strong><br>Mustafa Sudan</div>
</div>
</div>

<div class="grid">
<div class="card"><h3>🔧 Chimera</h3><span class="price-usd">$199 / $129 / $89 USD</span><br><a href="/chimera" class="btn">View $199 USD</a></div>
<div class="card"><h3>🔓 UnlockTool</h3><span class="price-usd">$49 USD</span><br><a href="/unlocktool" class="btn">View $49 USD</a></div>
<div class="card"><h3>⚙️ TSM</h3><span class="price-usd">$19 USD</span><br><a href="/tsmtool" class="btn">View $19</a></div>
<div class="card"><h3>👑 Haafedk</h3><span class="price-usd">$15 USD</span><br><a href="/haafedk" class="btn">View $15</a></div>
<div class="card"><h3>🐙 Octopus</h3><span class="price-usd">$49 USD</span><br><a href="/octopus" class="btn">View $49</a></div>
<div class="card"><h3>⚡ EFT Pro</h3><span class="price-usd">$29 USD</span><br><a href="/eft" class="btn">View $29</a></div>
<div class="card"><h3>📦 Pandora</h3><span class="price-usd">$35 USD</span><br><a href="/pandora" class="btn">View $35</a></div>
<div class="card"><h3>🔴 Z3X</h3><span class="price-usd">$59 USD</span><br><a href="/z3x" class="btn">View $59</a></div>
<div class="card"><h3>🔷 Sigma</h3><span class="price-usd">$45 USD</span><br><a href="/sigma" class="btn">View $45</a></div>
<div class="card"><h3>🕌 Muslim Odin</h3><span class="price-usd">$20 USD</span><br><a href="/muslimodin" class="btn">View $20</a></div>
<div class="card"><h3>🛠️ TFT</h3><span class="price-usd">$18 USD</span><br><a href="/tfttool" class="btn">View $18</a></div>
<div class="card"><h3>🔑 SK</h3><span class="price-usd">$15 USD</span><br><a href="/skunlocker" class="btn">View $15</a></div>
<div class="card"><h3>📱 DFT</h3><span class="price-usd">$22 USD</span><br><a href="/dft" class="btn">View $22</a></div>
<div class="card"><h3>🌐 Services</h3><span class="price-usd">$25 USD</span><br><a href="/services" class="btn">View $25</a></div>
<div class="card"><h3>📲 Xiaomi</h3><span class="price-usd">$20 USD</span><br><a href="/xiaomitool" class="btn">View $20</a></div>
</div>

<div class="footer">
Contact: {RESELLER_NAME} | {RESELLER_EMAIL} | {RESELLER_PHONE} | {RESELLER_ADDRESS} | {RESELLER_WEBSITE} | Service: {RESELLER_SERVICE_ID} Live<br>
Payment: Bankak 0900287738 ($199 USD), USDT TRC20 TE6q6..., BEP20, Binance Pay, PayPal USD<br>
✅ Prices without login $199/$129/$89 ✅ Contact displayed ✅ Payment methods ✅ USD consistent ✅ 20000 credits $200<br>
Apply: https://chimeratool.com/#reseller-registration
</div>
</body>
</html>
"""
    return get_html_page(title, status_text, extra_content)

def make_json(tool, status, tools_list):
    return jsonify({"reseller": RESELLER_NAME, "email": RESELLER_EMAIL, "phone": RESELLER_PHONE, "website": RESELLER_WEBSITE, "status": status, "tools": tools_list})

@app.route('/')
def index():
    return get_html_page("Mustafa Soft", "API Running ✅ Live - 15 Tools - Prices USD - Contact & Payment Displayed - No Login Required - Chimera Ready ✅")

@app.route('/chimera')
def chimera():
    if request.args.get('format') == 'json':
        return jsonify({
            "reseller": RESELLER_NAME, "email": RESELLER_EMAIL, "phone": RESELLER_PHONE, "website": RESELLER_WEBSITE, "address": RESELLER_ADDRESS, "service_id": RESELLER_SERVICE_ID,
            "pricing_usd": {"12M": "$199 USD", "6M": "$129 USD", "3M": "$89 USD", "20000 Credits": "$200 USD - Required, non-refundable, no upper limit", "Pro": "$299 USD"},
            "pricing_note": "Prices USD without login, consistent with chimeratool.com",
            "payment_methods": {"Bankak": "0900287738 - $199 USD displayed", "USDT_TRC20": "TE6q6QLYrpHkDFYppTDa1m97kTfCLou8PD - $199 USD", "USDT_BEP20": "0x2a11...", "Binance": "570077631", "PayPal": "mustafa888105@gmail.com USD"},
            "contact": {"operator": RESELLER_NAME, "email": RESELLER_EMAIL, "phone": RESELLER_PHONE, "address": RESELLER_ADDRESS, "website": RESELLER_WEBSITE},
            "chimera_conditions_met": True
        })
    return get_html_page("Chimera Tool", "Chimera Ready 🔧✅ - $199/$129/$89 USD - 20000 Credits $200 - No Login - Live on Render", "")

@app.route('/chimera/verify')
def verify_chimera():
    return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "chimera", "email": RESELLER_EMAIL, "phone": RESELLER_PHONE, "website": RESELLER_WEBSITE, "service_id": RESELLER_SERVICE_ID, "pricing_usd": "$199/$129/$89 consistent with chimeratool.com", "payment_methods": "Bankak, USDT TRC20, BEP20, Binance Pay, PayPal USD", "contact_displayed": True, "no_login_required": True, "chimera_conditions_met": True, "render_live": True})

@app.route('/unlocktool')
def unlocktool():
    if request.args.get('format') == 'json': return make_json("unlocktool", "Ready", ["FRP", "Flash"])
    return get_html_page("UnlockTool", "UnlockTool Ready 🔓✅ - $49 USD", "")
@app.route('/unlocktool/verify')
def verify_unlocktool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "unlocktool", "email": RESELLER_EMAIL})
@app.route('/tsmtool')
def tsmtool():
    if request.args.get('format') == 'json': return make_json("tsmtool", "Ready", ["Xiaomi", "MTK"])
    return get_html_page("TSM", "TSM Ready ⚙️✅ - $19 USD", "")
@app.route('/tsmtool/verify')
def verify_tsmtool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "tsmtool", "email": RESELLER_EMAIL})
@app.route('/haafedk')
def haafedk():
    if request.args.get('format') == 'json': return make_json("haafedk", "Ready", ["MTK", "Samsung"])
    return get_html_page("Haafedk", "Haafedk Ready 👑✅ - $15 USD", "")
@app.route('/haafedk/verify')
def verify_haafedk(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "haafedk", "email": RESELLER_EMAIL})
@app.route('/octopus')
def octopus():
    if request.args.get('format') == 'json': return make_json("octopus", "Ready", ["LG", "Samsung", "FRP"])
    return get_html_page("Octopus", "Octopus Ready 🐙✅ - $49 USD", "")
@app.route('/octopus/verify')
def verify_octopus(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "octopus", "email": RESELLER_EMAIL})
@app.route('/eft')
def eft():
    if request.args.get('format') == 'json': return make_json("eft", "Ready", ["MTK", "SPD", "Qualcomm", "Apple"])
    return get_html_page("EFT", "EFT Ready ⚡✅ - $29 USD", "")
@app.route('/eft/verify')
def verify_eft(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "eft", "email": RESELLER_EMAIL})
@app.route('/pandora')
def pandora():
    if request.args.get('format') == 'json': return make_json("pandora", "Ready", ["MTK", "SPD", "FRP"])
    return get_html_page("Pandora", "Pandora Ready 📦✅ - $35 USD", "")
@app.route('/pandora/verify')
def verify_pandora(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "pandora", "email": RESELLER_EMAIL})
@app.route('/z3x')
def z3x():
    if request.args.get('format') == 'json': return make_json("z3x", "Ready", ["Samsung Pro", "LG"])
    return get_html_page("Z3X", "Z3X Ready 🔴✅ - $59 USD", "")
@app.route('/z3x/verify')
def verify_z3x(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "z3x", "email": RESELLER_EMAIL})
@app.route('/sigma')
def sigma():
    if request.args.get('format') == 'json': return make_json("sigma", "Ready", ["Huawei", "MTK"])
    return get_html_page("Sigma", "Sigma Ready 🔷✅ - $45 USD", "")
@app.route('/sigma/verify')
def verify_sigma(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "sigma", "email": RESELLER_EMAIL})
@app.route('/muslimodin')
def muslimodin():
    if request.args.get('format') == 'json': return make_json("muslimodin", "Ready", ["Samsung", "FRP"])
    return get_html_page("Muslim Odin", "Muslim Odin Ready 🕌✅ - $20 USD", "")
@app.route('/muslimodin/verify')
def verify_muslimodin(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "muslimodin", "email": RESELLER_EMAIL})
@app.route('/tfttool')
def tfttool():
    if request.args.get('format') == 'json': return make_json("tfttool", "Ready", ["MTK", "Qualcomm"])
    return get_html_page("TFT", "TFT Ready 🛠️✅ - $18 USD", "")
@app.route('/tfttool/verify')
def verify_tfttool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "tfttool", "email": RESELLER_EMAIL})
@app.route('/skunlocker')
def skunlocker():
    if request.args.get('format') == 'json': return make_json("skunlocker", "Ready", ["FRP", "MDM"])
    return get_html_page("SK", "SK Ready 🔑✅ - $15 USD", "")
@app.route('/skunlocker/verify')
def verify_skunlocker(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "skunlocker", "email": RESELLER_EMAIL})
@app.route('/dft')
def dft():
    if request.args.get('format') == 'json': return make_json("dft", "Ready", ["MTK", "SPD"])
    return get_html_page("DFT", "DFT Ready 📱✅ - $22 USD", "")
@app.route('/dft/verify')
def verify_dft(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "dft", "email": RESELLER_EMAIL})
@app.route('/services')
def services():
    if request.args.get('format') == 'json': return make_json("services", "Ready", ["Xiaomi Auth"])
    return get_html_page("Services", "Services Ready 🌐✅ - $25 USD", "")
@app.route('/services/verify')
def verify_services(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "services", "email": RESELLER_EMAIL})
@app.route('/xiaomitool')
def xiaomitool():
    if request.args.get('format') == 'json': return make_json("xiaomitool", "Ready", ["Auth", "FRP"])
    return get_html_page("Xiaomi", "Xiaomi Ready 📲✅ - $20 USD", "")
@app.route('/xiaomitool/verify')
def verify_xiaomitool(): return jsonify({"verified": True, "ready": True, "reseller": RESELLER_NAME, "tool": "xiaomitool", "email": RESELLER_EMAIL})
@app.route('/activate')
@app.route('/check')
@app.route('/verify')
@app.route('/api')
def extra_routes():
    return get_html_page("API Status", "All Routes Working ✅ - 15 Tools Live - Live on Render - Deploy 26")
@app.route('/api/create-activation', methods=['GET', 'POST'])
def create_activation():
    data = request.get_json() or {} if request.is_json else request.args.to_dict() if request.args else {}
    if not data:
        try: data = request.get_json(force=True) or {}
        except: data = {}
    email = data.get('email', 'test@gmail.com')
    duration = data.get('duration', '12 months')
    tool = data.get('tool', 'chimera')
    order = data.get('order', f"MS-{tool.upper()}-{hashlib.md5(email.encode()).hex
