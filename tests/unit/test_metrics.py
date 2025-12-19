"""Unit tests for metrics calculation functions.

Tests for calc_return_pct and calc_intraday_vol_pct functions.
These are pure functions that calculate return percentage and intraday volatility
from OHLC (Open, High, Low, Close) DataFrame columns.
"""

import pytest
import pandas as pd
import numpy as np
from pandas import DataFrame

# Import functions to test (will fail until implemented - RED phase)
from nasdaq_scanner.core.metrics import calc_return_pct, calc_intraday_vol_pct


class TestCalcReturnPct:
    """Tests for calc_return_pct function."""

    @pytest.mark.unit
    def test_calc_return_pct_basic(self) -> None:
        """Test basic return percentage calculation."""
        # Given: DataFrame with OHLC columns
        df = pd.DataFrame({
            "Open": [100.0, 50.0, 200.0],
            "High": [105.0, 55.0, 210.0],
            "Low": [99.0, 48.0, 195.0],
            "Close": [104.0, 52.0, 205.0],
        })

        # When: Calculate return percentage
        result = calc_return_pct(df)

        # Then: Should add return_pct column with correct values
        assert "return_pct" in result.columns
        assert result["return_pct"].iloc[0] == pytest.approx(4.0)  # (104-100)/100 * 100
        assert result["return_pct"].iloc[1] == pytest.approx(4.0)  # (52-50)/50 * 100
        assert result["return_pct"].iloc[2] == pytest.approx(2.5)  # (205-200)/200 * 100

    @pytest.mark.unit
    def test_calc_return_pct_negative_return(self) -> None:
        """Test return percentage calculation with negative returns."""
        df = pd.DataFrame({
            "Open": [100.0, 50.0],
            "High": [102.0, 52.0],
            "Low": [95.0, 45.0],
            "Close": [95.0, 45.0],
        })

        result = calc_return_pct(df)

        assert result["return_pct"].iloc[0] == pytest.approx(-5.0)  # (95-100)/100 * 100
        assert result["return_pct"].iloc[1] == pytest.approx(-10.0)  # (45-50)/50 * 100

    @pytest.mark.unit
    def test_calc_return_pct_zero_open(self) -> None:
        """Test return percentage calculation when Open is zero."""
        df = pd.DataFrame({
            "Open": [0.0, 100.0],
            "High": [5.0, 105.0],
            "Low": [0.0, 99.0],
            "Close": [5.0, 104.0],
        })

        result = calc_return_pct(df)

        # Should handle zero division gracefully (NaN or inf)
        assert pd.isna(result["return_pct"].iloc[0]) or np.isinf(result["return_pct"].iloc[0])
        assert result["return_pct"].iloc[1] == pytest.approx(4.0)

    @pytest.mark.unit
    def test_calc_return_pct_nan_values(self) -> None:
        """Test return percentage calculation with NaN values."""
        df = pd.DataFrame({
            "Open": [100.0, np.nan, 50.0],
            "High": [105.0, 55.0, np.nan],
            "Low": [99.0, 48.0, 45.0],
            "Close": [np.nan, 52.0, 50.0],
        })

        result = calc_return_pct(df)

        # Should handle NaN gracefully
        assert pd.isna(result["return_pct"].iloc[0])  # Close is NaN
        assert pd.isna(result["return_pct"].iloc[1])  # Open is NaN
        assert pd.isna(result["return_pct"].iloc[2])  # High is NaN (but should still calculate if Open/Close exist)

    @pytest.mark.unit
    def test_calc_return_pct_missing_open_column(self) -> None:
        """Test return percentage calculation when Open column is missing."""
        df = pd.DataFrame({
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
        })

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError)):
            calc_return_pct(df)

    @pytest.mark.unit
    def test_calc_return_pct_missing_close_column(self) -> None:
        """Test return percentage calculation when Close column is missing."""
        df = pd.DataFrame({
            "Open": [100.0],
            "High": [105.0],
            "Low": [99.0],
        })

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError)):
            calc_return_pct(df)

    @pytest.mark.unit
    def test_calc_return_pct_empty_dataframe(self) -> None:
        """Test return percentage calculation with empty DataFrame."""
        df = pd.DataFrame(columns=["Open", "High", "Low", "Close"])

        result = calc_return_pct(df)

        # Should return empty DataFrame with return_pct column
        assert "return_pct" in result.columns
        assert len(result) == 0

    @pytest.mark.unit
    def test_calc_return_pct_preserves_original_columns(self) -> None:
        """Test that original columns are preserved."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "Open": [100.0, 50.0],
            "High": [105.0, 55.0],
            "Low": [99.0, 48.0],
            "Close": [104.0, 52.0],
            "Volume": [1000000, 2000000],
        })

        result = calc_return_pct(df)

        # Should preserve all original columns
        assert "symbol" in result.columns
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
        assert "return_pct" in result.columns

    @pytest.mark.unit
    def test_calc_return_pct_no_side_effects(self) -> None:
        """Test that function does not modify input DataFrame."""
        df = pd.DataFrame({
            "Open": [100.0],
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
        })
        df_copy = df.copy()

        calc_return_pct(df)

        # Original DataFrame should not be modified
        pd.testing.assert_frame_equal(df, df_copy)
        assert "return_pct" not in df.columns


class TestCalcIntradayVolPct:
    """Tests for calc_intraday_vol_pct function."""

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_basic(self) -> None:
        """Test basic intraday volatility percentage calculation."""
        df = pd.DataFrame({
            "Open": [100.0, 50.0, 200.0],
            "High": [105.0, 55.0, 210.0],
            "Low": [99.0, 48.0, 195.0],
            "Close": [104.0, 52.0, 205.0],
        })

        result = calc_intraday_vol_pct(df)

        assert "vol_pct" in result.columns
        assert result["vol_pct"].iloc[0] == pytest.approx(6.0)  # (105-99)/100 * 100
        assert result["vol_pct"].iloc[1] == pytest.approx(14.0)  # (55-48)/50 * 100
        assert result["vol_pct"].iloc[2] == pytest.approx(7.5)  # (210-195)/200 * 100

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_zero_range(self) -> None:
        """Test intraday volatility when High equals Low."""
        df = pd.DataFrame({
            "Open": [100.0, 50.0],
            "High": [100.0, 50.0],
            "Low": [100.0, 50.0],
            "Close": [100.0, 50.0],
        })

        result = calc_intraday_vol_pct(df)

        assert result["vol_pct"].iloc[0] == pytest.approx(0.0)
        assert result["vol_pct"].iloc[1] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_zero_open(self) -> None:
        """Test intraday volatility calculation when Open is zero."""
        df = pd.DataFrame({
            "Open": [0.0, 100.0],
            "High": [5.0, 105.0],
            "Low": [0.0, 99.0],
            "Close": [5.0, 104.0],
        })

        result = calc_intraday_vol_pct(df)

        # Should handle zero division gracefully (NaN or inf)
        assert pd.isna(result["vol_pct"].iloc[0]) or np.isinf(result["vol_pct"].iloc[0])
        assert result["vol_pct"].iloc[1] == pytest.approx(6.0)

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_nan_values(self) -> None:
        """Test intraday volatility calculation with NaN values."""
        df = pd.DataFrame({
            "Open": [100.0, np.nan, 50.0],
            "High": [np.nan, 55.0, 55.0],
            "Low": [99.0, np.nan, 45.0],
            "Close": [104.0, 52.0, 50.0],
        })

        result = calc_intraday_vol_pct(df)

        # Should handle NaN gracefully
        assert pd.isna(result["vol_pct"].iloc[0])  # High is NaN
        assert pd.isna(result["vol_pct"].iloc[1])  # Open is NaN
        assert pd.isna(result["vol_pct"].iloc[2])  # Low is NaN (but should still calculate if Open/High exist)

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_missing_open_column(self) -> None:
        """Test intraday volatility when Open column is missing."""
        df = pd.DataFrame({
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
        })

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError)):
            calc_intraday_vol_pct(df)

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_missing_high_column(self) -> None:
        """Test intraday volatility when High column is missing."""
        df = pd.DataFrame({
            "Open": [100.0],
            "Low": [99.0],
            "Close": [104.0],
        })

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError)):
            calc_intraday_vol_pct(df)

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_missing_low_column(self) -> None:
        """Test intraday volatility when Low column is missing."""
        df = pd.DataFrame({
            "Open": [100.0],
            "High": [105.0],
            "Close": [104.0],
        })

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError)):
            calc_intraday_vol_pct(df)

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_empty_dataframe(self) -> None:
        """Test intraday volatility calculation with empty DataFrame."""
        df = pd.DataFrame(columns=["Open", "High", "Low", "Close"])

        result = calc_intraday_vol_pct(df)

        # Should return empty DataFrame with vol_pct column
        assert "vol_pct" in result.columns
        assert len(result) == 0

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_preserves_original_columns(self) -> None:
        """Test that original columns are preserved."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "Open": [100.0, 50.0],
            "High": [105.0, 55.0],
            "Low": [99.0, 48.0],
            "Close": [104.0, 52.0],
            "Volume": [1000000, 2000000],
        })

        result = calc_intraday_vol_pct(df)

        # Should preserve all original columns
        assert "symbol" in result.columns
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
        assert "vol_pct" in result.columns

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_no_side_effects(self) -> None:
        """Test that function does not modify input DataFrame."""
        df = pd.DataFrame({
            "Open": [100.0],
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
        })
        df_copy = df.copy()

        calc_intraday_vol_pct(df)

        # Original DataFrame should not be modified
        pd.testing.assert_frame_equal(df, df_copy)
        assert "vol_pct" not in df.columns

    @pytest.mark.unit
    def test_calc_intraday_vol_pct_high_lower_than_low(self) -> None:
        """Test intraday volatility when High < Low (invalid data)."""
        df = pd.DataFrame({
            "Open": [100.0],
            "High": [99.0],  # Lower than Low
            "Low": [105.0],  # Higher than High
            "Close": [104.0],
        })

        result = calc_intraday_vol_pct(df)

        # Should handle invalid data (negative range)
        # Could return negative value or NaN depending on implementation
        assert result["vol_pct"].iloc[0] < 0 or pd.isna(result["vol_pct"].iloc[0])


