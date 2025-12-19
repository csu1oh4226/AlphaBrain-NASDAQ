"""Ranking functions for selecting top/bottom N rows from a DataFrame.

This module provides pure functions for ranking and selecting top/bottom N rows
with tie-breaking rules (stable sort + alphabetical symbol ordering).

Sorting Rules:
    - Primary sort: By the specified column (descending for top_n, ascending for bottom_n)
    - Tie-breaker: By 'symbol' column alphabetically (ascending)
    - Sort algorithm: Stable sort (preserves original order for equal values)
    - NaN handling: Rows with NaN in the specified column are excluded
"""

import pandas as pd
from pandas import DataFrame

# Sorting configuration constants
TIE_BREAKER_COLUMN: str = "symbol"
"""Column name used for tie-breaking when primary sort values are equal."""

SORT_KIND: str = "stable"
"""Sort algorithm kind. 'stable' ensures stable sort (preserves original order for equal values)."""

TIE_BREAKER_ASCENDING: bool = True
"""Sort direction for tie-breaker column. True means alphabetical (A-Z) order."""


def _rank_n(
    df: DataFrame, col: str, n: int, ascending: bool
) -> DataFrame:
    """Internal function to rank and return top/bottom N rows.

    Args:
        df: DataFrame to rank.
        col: Column name to sort by.
        n: Number of rows to return.
        ascending: True for bottom (ascending), False for top (descending).

    Returns:
        DataFrame with ranked rows.
    """
    if col not in df.columns:
        raise KeyError(f"Column '{col}' not found in DataFrame")

    if TIE_BREAKER_COLUMN not in df.columns:
        raise KeyError(
            f"Column '{TIE_BREAKER_COLUMN}' not found in DataFrame (required for tie-breaking)"
        )

    # Create a copy to avoid side effects
    result_df = df.copy()

    # Exclude rows with NaN values in the specified column
    result_df = result_df.dropna(subset=[col])

    # If no valid rows or n is 0, return empty DataFrame with same columns
    if len(result_df) == 0 or n == 0:
        return result_df.head(0)

    # Sort by column and tie-breaker
    result_df = result_df.sort_values(
        by=[col, TIE_BREAKER_COLUMN],
        ascending=[ascending, TIE_BREAKER_ASCENDING],
        kind=SORT_KIND,
    )

    # Return top N rows
    return result_df.head(n)


def top_n(df: DataFrame, col: str, n: int) -> DataFrame:
    """Return top N rows sorted by column in descending order.

    Sorting Rules:
        - Primary sort: By 'col' in descending order (highest values first)
        - Tie-breaker: By 'symbol' column alphabetically (ascending, A-Z)
        - Sort algorithm: Stable sort (preserves original order for equal values)
        - NaN handling: Rows with NaN in 'col' are excluded

    Args:
        df: DataFrame to rank. Must contain 'col' and 'symbol' columns.
        col: Column name to sort by (primary sort key).
        n: Number of top rows to return. If n > len(df), returns all valid rows.

    Returns:
        DataFrame with top N rows, sorted by:
        1. 'col' (descending)
        2. 'symbol' (ascending, for ties)
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
    return _rank_n(df, col, n, ascending=False)


def bottom_n(df: DataFrame, col: str, n: int) -> DataFrame:
    """Return bottom N rows sorted by column in ascending order.

    Sorting Rules:
        - Primary sort: By 'col' in ascending order (lowest values first)
        - Tie-breaker: By 'symbol' column alphabetically (ascending, A-Z)
        - Sort algorithm: Stable sort (preserves original order for equal values)
        - NaN handling: Rows with NaN in 'col' are excluded

    Args:
        df: DataFrame to rank. Must contain 'col' and 'symbol' columns.
        col: Column name to sort by (primary sort key).
        n: Number of bottom rows to return. If n > len(df), returns all valid rows.

    Returns:
        DataFrame with bottom N rows, sorted by:
        1. 'col' (ascending)
        2. 'symbol' (ascending, for ties)
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
    return _rank_n(df, col, n, ascending=True)

