# GUI 구성 추천 가이드

현재 CLI 기반으로 구현된 NASDAQ Daily Movers & Volatility Analyzer에 GUI를 추가하는 방법을 제안합니다.

---

## 🎯 추천 순위 (사용 사례별)

### 1️⃣ **Streamlit** (가장 추천 ⭐⭐⭐⭐⭐)

**추천 이유:**
- 빠른 프로토타이핑 (1-2일 내 구현 가능)
- 데이터 시각화에 최적화 (차트, 테이블 자동 렌더링)
- Python만으로 풀스택 구현 가능
- 현재 프로젝트 구조와 완벽하게 호환

**적합한 사용자:**
- 데이터 분석가
- 빠른 대시보드가 필요한 사용자
- 웹 기반 인터페이스 선호

**구현 예시:**
```python
# src/nasdaq_scanner/gui/streamlit_app.py
import streamlit as st
from datetime import date
from nasdaq_scanner.cli import run_analysis
import pandas as pd

st.title("NASDAQ Daily Movers & Volatility Analyzer")

# 입력 폼
analysis_date = st.date_input("Analysis Date", value=date.today())
universe_file = st.file_uploader("Upload Universe CSV", type=['csv'])
n = st.slider("Number of Top Movers", 5, 50, 10)

if st.button("Run Analysis"):
    with st.spinner("Analyzing..."):
        # run_analysis 호출
        # 결과를 DataFrame으로 받아서 표시
        st.dataframe(top_movers)
        st.line_chart(top_movers['return_pct'])
```

**장점:**
- ✅ 구현 시간: 1-2일
- ✅ 자동 리로드 (코드 변경 시)
- ✅ 내장 차트/테이블 위젯
- ✅ 배포 간편 (Streamlit Cloud)

**단점:**
- ❌ 커스터마이징 제한적
- ❌ 복잡한 상호작용 구현 어려움

**통합 방법:**
```python
# run_analysis를 수정하여 결과를 반환하도록 변경
def run_analysis(...) -> Dict[str, DataFrame]:
    # ... 기존 로직 ...
    return {
        'top_movers': top_movers,
        'bottom_movers': bottom_movers,
        'volatile_movers': volatile_movers,
        'analysis_date': analysis_date
    }
```

---

### 2️⃣ **Gradio** (간단한 인터페이스 ⭐⭐⭐⭐)

**추천 이유:**
- Streamlit보다 더 간단한 API
- 자동 UI 생성
- 공유 링크 생성 가능

**적합한 사용자:**
- 최소한의 UI로 빠른 데모가 필요한 경우
- 외부 공유가 필요한 경우

**구현 예시:**
```python
import gradio as gr
from nasdaq_scanner.cli import run_analysis

def analyze(date_str, universe_path, n):
    # 분석 실행
    results = run_analysis(...)
    return results['top_movers'].to_html()

iface = gr.Interface(
    fn=analyze,
    inputs=[
        gr.Textbox(label="Date (YYYY-MM-DD)"),
        gr.File(label="Universe CSV"),
        gr.Slider(5, 50, value=10)
    ],
    outputs=gr.HTML(),
    title="NASDAQ Scanner"
)
iface.launch()
```

**장점:**
- ✅ 매우 빠른 구현 (반나절)
- ✅ 자동 공유 링크
- ✅ 간단한 API

**단점:**
- ❌ 커스터마이징 제한적
- ❌ 복잡한 레이아웃 어려움

---

### 3️⃣ **Dash (Plotly)** (고급 대시보드 ⭐⭐⭐⭐)

**추천 이유:**
- 고급 차트 및 인터랙티브 시각화
- React 기반 컴포넌트
- 실시간 업데이트 가능

**적합한 사용자:**
- 복잡한 대시보드가 필요한 경우
- 인터랙티브 차트가 중요한 경우

