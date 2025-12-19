"""Unit tests for fetch_ohlcv function.

Tests for fetching OHLCV data from yfinance and converting to tidy DataFrame format.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from pandas import DataFrame

# Import function to test (will fail until implemented - RED phase)
from nasdaq_scanner.providers.fetch_ohlcv import fetch_ohlcv


class TestFetchOhlcv:
    """Tests for fetch_ohlcv function."""

    @pytest.mark.unit
    def test_fetch_ohlcv_returns_tidy_df(self) -> None:
        """Test that fetch_ohlcv returns a tidy DataFrame with correct columns."""
        # Given: List of tickers, period, and interval
        tickers = ["AAPL", "MSFT"]
        period = "5d"
        interval = "1d"

        # Mock yfinance.download to return MultiIndex DataFrame
        mock_yf_data = self._create_mock_yfinance_data(tickers)

        with patch("nasdaq_scanner.providers.fetch_ohlcv.yf.download") as mock_download:
            mock_download.return_value = mock_yf_data

            # When: fetch_ohlcv is called
            result_df = fetch_ohlcv(tickers, period, interval)

            # Then: Should return tidy DataFrame with expected columns
            expected_columns = ["ticker", "date", "open", "high", "low", "close", "volume"]
            assert isinstance(result_df, DataFrame)
            assert list(result_df.columns) == expected_columns
            assert len(result_df) > 0

            # Verify all tickers are present
            assert set(result_df["ticker"].unique()) == set(tickers)

            # Verify date column is date type
            assert pd.api.types.is_datetime64_any_dtype(result_df["date"])

            # Verify numeric columns are numeric
            numeric_cols = ["open", "high", "low", "close", "volume"]
            for col in numeric_cols:
                assert pd.api.types.is_numeric_dtype(result_df[col])

    @pytest.mark.unit
    def test_fetch_ohlcv_single_ticker(self) -> None:
        """Test fetch_ohlcv with a single ticker."""
        tickers = ["AAPL"]
        period = "1d"
        interval = "1d"

        mock_yf_data = self._create_mock_yfinance_data(tickers)

        with patch("nasdaq_scanner.providers.fetch_ohlcv.yf.download") as mock_download:
            mock_download.return_value = mock_yf_data

            result_df = fetch_ohlcv(tickers, period, interval)

            assert len(result_df) > 0
            assert all(result_df["ticker"] == "AAPL")

    @pytest.mark.unit
    def test_fetch_ohlcv_empty_tickers(self) -> None:
        """Test fetch_ohlcv with empty ticker list."""
        tickers = []
        period = "1d"
        interval = "1d"

        with patch("nasdaq_scanner.providers.fetch_ohlcv.yf.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            result_df = fetch_ohlcv(tickers, period, interval)

            assert isinstance(result_df, DataFrame)
            expected_columns = ["ticker", "date", "open", "high", "low", "close", "volume"]
            assert list(result_df.columns) == expected_columns
            assert len(result_df) == 0

    @pytest.mark.unit
    def test_fetch_ohlcv_handles_missing_data(self) -> None:
        """Test fetch_ohlcv handles missing data gracefully."""
        tickers = ["INVALID_TICKER"]
        period = "1d"
        interval = "1d"

        # Mock yfinance to return empty DataFrame
        with patch("nasdaq_scanner.providers.fetch_ohlcv.yf.download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            # Should raise ValueError when no data is returned
            with pytest.raises(ValueError, match="No data"):
                fetch_ohlcv(tickers, period, interval)

    @pytest.mark.unit
    def test_fetch_ohlcv_column_names_lowercase(self) -> None:
        """Test that returned DataFrame has lowercase column names."""
        tickers = ["AAPL"]
        period = "1d"
        interval = "1d"

        mock_yf_data = self._create_mock_yfinance_data(tickers)

        with patch("nasdaq_scanner.providers.fetch_ohlcv.yf.download") as mock_download:
            mock_download.return_value = mock_yf_data

            result_df = fetch_ohlcv(tickers, period, interval)

            # All column names should be lowercase
            assert all(col.islower() for col in result_df.columns)

    @pytest.mark.unit
    def test_fetch_ohlcv_calls_yfinance_with_correct_params(self) -> None:
        """Test that yfinance.download is called with correct parameters."""
        tickers = ["AAPL", "MSFT"]
        period = "5d"
        interval = "1d"

        mock_yf_data = self._create_mock_yfinance_data(tickers)

        with patch("nasdaq_scanner.providers.fetch_ohlcv.yf.download") as mock_download:
            mock_download.return_value = mock_yf_data

            fetch_ohlcv(tickers, period, interval)

            # Verify yfinance.download was called with correct parameters
            mock_download.assert_called_once()
            call_args = mock_download.call_args
            assert call_args[0][0] == tickers  # First positional arg should be tickers
            assert call_args[1]["period"] == period
            assert call_args[1]["interval"] == interval
            assert call_args[1]["group_by"] == "ticker"  # Should group by ticker

    @staticmethod
    def _create_mock_yfinance_data(tickers: list[str]) -> pd.DataFrame:
        """Create mock yfinance.download return value (MultiIndex DataFrame).

        yfinance.download returns a DataFrame with MultiIndex columns:
        - Level 0: OHLCV attributes (Open, High, Low, Close, Volume)
        - Level 1: Ticker symbols
        - Index: DatetimeIndex

        Args:
            tickers: List of ticker symbols.

        Returns:
            Mock DataFrame in yfinance format.
        """
        dates = pd.date_range(start="2024-01-15", periods=5, freq="D")

        # Create MultiIndex columns
        columns = pd.MultiIndex.from_product(
            [["Open", "High", "Low", "Close", "Volume"], tickers],
            names=["Attributes", "Symbols"],
        )

        # Create mock data
        data = []
        for date_idx, date_val in enumerate(dates):
            row = []
            for ticker in tickers:
                base_price = 100.0 + (date_idx * 0.5)  # Slight price increase
                row.extend([
                    base_price,  # Open
                    base_price + 2.0,  # High
                    base_price - 1.0,  # Low
                    base_price + 1.0,  # Close
                    1000000 + (date_idx * 10000),  # Volume
                ])
            data.append(row)

        df = pd.DataFrame(data, index=dates, columns=columns)

        return df


# Mock data example for reference
MOCK_YFINANCE_DATA_EXAMPLE = """
Example of what yfinance.download returns:

MultiIndex DataFrame:
                    Open              High              Low               Close             Volume
                    AAPL    MSFT     AAPL    MSFT     AAPL    MSFT     AAPL    MSFT     AAPL    MSFT
2024-01-15        100.0   200.0    102.0   202.0     99.0    199.0    101.0   201.0    1000000 2000000
2024-01-16        101.0   201.0    103.0   203.0    100.0    200.0    102.0   202.0    1100000 2100000

Expected tidy format:
ticker  date        open    high    low     close   volume
AAPL    2024-01-15  100.0   102.0   99.0    101.0   1000000
AAPL    2024-01-16  101.0   103.0   100.0   102.0   1100000
MSFT    2024-01-15  200.0   202.0   199.0   201.0   2000000
MSFT    2024-01-16  201.0   203.0   200.0   202.0   2100000
"""

