# 데이터 소스 변경 요약: yfinance → FinanceDataReader (NASDAQ → KOSDAQ)

## 📋 변경 개요

### 주요 변경 사항
1. **데이터 소스**: `yfinance` → `FinanceDataReader`
2. **분석 대상**: NASDAQ → KOSDAQ
3. **지수**: NASDAQ-100 (^NDX) → KOSDAQ 종합지수 (KQ11)
4. **개별 종목**: NASDAQ-100 종목 → KOSDAQ 종목 (시가총액 상위)

## 🔧 코드 변경 사항

### 1. 새로운 Provider 구현
- **파일**: `src/nasdaq_scanner/providers/financedatareader_provider.py`
- **기능**:
  - KOSDAQ 지수 (KQ11) 데이터 수집
  - KOSDAQ 개별 종목 데이터 수집
  - 지수 backoff 재시도 (최대 3회)
  - 캐싱으로 중복 요청 방지
  - 예외 처리 및 오류 분류

### 2. KOSDAQ Universe 모듈
- **파일**: `src/nasdaq_scanner/core/kosdaq_universe.py`
- **기능**:
  - `get_kosdaq_stock_listings()`: KOSDAQ 종목 리스트 가져오기
  - `get_kosdaq_tickers()`: KOSDAQ 티커 심볼 가져오기 (시가총액 상위 필터링 지원)
  - `get_kosdaq_index_symbol()`: KOSDAQ 지수 심볼 반환 (KQ11)

### 3. Data Collector 수정
- **파일**: `src/nasdaq_scanner/providers/data_collector.py`
- **변경**:
  - `load_ticker_list()`: `'kosdaq-index'`, `'kosdaq-top'` 옵션 추가
  - `collect_data()`: KOSDAQ 소스에 대해 `FinanceDataReaderProvider` 자동 선택

### 4. Config 업데이트
- **파일**: `src/nasdaq_scanner/config.py`
- **추가**:
  - `TICKER_SOURCE_KOSDAQ_INDEX`: "kosdaq-index"
  - `TICKER_SOURCE_KOSDAQ_TOP`: "kosdaq-top"

### 5. Streamlit UI 수정
- **파일**: `app.py`
- **변경**:
  - 페이지 제목: "ALPHABRAIN NASDAQ" → "ALPHABRAIN KOSDAQ"
  - 티커 소스 옵션: KOSDAQ 지수, KOSDAQ 상위 종목 추가
  - 오류 메시지에 KOSDAQ 거래 시간 안내 추가

### 6. 의존성 추가
- **파일**: `requirements.txt`
- **추가**: `FinanceDataReader>=0.9.50`

## 🧪 테스트

### 단위 테스트
- **파일**: `tests/unit/test_financedatareader_provider.py`
- **테스트 항목**:
  1. DataFrame 컬럼/인덱스 형태 검증
  2. 빈 데이터일 때 예외 처리 검증
  3. 네트워크 오류 처리 검증
  4. 단일 심볼 조회 검증

### 테스트 실행 방법
```bash
# 단위 테스트 실행
pytest tests/unit/test_financedatareader_provider.py -v

# 전체 테스트 실행
pytest tests/ -v
```

## 📦 설치 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

또는 FinanceDataReader만 설치:
```bash
pip install finance-datareader>=0.9.50
```

### 2. 프로그램 실행
```bash
streamlit run app.py
```

## 🎯 사용 방법

### Streamlit UI
1. **티커 소스 선택**:
   - **KOSDAQ 지수**: KOSDAQ 종합지수 (KQ11)만 분석
   - **KOSDAQ 상위**: 시가총액 상위 KOSDAQ 종목 분석 (기본: 상위 100개)
   - **CSV 파일**: CSV 파일에서 종목 리스트 업로드
   - **직접 입력**: 종목 코드 직접 입력

2. **날짜 선택**: 분석할 거래일 선택

3. **분석 실행**: "분석 시작" 버튼 클릭

### 프로그래밍 방식
```python
from nasdaq_scanner.providers.data_collector import collect_data
from datetime import date

# KOSDAQ 지수 데이터 수집
df, failed = collect_data('kosdaq-index', date(2025, 12, 19))

# KOSDAQ 상위 종목 데이터 수집
df, failed = collect_data('kosdaq-top', date(2025, 12, 19))
```

## ⚠️ 주의 사항

### 1. 거래 시간
- KOSDAQ 거래 시간: 09:00-15:30 KST (한국 시간)
- 장 마감 후 데이터 조회 가능

### 2. 데이터 지연
- FinanceDataReader는 실시간 데이터가 아닐 수 있음
- 당일 데이터는 장 마감 후 확인 가능

### 3. 종목 코드 형식
- KOSDAQ 종목 코드: 6자리 숫자 (예: "005930")
- 지수 코드: "KQ11" (KOSDAQ 종합지수)

### 4. 예외 처리
- 네트워크 오류: 자동 재시도 (최대 3회, 지수 backoff)
- 빈 데이터: 사용자에게 명확한 오류 메시지 표시
- 잘못된 종목 코드: 실패한 종목 리스트에 추가

## 🔄 기존 기능 유지

다음 기능은 변경 없이 유지됩니다:
- ✅ 변동성 계산 로직
- ✅ 상승/하락 Top 10 랭킹
- ✅ 추천 시스템 (관심 매수/매도 후보)
- ✅ Streamlit UI 컴포넌트
- ✅ 캐싱 및 성능 최적화

## 📝 향후 개선 사항

1. **KOSDAQ 종목 필터링 옵션 확장**
   - 업종별 필터링
   - 시가총액 범위 지정
   - 거래량 필터링

2. **데이터 소스 다중화**
   - FinanceDataReader 실패 시 대체 소스
   - 로컬 캐시 활용

3. **실시간 데이터 지원**
   - WebSocket 연결
   - 실시간 가격 업데이트

## 🐛 알려진 이슈

1. **FinanceDataReader 설치 오류**
   - 해결: `pip install finance-datareader>=0.9.50` 재실행

2. **KOSDAQ 종목 리스트 로딩 실패**
   - 해결: 인터넷 연결 확인, FinanceDataReader 버전 확인

3. **데이터 조회 실패**
   - 해결: 거래일 확인, 장 마감 후 조회

## 📚 참고 자료

- [FinanceDataReader 문서](https://github.com/FinanceData/FinanceDataReader)
- [KOSDAQ 공식 사이트](https://www.kosdaq.or.kr/)
- [한국거래소](https://www.krx.co.kr/)

