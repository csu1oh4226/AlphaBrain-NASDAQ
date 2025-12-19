"""Data collection module for fetching market data.

This module provides a high-level interface for collecting market data
with support for different ticker sources (NASDAQ-100, CSV files) and
different data providers (yfinance, etc.).
"""

import logging
import pandas as pd
from datetime import date
from typing import List, Tuple, Union, Optional
from pathlib import Path
from pandas import DataFrame

from nasdaq_scanner.providers.base import MarketDataProvider
from nasdaq_scanner.providers.yfinance_provider import YFinanceProvider
from nasdaq_scanner.core.universe import load_tickers

logger = logging.getLogger(__name__)


def get_nasdaq100_tickers() -> List[str]:
    """Get NASDAQ-100 ticker symbols.

    Returns:
        List of NASDAQ-100 ticker symbols (uppercase, sorted).

    Note:
        This is a hardcoded list. For production, consider fetching from
        an API or maintaining a separate data file.
    """
    # NASDAQ-100 ticker list (as of 2024)
    # In production, this should be fetched from an API or maintained in a data file
    nasdaq100 = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'NFLX',
        'AMD', 'PEP', 'ADBE', 'CSCO', 'CMCSA', 'INTU', 'AMGN', 'TXN', 'QCOM', 'ISRG',
        'AMAT', 'HON', 'BKNG', 'VRSK', 'ADI', 'REGN', 'ADP', 'PANW', 'SNPS', 'CDNS',
        'KLAC', 'CRWD', 'MRVL', 'FTNT', 'NXPI', 'ODFL', 'DXCM', 'CTSH', 'IDXX', 'FAST',
        'LRCX', 'KDP', 'BKR', 'PAYX', 'ROST', 'PCAR', 'ON', 'ANSS', 'CDW', 'CPRT',
        'MELI', 'ZS', 'DASH', 'MCHP', 'CTAS', 'WBD', 'GEHC', 'TEAM', 'EXC', 'AEP',
        'FANG', 'VRTX', 'ENPH', 'DLTR', 'ALGN', 'BIIB', 'EA', 'GFS', 'XEL', 'TTD',
        'NDAQ', 'ZS', 'VOD', 'ILMN', 'LCID', 'RIVN', 'PTON', 'DOCN', 'HOOD', 'SOFI',
        'RBLX', 'COIN', 'PLTR', 'AFRM', 'UPST', 'OPEN', 'WISH', 'CLOV', 'SPCE', 'SNDL',
    ]
    
    # Remove duplicates and sort
    return sorted(list(set(nasdaq100)))


def load_ticker_list(source: Union[str, Path, List[str]]) -> List[str]:
    """Load ticker list from various sources.

    Args:
        source: Can be:
            - 'nasdaq-100': Load NASDAQ-100 tickers
            - Path to CSV file: Load from CSV file
            - List of strings: Use directly as ticker list

    Returns:
        List of normalized ticker symbols.

    Raises:
        ValueError: If source format is not recognized.
        FileNotFoundError: If CSV file does not exist.
    """
    if isinstance(source, list):
        # Already a list, normalize it
        normalized = []
        seen = set()
        for ticker in source:
            ticker = str(ticker).strip().upper()
            if ticker and ticker not in seen:
                seen.add(ticker)
                normalized.append(ticker)
        return normalized

    elif isinstance(source, (str, Path)):
        source_str = str(source)
        
        if source_str.lower() == 'nasdaq-100':
            return get_nasdaq100_tickers()
        else:
            # Assume it's a file path
            return load_tickers(source_str)
    
    else:
        raise ValueError(
            f"Unsupported source type: {type(source)}. "
            f"Expected 'nasdaq-100', file path, or list of strings."
        )


def collect_data(
    ticker_source: Union[str, Path, List[str]],
    target_date: date,
    provider: Optional[MarketDataProvider] = None,
    max_retries: int = 2,
) -> Tuple[DataFrame, List[str]]:
    """Collect market data for tickers from specified source.

    Args:
        ticker_source: Source of ticker list:
            - 'nasdaq-100': Use NASDAQ-100 tickers
            - Path to CSV file: Load tickers from CSV
            - List of strings: Use directly as ticker list
        target_date: Target date for data collection.
        provider: MarketDataProvider instance. If None, uses YFinanceProvider.
        max_retries: Maximum number of retries for failed requests.

    Returns:
        Tuple of:
        - DataFrame with columns: ticker, date, close, volume
        - List of failed ticker symbols

    Examples:
        >>> df, failed = collect_data('nasdaq-100', date(2024, 1, 15))
        >>> len(df) > 0
        True
        >>> 'ticker' in df.columns
        True
    """
    # Load ticker list
    logger.info(f"Loading ticker list from source: {ticker_source}")
    try:
        symbols = load_ticker_list(ticker_source)
        logger.info(f"Loaded {len(symbols)} tickers")
    except Exception as e:
        logger.error(f"Failed to load ticker list: {e}")
        raise

    if not symbols:
        logger.warning("No tickers found in source")
        return pd.DataFrame(columns=["ticker", "date", "close", "volume"]), []

    # Use default provider if not specified
    if provider is None:
        provider = YFinanceProvider()

    # Fetch data
    logger.info(f"Collecting data for {len(symbols)} tickers on {target_date}")
    df, failed_symbols = provider.fetch_price_data(
        symbols=symbols,
        target_date=target_date,
        max_retries=max_retries,
    )

    logger.info(
        f"Data collection complete: {len(df)} successful, {len(failed_symbols)} failed"
    )

    return df, failed_symbols

