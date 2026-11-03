import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# مسار أساسي للتأكد من أن السيرفر يعمل
@app.route('/')
def home():
    return "Server is running successfully!"

# مسار اختبار الاتصال بـ GSMGenesis
@app.route('/test-gsm', methods=['GET'])
def test_gsm_connection():
    api_url = os.getenv('GSMGENESIS_API_URL')
    api_key = os.getenv('GSMGENESIS_API_KEY')
    
    if not api_url or not api_key:
        return jsonify({"error": "API URL or API Key is missing in environment variables"}), 500
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # إزالة أي شرطة مائلة زائدة من نهاية الرابط ثم إضافة المسار المطلوب بدقة
        base_url = api_url.strip().rstrip('/')
        target_url = f"{base_url}/account/info"
        
        response = requests.get(target_url, headers=headers)
        
        return jsonify({
            "status_code": response.status_code,
            "response_data": response.json() if response.content else "No content"
        }), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
