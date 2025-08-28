"""
Vercel용 바이낸스 베이시스 API
"""

import json
from datetime import datetime
from urllib.parse import urlparse
from .binance_simple import get_basis_data

def handler(request, context=None):
    """Vercel 서버리스 함수 핸들러"""
    
    # CORS 헤더
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    try:
        # 요청 메서드 확인
        method = getattr(request, 'method', 'GET')
        
        # OPTIONS 요청 처리 (CORS preflight)
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # URL 경로 파싱
        path = getattr(request, 'path', '/api/basis')
        if hasattr(request, 'url'):
            parsed = urlparse(request.url)
            path = parsed.path
        
        # 라우팅
        if path.endswith('/basis') or path.endswith('/api/basis'):
            # 베이시스 데이터 조회
            print("🚀 베이시스 데이터 요청...")
            basis_data = get_basis_data()
            
            response_data = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "data": basis_data,
                "total_count": len(basis_data)
            }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_data)
            }
            
        elif path.endswith('/health'):
            # 헬스체크
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "binance-basis-monitor"
                })
            }
        
        else:
            # 기본 응답
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Binance Basis Monitor API",
                    "endpoints": ["/api/basis", "/api/health"],
                    "timestamp": datetime.now().isoformat()
                })
            }
    
    except Exception as e:
        print(f"API Error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                "error": "Internal server error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
        }