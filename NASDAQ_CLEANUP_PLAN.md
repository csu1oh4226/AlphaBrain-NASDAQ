# NASDAQ 관련 코드 정리 계획

## 📋 삭제 대상 파일 목록

### 1. 완전 삭제 대상 파일

#### 데이터 파일
- `nasdaq_tickers.csv` - NASDAQ 티커 리스트 (AAPL, MSFT 등)

#### Provider 파일 (NASDAQ 전용)
- `src/nasdaq_scanner/providers/stooq_provider.py` - NASDAQ-100 (^NDX) 전용 provider
- `src/nasdaq_scanner/providers/yfinance_provider.py` - yfinance는 주로 NASDAQ/US 주식용

#### 테스트 파일
- `tests/unit/test_stooq_provider.py` - StooqProvider 테스트
- `tests/unit/test_yfinance_provider.py` - YFinanceProvider 테스트

#### 문서 파일
- `docs/yfinance_provider_failure_policy.md` - yfinance 관련 문서
- `YFINANCE_INTEGRATION_PLAN.md` - yfinance 통합 계획

### 2. 코드에서 제거할 부분 (파일은 유지)

#### `src/nasdaq_scanner/providers/data_collector.py`
- `get_nasdaq100_tickers()` 함수 전체 제거
- NASDAQ-100 관련 로직 제거 (170-174줄)
- YFinanceProvider, StooqProvider import 제거

#### `src/nasdaq_scanner/providers/__init__.py`
- YFinanceProvider, StooqProvider export 제거
- get_nasdaq100_tickers export 제거

#### `src/nasdaq_scanner/config.py`
- `TICKER_SOURCE_NASDAQ100` 상수 제거

#### `app.py`
- TICKER_SOURCE_NASDAQ100 import 제거
- NASDAQ-100 관련 UI 옵션 제거 (113-117줄)
- README 사용 방법에서 NASDAQ-100 언급 제거

#### `README.md`
- NASDAQ 관련 설명을 KOSPI/KOSDAQ으로 변경

## 🛑 유지할 파일 (공통 유틸)

- 모든 core 모듈 (analysis_functions, metrics, ranking 등)
- UI 컴포넌트 (components.py)
- 설정 파일 (requirements.txt, pyproject.toml 등)
- 테스트 프레임워크
- FinanceDataReaderProvider (KOSPI/KOSDAQ용)

## 📝 삭제 이유 요약

1. **stooq_provider.py**: NASDAQ-100 (^NDX) 전용으로 작성됨
2. **yfinance_provider.py**: 주로 미국 주식 시장용, KOSPI/KOSDAQ은 FinanceDataReader 사용
3. **nasdaq_tickers.csv**: NASDAQ 티커 리스트
4. **get_nasdaq100_tickers()**: NASDAQ-100 하드코딩 리스트
5. **관련 테스트/문서**: 위 provider들에 대한 테스트 및 문서

