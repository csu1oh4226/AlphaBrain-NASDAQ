# yfinance 통합 계획

## 1. 현재 파일 트리 및 엔트리포인트 요약

### 파일 트리
```
.
├── app.py                                    # Streamlit GUI 엔트리포인트
├── src/nasdaq_scanner/
│   ├── cli.py                                # CLI 엔트리포인트
│   ├── providers/
│   │   ├── base.py                           # MarketDataProvider 인터페이스
│   │   ├── yfinance_provider.py             # ✅ yfinance 구현 (새 구조)
│   │   ├── data_collector.py                 # ✅ 고수준 수집 인터페이스
│   │   └── data_provider.py                  # ⚠️ 레거시 구현 (CLI에서 사용)
│   ├── services/
│   │   └── analytics_service.py             # 분석 서비스 (GUI에서 사용)
│   └── core/                                 # 핵심 분석 로직
└── tests/
    ├── unit/
    └── integration/
```

### 엔트리포인트 (실행 커맨드)

1. **CLI:**
   ```bash
   python -m nasdaq_scanner.cli --date 2024-01-15 --universe nasdaq_tickers.csv --n 10
   # 또는
   nasdaq-scanner --date 2024-01-15 --universe nasdaq_tickers.csv --n 10
   ```
   - 엔트리포인트: `src/nasdaq_scanner/cli.py::main()`
   - 현재 사용: `data_provider.py::fetch_ohlcv_batch()` (레거시)

2. **GUI (Streamlit):**
   ```bash
   streamlit run app.py
   ```
   - 엔트리포인트: `app.py`
   - 현재 사용: `services/analytics_service.py` → `data_collector.py` → `YFinanceProvider` (새 구조)

## 2. 레이어 위치

### 데이터 수집 레이어
- **위치**: `src/nasdaq_scanner/providers/`
- **구성**:
  - `base.py`: `MarketDataProvider` 인터페이스 (ABC)
  - `yfinance_provider.py`: yfinance 구현체 (✅ 새 구조)
  - `data_collector.py`: 고수준 수집 함수 `collect_data()` (✅ 새 구조)
  - `data_provider.py`: 레거시 함수 `fetch_ohlcv_batch()` (⚠️ CLI에서만 사용)

### 분석 레이어
- **위치**: 
  - `src/nasdaq_scanner/core/`: 순수 함수 (metrics, ranking, analytics 등)
  - `src/nasdaq_scanner/services/`: 비즈니스 로직 오케스트레이션
- **사용처**:
  - CLI: 직접 `core/` 함수 사용
  - GUI: `services/analytics_service.py` 사용

### GUI 레이어
- **위치**: 
  - `app.py`: Streamlit 메인 앱
  - `src/nasdaq_scanner/ui/components.py`: 재사용 가능한 UI 컴포넌트
- **데이터 흐름**: `app.py` → `services/analytics_service.py` → `providers/data_collector.py` → `YFinanceProvider`

## 3. 문제점

### 현재 상황
- **CLI**: 레거시 `data_provider.py::fetch_ohlcv_batch()` 사용
- **GUI**: 새 구조 `YFinanceProvider` 사용
- **결과**: 두 경로가 다른 구현을 사용하여 일관성 부족

### 데이터 형식 차이
- `data_provider.py`: `(symbol, date, Open, High, Low, Close, Volume)` 반환
- `YFinanceProvider`: `(ticker, date, close, volume)` 반환 (소문자, 일부 컬럼만)
- CLI는 `Open, High, Low, Close`를 필요로 함

## 4. 최소 변경 파일 3개 제안

### 변경 1: `src/nasdaq_scanner/cli.py`
**목적**: 레거시 `fetch_ohlcv_batch` 대신 새 구조 `collect_data` 사용

**변경 내용**:
- `from nasdaq_scanner.providers.data_provider import fetch_ohlcv_batch` 제거
- `from nasdaq_scanner.providers import collect_data` 추가
- `fetch_ohlcv_batch(symbols, analysis_date)` → `collect_data(symbols, analysis_date)` 변경
- 반환값 형식 조정 (컬럼명: `symbol` → `symbol`, `Open/High/Low/Close` 확인 필요)

**영향 범위**: CLI 실행 경로만 변경, 동작 유지

### 변경 2: `src/nasdaq_scanner/providers/yfinance_provider.py`
**목적**: CLI가 필요로 하는 OHLCV 컬럼 모두 반환하도록 확장

**변경 내용**:
- `fetch_price_data()` 반환값에 `Open, High, Low, Close` 컬럼 추가
- 현재 `close`만 반환하는 것을 `Open, High, Low, Close, Volume` 모두 반환하도록 수정
- 컬럼명 통일: `ticker` → `symbol` (또는 둘 다 지원)

**영향 범위**: 데이터 형식 확장, 기존 GUI 코드와 호환성 유지

### 변경 3: `tests/integration/test_yfinance_integration.py` (신규)
**목적**: yfinance 통합 테스트 추가

**테스트 내용**:
- `YFinanceProvider`가 올바른 OHLCV 데이터를 반환하는지 확인
- `collect_data`가 CLI에서 사용 가능한 형식으로 데이터를 반환하는지 확인
- 실패한 티커 처리 확인
- 네트워크 오류 처리 확인 (mock 사용)

**테스트 전략**:
- 실제 yfinance 호출은 최소화 (느린 테스트)
- Mock을 사용한 단위 테스트 우선
- 통합 테스트는 `@pytest.mark.slow` 마커 사용

## 5. 변경 순서 및 주의사항

### 단계별 실행
1. **테스트 먼저 작성** (TDD)
   - `test_yfinance_integration.py` 작성
   - 기대 동작 정의

2. **yfinance_provider.py 확장**
   - OHLCV 컬럼 모두 반환하도록 수정
   - 기존 테스트 통과 확인

3. **cli.py 변경**
   - `collect_data` 사용하도록 변경
   - 통합 테스트 통과 확인

### 주의사항
- **컬럼명 통일**: `symbol` vs `ticker` → `symbol`로 통일 권장
- **하위 호환성**: 기존 GUI 코드가 깨지지 않도록 주의
- **에러 처리**: 네트워크 오류 시 기존과 동일한 동작 유지
- **테스트 커버리지**: 변경된 코드에 대한 테스트 필수

## 6. 예상 결과

### 변경 후
- CLI와 GUI가 동일한 `YFinanceProvider` 사용
- 코드 중복 제거 (`data_provider.py` deprecated 또는 제거 가능)
- 일관된 데이터 형식
- 테스트 커버리지 향상

### 장기적 이점
- 단일 데이터 소스로 유지보수 용이
- Provider 교체 시 한 곳만 수정
- 테스트 용이성 향상

