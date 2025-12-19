"""Unit tests for FinanceDataReaderProvider.

Tests cover:
- DataFrame column/index format validation
- Empty data exception handling
- KOSDAQ index (KQ11) fetching
- Individual stock fetching
- Caching behavior
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import date

from nasdaq_scanner.providers.financedatareader_provider import (
    FinanceDataReaderProvider,
    OHLCV_COLUMNS,
)


@pytest.fixture
def provider_index() -> FinanceDataReaderProvider:
    """Fixture for FinanceDataReaderProvider instance (index mode)."""
    with patch('nasdaq_scanner.providers.financedatareader_provider.fdr'):
        return FinanceDataReaderProvider(primary_symbol='KQ11', use_index=True)


@pytest.fixture
def provider_stocks() -> FinanceDataReaderProvider:
    """Fixture for FinanceDataReaderProvider instance (stocks mode)."""
    with patch('nasdaq_scanner.providers.financedatareader_provider.fdr'):
        return FinanceDataReaderProvider(primary_symbol='KQ11', use_index=False)


@pytest.fixture
def sample_fdr_dataframe() -> pd.DataFrame:
    """Sample FinanceDataReader DataFrame."""
    dates = pd.date_range('2025-12-16', periods=3, freq='D')
    return pd.DataFrame({
        'Date': dates,
        'Open': [18500.0, 18550.0, 18600.0],
        'High': [18600.0, 18650.0, 18700.0],
        'Low': [18450.0, 18500.0, 18550.0],
        'Close': [18550.0, 18600.0, 18650.0],
        'Volume': [1000000, 1100000, 1200000],
    })


class TestFinanceDataReaderProvider:
    """Unit tests for FinanceDataReaderProvider."""

    @pytest.mark.unit
    def test_fetch_price_data_returns_correct_dataframe_format(
        self, provider_index: FinanceDataReaderProvider, sample_fdr_dataframe: pd.DataFrame
    ) -> None:
        """Test that fetch_price_data returns DataFrame with correct columns and format."""
        target_date = date(2025, 12, 16)

        with patch.object(provider_index, '_fetch_from_fdr', return_value=sample_fdr_dataframe):
            # When: fetch_price_data is called
            df, failed_symbols = provider_index.fetch_price_data(['KQ11'], target_date)

            # Then: Should return DataFrame with correct columns
            assert isinstance(df, pd.DataFrame)
            assert list(df.columns) == OHLCV_COLUMNS
            assert len(df) > 0
            assert 'ticker' in df.columns
            assert 'date' in df.columns
            assert 'open' in df.columns
            assert 'high' in df.columns
            assert 'low' in df.columns
            assert 'close' in df.columns
            assert 'volume' in df.columns

            # Verify data types
            assert pd.api.types.is_object_dtype(df['ticker'])  # String
            assert pd.api.types.is_datetime64_any_dtype(df['date']) or \
                   isinstance(df['date'].iloc[0], date)  # Date
            assert pd.api.types.is_float_dtype(df['close'])  # Float
            assert pd.api.types.is_integer_dtype(df['volume']) or \
                   pd.api.types.is_float_dtype(df['volume'])  # Integer or Float

            # Verify no failed symbols
            assert len(failed_symbols) == 0

    @pytest.mark.unit
    def test_fetch_price_data_handles_empty_data(
        self, provider_index: FinanceDataReaderProvider
    ) -> None:
        """Test that fetch_price_data handles empty data gracefully."""
        target_date = date(2025, 12, 16)

        with patch.object(provider_index, '_fetch_from_fdr', return_value=pd.DataFrame()):
            # When: fetch_price_data is called with empty data
            df, failed_symbols = provider_index.fetch_price_data(['KQ11'], target_date)

            # Then: Should return empty DataFrame with correct columns
            assert isinstance(df, pd.DataFrame)
            assert list(df.columns) == OHLCV_COLUMNS
            assert df.empty
            # Should have failed symbols
            assert len(failed_symbols) > 0

    @pytest.mark.unit
    def test_fetch_price_data_handles_network_error(
        self, provider_index: FinanceDataReaderProvider
    ) -> None:
        """Test that fetch_price_data handles network errors gracefully."""
        target_date = date(2025, 12, 16)

        with patch.object(provider_index, '_fetch_from_fdr', side_effect=Exception("Network error")):
            # When: fetch_price_data is called with network error
            df, failed_symbols = provider_index.fetch_price_data(['KQ11'], target_date)

            # Then: Should return empty DataFrame and failed symbols
            assert isinstance(df, pd.DataFrame)
            assert df.empty
            assert len(failed_symbols) > 0

    @pytest.mark.unit
    def test_fetch_single_symbol_returns_series(
        self, provider_index: FinanceDataReaderProvider, sample_fdr_dataframe: pd.DataFrame
    ) -> None:
        """Test that fetch_single_symbol returns Series with correct format."""
        target_date = date(2025, 12, 16)

        with patch.object(provider_index, '_fetch_from_fdr', return_value=sample_fdr_dataframe):
            # When: fetch_single_symbol is called
            result = provider_index.fetch_single_symbol('KQ11', target_date)

            # Then: Should return Series with OHLCV data
            assert isinstance(result, pd.Series)
            assert result['ticker'] == 'KQ11'
            assert result['date'] == target_date
            assert 'open' in result.index
            assert 'high' in result.index
            assert 'low' in result.index
            assert 'close' in result.index
            assert 'volume' in result.index

