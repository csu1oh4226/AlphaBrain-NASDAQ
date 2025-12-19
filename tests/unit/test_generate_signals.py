"""Unit tests for generate_signals function (RED phase - tests only).

This module contains tests for:
- generate_signals(df_ranked): Generate buy/sell signals based on rules

These tests are written before implementation (TDD RED phase).
"""

import pytest
import pandas as pd
import numpy as np
from pandas import DataFrame
from datetime import date

# Import function to test (will fail until implemented - RED phase)
from nasdaq_scanner.core.signal_generator import generate_signals


class TestGenerateSignals:
    """Tests for generate_signals function."""

    @pytest.mark.unit
    def test_generate_signals_buy_candidates_intersection(self) -> None:
        """Test that buy_candidates are intersection of top gainers and top volatile."""
        # Given: DataFrame with ranked data (from rank_movers output format)
        # Create sample data with gainers and volatile rankings
        df_ranked = pd.DataFrame({
            "ticker": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"],
            "date": [date(2024, 1, 16)] * 6,
            "close": [105.0, 196.0, 154.5, 180.0, 250.0, 400.0],
            "return": [5.0, 3.0, 4.0, 2.0, 6.0, 1.0],  # TSLA: +6%, AAPL: +5%, GOOGL: +4%
            "vol": [0.05, 0.02, 0.06, 0.01, 0.07, 0.03],  # TSLA: 0.07, GOOGL: 0.06, AAPL: 0.05
        })

        # When: generate_signals is called
        result = generate_signals(df_ranked)

        # Then: Should return dict with 'buy_candidates' and 'sell_candidates'
        assert isinstance(result, dict)
        assert "buy_candidates" in result
        assert "sell_candidates" in result

        # buy_candidates should be intersection of:
        # - Top gainers (by return): TSLA (6%), AAPL (5%), GOOGL (4%)
        # - Top volatile (by vol): TSLA (0.07), GOOGL (0.06), AAPL (0.05)
        # Intersection: TSLA, GOOGL, AAPL (all 3 are in both top 3)
        buy_candidates = result["buy_candidates"]
        assert isinstance(buy_candidates, DataFrame)
        assert "ticker" in buy_candidates.columns
        assert "reason" in buy_candidates.columns  # Reason column should be present

        # Verify intersection logic: should contain tickers that are in both top gainers and top volatile
        # For this test data, if we take top 3 gainers and top 3 volatile:
        # Top 3 gainers: TSLA, AAPL, GOOGL
        # Top 3 volatile: TSLA, GOOGL, AAPL
        # Intersection: TSLA, GOOGL, AAPL (all 3)
        buy_tickers = set(buy_candidates["ticker"].unique())
        expected_buy = {"TSLA", "GOOGL", "AAPL"}  # In both top 3 gainers and top 3 volatile
        assert buy_tickers == expected_buy

        # Verify reason column contains explanation
        if len(buy_candidates) > 0:
            for _, row in buy_candidates.iterrows():
                assert isinstance(row["reason"], str)
                assert len(row["reason"]) > 0

    @pytest.mark.unit
    def test_generate_signals_sell_candidates_from_losers(self) -> None:
        """Test that sell_candidates are from losers with high volatility."""
        # Given: DataFrame with ranked data including losers
        df_ranked = pd.DataFrame({
            "ticker": ["XYZ", "ABC", "DEF", "GHI"],
            "date": [date(2024, 1, 16)] * 4,
            "close": [50.0, 60.0, 70.0, 80.0],
            "return": [-5.0, -3.0, -2.0, -1.0],  # All losers: XYZ worst, ABC second worst
            "vol": [0.08, 0.06, 0.02, 0.01],  # XYZ: 0.08 (highest), ABC: 0.06
        })

        # When: generate_signals is called
        result = generate_signals(df_ranked)

        # Then: sell_candidates should be from losers, sorted by volatility (descending)
        sell_candidates = result["sell_candidates"]
        assert isinstance(sell_candidates, DataFrame)
        assert "ticker" in sell_candidates.columns

        # sell_candidates: 하락 top10 중 변동성 상위
        # All are losers, so top volatile losers: XYZ (0.08), ABC (0.06)
        sell_tickers = sell_candidates["ticker"].tolist()
        assert "XYZ" in sell_tickers  # Highest vol among losers
        assert "ABC" in sell_tickers  # Second highest vol among losers

        # Should be sorted by vol descending
        if len(sell_candidates) > 1:
            vols = sell_candidates["vol"].tolist()
            assert vols == sorted(vols, reverse=True)  # Descending order

        # Should have reason column
        assert "reason" in sell_candidates.columns
        if len(sell_candidates) > 0:
            assert isinstance(sell_candidates.iloc[0]["reason"], str)
            assert len(sell_candidates.iloc[0]["reason"]) > 0

    @pytest.mark.unit
    def test_generate_signals_buy_no_intersection(self) -> None:
        """Test buy_candidates when there's no intersection between gainers and volatile."""
        # Given: Data where top gainers and top volatile don't overlap
        df_ranked = pd.DataFrame({
            "ticker": ["GAINER1", "GAINER2", "VOLATILE1", "VOLATILE2"],
            "date": [date(2024, 1, 16)] * 4,
            "close": [100.0, 110.0, 200.0, 210.0],
            "return": [10.0, 8.0, 1.0, 0.5],  # GAINER1, GAINER2 are top gainers
            "vol": [0.01, 0.02, 0.10, 0.09],  # VOLATILE1, VOLATILE2 are top volatile
        })

        # When: generate_signals is called
        result = generate_signals(df_ranked)

        # Then: buy_candidates should be empty (no intersection)
        buy_candidates = result["buy_candidates"]
        assert isinstance(buy_candidates, DataFrame)
        assert len(buy_candidates) == 0

    @pytest.mark.unit
    def test_generate_signals_sell_no_losers(self) -> None:
        """Test sell_candidates when there are no losers."""
        # Given: Data with only gainers (all positive returns)
        df_ranked = pd.DataFrame({
            "ticker": ["AAPL", "MSFT"],
            "date": [date(2024, 1, 16)] * 2,
            "close": [105.0, 210.0],
            "return": [5.0, 3.0],  # All positive
            "vol": [0.05, 0.03],
        })

        # When: generate_signals is called
        result = generate_signals(df_ranked)

        # Then: sell_candidates should be empty
        sell_candidates = result["sell_candidates"]
        assert isinstance(sell_candidates, DataFrame)
        assert len(sell_candidates) == 0

    @pytest.mark.unit
    def test_generate_signals_preserves_original_columns(self) -> None:
        """Test that generate_signals preserves original columns in results."""
        df_ranked = pd.DataFrame({
            "ticker": ["AAPL", "TSLA"],
            "date": [date(2024, 1, 16)] * 2,
            "close": [105.0, 250.0],
            "return": [5.0, 6.0],
            "vol": [0.05, 0.07],
            "volume": [1000000, 2000000],  # Additional column
        })

        result = generate_signals(df_ranked)

        # buy_candidates should preserve original columns and include reason
        if len(result["buy_candidates"]) > 0:
            buy = result["buy_candidates"]
            assert "ticker" in buy.columns
            assert "date" in buy.columns
            assert "close" in buy.columns
            assert "return" in buy.columns
            assert "vol" in buy.columns
            assert "volume" in buy.columns  # Additional column preserved
            assert "reason" in buy.columns  # Reason column should be present
            # Reason should be a string explaining why
            assert isinstance(buy.iloc[0]["reason"], str)
            assert len(buy.iloc[0]["reason"]) > 0

    @pytest.mark.unit
    def test_generate_signals_empty_dataframe(self) -> None:
        """Test generate_signals with empty DataFrame."""
        df_ranked = pd.DataFrame(columns=["ticker", "date", "close", "return", "vol"])

        result = generate_signals(df_ranked)

        # Should return empty DataFrames, not error
        assert isinstance(result["buy_candidates"], DataFrame)
        assert isinstance(result["sell_candidates"], DataFrame)
        assert len(result["buy_candidates"]) == 0
        assert len(result["sell_candidates"]) == 0

    @pytest.mark.unit
    def test_generate_signals_handles_nan_values(self) -> None:
        """Test generate_signals handles NaN values in return/vol."""
        df_ranked = pd.DataFrame({
            "ticker": ["AAPL", "MSFT", "GOOGL"],
            "date": [date(2024, 1, 16)] * 3,
            "close": [105.0, 200.0, 150.0],
            "return": [5.0, np.nan, 3.0],  # MSFT has NaN return
            "vol": [0.05, 0.02, np.nan],  # GOOGL has NaN vol
        })

        result = generate_signals(df_ranked)

        # Should handle NaN gracefully
        # buy_candidates should not include NaN returns or vols
        buy = result["buy_candidates"]
        if not buy.empty:
            assert not buy["return"].isna().any()
            assert not buy["vol"].isna().any()

        # sell_candidates should not include NaN returns or vols
        sell = result["sell_candidates"]
        if not sell.empty:
            assert not sell["return"].isna().any()
            assert not sell["vol"].isna().any()

    @pytest.mark.unit
    def test_generate_signals_top_n_configurable(self) -> None:
        """Test that top N for gainers/volatile/losers is configurable."""
        # Given: Data with more than 10 stocks
        df_ranked = pd.DataFrame({
            "ticker": [f"STOCK{i}" for i in range(20)],
            "date": [date(2024, 1, 16)] * 20,
            "close": [100.0] * 20,
            "return": [10.0 - i * 0.5 for i in range(20)],  # Decreasing returns
            "vol": [0.10 - i * 0.005 for i in range(20)],  # Decreasing volatility
        })

        # When: generate_signals is called (default should use top 10)
        result = generate_signals(df_ranked)

        # Then: Should use top 10 for intersection
        # Top 10 gainers: STOCK0-STOCK9
        # Top 10 volatile: STOCK0-STOCK9
        # Intersection: STOCK0-STOCK9 (all 10)
        buy = result["buy_candidates"]
        # Should have at most 10 (intersection of top 10 gainers and top 10 volatile)
        assert len(buy) <= 10

    @pytest.mark.unit
    def test_generate_signals_documentation_rules(self) -> None:
        """Test that the rules are correctly implemented as documented.

        Rules:
        1. buy_candidates: 상위 상승 + 변동성 상위 교집합
           - Top N gainers (by return, descending)
           - Top N volatile (by vol, descending)
           - Intersection of the two sets

        2. sell_candidates: 하락 top10 중 변동성 상위
           - Top N losers (by return, ascending - most negative first)
           - From those losers, select top M by volatility (descending)
        """
        # Given: Clear test data
        df_ranked = pd.DataFrame({
            "ticker": ["BEST", "GOOD", "BAD", "WORST"],
            "date": [date(2024, 1, 16)] * 4,
            "close": [110.0, 105.0, 95.0, 90.0],
            "return": [10.0, 5.0, -5.0, -10.0],  # BEST/GOOD gainers, BAD/WORST losers
            "vol": [0.08, 0.06, 0.04, 0.09],  # BEST/WORST most volatile
        })

        result = generate_signals(df_ranked)

        # Rule 1: buy_candidates = intersection of top gainers and top volatile
        # Top 2 gainers: BEST (10%), GOOD (5%)
        # Top 2 volatile: WORST (0.09), BEST (0.08)
        # Intersection: BEST (only one in both)
        buy = result["buy_candidates"]
        buy_tickers = set(buy["ticker"].unique())
        assert "BEST" in buy_tickers  # In both top gainers and top volatile
        assert "GOOD" not in buy_tickers  # Not in top volatile
        assert "WORST" not in buy_tickers  # Not a gainer

        # Rule 2: sell_candidates = top losers by volatility
        # Top 2 losers: WORST (-10%), BAD (-5%)
        # Among losers, top by vol: WORST (0.09), BAD (0.04)
        sell = result["sell_candidates"]
        sell_tickers = sell["ticker"].tolist()
        assert "WORST" in sell_tickers  # Highest vol among losers
        assert "BAD" in sell_tickers  # Second highest vol among losers
        # Should be sorted by vol descending
        if len(sell) > 1:
            assert sell.iloc[0]["vol"] >= sell.iloc[1]["vol"]

