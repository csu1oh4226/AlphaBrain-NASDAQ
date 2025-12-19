# PRD: NASDAQ Daily Movers & Volatility Analyzer

**Version:** 1.0  
**Date:** 2024  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Product Purpose

NASDAQ 상장 종목의 당일(또는 최근 거래일) 주가 데이터를 수집하여 다음을 산출합니다:

- 일중 변동성(Volatility) 상위 종목 10개
- 상승률 상위 10개
- 하락률 상위 10개

규칙 기반으로 **"오늘의 관심 매수 후보 10개 / 관심 매도(주의) 후보 10개"**를 자동 생성합니다.

### 1.2 Target Users

- 주식 시장 데이터를 빠르게 훑고 싶은 개인 투자자(초급~중급)
- 데일리 리포트 자동화가 필요한 개발자/데이터 분석가
- 퀀트/트레이딩 전략 입문자(규칙 기반 스크리너)

### 1.3 Core Value Proposition

- 매일 반복되는 "상·하위 종목 찾기" 자동화
- 변동성+거래량+뉴스(선택) 기반으로 "주의/관심" 후보를 빠르게 추림
- 결과를 CSV/리포트로 저장하여 추적 가능

---

## 2. Scope

### 2.1 In-Scope (MVP)

- ✅ NASDAQ 상장 종목 리스트 기반 종목 유니버스 구성
- ✅ 시세 데이터 수집(일봉 or 분봉/5분봉 등)
- ✅ 변동성 및 등락률 계산
- ✅ 상·하위 Top 10 산출
- ✅ 간단한 규칙 기반 "관심 후보" 생성
- ✅ 결과 저장(CSV/SQLite/PostgreSQL 선택)
- ✅ CLI 또는 간단한 Web 대시보드(택1)

### 2.2 Out-of-Scope (Phase 1)

- ❌ "수익 보장"이나 고급 포트폴리오 최적화
- ❌ 실시간 초단타 체결 데이터(틱 데이터)
- ❌ 주문 실행(브로커 API로 매매 자동화)
- ❌ 개인 투자 성향/리스크 성향 기반 맞춤 추천(2차로 가능)

---

## 3. User Stories

### 3.1 Data Collection

**Story:** 데이터 수집

```
Given 사용자가 오늘 날짜로 분석을 실행할 때
When 시스템이 NASDAQ 유니버스에 대해 가격 데이터를 수집하면
Then 수집 성공/실패 종목 수와 원인을 로그로 남긴다
```

**Acceptance Criteria:**
- [ ] 지정된 날짜의 데이터 수집 완료
- [ ] 성공/실패 종목 수 로깅
- [ ] 실패 원인 상세 로깅
- [ ] 부분 실패 시에도 분석 진행 가능

### 3.2 Top Movers View

**Story:** 상·하위 종목 보기

```
Given 데이터 수집이 완료되었을 때
When 사용자가 "오늘 상승 Top10"을 조회하면
Then 상승률, 가격, 거래량, 변동성 지표가 함께 출력된다
```

**Acceptance Criteria:**
- [ ] 상승 Top 10 정확히 산출
- [ ] 하락 Top 10 정확히 산출
- [ ] 변동성 Top 10 정확히 산출
- [ ] 각 항목에 상세 지표 포함(가격, 거래량, 변동성)

### 3.3 Watchlist Generation

**Story:** 관심 후보 생성

```
Given 상·하위 및 변동성 계산이 끝났을 때
When 사용자가 "관심 매수/매도 후보 생성"을 실행하면
Then 규칙/근거(룰 설명)를 함께 표시한다
```

**Acceptance Criteria:**
- [ ] 관심 매수 후보 10개 생성
- [ ] 관심 매도/주의 후보 10개 생성
- [ ] 각 후보에 선택 근거(룰 설명) 포함
- [ ] 경고 플래그 표시(예: 급등 주의)

### 3.4 Export Functionality

**Story:** 내보내기

