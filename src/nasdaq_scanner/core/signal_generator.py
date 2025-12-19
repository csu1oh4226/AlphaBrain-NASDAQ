"""Signal generator for rule-based buy/sell recommendations.

This module provides functions to generate buy and sell signals based on
intersection rules between gainers/losers and volatility rankings.
"""

import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import Dict
from nasdaq_scanner.config import DEFAULT_TOP_N


def generate_signals(df_ranked: DataFrame, top_n: int = DEFAULT_TOP_N) -> Dict[str, DataFrame]:
    """Generate buy and sell signals based on rule-based analysis.

    Rules:
    1. buy_candidates: 상위 상승 + 변동성 상위 교집합
       - Top N gainers (by return, descending)
       - Top N volatile (by vol, descending)
       - Intersection of the two sets

    2. sell_candidates: 하락 top10 중 변동성 상위
       - Top N losers (by return, ascending - most negative first)
       - From those losers, select top M by volatility (descending)

    Args:
        df_ranked: DataFrame with columns: ticker, date, close, return, vol (and optionally others).
            Should contain ranked data (from rank_movers or similar).
        top_n: Number of top stocks to consider for each category (default: 10).

    Returns:
        Dictionary with keys:
        - 'buy_candidates': DataFrame with buy signals (intersection of top gainers and top volatile)
        - 'sell_candidates': DataFrame with sell signals (top volatile losers)
        Each DataFrame contains columns: ticker, date, close, return, vol, reason (and original columns).

    Examples:
        >>> df = pd.DataFrame({
        ...     'ticker': ['AAPL', 'TSLA'],
        ...     'return': [5.0, 6.0],
        ...     'vol': [0.05, 0.07]
        ... })
        >>> result = generate_signals(df)
        >>> 'buy_candidates' in result
        True
    """
    if df_ranked.empty:
        return {
            "buy_candidates": pd.DataFrame(columns=df_ranked.columns),
            "sell_candidates": pd.DataFrame(columns=df_ranked.columns),
        }

    # Validate required columns
    required_cols = ["ticker", "return", "vol"]
    missing_cols = [col for col in required_cols if col not in df_ranked.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

    # Filter out NaN values
    df_clean = df_ranked[
        df_ranked["return"].notna() & df_ranked["vol"].notna()
    ].copy()

    if df_clean.empty:
        return {
            "buy_candidates": pd.DataFrame(columns=df_ranked.columns),
            "sell_candidates": pd.DataFrame(columns=df_ranked.columns),
        }

    # Rule 1: buy_candidates = intersection of top gainers and top volatile
    buy_candidates = _get_buy_candidates(df_clean, top_n)

    # Rule 2: sell_candidates = top volatile losers
    sell_candidates = _get_sell_candidates(df_clean, top_n)

    return {
        "buy_candidates": buy_candidates,
        "sell_candidates": sell_candidates,
    }


def _get_buy_candidates(df: DataFrame, top_n: int) -> DataFrame:
    """Get buy candidates as intersection of top gainers and top volatile.

    Args:
        df: Clean DataFrame with return and vol columns.
        top_n: Number of top stocks to consider.

    Returns:
        DataFrame with buy candidates, including 'reason' column.
    """
    # Get top N gainers (by return, descending)
    top_gainers = (
        df.sort_values("return", ascending=False)
        .head(top_n)
    )
    gainer_tickers = set(top_gainers["ticker"].unique())

    # Get top N volatile (by vol, descending)
    top_volatile = (
        df.sort_values("vol", ascending=False)
        .head(top_n)
    )
    volatile_tickers = set(top_volatile["ticker"].unique())

    # Intersection: tickers that are in both top gainers and top volatile
    intersection_tickers = gainer_tickers & volatile_tickers

    if not intersection_tickers:
        return pd.DataFrame(columns=df.columns)

    # Get rows for intersection tickers
    # For each ticker, take the row with highest return (in case of multiple dates)
    buy_df = df[df["ticker"].isin(intersection_tickers)].copy()
    buy_df = (
        buy_df.sort_values("return", ascending=False)
        .groupby("ticker", as_index=False)
        .first()
    )

    # Add reason column with detailed explanation
    buy_df["reason"] = buy_df.apply(
        lambda row: f"상위 상승({row['return']:.2f}%) + 변동성 상위({row['vol']:.4f}) 교집합",
        axis=1
    )

    return buy_df


def _get_sell_candidates(df: DataFrame, top_n: int) -> DataFrame:
    """Get sell candidates from top losers by volatility.

    Args:
        df: Clean DataFrame with return and vol columns.
        top_n: Number of top losers to consider.

    Returns:
        DataFrame with sell candidates, including 'reason' column.
    """
    # Get top N losers (by return, ascending - most negative first)
    losers = df[df["return"] < 0].copy()

    if losers.empty:
        return pd.DataFrame(columns=df.columns)

    # Sort by return ascending (most negative first) and take top N
    top_losers = (
        losers.sort_values("return", ascending=True)
        .head(top_n)
    )

    # From top losers, sort by volatility (descending) and take top N
    sell_df = (
        top_losers.sort_values("vol", ascending=False)
        .head(top_n)
        .copy()
    )

    # Add reason column with detailed explanation
    sell_df["reason"] = sell_df.apply(
        lambda row: f"하락({row['return']:.2f}%) 상위 중 변동성 높음({row['vol']:.4f})",
        axis=1
    )

    return sell_df

