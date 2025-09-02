"""
Vercel Serverless Function: /api/
기본 API 정보 및 Health Check
"""

import json
from datetime import datetime

def handler(request, context=None):
    """Vercel serverless function handler for API root"""
    
    # CORS 헤더
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    # OPTIONS 요청 처리 (CORS preflight)
    if hasattr(request, 'method') and request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        response_data = {
            'success': True,
            'message': '바이낸스 현선물 베이시스 모니터 API',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                '/api/': 'API 정보',
                '/api/basis': '베이시스 데이터'
            },
            'status': 'healthy'
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(error_response)
        }

# Vercel handler aliases
app = handler
main = handler