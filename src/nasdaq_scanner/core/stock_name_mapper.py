"""Stock name mapper for KOSPI/KOSDAQ.

This module provides functions to map ticker symbols to stock names.
"""

import logging
from typing import Dict, Optional
import pandas as pd

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = None

logger = logging.getLogger(__name__)

# Cache for stock listings
_stock_listings_cache: Dict[str, pd.DataFrame] = {}


def get_stock_name_mapping(market: str) -> Dict[str, str]:
    """Get mapping from ticker symbol to stock name.

    Args:
        market: 'KOSPI' or 'KOSDAQ'

    Returns:
        Dictionary mapping ticker symbol to stock name.
    """
    if fdr is None:
        logger.warning("FinanceDataReader not available, returning empty mapping")
        return {}

    # Check cache first
    if market.upper() in _stock_listings_cache:
        df = _stock_listings_cache[market.upper()]
    else:
        try:
            df = fdr.StockListing(market.upper())
            if df.empty:
                logger.warning(f"Empty {market} stock listings")
                return {}
            _stock_listings_cache[market.upper()] = df
        except Exception as e:
            logger.error(f"Error fetching {market} stock listings: {e}", exc_info=True)
            return {}

    # Create mapping
    mapping = {}
    if 'Symbol' in df.columns and 'Name' in df.columns:
        for _, row in df.iterrows():
            symbol = str(row['Symbol']).strip()
            name = str(row['Name']).strip()
            if symbol and name:
                mapping[symbol] = name
    elif 'Code' in df.columns and 'Name' in df.columns:
        for _, row in df.iterrows():
            code = str(row['Code']).strip()
            name = str(row['Name']).strip()
            if code and name:
                mapping[code] = name

    logger.info(f"Created stock name mapping for {market}: {len(mapping)} stocks")
    return mapping


def get_stock_name(ticker: str, market: Optional[str] = None) -> str:
    """Get stock name for a ticker symbol.

    Args:
        ticker: Ticker symbol (e.g., '005930', 'KS11', 'KQ11').
        market: Market name ('KOSPI' or 'KOSDAQ'). If None, tries both.

    Returns:
        Stock name if found, otherwise returns ticker.
        For index symbols (KS11, KQ11), returns Korean name.
    """
    # Handle index symbols
    index_names = {
        'KS11': 'KOSPI 종합지수',
        'KQ11': 'KOSDAQ 종합지수'
    }
    if ticker in index_names:
        return index_names[ticker]

    if market:
        markets = [market]
    else:
        markets = ['KOSPI', 'KOSDAQ']

    for mkt in markets:
        mapping = get_stock_name_mapping(mkt)
        if ticker in mapping:
            return mapping[ticker]

    # If not found, return ticker
    return ticker


def add_stock_names_to_dataframe(
    df: pd.DataFrame,
    market: Optional[str] = None,
    ticker_col: str = 'ticker',
    name_col: str = 'name'
) -> pd.DataFrame:
    """Add stock names to DataFrame.

    Args:
        df: DataFrame with ticker column.
        market: Market name ('KOSPI' or 'KOSDAQ'). If None, tries both.
        ticker_col: Name of ticker column (default: 'ticker').
        name_col: Name of name column to add (default: 'name').

    Returns:
        DataFrame with added name column.
    """
    if df.empty or ticker_col not in df.columns:
        return df.copy()

    result_df = df.copy()

    # Add name column using get_stock_name (handles index symbols)
    result_df[name_col] = result_df[ticker_col].apply(
        lambda t: get_stock_name(str(t).strip(), market)
    )

    return result_df

