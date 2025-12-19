"""Analytics functions for stock price analysis.

This module provides pure functions for calculating returns, volatility,
ranking movers, and generating trade recommendations.
"""

import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from typing import Dict, Any


def compute_daily_returns(prices: Series) -> Series:
    """Calculate daily returns percentage from price series.

    Formula: (p[t] - p[t-1]) / p[t-1] * 100

    Args:
        prices: Series of prices (can contain NaN values).

    Returns:
        Series of daily returns in percentage. First value is NaN (no previous value).
        Original Series is not modified.

    Examples:
        >>> prices = pd.Series([100.0, 105.0, 102.0])
        >>> returns = compute_daily_returns(prices)
        >>> returns.iloc[0]  # NaN
        nan
        >>> returns.iloc[1]  # (105-100)/100*100 = 5.0
        5.0
    """
    if len(prices) == 0:
        return pd.Series([], dtype=float)

    # Calculate percentage change: (p[t] - p[t-1]) / p[t-1] * 100
    # pct_change() returns fraction, multiply by 100 for percentage
    returns = prices.pct_change() * 100

    return returns


def compute_volatility(returns: Series, window: int) -> Series:
    """Calculate rolling volatility (standard deviation) of returns.

    Args:
        returns: Series of returns (can contain NaN values).
        window: Rolling window size for standard deviation calculation.

    Returns:
        Series of rolling volatility. First (window-1) values are NaN.
        If window > len(returns), all values are NaN.
        Original Series is not modified.

    Raises:
        ValueError: If window <= 0.

    Examples:
        >>> returns = pd.Series([1.0, 2.0, -1.0, 3.0])
        >>> vol = compute_volatility(returns, window=2)
        >>> pd.isna(vol.iloc[0])  # First value is NaN
        True
        >>> not pd.isna(vol.iloc[1])  # Second value is valid
        True
    """
    if window <= 0:
        raise ValueError(f"window must be > 0, got {window}")

    if len(returns) == 0:
        return pd.Series([], dtype=float)

    # Calculate rolling standard deviation
    # min_periods=window ensures we need at least 'window' values
    volatility = returns.rolling(window=window, min_periods=window).std()

    return volatility


def top_movers(df: DataFrame, n: int, direction: str) -> DataFrame:
    """Get top N movers by return percentage.

    Args:
        df: DataFrame with 'symbol' and 'return_pct' columns.
        n: Number of top movers to return.
        direction: 'up' for top gainers (descending), 'down' for top losers (ascending).
                   Case-insensitive.

    Returns:
        DataFrame with top N movers, sorted by return_pct.
        Rows with NaN in return_pct are excluded.
        If n > len(df), returns all valid rows.
        If n == 0, returns empty DataFrame.
        Original DataFrame is not modified.

    Raises:
        KeyError: If 'return_pct' or 'symbol' column is missing.
        ValueError: If direction is not 'up' or 'down'.

    Examples:
        >>> df = pd.DataFrame({
        ...     'symbol': ['AAPL', 'MSFT', 'GOOGL'],
        ...     'return_pct': [5.0, 7.0, 3.0]
        ... })
        >>> result = top_movers(df, n=2, direction='up')
        >>> result.iloc[0]['symbol']  # MSFT (highest return)
        'MSFT'
    """
    # Validate required columns
    if 'return_pct' not in df.columns:
        raise KeyError("Column 'return_pct' not found in DataFrame")
    if 'symbol' not in df.columns:
        raise KeyError("Column 'symbol' not found in DataFrame (required for tie-breaking)")

    # Validate direction
    direction_lower = direction.lower()
    if direction_lower not in ['up', 'down']:
        raise ValueError(f"direction must be 'up' or 'down', got '{direction}'")

    # Handle empty DataFrame
    if len(df) == 0:
        return df.copy().head(0)

    # Handle n == 0
    if n == 0:
        return df.copy().head(0)

    # Create a copy to avoid side effects
    result_df = df.copy()

    # Exclude rows with NaN in return_pct
    result_df = result_df.dropna(subset=['return_pct'])

    # If no valid rows, return empty DataFrame
    if len(result_df) == 0:
        return result_df.head(0)

    # Determine sort order
    ascending = (direction_lower == 'down')

    # Sort by return_pct (primary) and symbol (tie-breaker)
    result_df = result_df.sort_values(
        by=['return_pct', 'symbol'],
        ascending=[ascending, True],  # symbol always ascending (alphabetical)
        kind='stable'
    )

    # Return top N rows
    return result_df.head(n)


