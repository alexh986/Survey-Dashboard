from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import ssl
import os

# Fix SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context

TYPEFORM_TOKEN = os.environ.get('TYPEFORM_TOKEN')
TYPEFORM_FORM_ID = os.environ.get('TYPEFORM_FORM_ID', 'LNhHpdkI')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            url = f'https://api.typeform.com/forms/{TYPEFORM_FORM_ID}/responses?page_size=1000'
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Bearer {TYPEFORM_TOKEN}')

            with urllib.request.urlopen(req) as response:
                data = response.read()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
