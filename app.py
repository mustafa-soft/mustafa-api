@app.route('/test-gsm', methods=['GET'])
def test_gsm():
    try:
        target_url = f"{GSM_API_URL}?key={GSM_API_KEY}"
        response = requests.get(target_url, timeout=15)
        
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
