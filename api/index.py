"""
Vercel Python 함수 - 기본 테스트
"""

from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # CORS 헤더 설정
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 기본 응답
        response = {
            "status": "success",
            "message": "Basic Vercel Python handler working!",
            "timestamp": datetime.now().isoformat(),
            "path": self.path
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_OPTIONS(self):
        # CORS preflight 처리
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()