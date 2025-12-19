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
├── app.py                        # Streamlit 대시보드 (UI 레이어)
├── src/
│   └── nasdaq_scanner/
│       ├── __init__.py
│       ├── cli.py                # CLI 엔트리 포인트
│       ├── config.py              # 설정 상수 (매직넘버)
│       ├── core/                  # 핵심 분석 로직 (순수 함수)
│       │   ├── universe.py        # 유니버스 관리
│       │   ├── metrics.py         # 수익률/변동성 계산
│       │   ├── analytics.py       # 일일 수익률, 변동성, 랭킹
│       │   ├── ranking.py         # Top N 랭킹
│       │   ├── signals.py         # 규칙 기반 신호 생성
│       │   └── recommender.py     # 추천 모듈
│       ├── providers/             # 데이터 수집 레이어
│       │   ├── base.py            # Provider 인터페이스
│       │   ├── yfinance_provider.py  # yfinance 구현
│       │   ├── data_collector.py  # 데이터 수집 모듈
│       │   └── data_provider.py   # 레거시 (호환성)
│       ├── services/              # 서비스 레이어 (비즈니스 로직)
│       │   ├── analytics_service.py    # 분석 서비스
│       │   └── recommendation_service.py # 추천 서비스
│       ├── ui/                    # UI 컴포넌트 레이어
│       │   └── components.py      # 재사용 가능한 UI 컴포넌트
│       ├── reporter/              # 리포트 생성
│       │   └── report.py          # 마크다운 리포트
│       └── storage/               # 저장소 (향후 확장)
├── tests/
│   ├── conftest.py               # 공통 fixtures
│   ├── unit/                      # 단위 테스트
│   └── integration/               # 통합 테스트
├── pyproject.toml                 # 프로젝트 설정
├── requirements.txt               # 프로덕션 의존성
└── requirements-dev.txt          # 개발 의존성
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

### 레이어 분리

프로젝트는 다음과 같은 레이어로 구성됩니다:

1. **UI 레이어** (`app.py`, `ui/`)
   - Streamlit 기반 사용자 인터페이스
   - 재사용 가능한 UI 컴포넌트
   - 사용자 입력 처리

2. **서비스 레이어** (`services/`)
   - 비즈니스 로직 오케스트레이션
   - 데이터 수집, 분석, 추천 생성 조율
   - 캐싱 및 성능 최적화

3. **데이터 수집 레이어** (`providers/`)
   - 외부 API 어댑터 (yfinance 등)
   - 인터페이스 기반 설계 (교체 가능)
   - 에러 처리 및 재시도 로직

4. **핵심 로직 레이어** (`core/`)
   - 순수 함수 중심 설계
   - 부작용 없는 비즈니스 로직
   - 테스트 용이성

### 설계 결정 (Design Decisions)

#### 1. 레이어 분리
- **이유**: 관심사 분리, 테스트 용이성, 유지보수성 향상
- **구현**: UI, Service, Data Collection, Core 로직 분리

#### 2. 인터페이스 기반 Provider
- **이유**: 데이터 소스 교체 용이성
- **구현**: `MarketDataProvider` 추상 클래스

#### 3. 상수 분리
- **이유**: 매직넘버 제거, 설정 관리 용이
- **구현**: `config.py`에 모든 상수 정의

#### 4. 순수 함수 중심
- **이유**: 테스트 용이성, 예측 가능성, 재사용성
- **구현**: `core/` 모듈의 모든 함수는 순수 함수

#### 5. 캐싱 전략
- **이유**: 반복 요청 시 성능 향상
- **구현**: Streamlit `@st.cache_data` 사용

### TODO (향후 개선 사항)

#### High Priority
- [ ] 캐싱 메커니즘 구현 (SQLite/파일 기반)
- [ ] 병렬 다운로드 구현 (concurrent.futures)
- [ ] 휴장일 처리 강화 (pandas_market_calendars)
- [ ] 재시도 로직 개선 (지수 백오프)

#### Medium Priority
- [ ] 데이터 검증 강화 (OHLCV 일관성)
- [ ] 설정 파일 관리 (YAML/TOML)
- [ ] 로깅 개선 (구조화된 로깅)
- [ ] 성능 모니터링 (각 단계별 실행 시간)

#### Low Priority
- [ ] 에러 복구 전략 (부분 결과 저장)
- [ ] 문서화 개선 (Sphinx API 문서)
- [ ] 추가 데이터 제공자 (Polygon, IEX Cloud)
- [ ] 실시간 업데이트 (WebSocket 지원)

