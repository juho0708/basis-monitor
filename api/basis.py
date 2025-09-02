"""
Vercel Serverless Function: /api/basis
바이낸스 현선물 베이시스 데이터 제공 (간단한 구현)
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any

def handler(request, context=None):
    """Vercel serverless function handler"""
    
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
        # 베이시스 데이터 가져오기
        basis_data = get_basis_data()
        
        response_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': basis_data,
            'total_count': len(basis_data)
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
            'timestamp': datetime.now().isoformat(),
            'data': []
        }
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(error_response)
        }

def get_basis_data() -> List[Dict[str, Any]]:
    """바이낸스에서 베이시스 데이터 가져오기"""
    
    # 주요 거래량 많은 코인들만 선별
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'XRPUSDT',
        'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'SHIBUSDT',
        'MATICUSDT', 'LTCUSDT', 'ATOMUSDT', 'LINKUSDT', 'UNIUSDT',
        'BCHUSDT', 'XLMUSDT', 'VETUSDT', 'FILUSDT', 'TRXUSDT'
    ]
    
    basis_list = []
    
    for symbol in symbols:
        try:
            # 현물과 선물 가격 가져오기
            spot_data = get_spot_price(symbol)
            futures_data = get_futures_price(symbol)
            
            if spot_data and futures_data:
                # 베이시스 계산
                spot_price = float(spot_data['price'])
                futures_price = float(futures_data['price'])
                basis = futures_price - spot_price
                basis_percent = (basis / spot_price) * 100
                
                basis_item = {
                    'symbol': symbol.replace('USDT', ''),
                    'spot_price': round(spot_price, 4),
                    'futures_price': round(futures_price, 4),
                    'basis': round(basis, 4),
                    'basis_percent': round(basis_percent, 2),
                    'spot_volume': float(spot_data.get('volume', 0)),
                    'futures_volume': float(futures_data.get('volume', 0)),
                    'last_update': datetime.now()
                }
                
                basis_list.append(basis_item)
                
        except Exception as e:
            print(f"❌ {symbol} 처리 중 오류: {e}")
            continue
    
    # 베이시스 퍼센트 기준 정렬 (내림차순)
    basis_list.sort(key=lambda x: x['basis_percent'], reverse=True)
    
    return basis_list

def get_spot_price(symbol: str) -> Dict:
    """현물 가격 가져오기"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"현물 가격 조회 실패 {symbol}: {e}")
        return {}

def get_futures_price(symbol: str) -> Dict:
    """선물 가격 가져오기"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"선물 가격 조회 실패 {symbol}: {e}")
        return {}

# Vercel은 기본적으로 handler 함수를 찾습니다
# 추가로 다른 이름들도 지원
app = handler
main = handler
