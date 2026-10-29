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