class TestMetricsIntegration:
    """Integration tests for both metrics functions."""

    @pytest.mark.unit
    def test_both_metrics_together(self) -> None:
        """Test both metrics calculated on the same DataFrame."""
        df = pd.DataFrame({
            "Open": [100.0, 50.0],
            "High": [105.0, 55.0],
            "Low": [99.0, 48.0],
            "Close": [104.0, 52.0],
        })

        result = calc_return_pct(df)
        result = calc_intraday_vol_pct(result)

        # Should have both columns
        assert "return_pct" in result.columns
        assert "vol_pct" in result.columns
        assert result["return_pct"].iloc[0] == pytest.approx(4.0)
        assert result["vol_pct"].iloc[0] == pytest.approx(6.0)

    @pytest.mark.unit
    def test_metrics_with_realistic_data(self) -> None:
        """Test metrics with realistic stock price data."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "Open": [150.0, 300.0, 2500.0],
            "High": [152.5, 305.0, 2520.0],
            "Low": [149.5, 298.0, 2490.0],
            "Close": [151.0, 302.0, 2510.0],
            "Volume": [50000000, 30000000, 2000000],
        })

        result = calc_return_pct(df)
        result = calc_intraday_vol_pct(result)

        # All symbols should have valid metrics
        assert len(result) == 3
        assert all(not pd.isna(result["return_pct"]))
        assert all(not pd.isna(result["vol_pct"]))
        assert all(result["vol_pct"] >= 0)  # Volatility should be non-negative