## 📊 Signal Rules (시그널 규칙)

이 도구는 규칙 기반 시그널 생성 방식을 사용합니다. **투자 자문이 아닌 참고용 시그널**입니다.

### Buy Signals (매수 시그널)

**규칙:** 상위 상승 + 변동성 상위 교집합

1. **상위 상승 종목 선정**: 일간 수익률(`return`) 기준 상위 N개 (기본: 10개)
2. **변동성 상위 종목 선정**: 변동성 proxy(`vol`) 기준 상위 N개 (기본: 10개)
3. **교집합 선택**: 두 집합에 모두 포함된 종목만 매수 시그널로 선정

**예시:**
```
Top 3 Gainers: TSLA (+6%), AAPL (+5%), GOOGL (+4%)
Top 3 Volatile: TSLA (0.07), GOOGL (0.06), AAPL (0.05)
Buy Candidates: TSLA, GOOGL, AAPL (교집합)
```

**Reason (추천 근거):** `"상위 상승(5.00%) + 변동성 상위(0.0500) 교집합"`

### Sell Signals (매도 시그널)

**규칙:** 하락 top10 중 변동성 상위

1. **하락 종목 선정**: 일간 수익률(`return`)이 음수인 종목 중 하락률이 큰 순서로 상위 N개 (기본: 10개)
2. **변동성 기준 재정렬**: 선정된 하락 종목 중 변동성(`vol`)이 높은 순서로 정렬
3. **상위 M개 선택**: 변동성이 높은 순서로 상위 M개 선택 (기본: 10개)

**예시:**
```
Top 3 Losers: XYZ (-5%), ABC (-3%), DEF (-2%)
Among Losers, Top by Vol: XYZ (0.08), ABC (0.06), DEF (0.02)
Sell Candidates: XYZ, ABC (변동성 상위)
```

**Reason (추천 근거):** `"하락(-5.00%) 상위 중 변동성 높음(0.0800)"`

### 주의사항

- **투자 자문 아님**: 모든 시그널은 규칙 기반 자동 생성이며, 투자 판단의 참고용입니다.
- **과거 데이터 기반**: 현재 시점의 데이터만 사용하며, 미래 성과를 보장하지 않습니다.
- **리스크 고려**: 변동성이 높은 종목은 수익과 손실 모두 클 수 있습니다.
- **자체 판단 필수**: 모든 투자 결정은 사용자의 판단과 책임 하에 이루어져야 합니다.

### 설정 가능한 파라미터

- `top_n`: 각 카테고리에서 고려할 상위 종목 수 (기본: 10)
- `DEFAULT_TOP_N`: `config.py`에서 기본값 설정 가능

## 📝 문서

자세한 요구사항은 [PRD.md](PRD.md)를 참고하세요.

## 🤝 기여하기

이슈 및 Pull Request를 환영합니다!

## 📄 라이선스

[라이선스 정보 추가]

## 🔗 참고 자료

- [PRD 문서](PRD.md)
- [KTP 회고](KTP_RETROSPECTIVE.md)
- NASDAQ 공식 문서
- Provider API 문서 (Polygon, IEX Cloud 등)

---

## 📝 KTP 회고 (Keep, Try, Problem)

### ✅ Keep (잘된 점)

1. **TDD 기반 개발 프로세스**
   - 테스트 우선 작성(Red) → 구현(Green) → 리팩토링(Refactor) 사이클을 일관되게 적용
   - 순수 함수 중심 설계로 단위 테스트 작성이 용이했음
   - 테스트 커버리지가 높아 리팩토링 시 안정성 확보

2. **레이어 분리 아키텍처**
   - UI, Service, Data Collection, Core Logic 레이어를 명확히 분리
   - 관심사 분리로 코드 가독성 및 유지보수성 향상
   - 각 레이어의 독립적 테스트 및 확장 가능

3. **어댑터 패턴을 통한 외부 의존성 분리**
   - `MarketDataProvider` 인터페이스로 데이터 소스 교체 용이
   - 테스트 시 Mock Provider 사용으로 외부 API 의존성 제거
   - 향후 다른 데이터 제공자(Polygon, IEX Cloud 등) 추가 용이

4. **상수 중앙 관리 및 매직넘버 제거**
   - `config.py`에 모든 설정값을 상수로 정의
   - 코드 전반에 걸친 일관성 확보 및 유지보수성 향상
   - 임계값 변경 시 한 곳에서만 수정하면 됨

