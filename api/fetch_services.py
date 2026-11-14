from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        username = os.environ.get('IMEI_UNLOCK_USERNAME')
        api_key = os.environ.get('IMEI_UNLOCK_API_KEY')
        api_url = os.environ.get('IMEI_UNLOCK_API_URL')

        if not username or not api_key or not api_url:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing env variables'}).encode('utf-8'))
            return

        payload = urllib.parse.urlencode({
            'username': username,
            'apiaccesskey': api_key
        }).encode('utf-8')

        try:
            req = urllib.request.Request(api_url, data=payload)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req) as response:
                result = response.read().decode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
