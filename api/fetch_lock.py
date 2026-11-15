from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # جلب البيانات بناءً على الأسماء التي كتبتها في Vercel
        username = os.environ.get('LOCK2UNLOCK_USERNAME')
        api_key = os.environ.get('LOCK2UNLOCK_API_KEY')
        api_url = os.environ.get('NEW_API_URL', "https://lock2unlock.in/public")

        if not username or not api_key or not api_url:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing env vars in Vercel", "user": username, "key": api_key, "url": api_url}).encode('utf-8'))
            return

        payload = {
            'username': username,
            'apiaccesskey': api_key,
            'action': 'imeiservicelist',
            'requestformat': 'JSON'
        }

        try:
            response = requests.post(api_url, data=payload, timeout=30)
            
            if response.status_code != 200:
                self.send_response(response.status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "http_code": response.status_code,
                    "provider_says": response.text[:300],
                    "solution": "Remove IP restriction or check the URL/Auth"
                }).encode('utf-8'))
                return

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response.json()).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
