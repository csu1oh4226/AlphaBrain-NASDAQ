# [2단계] Code Smell & SOLID 진단 리포트

## 📋 진단 기준

각 항목을 다음 기준으로 평가:
- **파일경로/라인**: 문제가 있는 위치
- **문제**: 구체적인 문제 설명
- **영향**: 코드 품질/유지보수성에 미치는 영향
- **해결책**: 리팩토링 방안
- **우선순위**: High / Medium / Low

---

## 1. 네이밍 (의미 없는 변수/함수명)

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 275, 522 | `format_number` 함수 중복 정의 | 함수 충돌 가능성, 유지보수 어려움 | 하나로 통합, 공통 유틸로 이동 | **High** |
| `app.py` | 534 | `prepare_display_df` 내부 함수 | 재사용 불가, 테스트 어려움 | `ui/components.py`로 이동 | **Medium** |
| `app.py` | 169 | `categorize_failures` 내부 함수 | 재사용 불가 | `ui/components.py`로 이동 | **Medium** |
| `analytics_service.py` | 60 | `volatility_window` 파라미터 미사용 | 혼란, 불필요한 파라미터 | 제거 또는 실제 사용 | **Low** |
| `data_collector.py` | 138, 142 | 하드코딩된 `'KS11'` | KOSPI 전용 하드코딩 | `config.py`로 이동 | **Medium** |

---

## 2. 중복 코드 (DRY 위반)

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 275, 522 | `format_number` 함수 중복 | 코드 중복, 일관성 문제 | 공통 함수로 통합 | **High** |
| `app.py` | 290-313, 319-342 | 관찰/주의 종목 렌더링 로직 중복 | 약 50줄 중복 | 공통 함수 추출 | **High** |
| `app.py` | 571-630 | TOP N 테이블 렌더링 로직 중복 | 3개 테이블이 거의 동일한 로직 | 공통 함수 추출 | **High** |
| `analytics_service.py` | 110-115, 217-222 | NaN/inf 필터링 로직 중복 | 동일한 필터링 로직 반복 | 헬퍼 함수 추출 | **Medium** |
| `analysis_functions.py` | 57-61, 107-111 | 0으로 나누기 방지 로직 중복 | `np.where(open != 0, ...)` 반복 | 헬퍼 함수 추출 | **Low** |

---

## 3. 긴 함수/긴 클래스 (Long Method/God Class)

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 전체 | 691줄의 거대한 파일 | 가독성 저하, 테스트 어려움 | 기능별로 분리 (UI 컴포넌트, 비즈니스 로직) | **High** |
| `app.py` | 361-503 | `if run_button:` 블록이 142줄 | 복잡도 높음, 단일 책임 위반 | 함수로 추출 | **High** |
| `app.py` | 505-656 | 결과 표시 로직 151줄 | 복잡도 높음 | 함수로 추출 | **High** |
| `financedatareader_provider.py` | 69-157 | `fetch_price_data` 메서드 88줄 | 복잡도 높음 | 헬퍼 메서드로 분리 | **Medium** |
| `analytics_service.py` | 57-157 | `compute_metrics` 메서드 100줄 | 복잡도 높음 | 단계별로 함수 분리 | **Medium** |

---

## 4. 과도한 if/else 분기 (조건문 폭발)

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|--------|--------|---------|
| `app.py` | 94-138 | 티커 소스 선택 if/elif 체인 44줄 | 가독성 저하, 확장 어려움 | 전략 패턴 또는 딕셔너리 매핑 | **Medium** |
| `data_collector.py` | 123-143 | Provider 선택 if/elif 체인 | 가독성 저하 | 팩토리 패턴 또는 딕셔너리 매핑 | **Medium** |
| `app.py` | 169-200 | `categorize_failures` if/elif 체인 | 가독성 저하 | 딕셔너리 매핑 또는 Enum 사용 | **Low** |
| `app.py` | 378-385 | 시장 타입별 메시지 분기 | 중복 로직 | 딕셔너리 매핑 | **Low** |

---

## 5. 매직 넘버/하드코딩

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 231, 248 | `top_n * 2` 하드코딩 | 의미 불명확 | 상수로 정의 | **Medium** |
| `app.py` | 100, 110 | `total_tickers = 100` 하드코딩 | 실제 값과 불일치 가능 | 동적 계산 또는 상수 | **Low** |
| `data_collector.py` | 65, 138, 142 | `top_n=100`, `'KS11'` 하드코딩 | 유연성 부족 | `config.py`로 이동 | **Medium** |
| `analytics_service.py` | 98 | `window=5` 하드코딩 | 의미 불명확 | `DEFAULT_VOLATILITY_WINDOW` 사용 | **Low** |
| `app.py` | 152-156 | 슬라이더 범위 `5-20` 하드코딩 | `config.py`와 불일치 가능 | `config.py` 상수 사용 | **Low** |

---

## 6. 전역 상태/사이드 이펙트

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 55 | `_analytics_service` 전역 변수 | 테스트 어려움, 의존성 주입 불가 | 함수 파라미터로 전달 | **Medium** |
| `financedatareader_provider.py` | 46 | `_request_cache` 모듈 레벨 캐시 | 테스트 격리 어려움, 메모리 누수 가능 | 클래스 인스턴스 변수로 이동 | **Medium** |
| `app.py` | 367, 370, 488-493 | `st.session_state` 과도한 사용 | 상태 관리 복잡도 증가 | 상태 관리 로직 분리 | **Low** |

---

