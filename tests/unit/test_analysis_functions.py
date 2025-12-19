"""Unit tests for analysis functions (RED phase - tests only).

This module contains tests for:
- calc_daily_returns(df): Calculate daily returns per ticker
- calc_volatility_proxy(df): Calculate volatility proxy (high-low)/open
- rank_movers(df): Rank top movers (gainers, losers, volatile)

These tests are written before implementation (TDD RED phase).
"""

import pytest
import pandas as pd
import numpy as np
from pandas import DataFrame
from datetime import date

# Import functions to test (will fail until implemented - RED phase)
from nasdaq_scanner.core.analysis_functions import (
    calc_daily_returns,
    calc_volatility_proxy,
    rank_movers,
)


class TestCalcDailyReturns:
    """Tests for calc_daily_returns function."""

    @pytest.mark.unit
    def test_calc_daily_returns_basic(self) -> None:
        """Test basic daily returns calculation per ticker."""
        # Given: DataFrame with 2 tickers, 2 days of data
        df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "date": [
                date(2024, 1, 15),
                date(2024, 1, 16),
                date(2024, 1, 15),
                date(2024, 1, 16),
            ],
            "close": [100.0, 105.0, 200.0, 198.0],
        })

        # When: calc_daily_returns is called
        result_df = calc_daily_returns(df)

        # Then: Should add 'return' column with daily returns
        assert "return" in result_df.columns
        assert len(result_df) == 4

        # AAPL: (105 - 100) / 100 * 100 = 5.0%
        aapl_data = result_df[result_df["ticker"] == "AAPL"].sort_values("date")
        assert pd.isna(aapl_data.iloc[0]["return"])  # First day: NaN
        assert aapl_data.iloc[1]["return"] == pytest.approx(5.0, rel=1e-2)

        # MSFT: (198 - 200) / 200 * 100 = -1.0%
        msft_data = result_df[result_df["ticker"] == "MSFT"].sort_values("date")
        assert pd.isna(msft_data.iloc[0]["return"])  # First day: NaN
        assert msft_data.iloc[1]["return"] == pytest.approx(-1.0, rel=1e-2)

    @pytest.mark.unit
    def test_calc_daily_returns_preserves_original_columns(self) -> None:
        """Test that calc_daily_returns preserves original columns."""
        df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL"],
            "date": [date(2024, 1, 15), date(2024, 1, 16)],
            "close": [100.0, 105.0],
            "volume": [1000000, 1100000],
        })

        result_df = calc_daily_returns(df)

        # Original columns should be preserved
        assert "ticker" in result_df.columns
        assert "date" in result_df.columns
        assert "close" in result_df.columns
        assert "volume" in result_df.columns
        assert "return" in result_df.columns

    @pytest.mark.unit
    def test_calc_daily_returns_single_day_per_ticker(self) -> None:
        """Test calc_daily_returns with only one day per ticker."""
        df = pd.DataFrame({
            "ticker": ["AAPL", "MSFT"],
            "date": [date(2024, 1, 15), date(2024, 1, 15)],
            "close": [100.0, 200.0],
        })

        result_df = calc_daily_returns(df)

        # All returns should be NaN (no previous day)
        assert all(pd.isna(result_df["return"]))


