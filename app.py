from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
  return jsonify({
      "status": "success",
      "message": "API is running successfully!",
      "author": "Mustafa",
  })


@app.route("/api/services", methods=["GET"])
def get_services():
  # قائمة تجريبية لاختبار ظهور البيانات بنجاح
  sample_services = [
      {"id": 1, "service_name": "IMEI Unlock - iPhone", "price": "10.0$"},
      {"id": 2, "service_name": "FRP Bypass Service", "price": "5.0$"},
  ]
  return jsonify({"status": "success", "services": sample_services})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
