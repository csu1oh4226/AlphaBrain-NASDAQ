"""Data collection module for fetching market data.

This module provides a high-level interface for collecting market data
with support for different ticker sources (KOSPI/KOSDAQ index, top stocks, CSV files) and
FinanceDataReader provider.
"""

import logging
import pandas as pd
from datetime import date
from typing import List, Tuple, Union, Optional
from pathlib import Path
from pandas import DataFrame

from nasdaq_scanner.providers.base import MarketDataProvider
from nasdaq_scanner.providers.financedatareader_provider import FinanceDataReaderProvider
from nasdaq_scanner.core.universe import load_tickers
from nasdaq_scanner.core.korea_universe import (
    get_tickers,
    get_index_symbol,
)

logger = logging.getLogger(__name__)


def load_ticker_list(source: Union[str, Path, List[str]]) -> List[str]:
    """Load ticker list from various sources.

    Args:
        source: Can be:
            - 'kosdaq-index': Load KOSDAQ index (KQ11) only
            - 'kosdaq-top': Load top KOSDAQ stocks by market cap
            - 'nasdaq-100': Load NASDAQ-100 tickers (legacy)
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
            ticker = str(ticker).strip()
            if ticker and ticker not in seen:
                seen.add(ticker)
                normalized.append(ticker)
        return normalized

    elif isinstance(source, (str, Path)):
        source_str = str(source)
        
        if source_str.lower() in ['kosdaq-index', 'kospi-index']:
            # Return index symbol
            market = 'KOSDAQ' if 'kosdaq' in source_str.lower() else 'KOSPI'
            return [get_index_symbol(market)]
        elif source_str.lower() in ['kosdaq-top', 'kospi-top']:
            # Return top stocks by market cap (default: top 100)
            market = 'KOSDAQ' if 'kosdaq' in source_str.lower() else 'KOSPI'
            return get_tickers(market, top_n=100, by_market_cap=True)
        else:
            # Assume it's a file path
            return load_tickers(source_str)
    
    else:
        raise ValueError(
            f"Unsupported source type: {type(source)}. "
            f"Expected 'kospi-index', 'kospi-top', 'kosdaq-index', 'kosdaq-top', file path, or list of strings."
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
            - 'kospi-index' or 'kosdaq-index': Use index symbol (KS11 or KQ11)
            - 'kospi-top' or 'kosdaq-top': Use top stocks by market cap
            - Path to CSV file: Load tickers from CSV
            - List of strings: Use directly as ticker list
        target_date: Target date for data collection.
        provider: MarketDataProvider instance. If None, uses FinanceDataReaderProvider.
        max_retries: Maximum number of retries for failed requests.

    Returns:
        Tuple of:
        - DataFrame with columns: ticker, date, open, high, low, close, volume (OHLCV)
        - List of failed ticker symbols

    Examples:
        >>> df, failed = collect_data('kospi-top', date(2024, 1, 15))
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
        from nasdaq_scanner.config import OHLCV_COLUMNS
        return pd.DataFrame(columns=OHLCV_COLUMNS), []

    # Use default provider if not specified
    # For KOSPI/KOSDAQ, use FinanceDataReaderProvider
    if provider is None:
        if isinstance(ticker_source, str):
            source_lower = ticker_source.lower()
            if source_lower in ['kosdaq-index', 'kospi-index']:
                market = 'KOSDAQ' if 'kosdaq' in source_lower else 'KOSPI'
                index_symbol = get_index_symbol(market)
                provider = FinanceDataReaderProvider(primary_symbol=index_symbol, use_index=True)
                logger.info(f"Using FinanceDataReaderProvider for {market} index ({index_symbol})")
            elif source_lower in ['kosdaq-top', 'kospi-top']:
                market = 'KOSDAQ' if 'kosdaq' in source_lower else 'KOSPI'
                index_symbol = get_index_symbol(market)
                provider = FinanceDataReaderProvider(primary_symbol=index_symbol, use_index=False)
                logger.info(f"Using FinanceDataReaderProvider for {market} stocks")
            else:
                # For CSV or manual input, use FinanceDataReaderProvider as default
                provider = FinanceDataReaderProvider(primary_symbol='KS11', use_index=False)
                logger.info("Using FinanceDataReaderProvider for individual tickers")
        else:
            # For list input, use FinanceDataReaderProvider as default
            provider = FinanceDataReaderProvider(primary_symbol='KS11', use_index=False)
            logger.info("Using FinanceDataReaderProvider for individual tickers")

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