```
Given 결과 테이블이 생성되었을 때
When 사용자가 export를 실행하면
Then CSV(및 선택적으로 DB)로 저장된다
```

**Acceptance Criteria:**
- [ ] CSV 형식으로 저장 가능
- [ ] SQLite/PostgreSQL 선택 저장 가능
- [ ] 저장된 데이터 검증 가능

---

## 4. Data Requirements

### 4.1 Universe Data

**NASDAQ 상장 종목 목록**

**Minimum Fields:**
- `symbol` (string, PK): 티커 심볼
- `name` (string): 회사명
- `exchange` (string): 거래소 코드
- `type` (enum): stock/etf
- `is_active` (boolean): 활성 상태

**Optional Fields:**
- `sector` (string): 섹터
- `industry` (string): 산업
- `market_cap` (float): 시가총액

### 4.2 Price Data

**Option A: Daily OHLCV (MVP Recommended)**
- `open` (float): 시가
- `high` (float): 고가
- `low` (float): 저가
- `close` (float): 종가
- `volume` (int): 거래량
- `date` (date): 거래일

**Option B: Intraday Candles (Future Enhancement)**
- 분봉/5분봉 데이터
- 일중 표준편차, ATR 근사, 파동성 계산 가능

### 4.3 Data Sources

**Provider Interface (Abstract)**
- Provider 교체 가능한 아키텍처
- 후보: Polygon, IEX Cloud, Alpha Vantage, Twelve Data 등
- **Note:** API 키 필요, 무료/비공식 소스는 속도/정확성/약관 이슈 가능

---

## 5. Calculation & Analysis Logic

### 5.1 Price Change Calculation

**Option 1: Intraday Change (당일)**
```
pct_change = (close - open) / open * 100
```

**Option 2: Previous Close Comparison (전일 대비)**
```
pct_change = (close - prev_close) / prev_close * 100
```

**MVP Recommendation:** Option 1 (당일 기준)

### 5.2 Volatility Calculation

**Range Volatility (MVP Recommended)**
```
range_pct = (high - low) / open * 100
```

**Advantages:**
- 일봉만으로 가능
- 직관적
- 계산 간단

**Future Enhancements:**
- Intraday Std Dev (분봉 종가 수익률 표준편차)
- ATR(14) 유사 지표 (일봉 여러 일 필요)

### 5.3 Top 10 Ranking

- **상승 Top 10:** `pct_change DESC`
- **하락 Top 10:** `pct_change ASC`
- **변동성 Top 10:** `range_pct DESC`

### 5.4 Watchlist Recommendation Rules

**Important:** 투자 판단이 아닌 "신호 기반 스크리닝"으로 표현

#### 관심 매수 후보 (Buy Watchlist)

**Rule Set (Configurable):**
1. 상승 Top 10 ∩ 변동성 Top 10 포함 종목 중
2. `volume`이 유니버스 중 상위 X% (예: 상위 20%)
3. 단, 너무 급등(예: +20% 이상)인 경우 "추격 매수 경고" 플래그

**Example Rule:**
```
IF (pct_change in Top 10) AND (range_pct in Top 10) AND (volume_percentile >= 80)
THEN add to buy_watchlist
IF pct_change > 20
THEN add warning_flag = "급등 주의"
```

#### 관심 매도/주의 후보 (Sell/Caution Watchlist)

**Rule Set:**
1. 하락 Top 10 중
2. 변동성 Top 10에도 포함 + 거래량 급증(전일 대비 배수 가능하면)
3. 또는 전일 대비 갭다운(일봉 only면 open/prev_close 비교)

**Example Rule:**
```
IF (pct_change in Bottom 10) AND (range_pct in Top 10) AND (volume_spike >= 2.0)
THEN add to sell_watchlist
IF (open < prev_close * 0.95)
THEN add warning_flag = "갭다운"
```

**Configuration:**
- 룰을 설정 파일(config)로 관리
- 기본값 제공
- 사용자 커스터마이징 가능

