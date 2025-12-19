"""yfinance implementation of MarketDataProvider.

This module provides yfinance-based implementation of the market data provider interface.

Data Format:
- yfinance returns: DataFrame with DatetimeIndex and columns (Open, High, Low, Close, Volume)
- Provider returns: DataFrame/Series with columns (ticker, date, close, volume)
  - ticker: str (ticker symbol)
  - date: date (target date, not datetime)
  - close: float (closing price)
  - volume: int (trading volume)

Failure Policy:
- Empty history (invalid ticker): Returns None (fetch_single_symbol) or adds to failed_symbols (fetch_price_data)
- Network errors: Retries up to max_retries, then returns None or adds to failed_symbols
- All tickers fail: Returns empty DataFrame with correct columns, all tickers in failed_symbols
- Exceptions: Caught and logged, symbol added to failed_symbols, processing continues
"""

import logging
import pandas as pd
from datetime import date, timedelta
from typing import List, Tuple, Optional
from pandas import DataFrame, Series

try:
    import yfinance as yf
except ImportError:
    yf = None  # type: ignore

from nasdaq_scanner.providers.base import MarketDataProvider
from nasdaq_scanner.config import (
    DEFAULT_MAX_RETRIES,
    YFINANCE_HISTORY_LOOKBACK_DAYS,
    YFINANCE_HISTORY_LOOKAHEAD_DAYS,
    PRICE_DATA_COLUMNS,
    MAX_FAILED_SYMBOLS_DISPLAY,
)

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """yfinance-based market data provider."""

    def __init__(self):
        """Initialize yfinance provider."""
        if yf is None:
            raise ImportError(
                "yfinance is not installed. Install it with: pip install yfinance"
            )

    def fetch_price_data(
        self,
        symbols: List[str],
        target_date: date,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> Tuple[DataFrame, List[str]]:
        """Fetch price data for multiple symbols using yfinance.

        Args:
            symbols: List of ticker symbols to fetch.
            target_date: Target date for data.
            max_retries: Maximum number of retries for failed requests.

        Returns:
            Tuple of:
            - DataFrame with columns: ticker, date, close, volume
            - List of failed ticker symbols

        Raises:
            ImportError: If yfinance is not installed.
        """
        results: List[Series] = []
        failed_symbols: List[str] = []

        logger.info(f"Fetching price data for {len(symbols)} symbols on {target_date}")

        for symbol in symbols:
            price_data = self._fetch_symbol_with_error_handling(
                symbol, target_date, max_retries
            )
            if price_data is not None:
                results.append(price_data)
            else:
                failed_symbols.append(symbol)

        df = self._build_result_dataframe(results)
        self._log_fetch_results(len(results), len(symbols), failed_symbols)

        return df, failed_symbols

    def _fetch_symbol_with_error_handling(
        self, symbol: str, target_date: date, max_retries: int
    ) -> Optional[Series]:
        """Fetch single symbol with error handling.

        Args:
            symbol: Ticker symbol.
            target_date: Target date for data.
            max_retries: Maximum number of retries.

        Returns:
            Series with price data or None if failed.
        """
        try:
            return self.fetch_single_symbol(symbol, target_date, max_retries)
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}", exc_info=True)
            return None

    def _build_result_dataframe(self, results: List[Series]) -> DataFrame:
        """Build result DataFrame from list of Series.

        Args:
            results: List of Series with price data.

        Returns:
            DataFrame with price data or empty DataFrame with correct columns.
        """
        if results:
            df = pd.DataFrame(results)
            # Ensure columns are in correct order
            if not df.empty:
                df = df[PRICE_DATA_COLUMNS]
            return df
        else:
            # Policy: Empty DataFrame with expected columns when all tickers fail
            return pd.DataFrame(columns=PRICE_DATA_COLUMNS)

    def _log_fetch_results(
        self, success_count: int, total_count: int, failed_symbols: List[str]
    ) -> None:
        """Log fetch results.

        Args:
            success_count: Number of successfully fetched symbols.
            total_count: Total number of symbols requested.
            failed_symbols: List of failed symbol names.
        """
        if success_count > 0:
            logger.info(
                f"Successfully fetched {success_count}/{total_count} symbols. "
                f"Failed: {len(failed_symbols)}"
            )
        else:
            logger.warning("No data was successfully fetched")

        if failed_symbols:
            display_count = min(len(failed_symbols), MAX_FAILED_SYMBOLS_DISPLAY)
            logger.warning(
                f"Failed symbols: {', '.join(failed_symbols[:display_count])}"
            )
            if len(failed_symbols) > MAX_FAILED_SYMBOLS_DISPLAY:
                remaining = len(failed_symbols) - MAX_FAILED_SYMBOLS_DISPLAY
                logger.warning(f"... and {remaining} more")

    def fetch_single_symbol(
        self,
        symbol: str,
        target_date: date,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> Optional[Series]:
        """Fetch price data for a single symbol using yfinance.

        Args:
            symbol: Ticker symbol.
            target_date: Target date for data.
            max_retries: Maximum number of retries.

        Returns:
            Series with index: ['ticker', 'date', 'close', 'volume']
            or None if fetch failed.
        """
        start_date, end_date = self._calculate_history_date_range(target_date)

        for attempt in range(max_retries + 1):
            try:
                history_df = self._fetch_history_data(symbol, start_date, end_date)
                if history_df.empty:
                    return None

                price_row = self._find_trading_day_data(history_df, target_date, symbol)
                if price_row is None:
                    return None

                return self._create_price_series(symbol, target_date, price_row)

            except Exception as e:
                if attempt < max_retries:
                    logger.debug(f"Retry {attempt + 1}/{max_retries} for {symbol}")
                    continue
                else:
                    logger.error(
                        f"Failed to fetch {symbol} after {max_retries} retries: {e}"
                    )
                    return None

        return None

    def _calculate_history_date_range(self, target_date: date) -> Tuple[date, date]:
        """Calculate date range for fetching history data.

        Args:
            target_date: Target date for data.

        Returns:
            Tuple of (start_date, end_date).
        """
        start_date = target_date - timedelta(days=YFINANCE_HISTORY_LOOKBACK_DAYS)
        end_date = target_date + timedelta(days=YFINANCE_HISTORY_LOOKAHEAD_DAYS)
        return start_date, end_date

    def _fetch_history_data(
        self, symbol: str, start_date: date, end_date: date
    ) -> DataFrame:
        """Fetch history data from yfinance.

        Args:
            symbol: Ticker symbol.
            start_date: Start date for history.
            end_date: End date for history.

        Returns:
            DataFrame with history data (may be empty).
        """
        ticker = yf.Ticker(symbol)
        history_df = ticker.history(start=start_date, end=end_date)

        # Ensure index is DatetimeIndex
        if not isinstance(history_df.index, pd.DatetimeIndex):
            history_df.index = pd.to_datetime(history_df.index)

        return history_df

    def _find_trading_day_data(
        self, history_df: DataFrame, target_date: date, symbol: str
    ) -> Optional[pd.Series]:
        """Find trading day data for target date or closest previous trading day.

        Args:
            history_df: DataFrame with history data.
            target_date: Target date for data.
            symbol: Ticker symbol (for logging).

        Returns:
            Series with price data for the trading day, or None if not found.
        """
        target_datetime = pd.Timestamp(target_date)

        # Policy: Use closest previous trading day if target_date is not a trading day
        if target_datetime in history_df.index:
            return history_df.loc[target_datetime]

        # Get the closest previous trading day
        # Policy: If no previous trading day exists, return None
        previous_trading_days = history_df[history_df.index <= target_datetime]
        if previous_trading_days.empty:
            logger.debug(
                f"No previous trading day found for {symbol} on {target_date}"
            )
            return None

        return previous_trading_days.iloc[-1]

    def _create_price_series(
        self, symbol: str, target_date: date, price_row: pd.Series
    ) -> Series:
        """Create price Series from price row data.

        Args:
            symbol: Ticker symbol.
            target_date: Target date (kept as original, not actual trading day).
            price_row: Series with price data from yfinance.

        Returns:
            Series with columns: ticker, date, close, volume.
        """
        # Format: ticker (str), date (date), close (float), volume (int)
        return pd.Series({
            'ticker': symbol,
            'date': target_date,  # Keep original target_date, not the actual trading day
            'close': float(price_row['Close']),
            'volume': int(price_row['Volume']),
        })

