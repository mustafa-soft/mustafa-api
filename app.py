from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"

GSM_API_KEY = os.environ.get("GSM_API_KEY", "")
GSM_API_URL = os.environ.get("GSM_API_URL", "https://api2-gsm.elbroos.com/")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "9140932484:AAGY4OtmC6cDS3yd6kjvt7t6ZvkkEfr1lKo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8142874050")

def send_telegram(tool, email, duration, auto_ok):
    msg = f"🔔 طلب جديد - Mustafa Soft\n\n🛠️ {tool}\n⏱️ {duration}\n📧 {email}\n🤖 {'✅ أوتوماتيك' if auto_ok else '⚠️ يدوي'}\nBot @mustafa_soft_249_bot | ID {TELEGRAM_CHAT_ID}"
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", params={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=12)
        return True, r.json()
    except Exception as e:
        return False, str(e)

def get_html_page(title, status_text):
    return f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} - Mustafa Soft</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet"><style>*{{margin:0;padding:0;box-sizing:border-box;font-family:'Cairo',sans-serif}}body{{background:#0a0e1a;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}}.header{{width:100%;max-width:1200px;background:linear-gradient(135deg,#1a233a 0%,#0f172a 100%);border:1px solid #1e3a5f;border-radius:20px;padding:30px;margin-bottom:20px;text-align:center}}.logo{{font-size:42px;font-weight:800;background:linear-gradient(90deg,#00d4ff,#0ea5e9,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}}.subtitle{{color:#94a3b8;font-size:13px;margin-bottom:20px}}.status-badge{{display:inline-flex;align-items:center;gap:8px;background:#0f281e;border:1px solid #10b981;color:#10b981;padding:8px 18px;border-radius:50px;font-weight:700;font-size:14px}}.dot{{width:10px;height:10px;background:#10b981;border-radius:50%}}.grid{{width:100%;max-width:1200px;display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-bottom:20px}}.card{{background:#111b2f;border:1px solid #1e3a5f;border-radius:16px;padding:20px}}.card h3{{color:#e2e8f0;margin-bottom:8px;font-size:15px}}.card p{{color:#94a3b8;font-size:12px;margin-bottom:12px}}.btn{{display:inline-block;background:linear-gradient(90deg,#0ea5e9,#6366f1);color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;font-size:12px;width:100%;text-align:center}}.btn-outline{{background:transparent;border:1px solid #1e3a5f;color:#94a3b8}}</style></head><body><div class="header"><div class="logo">Mustafa Soft</div><div class="subtitle">Chimera & UnlockTool & TSM & Haafedk & Octopus & EFT & Pandora & Z3X & Sigma & Muslim Odin & TFT & SK Unlocker & DFT & Services & Xiaomi Tool - Reseller API<br>15 Tools Live - mustafa-soft</div><div class="status-badge"><span class="dot"></span> {status_text}</div><div style="margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap"><a href="https://mustafa-soft.vercel.app/" class="btn" style="width:auto;padding:12px 25px">🌐 الموقع الرسمي</a><a href="https://wa.me/249900287738" class="btn btn-outline" style="width:auto;padding:12px 25px">💬 واتساب: 0900287738</a></div></div><div class="grid"><div class="card"><h3>🔧 Chimera Tool</h3><p>تفعيل رسمي - 3 / 6 / 12 شهر</p><a href="/chimera" class="btn">عرض Chimera API</a></div><div class="card"><h3>🔓 UnlockTool</h3><p>تفعيل رسمي</p><a href="/unlocktool" class="btn">عرض UnlockTool API</a></div><div class="card"><h3>⚙️ TSM Tool</h3><p>TSM Pro</p><a href="/tsmtool" class="btn">عرض TSM API</a></div><div class="card"><h3>👑 Haafedk</h3><p>هفيدك</p><a href="/haafedk" class="btn">عرض Haafedk API</a></div><div class="card"><h3>🐙 Octopus</h3><p>Octopus Box</p><a href="/octopus" class="btn" style="background:linear-gradient(90deg,#f59e0b,#ef4444)">عرض Octopus API</a></div><div class="card"><h3>⚡ EFT Pro</h3><p>EFT Dongle</p><a href="/eft" class="btn" style="background:linear-gradient(90deg,#10b981,#06b6d4)">عرض EFT API</a></div><div class="card"><h3>📦 Pandora Box</h3><p>Pandora Tool</p><a href="/pandora" class="btn" style="background:linear-gradient(90deg,#8b5cf6,#ec4899)">عرض Pandora API</a></div><div class="card"><h3>🔴 Z3X Box</h3><p>Z3X Samsung Tool Pro</p><a href="/z3x" class="btn" style="background:linear-gradient(90deg,#dc2626,#991b1b)">عرض Z3X API</a></div><div class="card"><h3>🔷 Sigma Key</h3><p>Sigma Plus</p><a href="/sigma" class="btn" style="background:linear-gradient(90deg,#2563eb,#1e40af)">عرض Sigma API</a></div><div class="card"><h3>🕌 Muslim Odin</h3><p>Muslim Odin Tool</p><a href="/muslimodin" class="btn" style="background:linear-gradient(90deg,#059669,#047857)">عرض Muslim Odin API</a></div><div class="card"><h3>🛠️ TFT Tool</h3><p>TFT Tool</p><a href="/tfttool" class="btn" style="background:linear-gradient(90deg,#ea580c,#c2410c)">عرض TFT API</a></div><div class="card"><h3>🔑 SK Unlocker</h3><p>SK Unlocker</p><a href="/skunlocker" class="btn" style="background:linear-gradient(90deg,#0891b2,#0e7490)">عرض SK API</a></div><div class="card"><h3>📱 DFT Multi</h3><p>DFT Multi</p><a href="/dft" class="btn" style="background:linear-gradient(90deg,#7c3aed,#6d28d9)">عرض DFT API</a></div><div class="card"><h3>🌐 Services Tool</h3><p>Services Tool</p><a href="/services" class="btn" style="background:linear-gradient(90deg,#db2777,#be185d)">عرض Services API</a></div><div class="card"><h3>📲 Xiaomi Tool</h3><p>Xiaomi Tool</p><a href="/xiaomitool" class="btn" style="background:linear-gradient(90deg,#f59e0b,#d97706)">عرض Xiaomi API</a></div></div></body></html>"""

