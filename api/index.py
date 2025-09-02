"""
Vercel Python Handler - Flask style
"""

from datetime import datetime

def handler(request):
    """Flask-style handler for Vercel"""
    
    # HTTP method 확인
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
    
    # JSON 응답 데이터
    data = {
        'success': True,
        'message': 'Vercel Python API Works!',
        'version': '2.1.0',
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy'
    }
    
    return (data, 200, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    })

# Default export
app = handler