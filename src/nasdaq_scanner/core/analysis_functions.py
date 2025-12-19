"""Analysis functions for calculating returns, volatility, and ranking movers.

This module provides functions for:
- Calculating daily returns per ticker: (Close - Open) / Open * 100
- Calculating volatility proxy: (High - Low) / Open * 100
- Ranking top movers (gainers, losers, volatile)
- Handling NaN and inf values properly
"""

import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import Dict, List
from datetime import date

from nasdaq_scanner.config import DEFAULT_TOP_N


def calc_daily_returns(df: DataFrame) -> DataFrame:  # type: ignore[type-arg]
    """Calculate daily returns per ticker: (Close - Open) / Open * 100.

    Args:
        df: DataFrame with columns: ticker, date, open, close (and optionally others).
            Must be sorted by ticker and date.

    Returns:
        DataFrame with added 'return' column containing daily return percentage.
        NaN and inf values are removed.
        Original columns are preserved.

    Examples:
        >>> df = pd.DataFrame({
        ...     'ticker': ['AAPL', 'AAPL'],
        ...     'date': [date(2024, 1, 15), date(2024, 1, 16)],
        ...     'open': [100.0, 100.0],
        ...     'close': [100.0, 105.0]
        ... })
        >>> result = calc_daily_returns(df)
        >>> result['return'].iloc[0]  # 0.0%
        0.0
        >>> result['return'].iloc[1]  # 5.0%
        5.0
    """
    if df.empty:
        return df.copy()

    # Validate required columns
    required_cols = ["ticker", "date", "open", "close"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

    # Create a copy to avoid modifying original
    result_df = df.copy()

    # Calculate daily returns: (Close - Open) / Open * 100
    result_df["return"] = np.where(
        result_df["open"] != 0,
        ((result_df["close"] - result_df["open"]) / result_df["open"]) * 100,
        np.nan
    )

    # Remove inf values (replace with NaN)
    result_df["return"] = result_df["return"].replace([np.inf, -np.inf], np.nan)

    return result_df


def calc_volatility_proxy(df: DataFrame) -> DataFrame:  # type: ignore[type-arg]
    """Calculate volatility proxy: (High - Low) / Open * 100.

    Calculates intraday volatility as a percentage of opening price.

    Args:
        df: DataFrame with columns: ticker, date, open, high, low (and optionally others).

    Returns:
        DataFrame with added 'vol' column containing volatility proxy percentage.
        NaN and inf values are removed.
        Original columns are preserved.

    Examples:
        >>> df = pd.DataFrame({
        ...     'ticker': ['AAPL'],
        ...     'date': [date(2024, 1, 15)],
        ...     'open': [100.0],
        ...     'high': [102.0],
        ...     'low': [99.0]
        ... })
        >>> result = calc_volatility_proxy(df)
        >>> result['vol'].iloc[0]  # (102 - 99) / 100 * 100 = 3.0%
        3.0
    """
    if df.empty:
        return df.copy()

    # Validate required columns
    required_cols = ["open", "high", "low"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

    # Create a copy to avoid modifying original
    result_df = df.copy()

    # Calculate volatility proxy: (High - Low) / Open * 100
    result_df["vol"] = np.where(
        result_df["open"] != 0,
        ((result_df["high"] - result_df["low"]) / result_df["open"]) * 100,
        np.nan
    )

    # Remove inf values (replace with NaN)
    result_df["vol"] = result_df["vol"].replace([np.inf, -np.inf], np.nan)

    return result_df


def calc_volatility_std(df: DataFrame, window: int = 5) -> DataFrame:  # type: ignore[type-arg]
    """Calculate volatility using standard deviation of returns over a window.

    Calculates rolling standard deviation of daily returns as volatility measure.

    Args:
        df: DataFrame with columns: ticker, date, return (and optionally others).
            Must be sorted by ticker and date.
        window: Number of trading days for rolling window (default: 5).

    Returns:
        DataFrame with added 'vol_std' column containing volatility (standard deviation).
        NaN and inf values are removed.
        Original columns are preserved.

    Examples:
        >>> df = pd.DataFrame({
        ...     'ticker': ['A', 'A', 'A', 'A', 'A'],
        ...     'date': [date(2024, 1, 15), date(2024, 1, 16), date(2024, 1, 17), date(2024, 1, 18), date(2024, 1, 19)],
        ...     'return': [1.0, 2.0, -1.0, 3.0, 1.0]
        ... })
        >>> result = calc_volatility_std(df, window=5)
        >>> result['vol_std'].iloc[-1]  # Standard deviation of [1.0, 2.0, -1.0, 3.0, 1.0]
        ...
    """
    if df.empty:
        return df.copy()

    # Validate required columns
    required_cols = ["ticker", "date", "return"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

    # Create a copy to avoid modifying original
    result_df = df.copy()

    # Calculate rolling standard deviation of returns for each ticker
    result_df = result_df.sort_values(['ticker', 'date'])
    result_df['vol_std'] = result_df.groupby('ticker')['return'].transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )

    # Remove inf values (replace with NaN)
    result_df["vol_std"] = result_df["vol_std"].replace([np.inf, -np.inf], np.nan)

    return result_df


def rank_movers(df: DataFrame, top_n: int = DEFAULT_TOP_N) -> Dict[str, DataFrame]:  # type: ignore[type-arg]
    """Rank top movers: gainers, losers, and volatile stocks.

    Returns top N (or fewer) stocks for each category:
    - Gainers: Highest daily returns (descending)
    - Losers: Lowest daily returns (ascending, most negative first)
    - Volatile: Highest volatility proxy (descending)

    Args:
        df: DataFrame with columns: ticker, date, return, vol (and optionally others).
            Should have 'return' and 'vol' columns (from calc_daily_returns and calc_volatility_proxy).
        top_n: Number of top stocks to return for each category (default: 10).

    Returns:
        Dictionary with keys:
        - 'gainers': DataFrame with top N gainers (sorted by return descending)
        - 'losers': DataFrame with top N losers (sorted by return ascending)
        - 'volatile': DataFrame with top N volatile stocks (sorted by vol descending)
        Each DataFrame contains columns: ticker, date, close, return, vol (and original columns).
    """
    if df.empty:
        return {
            "gainers": pd.DataFrame(columns=df.columns),
            "losers": pd.DataFrame(columns=df.columns),
            "volatile": pd.DataFrame(columns=df.columns),
        }

    # Validate required columns
    required_cols = ["ticker", "return", "vol"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

    # Filter out NaN and inf values
    df_clean = df[
        df["return"].notna() & 
        df["vol"].notna() &
        np.isfinite(df["return"]) &
        np.isfinite(df["vol"])
    ].copy()

    if df_clean.empty:
        return {
            "gainers": pd.DataFrame(columns=df.columns),
            "losers": pd.DataFrame(columns=df.columns),
            "volatile": pd.DataFrame(columns=df.columns),
        }

    # Ensure we have latest data for each ticker (if multiple dates exist)
    latest_df = df_clean.sort_values("date").groupby("ticker").last().reset_index()

    # Rank gainers: sort by return descending, take top N
    gainers = _rank_by_metric(
        latest_df, "return", ascending=False, top_n=top_n, default_columns=df.columns
    )

    # Rank losers: sort by return ascending (most negative first), take top N
    losers = _rank_by_metric(
        latest_df, "return", ascending=True, top_n=top_n, default_columns=df.columns
    )

    # Rank volatile: sort by vol descending, take top N
    volatile = _rank_by_metric(
        latest_df, "vol", ascending=False, top_n=top_n, default_columns=df.columns
    )

    # Select required columns for result
    def _select_result_columns(df_result: DataFrame) -> DataFrame:
        if df_result.empty:
            return df_result
        # Standard columns to include
        standard_cols = ["ticker", "date", "open", "high", "low", "close", "volume", "return", "vol"]
        available_cols = [col for col in standard_cols if col in df_result.columns]
        # Add any other columns from original DataFrame
        other_cols = [col for col in df_result.columns if col not in standard_cols]
        all_cols = available_cols + other_cols
        if not all_cols:
            return df_result
        return df_result[all_cols]

    return {
        "gainers": _select_result_columns(gainers),
        "losers": _select_result_columns(losers),
        "volatile": _select_result_columns(volatile),
    }


def _rank_by_metric(
    df: DataFrame,
    metric_col: str,
    ascending: bool,
    top_n: int,
    default_columns: List[str],
) -> DataFrame:
    """Helper function to rank stocks by a metric and return top N.

    Args:
        df: DataFrame with ticker and metric column.
        metric_col: Column name to rank by.
        ascending: Sort order (True for ascending, False for descending).
        top_n: Number of top stocks to return.
        default_columns: Default columns for empty DataFrame.

    Returns:
        DataFrame with top N stocks ranked by metric.
    """
    if df.empty or top_n == 0:
        return pd.DataFrame(columns=default_columns)

    # Sort by metric and take top N
    result = (
        df.sort_values(metric_col, ascending=ascending, kind="stable")
        .head(top_n)
        .copy()
    )

    return result
