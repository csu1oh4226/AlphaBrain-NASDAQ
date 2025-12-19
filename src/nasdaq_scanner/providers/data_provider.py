"""Data provider for fetching market data from yfinance.

This module provides functions to fetch OHLCV data from yfinance
with error handling and logging for network failures and individual ticker failures.
"""

import logging
import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
from pandas import DataFrame

try:
    import yfinance as yf
except ImportError:
    yf = None  # type: ignore

logger = logging.getLogger(__name__)


def fetch_ohlcv_batch(
    symbols: List[str],
    target_date: date,
    max_retries: int = 2,
) -> DataFrame:
    """Fetch OHLCV data for multiple symbols from yfinance.

    Handles network failures and individual ticker failures gracefully.
    Failed symbols are logged but don't stop the entire process.

    Args:
        symbols: List of ticker symbols to fetch.
        target_date: Target date for data (will fetch around this date).
        max_retries: Maximum number of retries for failed requests.

    Returns:
        DataFrame with columns: symbol, date, Open, High, Low, Close, Volume.
        Only successful fetches are included.

    Raises:
        ImportError: If yfinance is not installed.
    """
    if yf is None:
        raise ImportError(
            "yfinance is not installed. Install it with: pip install yfinance"
        )

    results: List[Dict[str, Any]] = []
    failed_symbols: List[str] = []

    logger.info(f"Fetching OHLCV data for {len(symbols)} symbols on {target_date}")

    for symbol in symbols:
        try:
            ohlcv_data = _fetch_single_symbol(symbol, target_date, max_retries)
            if ohlcv_data is not None:
                results.append(ohlcv_data)
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
        df = pd.DataFrame(
            columns=["symbol", "date", "Open", "High", "Low", "Close", "Volume"]
        )
        logger.warning("No data was successfully fetched")

    return df


def _fetch_single_symbol(
    symbol: str, target_date: date, max_retries: int
) -> Optional[Dict[str, Any]]:
    """Fetch OHLCV data for a single symbol.

    Args:
        symbol: Ticker symbol.
        target_date: Target date for data.
        max_retries: Maximum number of retries.

    Returns:
        Dictionary with OHLCV data or None if fetch failed.
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

            return {
                "symbol": symbol,
                "date": target_date,
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "Volume": int(row["Volume"]),
            }

        except Exception as e:
            if attempt < max_retries:
                logger.debug(f"Retry {attempt + 1}/{max_retries} for {symbol}")
                continue
            else:
                raise

    return None

