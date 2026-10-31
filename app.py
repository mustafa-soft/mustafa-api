import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# إعدادات التوصيل (يمكنك استبدالها ببياناتك الفعلية أو متغيرات البيئة)
ELBROOS_API_URL = "https://api2-gsm.elbroos.com/api"  # رابط API الخاص بـ Elbroos
ELBROOS_TOKEN = "ضع_توكن_الوصول_هنا"  # Bearer Token الخاص بك

TELEGRAM_BOT_TOKEN = "ضع_توكن_البوت_هنا"
TELEGRAM_CHAT_ID = "ضع_رقم_الـ_chat_id_هنا"


# دالة مساعدة لإرسال إشعارات تيليجرام
def send_telegram_notification(message):
  try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=5)
  except Exception as e:
    print(f"Telegram Error: {e}")


# الصفحة الرئيسية للتأكد من عمل الـ API
@app.route("/")
def home():
  return jsonify({
      "status": "success",
      "message": "API is running successfully!",
      "author": "Mustafa",
  })


# مسار جلب قائمة الخدمات والأسعار من مزود الخدمة الخارجي (Elbroos مثلاً)
@app.route("/api/services", methods=["GET"])
def get_services():
  headers = {"Authorization": f"Bearer {ELBROOS_TOKEN}"}
  try:
    # جلب الخدمات من مزود الخدمة الخارجي
    response = requests.get(
        f"{ELBROOS_API_URL}/services", headers=headers, timeout=10
    )
    if response.status_code == 200:
      return jsonify(
          {"status": "success", "data": response.json()}
      )
    else:
      return (
          jsonify({
              "status": "error",
              "message": "Failed to fetch services from provider",
          }),
          response.status_code,
      )
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


# مسار إرسال طلب جديد وتحويله لمزود الخدمة + إشعار تيليجرام
@app.route("/api/order", methods=["POST"])
def create_order():
  data = request.get_json()

  service_id = data.get("service_id")
  imei_or_sn = data.get("imei")

  if not service_id or not imei_or_sn:
    return (
        jsonify({"status": "error", "message": "Missing service_id or imei"}),
        400,
    )

  # تجهيز الطلب لإرساله إلى مزود الخدمة (Elbroos)
  headers = {"Authorization": f"Bearer {ELBROOS_TOKEN}"}
  payload = {"service_id": service_id, "imei": imei_or_sn}

  try:
    response = requests.post(
        f"{ELBROOS_API_URL}/addOrder", json=payload, headers=headers, timeout=10
    )
    result = response.json()

    # إرسال إشعار فوري عبر تيليجرام بتفاصيل الطلب الجديد
    notification_msg = (
        f"🚨 **طلب جديد تم استلامه!**\n\n"
        f"📱 **رقم IMEI/SN:** `{imei_or_sn}`\n"
        f"⚙️ **رقم الخدمة:** `{service_id}`\n"
        f"📊 **الحالة:** تم الإرسال بنجاح"
    )
    send_telegram_notification(notification_msg)

    return jsonify({"status": "success", "provider_response": result})

  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
