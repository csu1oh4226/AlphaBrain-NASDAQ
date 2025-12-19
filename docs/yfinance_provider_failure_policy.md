# YFinanceProvider 실패 처리 정책

## 📋 개요

이 문서는 `YFinanceProvider`가 다양한 실패 상황을 어떻게 처리하는지 정의합니다.
테스트를 통해 이 정책들이 고정되어 있으며, 변경 시 테스트도 함께 업데이트되어야 합니다.

---

## 🔍 실패 처리 정책

### 1. `fetch_single_symbol()` 실패 정책

#### 1.1 빈 History (잘못된 티커)
**상황**: `yfinance.Ticker().history()`가 빈 DataFrame을 반환  
**정책**: `None` 반환  
**이유**: 티커가 존재하지 않거나 데이터가 없는 경우

```python
# 예시
result = provider.fetch_single_symbol("INVALID_TICKER", date(2024, 1, 15))
assert result is None
```

#### 1.2 예외 발생
**상황**: `yfinance.Ticker().history()` 호출 중 예외 발생 (네트워크 오류 등)  
**정책**: 
- `max_retries` 횟수만큼 재시도
- 모든 재시도 실패 시 `None` 반환
- 예외는 로깅되지만 호출자에게 전파되지 않음

```python
# 예시
result = provider.fetch_single_symbol("ERROR_TICKER", date(2024, 1, 15), max_retries=2)
assert result is None  # 재시도 후에도 실패하면 None
```

#### 1.3 Target Date가 History에 없음
**상황**: 요청한 날짜가 거래일이 아니거나 history에 없음  
**정책**: 
- 가장 가까운 이전 거래일의 데이터 사용
- 이전 거래일도 없으면 `None` 반환
- 반환된 Series의 `date` 필드는 여전히 원래 `target_date` 값 (데이터는 이전 거래일)

```python
# 예시: 주말 요청 시 금요일 데이터 사용
result = provider.fetch_single_symbol("AAPL", date(2024, 1, 14))  # Sunday
# 금요일(2024-01-12) 데이터를 사용하지만, result["date"]는 여전히 2024-01-14
```

---

### 2. `fetch_price_data()` 실패 정책

#### 2.1 일부 티커 실패
**상황**: 여러 티커 중 일부만 실패  
**정책**: 
- 성공한 티커는 DataFrame에 포함
- 실패한 티커는 `failed_symbols` 리스트에 추가
- DataFrame은 성공한 티커만 포함 (부분 성공 허용)

```python
# 예시
symbols = ["AAPL", "INVALID_TICKER", "MSFT"]
df, failed = provider.fetch_price_data(symbols, date(2024, 1, 15))

assert len(df) == 2  # AAPL, MSFT만 성공
assert len(failed) == 1
assert "INVALID_TICKER" in failed
assert set(df["ticker"].unique()) == {"AAPL", "MSFT"}
```

#### 2.2 모든 티커 실패
**상황**: 요청한 모든 티커가 실패  
**정책**: 
- 빈 DataFrame 반환 (컬럼은 유지: `["ticker", "date", "close", "volume"]`)
- 모든 티커를 `failed_symbols` 리스트에 추가
- 예외를 발생시키지 않음

```python
# 예시
symbols = ["INVALID1", "INVALID2"]
df, failed = provider.fetch_price_data(symbols, date(2024, 1, 15))

assert len(df) == 0
assert list(df.columns) == ["ticker", "date", "close", "volume"]
assert len(failed) == 2
assert set(failed) == {"INVALID1", "INVALID2"}
```

#### 2.3 예외 발생
**상황**: 특정 티커 처리 중 예외 발생  
**정책**: 
- 예외를 잡아서 로깅
- 해당 티커를 `failed_symbols`에 추가
- 다른 티커 처리는 계속 진행 (예외 전파 없음)

```python
# 예시
symbols = ["AAPL", "ERROR_TICKER", "MSFT"]
# ERROR_TICKER가 예외 발생
df, failed = provider.fetch_price_data(symbols, date(2024, 1, 15), max_retries=0)

assert len(df) == 2  # AAPL, MSFT는 성공
assert "ERROR_TICKER" in failed
```

#### 2.4 빈 티커 리스트
**상황**: 빈 티커 리스트 전달  
**정책**: 
- 빈 DataFrame 반환 (컬럼은 유지)
- 빈 `failed_symbols` 리스트 반환

```python
# 예시
symbols = []
df, failed = provider.fetch_price_data(symbols, date(2024, 1, 15))

assert len(df) == 0
assert list(df.columns) == ["ticker", "date", "close", "volume"]
assert len(failed) == 0
```

---

## ✅ 정책 검증

모든 실패 정책은 `tests/unit/test_yfinance_provider.py`에 테스트로 고정되어 있습니다:

- `test_fetch_single_symbol_handles_empty_history()` - 빈 history 처리
- `test_fetch_single_symbol_handles_exception()` - 예외 처리
- `test_fetch_single_symbol_uses_closest_previous_trading_day()` - 이전 거래일 사용
- `test_fetch_price_data_handles_invalid_tickers()` - 일부 티커 실패
- `test_fetch_price_data_returns_empty_dataframe_when_all_tickers_fail()` - 모든 티커 실패
- `test_fetch_price_data_handles_exceptions_gracefully()` - 예외 처리
- `test_fetch_price_data_handles_empty_symbols_list()` - 빈 리스트 처리

---

## 🔄 정책 변경 시 주의사항

1. **정책 변경 시 테스트 업데이트 필수**
   - 실패 정책을 변경하면 해당 테스트도 함께 수정해야 합니다.
   - 테스트는 정책의 단일 진실 공급원(single source of truth)입니다.

2. **하위 호환성 고려**
   - 정책 변경은 기존 호출 코드에 영향을 줄 수 있습니다.
   - 변경 전 호출부를 확인하고 필요시 마이그레이션 가이드 제공.

3. **문서화**
   - 정책 변경 시 이 문서도 함께 업데이트해야 합니다.

---

## 📚 참고 자료

- [테스트 파일](../tests/unit/test_yfinance_provider.py)
- [YFinanceProvider 구현](../src/nasdaq_scanner/providers/yfinance_provider.py)
- [MarketDataProvider 인터페이스](../src/nasdaq_scanner/providers/base.py)

