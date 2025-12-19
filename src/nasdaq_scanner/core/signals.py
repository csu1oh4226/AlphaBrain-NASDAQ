"""Signal generation for buy/sell candidates.

This module provides functions to generate buy and sell signals based on:
- Volatility (high volatility)
- Daily returns (positive for buy, negative for sell)

Rules:
- Buy candidates: High volatility + Positive daily return
- Sell candidates: High volatility + Negative daily return
"""

import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_signals(
    df: DataFrame,
    volatility_threshold: float = 3.0,  # Minimum volatility percentage
    top_n: int = 10
) -> Dict[str, DataFrame]:
    """Generate buy and sell signals based on volatility and returns.

    Args:
        df: DataFrame with columns: ticker, date, return, vol (and optionally others).
        volatility_threshold: Minimum volatility percentage to consider (default: 3.0%).
        top_n: Number of top candidates to return (default: 10).

    Returns:
        Dictionary with keys:
        - 'buy_candidates': DataFrame with buy candidates (high vol + positive return)
        - 'sell_candidates': DataFrame with sell candidates (high vol + negative return)
    """
    if df.empty:
        return {
            'buy_candidates': pd.DataFrame(),
            'sell_candidates': pd.DataFrame(),
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
            'buy_candidates': pd.DataFrame(),
            'sell_candidates': pd.DataFrame(),
        }

    # Filter by volatility threshold
    df_high_vol = df_clean[df_clean["vol"] >= volatility_threshold].copy()

    if df_high_vol.empty:
        return {
            'buy_candidates': pd.DataFrame(),
            'sell_candidates': pd.DataFrame(),
        }

    # Buy candidates: High volatility + Positive return
    buy_candidates = df_high_vol[df_high_vol["return"] > 0].copy()
    buy_candidates = buy_candidates.sort_values(
        by=["vol", "return"],
        ascending=[False, False]
    ).head(top_n)

    # Sell candidates: High volatility + Negative return
    sell_candidates = df_high_vol[df_high_vol["return"] < 0].copy()
    sell_candidates = sell_candidates.sort_values(
        by=["vol", "return"],
        ascending=[False, True]  # Most negative return first
    ).head(top_n)

    # Select standard columns for result
    standard_cols = ["ticker", "date", "open", "high", "low", "close", "volume", "return", "vol"]
    
    def _select_columns(df_result: DataFrame) -> DataFrame:
        if df_result.empty:
            return df_result
        available_cols = [col for col in standard_cols if col in df_result.columns]
        return df_result[available_cols]

    return {
        'buy_candidates': _select_columns(buy_candidates),
        'sell_candidates': _select_columns(sell_candidates),
    }
