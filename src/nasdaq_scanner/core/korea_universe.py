"""KOSPI/KOSDAQ universe management.

This module provides functions to load KOSPI and KOSDAQ stock listings.
"""

import logging
from typing import List, Optional
import pandas as pd

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = None

logger = logging.getLogger(__name__)


def get_stock_listings(market: str) -> pd.DataFrame:
    """Get stock listings from FinanceDataReader.

    Args:
        market: 'KOSPI' or 'KOSDAQ'

    Returns:
        DataFrame with columns: Symbol, Name, Market, Sector, Industry, etc.

    Raises:
        ImportError: If FinanceDataReader is not installed.
        ValueError: If market is not 'KOSPI' or 'KOSDAQ'.
    """
    if fdr is None:
        raise ImportError(
            "FinanceDataReader is not installed. "
            "Please install it with: pip install finance-datareader>=0.9.50"
        )

    if market.upper() not in ['KOSPI', 'KOSDAQ']:
        raise ValueError(f"Market must be 'KOSPI' or 'KOSDAQ', got: {market}")

    try:
        # Get all stock listings
        df = fdr.StockListing(market.upper())
        
        if df.empty:
            logger.warning(f"Empty {market} stock listings from FinanceDataReader")
            return pd.DataFrame()
        
        logger.info(f"Loaded {len(df)} {market} stocks from FinanceDataReader")
        return df
    except Exception as e:
        logger.error(f"Error fetching {market} stock listings: {e}", exc_info=True)
        return pd.DataFrame()


def get_tickers(
    market: str,
    top_n: Optional[int] = None,
    by_market_cap: bool = True
) -> List[str]:
    """Get ticker symbols for KOSPI or KOSDAQ.

    Args:
        market: 'KOSPI' or 'KOSDAQ'
        top_n: If provided, return only top N stocks by market cap.
        by_market_cap: If True, sort by market cap (descending). If False, return all.

    Returns:
        List of ticker symbols (stock codes).
    """
    df = get_stock_listings(market)
    
    if df.empty:
        logger.warning(f"No {market} stocks found")
        return []

    # Filter out invalid symbols
    if 'Symbol' in df.columns:
        df = df[df['Symbol'].notna()]
        df = df[df['Symbol'].str.len() == 6]  # Korean stock codes are 6 digits
        symbols = df['Symbol'].tolist()
    elif 'Code' in df.columns:
        df = df[df['Code'].notna()]
        df = df[df['Code'].str.len() == 6]
        symbols = df['Code'].tolist()
    else:
        logger.error(f"No Symbol or Code column found in {market} listings")
        return []

    # Sort by market cap if requested
    if by_market_cap and 'Marcap' in df.columns:
        df = df.sort_values('Marcap', ascending=False)
        symbols = df['Symbol'].tolist() if 'Symbol' in df.columns else df['Code'].tolist()

    # Limit to top N if specified
    if top_n is not None and top_n > 0:
        symbols = symbols[:top_n]

    logger.info(f"Returning {len(symbols)} {market} tickers")
    return symbols


def get_index_symbol(market: str) -> str:
    """Get index symbol for market.

    Args:
        market: 'KOSPI' or 'KOSDAQ'

    Returns:
        Index symbol: 'KS11' for KOSPI, 'KQ11' for KOSDAQ
    """
    market_upper = market.upper()
    if market_upper == 'KOSPI':
        return 'KS11'
    elif market_upper == 'KOSDAQ':
        return 'KQ11'
    else:
        raise ValueError(f"Market must be 'KOSPI' or 'KOSDAQ', got: {market}")

