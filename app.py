from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# بيانات الموزع
RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa88105@gmail.com"

def get_html_page(title, status_text, extra_content=""):
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Mustafa Soft</title>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: #0a0e1a; color: #fff; font-family: 'Cairo', sans-serif; min-height: 100vh; display: flex; justify-content: center; align-items: center; }}
            .container {{ text-align: center; padding: 20px; }}
            h1 {{ color: #00ff88; margin-bottom: 10px; }}
            p {{ color: #8a99ad; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <p>{status_text}</p>
            {extra_content}
        </div>
    </body>
    </html>
    """

@app.route('/')
def home():
    return get_html_page("Mustafa Soft API", "API is Running Successfully ✅")

# --- مسار استقبال الطلبات وإرسالها إلى تليجرام ---
@app.route('/api/order', methods=['POST'])
def send_order():
    data = request.json or {}
    tool_name = data.get('toolName', 'أداة غير محددة')
    user_phone = data.get('phone', '0900287738')
    
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    message = f"🚨 طلب تفعيل جديد!\n\n🛠️ الأداة: {tool_name}\n📞 الهاتف: {user_phone}"
    
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    
    try:
        response = requests.post(telegram_url, json=payload)
        if response.status_code == 200:
            return jsonify({"success": True, "message": "تم الإرسال بنجاح"}), 200
        else:
            return jsonify({"success": False, "error": response.text}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
