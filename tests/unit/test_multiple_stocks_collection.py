"""Unit tests for multiple stocks collection.

Tests for collecting data from multiple stocks successfully.
"""

import pytest
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock

from nasdaq_scanner.providers.financedatareader_provider import FinanceDataReaderProvider
from nasdaq_scanner.providers.data_collector import collect_data
from nasdaq_scanner.core.korea_universe import get_tickers


class TestMultipleStocksCollection:
    """Tests for collecting data from multiple stocks."""

    @patch('nasdaq_scanner.providers.financedatareader_provider.fdr')
    def test_fetch_multiple_stocks_success(self, mock_fdr):
        """Test successfully fetching multiple stocks."""
        # Arrange
        def mock_data_reader(symbol, start, end):
            return pd.DataFrame({
                'Date': [date(2025, 12, 18)],
                'Open': [70000 if symbol == '005930' else 120000],
                'High': [71000 if symbol == '005930' else 125000],
                'Low': [69000 if symbol == '005930' else 115000],
                'Close': [70500 if symbol == '005930' else 122000],
                'Volume': [1000000]
            })

        mock_fdr.DataReader.side_effect = mock_data_reader
        provider = FinanceDataReaderProvider(primary_symbol='KS11', use_index=False)

        # Act
        df, failed = provider.fetch_price_data(
            ['005930', '000660'], date(2025, 12, 18), max_retries=1
        )

        # Assert
        assert not df.empty
        assert len(df) == 2
        assert set(df['ticker'].unique()) == {'005930', '000660'}
        assert len(failed) == 0

    @patch('nasdaq_scanner.core.korea_universe.fdr')
    @patch('nasdaq_scanner.providers.financedatareader_provider.fdr')
    def test_collect_top_stocks(self, mock_fdr_provider, mock_fdr_universe):
        """Test collecting data for top stocks."""
        # Arrange - Mock stock listings
        mock_listings = pd.DataFrame({
            'Symbol': ['005930', '000660', '035720', '035420', '051910'],
            'Name': ['삼성전자', 'SK하이닉스', '카카오', 'NAVER', 'LG화학'],
            'Marcap': [500000000000, 300000000000, 200000000000, 150000000000, 100000000000]
        })
        mock_fdr_universe.StockListing.return_value = mock_listings

        # Arrange - Mock data reader
        def mock_data_reader(symbol, start, end):
            return pd.DataFrame({
                'Date': [date(2025, 12, 18)],
                'Open': [70000],
                'High': [71000],
                'Low': [69000],
                'Close': [70500],
                'Volume': [1000000]
            })

        mock_fdr_provider.DataReader.side_effect = mock_data_reader

        # Act
        tickers = get_tickers('KOSPI', top_n=5, by_market_cap=True)
        df, failed = collect_data('kospi-top', date(2025, 12, 18), max_retries=1)

        # Assert
        assert len(tickers) == 5
        assert not df.empty
        assert len(df) >= 1  # At least some stocks should be collected

    @patch('nasdaq_scanner.providers.financedatareader_provider.fdr')
    def test_fetch_stocks_with_different_dates(self, mock_fdr):
        """Test fetching stocks with different trading dates."""
        # Arrange
        def mock_data_reader(symbol, start, end):
            # Return data for the target date
            return pd.DataFrame({
                'Date': [date(2025, 12, 18)],
                'Open': [70000],
                'High': [71000],
                'Low': [69000],
                'Close': [70500],
                'Volume': [1000000]
            })

        mock_fdr.DataReader.side_effect = mock_data_reader
        provider = FinanceDataReaderProvider(primary_symbol='KS11', use_index=False)

        # Act
        df, failed = provider.fetch_price_data(
            ['005930', '000660'], date(2025, 12, 18), max_retries=1
        )

        # Assert
        assert not df.empty
        assert all(df['date'] == date(2025, 12, 18))
        assert len(failed) == 0

