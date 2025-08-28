# 바이낸스 현선물 베이시스 모니터

실시간으로 바이낸스 현물과 선물의 베이시스를 모니터링하는 웹 애플리케이션입니다.

## 🌟 주요 기능

- 📊 **실시간 베이시스 모니터링**: 바이낸스 현물/선물 가격차이를 실시간으로 계산
- 🔄 **자동 정렬**: 컬럼 클릭으로 다양한 기준으로 정렬 가능
- 📱 **반응형 디자인**: 모바일/데스크톱 모든 환경에서 사용 가능
- ⚡ **빠른 업데이트**: 10초마다 자동 업데이트
- 🔗 **바이낸스 연동**: 심볼 클릭 시 바이낸스 거래 페이지로 이동

## 🚀 기술 스택

### Backend
- **FastAPI**: 고성능 웹 API 프레임워크
- **aiohttp**: 비동기 HTTP 클라이언트로 바이낸스 API 호출
- **Python 3.13**: 최신 Python 버전

### Frontend
- **HTML5/CSS3**: 모던 웹 표준
- **Vanilla JavaScript**: 프레임워크 없는 순수 자바스크립트
- **Font Awesome**: 아이콘

### Deployment
- **Vercel**: 서버리스 배포 플랫폼
- **HTTP 폴링**: WebSocket 대신 REST API 사용 (서버리스 환경 최적화)

## 📁 프로젝트 구조

```
basis_monitor/
├── api/
│   ├── index.py          # Vercel 서버리스 함수 (메인 API)
│   └── binance_api.py    # 바이낸스 API 클라이언트
├── static/
│   ├── index.html        # 메인 HTML 페이지
│   ├── style.css         # 스타일시트
│   └── script_vercel.js  # Vercel용 JavaScript (HTTP 폴링)
├── vercel.json           # Vercel 배포 설정
├── requirements.txt      # Python 의존성
└── README.md
```

## 🌐 API 엔드포인트

- `GET /api/basis` - 현재 베이시스 데이터 조회
- `GET /api/health` - 헬스 체크
- `GET /api` - API 정보

## 📊 데이터 필터링

### 포함 조건
- ✅ USDT 페어만 대상
- ✅ 활성 거래 상태 (`TRADING` status)
- ✅ 현물/선물 각각 $500K 이상 24시간 거래량
- ✅ 베이시스 ±10% 이내

### 제외 조건
- ❌ 비활성 심볼
- ❌ 거래량 부족 심볼
- ❌ 극단적 베이시스 (±10% 초과)

## 🎯 주요 메트릭

- **베이시스**: 선물가격 - 현물가격
- **베이시스 %**: (베이시스 / 현물가격) × 100
- **거래량**: USD 기준 24시간 거래량
- **업데이트 주기**: 10초

## 🔧 로컬 개발

### 1. 환경 설정
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python server.py
```

### 3. 접속
브라우저에서 `http://localhost:8000` 접속

## 🚀 Vercel 배포

### 1. GitHub 연동
1. 이 프로젝트를 GitHub에 업로드
2. [Vercel](https://vercel.com)에서 GitHub 연동
3. 프로젝트 import 후 자동 배포

### 2. 환경 변수 (필요시)
현재는 환경 변수가 필요하지 않지만, 향후 API 키 등이 필요한 경우 Vercel 대시보드에서 설정 가능

## 📱 사용법

1. **정렬**: 테이블 헤더를 클릭하여 해당 컬럼 기준으로 정렬
2. **거래 페이지 이동**: 심볼을 클릭하면 바이낸스 선물 거래 페이지로 이동
3. **실시간 업데이트**: 자동으로 10초마다 데이터 갱신

## ⚡ 성능 최적화

- **비동기 처리**: 모든 API 호출이 비동기로 처리
- **효율적 필터링**: 서버에서 사전 필터링하여 불필요한 데이터 전송 최소화
- **캐싱**: 클라이언트에서 전체 데이터를 캐싱하여 정렬 성능 향상
- **서버리스**: Vercel 서버리스 환경에서 최적화된 아키텍처

## 🛠️ 기술적 특징

- **실시간 가격**: `/api/v3/ticker/price` (현물), `/fapi/v1/ticker/price` (선물)
- **24시간 거래량**: `/api/v3/ticker/24hr` (현물), `/fapi/v1/ticker/24hr` (선물)  
- **활성 심볼**: `/api/v3/exchangeInfo`로 활성 상태 확인
- **에러 처리**: 포괄적인 에러 핸들링 및 재시도 로직

## 📈 향후 개선 계획

- [ ] 차트 기능 추가
- [ ] 알림 기능 (특정 베이시스 임계값)
- [ ] 히스토리컬 데이터
- [ ] 다른 거래소 지원 (Bybit, OKX 등)
- [ ] PWA 지원

## 📞 문의

프로젝트 관련 문의나 이슈는 GitHub Issues를 이용해 주세요.

---

⚡ **Live Demo**: [배포 후 URL 업데이트 예정]