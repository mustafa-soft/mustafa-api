# ==========================================
# كود الفحص (يستقبل الرابطين لضمان العمل)
# ==========================================
@app.get("/test_lock_api")
@app.get("/api/test_lock_api")
def test_lock_api_new():
    username = os.environ.get('LOCK2UNLOCK_USERNAME')
    api_key = os.environ.get('LOCK2UNLOCK_API_KEY')
    api_url = os.environ.get('LOCK2UNLOCK_API_URL', "https://lock2unlock.in/api/index.php")

    if not username or not api_key:
        return {"error": "تأكد من إضافة LOCK2UNLOCK_USERNAME و LOCK2UNLOCK_API_KEY في إعدادات Vercel"}

    payload = {
        'username': username,
        'apiaccesskey': api_key,
        'action': 'imeiservicelist',
        'requestformat': 'JSON'
    }

    try:
        response = requests.post(api_url, data=payload, timeout=30)
        
        if response.status_code != 200:
            return {
                "status": "error",
                "http_code": response.status_code,
                "provider_says": response.text[:300],
                "solution": "يجب إزالة قيد الـ IP من موقع lock2unlock.in أو التأكد من صحة المفتاح"
            }
            
        return response.json()
        
    except Exception as e:
        return {"error": f"فشل الاتصال: {str(e)}"}