## 7. 예외처리 불일치

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 127 | `except:` 빈 예외 처리 | 모든 예외 무시, 디버깅 어려움 | 구체적 예외 처리 | **High** |
| `app.py` | 283, 530 | `except:` 빈 예외 처리 | 모든 예외 무시 | 구체적 예외 처리 | **High** |
| `analytics_service.py` | 112-128 | 예외 처리 없이 빈 DataFrame 반환 | 실패 원인 파악 어려움 | 로깅 추가 | **Medium** |
| `data_collector.py` | 112-114 | 예외를 다시 raise만 함 | 상위 레벨에서만 처리 | 구체적 예외 타입 사용 | **Low** |

---

## 8. 의존성 얽힘 (모듈 간 결합도 높음)

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 25-42 | 많은 import, 직접 의존성 | 결합도 높음, 테스트 어려움 | 의존성 주입 패턴 | **Medium** |
| `analytics_service.py` | 13 | `from nasdaq_scanner.providers import collect_data` | 직접 import | 인터페이스 의존 | **Low** |
| `data_collector.py` | 16-21 | 여러 모듈 직접 import | 결합도 높음 | 인터페이스 기반 설계 | **Low** |

---

## 9. 테스트하기 어려운 구조

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 전체 | Streamlit 의존성 강함 | 단위 테스트 어려움 | 비즈니스 로직 분리 | **High** |
| `app.py` | 55 | 전역 서비스 인스턴스 | Mock 어려움 | 의존성 주입 | **Medium** |
| `financedatareader_provider.py` | 46 | 모듈 레벨 캐시 | 테스트 격리 어려움 | 인스턴스 변수로 이동 | **Medium** |
| `app.py` | 23 | `sys.path.insert` 직접 조작 | 테스트 환경 의존 | 패키지 구조 개선 | **Low** |

---

## 10. SOLID 위반 가능성

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `app.py` | 전체 | 단일 책임 위반 (UI + 비즈니스 로직) | 유지보수 어려움 | UI와 로직 분리 | **High** |
| `analytics_service.py` | 57-157 | `compute_metrics` 너무 많은 책임 | 단일 책임 위반 | 단계별 함수 분리 | **Medium** |
| `data_collector.py` | 123-143 | Provider 선택 로직이 함수 내부 | 개방-폐쇄 원칙 위반 | 팩토리 패턴 | **Medium** |
| `app.py` | 55 | 전역 서비스 인스턴스 | 의존성 역전 원칙 위반 | 의존성 주입 | **Medium** |
| `financedatareader_provider.py` | 46 | 모듈 레벨 캐시 | 단일 책임 위반 | 캐시 관리자 분리 | **Low** |

---

## 11. Dead Code (사용 안 하는 코드)

| 파일경로 | 라인 | 문제 | 영향 | 해결책 | 우선순위 |
|---------|------|------|------|--------|---------|
| `core/analytics.py` | 전체 | 레거시 모듈, 미사용 | 혼란, 유지보수 부담 | 제거 또는 격리 | **Medium** |
| `core/metrics.py` | 전체 | 레거시 모듈, 미사용 | 혼란 | 제거 또는 격리 | **Medium** |
| `core/ranking.py` | 전체 | 레거시 모듈, 미사용 | 혼란 | 제거 또는 격리 | **Medium** |
| `core/recommender.py` | 전체 | 레거시 모듈, 미사용 | 혼란 | 제거 또는 격리 | **Medium** |
| `core/signal_generator.py` | 전체 | 레거시 모듈, 미사용 | 혼란 | 제거 또는 격리 | **Medium** |
| `core/kosdaq_universe.py` | 전체 | `korea_universe.py`와 중복 가능 | 혼란 | 통합 또는 제거 | **Medium** |
| `providers/data_provider.py` | 전체 | yfinance 기반, 미사용 | 혼란 | 제거 또는 격리 | **Medium** |
| `providers/fetch_ohlcv.py` | 전체 | yfinance 기반, 미사용 | 혼란 | 제거 또는 격리 | **Medium** |
| `cli.py` | 전체 | CLI 엔트리포인트, 미사용 | 혼란 | 제거 또는 격리 | **Low** |
| `app_streamlit.py` | 전체 | `app.py`와 중복 가능 | 혼란 | 확인 후 제거 | **Low** |
| `core/signals.py` | 17 | `import logging` 누락 (logger 사용) | 런타임 오류 가능 | import 추가 | **High** |

---

## 📊 우선순위 요약

### High Priority (즉시 처리)
1. `app.py`의 `format_number` 중복 제거
2. `app.py`의 관찰/주의 종목 렌더링 중복 제거
3. `app.py`의 TOP N 테이블 렌더링 중복 제거
4. `app.py`의 빈 `except:` 구문 수정
5. `core/signals.py`의 `import logging` 누락 수정
6. `app.py`의 거대한 파일 분리 (UI와 로직 분리)

### Medium Priority (단기 처리)
7. `app.py`의 긴 함수 분리
8. 레거시 모듈 제거 또는 격리
9. 하드코딩된 값들을 `config.py`로 이동
10. 전역 상태를 인스턴스 변수로 변경
11. Provider 선택 로직 개선 (팩토리 패턴)

### Low Priority (장기 개선)
12. 조건문 폭발 개선 (전략 패턴)
13. 의존성 주입 패턴 도입
14. 테스트 격리 개선

---

## 🎯 다음 단계

3단계에서 위 우선순위를 기반으로 커밋 플랜을 수립합니다.

