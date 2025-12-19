"""Metrics calculation functions for stock price analysis.

This module provides pure functions for calculating return percentage
and intraday volatility from OHLC (Open, High, Low, Close) data.
"""

import pandas as pd
from pandas import DataFrame
from typing import List


def _validate_required_columns(df: DataFrame, required_column_names: List[str]) -> None:
    """Validate that DataFrame contains all required columns.

    Args:
        df: DataFrame to validate.
        required_column_names: List of required column names.

    Raises:
        KeyError: If any required column is missing, with a clear error message.
    """
    missing_column_names = [
        col_name for col_name in required_column_names if col_name not in df.columns
    ]
    if missing_column_names:
        raise KeyError(
            f"Missing required columns: {', '.join(missing_column_names)}. "
            f"Required columns: {', '.join(required_column_names)}"
        )


def calc_return_pct(df: DataFrame) -> DataFrame:
    """Calculate return percentage from Open and Close prices.

    Formula: (Close - Open) / Open * 100

    Args:
        df: DataFrame with 'Open' and 'Close' columns.

    Returns:
        DataFrame with added 'return_pct' column. Original DataFrame is not modified.

    Raises:
        KeyError: If 'Open' or 'Close' column is missing.

    Examples:
        >>> df = pd.DataFrame({'Open': [100.0], 'Close': [104.0]})
        >>> result = calc_return_pct(df)
        >>> result['return_pct'].iloc[0]
        4.0
    """
    _validate_required_columns(df, required_column_names=["Open", "Close"])

    result_df = df.copy()
    open_prices = result_df["Open"]
    close_prices = result_df["Close"]

    # Calculate return percentage: (Close - Open) / Open * 100
    # Division by zero and NaN values are handled naturally by pandas
    result_df["return_pct"] = ((close_prices - open_prices) / open_prices) * 100

    return result_df


def calc_intraday_vol_pct(df: DataFrame) -> DataFrame:
    """Calculate intraday volatility percentage from Open, High, and Low prices.

    Formula: (High - Low) / Open * 100

    Args:
        df: DataFrame with 'Open', 'High', and 'Low' columns.

    Returns:
        DataFrame with added 'vol_pct' column. Original DataFrame is not modified.

    Raises:
        KeyError: If 'Open', 'High', or 'Low' column is missing.

    Examples:
        >>> df = pd.DataFrame({'Open': [100.0], 'High': [105.0], 'Low': [99.0]})
        >>> result = calc_intraday_vol_pct(df)
        >>> result['vol_pct'].iloc[0]
        6.0
    """
    _validate_required_columns(df, required_column_names=["Open", "High", "Low"])

    result_df = df.copy()
    open_prices = result_df["Open"]
    high_prices = result_df["High"]
    low_prices = result_df["Low"]

    # Calculate intraday volatility percentage: (High - Low) / Open * 100
    # Division by zero and NaN values are handled naturally by pandas
    result_df["vol_pct"] = ((high_prices - low_prices) / open_prices) * 100

    return result_df

