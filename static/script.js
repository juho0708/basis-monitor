/**
 * 바이낸스 현선물 베이시스 모니터 - JavaScript
 * WebSocket 연결 및 실시간 데이터 업데이트
 */

class BasisMonitor {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        
        // 정렬 상태
        this.currentData = [];
        this.sortColumn = 'basis_percent';  // 기본 정렬: 베이시스 %
        this.sortDirection = 'desc';        // 기본: 내림차순
        
        // 데이터 관리
        this.allData = [];  // 전체 데이터
        this.displayLimit = 10;  // 표시할 개수
        
        // DOM 요소 참조
        this.elements = {
            connectionStatus: document.getElementById('connectionStatus'),
            lastUpdate: document.getElementById('lastUpdate'),
            refreshIcon: document.getElementById('refreshIcon'),
            basisTableBody: document.getElementById('basisTableBody'),
            basisTable: document.getElementById('basisTable'),
            maxBasis: document.getElementById('maxBasis'),
            maxBasisSymbol: document.getElementById('maxBasisSymbol'),
            avgBasis: document.getElementById('avgBasis'),
            totalVolume: document.getElementById('totalVolume'),
            toast: document.getElementById('toast'),
            toastMessage: document.getElementById('toastMessage')
        };
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        console.log('🚀 바이낸스 베이시스 모니터 초기화 완료');
    }
    
    setupEventListeners() {
        // 페이지 언로드 시 WebSocket 연결 종료
        window.addEventListener('beforeunload', () => {
            if (this.ws) {
                this.ws.close();
            }
        });
        
        // 포커스 복귀 시 연결 상태 확인
        window.addEventListener('focus', () => {
            if (!this.isConnected) {
                this.connectWebSocket();
            }
        });
        
        // 테이블 헤더 클릭 이벤트 (정렬)
        this.setupTableSorting();
        

    }
    
    setupTableSorting() {
        const headers = this.elements.basisTable.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            
            // 호버 효과
            header.addEventListener('mouseenter', () => {
                header.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
            });
            
            header.addEventListener('mouseleave', () => {
                header.style.backgroundColor = '';
            });
            
            // 클릭 이벤트
            header.addEventListener('click', () => {
                const sortKey = header.getAttribute('data-sort');
                this.sortTable(sortKey);
            });
        });
        
        // 초기 정렬 표시 업데이트
        this.updateSortIndicators();
    }
    
    sortTable(column) {
        // 같은 컬럼 클릭 시 방향 토글, 다른 컬럼 클릭 시 내림차순으로 시작
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'desc';
        }
        
        // 전체 데이터를 다시 정렬하여 표시
        this.updateDisplayData();
        
        // 정렬 완료 알림
        this.showToast(`${this.getColumnName(column)} ${this.sortDirection === 'desc' ? '내림차순' : '오름차순'} 정렬`, 'info');
    }
    
    updateSortIndicators() {
        const headers = this.elements.basisTable.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            const sortKey = header.getAttribute('data-sort');
            const icon = header.querySelector('.sort-icon') || document.createElement('span');
            
            if (!header.querySelector('.sort-icon')) {
                icon.className = 'sort-icon';
                icon.style.marginLeft = '5px';
                header.appendChild(icon);
            }
            
            if (sortKey === this.sortColumn) {
                icon.innerHTML = this.sortDirection === 'desc' ? '▼' : '▲';
                icon.style.color = '#3b82f6';
            } else {
                icon.innerHTML = '↕';
                icon.style.color = '#9ca3af';
            }
        });
    }
    
    getColumnName(column) {
        const names = {
            'symbol': '심볼',
            'spot_price': '현물가격',
            'futures_price': '선물가격', 
            'basis': '베이시스',
            'basis_percent': '베이시스%',
            'spot_volume': '현물거래액',
            'futures_volume': '선물거래액'
        };
        return names[column] || column;
    }
    

    
    updateDisplayData() {
        console.log(`🔄 updateDisplayData 호출: allData=${this.allData?.length}개`);
        
        if (!this.allData || this.allData.length === 0) {
            console.log('❌ allData가 없음');
            return;
        }
        
        // 전체 데이터를 현재 정렬 기준으로 정렬
        let sortedData = [...this.allData];
        sortedData.sort((a, b) => {
            let aVal, bVal;
            
            switch (this.sortColumn) {
                case 'symbol':
                    aVal = a.symbol;
                    bVal = b.symbol;
                    break;
                case 'spot_price':
                    aVal = parseFloat(a.spot_price);
                    bVal = parseFloat(b.spot_price);
                    break;
                case 'futures_price':
                    aVal = parseFloat(a.futures_price);
                    bVal = parseFloat(b.futures_price);
                    break;
                case 'basis_percent':
                    aVal = parseFloat(a.basis_percent);
                    bVal = parseFloat(b.basis_percent);
                    break;
                case 'spot_volume':
                    aVal = parseFloat(a.spot_volume) * parseFloat(a.spot_price);  // USD 거래량
                    bVal = parseFloat(b.spot_volume) * parseFloat(b.spot_price);
                    break;
                case 'futures_volume':
                    aVal = parseFloat(a.futures_volume) * parseFloat(a.futures_price);  // USD 거래량
                    bVal = parseFloat(b.futures_volume) * parseFloat(b.futures_price);
                    break;
                default:
                    aVal = a[this.sortColumn];
                    bVal = b[this.sortColumn];
            }
            
            // 문자열 비교
            if (typeof aVal === 'string' && typeof bVal === 'string') {
                return this.sortDirection === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
            }
            
            // 숫자 비교
            return this.sortDirection === 'desc' ? bVal - aVal : aVal - bVal;
        });
        
        console.log(`📊 전체 정렬 완료: ${this.sortColumn} ${this.sortDirection} - 1위: ${sortedData[0]?.symbol} (${sortedData[0]?.[this.sortColumn]})`);
        
        // 정렬된 결과에서 상위 10개만 선택
        this.currentData = sortedData.slice(0, this.displayLimit);
        console.log(`✂️ ${this.displayLimit}개 선택: ${this.currentData.length}개`);
        
        // 테이블 업데이트
        this.updateTable(this.currentData);
        this.updateSortIndicators();
        
        console.log(`✅ 표시 완료: ${this.currentData.length}개`);
    }
    
    connectWebSocket() {
        try {
            // WebSocket 프로토콜 결정 (HTTPS면 WSS, HTTP면 WS)
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log(`WebSocket 연결 시도: ${wsUrl}`);
            this.updateConnectionStatus('connecting', '연결 중...');
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = (event) => {
                console.log('✅ WebSocket 연결 성공');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', '연결됨');
                this.showToast('실시간 연결이 설정되었습니다', 'success');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('메시지 파싱 오류:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('❌ WebSocket 연결 종료:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus('disconnected', '연결 끊김');
                
                // 자동 재연결 시도
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                } else {
                    this.showToast('연결에 실패했습니다. 페이지를 새로고침 해주세요.', 'error');
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket 오류:', error);
                this.updateConnectionStatus('disconnected', '연결 오류');
                this.showToast('연결 오류가 발생했습니다', 'error');
            };
            
        } catch (error) {
            console.error('WebSocket 연결 실패:', error);
            this.updateConnectionStatus('disconnected', '연결 실패');
            this.scheduleReconnect();
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;
        
        console.log(`🔄 ${delay/1000}초 후 재연결 시도 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.updateConnectionStatus('connecting', `${delay/1000}초 후 재연결...`);
        
        setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }
    
    updateConnectionStatus(status, message) {
        this.elements.connectionStatus.className = `connection-status ${status}`;
        this.elements.connectionStatus.querySelector('span').textContent = message;
        
        // 새로고침 아이콘 애니메이션
        if (status === 'connected') {
            this.elements.refreshIcon.style.animationPlayState = 'running';
        } else {
            this.elements.refreshIcon.style.animationPlayState = 'paused';
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('📥 데이터 수신:', data.type);
        
        switch (data.type) {
            case 'initial_data':
                this.updateBasisData(data);
                this.updateLastUpdate(data.timestamp);
                // 초기 데이터 로드 시 정렬 표시 설정
                setTimeout(() => this.updateSortIndicators(), 100);
                break;
            case 'basis_update':
                this.updateBasisData(data);
                this.updateLastUpdate(data.timestamp);
                break;
            default:
                console.log('알 수 없는 메시지 타입:', data.type);
        }
    }
    
    updateBasisData(data) {
        console.log('🔍 updateBasisData 호출됨:', data);
        
        if (!data) {
            console.error('❌ data가 없음');
            this.showNoData();
            return;
        }
        
        // 데이터 구조 확인
        if (data.data) {
            console.log(`✅ 새 구조 감지: ${data.data.length}개 데이터`);
            this.allData = data.data;
        } else if (data.top && data.bottom) {
            console.log(`⚠️ 예전 구조 감지: top ${data.top.length}개, bottom ${data.bottom.length}개`);
            this.allData = [...data.top, ...data.bottom];
        } else {
            console.error('❌ 알 수 없는 데이터 구조:', Object.keys(data));
            this.showNoData();
            return;
        }
        
        console.log(`🔢 전체 데이터: ${this.allData.length}개`);
        
        // 표시 데이터 업데이트
        this.updateDisplayData();
        
        // 통계 업데이트 (전체 데이터 기준)
        this.updateStats(this.allData);
        
        console.log(`📊 베이시스 데이터 업데이트 완료: 전체 ${this.allData.length}개 중 ${this.currentMode} 모드로 ${this.currentData.length}개 표시`);
    }
    
    updateTable(basisData) {
        const tbody = this.elements.basisTableBody;
        tbody.innerHTML = '';
        
        basisData.forEach((item, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="rank">${index + 1}</span></td>
                <td>
                    <a href="https://www.binance.com/en/futures/${item.symbol}" 
                       target="_blank" 
                       rel="noopener noreferrer"
                       class="symbol-link"
                       title="바이낸스 ${item.symbol} 선물 거래 페이지로 이동">
                        <span class="symbol">${item.symbol}</span>
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </td>
                <td class="price">$${this.formatNumber(item.spot_price, 4)}</td>
                <td class="price">$${this.formatNumber(item.futures_price, 4)}</td>
                <td class="price ${this.getBasisClass(item.basis)}">$${this.formatNumber(item.basis, 4)}</td>
                <td class="${this.getBasisClass(item.basis_percent)}">${this.formatNumber(item.basis_percent, 2)}%</td>
                <td class="volume">${this.formatVolumeUSD(item.spot_volume * item.spot_price)}</td>
                <td class="volume">${this.formatVolumeUSD(item.futures_volume * item.futures_price)}</td>
            `;
            
            // 행 애니메이션
            row.style.opacity = '0';
            row.style.transform = 'translateY(10px)';
            tbody.appendChild(row);
            
            // 애니메이션 지연 (더 빠르게)
            setTimeout(() => {
                row.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, index * 20);
        });
    }
    
    updateStats(basisData) {
        if (basisData.length === 0) return;
        
        // 최고 베이시스
        const maxBasisItem = basisData[0];
        this.elements.maxBasis.textContent = `${this.formatNumber(maxBasisItem.basis_percent, 2)}%`;
        this.elements.maxBasisSymbol.textContent = maxBasisItem.symbol;
        
        // 평균 베이시스
        const avgBasisPercent = basisData.reduce((sum, item) => sum + item.basis_percent, 0) / basisData.length;
        this.elements.avgBasis.textContent = `${this.formatNumber(avgBasisPercent, 2)}%`;
        
        // 총 거래액 (USD)
        const totalVolumeUSD = basisData.reduce((sum, item) => 
            sum + (item.spot_volume * item.spot_price) + (item.futures_volume * item.futures_price), 0);
        this.elements.totalVolume.textContent = this.formatVolumeUSD(totalVolumeUSD);
    }
    
    updateLastUpdate(timestamp) {
        const date = new Date(timestamp);
        const timeString = date.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        this.elements.lastUpdate.textContent = `마지막 업데이트: ${timeString}`;
    }
    
    showNoData() {
        this.elements.basisTableBody.innerHTML = `
            <tr class="loading-row">
                <td colspan="8">
                    <div class="loading">
                        <i class="fas fa-exclamation-triangle"></i>
                        데이터를 불러올 수 없습니다
                    </div>
                </td>
            </tr>
        `;
    }
    
    getBasisClass(value) {
        if (value > 0) return 'basis-positive';
        if (value < 0) return 'basis-negative';
        return 'basis-neutral';
    }
    
    formatNumber(num, decimals = 2) {
        if (typeof num !== 'number' || isNaN(num)) return '0.00';
        return num.toLocaleString('ko-KR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }
    
    formatVolume(volume) {
        if (typeof volume !== 'number' || isNaN(volume)) return '0';
        
        if (volume >= 1e9) {
            return `${this.formatNumber(volume / 1e9, 1)}B`;
        } else if (volume >= 1e6) {
            return `${this.formatNumber(volume / 1e6, 1)}M`;
        } else if (volume >= 1e3) {
            return `${this.formatNumber(volume / 1e3, 1)}K`;
        }
        return this.formatNumber(volume, 0);
    }
    
    formatVolumeUSD(volumeUSD) {
        if (typeof volumeUSD !== 'number' || isNaN(volumeUSD)) return '$0';
        
        if (volumeUSD >= 1e9) {
            return `$${this.formatNumber(volumeUSD / 1e9, 1)}B`;
        } else if (volumeUSD >= 1e6) {
            return `$${this.formatNumber(volumeUSD / 1e6, 1)}M`;
        } else if (volumeUSD >= 1e3) {
            return `$${this.formatNumber(volumeUSD / 1e3, 1)}K`;
        }
        return `$${this.formatNumber(volumeUSD, 0)}`;
    }
    
    showToast(message, type = 'info') {
        this.elements.toastMessage.textContent = message;
        this.elements.toast.className = `toast ${type}`;
        this.elements.toast.classList.add('show');
        
        // 3초 후 자동 숨김
        setTimeout(() => {
            this.elements.toast.classList.remove('show');
        }, 3000);
    }
}

// 문서 로드 완료 시 모니터 시작
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 문서 로드 완료, 베이시스 모니터 시작');
    new BasisMonitor();
});

// 서비스 워커 등록 (PWA 지원)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('🛠️ Service Worker 등록 성공:', registration);
            })
            .catch(error => {
                console.log('Service Worker 등록 실패:', error);
            });
    });
}