def recommend_trades(metrics_df: DataFrame) -> Dict[str, DataFrame]:
    """Generate buy and sell trade recommendations based on metrics.

    Uses rule-based analysis to identify buy and sell candidates.

    Args:
        metrics_df: DataFrame with columns:
            - 'symbol': Stock symbol
            - 'return_pct': Daily return percentage
            - 'vol_pct': Intraday volatility percentage
            - 'volatility': Rolling volatility (optional, uses vol_pct if missing)

    Returns:
        Dictionary with:
        {
            'buy': DataFrame with buy recommendations (columns: symbol, signal, reason, ...),
            'sell': DataFrame with sell/watch recommendations
        }
        Both DataFrames may be empty if no signals are generated.
        Original DataFrame is not modified.

    Examples:
        >>> df = pd.DataFrame({
        ...     'symbol': ['AAPL', 'TSLA'],
        ...     'return_pct': [6.0, -6.0],
        ...     'vol_pct': [3.0, 6.0],
        ...     'volatility': [2.5, 5.5]
        ... })
        >>> result = recommend_trades(df)
        >>> 'buy' in result
        True
        >>> 'sell' in result
        True
    """
    # Create a copy to avoid side effects
    result_df = metrics_df.copy()

    # Validate required columns
    required_cols = ['symbol', 'return_pct']
    missing_cols = [col for col in required_cols if col not in result_df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

    # Use volatility column if available, otherwise use vol_pct
    if 'volatility' not in result_df.columns and 'vol_pct' in result_df.columns:
        result_df['volatility'] = result_df['vol_pct']

    # Define buy rules
    buy_rules = [
        {
            'name': 'high_return',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                row.get('return_pct', 0) > 5.0
            ),
            'action': 'buy',
            'description': '일간 수익률 5% 이상'
        },
        {
            'name': 'moderate_return',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                3.0 < row.get('return_pct', 0) <= 5.0
            ),
            'action': 'buy',
            'description': '수익률 3-5%'
        },
        {
            'name': 'high_return_low_volatility',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                pd.notna(row.get('volatility')) and
                row.get('return_pct', 0) > 2.0 and
                row.get('volatility', float('inf')) < 3.0
            ),
            'action': 'buy',
            'description': '수익률 2% 이상 + 낮은 변동성'
        },
    ]

    # Define sell rules
    sell_rules = [
        {
            'name': 'sharp_decline',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                row.get('return_pct', 0) < -5.0
            ),
            'action': 'sell',
            'description': '일간 하락률 5% 이상 (급락 주의)'
        },
        {
            'name': 'moderate_decline',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                -5.0 <= row.get('return_pct', 0) < -3.0
            ),
            'action': 'sell',
            'description': '하락률 3-5%'
        },
        {
            'name': 'high_volatility_decline',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                pd.notna(row.get('volatility')) and
                row.get('return_pct', 0) < -2.0 and
                row.get('volatility', 0) > 5.0
            ),
            'action': 'sell',
            'description': '하락률 2% 이상 + 높은 변동성'
        },
    ]

    # Generate buy signals
    buy_signals_df = result_df.copy()
    buy_signals_df['signal'] = pd.NA
    buy_signals_df['reason'] = ''

    for idx, row in buy_signals_df.iterrows():
        matching_rules = []
        for rule in buy_rules:
            try:
                if rule['condition'](row):
                    matching_rules.append(rule['description'])
                    if pd.isna(buy_signals_df.at[idx, 'signal']):
                        buy_signals_df.at[idx, 'signal'] = 'buy'
            except (KeyError, TypeError):
                continue

        if matching_rules:
            buy_signals_df.at[idx, 'reason'] = ', '.join(matching_rules)

    # Generate sell signals
    sell_signals_df = result_df.copy()
    sell_signals_df['signal'] = pd.NA
    sell_signals_df['reason'] = ''

    for idx, row in sell_signals_df.iterrows():
        matching_rules = []
        for rule in sell_rules:
            try:
                if rule['condition'](row):
                    matching_rules.append(rule['description'])
                    if pd.isna(sell_signals_df.at[idx, 'signal']):
                        sell_signals_df.at[idx, 'signal'] = 'sell'
            except (KeyError, TypeError):
                continue

        if matching_rules:
            sell_signals_df.at[idx, 'reason'] = ', '.join(matching_rules)

    # Filter to only rows with signals
    buy_recommendations = buy_signals_df[buy_signals_df['signal'] == 'buy'].copy()
    sell_recommendations = sell_signals_df[sell_signals_df['signal'] == 'sell'].copy()

    # Sort buy by return_pct descending, sell by return_pct ascending
    if not buy_recommendations.empty and 'return_pct' in buy_recommendations.columns:
        buy_recommendations = buy_recommendations.sort_values('return_pct', ascending=False)

    if not sell_recommendations.empty and 'return_pct' in sell_recommendations.columns:
        sell_recommendations = sell_recommendations.sort_values('return_pct', ascending=True)

    return {
        'buy': buy_recommendations,
        'sell': sell_recommendations,
    }

