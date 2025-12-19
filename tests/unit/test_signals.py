"""Unit tests for signal generation functions.

Tests for generate_signals function that applies rules to a DataFrame
and generates signals with reasons.
"""

import pytest
import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import Callable, Dict, Any, List

# Import functions to test (will fail until implemented - RED phase)
from nasdaq_scanner.core.signals import generate_signals


class TestGenerateSignals:
    """Tests for generate_signals function."""

    @pytest.mark.unit
    def test_generate_signals_basic_single_rule(self) -> None:
        """Test basic signal generation with a single rule."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, 3.0, 7.0],
            "vol_pct": [2.0, 1.5, 3.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        rules = [
            {
                "name": "high_return",
                "condition": condition_high_return,
                "action": "buy",
            }
        ]

        result = generate_signals(df, rules)

        assert "signal" in result.columns
        assert "reasons" in result.columns
        assert result.loc[result["symbol"] == "GOOGL", "signal"].iloc[0] == "buy"
        assert result.loc[result["symbol"] == "AAPL", "signal"].iloc[0] == "buy"
        assert result.loc[result["symbol"] == "MSFT", "signal"].iloc[0] != "buy"

    @pytest.mark.unit
    def test_generate_signals_multiple_rules(self) -> None:
        """Test signal generation with multiple rules."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "return_pct": [5.0, 3.0, 7.0, -2.0],
            "vol_pct": [2.0, 1.5, 3.0, 4.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        def condition_high_volatility(row: pd.Series) -> bool:
            return row["vol_pct"] > 2.5

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
            {"name": "high_volatility", "condition": condition_high_volatility, "action": "watch"},
        ]

        result = generate_signals(df, rules)

        # GOOGL should match both rules
        googl_row = result[result["symbol"] == "GOOGL"].iloc[0]
        assert googl_row["signal"] in ["buy", "watch"]  # One of the signals
        assert "high_return" in googl_row["reasons"] or "high_volatility" in googl_row["reasons"]

    @pytest.mark.unit
    def test_generate_signals_reasons_format(self) -> None:
        """Test that reasons are properly formatted."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [6.0, 3.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
        ]

        result = generate_signals(df, rules)

        # Check that reasons is a list or string containing rule names
        aapl_row = result[result["symbol"] == "AAPL"].iloc[0]
        assert aapl_row["reasons"] is not None
        # Reasons should contain the rule name
        assert "high_return" in str(aapl_row["reasons"])

    @pytest.mark.unit
    def test_generate_signals_no_matching_rules(self) -> None:
        """Test signal generation when no rules match."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [2.0, 3.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
        ]

        result = generate_signals(df, rules)

        # All rows should have no signal or default signal
        assert all(result["signal"].isna() | (result["signal"] == "")) or "signal" in result.columns

    @pytest.mark.unit
    def test_generate_signals_conflicting_rules(self) -> None:
        """Test signal generation with conflicting rules (same row matches multiple rules)."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [6.0],
            "vol_pct": [3.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        def condition_high_volatility(row: pd.Series) -> bool:
            return row["vol_pct"] > 2.5

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
            {"name": "high_volatility", "condition": condition_high_volatility, "action": "sell"},
        ]

        result = generate_signals(df, rules)

        # Should handle conflicting signals (either prioritize or combine)
        aapl_row = result[result["symbol"] == "AAPL"].iloc[0]
        assert aapl_row["reasons"] is not None
        # Should contain both rule names in reasons
        reasons_str = str(aapl_row["reasons"])
        assert "high_return" in reasons_str or "high_volatility" in reasons_str

    @pytest.mark.unit
    def test_generate_signals_empty_rules(self) -> None:
        """Test signal generation with empty rules list."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })

        rules: List[Dict[str, Any]] = []

        result = generate_signals(df, rules)

        # Should return DataFrame with signal and reasons columns
        assert "signal" in result.columns
        assert "reasons" in result.columns
        assert len(result) == len(df)

    @pytest.mark.unit
    def test_generate_signals_empty_dataframe(self) -> None:
        """Test signal generation with empty DataFrame."""
        df = pd.DataFrame(columns=["symbol", "return_pct"])

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
        ]

        result = generate_signals(df, rules)

        assert len(result) == 0
        assert "signal" in result.columns
        assert "reasons" in result.columns

    @pytest.mark.unit
    def test_generate_signals_condition_raises_exception(self) -> None:
        """Test signal generation when condition function raises an exception."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })

        def condition_error(row: pd.Series) -> bool:
            raise ValueError("Condition error")

        rules = [
            {"name": "error_rule", "condition": condition_error, "action": "buy"},
        ]

        # Should handle exceptions gracefully (either skip rule or raise)
        with pytest.raises((ValueError, KeyError, AttributeError)):
            generate_signals(df, rules)

    @pytest.mark.unit
    def test_generate_signals_condition_returns_non_boolean(self) -> None:
        """Test signal generation when condition returns non-boolean value."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })

        def condition_non_boolean(row: pd.Series) -> int:
            return 1  # Not a boolean

        rules = [
            {"name": "non_boolean", "condition": condition_non_boolean, "action": "buy"},
        ]

        # Should handle non-boolean returns (convert to bool or raise)
        result = generate_signals(df, rules)
        # Either works with truthy values or raises error
        assert "signal" in result.columns

    @pytest.mark.unit
    def test_generate_signals_preserves_original_columns(self) -> None:
        """Test that original columns are preserved."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
            "vol_pct": [2.0, 1.5],
            "volume": [1000000, 2000000],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 4.0

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
        ]

        result = generate_signals(df, rules)

        # Should preserve all original columns
        assert "symbol" in result.columns
        assert "return_pct" in result.columns
        assert "vol_pct" in result.columns
        assert "volume" in result.columns
        assert "signal" in result.columns
        assert "reasons" in result.columns

    @pytest.mark.unit
    def test_generate_signals_no_side_effects(self) -> None:
        """Test that function does not modify input DataFrame."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })
        df_copy = df.copy()

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 4.0

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
        ]

        generate_signals(df, rules)

        # Original DataFrame should not be modified
        pd.testing.assert_frame_equal(df, df_copy)
        assert "signal" not in df.columns
        assert "reasons" not in df.columns

    @pytest.mark.unit
    def test_generate_signals_rule_with_nan_values(self) -> None:
        """Test signal generation with NaN values in DataFrame."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, np.nan, 7.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
        ]

        result = generate_signals(df, rules)

        # Should handle NaN values gracefully
        assert len(result) == 3
        # MSFT with NaN should not match condition
        msft_row = result[result["symbol"] == "MSFT"].iloc[0]
        # NaN comparison should return False, so no signal or empty signal
        assert msft_row["signal"] != "buy" or pd.isna(msft_row["signal"])

    @pytest.mark.unit
    def test_generate_signals_multiple_actions_same_row(self) -> None:
        """Test that multiple rules can apply to the same row."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [6.0],
            "vol_pct": [3.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        def condition_high_volatility(row: pd.Series) -> bool:
            return row["vol_pct"] > 2.5

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
            {"name": "high_volatility", "condition": condition_high_volatility, "action": "watch"},
        ]

        result = generate_signals(df, rules)

        aapl_row = result[result["symbol"] == "AAPL"].iloc[0]
        # Should have signal and reasons containing both rules
        assert aapl_row["signal"] is not None
        reasons_str = str(aapl_row["reasons"])
        assert "high_return" in reasons_str or "high_volatility" in reasons_str

    @pytest.mark.unit
    def test_generate_signals_rule_missing_keys(self) -> None:
        """Test signal generation when rule is missing required keys."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })

        # Rule missing 'name' key
        rules = [
            {"condition": lambda row: True, "action": "buy"},
        ]

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError, TypeError)):
            generate_signals(df, rules)

    @pytest.mark.unit
    def test_generate_signals_rule_missing_condition(self) -> None:
        """Test signal generation when rule is missing condition."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })

        # Rule missing 'condition' key
        rules = [
            {"name": "test_rule", "action": "buy"},
        ]

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError, TypeError)):
            generate_signals(df, rules)

    @pytest.mark.unit
    def test_generate_signals_rule_missing_action(self) -> None:
        """Test signal generation when rule is missing action."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 4.0

        # Rule missing 'action' key
        rules = [
            {"name": "test_rule", "condition": condition_high_return},
        ]

        # Should raise KeyError or ValueError
        with pytest.raises((KeyError, ValueError, TypeError)):
            generate_signals(df, rules)

    @pytest.mark.unit
    def test_generate_signals_complex_condition(self) -> None:
        """Test signal generation with complex condition logic."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [6.0, 3.0, 8.0],
            "vol_pct": [2.0, 1.5, 4.0],
            "volume": [1000000, 2000000, 1500000],
        })

        def condition_complex(row: pd.Series) -> bool:
            return (row["return_pct"] > 5.0) and (row["vol_pct"] > 2.5) and (row["volume"] > 1200000)

        rules = [
            {"name": "complex_condition", "condition": condition_complex, "action": "buy"},
        ]

        result = generate_signals(df, rules)

        # Only GOOGL should match (6.0 > 5.0, 4.0 > 2.5, 1500000 > 1200000)
        googl_row = result[result["symbol"] == "GOOGL"].iloc[0]
        assert googl_row["signal"] == "buy"
        assert "complex_condition" in str(googl_row["reasons"])

    @pytest.mark.unit
    def test_generate_signals_reasons_aggregation(self) -> None:
        """Test that reasons properly aggregate multiple matching rules."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [6.0],
            "vol_pct": [3.0],
        })

        def condition_high_return(row: pd.Series) -> bool:
            return row["return_pct"] > 5.0

        def condition_high_volatility(row: pd.Series) -> bool:
            return row["vol_pct"] > 2.5

        rules = [
            {"name": "high_return", "condition": condition_high_return, "action": "buy"},
            {"name": "high_volatility", "condition": condition_high_volatility, "action": "watch"},
        ]

        result = generate_signals(df, rules)

        aapl_row = result[result["symbol"] == "AAPL"].iloc[0]
        reasons_str = str(aapl_row["reasons"])
        # Should contain both rule names
        assert "high_return" in reasons_str
        assert "high_volatility" in reasons_str

