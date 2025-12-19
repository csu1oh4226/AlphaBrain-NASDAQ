"""Unit tests for data collection failure scenarios.

Tests for handling failures in data collection from FinanceDataReader.
"""

import pytest
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock

from nasdaq_scanner.providers.financedatareader_provider import FinanceDataReaderProvider
from nasdaq_scanner.providers.data_collector import collect_data


class TestDataCollectionFailure:
    """Tests for data collection failure scenarios."""

    @patch('nasdaq_scanner.providers.financedatareader_provider.fdr')
    def test_fetch_empty_dataframe(self, mock_fdr):
        """Test handling of empty DataFrame from FinanceDataReader."""
        # Arrange
        mock_fdr.DataReader.return_value = pd.DataFrame()
        provider = FinanceDataReaderProvider(primary_symbol='KQ11', use_index=True)

        # Act
        df, failed = provider.fetch_price_data(['KQ11'], date(2025, 12, 18), max_retries=1)

        # Assert
        assert df.empty
        assert len(failed) > 0
        assert 'KQ11' in failed

    @patch('nasdaq_scanner.providers.financedatareader_provider.fdr')
    def test_fetch_network_error(self, mock_fdr):
        """Test handling of network errors."""
        # Arrange
        mock_fdr.DataReader.side_effect = Exception("Network error")
        provider = FinanceDataReaderProvider(primary_symbol='KQ11', use_index=True)

        # Act
        df, failed = provider.fetch_price_data(['KQ11'], date(2025, 12, 18), max_retries=1)

        # Assert
        assert df.empty
        assert len(failed) > 0

    @patch('nasdaq_scanner.providers.financedatareader_provider.fdr')
    def test_fetch_multiple_stocks_partial_failure(self, mock_fdr):
        """Test handling when some stocks fail to fetch."""
        # Arrange
        def mock_data_reader(symbol, start, end):
            if symbol == '005930':
                return pd.DataFrame({
                    'Date': [date(2025, 12, 18)],
                    'Open': [70000],
                    'High': [71000],
                    'Low': [69000],
                    'Close': [70500],
                    'Volume': [1000000]
                })
            else:
                raise Exception("Symbol not found")

        mock_fdr.DataReader.side_effect = mock_data_reader
        provider = FinanceDataReaderProvider(primary_symbol='KS11', use_index=False)

        # Act
        df, failed = provider.fetch_price_data(
            ['005930', '999999'], date(2025, 12, 18), max_retries=1
        )

        # Assert
        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]['ticker'] == '005930'
        assert len(failed) == 1
        assert '999999' in failed

    def test_collect_data_empty_ticker_list(self):
        """Test collecting data with empty ticker list."""
        # Act
        df, failed = collect_data([], date(2025, 12, 18))

        # Assert
        assert df.empty
        assert len(failed) == 0

    @patch('nasdaq_scanner.providers.financedatareader_provider.fdr')
    def test_collect_data_all_stocks_fail(self, mock_fdr):
        """Test collecting data when all stocks fail."""
        # Arrange
        mock_fdr.DataReader.side_effect = Exception("All requests failed")
        provider = FinanceDataReaderProvider(primary_symbol='KS11', use_index=False)

        # Act
        df, failed = provider.fetch_price_data(
            ['005930', '000660'], date(2025, 12, 18), max_retries=1
        )

        # Assert
        assert df.empty
        assert len(failed) == 2

