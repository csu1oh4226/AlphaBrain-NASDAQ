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

# 의존성 설치
pip install -r requirements.txt
```

### 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 API 키를 설정하세요.

```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

## 📖 사용 방법

```bash
# 오늘 날짜로 분석 실행
python app/main.py --date 2024-01-15

# CSV로 결과 저장
python app/main.py --date 2024-01-15 --export csv
```

## 📁 프로젝트 구조

```
app/
├── main.py                 # CLI 엔트리
├── core/
│   ├── universe.py        # 유니버스 관리
│   ├── providers/         # Provider 인터페이스 + 구현
│   ├── fetcher.py         # 데이터 수집
│   ├── analyzer.py        # 분석 로직
│   ├── ranker.py          # Top 10 랭킹
│   ├── recommender.py     # Watchlist 제안
│   └── reporter.py        # 리포트 생성
├── storage/
│   ├── cache.py           # SQLite/파일 캐시
│   └── exporter.py        # CSV/DB export
└── config/
    └── rules.yaml         # 룰 설정 파일
```

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app
```

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

