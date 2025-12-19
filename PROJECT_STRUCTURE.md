# 프로젝트 구조 가이드

## 디렉토리 구조

```
AlphaBrain-NASDAQ/
├── src/                          # 소스 코드
│   └── nasdaq_scanner/           # 메인 패키지
│       ├── __init__.py
│       ├── cli.py                # CLI 엔트리 포인트
│       ├── core/                 # 핵심 비즈니스 로직 (순수 함수)
│       │   ├── __init__.py
│       │   ├── universe.py       # 종목 유니버스 관리
│       │   ├── analyzer.py       # 변동성/등락률 계산 (순수 함수)
│       │   ├── ranker.py         # Top 10 랭킹 (순수 함수)
│       │   └── recommender.py    # Watchlist 제안 (순수 함수)
│       ├── providers/            # 외부 API 어댑터 (의존성 주입)
│       │   ├── __init__.py
│       │   ├── base.py           # Provider 인터페이스 (ABC)
│       │   ├── yfinance.py       # yfinance 어댑터 구현
│       │   └── mock.py           # 테스트용 Mock Provider
│       ├── storage/              # 데이터 저장소
│       │   ├── __init__.py
│       │   ├── cache.py          # 캐시 관리 (SQLite/파일)
│       │   └── exporter.py        # CSV/DB export
│       └── reporter/              # 리포트 생성
│           ├── __init__.py
│           └── formatter.py      # 콘솔/CSV/HTML 리포트
│
├── tests/                        # 테스트 코드
│   ├── __init__.py
│   ├── conftest.py               # 공통 fixtures
│   ├── unit/                     # 단위 테스트
│   │   ├── __init__.py
│   │   ├── test_example.py
│   │   ├── test_analyzer.py      # analyzer 순수 함수 테스트
│   │   ├── test_ranker.py        # ranker 순수 함수 테스트
│   │   └── test_recommender.py   # recommender 순수 함수 테스트
│   ├── integration/              # 통합 테스트
│   │   ├── __init__.py
│   │   ├── test_provider.py      # Provider 어댑터 테스트
│   │   └── test_pipeline.py      # 전체 파이프라인 테스트
│   └── fixtures/                 # 테스트 데이터
│       ├── __init__.py
│       └── sample_data.py        # 샘플 OHLCV 데이터
│
├── pyproject.toml                # 프로젝트 설정 (의존성, pytest, ruff, black, mypy)
├── requirements.txt              # 프로덕션 의존성
├── requirements-dev.txt          # 개발 의존성
├── pytest.ini                    # pytest 설정
├── Makefile                      # 개발 명령어
├── .editorconfig                 # 에디터 설정
├── .gitignore                    # Git 무시 파일
├── .env.example                  # 환경 변수 예시
├── README.md                     # 프로젝트 소개
├── PRD.md                        # 제품 요구사항 문서
└── PROJECT_STRUCTURE.md          # 이 파일
```

## 아키텍처 원칙

### 1. 순수 함수 중심 설계

**`core/` 모듈의 모든 함수는 순수 함수로 작성:**

```python
# ✅ 좋은 예: 순수 함수
def calculate_pct_change(open_price: float, close_price: float) -> float:
    """순수 함수: 입력에 대해 항상 동일한 출력"""
    return (close_price - open_price) / open_price * 100

# ❌ 나쁜 예: 부작용이 있는 함수
def fetch_and_calculate(symbol: str) -> float:
    """외부 API 호출이 포함된 함수"""
    data = yfinance.download(symbol)  # 부작용!
    return calculate_pct_change(...)
```

### 2. 어댑터 패턴으로 외부 의존성 분리

**`providers/` 모듈은 인터페이스 기반:**

```python
# providers/base.py
from abc import ABC, abstractmethod

class MarketDataProvider(ABC):
    @abstractmethod
    def get_daily_ohlcv(self, symbol: str, date: date) -> OHLCV:
        """일봉 데이터 조회"""
        pass

# providers/yfinance.py
class YFinanceProvider(MarketDataProvider):
    def get_daily_ohlcv(self, symbol: str, date: date) -> OHLCV:
        # yfinance 구현
        pass

# providers/mock.py (테스트용)
class MockProvider(MarketDataProvider):
    def get_daily_ohlcv(self, symbol: str, date: date) -> OHLCV:
        # Mock 데이터 반환
        pass
```

### 3. 의존성 주입

**Provider는 함수 인자로 주입:**

```python
# core/analyzer.py
def analyze_symbol(
    symbol: str,
    ohlcv_data: OHLCV,
    provider: MarketDataProvider  # 의존성 주입
) -> AnalysisResult:
    """Provider를 인자로 받아 사용"""
    # 순수 함수로 계산
    pct_change = calculate_pct_change(ohlcv_data.open, ohlcv_data.close)
    # ...
```

### 4. 테스트 전략

**단위 테스트: 순수 함수만 테스트 (Mock 불필요)**
```python
# tests/unit/test_analyzer.py
def test_calculate_pct_change():
    result = calculate_pct_change(100.0, 105.0)
    assert result == 5.0
```

**통합 테스트: Provider 어댑터 테스트 (Mock Provider 사용)**
```python
# tests/integration/test_provider.py
def test_yfinance_provider(mock_provider):
    result = mock_provider.get_daily_ohlcv("AAPL", date(2024, 1, 15))
    assert result.symbol == "AAPL"
```

## 개발 가이드라인

### 파일 작성 순서

1. **인터페이스 정의** (`providers/base.py`)
2. **순수 함수 구현** (`core/analyzer.py`, `core/ranker.py`)
3. **단위 테스트 작성** (`tests/unit/test_*.py`)
4. **어댑터 구현** (`providers/yfinance.py`)
5. **통합 테스트 작성** (`tests/integration/test_*.py`)

### 코딩 스타일

- **타입 힌트 필수**: 모든 함수에 타입 힌트 추가
- **Docstring 작성**: Google 스타일 또는 NumPy 스타일
- **함수 길이**: 한 함수당 50줄 이하 권장
- **순수 함수 우선**: 가능한 한 부작용 없는 함수 작성

### 테스트 작성 규칙

- **단위 테스트**: `tests/unit/`에 순수 함수 테스트
- **통합 테스트**: `tests/integration/`에 Provider/파이프라인 테스트
- **Fixture 사용**: `conftest.py`에 공통 fixture 정의
- **Mock 사용**: 외부 API 호출은 반드시 mock/stub으로 대체

## 다음 단계

1. ✅ 프로젝트 스캐폴딩 완료
2. ⏭️ Provider 인터페이스 정의 (`providers/base.py`)
3. ⏭️ 데이터 모델 정의 (Pydantic models)
4. ⏭️ 순수 함수 구현 (`core/analyzer.py`, `core/ranker.py`)
5. ⏭️ yfinance 어댑터 구현 (`providers/yfinance.py`)
6. ⏭️ CLI 구현 (`cli.py`)