---

## 6. Functional Requirements

### 6.1 Core Features

#### 6.1.1 Universe Loader
- [ ] NASDAQ 심볼 리스트 로드/캐시
- [ ] ETF 포함 여부 옵션
- [ ] 심볼 목록 업데이트 기능

#### 6.1.2 Market Data Fetcher
- [ ] 날짜/기간 지정 수집
- [ ] 실패 재시도(backoff)
- [ ] API rate limit 대응
- [ ] 수집 결과 로깅

#### 6.1.3 Analyzer
- [ ] `pct_change` 계산
- [ ] `range_pct` 계산
- [ ] Top 10 리스트 생성
- [ ] 후보 제안(룰 기반) + 근거 텍스트 생성

#### 6.1.4 Reporter
- [ ] 콘솔 표 출력
- [ ] JSON 출력
- [ ] CSV export
- [ ] (옵션) HTML 리포트/PDF

### 6.2 Output Format Example

**Console Output:**
```
========================================
NASDAQ Daily Movers & Volatility Analyzer
Date: 2024-01-15
========================================

📈 상승 Top 10
Rank | Symbol | Name | Change % | Volume | Volatility %
-----|--------|------|----------|--------|-------------
1    | AAPL   | ...  | +5.2%    | 50M    | 3.1%

📉 하락 Top 10
...

📊 변동성 Top 10
...

💡 관심 매수 후보 10
Rank | Symbol | Reason
-----|--------|-------
1    | TSLA   | 상승 Top10 + 변동성 Top10 + 거래량 상위 15%

⚠️ 관심 매도/주의 후보 10
...
```

---

## 7. Non-Functional Requirements

### 7.1 Performance

- **Universe Size:** 3,000~5,000 종목
- **Data Collection:** 5~15분 내 완료 (Provider/RateLimit에 따라)
- **Cache Strategy:** 재실행 시간 단축
- **Analysis Time:** < 1분 (수집 완료 후)

### 7.2 Reliability & Recovery

- [ ] 일부 종목 수집 실패해도 전체 분석 지속
- [ ] 실패 목록 별도 저장
- [ ] 재시도 메커니즘
- [ ] 부분 결과 저장 가능

### 7.3 Security

- [ ] API 키는 `.env`로 관리
- [ ] 리포지토리에 키 커밋 금지 (`.gitignore`)
- [ ] 로그에 키 출력 금지
- [ ] 환경 변수 검증

### 7.4 Legal & Disclaimers

- [ ] "투자 자문 아님" 고지 (모든 출력에 포함)
- [ ] 데이터 제공사 약관 준수
- [ ] 재배포/캐싱 규정 준수
- [ ] 라이선스 명시

---

## 8. System Architecture

### 8.1 Module Structure

```
app/
├── main.py                 # CLI 엔트리
├── core/
│   ├── universe.py        # 유니버스 관리
│   ├── providers/         # Provider 인터페이스 + 구현
│   │   ├── __init__.py
│   │   ├── base.py        # MarketDataProvider 인터페이스
│   │   ├── polygon.py
│   │   ├── iex.py
│   │   └── mock.py        # 테스트용 Mock Provider
│   ├── fetcher.py         # 데이터 수집
│   ├── analyzer.py        # 분석 로직
│   ├── ranker.py          # Top 10 랭킹
│   ├── recommender.py     # Watchlist 제안
│   └── reporter.py        # 리포트 생성
├── storage/
│   ├── cache.py           # SQLite/파일 캐시
│   └── exporter.py        # CSV/DB export
├── config/
│   └── rules.yaml         # 룰 설정 파일
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── README.md
```

### 8.2 Provider Abstraction (Required)

**MarketDataProvider Interface:**

