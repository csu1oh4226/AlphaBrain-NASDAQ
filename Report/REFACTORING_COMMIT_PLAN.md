# [3단계] 리팩토링 커밋 플랜

## 📋 커밋 규칙

- 각 커밋은 **하나의 리팩토링**만 수행
- 각 커밋 후 **테스트 통과 확인**
- **기능 변경 없음** (동작 동일 유지)
- Conventional Commits 스타일 사용

---

## 🎯 커밋 플랜 (우선순위 순)

### A) 포맷/정렬 (최소 변경)

#### Commit A1: Fix missing import in signals.py
- **타입**: `fix`
- **변경 요약**: `core/signals.py`에 누락된 `import logging` 추가
- **변경 파일**: 
  - `src/nasdaq_scanner/core/signals.py`
- **검증 방법**: 
  ```bash
  python -c "from nasdaq_scanner.core.signals import generate_signals; print('OK')"
  pytest tests/unit/test_signals.py -v
  ```

---

### B) Rename (가독성 개선)

#### Commit B1: Extract format_number to ui/components.py
- **타입**: `refactor`
- **변경 요약**: `app.py`의 중복된 `format_number` 함수를 `ui/components.py`로 통합
- **변경 파일**: 
  - `src/nasdaq_scanner/ui/components.py` (추가)
  - `app.py` (수정: 중복 제거, import 추가)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  python -c "import streamlit; from app import *; print('Import OK')"
  ```

---

### C) Extract Method / Decompose Conditional (복잡도 낮추기)

#### Commit C1: Extract render_stock_card to ui/components.py
- **타입**: `refactor`
- **변경 요약**: `app.py`의 관찰/주의 종목 렌더링 로직을 공통 함수로 추출
- **변경 파일**: 
  - `src/nasdaq_scanner/ui/components.py` (추가)
  - `app.py` (수정: 중복 제거)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: Streamlit 앱 실행하여 UI 확인
  ```

#### Commit C2: Extract render_top_rankings_table to ui/components.py
- **타입**: `refactor`
- **변경 요약**: `app.py`의 TOP N 테이블 렌더링 로직을 공통 함수로 추출
- **변경 파일**: 
  - `src/nasdaq_scanner/ui/components.py` (추가)
  - `app.py` (수정: 중복 제거)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: Streamlit 앱 실행하여 테이블 확인
  ```

#### Commit C3: Extract categorize_failures to ui/components.py
- **타입**: `refactor`
- **변경 요약**: `app.py`의 `categorize_failures` 함수를 `ui/components.py`로 이동
- **변경 파일**: 
  - `src/nasdaq_scanner/ui/components.py` (추가)
  - `app.py` (수정: 함수 제거, import 추가)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: Streamlit 앱 실행하여 실패 요약 확인
  ```

#### Commit C4: Extract prepare_display_df to ui/components.py
- **타입**: `refactor`
- **변경 요약**: `app.py`의 `prepare_display_df` 함수를 `ui/components.py`로 이동
- **변경 파일**: 
  - `src/nasdaq_scanner/ui/components.py` (추가)
  - `app.py` (수정: 함수 제거, import 추가)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: Streamlit 앱 실행하여 표시 확인
  ```

#### Commit C5: Extract data collection logic from app.py
- **타입**: `refactor`
- **변경 요약**: `app.py`의 데이터 수집 로직(361-503줄)을 함수로 추출
- **변경 파일**: 
  - `app.py` (수정: 함수 추출)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: Streamlit 앱 실행하여 데이터 수집 확인
  ```

#### Commit C6: Extract result display logic from app.py
- **타입**: `refactor`
- **변경 요약**: `app.py`의 결과 표시 로직(505-656줄)을 함수로 추출
- **변경 파일**: 
  - `app.py` (수정: 함수 추출)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: Streamlit 앱 실행하여 결과 표시 확인
  ```

---

### D) 중복 제거 (공통 함수/모듈화)

#### Commit D1: Extract filter_nan_inf helper function
- **타입**: `refactor`
- **변경 요약**: `analytics_service.py`의 NaN/inf 필터링 로직을 헬퍼 함수로 추출
- **변경 파일**: 
  - `src/nasdaq_scanner/core/analysis_functions.py` (추가)
  - `src/nasdaq_scanner/services/analytics_service.py` (수정)
- **검증 방법**: 
  ```bash
  pytest tests/unit/test_analytics_service.py -v
  pytest tests/unit/test_analysis_functions.py -v
  ```

#### Commit D2: Extract zero division guard helper function
- **타입**: `refactor`
- **변경 요약**: `analysis_functions.py`의 0으로 나누기 방지 로직을 헬퍼 함수로 추출
- **변경 파일**: 
  - `src/nasdaq_scanner/core/analysis_functions.py` (수정)
- **검증 방법**: 
  ```bash
  pytest tests/unit/test_analysis_functions.py -v
  ```

---

### E) 에러 처리 정책 통일

#### Commit E1: Replace bare except with specific exceptions
- **타입**: `fix`
- **변경 요약**: `app.py`의 빈 `except:` 구문을 구체적 예외 처리로 변경
- **변경 파일**: 
  - `app.py` (수정: 127줄, 283줄, 530줄)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: 예외 상황 테스트
  ```

