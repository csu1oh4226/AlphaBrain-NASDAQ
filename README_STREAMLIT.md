# NASDAQ 주가 분석 대시보드 (Streamlit)

Streamlit 기반의 NASDAQ 주가 분석 대시보드 MVP입니다.

## 📋 기능

- **데이터 수집**: 티커 리스트와 가격 데이터 자동 수집
- **분석 모듈**: 일간 수익률, 변동성, 상승/하락 TOP10 계산
- **추천 모듈**: 규칙 기반 매수/매도 후보 산출 및 근거 표시
- **대시보드**: Streamlit 기반 인터랙티브 UI

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
# 가상 환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 티커 유니버스 파일 준비

`nasdaq_tickers.csv` 파일이 프로젝트 루트에 있어야 합니다. 예시:

```csv
symbol
AAPL
MSFT
GOOGL
AMZN
TSLA
```

또는 새 파일을 만들 수 있습니다.

### 3. Streamlit 앱 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 대시보드를 확인할 수 있습니다.

## 📖 사용 방법

### 대시보드 사용

1. **티커 유니버스 파일 업로드**
   - 사이드바에서 CSV 파일 업로드
   - `symbol` 컬럼이 포함되어 있어야 합니다

2. **분석 날짜 선택**
   - 분석할 날짜를 선택하세요 (오늘 이전 날짜만 가능)

3. **설정 조정**
   - 상위/하위 종목 수: 표시할 종목 수 (기본: 10)
   - 추천 종목 수: 매수/매도 추천 종목 수 (기본: 10)

4. **분석 실행**
   - "🚀 분석 실행" 버튼 클릭
   - 데이터 수집 및 분석이 진행됩니다

### 결과 확인

대시보드는 5개의 탭으로 구성되어 있습니다:

- **📈 상위 종목**: 일간 수익률 상위 종목
- **📉 하위 종목**: 일간 하락률 상위 종목
- **📊 변동성**: 일중 변동성 상위 종목
- **💰 매수 추천**: 규칙 기반 매수 후보 종목
- **⚠️ 매도/주의**: 규칙 기반 매도/주의 후보 종목

각 탭에서:
- 테이블로 상세 데이터 확인
- 차트로 시각화
- 추천 근거 확인 (매수/매도 탭)

## 🧪 테스트

### 단위 테스트 실행

```bash
# 모든 테스트 실행
pytest tests/test_streamlit.py -v

# 특정 테스트만 실행
pytest tests/test_streamlit.py::TestRecommender::test_generate_recommendations_basic -v

# 커버리지 포함
pytest tests/test_streamlit.py --cov=src/nasdaq_scanner/core/recommender --cov-report=html
```

### 테스트 구조

- `tests/test_streamlit.py`: Streamlit 앱 및 추천 모듈 테스트
  - `TestRecommender`: 추천 모듈 단위 테스트
  - `TestStreamlitIntegration`: Streamlit 통합 테스트

## 📁 프로젝트 구조

```
.
├── app.py                              # Streamlit 메인 앱
├── nasdaq_tickers.csv                  # 티커 유니버스 파일 (예시)
├── src/
│   └── nasdaq_scanner/
│       ├── cli.py                      # CLI (run_analysis 함수 포함)
│       ├── core/
│       │   ├── metrics.py              # 수익률/변동성 계산
│       │   ├── ranking.py              # TOP N 랭킹
│       │   ├── signals.py              # 규칙 기반 신호 생성
│       │   ├── universe.py             # 티커 로드
│       │   └── recommender.py          # 매수/매도 추천 (새로 추가)
│       ├── providers/
│       │   └── data_provider.py        # 가격 데이터 수집
│       └── reporter/
│           └── report.py              # 리포트 생성
├── tests/
│   └── test_streamlit.py               # Streamlit 테스트
└── requirements.txt                    # 의존성 (streamlit 포함)
```

## 🔧 주요 모듈

### 1. 데이터 수집 모듈

- **`core/universe.py`**: 티커 리스트 로드
- **`providers/data_provider.py`**: yfinance를 통한 가격 데이터 수집

### 2. 분석 모듈

- **`core/metrics.py`**: 일간 수익률(`return_pct`), 변동성(`vol_pct`) 계산
- **`core/ranking.py`**: 상승/하락/변동성 TOP N 추출

### 3. 추천 모듈

- **`core/recommender.py`**: 규칙 기반 매수/매도 추천
  - 기본 매수 규칙:
    - 일간 수익률 5% 이상
    - 수익률 3% 이상 + 변동성 4% 이상
    - 수익률 2-5% (적정 상승)
  - 기본 매도/주의 규칙:
    - 일간 하락률 5% 이상 (급락 주의)
    - 하락률 3% 이상 + 변동성 5% 이상 (불안정)
    - 하락률 2-5% (주의 관찰)

### 4. Streamlit UI

- **`app.py`**: 메인 대시보드 앱
  - 사이드바: 입력 파라미터 설정
  - 메인 영역: 결과 표시 (테이블, 차트)

## ⚙️ 설정

### 추천 규칙 커스터마이징

`src/nasdaq_scanner/core/recommender.py`에서 규칙을 수정할 수 있습니다:

```python
def get_default_buy_rules() -> List[Dict[str, Any]]:
    return [
        {
            'name': 'custom_rule',
            'condition': lambda row: row.get('return_pct', 0) > 7.0,
            'action': 'buy',
            'description': '사용자 정의 규칙'
        },
    ]
```

## 🐛 문제 해결

### "yfinance not installed" 오류

```bash
pip install yfinance>=0.2.0
```

### 데이터 수집 실패

- 네트워크 연결 확인
- 주말/공휴일에는 시장 데이터가 없을 수 있음
- 티커 심볼이 올바른지 확인

### Streamlit 실행 오류

```bash
# Streamlit 재설치
pip install --upgrade streamlit

# 포트 변경
streamlit run app.py --server.port 8502
```

## 📝 개발 가이드

### 새로운 추천 규칙 추가

1. `src/nasdaq_scanner/core/recommender.py` 수정
2. `get_default_buy_rules()` 또는 `get_default_sell_rules()`에 규칙 추가
3. 테스트 작성 및 실행

### UI 커스터마이징

`app.py`에서 Streamlit 컴포넌트를 수정하여 UI를 변경할 수 있습니다.

## ⚠️ 면책 조항

이 도구는 투자 자문이 아닙니다. 모든 분석 결과는 참고용이며,
투자 결정은 사용자의 판단에 따라 이루어져야 합니다.

## 📄 라이선스

MIT License

## 🤝 기여

이슈 및 풀 리퀘스트를 환영합니다!

---

**작성일:** 2024