def make_json(t): return jsonify({"tool":t,"status":"Ready","reseller":RESELLER_NAME,"bot":"@mustafa_soft_249_bot","chat_id":TELEGRAM_CHAT_ID,"auto":bool(GSM_API_KEY)})
def verify_resp(t): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":t,"email":RESELLER_EMAIL,"bot":"@mustafa_soft_249_bot","chat_id":TELEGRAM_CHAT_ID,"auto":bool(GSM_API_KEY)})

@app.route('/')
def home(): return get_html_page("Mustafa Soft", "API is Running ✅ - 15 Tools - mustafa-soft")
@app.route('/chimera')
def chimera(): return get_html_page("Chimera Tool","Chimera Tool Ready 🔧✅") if request.args.get('format')!='json' else make_json("chimera")
@app.route('/chimera/verify')
def v_c(): return verify_resp("chimera")
@app.route('/unlocktool')
def ut(): return get_html_page("UnlockTool","UnlockTool Ready 🔓✅") if request.args.get('format')!='json' else make_json("unlocktool")
@app.route('/unlocktool/verify')
def v_u(): return verify_resp("unlocktool")
@app.route('/tsmtool')
def tsm(): return get_html_page("TSM Tool","TSM Tool Ready ⚙️✅")
@app.route('/tsmtool/verify')
def v_tsm(): return verify_resp("tsmtool")
@app.route('/haafedk')
def ha(): return get_html_page("Haafedk Tools","Haafedk Ready 👑✅")
@app.route('/haafedk/verify')
def v_ha(): return verify_resp("haafedk")
@app.route('/octopus')
def oc(): return get_html_page("Octopus Box","Octopus Box Ready 🐙✅")
@app.route('/octopus/verify')
def v_oc(): return verify_resp("octopus")
@app.route('/eft')
def eft(): return get_html_page("EFT Pro","EFT Pro Ready ⚡✅")
@app.route('/eft/verify')
def v_eft(): return verify_resp("eft")
@app.route('/pandora')
def pa(): return get_html_page("Pandora Box","Pandora Box Ready 📦✅")
@app.route('/pandora/verify')
def v_pa(): return verify_resp("pandora")
@app.route('/z3x')
def z3(): return get_html_page("Z3X Box","Z3X Box Ready 🔴✅")
@app.route('/z3x/verify')
def v_z3(): return verify_resp("z3x")
@app.route('/sigma')
def sig(): return get_html_page("Sigma Key","Sigma Key Ready 🔷✅")
@app.route('/sigma/verify')
def v_sig(): return verify_resp("sigma")
@app.route('/muslimodin')
def mo(): return get_html_page("Muslim Odin","Muslim Odin Ready 🕌✅")
@app.route('/muslimodin/verify')
def v_mo(): return verify_resp("muslimodin")
@app.route('/tfttool')
def tft(): return get_html_page("TFT Tool","TFT Tool Ready 🛠️✅")
@app.route('/tfttool/verify')
def v_tft(): return verify_resp("tfttool")
@app.route('/skunlocker')
def sk(): return get_html_page("SK Unlocker","SK Unlocker Ready 🔑✅")
@app.route('/skunlocker/verify')
def v_sk(): return verify_resp("skunlocker")
@app.route('/dft')
def dft(): return get_html_page("DFT Multi","DFT Multi Ready 📱✅")
@app.route('/dft/verify')
def v_dft(): return verify_resp("dft")
@app.route('/services')
def ser(): return get_html_page("Services Tool","Services Tool Ready 🌐✅")
@app.route('/services/verify')
def v_ser(): return verify_resp("services")
@app.route('/xiaomitool')
def xia(): return get_html_page("Xiaomi Tool","Xiaomi Tool Ready 📲✅")
@app.route('/xiaomitool/verify')
def v_xia(): return verify_resp("xiaomitool")
@app.route('/activate')
@app.route('/check')
@app.route('/verify')
@app.route('/api')
def extra(): return get_html_page("API Status","All Routes Working ✅ - 15 Tools Live")

