"""
현선물 베이시스 실시간 모니터링 FastAPI 서버
WebSocket을 통한 실시간 데이터 전송
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
import os
from typing import List
from datetime import datetime
import uvicorn

from binance_api import BinanceAPI, TickerData

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="바이낸스 현선물 베이시스 모니터", version="1.0.0")

# 정적 파일 서빙 (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"새 연결: 총 {len(self.active_connections)}개 연결")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"연결 끊김: 총 {len(self.active_connections)}개 연결")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"개별 메시지 전송 실패: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"브로드캐스트 실패: {e}")
                disconnected.append(connection)
        
        # 끊어진 연결 제거
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

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

async def data_broadcaster():
    """백그라운드에서 실행되는 데이터 브로드캐스터"""
    while True:
        try:
            if manager.active_connections:
                async with BinanceAPI() as api:
                    all_basis = await api.get_all_basis_data()
                    
                    data = {
                        "type": "basis_update",
                        "timestamp": datetime.now().isoformat(),
                        "data": [ticker_to_dict(ticker) for ticker in all_basis],
                        "total_count": len(all_basis)
                    }
                    
                    await manager.broadcast(json.dumps(data))
                    logger.info(f"브로드캐스트 완료: 전체 {len(all_basis)}개 베이시스 데이터")
            
            # 10초마다 업데이트
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"데이터 브로드캐스트 오류: {e}")
            await asyncio.sleep(5)  # 오류 시 5초 대기

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 백그라운드 작업 시작"""
    logger.info("🚀 바이낸스 베이시스 모니터 서버 시작")
    asyncio.create_task(data_broadcaster())

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """메인 페이지"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/basis")
async def get_basis():
    """REST API: 현재 베이시스 데이터"""
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
        logger.error(f"REST API 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트"""
    await manager.connect(websocket)
    
    try:
        # 연결 즉시 현재 데이터 전송
        async with BinanceAPI() as api:
            all_basis = await api.get_all_basis_data()
            initial_data = {
                "type": "initial_data",
                "timestamp": datetime.now().isoformat(),
                "data": [ticker_to_dict(ticker) for ticker in all_basis],
                "total_count": len(all_basis)
            }
            await manager.send_personal_message(json.dumps(initial_data), websocket)
        
        # 연결 유지
        while True:
            await websocket.receive_text()  # 클라이언트 메시지 대기
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections)
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"서버 시작... 포트: {port}")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # 프로덕션에서는 reload=False
        log_level="info"
    )
