"""
Vercel용 바이낸스 현선물 베이시스 모니터링 API
서버리스 함수로 실행됨 (WebSocket 대신 HTTP 폴링 사용)
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio
import json
import logging
from typing import List
from datetime import datetime
import sys
import os

# 상위 디렉토리의 모듈 import를 위한 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from binance_api import BinanceAPI, TickerData

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="바이낸스 현선물 베이시스 모니터 (Vercel)", version="2.0.0")

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

@app.get("/api/basis")
async def get_basis():
    """REST API: 현재 베이시스 데이터 (실시간)"""
    try:
        logger.info("베이시스 데이터 요청 시작")
        async with BinanceAPI() as api:
            all_basis = await api.get_all_basis_data()
            
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "data": [ticker_to_dict(ticker) for ticker in all_basis],
                "total_count": len(all_basis)
            }
            
            logger.info(f"베이시스 데이터 반환 완료: {len(all_basis)}개")
            return JSONResponse(content=result)
            
    except Exception as e:
        logger.error(f"베이시스 데이터 API 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "vercel",
        "version": "2.0.0"
    })

@app.get("/api")
async def api_info():
    """API 정보"""
    return JSONResponse(content={
        "name": "바이낸스 현선물 베이시스 모니터 API",
        "version": "2.0.0",
        "environment": "vercel",
        "endpoints": {
            "/api/basis": "현재 베이시스 데이터 조회",
            "/api/health": "헬스 체크"
        },
        "timestamp": datetime.now().isoformat()
    })

# Vercel용 핸들러
def handler(request):
    """Vercel 서버리스 함수 핸들러"""
    import uvicorn
    return uvicorn.run(app, host="0.0.0.0", port=8000)

# FastAPI 앱을 Vercel에서 직접 사용할 수 있도록 export
def create_app():
    return app
