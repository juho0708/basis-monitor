"""
Vercel용 바이낸스 현선물 베이시스 모니터링 API
간단한 HTTP 핸들러 방식
"""

import json
import asyncio
from datetime import datetime
from urllib.parse import urlparse

# 절대 import로 변경
try:
    from .binance_api import BinanceAPI, TickerData
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from binance_api import BinanceAPI, TickerData

def ticker_to_dict(ticker: TickerData) -> dict:
    """TickerData를 딕셔너리로 변환"""
    return {
        "symbol": ticker.symbol,
        "spot_price": round(ticker.spot_price, 4),
        "futures_price": round(ticker.futures_price, 4),
        "basis": round(ticker.basis, 4),
        "basis_percent": round(ticker.basis_percent, 2),
        "spot_volume": round(ticker.spot_volume, 2),
        "futures_volume": round(ticker.futures_volume, 2),
        "last_update": ticker.last_update.isoformat()
    }

def handler(request, context):
    """Vercel 서버리스 함수 핸들러"""
    try:
        # 요청 URL 파싱
        path = request.get('url', '/')
        if path.startswith('https://'):
            parsed = urlparse(path)
            path = parsed.path
        
        # 라우팅
        if path == '/api/health':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "environment": "vercel",
                    "version": "3.0.0",
                    "message": "Simple handler working!"
                })
            }
        
        elif path == '/api/test':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "success": True,
                    "message": "Simple test working!",
                    "timestamp": datetime.now().isoformat(),
                    "request_info": {
                        "path": path,
                        "url": request.get('url', 'unknown')
                    }
                })
            }
        
        elif path == '/api/basis':
            # 비동기 함수를 동기적으로 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(get_basis_data())
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(result)
                }
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                }
            finally:
                loop.close()
        
        elif path == '/api':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "name": "바이낸스 현선물 베이시스 모니터 API",
                    "version": "3.0.0",
                    "environment": "vercel",
                    "endpoints": {
                        "/api/test": "간단한 테스트",
                        "/api/health": "헬스 체크",
                        "/api/basis": "현재 베이시스 데이터 조회"
                    },
                    "timestamp": datetime.now().isoformat()
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "error": "Not Found",
                    "path": path,
                    "timestamp": datetime.now().isoformat()
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "error": f"Handler error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        }

async def get_basis_data():
    """베이시스 데이터 가져오기"""
    try:
        async with BinanceAPI() as api:
            all_basis = await api.get_all_basis_data()
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "data": [ticker_to_dict(ticker) for ticker in all_basis],
                "total_count": len(all_basis)
            }
    except Exception as e:
        raise Exception(f"Binance API error: {str(e)}")