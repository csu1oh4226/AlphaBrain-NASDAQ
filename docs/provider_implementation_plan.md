# Provider 구현 계획 및 데이터 흐름 분석

## 📋 현재 상태 분석

### 1. 아키텍처 구조 (README 기준)

```
Providers (데이터 수집 레이어)
  ↓
Services (비즈니스 로직 레이어)
  ↓
Core (핵심 분석 로직 - 순수 함수)
  ↓
UI (사용자 인터페이스)
```

### 2. MarketDataProvider 인터페이스 (`base.py`)

**정의된 메서드:**
- `fetch_price_data(symbols, target_date, max_retries) -> (DataFrame, List[str])`
  - 반환: `(ticker, date, close, volume)` 컬럼을 가진 DataFrame
  - 실패한 티커 리스트 반환
  
- `fetch_single_symbol(symbol, target_date, max_retries) -> Series`
  - 반환: `['ticker', 'date', 'close', 'volume']` 인덱스를 가진 Series

**현재 인터페이스의 한계:**
- ❌ OHLCV 데이터를 반환하지 않음 (close, volume만)
- ❌ 기간/간격 파라미터가 없음 (특정 날짜만)
- ❌ `fetch_ohlcv.py`의 기능과 불일치

### 3. YFinanceProvider 구현 상태 (`yfinance_provider.py`)

**✅ 구현된 부분:**
- `MarketDataProvider` 인터페이스 상속
- `fetch_price_data()` 구현 (close, volume만 반환)
- `fetch_single_symbol()` 구현 (close, volume만 반환)
- 재시도 로직 포함
- 에러 처리 및 로깅

**❌ 미구현/문제점:**
- OHLCV 데이터 반환 불가 (open, high, low 누락)
- 특정 날짜만 지원 (기간/간격 파라미터 없음)
- `fetch_ohlcv.py`의 기능과 중복이지만 통합되지 않음

### 4. fetch_ohlcv.py (별도 구현)

**기능:**
- ✅ OHLCV 데이터 반환 (ticker, date, open, high, low, close, volume)
- ✅ 기간/간격 파라미터 지원 (period, interval)
- ✅ MultiIndex DataFrame을 tidy format으로 변환
- ❌ `MarketDataProvider` 인터페이스를 따르지 않음

---

## 🎯 구현 계획

### Phase 1: 인터페이스 확장 (최소 기능)

#### 1.1 MarketDataProvider 인터페이스 확장

**옵션 A: 기존 메서드 확장 (권장)**
```python
@abstractmethod
def fetch_price_data(
    self,
    symbols: List[str],
    target_date: date,
    max_retries: int = 2,
    include_ohlcv: bool = False,  # 새 파라미터
) -> Tuple[DataFrame, List[str]]:
    """Fetch price data for multiple symbols.
    
    Args:
        include_ohlcv: If True, return OHLCV data (open, high, low, close, volume).
                      If False, return only close and volume (backward compatible).
    """
```

**옵션 B: 새 메서드 추가**
```python
@abstractmethod
def fetch_ohlcv_data(
    self,
    symbols: List[str],
    period: str,
    interval: str,
    max_retries: int = 2,
) -> Tuple[DataFrame, List[str]]:
    """Fetch OHLCV data for multiple symbols.
    
    Args:
        symbols: List of ticker symbols.
        period: Period to fetch (e.g., "1d", "5d", "1mo").
        interval: Data interval (e.g., "1d", "1h", "5m").
    
    Returns:
        Tuple of:
        - DataFrame with columns: ticker, date, open, high, low, close, volume
        - List of failed ticker symbols
    """
```

**권장: 옵션 B (새 메서드 추가)**
- 기존 코드와의 호환성 유지
- 명확한 책임 분리
- 점진적 마이그레이션 가능

#### 1.2 YFinanceProvider 구현

**구현 내용:**
```python
def fetch_ohlcv_data(
    self,
    symbols: List[str],
    period: str,
    interval: str,
    max_retries: int = 2,
) -> Tuple[DataFrame, List[str]]:
    """Fetch OHLCV data using yfinance.download."""
    # fetch_ohlcv.py의 로직 재사용
    # MultiIndex → tidy format 변환
    # 실패한 티커 추적
```

