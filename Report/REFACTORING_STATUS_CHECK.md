# [1단계] 현재 상태 점검 리포트

## 📁 프로젝트 트리 요약

### 주요 모듈 구조
```
.
├── app.py                          # Streamlit 메인 엔트리포인트 (691줄)
├── src/nasdaq_scanner/
│   ├── __init__.py                 # 패키지 초기화
│   ├── cli.py                      # CLI 엔트리포인트 (레거시, 미사용)
│   ├── config.py                   # 설정 상수 (79줄)
│   ├── core/                       # 핵심 분석 로직 (순수 함수)
│   │   ├── analysis_functions.py  # 수익률/변동성 계산 (285줄)
│   │   ├── analytics.py             # 레거시 분석 모듈
│   │   ├── korea_universe.py       # KOSPI/KOSDAQ 유니버스 관리
│   │   ├── kosdaq_universe.py      # 레거시 (중복 가능성)
│   │   ├── metrics.py              # 레거시 메트릭 모듈
│   │   ├── ranking.py              # 레거시 랭킹 모듈
│   │   ├── recommender.py          # 레거시 추천 모듈
│   │   ├── signal_generator.py     # 레거시 시그널 생성기
│   │   ├── signals.py              # 시그널 생성 (활성)
│   │   ├── stock_name_mapper.py    # 종목명 매핑
│   │   └── universe.py             # 유니버스 관리
│   ├── providers/                   # 데이터 수집 레이어
│   │   ├── base.py                 # MarketDataProvider 인터페이스
│   │   ├── data_collector.py       # 데이터 수집 오케스트레이션 (158줄)
│   │   ├── data_provider.py        # 레거시 (yfinance, 미사용)
│   │   ├── fetch_ohlcv.py          # 레거시 (yfinance, 미사용)
│   │   └── financedatareader_provider.py  # FinanceDataReader 구현 (활성)
│   ├── services/                   # 서비스 레이어
│   │   ├── analytics_service.py    # 분석 서비스 (258줄)
│   │   └── recommendation_service.py  # 추천 서비스 (레거시)
│   ├── reporter/                   # 리포트 생성
│   │   └── report.py               # 마크다운 리포트
│   └── ui/                         # UI 컴포넌트
│       └── components.py           # 재사용 가능한 UI 컴포넌트
└── tests/
    ├── unit/                       # 단위 테스트
    └── integration/                # 통합 테스트
```

### 엔트리포인트
- **메인**: `app.py` (Streamlit 앱)
- **CLI**: `src/nasdaq_scanner/cli.py` (레거시, 미사용)

## 🚀 실행 방법

### Streamlit 앱 실행
```bash
streamlit run app.py
# 또는
python -m streamlit run app.py
```

### 테스트 실행
```bash
# 전체 테스트
pytest

# 단위 테스트만
pytest tests/unit/

# 통합 테스트만
pytest tests/integration/

# 커버리지 포함
pytest --cov=src/nasdaq_scanner --cov-report=html
```

### 환경 변수/설정 파일
- **설정 파일**: `src/nasdaq_scanner/config.py` (모든 상수 중앙 관리)
- **환경 변수**: 없음 (FinanceDataReader는 API 키 불필요)
- **임시 파일**: `temp_universe.csv` (CSV 업로드 시 생성)

## ✅ 문법/타입/임포트 오류 확인

### Linter 결과
- ✅ **Linter 오류 없음** (`read_lints` 확인 완료)

### 잠재적 문제
1. **레거시 모듈**: `core/`에 중복 기능 모듈 다수 존재
   - `analytics.py`, `metrics.py`, `ranking.py`, `recommender.py`, `signal_generator.py`
   - 현재 사용되는 모듈: `analysis_functions.py`, `signals.py`
   
2. **미사용 파일**: 
   - `cli.py` (data_provider 사용, 현재 미사용)
   - `data_provider.py` (yfinance 기반, 미사용)
   - `fetch_ohlcv.py` (yfinance 기반, 미사용)
   - `app_streamlit.py` (중복 파일?)

3. **중복 함수**: `app.py`에 `format_number` 함수가 2번 정의됨 (275줄, 522줄)

## 🧪 테스트 상태

### 테스트 파일 목록
- `tests/unit/test_analysis_functions.py`
- `tests/unit/test_analytics.py`
- `tests/unit/test_data_collection_failure.py`
- `tests/unit/test_fetch_ohlcv.py`
- `tests/unit/test_financedatareader_provider.py`
- `tests/unit/test_generate_signals.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_multiple_stocks_collection.py`
- `tests/unit/test_ranking.py`
- `tests/unit/test_report.py`
- `tests/unit/test_signals.py`
- `tests/unit/test_stock_name_mapper.py`
- `tests/unit/test_universe.py`
- `tests/integration/test_analytics_service_e2e.py`
- `tests/integration/test_smoke.py`

### 테스트 실행 결과
- 테스트 수집 명령 실행 시도했으나 취소됨
- **다음 단계에서 전체 테스트 실행 필요**

## 📊 코드 통계 (예상)

- **총 파일 수**: 약 30개 Python 파일
- **주요 파일 크기**:
  - `app.py`: 691줄
  - `analytics_service.py`: 258줄
  - `analysis_functions.py`: 285줄
  - `data_collector.py`: 158줄
  - `financedatareader_provider.py`: 약 400줄

## ⚠️ 초기 발견된 문제점

1. **중복 함수**: `app.py`의 `format_number` 중복 정의
2. **레거시 모듈**: `core/`에 사용되지 않는 모듈 다수
3. **미사용 파일**: `data_provider.py`, `fetch_ohlcv.py`, `cli.py`
4. **중복 파일**: `app_streamlit.py` vs `app.py`
5. **하드코딩**: `app.py`에 매직 넘버 일부 존재 (예: `top_n * 2`)

## 🔄 다음 단계

2단계로 진행하여 Code Smell 및 SOLID 진단 리포트 작성 예정.

