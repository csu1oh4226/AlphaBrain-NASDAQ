"""Unit tests for ranking functions.

Tests for top_n and bottom_n functions that return top/bottom N rows
from a DataFrame sorted by a specified column, with tie-breaking rules.
"""

import pytest
import pandas as pd
import numpy as np
from pandas import DataFrame

# Import functions to test (will fail until implemented - RED phase)
from nasdaq_scanner.core.ranking import top_n, bottom_n


class TestTopN:
    """Tests for top_n function."""

    @pytest.mark.unit
    def test_top_n_basic(self) -> None:
        """Test basic top N selection."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "return_pct": [5.0, 3.0, 7.0, 2.0, 6.0],
        })

        result = top_n(df, col="return_pct", n=3)

        assert len(result) == 3
        assert result["return_pct"].iloc[0] == 7.0  # GOOGL
        assert result["return_pct"].iloc[1] == 6.0  # TSLA
        assert result["return_pct"].iloc[2] == 5.0  # AAPL

    @pytest.mark.unit
    def test_top_n_with_ties_stable_sort(self) -> None:
        """Test top N with ties uses stable sort (preserves original order)."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "return_pct": [5.0, 5.0, 7.0, 5.0, 6.0],  # Three 5.0 values
        })

        result = top_n(df, col="return_pct", n=4)

        assert len(result) == 4
        # Should preserve original order for ties (stable sort)
        # Then sort by symbol alphabetically as tie-breaker
        assert result["return_pct"].iloc[0] == 7.0  # GOOGL (highest)
        assert result["return_pct"].iloc[1] == 6.0  # TSLA
        # For ties at 5.0, should be sorted by symbol alphabetically
        assert result["return_pct"].iloc[2] == 5.0
        assert result["return_pct"].iloc[3] == 5.0
        # Check that symbols are in alphabetical order for ties
        tied_symbols = result[result["return_pct"] == 5.0]["symbol"].tolist()
        assert tied_symbols == sorted(tied_symbols)

    @pytest.mark.unit
    def test_top_n_tie_breaker_alphabetical(self) -> None:
        """Test that ties are broken by symbol alphabetical order."""
        df = pd.DataFrame({
            "symbol": ["Z", "A", "M", "B"],
            "return_pct": [10.0, 10.0, 10.0, 10.0],  # All same value
        })

        result = top_n(df, col="return_pct", n=4)

        assert len(result) == 4
        # All have same return_pct, so should be sorted by symbol alphabetically
        assert result["symbol"].tolist() == ["A", "B", "M", "Z"]

    @pytest.mark.unit
    def test_top_n_n_larger_than_dataframe(self) -> None:
        """Test top N when n is larger than DataFrame size."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, 3.0, 7.0],
        })

        result = top_n(df, col="return_pct", n=10)

        # Should return all rows, sorted
        assert len(result) == 3
        assert result["return_pct"].iloc[0] == 7.0
        assert result["return_pct"].iloc[1] == 5.0
        assert result["return_pct"].iloc[2] == 3.0

    @pytest.mark.unit
    def test_top_n_n_equals_zero(self) -> None:
        """Test top N when n is zero."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })

        result = top_n(df, col="return_pct", n=0)

        assert len(result) == 0
        assert list(result.columns) == list(df.columns)

    @pytest.mark.unit
    def test_top_n_empty_dataframe(self) -> None:
        """Test top N with empty DataFrame."""
        df = pd.DataFrame(columns=["symbol", "return_pct"])

        result = top_n(df, col="return_pct", n=5)

        assert len(result) == 0
        assert list(result.columns) == list(df.columns)

    @pytest.mark.unit
    def test_top_n_nan_values(self) -> None:
        """Test top N with NaN values in the column."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "return_pct": [5.0, np.nan, 7.0, np.nan],
        })

        result = top_n(df, col="return_pct", n=2)

        # NaN values should be sorted to the end (or excluded)
        assert len(result) == 2
        assert result["return_pct"].iloc[0] == 7.0
        assert result["return_pct"].iloc[1] == 5.0
        # NaN values should not be in top N
        assert not result["return_pct"].isna().any()

    @pytest.mark.unit
    def test_top_n_missing_column(self) -> None:
        """Test top N when specified column is missing."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })

        with pytest.raises((KeyError, ValueError)):
            top_n(df, col="nonexistent_col", n=1)

    @pytest.mark.unit
    def test_top_n_preserves_original_columns(self) -> None:
        """Test that all original columns are preserved."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, 3.0, 7.0],
            "vol_pct": [2.0, 1.5, 3.0],
            "volume": [1000000, 2000000, 1500000],
        })

        result = top_n(df, col="return_pct", n=2)

        assert "symbol" in result.columns
        assert "return_pct" in result.columns
        assert "vol_pct" in result.columns
        assert "volume" in result.columns

    @pytest.mark.unit
    def test_top_n_no_side_effects(self) -> None:
        """Test that function does not modify input DataFrame."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })
        df_copy = df.copy()

        top_n(df, col="return_pct", n=1)

        # Original DataFrame should not be modified
        pd.testing.assert_frame_equal(df, df_copy)

    @pytest.mark.unit
    def test_top_n_all_negative_values(self) -> None:
        """Test top N with all negative values."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [-5.0, -3.0, -7.0],
        })

        result = top_n(df, col="return_pct", n=2)

        # Top N should be the least negative (highest values)
        assert len(result) == 2
        assert result["return_pct"].iloc[0] == -3.0  # MSFT (highest)
        assert result["return_pct"].iloc[1] == -5.0  # AAPL


class TestBottomN:
    """Tests for bottom_n function."""

    @pytest.mark.unit
    def test_bottom_n_basic(self) -> None:
        """Test basic bottom N selection."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "return_pct": [5.0, 3.0, 7.0, 2.0, 6.0],
        })

        result = bottom_n(df, col="return_pct", n=3)

        assert len(result) == 3
        assert result["return_pct"].iloc[0] == 2.0  # AMZN (lowest)
        assert result["return_pct"].iloc[1] == 3.0  # MSFT
        assert result["return_pct"].iloc[2] == 5.0  # AAPL

    @pytest.mark.unit
    def test_bottom_n_with_ties_stable_sort(self) -> None:
        """Test bottom N with ties uses stable sort."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "return_pct": [5.0, 5.0, 7.0, 5.0, 6.0],  # Three 5.0 values
        })

        result = bottom_n(df, col="return_pct", n=4)

        assert len(result) == 4
        # Should get lowest values first
        assert result["return_pct"].iloc[0] == 5.0
        assert result["return_pct"].iloc[1] == 5.0
        assert result["return_pct"].iloc[2] == 5.0
        assert result["return_pct"].iloc[3] == 6.0
        # For ties at 5.0, should be sorted by symbol alphabetically
        tied_symbols = result[result["return_pct"] == 5.0]["symbol"].tolist()
        assert tied_symbols == sorted(tied_symbols)

    @pytest.mark.unit
    def test_bottom_n_tie_breaker_alphabetical(self) -> None:
        """Test that ties are broken by symbol alphabetical order."""
        df = pd.DataFrame({
            "symbol": ["Z", "A", "M", "B"],
            "return_pct": [10.0, 10.0, 10.0, 10.0],  # All same value
        })

        result = bottom_n(df, col="return_pct", n=4)

        assert len(result) == 4
        # All have same return_pct, so should be sorted by symbol alphabetically
        assert result["symbol"].tolist() == ["A", "B", "M", "Z"]

    @pytest.mark.unit
    def test_bottom_n_n_larger_than_dataframe(self) -> None:
        """Test bottom N when n is larger than DataFrame size."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, 3.0, 7.0],
        })

        result = bottom_n(df, col="return_pct", n=10)

        # Should return all rows, sorted ascending
        assert len(result) == 3
        assert result["return_pct"].iloc[0] == 3.0
        assert result["return_pct"].iloc[1] == 5.0
        assert result["return_pct"].iloc[2] == 7.0

    @pytest.mark.unit
    def test_bottom_n_n_equals_zero(self) -> None:
        """Test bottom N when n is zero."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })

        result = bottom_n(df, col="return_pct", n=0)

        assert len(result) == 0
        assert list(result.columns) == list(df.columns)

    @pytest.mark.unit
    def test_bottom_n_empty_dataframe(self) -> None:
        """Test bottom N with empty DataFrame."""
        df = pd.DataFrame(columns=["symbol", "return_pct"])

        result = bottom_n(df, col="return_pct", n=5)

        assert len(result) == 0
        assert list(result.columns) == list(df.columns)

    @pytest.mark.unit
    def test_bottom_n_nan_values(self) -> None:
        """Test bottom N with NaN values in the column."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "return_pct": [5.0, np.nan, 7.0, np.nan],
        })

        result = bottom_n(df, col="return_pct", n=2)

        # NaN values should be excluded from bottom N
        assert len(result) == 2
        assert result["return_pct"].iloc[0] == 5.0
        assert result["return_pct"].iloc[1] == 7.0
        # NaN values should not be in bottom N
        assert not result["return_pct"].isna().any()

    @pytest.mark.unit
    def test_bottom_n_missing_column(self) -> None:
        """Test bottom N when specified column is missing."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })

        with pytest.raises((KeyError, ValueError)):
            bottom_n(df, col="nonexistent_col", n=1)

    @pytest.mark.unit
    def test_bottom_n_preserves_original_columns(self) -> None:
        """Test that all original columns are preserved."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, 3.0, 7.0],
            "vol_pct": [2.0, 1.5, 3.0],
            "volume": [1000000, 2000000, 1500000],
        })

        result = bottom_n(df, col="return_pct", n=2)

        assert "symbol" in result.columns
        assert "return_pct" in result.columns
        assert "vol_pct" in result.columns
        assert "volume" in result.columns

    @pytest.mark.unit
    def test_bottom_n_no_side_effects(self) -> None:
        """Test that function does not modify input DataFrame."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })
        df_copy = df.copy()

        bottom_n(df, col="return_pct", n=1)

        # Original DataFrame should not be modified
        pd.testing.assert_frame_equal(df, df_copy)

    @pytest.mark.unit
    def test_bottom_n_all_negative_values(self) -> None:
        """Test bottom N with all negative values."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [-5.0, -3.0, -7.0],
        })

        result = bottom_n(df, col="return_pct", n=2)

        # Bottom N should be the most negative (lowest values)
        assert len(result) == 2
        assert result["return_pct"].iloc[0] == -7.0  # GOOGL (lowest)
        assert result["return_pct"].iloc[1] == -5.0  # AAPL