class TestCalcVolatilityProxy:
    """Tests for calc_volatility_proxy function."""

    @pytest.mark.unit
    def test_calc_volatility_proxy_basic(self) -> None:
        """Test basic volatility proxy calculation."""
        # Given: DataFrame with OHLC data
        df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "date": [
                date(2024, 1, 15),
                date(2024, 1, 16),
                date(2024, 1, 15),
                date(2024, 1, 16),
            ],
            "open": [100.0, 105.0, 200.0, 198.0],
            "high": [102.0, 107.0, 202.0, 200.0],
            "low": [99.0, 104.0, 199.0, 197.0],
            "close": [101.0, 106.0, 201.0, 199.0],
        })

        # When: calc_volatility_proxy is called
        result_df = calc_volatility_proxy(df)

        # Then: Should add 'vol' column with (high-low)/open
        assert "vol" in result_df.columns

        # AAPL day 1: (102 - 99) / 100 = 0.03 = 3.0%
        aapl_day1 = result_df[
            (result_df["ticker"] == "AAPL") & (result_df["date"] == date(2024, 1, 15))
        ]
        assert aapl_day1.iloc[0]["vol"] == pytest.approx(0.03, rel=1e-2)

        # AAPL day 2: (107 - 104) / 105 = 0.02857 = 2.857%
        aapl_day2 = result_df[
            (result_df["ticker"] == "AAPL") & (result_df["date"] == date(2024, 1, 16))
        ]
        assert aapl_day2.iloc[0]["vol"] == pytest.approx(0.02857, rel=1e-2)

        # MSFT day 1: (202 - 199) / 200 = 0.015 = 1.5%
        msft_day1 = result_df[
            (result_df["ticker"] == "MSFT") & (result_df["date"] == date(2024, 1, 15))
        ]
        assert msft_day1.iloc[0]["vol"] == pytest.approx(0.015, rel=1e-2)

    @pytest.mark.unit
    def test_calc_volatility_proxy_zero_open(self) -> None:
        """Test calc_volatility_proxy handles zero open price."""
        df = pd.DataFrame({
            "ticker": ["AAPL"],
            "date": [date(2024, 1, 15)],
            "open": [0.0],
            "high": [1.0],
            "low": [0.5],
            "close": [0.8],
        })

        result_df = calc_volatility_proxy(df)

        # Should handle zero open gracefully (NaN or inf)
        assert "vol" in result_df.columns
        # Either NaN or inf is acceptable
        vol_value = result_df.iloc[0]["vol"]
        assert pd.isna(vol_value) or np.isinf(vol_value)

    @pytest.mark.unit
    def test_calc_volatility_proxy_preserves_original_columns(self) -> None:
        """Test that calc_volatility_proxy preserves original columns."""
        df = pd.DataFrame({
            "ticker": ["AAPL"],
            "date": [date(2024, 1, 15)],
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [1000000],
        })

        result_df = calc_volatility_proxy(df)

        # Original columns should be preserved
        assert "ticker" in result_df.columns
        assert "date" in result_df.columns
        assert "open" in result_df.columns
        assert "high" in result_df.columns
        assert "low" in result_df.columns
        assert "close" in result_df.columns
        assert "volume" in result_df.columns
        assert "vol" in result_df.columns