```python
class MarketDataProvider(ABC):
    @abstractmethod
    def get_symbols(self) -> List[Symbol]:
        """NASDAQ 심볼 리스트 반환"""
        pass
    
    @abstractmethod
    def get_daily_ohlcv(self, symbol: str, date: date) -> OHLCV:
        """일봉 데이터 반환"""
        pass
    
    @abstractmethod
    def get_intraday_ohlcv(self, symbol: str, date: date, interval: str) -> List[OHLCV]:
        """분봉 데이터 반환 (옵션)"""
        pass
```

### 8.3 Technology Stack (Recommendation)

- **Language:** Python 3.10+
- **Data Processing:** pandas, numpy
- **API Client:** httpx, requests
- **Database:** SQLite (MVP), PostgreSQL (옵션)
- **CLI:** click, typer
- **Testing:** pytest
- **Linting:** ruff, black
- **Config:** pydantic, pyyaml

---

## 9. Data Model

### 9.1 Database Schema

#### `symbols` Table
```sql
CREATE TABLE symbols (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    exchange VARCHAR(10),
    type VARCHAR(10),  -- 'stock' or 'etf'
    is_active BOOLEAN,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    updated_at TIMESTAMP
);
```

#### `prices_daily` Table
```sql
CREATE TABLE prices_daily (
    symbol VARCHAR(10),
    date DATE,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    volume BIGINT,
    PRIMARY KEY (symbol, date)
);
```

#### `analysis_daily` Table
```sql
CREATE TABLE analysis_daily (
    symbol VARCHAR(10),
    date DATE,
    pct_change DECIMAL(5, 2),
    range_pct DECIMAL(5, 2),
    flags JSON,  -- {"warning": "급등 주의", "category": "buy_watchlist"}
    score DECIMAL(5, 2),  -- optional ranking score
    PRIMARY KEY (symbol, date)
);
```

### 9.2 DataFrame Schema (In-Memory)

```python
# pandas DataFrame schemas
SymbolSchema = {
    'symbol': str,
    'name': str,
    'exchange': str,
    'type': str,
    'is_active': bool
}

PriceSchema = {
    'symbol': str,
    'date': datetime,
    'open': float,
    'high': float,
    'low': float,
    'close': float,
    'volume': int
}

AnalysisSchema = {
    'symbol': str,
    'date': datetime,
    'pct_change': float,
    'range_pct': float,
    'flags': dict,
    'score': float
}
```

---

## 10. Test Strategy

### 10.1 Unit Tests

**Target Modules:**
- 변동성/등락 계산 정확성
- Top 10 정렬 및 타이 브레이커
- 룰 기반 후보 생성(경고 플래그 포함)

**Example Test Cases:**
```python
def test_pct_change_calculation():
    assert calculate_pct_change(open=100, close=105) == 5.0

def test_top10_ranking():
    data = [{'symbol': 'A', 'pct_change': 10}, ...]
    top10 = get_top10(data, 'pct_change', desc=True)
    assert len(top10) == 10
    assert top10[0]['pct_change'] >= top10[1]['pct_change']

def test_buy_watchlist_rules():
    # 룰 적용 테스트
    pass
```

### 10.2 Integration Tests

- Provider mock으로 API 응답 시뮬레이션
- Rate limit/실패 재시도 케이스
- End-to-end 파이프라인 테스트

### 10.3 Sanity Tests

- 소규모 심볼(예: 20개)로 end-to-end 실행
- 실제 Provider 연결 테스트(개발 환경)

---

## 11. Logging & Observability

### 11.1 Log Levels

- **INFO:** 실행 시작/종료, 수집 성공/실패 수
- **DEBUG:** Provider 응답 시간, 상세 계산 과정
- **WARNING:** Rate limit 접근, 부분 실패
- **ERROR:** API 실패, 데이터 파싱 오류

### 11.2 Log Output

```
[INFO] Analysis started for date: 2024-01-15
[INFO] Universe loaded: 4,523 symbols
[INFO] Fetching price data... (0/4523)
[INFO] Fetching price data... (1000/4523)
[INFO] Fetching price data... (4523/4523)
[INFO] Collection completed: 4,500 success, 23 failed
[INFO] Analysis completed in 12.3s
[INFO] Top 10 movers generated
[INFO] Watchlist recommendations generated
```

