from flask import Flask, jsonify, request

app = Flask(__name__)


# الصفحة الرئيسية للتأكد من عمل الـ API
@app.route("/")
def home():
  return jsonify({
      "status": "success",
      "message": "API is running successfully!",
      "author": "Mustafa",
  })


# مسار جلب قائمة الخدمات والأسعار
@app.route("/api/services", methods=["GET"])
def get_services():
  # يمكنك هنا إضافة استدعاء API الخاص بـ Elbroos أو جلب البيانات
  sample_services = [
      {"id": 1, "service_name": "IMEI Unlock - iPhone", "price": "10.0$"},
      {"id": 2, "service_name": "FRP Bypass Service", "price": "5.0$"},
  ]
  return jsonify({"status": "success", "services": sample_services})


# مسار إرسال طلب جديد (مثل طلب فحص أو فتح قفل)
@app.route("/api/order", methods=["POST"])
def create_order():
  data = request.get_json()

  # استقبال البيانات المرسلة من الواجهة الأمامية (Vercel) أو البوت
  service_id = data.get("service_id")
  imei_or_sn = data.get("imei")

  if not service_id or not imei_or_sn:
    return (
        jsonify({"status": "error", "message": "Missing service_id or imei"}),
        400,
    )

  # هنا يتم وضع كود الاتصال بسيرفر مزود الخدمة (مثل Elbroos)
  # محاكاة لنجاح الطلب:
  order_response = {
      "status": "success",
      "order_id": "123456",
      "service_id": service_id,
      "imei": imei_or_sn,
      "message": "Order submitted successfully",
  }

  return jsonify(order_response)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
