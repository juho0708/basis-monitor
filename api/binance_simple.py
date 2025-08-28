"""
Vercel용 간단한 바이낸스 API
동기식 requests 사용으로 안정성 향상
"""

import requests
import json
from datetime import datetime
import time

class SimpleBinanceAPI:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.timeout = 8  # Vercel 타임아웃 고려해서 짧게 설정
    
    def get_spot_prices(self):
        """현물 가격 조회"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                # USDT 페어만 필터링
                usdt_pairs = {}
                for item in data:
                    symbol = item['symbol']
                    if symbol.endswith('USDT') and float(item['quoteVolume']) > 500000:  # 최소 거래량
                        usdt_pairs[symbol] = {
                            'price': float(item['lastPrice']),
                            'volume': float(item['quoteVolume'])
                        }
                return usdt_pairs
            return {}
        except Exception as e:
            print(f"Spot prices error: {e}")
            return {}
    
    def get_futures_prices(self):
        """선물 가격 조회"""
        try:
            url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                # USDT 페어만 필터링
                usdt_pairs = {}
                for item in data:
                    symbol = item['symbol']
                    if symbol.endswith('USDT') and float(item['quoteVolume']) > 500000:  # 최소 거래량
                        usdt_pairs[symbol] = {
                            'price': float(item['lastPrice']),
                            'volume': float(item['quoteVolume'])
                        }
                return usdt_pairs
            return {}
        except Exception as e:
            print(f"Futures prices error: {e}")
            return {}
    
    def calculate_basis(self):
        """베이시스 계산"""
        print("🚀 베이시스 계산 시작...")
        
        # 현물과 선물 데이터 조회
        spot_data = self.get_spot_prices()
        futures_data = self.get_futures_prices()
        
        if not spot_data or not futures_data:
            return []
        
        print(f"📊 현물: {len(spot_data)}개, 선물: {len(futures_data)}개")
        
        basis_data = []
        
        # 공통 심볼 찾기
        common_symbols = set(spot_data.keys()) & set(futures_data.keys())
        
        for symbol in common_symbols:
            try:
                spot_price = spot_data[symbol]['price']
                futures_price = futures_data[symbol]['price']
                spot_volume = spot_data[symbol]['volume']
                futures_volume = futures_data[symbol]['volume']
                
                # 베이시스 계산
                basis = futures_price - spot_price
                basis_percent = (basis / spot_price) * 100 if spot_price > 0 else 0
                
                # 필터링: 베이시스 ±10% 이내
                if abs(basis_percent) <= 10:
                    basis_data.append({
                        'symbol': symbol,
                        'spot_price': round(spot_price, 6),
                        'futures_price': round(futures_price, 6),
                        'basis': round(basis, 6),
                        'basis_percent': round(basis_percent, 2),
                        'spot_volume': round(spot_volume, 2),
                        'futures_volume': round(futures_volume, 2),
                        'last_update': datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        # 베이시스 퍼센트로 정렬 (내림차순)
        basis_data.sort(key=lambda x: x['basis_percent'], reverse=True)
        
        print(f"✅ {len(basis_data)}개 베이시스 계산 완료")
        return basis_data[:50]  # 상위 50개만 반환 (응답 크기 제한)

def get_basis_data():
    """베이시스 데이터 조회 함수"""
    api = SimpleBinanceAPI()
    return api.calculate_basis()