**구현 예시:**
```python
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from nasdaq_scanner.cli import run_analysis

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.DatePickerSingle(id='date-picker'),
    dcc.Slider(id='n-slider', min=5, max=50, value=10),
    html.Button('Run Analysis', id='run-button'),
    dcc.Graph(id='top-movers-chart'),
    html.Div(id='results-table')
])

@app.callback(
    Output('top-movers-chart', 'figure'),
    Input('run-button', 'n_clicks'),
    [State('date-picker', 'date'), State('n-slider', 'value')]
)
def update_chart(n_clicks, date, n):
    results = run_analysis(...)
    fig = px.bar(results['top_movers'], x='symbol', y='return_pct')
    return fig
```

**장점:**
- ✅ 강력한 시각화
- ✅ 인터랙티브 차트
- ✅ React 기반 (확장성)

**단점:**
- ❌ 학습 곡선 있음
- ❌ 구현 시간: 3-5일

---

### 4️⃣ **Flask/FastAPI + React** (풀스택 웹 앱 ⭐⭐⭐)

**추천 이유:**
- 완전한 커스터마이징 가능
- 프로덕션 레벨 품질
- 모바일 반응형 가능

**적합한 사용자:**
- 장기적인 프로덕트
- 복잡한 기능이 필요한 경우
- 프론트엔드 개발자와 협업 가능

**구조:**
```
src/nasdaq_scanner/
├── api/              # FastAPI 백엔드
│   ├── routes.py     # API 엔드포인트
│   └── models.py     # Pydantic 모델
└── gui/
    └── frontend/      # React 앱
        ├── src/
        └── public/
```

**구현 예시:**
```python
# api/routes.py
from fastapi import FastAPI
from nasdaq_scanner.cli import run_analysis

app = FastAPI()

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    results = run_analysis(
        request.date,
        request.universe_path,
        request.n
    )
    return {
        'top_movers': results['top_movers'].to_dict('records'),
        'bottom_movers': results['bottom_movers'].to_dict('records'),
        'volatile_movers': results['volatile_movers'].to_dict('records')
    }
```

**장점:**
- ✅ 완전한 제어
- ✅ 프로덕션 레벨
- ✅ 확장성

**단점:**
- ❌ 구현 시간: 1-2주
- ❌ 프론트엔드 개발 필요

---

### 5️⃣ **Tkinter** (데스크톱 앱 - 간단) ⭐⭐⭐

**추천 이유:**
- Python 표준 라이브러리 (추가 설치 불필요)
- 간단한 데스크톱 앱
- 오프라인 사용 가능

**적합한 사용자:**
- 데스크톱 앱 선호
- 간단한 인터페이스로 충분한 경우

**구현 예시:**
```python
import tkinter as tk
from tkinter import ttk, filedialog
from nasdaq_scanner.cli import run_analysis

class NasdaqScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NASDAQ Scanner")
        
        # 입력 필드
        ttk.Label(root, text="Date:").grid(row=0, column=0)
        self.date_entry = ttk.Entry(root)
        self.date_entry.grid(row=0, column=1)
        
        ttk.Button(root, text="Select Universe", 
                  command=self.select_universe).grid(row=1, column=0)
        
        ttk.Button(root, text="Run Analysis", 
                  command=self.run_analysis).grid(row=2, column=0)
        
        # 결과 표시
        self.results_text = tk.Text(root, height=20, width=80)
        self.results_text.grid(row=3, column=0, columnspan=2)
    
    def run_analysis(self):
        # run_analysis 호출 및 결과 표시
        pass
```

**장점:**
- ✅ 추가 의존성 없음
- ✅ 오프라인 사용
- ✅ 구현 시간: 2-3일

**단점:**
- ❌ UI가 구식
- ❌ 모던한 디자인 어려움

---

### 6️⃣ **PyQt/PySide** (데스크톱 앱 - 고급) ⭐⭐⭐

**추천 이유:**
- 프로페셔널한 데스크톱 앱
- 모던한 UI
- 강력한 위젯

