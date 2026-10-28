@app.route('/test-gsm', methods=['GET'])
def test_gsm():
    try:
        headers = {
            "Authorization": f"Bearer {GSM_API_KEY}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(GSM_API_URL, headers=headers, timeout=15)
        
        try:
            res_data = response.json()
        except:
            res_data = response.text

        return jsonify({
            "status": "success",
            "gsm_status_code": response.status_code,
            "response_data": res_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
