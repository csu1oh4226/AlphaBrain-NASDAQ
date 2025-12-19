"""Unit tests for stock name mapper.

Tests for mapping ticker symbols to stock names using FinanceDataReader.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from nasdaq_scanner.core.stock_name_mapper import (
    get_stock_name_mapping,
    get_stock_name,
    add_stock_names_to_dataframe,
)


class TestGetStockNameMapping:
    """Tests for get_stock_name_mapping function."""

    @patch('nasdaq_scanner.core.stock_name_mapper.fdr')
    def test_get_stock_name_mapping_kospi_success(self, mock_fdr):
        """Test successful mapping for KOSPI stocks."""
        # Arrange
        mock_df = pd.DataFrame({
            'Symbol': ['005930', '000660'],
            'Name': ['삼성전자', 'SK하이닉스']
        })
        mock_fdr.StockListing.return_value = mock_df

        # Act
        result = get_stock_name_mapping('KOSPI')

        # Assert
        assert result == {'005930': '삼성전자', '000660': 'SK하이닉스'}
        mock_fdr.StockListing.assert_called_once_with('KOSPI')

    @patch('nasdaq_scanner.core.stock_name_mapper.fdr')
    def test_get_stock_name_mapping_kosdaq_success(self, mock_fdr):
        """Test successful mapping for KOSDAQ stocks."""
        # Arrange
        mock_df = pd.DataFrame({
            'Code': ['035720', '035420'],
            'Name': ['카카오', 'NAVER']
        })
        mock_fdr.StockListing.return_value = mock_df

        # Act
        result = get_stock_name_mapping('KOSDAQ')

        # Assert
        assert result == {'035720': '카카오', '035420': 'NAVER'}

    @patch('nasdaq_scanner.core.stock_name_mapper.fdr')
    def test_get_stock_name_mapping_empty_dataframe(self, mock_fdr):
        """Test handling of empty DataFrame."""
        # Arrange
        mock_fdr.StockListing.return_value = pd.DataFrame()

        # Act
        result = get_stock_name_mapping('KOSPI')

        # Assert
        assert result == {}

    @patch('nasdaq_scanner.core.stock_name_mapper.fdr', None)
    def test_get_stock_name_mapping_fdr_not_available(self):
        """Test handling when FinanceDataReader is not available."""
        # Act
        result = get_stock_name_mapping('KOSPI')

        # Assert
        assert result == {}

    @patch('nasdaq_scanner.core.stock_name_mapper.fdr')
    def test_get_stock_name_mapping_index_symbols(self, mock_fdr):
        """Test mapping for index symbols (KS11, KQ11)."""
        # Arrange
        mock_df = pd.DataFrame({
            'Symbol': ['005930'],
            'Name': ['삼성전자']
        })
        mock_fdr.StockListing.return_value = mock_df

        # Act
        result = get_stock_name_mapping('KOSPI')

        # Assert
        # Index symbols (KS11, KQ11) are not in stock listings
        # They should be handled separately
        assert 'KS11' not in result
        assert 'KQ11' not in result


class TestGetStockName:
    """Tests for get_stock_name function."""

    @patch('nasdaq_scanner.core.stock_name_mapper.get_stock_name_mapping')
    def test_get_stock_name_found(self, mock_get_mapping):
        """Test getting stock name when found."""
        # Arrange
        mock_get_mapping.return_value = {'005930': '삼성전자'}

        # Act
        result = get_stock_name('005930', 'KOSPI')

        # Assert
        assert result == '삼성전자'

    @patch('nasdaq_scanner.core.stock_name_mapper.get_stock_name_mapping')
    def test_get_stock_name_not_found(self, mock_get_mapping):
        """Test getting stock name when not found."""
        # Arrange
        mock_get_mapping.return_value = {}

        # Act
        result = get_stock_name('999999', 'KOSPI')

        # Assert
        assert result == '999999'  # Returns ticker if not found

    @patch('nasdaq_scanner.core.stock_name_mapper.get_stock_name_mapping')
    def test_get_stock_name_index_symbol(self, mock_get_mapping):
        """Test getting name for index symbol (KS11, KQ11)."""
        # Arrange
        mock_get_mapping.return_value = {}

        # Act
        result_ks11 = get_stock_name('KS11', 'KOSPI')
        result_kq11 = get_stock_name('KQ11', 'KOSDAQ')

        # Assert
        assert result_ks11 == 'KS11'  # Should return ticker for index
        assert result_kq11 == 'KQ11'


class TestAddStockNamesToDataFrame:
    """Tests for add_stock_names_to_dataframe function."""

    @patch('nasdaq_scanner.core.stock_name_mapper.get_stock_name_mapping')
    def test_add_stock_names_success(self, mock_get_mapping):
        """Test adding stock names to DataFrame."""
        # Arrange
        df = pd.DataFrame({
            'ticker': ['005930', '000660'],
            'return': [1.5, -0.5],
            'close': [70000, 120000]
        })
        mock_get_mapping.return_value = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스'
        }

        # Act
        result = add_stock_names_to_dataframe(df, market='KOSPI')

        # Assert
        assert 'name' in result.columns
        assert result.loc[0, 'name'] == '삼성전자'
        assert result.loc[1, 'name'] == 'SK하이닉스'

    @patch('nasdaq_scanner.core.stock_name_mapper.get_stock_name_mapping')
    def test_add_stock_names_empty_dataframe(self, mock_get_mapping):
        """Test adding names to empty DataFrame."""
        # Arrange
        df = pd.DataFrame()

        # Act
        result = add_stock_names_to_dataframe(df, market='KOSPI')

        # Assert
        assert result.empty

    @patch('nasdaq_scanner.core.stock_name_mapper.get_stock_name_mapping')
    def test_add_stock_names_no_ticker_column(self, mock_get_mapping):
        """Test adding names when ticker column is missing."""
        # Arrange
        df = pd.DataFrame({
            'return': [1.5],
            'close': [70000]
        })

        # Act
        result = add_stock_names_to_dataframe(df, market='KOSPI')

        # Assert
        assert 'name' not in result.columns

    @patch('nasdaq_scanner.core.stock_name_mapper.get_stock_name_mapping')
    def test_add_stock_names_index_symbol(self, mock_get_mapping):
        """Test adding names for index symbols."""
        # Arrange
        df = pd.DataFrame({
            'ticker': ['KS11'],
            'return': [0.12],
            'close': [3994.51]
        })
        mock_get_mapping.return_value = {}  # Index not in stock listings

        # Act
        result = add_stock_names_to_dataframe(df, market='KOSPI')

        # Assert
        assert 'name' in result.columns
        assert result.loc[0, 'name'] == 'KS11'  # Should use ticker as name

