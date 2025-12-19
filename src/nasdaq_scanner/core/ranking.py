"""Ranking functions for selecting top/bottom N rows from a DataFrame.

This module provides pure functions for ranking and selecting top/bottom N rows
with tie-breaking rules (stable sort + alphabetical symbol ordering).
"""

import pandas as pd
from pandas import DataFrame


def top_n(df: DataFrame, col: str, n: int) -> DataFrame:
    """Return top N rows sorted by column in descending order.

    Ties are broken by sorting 'symbol' column alphabetically (ascending).
    Rows with NaN values in the specified column are excluded.

    Args:
        df: DataFrame to rank.
        col: Column name to sort by.
        n: Number of top rows to return.

    Returns:
        DataFrame with top N rows, sorted by col (descending) then symbol (ascending).
        Original DataFrame is not modified.

    Raises:
        KeyError: If 'col' or 'symbol' column is missing.

    Examples:
        >>> df = pd.DataFrame({
        ...     'symbol': ['AAPL', 'MSFT', 'GOOGL'],
        ...     'return_pct': [5.0, 7.0, 6.0]
        ... })
        >>> result = top_n(df, col='return_pct', n=2)
        >>> result['return_pct'].iloc[0]
        7.0
    """
    if col not in df.columns:
        raise KeyError(f"Column '{col}' not found in DataFrame")

    if "symbol" not in df.columns:
        raise KeyError("Column 'symbol' not found in DataFrame (required for tie-breaking)")

    # Create a copy to avoid side effects
    result_df = df.copy()

    # Exclude rows with NaN values in the specified column
    result_df = result_df.dropna(subset=[col])

    # If no valid rows or n is 0, return empty DataFrame with same columns
    if len(result_df) == 0 or n == 0:
        return result_df.head(0)

    # Sort by column (descending) and symbol (ascending) for tie-breaking
    # kind='stable' ensures stable sort (preserves original order for equal values)
    result_df = result_df.sort_values(
        by=[col, "symbol"],
        ascending=[False, True],
        kind="stable",
    )

    # Return top N rows
    return result_df.head(n)


def bottom_n(df: DataFrame, col: str, n: int) -> DataFrame:
    """Return bottom N rows sorted by column in ascending order.

    Ties are broken by sorting 'symbol' column alphabetically (ascending).
    Rows with NaN values in the specified column are excluded.

    Args:
        df: DataFrame to rank.
        col: Column name to sort by.
        n: Number of bottom rows to return.

    Returns:
        DataFrame with bottom N rows, sorted by col (ascending) then symbol (ascending).
        Original DataFrame is not modified.

    Raises:
        KeyError: If 'col' or 'symbol' column is missing.

    Examples:
        >>> df = pd.DataFrame({
        ...     'symbol': ['AAPL', 'MSFT', 'GOOGL'],
        ...     'return_pct': [5.0, 7.0, 6.0]
        ... })
        >>> result = bottom_n(df, col='return_pct', n=2)
        >>> result['return_pct'].iloc[0]
        5.0
    """
    if col not in df.columns:
        raise KeyError(f"Column '{col}' not found in DataFrame")

    if "symbol" not in df.columns:
        raise KeyError("Column 'symbol' not found in DataFrame (required for tie-breaking)")

    # Create a copy to avoid side effects
    result_df = df.copy()

    # Exclude rows with NaN values in the specified column
    result_df = result_df.dropna(subset=[col])

    # If no valid rows or n is 0, return empty DataFrame with same columns
    if len(result_df) == 0 or n == 0:
        return result_df.head(0)

    # Sort by column (ascending) and symbol (ascending) for tie-breaking
    # kind='stable' ensures stable sort (preserves original order for equal values)
    result_df = result_df.sort_values(
        by=[col, "symbol"],
        ascending=[True, True],
        kind="stable",
    )

    # Return bottom N rows
    return result_df.head(n)

