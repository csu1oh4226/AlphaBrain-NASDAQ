"""Base interface for market data providers.

This module defines the abstract interface that all market data providers
must implement, allowing easy swapping of data sources.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Tuple
import pandas as pd
from pandas import DataFrame


class MarketDataProvider(ABC):
    """Abstract base class for market data providers.

    All market data providers must implement this interface to ensure
    consistent behavior and easy swapping between different data sources.
    """

    @abstractmethod
    def fetch_price_data(
        self,
        symbols: List[str],
        target_date: date,
        max_retries: int = 2,
    ) -> Tuple[DataFrame, List[str]]:
        """Fetch price data for multiple symbols.

        Args:
            symbols: List of ticker symbols to fetch.
            target_date: Target date for data.
            max_retries: Maximum number of retries for failed requests.

        Returns:
            Tuple of:
            - DataFrame with columns: ticker, date, close, volume
            - List of failed ticker symbols

        Raises:
            Implementation-specific exceptions for critical errors.
        """
        pass

    @abstractmethod
    def fetch_single_symbol(
        self,
        symbol: str,
        target_date: date,
        max_retries: int = 2,
    ) -> pd.Series:
        """Fetch price data for a single symbol.

        Args:
            symbol: Ticker symbol.
            target_date: Target date for data.
            max_retries: Maximum number of retries.

        Returns:
            Series with index: ['ticker', 'date', 'close', 'volume']
            or None if fetch failed.

        Raises:
            Implementation-specific exceptions.
        """
        pass

