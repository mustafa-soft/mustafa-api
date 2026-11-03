    try:
        target_url = f"{api_url.strip().rstrip('/')}/account/info"
        response = requests.get(target_url, headers=headers)
        
        # محاولة قراءة الـ JSON، وإذا فشلت يتم إرجاع النص الخام
        try:
            res_data = response.json()
        except Exception:
            res_data = response.text
            
        return jsonify({
            "status_code": response.status_code,
            "response_data": res_data
        }), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
