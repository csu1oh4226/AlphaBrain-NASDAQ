# 라이브러리 설치 가이드

## 프로그램 실행에 필수 라이브러리

### 1. 핵심 라이브러리 (필수)

다음 라이브러리들은 `app.py` 실행에 **반드시 필요**합니다:

```bash
pip install streamlit
pip install pandas
pip install numpy
pip install yfinance
```

### 2. 한 번에 설치 (권장)

```bash
pip install streamlit pandas numpy yfinance
```

또는

```bash
pip install -r requirements.txt
```

---

## 라이브러리별 용도

| 라이브러리 | 버전 | 용도 | 필수 여부 |
|-----------|------|------|----------|
| **streamlit** | >=1.28.0 | 웹 UI (대시보드) | ✅ 필수 |
| **pandas** | >=2.0.0 | 데이터 처리 및 분석 | ✅ 필수 |
| **numpy** | >=1.24.0 | 수치 계산 (pandas 의존성) | ✅ 필수 |
| **yfinance** | >=0.2.0 | 주가 데이터 수집 | ✅ 필수 |

---

## 선택적 라이브러리

다음 라이브러리들은 CLI 사용 시에만 필요합니다:

```bash
pip install click
```

---

## 설치 확인

설치가 완료되었는지 확인하려면:

```bash
python -c "import streamlit, pandas, numpy, yfinance; print('✅ 모든 라이브러리 설치 완료!')"
```

---

## 프로그램 실행

설치 완료 후:

```bash
# 방법 1: python -m streamlit 사용 (권장)
python -m streamlit run app.py

# 방법 2: streamlit 명령어 사용 (PATH에 등록된 경우)
streamlit run app.py
```

---

## 문제 해결

### `streamlit` 명령어를 찾을 수 없는 경우

Windows에서 `streamlit` 명령어가 인식되지 않으면:

```bash
# python -m streamlit 사용
python -m streamlit run app.py
```

### 라이브러리 설치 오류

```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 개별 설치
pip install streamlit
pip install pandas
pip install numpy
pip install yfinance
```

