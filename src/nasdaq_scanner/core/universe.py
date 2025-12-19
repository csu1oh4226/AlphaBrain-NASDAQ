"""Universe loader functions for loading ticker symbols from CSV files.

This module provides functions for loading and normalizing ticker symbols
from CSV files with various normalization rules.
"""

import pandas as pd
from typing import List


def load_tickers(path: str) -> List[str]:
    """Load ticker symbols from CSV file with normalization.

    Normalization rules applied in order:
    1. Trim whitespace from ticker symbols
    2. Convert to uppercase
    3. Remove duplicates (keep first occurrence, preserve order)
    4. Ignore empty lines (after trimming)

    CSV format handling:
    - If 'symbol' column exists, use it
    - Otherwise, use first column
    - Header row is automatically detected and skipped by pandas

    Args:
        path: Path to CSV file.

    Returns:
        List of normalized ticker symbols (uppercase, no duplicates, no empty strings).

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.

    Examples:
        >>> tickers = load_tickers("tickers.csv")
        >>> "AAPL" in tickers
        True
    """
    # Read CSV file
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {path}")
    except IOError as e:
        raise IOError(f"Error reading CSV file {path}: {str(e)}") from e

    # Determine which column to use
    if "symbol" in df.columns:
        column_name = "symbol"
    elif len(df.columns) > 0:
        column_name = df.columns[0]
    else:
        # Empty DataFrame (no columns)
        return []

    # Extract ticker symbols from the column
    tickers = df[column_name].astype(str).tolist()

    # Normalize tickers
    normalized_tickers: List[str] = []
    seen_tickers = set()

    for ticker in tickers:
        # Trim whitespace
        ticker = ticker.strip()

        # Skip empty strings (after trimming)
        if not ticker:
            continue

        # Convert to uppercase
        ticker = ticker.upper()

        # Remove duplicates (keep first occurrence)
        if ticker not in seen_tickers:
            seen_tickers.add(ticker)
            normalized_tickers.append(ticker)

    return normalized_tickers

