"""
가장 기본적인 Vercel Python 함수
"""

import json
from datetime import datetime

def handler(request, context):
    """기본 핸들러 테스트"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            "status": "success",
            "message": "Basic Python handler working!",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })
    }