class TestRankingTieBreaking:
    """Tests for tie-breaking behavior in ranking functions."""

    @pytest.mark.unit
    def test_tie_breaking_complex_case(self) -> None:
        """Test tie-breaking with multiple groups of ties."""
        df = pd.DataFrame({
            "symbol": ["Z", "A", "M", "B", "C", "Y"],
            "return_pct": [10.0, 10.0, 5.0, 10.0, 5.0, 10.0],
        })

        result_top = top_n(df, col="return_pct", n=4)
        result_bottom = bottom_n(df, col="return_pct", n=4)

        # Top N: Should have 10.0 values first, sorted by symbol
        top_10_values = result_top[result_top["return_pct"] == 10.0]
        assert len(top_10_values) == 4
        assert top_10_values["symbol"].tolist() == sorted(top_10_values["symbol"].tolist())

        # Bottom N: Should have 5.0 values first, sorted by symbol
        bottom_5_values = result_bottom[result_bottom["return_pct"] == 5.0]
        assert len(bottom_5_values) == 2
        assert bottom_5_values["symbol"].tolist() == sorted(bottom_5_values["symbol"].tolist())

    @pytest.mark.unit
    def test_tie_breaking_case_sensitivity(self) -> None:
        """Test that symbol tie-breaking is case-sensitive (alphabetical order)."""
        df = pd.DataFrame({
            "symbol": ["a", "A", "b", "B", "z", "Z"],
            "return_pct": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
        })

        result = top_n(df, col="return_pct", n=6)

        # In ASCII/Unicode order: 'A' < 'B' < 'Z' < 'a' < 'b' < 'z'
        assert result["symbol"].tolist() == ["A", "B", "Z", "a", "b", "z"]

    @pytest.mark.unit
    def test_tie_breaking_with_mixed_data_types(self) -> None:
        """Test tie-breaking when symbol column has mixed types (should handle gracefully)."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, 5.0, 5.0],
        })

        result = top_n(df, col="return_pct", n=3)

        # Should sort by symbol alphabetically
        assert result["symbol"].tolist() == sorted(["AAPL", "MSFT", "GOOGL"])

