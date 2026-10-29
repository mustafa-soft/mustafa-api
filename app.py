from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafaopen88@gmail.com"

GSM_API_KEY = os.environ.get("GSM_API_KEY", "").strip()
GSM_API_URL = os.environ.get("GSM_API_URL", "https://api2-gsm.elbroos.com/").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "9140932484:AAGY4OtmC6cDS3yd6kjvt7t6ZvkkEfr1lKo").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8142874050").strip()

def send_telegram(tool, email, duration, auto_ok):
    status = "✅ أوتوماتيك Elbroos" if auto_ok else "⚠️ يدوي"
    msg = f"🔔 طلب جديد - Mustafa Soft\n\n🛠️ {tool}\n⏱️ {duration}\n📧 {email}\n🤖 {status}\n\nBot @mustafa_soft_249_bot | ID {TELEGRAM_CHAT_ID}"
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", params={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=15)
        return True, r.json()
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    return f"<h1>Mustafa Soft API ✅</h1><p>{RESELLER_EMAIL}</p>"

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
    elbroos_resp = None
    if GSM_API_KEY:
        headers = {"Authorization": f"Bearer {GSM_API_KEY}", "X-API-KEY": GSM_API_KEY, "Content-Type": "application/json"}
        payload = {"email": email, "tool": tool, "duration": duration, "api_key": GSM_API_KEY, "key": GSM_API_KEY, "login": RESELLER_EMAIL, "reseller": RESELLER_NAME, "reseller_email": RESELLER_EMAIL}
        for ep in ["/api/activation","/api/place_order","/api/create-order","/api/order","/api/v1/order","/api/v1/activation","/"]:
            try:
                url = GSM_API_URL.rstrip('/') + ep
                r = requests.post(url, json=payload, headers=headers, timeout=20)
                if r.status_code in [200,201]:
                    try: elbroos_resp = r.json()
                    except: elbroos_resp = {"raw": r.text[:1000]}
                    auto_ok = True
                    break
                else:
                    elbroos_resp = {"status": r.status_code, "endpoint": ep, "body": r.text[:1000]}
            except Exception as e:
                elbroos_resp = {"error": str(e), "endpoint": ep}
                continue
    ok, tg = send_telegram(tool, email, duration, auto_ok)
    return jsonify({
        "status":"success",
        "auto":auto_ok,
        "message": f"تم استلام طلب تفعيل {tool} - {duration}" + (" - أوتوماتيك ✅" if auto_ok else " - يدوي ⚠️"),
        "email": email,
        "tool": tool,
        "duration": duration,
        "elbroos_response": elbroos_resp,
        "notified": ok,
        "telegram": tg,
        "bot":"@mustafa_soft_249_bot",
        "chat_id": TELEGRAM_CHAT_ID,
        "reseller_email": RESELLER_EMAIL,
        "gsm_api": GSM_API_URL,
        "gsm_key_set": bool(GSM_API_KEY)
    })

@app.route('/api/test-bot')
def test_bot():
    ok, tg = send_telegram("test", "test@gmail.com", "اختبار البوت", False)
    return jsonify({
        "success": ok,
        "bot":"@mustafa_soft_249_bot",
        "chat_id": TELEGRAM_CHAT_ID,
        "telegram_response": tg,
        "reseller_email": RESELLER_EMAIL,
        "gsm_key_set": bool(GSM_API_KEY),
        "bot_token_preview": TELEGRAM_BOT_TOKEN[:15]+"..." if TELEGRAM_BOT_TOKEN else None,
        "bot_token_len": len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
