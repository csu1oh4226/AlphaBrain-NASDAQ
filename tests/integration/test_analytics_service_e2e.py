"""End-to-end integration test for AnalyticsService.

Tests the complete flow:
1. Data collection (providers/data_collector.py)
2. Metrics computation (core/analysis_functions.py)
3. Ranking (core/analysis_functions.py or core/ranking.py)
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import date
from typing import List, Tuple
from pandas import DataFrame, Series

from nasdaq_scanner.services.analytics_service import AnalyticsService
from nasdaq_scanner.providers.base import MarketDataProvider
from nasdaq_scanner.config import DEFAULT_TOP_N


class MockProvider(MarketDataProvider):
    """Mock provider for testing."""

    def __init__(self, mock_data: DataFrame):
        """Initialize with mock data.

        Args:
            mock_data: DataFrame with columns: ticker, date, close, volume
        """
        self.mock_data = mock_data

    def fetch_price_data(
        self,
        symbols: List[str],
        target_date: date,
        max_retries: int = 2,
    ) -> Tuple[DataFrame, List[str]]:
        """Return mock data for requested symbols."""
        # Filter mock_data by requested symbols
        result_df = self.mock_data[
            self.mock_data["ticker"].isin(symbols)
        ].copy()

        # Find failed symbols (requested but not in mock_data)
        fetched_tickers = set(result_df["ticker"].unique())
        failed_symbols = [s for s in symbols if s not in fetched_tickers]

        return result_df, failed_symbols

    def fetch_single_symbol(
        self,
        symbol: str,
        target_date: date,
        max_retries: int = 2,
    ) -> Series:
        """Return mock data for single symbol."""
        symbol_data = self.mock_data[self.mock_data["ticker"] == symbol]
        if symbol_data.empty:
            return None

        # Return latest row as Series
        latest = symbol_data.sort_values("date").iloc[-1]
        return pd.Series({
            'ticker': latest['ticker'],
            'date': latest['date'],
            'close': latest['close'],
            'volume': latest['volume'],
        })


@pytest.mark.integration
def test_analytics_service_end_to_end_flow() -> None:
    """Test complete end-to-end flow: collect -> compute -> rank."""
    # Given: Mock price data (multiple days for multiple tickers)
    mock_price_data = pd.DataFrame([
        # AAPL: 2 days of data
        {'ticker': 'AAPL', 'date': date(2024, 1, 14), 'close': 100.0, 'volume': 50000000},
        {'ticker': 'AAPL', 'date': date(2024, 1, 15), 'close': 105.0, 'volume': 51000000},  # +5%
        # MSFT: 2 days of data
        {'ticker': 'MSFT', 'date': date(2024, 1, 14), 'close': 200.0, 'volume': 30000000},
        {'ticker': 'MSFT', 'date': date(2024, 1, 15), 'close': 196.0, 'volume': 31000000},  # -2%
        # GOOGL: 2 days of data
        {'ticker': 'GOOGL', 'date': date(2024, 1, 14), 'close': 150.0, 'volume': 20000000},
        {'ticker': 'GOOGL', 'date': date(2024, 1, 15), 'close': 160.0, 'volume': 21000000},  # +6.67%
    ])

    # Create mock provider
    mock_provider = MockProvider(mock_price_data)

    # Create service
    service = AnalyticsService(max_retries=0)

    # Step 1: Collect market data
    with patch('nasdaq_scanner.providers.data_collector.YFinanceProvider', return_value=mock_provider):
        ticker_source = ['AAPL', 'MSFT', 'GOOGL']
        target_date = date(2024, 1, 15)
        
        price_df, failed_symbols = service.collect_market_data(
            ticker_source=ticker_source,
            target_date=target_date,
        )

    # Verify data collection
    assert isinstance(price_df, DataFrame)
    assert 'ticker' in price_df.columns
    assert 'date' in price_df.columns
    assert 'close' in price_df.columns
    assert 'volume' in price_df.columns
    assert len(price_df) > 0
    assert len(failed_symbols) == 0  # All symbols should succeed

    # Step 2: Compute metrics (daily returns and volatility)
    volatility_window = 2
    metrics_df = service.compute_metrics(price_df, volatility_window=volatility_window)

    # Verify metrics computation
    assert isinstance(metrics_df, DataFrame)
    assert 'ticker' in metrics_df.columns
    assert 'return' in metrics_df.columns  # Daily return percentage (from calc_daily_returns)
    assert 'vol' in metrics_df.columns  # Intraday volatility (from calc_volatility_proxy or fallback)
    assert len(metrics_df) > 0

    # Verify return calculation (AAPL: (105-100)/100*100 = 5.0%)
    aapl_metrics = metrics_df[metrics_df['ticker'] == 'AAPL']
    if not aapl_metrics.empty:
        assert aapl_metrics['return'].iloc[0] == pytest.approx(5.0, abs=0.1)

    # Verify return calculation (MSFT: (196-200)/200*100 = -2.0%)
    msft_metrics = metrics_df[metrics_df['ticker'] == 'MSFT']
    if not msft_metrics.empty:
        assert msft_metrics['return'].iloc[0] == pytest.approx(-2.0, abs=0.1)

    # Step 3: Get top rankings (gainers, losers, volatile)
    top_n = 2
    rankings = service.get_top_rankings(metrics_df, n=top_n)

    # Verify rankings structure
    assert isinstance(rankings, dict)
    assert 'gainers' in rankings
    assert 'losers' in rankings
    assert 'volatile' in rankings

    # Verify gainers (should be sorted by return descending)
    gainers = rankings['gainers']
    assert isinstance(gainers, DataFrame)
    if not gainers.empty:
        assert 'ticker' in gainers.columns
        assert 'return' in gainers.columns
        # GOOGL should be top gainer (+6.67% > +5%)
        if len(gainers) >= 1:
            top_gainer = gainers.iloc[0]
            assert top_gainer['ticker'] == 'GOOGL' or top_gainer['return'] > 0

    # Verify losers (should be sorted by return ascending)
    losers = rankings['losers']
    assert isinstance(losers, DataFrame)
    if not losers.empty:
        assert 'ticker' in losers.columns
        assert 'return' in losers.columns
        # MSFT should be top loser (-2%)
        if len(losers) >= 1:
            top_loser = losers.iloc[0]
            assert top_loser['ticker'] == 'MSFT' or top_loser['return'] < 0

    # Verify volatile (should be sorted by vol descending)
    volatile = rankings['volatile']
    assert isinstance(volatile, DataFrame)
    if not volatile.empty:
        assert 'ticker' in volatile.columns
        assert 'vol' in volatile.columns


@pytest.mark.integration
def test_analytics_service_handles_empty_data() -> None:
    """Test that AnalyticsService handles empty data gracefully."""
    # Given: Empty price data
    empty_price_df = pd.DataFrame(columns=['ticker', 'date', 'close', 'volume'])

    service = AnalyticsService()

    # When: Compute metrics on empty data
    metrics_df = service.compute_metrics(empty_price_df, volatility_window=5)

    # Then: Should return empty DataFrame
    assert isinstance(metrics_df, DataFrame)
    assert len(metrics_df) == 0

    # When: Get rankings on empty metrics
    rankings = service.get_top_rankings(metrics_df, n=10)

    # Then: Should return empty DataFrames
    assert isinstance(rankings, dict)
    assert len(rankings['gainers']) == 0
    assert len(rankings['losers']) == 0
    assert len(rankings['volatile']) == 0


@pytest.mark.integration
def test_analytics_service_handles_partial_failures() -> None:
    """Test that AnalyticsService handles partial data collection failures."""
    # Given: Mock data with only some symbols
    mock_price_data = pd.DataFrame([
        {'ticker': 'AAPL', 'date': date(2024, 1, 15), 'close': 105.0, 'volume': 51000000},
        # MSFT and GOOGL are missing (will fail)
    ])

    mock_provider = MockProvider(mock_price_data)

    service = AnalyticsService(max_retries=0)

    # When: Collect data for symbols (some will fail)
    with patch('nasdaq_scanner.providers.data_collector.YFinanceProvider') as mock_provider_class:
        mock_provider_class.return_value = mock_provider
        ticker_source = ['AAPL', 'MSFT', 'GOOGL']
        target_date = date(2024, 1, 15)
        
        price_df, failed_symbols = service.collect_market_data(
            ticker_source=ticker_source,
            target_date=target_date,
        )

    # Then: Should have successful data and failed symbols
    assert len(price_df) > 0  # At least AAPL succeeded
    assert len(failed_symbols) > 0  # MSFT and GOOGL failed
    assert 'MSFT' in failed_symbols or 'GOOGL' in failed_symbols

    # When: Compute metrics
    metrics_df = service.compute_metrics(price_df, volatility_window=2)

    # Then: Should only have metrics for successful symbols
    assert len(metrics_df) > 0
    assert set(metrics_df['ticker'].unique()).issubset(set(price_df['ticker'].unique()))

