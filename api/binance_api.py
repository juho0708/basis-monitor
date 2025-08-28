"""
바이낸스 현물/선물 가격 API 연동
현선물 베이시스 계산을 위한 바이낸스 API 클라이언트
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TickerData:
    """티커 데이터 구조"""
    symbol: str
    spot_price: float
    futures_price: float
    basis: float
    basis_percent: float
    spot_volume: float
    futures_volume: float
    last_update: datetime

class BinanceAPI:
    """바이낸스 API 클라이언트"""
    
    def __init__(self):
        self.spot_base_url = "https://api.binance.com"
        self.futures_base_url = "https://fapi.binance.com"
        self.session = None
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def get_spot_prices(self) -> Dict[str, float]:
        """현물 실시간 가격 정보 가져오기"""
        url = f"{self.spot_base_url}/api/v3/ticker/price"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        item['symbol']: float(item['price'])
                        for item in data 
                        if item['symbol'].endswith('USDT')  # USDT 페어만 필터링
                    }
                else:
                    logger.error(f"현물 가격 데이터 가져오기 실패: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"현물 가격 API 호출 오류: {e}")
            return {}
    
    async def get_spot_volumes(self) -> Dict[str, float]:
        """현물 거래량 정보 가져오기"""
        url = f"{self.spot_base_url}/api/v3/ticker/24hr"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        item['symbol']: float(item['volume'])
                        for item in data 
                        if item['symbol'].endswith('USDT')  # USDT 페어만 필터링
                    }
                else:
                    logger.error(f"현물 거래량 데이터 가져오기 실패: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"현물 거래량 API 호출 오류: {e}")
            return {}
    
    async def get_futures_prices(self) -> Dict[str, float]:
        """선물 실시간 가격 정보 가져오기"""
        url = f"{self.futures_base_url}/fapi/v1/ticker/price"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        item['symbol']: float(item['price'])
                        for item in data 
                        if item['symbol'].endswith('USDT')  # USDT 페어만 필터링
                    }
                else:
                    logger.error(f"선물 가격 데이터 가져오기 실패: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"선물 가격 API 호출 오류: {e}")
            return {}
    
    async def get_futures_volumes(self) -> Dict[str, float]:
        """선물 거래량 정보 가져오기"""
        url = f"{self.futures_base_url}/fapi/v1/ticker/24hr"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        item['symbol']: float(item['volume'])
                        for item in data 
                        if item['symbol'].endswith('USDT')  # USDT 페어만 필터링
                    }
                else:
                    logger.error(f"선물 거래량 데이터 가져오기 실패: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"선물 거래량 API 호출 오류: {e}")
            return {}
    
    async def get_active_symbols(self) -> set:
        """활성 거래 중인 USDT 심볼 목록 가져오기"""
        url = f"{self.spot_base_url}/api/v3/exchangeInfo"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # TRADING 상태이고 USDT로 끝나는 심볼만 선택
                    active_symbols = {
                        symbol['symbol'] 
                        for symbol in data['symbols']
                        if symbol['status'] == 'TRADING' and symbol['symbol'].endswith('USDT')
                    }
                    logger.info(f"활성 USDT 심볼 {len(active_symbols)}개 확인")
                    return active_symbols
                else:
                    logger.error(f"거래소 정보 가져오기 실패: {response.status}")
                    return set()
        except Exception as e:
            logger.error(f"거래소 정보 API 호출 오류: {e}")
            return set()

    async def calculate_basis(self) -> List[TickerData]:
        """현선물 베이시스 계산"""
        # 활성 심볼과 가격/거래량 데이터를 병렬로 가져오기
        active_symbols, spot_prices, futures_prices, spot_volumes, futures_volumes = await asyncio.gather(
            self.get_active_symbols(),
            self.get_spot_prices(),
            self.get_futures_prices(), 
            self.get_spot_volumes(),
            self.get_futures_volumes()
        )
        
        basis_data = []
        current_time = datetime.now()
        
        # 활성 거래 중이고 현물과 선물 모두 존재하는 심볼만 처리
        common_symbols = active_symbols & set(spot_prices.keys()) & set(futures_prices.keys())
        
        for symbol in common_symbols:
            try:
                spot_price = spot_prices[symbol]
                futures_price = futures_prices[symbol]
                spot_volume = spot_volumes.get(symbol, 0)
                futures_volume = futures_volumes.get(symbol, 0)
                
                # 유효성 검사
                if spot_price <= 0 or futures_price <= 0:
                    continue
                
                # 선물과 현물 거래량이 모두 있는지 확인 (활발한 거래 확인)
                if spot_volume <= 0 or futures_volume <= 0:
                    continue
                    
                # 베이시스 계산: (선물가격 - 현물가격)
                basis = futures_price - spot_price
                # 베이시스 퍼센트: (선물가격 - 현물가격) / 현물가격 * 100
                basis_percent = (basis / spot_price) * 100
                
                # 합리적인 베이시스 범위 필터링 (-10% ~ +10%) - 더 엄격하게
                if abs(basis_percent) > 10:
                    continue
                    
                # 최소 거래량 필터링 - 현물과 선물 각각 최소 거래액 필요
                spot_volume_usd = spot_volume * spot_price
                futures_volume_usd = futures_volume * futures_price
                
                # 현물과 선물 각각 최소 50만 달러 거래액 필요
                if spot_volume_usd < 500_000 or futures_volume_usd < 500_000:
                    continue
                
                ticker_data = TickerData(
                    symbol=symbol,
                    spot_price=spot_price,
                    futures_price=futures_price,
                    basis=basis,
                    basis_percent=basis_percent,
                    spot_volume=spot_volume,
                    futures_volume=futures_volume,
                    last_update=current_time
                )
                
                basis_data.append(ticker_data)
                
            except Exception as e:
                logger.error(f"{symbol} 베이시스 계산 오류: {e}")
                continue
        
        # 베이시스 퍼센트 기준으로 내림차순 정렬 (높은 순서)
        basis_data.sort(key=lambda x: x.basis_percent, reverse=True)
        
        logger.info(f"총 {len(basis_data)}개 심볼의 베이시스 계산 완료 (전체 USDT 페어 대상)")
        return basis_data
    
    async def get_top_basis(self, limit: int = 5) -> List[TickerData]:
        """상위 N개 베이시스 반환"""
        all_basis = await self.calculate_basis()
        return all_basis[:limit]
    
    async def get_all_basis_data(self) -> List[TickerData]:
        """전체 베이시스 데이터 반환 (클라이언트에서 정렬)"""
        return await self.calculate_basis()

# 테스트 함수
async def test_api():
    """API 테스트"""
    async with BinanceAPI() as api:
        print("🔄 바이낸스 현선물 베이시스 테스트 중...")
        
        top_basis = await api.get_top_basis(5)
        
        print(f"\n📊 상위 5개 베이시스:")
        print("-" * 80)
        print(f"{'심볼':<15} {'현물가격':<12} {'선물가격':<12} {'베이시스':<10} {'베이시스%':<10}")
        print("-" * 80)
        
        for ticker in top_basis:
            print(f"{ticker.symbol:<15} ${ticker.spot_price:<11.4f} ${ticker.futures_price:<11.4f} "
                  f"${ticker.basis:<9.4f} {ticker.basis_percent:<9.2f}%")

if __name__ == "__main__":
    asyncio.run(test_api())