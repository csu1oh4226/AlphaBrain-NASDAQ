"""yfinance implementation of MarketDataProvider.

This module provides yfinance-based implementation of the market data provider interface.
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
        max_retries: int = 2,
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
            try:
                price_data = self.fetch_single_symbol(symbol, target_date, max_retries)
                if price_data is not None:
                    results.append(price_data)
                else:
                    failed_symbols.append(symbol)
                    logger.warning(f"Failed to fetch data for {symbol}")

            except Exception as e:
                failed_symbols.append(symbol)
                logger.error(f"Error fetching {symbol}: {str(e)}", exc_info=True)
                continue

        if results:
            df = pd.DataFrame(results)
            logger.info(
                f"Successfully fetched {len(results)}/{len(symbols)} symbols. "
                f"Failed: {len(failed_symbols)}"
            )
            if failed_symbols:
                logger.warning(f"Failed symbols: {', '.join(failed_symbols[:10])}")
                if len(failed_symbols) > 10:
                    logger.warning(f"... and {len(failed_symbols) - 10} more")
        else:
            df = pd.DataFrame(columns=["ticker", "date", "close", "volume"])
            logger.warning("No data was successfully fetched")

        return df, failed_symbols

    def fetch_single_symbol(
        self,
        symbol: str,
        target_date: date,
        max_retries: int = 2,
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
        # yfinance needs a date range, so we fetch a small window around target_date
        start_date = target_date - timedelta(days=5)
        end_date = target_date + timedelta(days=1)

        for attempt in range(max_retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)

                if hist.empty:
                    return None

                # Find the row closest to target_date
                hist.index = pd.to_datetime(hist.index)
                target_datetime = pd.Timestamp(target_date)

                # Get the row for target_date or closest previous trading day
                if target_datetime in hist.index:
                    row = hist.loc[target_datetime]
                else:
                    # Get the closest previous trading day
                    previous_days = hist[hist.index <= target_datetime]
                    if previous_days.empty:
                        return None
                    row = previous_days.iloc[-1]

                # Return as Series with required columns
                return pd.Series({
                    'ticker': symbol,
                    'date': target_date,
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                })

            except Exception as e:
                if attempt < max_retries:
                    logger.debug(f"Retry {attempt + 1}/{max_retries} for {symbol}")
                    continue
                else:
                    logger.error(f"Failed to fetch {symbol} after {max_retries} retries: {e}")
                    return None

        return None

