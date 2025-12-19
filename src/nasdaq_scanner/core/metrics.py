"""Metrics calculation functions for stock price analysis.

This module provides pure functions for calculating return percentage
and intraday volatility from OHLC (Open, High, Low, Close) data.
"""

import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame


def calc_return_pct(df: "DataFrame") -> "DataFrame":
    """Calculate return percentage from Open and Close prices.

    Formula: (Close - Open) / Open * 100

    Args:
        df: DataFrame with 'Open' and 'Close' columns.

    Returns:
        DataFrame with added 'return_pct' column.

    Raises:
        KeyError: If 'Open' or 'Close' column is missing.
        ValueError: If required columns are missing.

    Examples:
        >>> df = pd.DataFrame({'Open': [100.0], 'Close': [104.0]})
        >>> result = calc_return_pct(df)
        >>> result['return_pct'].iloc[0]
        4.0
    """
    # Validate required columns
    required_columns = ["Open", "Close"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(
            f"Missing required columns: {', '.join(missing_columns)}. "
            f"Required columns: {', '.join(required_columns)}"
        )

    # Create a copy to avoid side effects
    result = df.copy()

    # Calculate return percentage: (Close - Open) / Open * 100
    # Handle division by zero and NaN values naturally
    result["return_pct"] = ((result["Close"] - result["Open"]) / result["Open"]) * 100

    return result


def calc_intraday_vol_pct(df: "DataFrame") -> "DataFrame":
    """Calculate intraday volatility percentage from Open, High, and Low prices.

    Formula: (High - Low) / Open * 100

    Args:
        df: DataFrame with 'Open', 'High', and 'Low' columns.

    Returns:
        DataFrame with added 'vol_pct' column.

    Raises:
        KeyError: If 'Open', 'High', or 'Low' column is missing.
        ValueError: If required columns are missing.

    Examples:
        >>> df = pd.DataFrame({'Open': [100.0], 'High': [105.0], 'Low': [99.0]})
        >>> result = calc_intraday_vol_pct(df)
        >>> result['vol_pct'].iloc[0]
        6.0
    """
    # Validate required columns
    required_columns = ["Open", "High", "Low"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(
            f"Missing required columns: {', '.join(missing_columns)}. "
            f"Required columns: {', '.join(required_columns)}"
        )

    # Create a copy to avoid side effects
    result = df.copy()

    # Calculate intraday volatility percentage: (High - Low) / Open * 100
    # Handle division by zero and NaN values naturally
    result["vol_pct"] = ((result["High"] - result["Low"]) / result["Open"]) * 100

    return result

