"""Unit tests for YFinanceProvider.

Tests for yfinance-based market data provider implementation.
All external network calls are mocked to ensure unit test isolation.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from typing import List
from pandas import DataFrame, Series

from nasdaq_scanner.providers.yfinance_provider import YFinanceProvider
from nasdaq_scanner.providers.base import MarketDataProvider


class TestYFinanceProvider:
    """Tests for YFinanceProvider class."""

    @pytest.fixture
    def provider(self) -> YFinanceProvider:
        """Create YFinanceProvider instance."""
        with patch("nasdaq_scanner.providers.yfinance_provider.yf"):
            return YFinanceProvider()

    @pytest.fixture
    def sample_target_date(self) -> date:
        """Sample target date for testing."""
        return date(2024, 1, 15)

    @pytest.fixture
    def mock_history_dataframe(self) -> DataFrame:
        """Create mock yfinance history DataFrame with OHLCV columns."""
        # Create a DataFrame with OHLCV columns (yfinance format)
        dates = pd.date_range(start="2024-01-10", end="2024-01-16", freq="D")
        data = {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0],
            "High": [105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0],
            "Low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
            "Close": [104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
            "Volume": [50000000, 51000000, 52000000, 53000000, 54000000, 55000000, 56000000],
        }
        df = pd.DataFrame(data, index=dates)
        return df

    def _create_mock_ticker(self, symbol: str, history_df: DataFrame) -> MagicMock:
        """Create a mock yfinance Ticker object."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = history_df
        return mock_ticker

    # ====================================================================
    # fetch_single_symbol Tests
    # ====================================================================

    @pytest.mark.unit
    def test_fetch_single_symbol_returns_series_with_ohlcv_columns(
        self, provider: YFinanceProvider, sample_target_date: date, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_single_symbol returns Series with ticker, date, close, volume."""
        # Given: Valid symbol and target date
        symbol = "AAPL"

        # Mock yfinance.Ticker
        mock_ticker = self._create_mock_ticker(symbol, mock_history_dataframe)

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_single_symbol is called
            result = provider.fetch_single_symbol(symbol, sample_target_date)

            # Then: Should return Series with expected columns
            assert result is not None
            assert isinstance(result, Series)
            assert result["ticker"] == symbol
            assert result["date"] == sample_target_date
            assert "close" in result
            assert "volume" in result
            assert isinstance(result["close"], float)
            assert isinstance(result["volume"], int)

            # Verify yfinance.Ticker was called
            mock_ticker_class.assert_called_once_with(symbol)
            mock_ticker.history.assert_called_once()

    @pytest.mark.unit
    def test_fetch_single_symbol_handles_empty_history(
        self, provider: YFinanceProvider, sample_target_date: date
    ) -> None:
        """Test that fetch_single_symbol returns None when history is empty (invalid ticker)."""
        # Given: Invalid symbol that returns empty history
        symbol = "INVALID_TICKER"

        # Mock yfinance.Ticker to return empty DataFrame
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_single_symbol is called
            result = provider.fetch_single_symbol(symbol, sample_target_date)

            # Then: Should return None (failure policy: return None for invalid ticker)
            assert result is None

    @pytest.mark.unit
    def test_fetch_single_symbol_handles_exception(
        self, provider: YFinanceProvider, sample_target_date: date
    ) -> None:
        """Test that fetch_single_symbol returns None when exception occurs."""
        # Given: Symbol that raises exception
        symbol = "ERROR_TICKER"

        # Mock yfinance.Ticker to raise exception
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("Network error")

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_single_symbol is called
            result = provider.fetch_single_symbol(symbol, sample_target_date, max_retries=0)

            # Then: Should return None after retries exhausted
            assert result is None

    @pytest.mark.unit
    def test_fetch_single_symbol_retries_on_failure(
        self, provider: YFinanceProvider, sample_target_date: date, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_single_symbol retries on failure."""
        # Given: Symbol that fails first time, succeeds second time
        symbol = "AAPL"

        mock_ticker = MagicMock()
        # First call fails, second call succeeds
        mock_ticker.history.side_effect = [
            Exception("Temporary error"),
            mock_history_dataframe,
        ]

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_single_symbol is called with max_retries=1
            result = provider.fetch_single_symbol(symbol, sample_target_date, max_retries=1)

            # Then: Should succeed after retry
            assert result is not None
            assert result["ticker"] == symbol
            # Verify retry happened (called twice)
            assert mock_ticker.history.call_count == 2

    @pytest.mark.unit
    def test_fetch_single_symbol_uses_closest_previous_trading_day(
        self, provider: YFinanceProvider, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_single_symbol uses closest previous trading day if target_date not in history."""
        # Given: Target date that is not in history (e.g., weekend)
        symbol = "AAPL"
        target_date = date(2024, 1, 14)  # Sunday (not a trading day)

        # Mock history with data up to Friday
        friday_date = pd.Timestamp("2024-01-12")
        history_df = mock_history_dataframe.loc[:friday_date]

        mock_ticker = self._create_mock_ticker(symbol, history_df)

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_single_symbol is called
            result = provider.fetch_single_symbol(symbol, target_date)

            # Then: Should use closest previous trading day (Friday)
            assert result is not None
            assert result["ticker"] == symbol
            assert result["date"] == target_date  # date field is still target_date
            assert "close" in result

    # ====================================================================
    # fetch_price_data Tests
    # ====================================================================

    @pytest.mark.unit
    def test_fetch_price_data_returns_dataframe_with_expected_columns(
        self, provider: YFinanceProvider, sample_target_date: date, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_price_data returns DataFrame with ticker, date, close, volume columns."""
        # Given: List of valid symbols
        symbols = ["AAPL", "MSFT"]

        # Mock yfinance.Ticker for each symbol
        mock_ticker_aapl = self._create_mock_ticker("AAPL", mock_history_dataframe)
        mock_ticker_msft = self._create_mock_ticker("MSFT", mock_history_dataframe)

        def ticker_side_effect(symbol: str) -> MagicMock:
            if symbol == "AAPL":
                return mock_ticker_aapl
            elif symbol == "MSFT":
                return mock_ticker_msft
            return MagicMock()

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.side_effect = ticker_side_effect

            # When: fetch_price_data is called
            df, failed_symbols = provider.fetch_price_data(symbols, sample_target_date)

            # Then: Should return DataFrame with expected columns
            assert isinstance(df, DataFrame)
            expected_columns = ["ticker", "date", "close", "volume"]
            assert list(df.columns) == expected_columns
            assert len(df) == len(symbols)
            assert len(failed_symbols) == 0

            # Verify all symbols are present
            assert set(df["ticker"].unique()) == set(symbols)

    @pytest.mark.unit
    def test_fetch_price_data_handles_invalid_tickers(
        self, provider: YFinanceProvider, sample_target_date: date, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_price_data handles invalid tickers by returning them in failed_symbols list."""
        # Given: Mix of valid and invalid symbols
        symbols = ["AAPL", "INVALID_TICKER", "MSFT"]

        # Mock: AAPL and MSFT succeed, INVALID_TICKER fails (empty history)
        mock_ticker_aapl = self._create_mock_ticker("AAPL", mock_history_dataframe)
        mock_ticker_msft = self._create_mock_ticker("MSFT", mock_history_dataframe)
        mock_ticker_invalid = MagicMock()
        mock_ticker_invalid.history.return_value = pd.DataFrame()  # Empty DataFrame

        def ticker_side_effect(symbol: str) -> MagicMock:
            if symbol == "AAPL":
                return mock_ticker_aapl
            elif symbol == "MSFT":
                return mock_ticker_msft
            elif symbol == "INVALID_TICKER":
                return mock_ticker_invalid
            return MagicMock()

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.side_effect = ticker_side_effect

            # When: fetch_price_data is called
            df, failed_symbols = provider.fetch_price_data(symbols, sample_target_date)

            # Then: Should return successful symbols in DataFrame, failed in list
            # Policy: Invalid tickers are added to failed_symbols, not included in DataFrame
            assert isinstance(df, DataFrame)
            assert len(df) == 2  # Only AAPL and MSFT
            assert len(failed_symbols) == 1
            assert "INVALID_TICKER" in failed_symbols
            assert "AAPL" not in failed_symbols
            assert "MSFT" not in failed_symbols

            # Verify successful symbols are in DataFrame
            assert set(df["ticker"].unique()) == {"AAPL", "MSFT"}

    @pytest.mark.unit
    def test_fetch_price_data_returns_empty_dataframe_when_all_tickers_fail(
        self, provider: YFinanceProvider, sample_target_date: date
    ) -> None:
        """Test that fetch_price_data returns empty DataFrame when all tickers fail."""
        # Given: All invalid symbols
        symbols = ["INVALID1", "INVALID2"]

        # Mock: All return empty history
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_price_data is called
            df, failed_symbols = provider.fetch_price_data(symbols, sample_target_date)

            # Then: Should return empty DataFrame with correct columns, all in failed list
            # Policy: When all tickers fail, return empty DataFrame with expected columns
            assert isinstance(df, DataFrame)
            assert len(df) == 0
            expected_columns = ["ticker", "date", "close", "volume"]
            assert list(df.columns) == expected_columns
            assert len(failed_symbols) == len(symbols)
            assert set(failed_symbols) == set(symbols)

    @pytest.mark.unit
    def test_fetch_price_data_handles_exceptions_gracefully(
        self, provider: YFinanceProvider, sample_target_date: date, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_price_data handles exceptions and continues processing other symbols."""
        # Given: Mix of symbols, one raises exception
        symbols = ["AAPL", "ERROR_TICKER", "MSFT"]

        # Mock: AAPL and MSFT succeed, ERROR_TICKER raises exception
        mock_ticker_aapl = self._create_mock_ticker("AAPL", mock_history_dataframe)
        mock_ticker_msft = self._create_mock_ticker("MSFT", mock_history_dataframe)
        mock_ticker_error = MagicMock()
        mock_ticker_error.history.side_effect = Exception("Network error")

        def ticker_side_effect(symbol: str) -> MagicMock:
            if symbol == "AAPL":
                return mock_ticker_aapl
            elif symbol == "MSFT":
                return mock_ticker_msft
            elif symbol == "ERROR_TICKER":
                return mock_ticker_error
            return MagicMock()

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.side_effect = ticker_side_effect

            # When: fetch_price_data is called
            df, failed_symbols = provider.fetch_price_data(symbols, sample_target_date, max_retries=0)

            # Then: Should return successful symbols, failed in list
            # Policy: Exceptions are caught, symbol added to failed_symbols, processing continues
            assert isinstance(df, DataFrame)
            assert len(df) == 2  # AAPL and MSFT
            assert len(failed_symbols) == 1
            assert "ERROR_TICKER" in failed_symbols

    @pytest.mark.unit
    def test_fetch_price_data_handles_empty_symbols_list(
        self, provider: YFinanceProvider, sample_target_date: date
    ) -> None:
        """Test that fetch_price_data handles empty symbols list."""
        # Given: Empty symbols list
        symbols: List[str] = []

        # When: fetch_price_data is called
        df, failed_symbols = provider.fetch_price_data(symbols, sample_target_date)

        # Then: Should return empty DataFrame with correct columns, empty failed list
        assert isinstance(df, DataFrame)
        assert len(df) == 0
        expected_columns = ["ticker", "date", "close", "volume"]
        assert list(df.columns) == expected_columns
        assert len(failed_symbols) == 0

    # ====================================================================
    # Interface Compliance Tests
    # ====================================================================

    @pytest.mark.unit
    def test_yfinance_provider_implements_market_data_provider(
        self, provider: YFinanceProvider
    ) -> None:
        """Test that YFinanceProvider implements MarketDataProvider interface."""
        # Then: Should be instance of MarketDataProvider
        assert isinstance(provider, MarketDataProvider)

    @pytest.mark.unit
    def test_yfinance_provider_raises_import_error_when_yfinance_not_installed(self) -> None:
        """Test that YFinanceProvider raises ImportError when yfinance is not installed."""
        # Given: yfinance module is None (not installed)
        with patch("nasdaq_scanner.providers.yfinance_provider.yf", None):
            # When/Then: Should raise ImportError
            with pytest.raises(ImportError, match="yfinance is not installed"):
                YFinanceProvider()

    # ====================================================================
    # Edge Cases
    # ====================================================================

    @pytest.mark.unit
    def test_fetch_single_symbol_handles_history_without_target_date(
        self, provider: YFinanceProvider, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_single_symbol handles history that doesn't contain target_date."""
        # Given: Target date that is before all history data
        symbol = "AAPL"
        target_date = date(2024, 1, 5)  # Before all history dates

        # Mock history with dates after target_date
        mock_ticker = self._create_mock_ticker(symbol, mock_history_dataframe)

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_single_symbol is called
            result = provider.fetch_single_symbol(symbol, target_date)

            # Then: Should return None (no previous trading day available)
            # Policy: If no previous trading day exists, return None
            assert result is None

    @pytest.mark.unit
    def test_fetch_price_data_preserves_data_types(
        self, provider: YFinanceProvider, sample_target_date: date, mock_history_dataframe: DataFrame
    ) -> None:
        """Test that fetch_price_data preserves correct data types in returned DataFrame."""
        # Given: Valid symbol
        symbols = ["AAPL"]

        mock_ticker = self._create_mock_ticker("AAPL", mock_history_dataframe)

        with patch("nasdaq_scanner.providers.yfinance_provider.yf.Ticker") as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker

            # When: fetch_price_data is called
            df, _ = provider.fetch_price_data(symbols, sample_target_date)

            # Then: Data types should be correct
            assert pd.api.types.is_object_dtype(df["ticker"])  # String
            assert pd.api.types.is_datetime64_any_dtype(df["date"]) or isinstance(
                df["date"].iloc[0], date
            )  # Date
            assert pd.api.types.is_float_dtype(df["close"])  # Float
            assert pd.api.types.is_integer_dtype(df["volume"])  # Integer