5. **재사용 가능한 UI 컴포넌트 설계**
   - Streamlit UI 컴포넌트를 모듈화하여 중복 제거
   - 테이블, 차트, 추천 카드 등 재사용 가능한 컴포넌트로 구성
   - UI 변경 시 영향 범위 최소화

### ⚠️ Problem (문제/리스크)

1. **데이터 신뢰성 및 품질 이슈**
   - `yfinance` 무료 API의 데이터 지연 및 불완전성 위험
   - 휴장일/공휴일 데이터 처리 미흡 (빈 데이터 반환 가능)
   - 티커 심볼 오타나 잘못된 심볼에 대한 검증 부족
   - OHLCV 데이터 일관성 검증 로직 부재

2. **추천 시스템의 책임성 및 법적 리스크**
   - 규칙 기반 추천이 투자 자문으로 오해될 수 있음
   - 추천 근거가 단순 수치 기반으로 리스크 분석 부족
   - 과거 성과 검증 없이 현재 데이터만 기반 추천
   - 사용자가 추천을 맹신할 경우 투자 손실 가능성

3. **API Rate Limit 및 성능 제약**
   - `yfinance` 무료 버전의 요청 제한으로 대량 티커 처리 시 실패 가능
   - 순차 다운로드로 인한 느린 데이터 수집 속도
   - 네트워크 오류 시 재시도 로직이 있으나 완벽하지 않음
   - 캐싱 전략이 있으나 장기간 데이터 보관 미흡

4. **변동성 계산의 한계**
   - 일봉 데이터만으로 계산한 변동성이 실제 변동성을 정확히 반영하지 못할 수 있음
   - 분봉/틱 데이터 부재로 일중 변동성 측정 정확도 제한
   - 롤링 윈도우 기반 변동성 계산이 최근 추세를 충분히 반영하지 못할 수 있음

5. **종목 필터링 및 스크리닝 로직의 단순성**
   - 현재 필터가 수익률/변동성만 기반으로 단순함
   - 거래량, 시가총액, 업종 등 추가 필터 부재
   - 기술적 지표(RSI, MACD 등) 미적용
   - 뉴스/이벤트 기반 필터링 불가

### 🚀 Try (다음 개선 사항)

1. **백테스트 시스템 구축**
   - 과거 데이터를 활용한 추천 규칙 성과 검증
   - 승률, 수익률, 최대 낙폭(MDD) 등 성과 지표 측정
   - 다양한 시장 상황(상승장/하락장/횡보장)에서의 규칙 성과 분석
   - 추천 규칙의 파라미터 최적화를 위한 백테스트 프레임워크

2. **포트폴리오 리밸런싱 및 리스크 관리**
   - 포트폴리오 분산 투자 전략 구현
   - 섹터/업종별 분산도 계산 및 제한
   - 개별 종목 비중 제한 (예: 최대 10%)
   - 리스크 지표(베타, 샤프 비율 등) 계산 및 표시
   - 손절/익절 가격 제안 기능

3. **종목 필터링 강화**
   - 거래량 필터 (최소 거래량, 평균 대비 거래량 비율)
   - 시가총액 필터 (대형주/중형주/소형주 구분)
   - 업종/섹터 필터
   - 기술적 지표 필터 (RSI, MACD, 볼린저 밴드 등)
   - 펀더멘털 필터 (P/E, P/B, 부채비율 등) - 데이터 소스 확보 시

4. **데이터 품질 개선 및 검증 강화**
   - OHLCV 데이터 일관성 검증 (예: High >= Low, Open/Close 범위 검증)
   - 휴장일/공휴일 처리 로직 강화 (pandas_market_calendars 활용)
   - 티커 심볼 유효성 검증 (실제 거래 가능한 종목인지 확인)
   - 데이터 소스 다중화 (주 데이터 소스 + 백업 소스)
   - 데이터 수집 실패 시 자동 재시도 및 알림

5. **성능 최적화 및 확장성 개선**
   - 병렬 다운로드 구현 (concurrent.futures, asyncio)
   - SQLite 기반 영구 캐시 시스템 구축
   - 증분 업데이트 (변경된 데이터만 갱신)
   - 대용량 데이터 처리 최적화 (청크 단위 처리)
   - API 호출 최소화를 위한 스마트 캐싱 전략

**자세한 내용은 [KTP_RETROSPECTIVE.md](KTP_RETROSPECTIVE.md)를 참고하세요.**

