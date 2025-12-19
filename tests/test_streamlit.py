"""Tests for Streamlit app and recommender module."""

import pytest
import pandas as pd
from datetime import date
from pathlib import Path

from nasdaq_scanner.core.recommender import (
    generate_recommendations,
    get_default_buy_rules,
    get_default_sell_rules,
    format_reasons,
)


class TestRecommender:
    """Tests for recommender module."""

    def test_get_default_buy_rules(self) -> None:
        """Test default buy rules are returned."""
        rules = get_default_buy_rules()
        assert len(rules) > 0
        assert all('name' in rule for rule in rules)
        assert all('condition' in rule for rule in rules)
        assert all('action' in rule for rule in rules)
        assert all(rule['action'] == 'buy' for rule in rules)

    def test_get_default_sell_rules(self) -> None:
        """Test default sell rules are returned."""
        rules = get_default_sell_rules()
        assert len(rules) > 0
        assert all('name' in rule for rule in rules)
        assert all('condition' in rule for rule in rules)
        assert all('action' in rule for rule in rules)
        assert all(rule['action'] in ['sell', 'watch'] for rule in rules)

    def test_generate_recommendations_basic(self) -> None:
        """Test basic recommendation generation."""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT', 'TSLA', 'GOOGL'],
            'return_pct': [6.0, 3.0, -6.0, 1.0],
            'vol_pct': [3.0, 2.0, 6.0, 1.5],
            'Open': [100.0, 200.0, 300.0, 150.0],
            'Close': [106.0, 206.0, 282.0, 151.5],
        })

        results = generate_recommendations(df, max_recommendations=10)

        assert 'buy' in results
        assert 'sell' in results
        assert 'buy_rules' in results
        assert 'sell_rules' in results
        assert isinstance(results['buy'], pd.DataFrame)
        assert isinstance(results['sell'], pd.DataFrame)

    def test_generate_recommendations_buy_signals(self) -> None:
        """Test buy recommendations are generated for high return stocks."""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT'],
            'return_pct': [6.0, 4.0],  # Both should trigger buy signals
            'vol_pct': [3.0, 2.0],
            'Open': [100.0, 200.0],
            'Close': [106.0, 208.0],
        })

        results = generate_recommendations(df, max_recommendations=10)

        assert len(results['buy']) > 0
        assert 'signal' in results['buy'].columns
        assert all(results['buy']['signal'] == 'buy')

    def test_generate_recommendations_sell_signals(self) -> None:
        """Test sell recommendations are generated for declining stocks."""
        df = pd.DataFrame({
            'symbol': ['TSLA', 'NVDA'],
            'return_pct': [-6.0, -4.0],  # Both should trigger sell/watch signals
            'vol_pct': [6.0, 5.0],
            'Open': [300.0, 400.0],
            'Close': [282.0, 384.0],
        })

        results = generate_recommendations(df, max_recommendations=10)

        assert len(results['sell']) > 0
        assert 'signal' in results['sell'].columns
        assert all(results['sell']['signal'].isin(['sell', 'watch']))

    def test_generate_recommendations_max_limit(self) -> None:
        """Test max_recommendations limit is respected."""
        # Create many high return stocks
        symbols = [f'STOCK{i}' for i in range(20)]
        df = pd.DataFrame({
            'symbol': symbols,
            'return_pct': [6.0] * 20,  # All should trigger buy
            'vol_pct': [3.0] * 20,
            'Open': [100.0] * 20,
            'Close': [106.0] * 20,
        })

        results = generate_recommendations(df, max_recommendations=5)

        assert len(results['buy']) <= 5

    def test_generate_recommendations_empty_input(self) -> None:
        """Test recommendations with empty DataFrame."""
        df = pd.DataFrame(columns=['symbol', 'return_pct', 'vol_pct'])

        results = generate_recommendations(df, max_recommendations=10)

        assert len(results['buy']) == 0
        assert len(results['sell']) == 0

    def test_format_reasons(self) -> None:
        """Test reason formatting."""
        rules = [
            {'name': 'rule1', 'description': 'High return'},
            {'name': 'rule2', 'description': 'High volatility'},
        ]

        reasons = ['rule1', 'rule2']
        formatted = format_reasons(reasons, rules)
        assert 'High return' in formatted
        assert 'High volatility' in formatted

    def test_format_reasons_empty(self) -> None:
        """Test formatting empty reasons."""
        rules = []
        reasons = []
        formatted = format_reasons(reasons, rules)
        assert formatted == 'No specific reason'

    def test_generate_recommendations_custom_rules(self) -> None:
        """Test recommendations with custom rules."""
        df = pd.DataFrame({
            'symbol': ['AAPL'],
            'return_pct': [10.0],
            'vol_pct': [5.0],
            'Open': [100.0],
            'Close': [110.0],
        })

        custom_buy_rules = [
            {
                'name': 'very_high_return',
                'condition': lambda row: row.get('return_pct', 0) > 8.0,
                'action': 'buy',
                'description': 'Very high return (>8%)'
            }
        ]

        results = generate_recommendations(
            df,
            buy_rules=custom_buy_rules,
            max_recommendations=10
        )

        assert len(results['buy']) > 0
        assert results['buy_rules'] == custom_buy_rules


class TestStreamlitIntegration:
    """Tests for Streamlit app integration."""

    def test_run_analysis_returns_results(self) -> None:
        """Test that run_analysis can return results for Streamlit."""
        from nasdaq_scanner.cli import run_analysis
        import tempfile
        import os

        # Create temporary universe file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('symbol\nAAPL\nMSFT\n')
            temp_path = f.name

        try:
            # This will make actual API calls, so we skip if yfinance not available
            try:
                results = run_analysis(
                    analysis_date=date(2024, 1, 15),
                    universe_path=temp_path,
                    n=5,
                    output_path=None,
                    export_csv=False,
                    return_results=True,
                )

                # If we get here, check structure
                if results is not None:
                    assert 'top_movers' in results
                    assert 'bottom_movers' in results
                    assert 'volatile_movers' in results
                    assert 'analysis_df' in results
                    assert 'analysis_date' in results
                    assert 'stats' in results
            except ImportError:
                pytest.skip("yfinance not available")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

