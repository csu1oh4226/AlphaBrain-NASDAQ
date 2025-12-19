"""Fetch OHLCV data from yfinance and convert to tidy DataFrame format.

This module provides a function to fetch OHLCV data using yfinance.download
and convert the MultiIndex DataFrame format to a tidy format.
"""

import logging
import pandas as pd
from typing import List, Union
from pandas import DataFrame

try:
    import yfinance as yf
except ImportError:
    yf = None  # type: ignore

logger = logging.getLogger(__name__)


def fetch_ohlcv(
    tickers: Union[str, List[str]],
    period: str,
    interval: str,
) -> DataFrame:  # type: ignore[type-arg]
    """Fetch OHLCV data from yfinance and return as tidy DataFrame.

    Args:
        tickers: Single ticker symbol (str) or list of ticker symbols.
        period: Period to fetch (e.g., "1d", "5d", "1mo", "1y").
        interval: Data interval (e.g., "1d", "1h", "5m").
            See yfinance documentation for valid values.

    Returns:
        Tidy DataFrame with columns: ticker, date, open, high, low, close, volume.
        All column names are lowercase.

    Raises:
        ImportError: If yfinance is not installed.
        ValueError: If no data is returned from yfinance.

    Examples:
        >>> df = fetch_ohlcv("AAPL", period="5d", interval="1d")
        >>> "ticker" in df.columns
        True
        >>> df = fetch_ohlcv(["AAPL", "MSFT"], period="1d", interval="1d")
        >>> len(df["ticker"].unique()) == 2
        True
    """
    if yf is None:
        raise ImportError(
            "yfinance is not installed. Install it with: pip install yfinance"
        )

    # Normalize tickers to list
    if isinstance(tickers, str):
        ticker_list = [tickers]
    else:
        ticker_list = tickers

    if not ticker_list:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(
            columns=["ticker", "date", "open", "high", "low", "close", "volume"]
        )

    logger.info(f"Fetching OHLCV data for {len(ticker_list)} ticker(s): {ticker_list}")

    # Fetch data using yfinance.download
    # group_by='ticker' ensures MultiIndex columns with ticker symbols
    # Note: yfinance.download takes tickers as first positional argument
    df = yf.download(
        ticker_list,
        period=period,
        interval=interval,
        group_by="ticker",
        progress=False,
    )

    # Check if data is empty (after fetching)
    # Note: Empty ticker list case is handled above, this is for when yfinance returns empty
    if df.empty:
        raise ValueError("No data")

    # Convert MultiIndex DataFrame to tidy format
    tidy_df = _convert_to_tidy_format(df, ticker_list)

    logger.info(f"Fetched {len(tidy_df)} rows of OHLCV data")

    return tidy_df


def _convert_to_tidy_format(
    df: DataFrame,
    tickers: List[str],
) -> DataFrame:  # type: ignore[type-arg]
    """Convert yfinance MultiIndex DataFrame to tidy format.

    Args:
        df: MultiIndex DataFrame from yfinance.download.
            Columns: MultiIndex with (Attributes, Symbols)
            Index: DatetimeIndex
        tickers: List of ticker symbols that were requested.

    Returns:
        Tidy DataFrame with columns: ticker, date, open, high, low, close, volume.
    """
    results = []

    # Handle single ticker case (yfinance returns different structure)
    if len(tickers) == 1:
        # Single ticker: columns are just Attributes (Open, High, Low, Close, Volume)
        # No MultiIndex in this case
        ticker = tickers[0]
        for date_idx in df.index:
            row = {
                "ticker": ticker,
                "date": date_idx,
                "open": float(df.loc[date_idx, "Open"]),
                "high": float(df.loc[date_idx, "High"]),
                "low": float(df.loc[date_idx, "Low"]),
                "close": float(df.loc[date_idx, "Close"]),
                "volume": int(df.loc[date_idx, "Volume"]),
            }
            results.append(row)
    else:
        # Multiple tickers: MultiIndex columns (Attributes, Symbols)
        for date_idx in df.index:
            for ticker in tickers:
                try:
                    row = {
                        "ticker": ticker,
                        "date": date_idx,
                        "open": float(df.loc[date_idx, ("Open", ticker)]),
                        "high": float(df.loc[date_idx, ("High", ticker)]),
                        "low": float(df.loc[date_idx, ("Low", ticker)]),
                        "close": float(df.loc[date_idx, ("Close", ticker)]),
                        "volume": int(df.loc[date_idx, ("Volume", ticker)]),
                    }
                    results.append(row)
                except KeyError:
                    # Skip if ticker data is missing for this date
                    logger.debug(f"Missing data for {ticker} on {date_idx}")
                    continue

    tidy_df = pd.DataFrame(results)

    # Ensure date column is datetime
    if not tidy_df.empty:
        tidy_df["date"] = pd.to_datetime(tidy_df["date"])

    return tidy_df

