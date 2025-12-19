"""FinanceDataReader implementation of MarketDataProvider for KOSDAQ.

This module provides FinanceDataReader-based implementation for fetching KOSDAQ data.
Uses KQ11 (KOSDAQ Composite Index) as primary source, falls back to individual stocks if needed.

Data Source Priority:
1. KQ11 (KOSDAQ Composite Index) - Primary
2. Individual KOSDAQ stocks - Fallback

Data Format:
- FinanceDataReader returns: DataFrame with Date index, Open, High, Low, Close, Volume columns
- Provider returns: DataFrame/Series with columns (ticker, date, open, high, low, close, volume)

Features:
- No API key required
- Caching to prevent duplicate requests
- Exponential backoff retry (max 3 attempts)
- Detailed error categorization
- Support for KOSDAQ index (KQ11) and individual stocks
"""

import logging
import pandas as pd
import time
from datetime import date, timedelta
from typing import List, Tuple, Optional, Dict
from pandas import DataFrame, Series

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = None

from nasdaq_scanner.providers.base import MarketDataProvider
from nasdaq_scanner.config import (
    DEFAULT_MAX_RETRIES,
    MAX_FAILED_SYMBOLS_DISPLAY,
)

logger = logging.getLogger(__name__)

# OHLCV columns for price data
OHLCV_COLUMNS = ["ticker", "date", "open", "high", "low", "close", "volume"]

# Cache for requests (date, symbol) -> DataFrame
_request_cache: Dict[Tuple[date, str], DataFrame] = {}