#### Commit E2: Add logging to empty DataFrame returns
- **타입**: `refactor`
- **변경 요약**: `analytics_service.py`의 빈 DataFrame 반환 시 로깅 추가
- **변경 파일**: 
  - `src/nasdaq_scanner/services/analytics_service.py` (수정)
- **검증 방법**: 
  ```bash
  pytest tests/unit/test_analytics_service.py -v
  ```

---

### F) 모듈 경계 정리

#### Commit F1: Move hardcoded values to config.py
- **타입**: `refactor`
- **변경 요약**: 하드코딩된 값들을 `config.py`로 이동
- **변경 파일**: 
  - `src/nasdaq_scanner/config.py` (추가)
  - `app.py` (수정: 상수 사용)
  - `data_collector.py` (수정: 상수 사용)
  - `analytics_service.py` (수정: 상수 사용)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  ```

#### Commit F2: Move module-level cache to instance variable
- **타입**: `refactor`
- **변경 요약**: `financedatareader_provider.py`의 모듈 레벨 캐시를 인스턴스 변수로 이동
- **변경 파일**: 
  - `src/nasdaq_scanner/providers/financedatareader_provider.py` (수정)
- **검증 방법**: 
  ```bash
  pytest tests/unit/test_financedatareader_provider.py -v
  ```

---

### G) Dead Code 제거

#### Commit G1: Remove unused legacy modules (Phase 1)
- **타입**: `refactor`
- **변경 요약**: 사용되지 않는 레거시 모듈 제거 (1차)
- **변경 파일**: 
  - `src/nasdaq_scanner/core/analytics.py` (제거 또는 격리)
  - `src/nasdaq_scanner/core/metrics.py` (제거 또는 격리)
  - `src/nasdaq_scanner/core/ranking.py` (제거 또는 격리)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  grep -r "from.*analytics import\|from.*metrics import\|from.*ranking import" src/ tests/
  ```

#### Commit G2: Remove unused legacy modules (Phase 2)
- **타입**: `refactor`
- **변경 요약**: 사용되지 않는 레거시 모듈 제거 (2차)
- **변경 파일**: 
  - `src/nasdaq_scanner/core/recommender.py` (제거 또는 격리)
  - `src/nasdaq_scanner/core/signal_generator.py` (제거 또는 격리)
  - `src/nasdaq_scanner/providers/data_provider.py` (제거 또는 격리)
  - `src/nasdaq_scanner/providers/fetch_ohlcv.py` (제거 또는 격리)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  grep -r "from.*recommender import\|from.*signal_generator import\|from.*data_provider import\|from.*fetch_ohlcv import" src/ tests/
  ```

#### Commit G3: Remove or consolidate duplicate files
- **타입**: `refactor`
- **변경 요약**: 중복 파일 제거 또는 통합
- **변경 파일**: 
  - `app_streamlit.py` (확인 후 제거)
  - `src/nasdaq_scanner/core/kosdaq_universe.py` (확인 후 통합 또는 제거)
  - `src/nasdaq_scanner/cli.py` (확인 후 제거 또는 격리)
- **검증 방법**: 
  ```bash
  pytest tests/unit/ -v
  # 수동: 각 파일 사용 여부 확인
  ```

---

### H) 테스트 보강 (선택적)

#### Commit H1: Add tests for ui/components.py functions
- **타입**: `test`
- **변경 요약**: 새로 추출한 UI 컴포넌트 함수들에 대한 테스트 추가
- **변경 파일**: 
  - `tests/unit/test_ui_components.py` (신규)
- **검증 방법**: 
  ```bash
  pytest tests/unit/test_ui_components.py -v
  ```

---

## 📊 커밋 순서 요약

1. **A1**: Fix missing import (즉시 수정)
2. **B1**: Extract format_number
3. **C1-C6**: Extract methods (복잡도 낮추기)
4. **D1-D2**: 중복 제거
5. **E1-E2**: 에러 처리 개선
6. **F1-F2**: 모듈 경계 정리
7. **G1-G3**: Dead code 제거
8. **H1**: 테스트 보강 (선택적)

---

## ⚠️ 주의사항

1. **각 커밋 후 반드시 테스트 실행**
2. **기능 변경 없음 확인** (동작 동일)
3. **레거시 모듈 제거 전 사용 여부 확인** (`grep` 사용)
4. **중복 파일 제거 전 내용 비교**

---

## 🎯 다음 단계

4단계에서 위 커밋 플랜을 순서대로 실행합니다.