@app.route('/api/create-activation', methods=['GET','POST'])
def create_activation():
    data = request.get_json() or {} if request.is_json else request.args.to_dict() if request.args else {}
    if not data:
        try: data = request.get_json(force=True) or {}
        except: data = {}
    email = data.get('email','test@gmail.com')
    duration = data.get('duration','12 months')
    tool = data.get('tool','chimera').lower()
    auto_ok = False
    elbroos_resp = {}
    if GSM_API_KEY:
        headers = {"Authorization": f"Bearer {GSM_API_KEY}", "Content-Type":"application/json"}
        payload = {"email":email,"tool":tool,"duration":duration,"api_key":GSM_API_KEY,"key":GSM_API_KEY,"login":"mustafaopen88@gmail.com","reseller":RESELLER_NAME}
        for ep in ["/api/activation","/api/place_order","/api/create-order","/api/order"]:
            url = GSM_API_URL.rstrip('/') + ep
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=12)
                if r.status_code in [200,201]:
                    try: elbroos_resp = r.json()
                    except: elbroos_resp = {"raw": r.text[:500]}
                    auto_ok = True
                    break
            except: continue
    ok, tg = send_telegram(tool, email, duration, auto_ok)
    return jsonify({"status":"success","auto":auto_ok,"message": f"تم استلام طلب تفعيل {tool} - {duration}" + (" - أوتوماتيك ✅" if auto_ok else ""),"email":email,"tool":tool,"duration":duration,"elbroos_response":elbroos_resp if auto_ok else None,"notified":ok,"telegram":tg,"bot":"@mustafa_soft_249_bot","chat_id":TELEGRAM_CHAT_ID,"chat_id_from_image":"8142874050","gsm_api":GSM_API_URL})

@app.route('/api/test-bot')
def test_bot():
    ok, tg = send_telegram("test", "test@gmail.com", "اختبار البوت", False)
    return jsonify({"success":ok,"bot":"@mustafa_soft_249_bot","chat_id":TELEGRAM_CHAT_ID,"chat_id_from_image":"8142874050","telegram_response":tg,"message":"لو success true معناها جاتك رسالة في البوت @mustafa_soft_249_bot"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
