# Streamlit 대시보드 프로젝트 구조

## 📁 파일 구조

```
AlphaBrain-NASDAQ/
├── app.py                              # 🎯 Streamlit 메인 앱 (진입점)
├── nasdaq_tickers.csv                  # 티커 유니버스 파일 (예시)
│
├── src/
│   └── nasdaq_scanner/
│       ├── __init__.py
│       ├── cli.py                      # CLI (run_analysis 함수 - 결과 반환 지원)
│       │
│       ├── core/                       # 핵심 비즈니스 로직 (순수 함수)
│       │   ├── __init__.py
│       │   ├── metrics.py              # ✅ 일간 수익률, 변동성 계산
│       │   ├── ranking.py              # ✅ 상승/하락/변동성 TOP N
│       │   ├── signals.py              # ✅ 규칙 기반 신호 생성
│       │   ├── universe.py             # ✅ 티커 리스트 로드
│       │   └── recommender.py          # 🆕 매수/매도 추천 모듈
│       │
│       ├── providers/                  # 외부 API 어댑터
│       │   ├── __init__.py
│       │   └── data_provider.py        # ✅ yfinance 가격 데이터 수집
│       │
│       └── reporter/                   # 리포트 생성
│           ├── __init__.py
│           └── report.py              # 마크다운 리포트 생성
│
├── tests/
│   ├── test_streamlit.py               # 🆕 Streamlit 앱 테스트
│   ├── unit/                           # 기존 단위 테스트
│   └── integration/                    # 기존 통합 테스트
│
├── requirements.txt                    # 의존성 (streamlit 추가됨)
├── README_STREAMLIT.md                 # 🆕 Streamlit 사용 가이드
└── STREAMLIT_PROJECT_STRUCTURE.md      # 🆕 이 파일
```

## 🔄 데이터 흐름

```
사용자 입력 (Streamlit UI)
    ↓
app.py
    ↓
run_analysis() [cli.py]
    ↓
┌─────────────────────────────────────┐
│ 1. 데이터 수집                      │
│    - universe.py: 티커 로드         │
│    - data_provider.py: 가격 데이터   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. 분석 모듈                        │
│    - metrics.py: 수익률/변동성 계산  │
│    - ranking.py: TOP N 추출         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. 추천 모듈                        │
│    - recommender.py: 매수/매도 추천 │
│      (signals.py 사용)              │
└─────────────────────────────────────┘
    ↓
결과 반환 (Dict)
    ↓
Streamlit UI 표시
```

## 📦 모듈 설명

### 1. 데이터 수집 모듈

#### `core/universe.py`
- **기능**: CSV 파일에서 티커 리스트 로드
- **함수**: `load_tickers(path: str) -> List[str]`
- **특징**: 
  - 공백 제거, 대문자 변환, 중복 제거
  - 빈 줄 무시

#### `providers/data_provider.py`
- **기능**: yfinance를 통한 OHLCV 데이터 수집
- **함수**: `fetch_ohlcv_batch(symbols, target_date) -> DataFrame`
- **특징**:
  - 배치 처리
  - 재시도 로직
  - 부분 실패 허용

### 2. 분석 모듈

#### `core/metrics.py`
- **기능**: 금융 지표 계산
- **함수**:
  - `calc_return_pct(df) -> DataFrame`: 일간 수익률 계산
  - `calc_intraday_vol_pct(df) -> DataFrame`: 일중 변동성 계산
- **출력 컬럼**: `return_pct`, `vol_pct`

#### `core/ranking.py`
- **기능**: TOP N 랭킹 추출
- **함수**:
  - `top_n(df, col, n) -> DataFrame`: 상위 N개
  - `bottom_n(df, col, n) -> DataFrame`: 하위 N개
- **특징**: 안정 정렬 + 티커 알파벳 순 2차 정렬

### 3. 추천 모듈

#### `core/recommender.py` 🆕
- **기능**: 규칙 기반 매수/매도 추천
- **함수**:
  - `generate_recommendations(analysis_df, ...) -> Dict`
  - `get_default_buy_rules() -> List[Dict]`
  - `get_default_sell_rules() -> List[Dict]`
  - `format_reasons(reasons, rules) -> str`
- **규칙 구조**:
  ```python
  {
      'name': str,           # 규칙 이름
      'condition': Callable,  # 조건 함수 (row -> bool)
      'action': str,         # 'buy', 'sell', 'watch'
      'description': str     # 규칙 설명
  }
  ```

#### `core/signals.py`
- **기능**: 규칙을 DataFrame에 적용하여 신호 생성
- **함수**: `generate_signals(df, rules) -> DataFrame`
- **출력**: `signal`, `reasons` 컬럼 추가

### 4. Streamlit UI

#### `app.py` 🆕
- **구조**:
  - 사이드바: 입력 파라미터
  - 메인 영역: 5개 탭
    - 상위 종목
    - 하위 종목
    - 변동성
    - 매수 추천
    - 매도/주의
- **주요 기능**:
  - 파일 업로드
  - 날짜 선택
  - 실시간 분석
  - 테이블 및 차트 표시

### 5. CLI 통합

#### `cli.py` (수정됨)
- **변경사항**: `run_analysis()` 함수에 `return_results` 파라미터 추가
- **반환값**: `Dict[str, Any]` (GUI용)
  ```python
  {
      'top_movers': DataFrame,
      'bottom_movers': DataFrame,
      'volatile_movers': DataFrame,
      'analysis_df': DataFrame,
      'analysis_date': date,
      'stats': {
          'total_symbols': int,
          'successful_fetches': int,
          'failed_fetches': int
      }
  }
  ```

## 🧪 테스트 구조

### `tests/test_streamlit.py`
- **TestRecommender**: 추천 모듈 단위 테스트
  - 기본 규칙 테스트
  - 추천 생성 테스트
  - 커스텀 규칙 테스트
- **TestStreamlitIntegration**: Streamlit 통합 테스트
  - `run_analysis` 결과 반환 테스트

## 🚀 실행 방법

### 개발 모드

```bash
# 의존성 설치
pip install -r requirements.txt

# Streamlit 앱 실행
streamlit run app.py
```

### 프로덕션 배포

```bash
# Streamlit Cloud에 배포
# 또는 자체 서버에 배포
streamlit run app.py --server.port 8501
```

## 📝 주요 변경사항

### 새로 추가된 파일
1. `app.py`: Streamlit 메인 앱
2. `src/nasdaq_scanner/core/recommender.py`: 추천 모듈
3. `tests/test_streamlit.py`: Streamlit 테스트
4. `README_STREAMLIT.md`: 사용 가이드

### 수정된 파일
1. `src/nasdaq_scanner/cli.py`: `run_analysis()` 결과 반환 지원
2. `requirements.txt`: `streamlit>=1.28.0` 추가

## 🔧 확장 포인트

### 1. 추천 규칙 추가
- `recommender.py`의 `get_default_buy_rules()` / `get_default_sell_rules()` 수정

### 2. UI 개선
- `app.py`에서 Streamlit 컴포넌트 추가/수정
- 차트 라이브러리 추가 (plotly 등)

### 3. 데이터 소스 확장
- `providers/`에 새로운 데이터 제공자 추가
- 캐싱 메커니즘 추가

### 4. 성능 최적화
- 병렬 다운로드
- 결과 캐싱
- 증분 업데이트

---

**작성일:** 2024

