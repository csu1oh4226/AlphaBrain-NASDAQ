# NASDAQ Daily Movers & Volatility Analyzer

NASDAQ 상장 종목의 당일 주가 데이터를 수집하여 변동성 및 등락률 상위 종목을 분석하고, 규칙 기반으로 관심 매수/매도 후보를 생성하는 도구입니다.

## 📋 개요

이 프로젝트는 NASDAQ 상장 종목의 일일 주가 데이터를 분석하여:
- 일중 변동성(Volatility) 상위 종목 10개
- 상승률 상위 10개
- 하락률 상위 10개

를 산출하고, 규칙 기반으로 **"오늘의 관심 매수 후보 10개 / 관심 매도(주의) 후보 10개"**를 자동 생성합니다.

## ⚠️ 면책 조항

**이 도구는 투자 자문이 아닙니다.** 모든 분석 결과는 참고용이며, 투자 결정은 사용자의 판단에 따라 이루어져야 합니다. 데이터 제공사의 약관을 준수하며 사용하시기 바랍니다.

## 🚀 시작하기

### 필수 요구사항

- Python 3.10 이상
- API 키 (Polygon, IEX Cloud, Alpha Vantage 등)

### 설치 방법

```bash
# 저장소 클론
git clone https://github.com/csu1oh4226/AlphaBrain-NASDAQ.git
cd AlphaBrain-NASDAQ

# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 의존성 포함 설치
pip install -r requirements-dev.txt

# 또는 편집 가능 모드로 설치
pip install -e ".[dev]"
```

### 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 API 키를 설정하세요.

```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

## 📖 사용 방법

```bash
# CLI 실행 (구현 예정)
nasdaq-scanner --date 2024-01-15

# 또는 Python 모듈로 실행
python -m nasdaq_scanner.cli --date 2024-01-15
```

## 📁 프로젝트 구조

```
.
├── src/
│   └── nasdaq_scanner/
│       ├── __init__.py
│       ├── cli.py              # CLI 엔트리 포인트
│       ├── core/                # 핵심 분석 로직 (순수 함수)
│       │   ├── universe.py      # 유니버스 관리
│       │   ├── analyzer.py      # 변동성/등락률 계산
│       │   ├── ranker.py        # Top 10 랭킹
│       │   └── recommender.py   # Watchlist 제안
│       ├── providers/            # 외부 API 어댑터 (yfinance 등)
│       │   ├── base.py          # Provider 인터페이스
│       │   ├── yfinance.py      # yfinance 어댑터
│       │   └── mock.py          # 테스트용 Mock Provider
│       ├── storage/              # 저장소 및 캐시
│       │   ├── cache.py         # SQLite/파일 캐시
│       │   └── exporter.py      # CSV/DB export
│       └── reporter/             # 리포트 생성
│           └── formatter.py      # 콘솔/CSV/HTML 리포트
├── tests/
│   ├── conftest.py              # 공통 fixtures
│   ├── unit/                    # 단위 테스트
│   ├── integration/             # 통합 테스트
│   └── fixtures/                # 테스트 데이터
├── pyproject.toml               # 프로젝트 설정 (의존성, pytest 등)
├── requirements.txt             # 프로덕션 의존성
├── requirements-dev.txt         # 개발 의존성
└── pytest.ini                   # pytest 설정
```

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src/nasdaq_scanner --cov-report=html

# 특정 마커만 실행
pytest -m unit              # 단위 테스트만
pytest -m integration       # 통합 테스트만
pytest -m "not slow"        # 느린 테스트 제외
```

## 🛠️ 개발 워크플로우

```bash
# 코드 포맷팅
make format
# 또는
black src/ tests/
ruff check --fix src/ tests/

# 린팅
make lint
# 또는
ruff check src/ tests/

# 타입 체크
make type-check
# 또는
mypy src/

# 모든 검사 실행
make lint && make type-check && make test
```

## 🏗️ 아키텍처 원칙

- **순수 함수 중심**: 비즈니스 로직은 순수 함수로 작성 (부작용 최소화)
- **어댑터 패턴**: 외부 API 호출(yfinance 등)은 어댑터로 분리
- **테스트 가능성**: 모든 외부 의존성은 mock/stub으로 대체 가능
- **의존성 주입**: Provider는 인터페이스 기반으로 주입

## 📝 문서

자세한 요구사항은 [PRD.md](PRD.md)를 참고하세요.

## 🤝 기여하기

이슈 및 Pull Request를 환영합니다!

## 📄 라이선스

[라이선스 정보 추가]

## 🔗 참고 자료

- [PRD 문서](PRD.md)
- NASDAQ 공식 문서
- Provider API 문서 (Polygon, IEX Cloud 등)