class FinanceDataReaderProvider(MarketDataProvider):
    """FinanceDataReader-based market data provider for KOSDAQ."""

    def __init__(self, primary_symbol: str = 'KQ11', use_index: bool = True):
        """Initialize FinanceDataReader provider.

        Args:
            primary_symbol: Primary symbol to fetch (default: 'KQ11' for KOSDAQ index).
            use_index: If True, fetch index data. If False, fetch individual stocks.
        """
        if fdr is None:
            raise ImportError(
                "FinanceDataReader is not installed. "
                "Please install it with: pip install finance-datareader>=0.9.50"
            )
        
        self.primary_symbol = primary_symbol
        self.use_index = use_index
        self.base_url = "https://finance.naver.com"  # For reference only

    def fetch_price_data(
        self,
        symbols: List[str],
        target_date: date,
        max_retries: int = 3,
    ) -> Tuple[DataFrame, List[str]]:
        """Fetch OHLCV data for KOSDAQ index or individual stocks.

        For KOSDAQ, we fetch KQ11 (index) or individual stock codes.

        Args:
            symbols: List of ticker symbols (for index, uses primary_symbol instead).
            target_date: Target date for data.
            max_retries: Maximum number of retries (default: 3).

        Returns:
            Tuple of:
            - DataFrame with columns: ticker, date, open, high, low, close, volume
            - List of failed ticker symbols (empty if successful)
        """
        results: List[Series] = []
        failed_symbols: List[str] = []

        logger.info(f"Fetching KOSDAQ data via FinanceDataReader for date {target_date}")

        if self.use_index:
            # Fetch index data (KQ11)
            index_data, index_error = self._fetch_with_retry(
                self.primary_symbol, target_date, max_retries
            )

            if index_data is not None:
                results.append(index_data)
                logger.info(f"Successfully fetched {self.primary_symbol} data")
            else:
                failed_symbols = [self.primary_symbol]
                logger.error(f"Failed to fetch {self.primary_symbol}: {index_error}")
        else:
            # Fetch individual stocks
            for symbol in symbols:
                stock_data, stock_error = self._fetch_with_retry(
                    symbol, target_date, max_retries
                )

                if stock_data is not None:
                    results.append(stock_data)
                    logger.info(f"Successfully fetched {symbol} data")
                else:
                    failed_symbols.append(symbol)
                    logger.warning(f"Failed to fetch {symbol}: {stock_error}")

        df = self._build_result_dataframe(results)
        return df, failed_symbols

    def _fetch_with_retry(
        self, symbol: str, target_date: date, max_retries: int
    ) -> Tuple[Optional[Series], Optional[str]]:
        """Fetch data with exponential backoff retry.

        Args:
            symbol: Ticker symbol (KQ11 or stock code).
            target_date: Target date for data.
            max_retries: Maximum number of retries (default: 3).

        Returns:
            Tuple of (Series with data or None, error message or None).
        """
        # Check cache first (prevent duplicate requests)
        cache_key = (target_date, symbol)
        if cache_key in _request_cache:
            logger.debug(f"Using cached data for {symbol} on {target_date}")
            cached_df = _request_cache[cache_key]
            if not cached_df.empty:
                target_data = self._find_date_data(cached_df, target_date, symbol)
                if target_data is not None:
                    return target_data, None

        # Calculate date range (need a few days for FinanceDataReader)
        # For volatility calculation, we may need more days
        start_date = target_date - timedelta(days=30)  # Get more data for rolling calculations
        end_date = target_date + timedelta(days=1)

        for attempt in range(max_retries + 1):
            try:
                data = self._fetch_from_fdr(symbol, start_date, end_date)
                if data is not None and not data.empty:
                    # Cache the raw data
                    _request_cache[cache_key] = data
                    
                    # Find data for target_date
                    target_data = self._find_date_data(data, target_date, symbol)
                    if target_data is not None:
                        return target_data, None
                    else:
                        error_msg = f"No data for {symbol} on {target_date}"
                        if attempt < max_retries:
                            logger.debug(f"Retry {attempt + 1}/{max_retries}: {error_msg}")
                            time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                            continue
                        return None, error_msg
                else:
                    error_msg = f"Empty data from FinanceDataReader for {symbol}"
                    if attempt < max_retries:
                        logger.debug(f"Retry {attempt + 1}/{max_retries}: {error_msg}")
                        time.sleep(2 ** attempt)
                        continue
                    return None, error_msg

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                if attempt < max_retries:
                    logger.debug(f"Retry {attempt + 1}/{max_retries} for {symbol}: {error_msg}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"Failed to fetch {symbol} after {max_retries} retries: {error_msg}")
                    return None, error_msg

        return None, "Max retries exceeded"

    def _fetch_from_fdr(
        self, symbol: str, start_date: date, end_date: date
    ) -> Optional[DataFrame]:
        """Fetch data from FinanceDataReader.

        Args:
            symbol: Ticker symbol (KQ11 or stock code).
            start_date: Start date for data range.
            end_date: End date for data range.

        Returns:
            DataFrame with OHLCV data or None if failed.
        """
        try:
            logger.debug(f"Fetching from FinanceDataReader: {symbol} from {start_date} to {end_date}")

            # FinanceDataReader expects string dates in 'YYYY-MM-DD' format
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # Fetch data
            df = fdr.DataReader(symbol, start_str, end_str)

            if df.empty:
                logger.warning(f"Empty DataFrame from FinanceDataReader for {symbol}")
                return None

            # FinanceDataReader returns DataFrame with Date index and columns: Open, High, Low, Close, Volume
            # Reset index to make Date a column
            if df.index.name == 'Date' or isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                if 'Date' not in df.columns:
                    # Try to find date column
                    for col in df.columns:
                        if 'date' in col.lower() or '날짜' in col.lower():
                            df = df.rename(columns={col: 'Date'})
                            break

            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            col_mapping = {}
            
            # Map column names (case-insensitive, handle Korean column names)
            for target_col in required_cols:
                found = False
                for df_col in df.columns:
                    if df_col.lower() == target_col.lower():
                        col_mapping[df_col] = target_col
                        found = True
                        break
                    # Handle Korean column names
                    elif target_col == 'Open' and ('시가' in df_col or 'open' in df_col.lower()):
                        col_mapping[df_col] = 'Open'
                        found = True
                        break
                    elif target_col == 'High' and ('고가' in df_col or 'high' in df_col.lower()):
                        col_mapping[df_col] = 'High'
                        found = True
                        break
                    elif target_col == 'Low' and ('저가' in df_col or 'low' in df_col.lower()):
                        col_mapping[df_col] = 'Low'
                        found = True
                        break
                    elif target_col == 'Close' and ('종가' in df_col or 'close' in df_col.lower()):
                        col_mapping[df_col] = 'Close'
                        found = True
                        break
                    elif target_col == 'Volume' and ('거래량' in df_col or 'volume' in df_col.lower()):
                        col_mapping[df_col] = 'Volume'
                        found = True
                        break
                
                if not found:
                    logger.error(f"Missing required column: {target_col} in FinanceDataReader response for {symbol}")
                    return None

            # Rename columns to standard format
            df = df.rename(columns=col_mapping)

            # Ensure Date column exists
            if 'Date' not in df.columns:
                logger.error(f"No Date column found in FinanceDataReader response for {symbol}")
                return None

            # Convert Date to datetime
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')

            return df

        except Exception as e:
            logger.error(f"Error fetching {symbol} from FinanceDataReader: {e}", exc_info=True)
            return None

    def _find_date_data(
        self, df: DataFrame, target_date: date, symbol: str
    ) -> Optional[Series]:
        """Find data for target date or closest previous trading day.

        Args:
            df: DataFrame with FinanceDataReader data.
            target_date: Target date for data.
            symbol: Ticker symbol (for logging).

        Returns:
            Series with OHLCV data or None if not found.
        """
        target_datetime = pd.Timestamp(target_date)

        # Try exact date first
        exact_match = df[df['Date'].dt.date == target_date]
        if not exact_match.empty:
            row = exact_match.iloc[-1]
            result = self._create_ohlcv_series(symbol, target_date, row)
            # If result is None (invalid data), return None
            if result is None:
                return None
            return result

        # Find closest previous trading day
        previous_days = df[df['Date'] <= target_datetime]
        if previous_days.empty:
            logger.debug(f"No previous trading day found for {symbol} on {target_date}")
            return None

        # Use closest previous trading day
        closest_row = previous_days.iloc[-1]
        actual_date = closest_row['Date'].date()
        return self._create_ohlcv_series(symbol, actual_date, closest_row)

    def _create_ohlcv_series(
        self, symbol: str, actual_date: date, row: pd.Series
    ) -> Series:
        """Create OHLCV Series from FinanceDataReader data row.

        Args:
            symbol: Ticker symbol.
            actual_date: Actual trading date.
            row: Series with FinanceDataReader data (Date, Open, High, Low, Close, Volume).

        Returns:
            Series with columns: ticker, date, open, high, low, close, volume.
        """
        # Ensure we have valid price data (avoid zero prices which cause division errors)
        open_price = float(row['Open']) if pd.notna(row['Open']) and row['Open'] != 0 else None
        high_price = float(row['High']) if pd.notna(row['High']) and row['High'] != 0 else None
        low_price = float(row['Low']) if pd.notna(row['Low']) and row['Low'] != 0 else None
        close_price = float(row['Close']) if pd.notna(row['Close']) and row['Close'] != 0 else None
        
        # If any critical price is missing or zero, return None (will be filtered out)
        if open_price is None or close_price is None:
            logger.warning(f"Invalid price data for {symbol} on {actual_date}: Open={open_price}, Close={close_price}")
            return None
        
        return pd.Series({
            'ticker': symbol,
            'date': actual_date,
            'open': open_price,
            'high': high_price if high_price is not None else open_price,
            'low': low_price if low_price is not None else open_price,
            'close': close_price,
            'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
        })

    def _build_result_dataframe(self, results: List[Series]) -> DataFrame:
        """Build result DataFrame from list of Series.

        Args:
            results: List of Series with OHLCV data (may contain None values).

        Returns:
            DataFrame with OHLCV data or empty DataFrame with correct columns.
        """
        if results:
            # Filter out None values (invalid data)
            valid_results = [r for r in results if r is not None]
            if valid_results:
                df = pd.DataFrame(valid_results)
                if not df.empty:
                    df = df[OHLCV_COLUMNS]
                    # Ensure date column is date type
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date']).dt.date
                return df
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    def fetch_single_symbol(
        self,
        symbol: str,
        target_date: date,
        max_retries: int = 3,
    ) -> Optional[Series]:
        """Fetch OHLCV data for a single symbol.

        Args:
            symbol: Ticker symbol (KQ11 or stock code).
            target_date: Target date for data.
            max_retries: Maximum number of retries.

        Returns:
            Series with OHLCV data or None if failed.
        """
        data, error = self._fetch_with_retry(symbol, target_date, max_retries)
        return data