### 11.3 Metrics to Track

- 수집 성공률
- 평균 API 응답 시간
- 분석 실행 시간
- Top 10 티커 리스트 (결과 요약)

---

## 12. MVP Release Criteria (Definition of Done)

### 12.1 Functional Requirements

- [ ] CLI로 `--date` 지정 실행 가능
- [ ] 상승/하락/변동성 Top 10 생성
- [ ] 관심 매수/매도 "후보" 생성 + 근거 출력
- [ ] CSV export 기능

### 12.2 Quality Requirements

- [ ] 테스트 통과 (Unit + Integration)
- [ ] 린트 통과 (ruff/black)
- [ ] 타입 체크 통과 (mypy, optional)

### 12.3 Documentation

- [ ] README에 실행 방법 포함
- [ ] README에 고지(투자 자문 아님) 포함
- [ ] README에 설정 방법(API 키 등) 포함
- [ ] 코드 주석 및 docstring

### 12.4 Configuration

- [ ] `.env.example` 파일 제공
- [ ] 설정 파일 예시 제공
- [ ] Provider 교체 가이드

---

## 13. Implementation Roadmap

### Phase 1: MVP (Current)

1. **Project Scaffolding**
   - 폴더 구조 생성
   - 의존성 관리 (requirements.txt / poetry)
   - ruff/pytest 설정

2. **Provider Interface**
   - `MarketDataProvider` 인터페이스 정의
   - Mock Provider 구현 (테스트용)

3. **Core Modules (TDD)**
   - Analyzer (변동성/등락 계산)
   - Ranker (Top 10)
   - Recommender (Watchlist)

4. **Data Collection**
   - Fetcher 구현
   - 실제 Provider 연결 (Polygon/IEX 등)

5. **Reporter**
   - CLI 출력
   - CSV export

6. **Cache & Performance**
   - SQLite 캐시
   - 재실행 시간 단축

### Phase 2: Enhancements (Future)

- HTML 리포트/PDF 생성
- Web 대시보드 (FastAPI/Streamlit)
- 추가 변동성 지표 (ATR, Std Dev)
- 분봉 데이터 지원
- 알림 기능 (이메일/Slack)

---

## 14. Risk & Mitigation

### 14.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API Rate Limits | High | 캐싱, 배치 처리, Provider 교체 가능 |
| 데이터 품질 이슈 | Medium | 데이터 검증, 다중 Provider 지원 |
| 성능 저하 (대량 종목) | Medium | 병렬 처리, 캐시 최적화 |

### 14.2 Business Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API 키 비용 | Medium | 무료 티어 활용, Provider 비교 |
| 법적 이슈 (데이터 사용) | High | 약관 준수, 고지 명시 |

---

## 15. Success Metrics

### 15.1 Technical Metrics

- 수집 성공률 > 95%
- 분석 실행 시간 < 15분 (전체)
- 테스트 커버리지 > 80%

### 15.2 User Metrics (Future)

- 일일 실행 횟수
- CSV 다운로드 횟수
- 사용자 피드백

---

## 16. Appendix

### 16.1 Glossary

- **Universe:** 분석 대상 종목 전체 집합
- **OHLCV:** Open, High, Low, Close, Volume
- **Range Volatility:** (High - Low) / Open * 100
- **Watchlist:** 관심 종목 목록

### 16.2 References

- NASDAQ 공식 문서
- Provider API 문서 (Polygon, IEX Cloud 등)
- Python best practices

### 16.3 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01 | Initial PRD |

---

## 17. Approval & Sign-off

**Product Owner:** [TBD]  
**Tech Lead:** [TBD]  
**Date:** [TBD]

---

**Disclaimer:** 이 제품은 투자 자문이 아닙니다. 모든 분석 결과는 참고용이며, 투자 결정은 사용자의 판단에 따라 이루어져야 합니다.

