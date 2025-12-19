"""Analysis functions for calculating returns, volatility, and ranking movers.

This module provides functions for:
- Calculating daily returns per ticker
- Calculating volatility proxy
- Ranking top movers (gainers, losers, volatile)
"""

import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import Dict
from datetime import date


def calc_daily_returns(df: DataFrame) -> DataFrame:
    """Calculate daily returns per ticker.

    Calculates daily return percentage for each ticker by grouping by ticker
    and computing percentage change from previous day's close price.

    Args:
        df: DataFrame with columns: ticker, date, close (and optionally others).
            Must be sorted by ticker and date.

    Returns:
        DataFrame with added 'return' column containing daily return percentage.
        First day for each ticker will have NaN (no previous day to compare).
        Original columns are preserved.

    Examples:
        >>> df = pd.DataFrame({
        ...     'ticker': ['AAPL', 'AAPL'],
        ...     'date': [date(2024, 1, 15), date(2024, 1, 16)],
        ...     'close': [100.0, 105.0]
        ... })
        >>> result = calc_daily_returns(df)
        >>> result['return'].iloc[0]  # NaN
        nan
        >>> result['return'].iloc[1]  # 5.0%
        5.0
    """
    if df.empty:
        return df.copy()

    # Validate required columns
    required_cols = ["ticker", "date", "close"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

    # Create a copy to avoid modifying original
    result_df = df.copy()

    # Group by ticker and calculate daily returns
    # Formula: (close[t] - close[t-1]) / close[t-1] * 100
    result_df = result_df.sort_values(["ticker", "date"])

    # Calculate returns per ticker group
    result_df["return"] = (
        result_df.groupby("ticker")["close"]
        .pct_change()
        .multiply(100)
    )

    return result_df


def calc_volatility_proxy(df: DataFrame) -> DataFrame:
    """Calculate volatility proxy: (high - low) / open.

    Calculates intraday volatility as a percentage of opening price.

    Args:
        df: DataFrame with columns: ticker, date, open, high, low (and optionally others).

    Returns:
        DataFrame with added 'vol' column containing volatility proxy.
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
        >>> result['vol'].iloc[0]  # (102 - 99) / 100 = 0.03
        0.03
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

    # Calculate volatility proxy: (high - low) / open
    # Handle zero open price by returning NaN
    result_df["vol"] = np.where(
        result_df["open"] != 0,
        (result_df["high"] - result_df["low"]) / result_df["open"],
        np.nan,
    )

    return result_df


def rank_movers(df: DataFrame) -> Dict[str, DataFrame]:
    """Rank top movers: gainers, losers, and volatile stocks.

    Returns top 10 (or fewer) stocks for each category:
    - Gainers: Highest daily returns (descending)
    - Losers: Lowest daily returns (ascending, most negative first)
    - Volatile: Highest volatility proxy (descending)

    Args:
        df: DataFrame with columns: ticker, date, return, vol (and optionally others).
            Should have 'return' and 'vol' columns (from calc_daily_returns and calc_volatility_proxy).

    Returns:
        Dictionary with keys:
        - 'gainers': DataFrame with top 10 gainers (sorted by return descending)
        - 'losers': DataFrame with top 10 losers (sorted by return ascending)
        - 'volatile': DataFrame with top 10 volatile stocks (sorted by vol descending)
        Each DataFrame contains columns: ticker, date, close, return, vol (and original columns).

    Examples:
        >>> df = pd.DataFrame({
        ...     'ticker': ['AAPL', 'MSFT'],
        ...     'date': [date(2024, 1, 16), date(2024, 1, 16)],
        ...     'return': [5.0, -2.0],
        ...     'vol': [0.03, 0.01],
        ...     'close': [105.0, 196.0]
        ... })
        >>> result = rank_movers(df)
        >>> 'gainers' in result
        True
        >>> len(result['gainers']) <= 10
        True
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

    # Ensure 'close' column exists (for result DataFrame requirement)
    result_cols = ["ticker", "date", "close", "return", "vol"]
    available_cols = [col for col in result_cols if col in df.columns]
    # Add any other columns from original DataFrame
    other_cols = [col for col in df.columns if col not in result_cols]
    final_cols = available_cols + other_cols

    # Filter out NaN returns for gainers/losers
    df_with_returns = df[df["return"].notna()].copy()
    # Filter out NaN vols for volatile
    df_with_vols = df[df["vol"].notna()].copy()

    # Rank gainers: sort by return descending, take top 10
    # For each ticker, use the row with highest return (in case of multiple dates)
    if not df_with_returns.empty:
        # Group by ticker and take the row with highest return for each ticker
        gainers_by_ticker = (
            df_with_returns.sort_values("return", ascending=False)
            .groupby("ticker", as_index=False)
            .first()
        )
        # Then sort by return descending and take top 10
        gainers = (
            gainers_by_ticker.sort_values("return", ascending=False)
            .head(10)
            .copy()
        )
    else:
        gainers = pd.DataFrame(columns=df.columns)

    # Rank losers: sort by return ascending (most negative first), take top 10
    if not df_with_returns.empty:
        # Group by ticker and take the row with lowest return for each ticker
        losers_by_ticker = (
            df_with_returns.sort_values("return", ascending=True)
            .groupby("ticker", as_index=False)
            .first()
        )
        # Then sort by return ascending and take top 10
        losers = (
            losers_by_ticker.sort_values("return", ascending=True)
            .head(10)
            .copy()
        )
    else:
        losers = pd.DataFrame(columns=df.columns)

    # Rank volatile: sort by vol descending, take top 10
    if not df_with_vols.empty:
        # Group by ticker and take the row with highest vol for each ticker
        volatile_by_ticker = (
            df_with_vols.sort_values("vol", ascending=False)
            .groupby("ticker", as_index=False)
            .first()
        )
        # Then sort by vol descending and take top 10
        volatile = (
            volatile_by_ticker.sort_values("vol", ascending=False)
            .head(10)
            .copy()
        )
    else:
        volatile = pd.DataFrame(columns=df.columns)

    # Select required columns for result
    # Ensure ticker, date, close, return, vol are included if available
    def select_columns(df_result: DataFrame) -> DataFrame:
        if df_result.empty:
            return df_result
        # Always include available required columns
        cols_to_include = [col for col in final_cols if col in df_result.columns]
        # Add any other columns from original DataFrame
        other_cols = [col for col in df_result.columns if col not in final_cols]
        all_cols = cols_to_include + other_cols
        if not all_cols:
            return df_result
        return df_result[all_cols]

    return {
        "gainers": select_columns(gainers),
        "losers": select_columns(losers),
        "volatile": select_columns(volatile),
    }