**적합한 사용자:**
- 고급 데스크톱 앱이 필요한 경우
- Qt 경험이 있는 경우

**장점:**
- ✅ 프로페셔널한 UI
- ✅ 강력한 기능

**단점:**
- ❌ 학습 곡선
- ❌ 라이선스 고려 (PySide는 LGPL)
- ❌ 구현 시간: 1주

---

## 🏗️ 아키텍처 제안

현재 `run_analysis` 함수를 수정하여 결과를 반환하도록 변경하는 것을 추천합니다:

```python
# src/nasdaq_scanner/cli.py 수정
def run_analysis(
    analysis_date: date,
    universe_path: str,
    n: int = 10,
    output_path: Optional[str] = None,
    export_csv: bool = True,
    return_results: bool = False,  # 새 파라미터
) -> Optional[Dict[str, Any]]:
    """Run the complete analysis pipeline.
    
    Returns:
        If return_results=True, returns dict with:
        {
            'top_movers': DataFrame,
            'bottom_movers': DataFrame,
            'volatile_movers': DataFrame,
            'analysis_date': date,
            'stats': {
                'total_symbols': int,
                'successful_fetches': int,
                'failed_fetches': int
            }
        }
    """
    # ... 기존 로직 ...
    
    if return_results:
        return {
            'top_movers': top_movers,
            'bottom_movers': bottom_movers,
            'volatile_movers': volatile_movers,
            'analysis_date': analysis_date,
            'stats': {
                'total_symbols': len(symbols),
                'successful_fetches': len(ohlcv_df),
                'failed_fetches': len(symbols) - len(ohlcv_df)
            }
        }
    else:
        # 기존 동작 (파일 저장 또는 stdout 출력)
        ...
```

---

## 📊 비교표

| 옵션 | 구현 시간 | 난이도 | 커스터마이징 | 시각화 | 배포 | 추천도 |
|------|----------|--------|-------------|--------|------|--------|
| **Streamlit** | 1-2일 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Gradio** | 0.5일 | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Dash** | 3-5일 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Flask+React** | 1-2주 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Tkinter** | 2-3일 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **PyQt** | 1주 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 최종 추천

### 빠른 프로토타입이 필요한 경우
→ **Streamlit** 선택

**이유:**
1. 현재 프로젝트 구조와 완벽 호환
2. DataFrame 자동 렌더링
3. 1-2일 내 구현 가능
4. 배포 간편

### 장기적인 프로덕트인 경우
→ **FastAPI + React** 선택

**이유:**
1. 확장성
2. 프로덕션 레벨 품질
3. 완전한 커스터마이징

### 데스크톱 앱이 필요한 경우
→ **Tkinter** (간단) 또는 **PyQt** (고급)

---

## 🚀 다음 단계

1. **`run_analysis` 함수 수정** - 결과 반환 옵션 추가
2. **선택한 GUI 프레임워크로 프로토타입 구현**
3. **기존 CLI와 병행 사용 가능하도록 구조 유지**

---

## 📝 구현 체크리스트

### 공통 작업
- [ ] `run_analysis` 함수에 `return_results` 파라미터 추가
- [ ] 결과를 Dict로 반환하도록 수정
- [ ] 에러 처리 개선 (GUI에서 표시 가능하도록)

### Streamlit 구현 시
- [ ] `streamlit` 의존성 추가
- [ ] `src/nasdaq_scanner/gui/streamlit_app.py` 생성
- [ ] 입력 폼 구현 (날짜, 파일 업로드, 슬라이더)
- [ ] 결과 테이블 및 차트 표시
- [ ] 진행 상황 표시 (progress bar)
- [ ] 에러 메시지 표시

### 배포
- [ ] Streamlit Cloud 또는 자체 서버에 배포
- [ ] 환경 변수 설정 (API 키 등)
- [ ] 사용자 가이드 작성

---

**작성일:** 2024