**기존 `fetch_ohlcv.py` 통합:**
- `_convert_to_tidy_format()` 함수 재사용
- `yfinance.download()` 호출 로직 재사용
- 에러 처리 및 재시도 로직 추가

---

## 📊 데이터 흐름 분석

### 현재 흐름: `data_collector.py` → Provider → DataFrame

```
1. load_ticker_list(ticker_source)
   └─> List[str] (티커 리스트)
   
2. provider = YFinanceProvider() (기본값)
   
3. provider.fetch_price_data(symbols, target_date, max_retries)
   └─> (DataFrame, List[str])
       DataFrame: ticker, date, close, volume
       List[str]: 실패한 티커들
   
4. collect_data() 반환
   └─> (DataFrame, List[str])
```

### 개선된 흐름: OHLCV 데이터 수집

```
1. load_ticker_list(ticker_source)
   └─> List[str] (티커 리스트)
   
2. provider = YFinanceProvider()
   
3. provider.fetch_ohlcv_data(symbols, period, interval, max_retries)
   └─> (DataFrame, List[str])
       DataFrame: ticker, date, open, high, low, close, volume
       List[str]: 실패한 티커들
   
4. collect_data() 또는 새로운 collect_ohlcv_data() 반환
   └─> (DataFrame, List[str])
```

---

## 🔧 구현 단계

### Step 1: 인터페이스 확장
- [ ] `base.py`에 `fetch_ohlcv_data()` 추상 메서드 추가
- [ ] 문서화 및 타입힌트 추가

### Step 2: YFinanceProvider 구현
- [ ] `fetch_ohlcv_data()` 메서드 구현
- [ ] `fetch_ohlcv.py`의 `_convert_to_tidy_format()` 로직 통합
- [ ] 에러 처리 및 재시도 로직 추가
- [ ] 단일/다중 티커 모두 지원

### Step 3: data_collector.py 확장
- [ ] `collect_ohlcv_data()` 함수 추가 (선택사항)
- [ ] 기존 `collect_data()`는 유지 (하위 호환성)

### Step 4: 테스트
- [ ] 단위 테스트 작성 (RED)
- [ ] 구현 (GREEN)
- [ ] 통합 테스트

### Step 5: 리팩토링
- [ ] `fetch_ohlcv.py`의 중복 코드 제거
- [ ] 기존 코드에서 `fetch_ohlcv()` 호출을 provider로 마이그레이션

---

## 📝 상세 구현 계획

### 1. base.py 수정

```python
class MarketDataProvider(ABC):
    # 기존 메서드 유지 (하위 호환성)
    
    @abstractmethod
    def fetch_ohlcv_data(
        self,
        symbols: List[str],
        period: str,
        interval: str,
        max_retries: int = 2,
    ) -> Tuple[DataFrame, List[str]]:
        """Fetch OHLCV data for multiple symbols.
        
        Args:
            symbols: List of ticker symbols to fetch.
            period: Period to fetch (e.g., "1d", "5d", "1mo", "1y").
            interval: Data interval (e.g., "1d", "1h", "5m").
            max_retries: Maximum number of retries for failed requests.
        
        Returns:
            Tuple of:
            - DataFrame with columns: ticker, date, open, high, low, close, volume
            - List of failed ticker symbols
        
        Raises:
            Implementation-specific exceptions for critical errors.
        """
        pass
```

### 2. yfinance_provider.py 수정

