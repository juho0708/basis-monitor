"""
Vercel Python Handler - Basis API (Flask style)
"""

from datetime import datetime

def handler(request):
    """Flask-style handler for Binance basis data"""
    
    # HTTP method 확인
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
    
    try:
        # 간단한 테스트 데이터 (일단 하드코딩)
        test_data = [
            {
                'symbol': 'BTC',
                'spot_price': 42000.0,
                'futures_price': 42150.0,
                'basis': 150.0,
                'basis_percent': 0.36,
                'spot_volume': 1000.0,
                'futures_volume': 1200.0,
                'last_update': datetime.now()
            },
            {
                'symbol': 'ETH',
                'spot_price': 2500.0,
                'futures_price': 2520.0,
                'basis': 20.0,
                'basis_percent': 0.80,
                'spot_volume': 800.0,
                'futures_volume': 900.0,
                'last_update': datetime.now()
            }
        ]
        
        response_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': test_data,
            'total_count': len(test_data),
            'message': 'Test data (Binance API 대신 하드코딩 데이터)'
        }
        
        return (response_data, 200, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        })
        
    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'data': []
        }
        
        return (error_response, 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        })

# Default export
app = handler