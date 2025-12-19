# Smoke Test Checklist

이 문서는 NASDAQ Daily Movers & Volatility Analyzer의 스모크 테스트 체크리스트입니다.

## 사전 준비

- [ ] Python 3.10+ 설치 확인
- [ ] 프로젝트 의존성 설치: `pip install -r requirements.txt -r requirements-dev.txt`
- [ ] `nasdaq_tickers.csv` 파일이 프로젝트 루트에 존재하는지 확인

## 테스트 실행

### 1. Unit Tests 실행

```bash
pytest -q
```

**예상 결과:**
- 모든 테스트가 통과해야 함
- 테스트 커버리지 리포트 생성 (선택사항)

### 2. CLI 실행 (오늘 날짜 자동 사용)

**방법 1: 모듈로 실행**
```bash
python -m nasdaq_scanner.cli --universe nasdaq_tickers.csv --n 10
```

**방법 2: 설치 후 실행 (권장)**
```bash
# 먼저 설치 (개발 모드)
pip install -e .

# 그 다음 실행
nasdaq-scanner --universe nasdaq_tickers.csv --n 10
```

**방법 3: 직접 실행**
```bash
python src/nasdaq_scanner/cli.py --universe nasdaq_tickers.csv --n 10
```

**예상 결과:**
- 분석이 성공적으로 완료되어야 함
- 로그에 각 단계의 진행 상황이 표시되어야 함
- `reports/YYYY-MM-DD_report.md` 파일이 생성되어야 함
- `reports/YYYY-MM-DD_top.csv` 파일이 생성되어야 함

### 3. CLI 실행 (특정 날짜 지정)

```bash
python -m nasdaq_scanner.cli --date 2024-01-15 --universe nasdaq_tickers.csv --n 10
```

또는:

```bash
nasdaq-scanner --date 2024-01-15 --universe nasdaq_tickers.csv --n 10
```

**예상 결과:**
- 지정된 날짜로 분석이 실행되어야 함
- `reports/2024-01-15_report.md` 파일이 생성되어야 함
- `reports/2024-01-15_top.csv` 파일이 생성되어야 함

### 4. CSV 내보내기 비활성화 테스트

```bash
python -m nasdaq_scanner.cli --universe nasdaq_tickers.csv --n 10 --no-csv
```

또는:

```bash
nasdaq-scanner --universe nasdaq_tickers.csv --n 10 --no-csv
```

**예상 결과:**
- 마크다운 리포트만 생성되어야 함
- CSV 파일은 생성되지 않아야 함

## 결과물 검증

### 생성된 파일 확인

- [ ] `reports/` 디렉터리가 생성되었는지 확인
- [ ] `reports/YYYY-MM-DD_report.md` 파일이 존재하는지 확인
- [ ] `reports/YYYY-MM-DD_top.csv` 파일이 존재하는지 확인 (--no-csv 옵션 미사용 시)

### 마크다운 리포트 검증

- [ ] 리포트 헤더에 "NASDAQ Daily Movers & Volatility Analyzer"가 포함되어 있는지 확인
- [ ] 날짜가 올바르게 표시되는지 확인 (YYYY-MM-DD 형식)
- [ ] "Top Movers (상승)" 섹션이 있는지 확인
- [ ] "Bottom Movers (하락)" 섹션이 있는지 확인
- [ ] "Volatile Movers (변동성)" 섹션이 있는지 확인
- [ ] 각 섹션에 테이블이 포함되어 있는지 확인
- [ ] 데이터가 올바르게 표시되는지 확인

### CSV 파일 검증

- [ ] CSV 파일이 UTF-8 인코딩으로 저장되었는지 확인
- [ ] CSV 파일에 헤더 행이 있는지 확인
- [ ] CSV 파일에 데이터 행이 있는지 확인 (최대 n개)
- [ ] CSV 파일의 컬럼이 예상과 일치하는지 확인 (symbol, return_pct, vol_pct 등)

## 에러 케이스 테스트

### 1. 존재하지 않는 유니버스 파일

```bash
python -m nasdaq_scanner.cli --universe nonexistent.csv --n 10
```

**예상 결과:**
- 에러 메시지가 표시되어야 함
- 프로그램이 종료되어야 함 (exit code 1)

### 2. 잘못된 날짜 형식

```bash
python -m nasdaq_scanner.cli --date 2024/01/15 --universe nasdaq_tickers.csv --n 10
```

**예상 결과:**
- 날짜 형식 오류 메시지가 표시되어야 함
- 프로그램이 종료되어야 함 (exit code 1)

### 3. 빈 유니버스 파일

```bash
# 빈 CSV 파일 생성 후
python -m nasdaq_scanner.cli --universe empty.csv --n 10
```

**예상 결과:**
- "No tickers found" 에러 메시지가 표시되어야 함
- 프로그램이 종료되어야 함 (exit code 1)

## 통합 테스트

### 전체 파이프라인 테스트

```bash
pytest tests/integration/test_smoke.py -v
```

**예상 결과:**
- 모든 통합 테스트가 통과해야 함
- 모의 데이터를 사용한 파이프라인 테스트가 성공해야 함

## 성능 체크

- [ ] 10개 종목에 대한 분석이 30초 이내에 완료되는지 확인
- [ ] 네트워크 오류 시에도 부분 실패를 처리하는지 확인
- [ ] 로그가 적절한 수준으로 출력되는지 확인

## 체크리스트 완료 확인

모든 항목을 확인한 후:

- [ ] 모든 테스트가 통과함
- [ ] CLI가 정상적으로 실행됨
- [ ] 결과물이 올바르게 생성됨
- [ ] 에러 케이스가 적절히 처리됨

---

**참고:**
- 실제 시장 데이터를 가져오는 경우 네트워크 상태에 따라 시간이 걸릴 수 있습니다.
- 주말이나 공휴일에는 시장 데이터가 없을 수 있습니다.
- `yfinance` 라이브러리가 일부 종목에 대해 데이터를 제공하지 않을 수 있습니다.