```python
class YFinanceProvider(MarketDataProvider):
    def fetch_ohlcv_data(
        self,
        symbols: List[str],
        period: str,
        interval: str,
        max_retries: int = 2,
    ) -> Tuple[DataFrame, List[str]]:
        """Fetch OHLCV data using yfinance.download."""
        if not symbols:
            return pd.DataFrame(
                columns=["ticker", "date", "open", "high", "low", "close", "volume"]
            ), []
        
        failed_symbols: List[str] = []
        
        for attempt in range(max_retries + 1):
            try:
                # yfinance.download 호출
                df = yf.download(
                    symbols,
                    period=period,
                    interval=interval,
                    group_by="ticker",
                    progress=False,
                )
                
                if df.empty:
                    if attempt < max_retries:
                        continue
                    # 모든 티커 실패
                    return pd.DataFrame(
                        columns=["ticker", "date", "open", "high", "low", "close", "volume"]
                    ), symbols
                
                # MultiIndex → tidy format 변환
                tidy_df = self._convert_to_tidy_format(df, symbols)
                
                # 실패한 티커 확인 (요청한 티커 중 결과에 없는 것)
                fetched_tickers = set(tidy_df["ticker"].unique())
                failed_symbols = [s for s in symbols if s not in fetched_tickers]
                
                return tidy_df, failed_symbols
                
            except Exception as e:
                if attempt < max_retries:
                    logger.debug(f"Retry {attempt + 1}/{max_retries}")
                    continue
                else:
                    logger.error(f"Failed after {max_retries} retries: {e}")
                    return pd.DataFrame(
                        columns=["ticker", "date", "open", "high", "low", "close", "volume"]
                    ), symbols
    
    def _convert_to_tidy_format(
        self,
        df: DataFrame,
        tickers: List[str],
    ) -> DataFrame:
        """Convert yfinance MultiIndex DataFrame to tidy format.
        
        (fetch_ohlcv.py의 _convert_to_tidy_format 로직 재사용)
        """
        # 기존 fetch_ohlcv.py의 로직 재사용
        pass
```

### 3. data_collector.py 확장 (선택사항)

```python
def collect_ohlcv_data(
    ticker_source: Union[str, Path, List[str]],
    period: str,
    interval: str,
    provider: Optional[MarketDataProvider] = None,
    max_retries: int = 2,
) -> Tuple[DataFrame, List[str]]:
    """Collect OHLCV data for tickers from specified source.
    
    Args:
        ticker_source: Source of ticker list.
        period: Period to fetch (e.g., "1d", "5d", "1mo").
        interval: Data interval (e.g., "1d", "1h", "5m").
        provider: MarketDataProvider instance. If None, uses YFinanceProvider.
        max_retries: Maximum number of retries.
    
    Returns:
        Tuple of:
        - DataFrame with columns: ticker, date, open, high, low, close, volume
        - List of failed ticker symbols
    """
    # 티커 리스트 로드
    symbols = load_ticker_list(ticker_source)
    
    if not symbols:
        return pd.DataFrame(
            columns=["ticker", "date", "open", "high", "low", "close", "volume"]
        ), []
    
    # Provider 사용
    if provider is None:
        provider = YFinanceProvider()
    
    # OHLCV 데이터 수집
    df, failed_symbols = provider.fetch_ohlcv_data(
        symbols=symbols,
        period=period,
        interval=interval,
        max_retries=max_retries,
    )
    
    return df, failed_symbols
```

---

## 🔄 마이그레이션 전략

### 기존 코드와의 호환성

1. **기존 `fetch_price_data()` 유지**
   - close, volume만 필요한 경우 계속 사용
   - 하위 호환성 보장

2. **새로운 `fetch_ohlcv_data()` 추가**
   - OHLCV가 필요한 경우 사용
   - 점진적 마이그레이션

3. **`fetch_ohlcv.py` 단계적 제거**
   - 먼저 provider로 마이그레이션
   - 모든 호출부 변경 후 제거
   - 또는 내부적으로 `fetch_ohlcv()`가 provider를 사용하도록 변경

---

## ✅ 체크리스트

### 인터페이스 구현 확인
- [ ] `YFinanceProvider`가 `MarketDataProvider`를 상속하는가?
- [ ] `fetch_price_data()` 메서드가 구현되어 있는가?
- [ ] `fetch_single_symbol()` 메서드가 구현되어 있는가?
- [ ] `fetch_ohlcv_data()` 메서드가 구현되어 있는가? (추가 필요)

### 데이터 흐름 확인
- [ ] `data_collector.py`에서 provider를 통해 티커 리스트를 받는가?
- [ ] provider의 `fetch_price_data()`를 호출하는가?
- [ ] 결과를 DataFrame으로 합치는가?
- [ ] 실패한 티커를 별도로 반환하는가?

---

## 📚 참고 자료

- [README.md](../README.md) - 아키텍처 설명
- [base.py](../src/nasdaq_scanner/providers/base.py) - 인터페이스 정의
- [yfinance_provider.py](../src/nasdaq_scanner/providers/yfinance_provider.py) - 현재 구현
- [fetch_ohlcv.py](../src/nasdaq_scanner/providers/fetch_ohlcv.py) - OHLCV 수집 로직
- [data_collector.py](../src/nasdaq_scanner/providers/data_collector.py) - 데이터 수집 모듈

