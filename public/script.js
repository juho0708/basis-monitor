/**
 * 바이낸스 현선물 베이시스 모니터 - JavaScript (HTTP Polling 버전)
 * Vercel Serverless Functions용
 */

class BasisMonitor {
    constructor() {
        this.isLoading = false;
        this.pollingInterval = null;
        this.pollingDelay = 10000; // 10초마다 업데이트
        this.retryAttempts = 0;
        this.maxRetryAttempts = 3;
        
        // 정렬 상태
        this.currentData = [];
        this.sortColumn = 'basis_percent';
        this.sortDirection = 'desc';
        
        // 데이터 관리
        this.allData = [];
        this.displayLimit = 10;
        
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
        this.setupEventListeners();
        this.startPolling();
        console.log('🚀 바이낸스 베이시스 모니터 초기화 완료 (HTTP Polling)');
    }
    
    setupEventListeners() {
        // 페이지 언로드 시 폴링 중지
        window.addEventListener('beforeunload', () => {
            this.stopPolling();
        });
        
        // 포커스 복귀 시 즉시 데이터 새로고침
        window.addEventListener('focus', () => {
            if (!this.isLoading) {
                this.fetchData();
            }
        });
        
        // 테이블 헤더 클릭 이벤트 (정렬)
        this.setupTableSorting();
        
        // 수동 새로고침 버튼 (새로고침 아이콘 클릭)
        if (this.elements.refreshIcon) {
            this.elements.refreshIcon.addEventListener('click', () => {
                if (!this.isLoading) {
                    this.fetchData();
                    this.showToast('데이터를 새로고침합니다', 'info');
                }
            });
            this.elements.refreshIcon.style.cursor = 'pointer';
        }
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
    
    startPolling() {
        // 즉시 첫 데이터 로드
        this.fetchData();
        
        // 주기적 폴링 시작
        this.pollingInterval = setInterval(() => {
            this.fetchData();
        }, this.pollingDelay);
        
        console.log(`🔄 폴링 시작: ${this.pollingDelay/1000}초 간격`);
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('⏹️ 폴링 중지');
        }
    }
    
    async fetchData() {
        if (this.isLoading) {
            console.log('⏳ 이미 로딩 중...');
            return;
        }
        
        this.isLoading = true;
        this.updateConnectionStatus('loading', '데이터 로딩 중...');
        
        // 새로고침 아이콘 애니메이션 시작
        if (this.elements.refreshIcon) {
            this.elements.refreshIcon.style.animation = 'spin 2s linear infinite';
        }
        
        try {
            console.log('📡 API 호출 시작...');
            const response = await fetch('/api/basis', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                // 캐시 방지
                cache: 'no-cache'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('✅ API 응답 받음:', data);
            
            if (data.success && data.data) {
                this.handleDataUpdate(data);
                this.retryAttempts = 0; // 성공시 재시도 카운터 리셋
                this.updateConnectionStatus('connected', '연결됨');
            } else {
                throw new Error(data.error || '데이터가 올바르지 않습니다');
            }
            
        } catch (error) {
            console.error('❌ 데이터 로딩 실패:', error);
            this.handleError(error);
        } finally {
            this.isLoading = false;
            
            // 새로고침 아이콘 애니메이션 중지
            if (this.elements.refreshIcon) {
                this.elements.refreshIcon.style.animation = '';
            }
        }
    }
    
    handleDataUpdate(data) {
        console.log('🔍 handleDataUpdate 호출됨:', data);
        
        if (!data || !data.data || data.data.length === 0) {
            console.error('❌ 유효하지 않은 데이터');
            this.showNoData();
            return;
        }
        
        // 전체 데이터 저장
        this.allData = data.data;
        console.log(`✅ 새 데이터 저장: ${this.allData.length}개`);
        
        // 표시 데이터 업데이트
        this.updateDisplayData();
        
        // 통계 업데이트
        this.updateStats(this.allData);
        
        // 마지막 업데이트 시간
        this.updateLastUpdate(data.timestamp);
        
        console.log(`📊 데이터 업데이트 완료: ${this.allData.length}개 중 ${this.currentData.length}개 표시`);
    }
    
    handleError(error) {
        this.retryAttempts++;
        
        if (this.retryAttempts <= this.maxRetryAttempts) {
            console.log(`🔄 재시도 ${this.retryAttempts}/${this.maxRetryAttempts}: ${error.message}`);
            this.updateConnectionStatus('connecting', `재시도 중... (${this.retryAttempts}/${this.maxRetryAttempts})`);
            
            // 3초 후 재시도
            setTimeout(() => {
                this.fetchData();
            }, 3000);
        } else {
            console.error('💔 최대 재시도 횟수 초과');
            this.updateConnectionStatus('disconnected', '연결 실패');
            this.showToast('데이터를 불러올 수 없습니다. 잠시 후 다시 시도하세요.', 'error');
        }
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
                    aVal = parseFloat(a.spot_volume) * parseFloat(a.spot_price);
                    bVal = parseFloat(b.spot_volume) * parseFloat(b.spot_price);
                    break;
                case 'futures_volume':
                    aVal = parseFloat(a.futures_volume) * parseFloat(a.futures_price);
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
    
    updateConnectionStatus(status, message) {
        this.elements.connectionStatus.className = `connection-status ${status}`;
        this.elements.connectionStatus.querySelector('span').textContent = message;
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
            
            // 애니메이션 지연
            setTimeout(() => {
                row.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, index * 20);
        });
    }
    
    updateStats(basisData) {
        if (basisData.length === 0) return;
        
        // 베이시스 퍼센트 기준으로 정렬하여 최고값 찾기
        const sortedByBasis = [...basisData].sort((a, b) => b.basis_percent - a.basis_percent);
        const maxBasisItem = sortedByBasis[0];
        
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

// CSS 스타일 추가 (새로고침 아이콘 애니메이션)
const style = document.createElement('style');
style.textContent = `
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.refresh-icon {
    transition: transform 0.2s ease;
}

.refresh-icon:hover {
    transform: scale(1.1);
}
`;
document.head.appendChild(style);

// 문서 로드 완료 시 모니터 시작
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 문서 로드 완료, 베이시스 모니터 시작 (HTTP Polling 모드)');
    new BasisMonitor();
});