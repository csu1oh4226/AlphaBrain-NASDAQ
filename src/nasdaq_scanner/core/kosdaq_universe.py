"""KOSDAQ universe management.

This module provides functions to load KOSDAQ stock listings and filter by market cap.
"""

import logging
from typing import List, Optional
import pandas as pd

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = None

logger = logging.getLogger(__name__)


def get_kosdaq_stock_listings() -> pd.DataFrame:
    """Get KOSDAQ stock listings from FinanceDataReader.

    Returns:
        DataFrame with columns: Symbol, Name, Market, Sector, Industry, etc.

    Raises:
        ImportError: If FinanceDataReader is not installed.
    """
    if fdr is None:
        raise ImportError(
            "FinanceDataReader is not installed. "
            "Please install it with: pip install finance-datareader>=0.9.50"
        )

    try:
        # Get all stock listings
        df = fdr.StockListing('KOSDAQ')
        
        if df.empty:
            logger.warning("Empty KOSDAQ stock listings from FinanceDataReader")
            return pd.DataFrame()
        
        logger.info(f"Loaded {len(df)} KOSDAQ stocks from FinanceDataReader")
        return df
    except Exception as e:
        logger.error(f"Error fetching KOSDAQ stock listings: {e}", exc_info=True)
        return pd.DataFrame()


def get_kosdaq_tickers(
    top_n: Optional[int] = None,
    by_market_cap: bool = True
) -> List[str]:
    """Get KOSDAQ ticker symbols.

    Args:
        top_n: If provided, return only top N stocks by market cap.
        by_market_cap: If True, sort by market cap (descending). If False, return all.

    Returns:
        List of KOSDAQ ticker symbols (stock codes).
    """
    df = get_kosdaq_stock_listings()
    
    if df.empty:
        logger.warning("No KOSDAQ stocks found")
        return []

    # Filter out invalid symbols
    if 'Symbol' in df.columns:
        df = df[df['Symbol'].notna()]
        df = df[df['Symbol'].str.len() == 6]  # KOSDAQ codes are 6 digits
        symbols = df['Symbol'].tolist()
    elif 'Code' in df.columns:
        df = df[df['Code'].notna()]
        df = df[df['Code'].str.len() == 6]
        symbols = df['Code'].tolist()
    else:
        logger.error("No Symbol or Code column found in KOSDAQ listings")
        return []

    # Sort by market cap if requested
    if by_market_cap and 'Marcap' in df.columns:
        df = df.sort_values('Marcap', ascending=False)
        symbols = df['Symbol'].tolist() if 'Symbol' in df.columns else df['Code'].tolist()

    # Limit to top N if specified
    if top_n is not None and top_n > 0:
        symbols = symbols[:top_n]

    logger.info(f"Returning {len(symbols)} KOSDAQ tickers")
    return symbols


def get_kosdaq_index_symbol() -> str:
    """Get KOSDAQ index symbol.

    Returns:
        'KQ11' (KOSDAQ Composite Index symbol).
    """
    return 'KQ11'