class TestRankMovers:
    """Tests for rank_movers function."""

    @pytest.mark.unit
    def test_rank_movers_top10(self) -> None:
        """Test rank_movers returns top 10 gainers, losers, and volatile stocks."""
        # Given: DataFrame with 2 tickers, 2 days of data with returns and volatility
        df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT", "GOOGL", "GOOGL"],
            "date": [
                date(2024, 1, 15),
                date(2024, 1, 16),
                date(2024, 1, 15),
                date(2024, 1, 16),
                date(2024, 1, 15),
                date(2024, 1, 16),
            ],
            "return": [np.nan, 5.0, np.nan, -2.0, np.nan, 3.0],  # AAPL: +5%, MSFT: -2%, GOOGL: +3%
            "vol": [0.02, 0.03, 0.01, 0.015, 0.05, 0.04],  # GOOGL most volatile
            "close": [100.0, 105.0, 200.0, 196.0, 150.0, 154.5],
        })

        # When: rank_movers is called
        result = rank_movers(df)

        # Then: Should return dict with 'gainers', 'losers', 'volatile' DataFrames
        assert isinstance(result, dict)
        assert "gainers" in result
        assert "losers" in result
        assert "volatile" in result

        # All should be DataFrames
        assert isinstance(result["gainers"], DataFrame)
        assert isinstance(result["losers"], DataFrame)
        assert isinstance(result["volatile"], DataFrame)

        # Gainers: Should be sorted by return descending, top 10
        gainers = result["gainers"]
        assert len(gainers) <= 10
        if len(gainers) > 1:
            # Should be sorted descending by return
            returns = gainers["return"].dropna()
            assert returns.is_monotonic_decreasing or len(returns) == 1

        # Losers: Should be sorted by return ascending (most negative first), top 10
        losers = result["losers"]
        assert len(losers) <= 10
        if len(losers) > 1:
            # Should be sorted ascending by return (most negative first)
            returns = losers["return"].dropna()
            assert returns.is_monotonic_increasing or len(returns) == 1

        # Volatile: Should be sorted by vol descending, top 10
        volatile = result["volatile"]
        assert len(volatile) <= 10
        if len(volatile) > 1:
            # Should be sorted descending by vol
            vols = volatile["vol"].dropna()
            assert vols.is_monotonic_decreasing or len(vols) == 1

        # Verify specific rankings with our test data
        # Gainers: AAPL (+5%) > GOOGL (+3%)
        gainer_tickers = gainers["ticker"].tolist()
        if "AAPL" in gainer_tickers and "GOOGL" in gainer_tickers:
            aapl_idx = gainer_tickers.index("AAPL")
            googl_idx = gainer_tickers.index("GOOGL")
            assert aapl_idx < googl_idx  # AAPL should come before GOOGL

        # Losers: MSFT (-2%) should be in losers
        loser_tickers = losers["ticker"].tolist()
        assert "MSFT" in loser_tickers

        # Volatile: GOOGL (0.05) > AAPL (0.03) > MSFT (0.015)
        volatile_tickers = volatile["ticker"].tolist()
        if "GOOGL" in volatile_tickers and "AAPL" in volatile_tickers:
            googl_idx = volatile_tickers.index("GOOGL")
            aapl_idx = volatile_tickers.index("AAPL")
            assert googl_idx < aapl_idx  # GOOGL should come before AAPL

    @pytest.mark.unit
    def test_rank_movers_handles_less_than_10(self) -> None:
        """Test rank_movers when there are less than 10 stocks."""
        # Given: Only 2 tickers
        df = pd.DataFrame({
            "ticker": ["AAPL", "MSFT"],
            "date": [date(2024, 1, 16), date(2024, 1, 16)],
            "return": [5.0, -2.0],
            "vol": [0.03, 0.01],
            "close": [105.0, 196.0],
        })

        result = rank_movers(df)

        # Should return all available stocks (2), not error
        assert len(result["gainers"]) <= 2
        assert len(result["losers"]) <= 2
        assert len(result["volatile"]) <= 2

    @pytest.mark.unit
    def test_rank_movers_handles_nan_values(self) -> None:
        """Test rank_movers handles NaN values in return/vol columns."""
        df = pd.DataFrame({
            "ticker": ["AAPL", "MSFT", "GOOGL"],
            "date": [date(2024, 1, 16), date(2024, 1, 16), date(2024, 1, 16)],
            "return": [5.0, np.nan, 3.0],  # MSFT has NaN return
            "vol": [0.03, 0.01, np.nan],  # GOOGL has NaN vol
            "close": [105.0, 200.0, 150.0],
        })

        result = rank_movers(df)

        # Should handle NaN gracefully
        # Gainers should not include NaN returns
        gainers = result["gainers"]
        if not gainers.empty:
            assert not gainers["return"].isna().any()

        # Volatile should not include NaN vols
        volatile = result["volatile"]
        if not volatile.empty:
            assert not volatile["vol"].isna().any()

    @pytest.mark.unit
    def test_rank_movers_empty_dataframe(self) -> None:
        """Test rank_movers with empty DataFrame."""
        df = pd.DataFrame(columns=["ticker", "date", "return", "vol", "close"])

        result = rank_movers(df)

        # Should return empty DataFrames, not error
        assert isinstance(result["gainers"], DataFrame)
        assert isinstance(result["losers"], DataFrame)
        assert isinstance(result["volatile"], DataFrame)
        assert len(result["gainers"]) == 0
        assert len(result["losers"]) == 0
        assert len(result["volatile"]) == 0

