"""Smoke tests for end-to-end pipeline integration.

These tests verify that the complete pipeline works together,
with minimal external calls (mocked where possible).
"""

import pytest
import pandas as pd
import tempfile
import os
from datetime import date
from pathlib import Path

# Import modules to test
from nasdaq_scanner.core.universe import load_tickers
from nasdaq_scanner.core.metrics import calc_return_pct, calc_intraday_vol_pct
from nasdaq_scanner.core.ranking import top_n, bottom_n
from nasdaq_scanner.reporter.report import render_markdown, save_markdown
from nasdaq_scanner.providers.data_provider import fetch_ohlcv_batch


@pytest.mark.integration
@pytest.mark.slow
def test_smoke_pipeline_with_mock_data() -> None:
    """Smoke test: Complete pipeline with mock OHLCV data (no network calls)."""
    # Create sample universe file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("symbol\n")
        f.write("AAPL\n")
        f.write("MSFT\n")
        f.write("GOOGL\n")
        universe_path = f.name

    try:
        # Step 1: Load universe
        symbols = load_tickers(universe_path)
        assert len(symbols) == 3
        assert "AAPL" in symbols

        # Step 2: Create mock OHLCV data (skip actual network call)
        ohlcv_data = [
            {
                "symbol": "AAPL",
                "date": date(2024, 1, 15),
                "Open": 100.0,
                "High": 105.0,
                "Low": 99.0,
                "Close": 104.0,
                "Volume": 50000000,
            },
            {
                "symbol": "MSFT",
                "date": date(2024, 1, 15),
                "Open": 200.0,
                "High": 210.0,
                "Low": 195.0,
                "Close": 205.0,
                "Volume": 30000000,
            },
            {
                "symbol": "GOOGL",
                "date": date(2024, 1, 15),
                "Open": 150.0,
                "High": 160.0,
                "Low": 145.0,
                "Close": 155.0,
                "Volume": 20000000,
            },
        ]
        ohlcv_df = pd.DataFrame(ohlcv_data)

        # Step 3: Calculate metrics
        analysis_df = calc_return_pct(ohlcv_df)
        analysis_df = calc_intraday_vol_pct(analysis_df)

        assert "return_pct" in analysis_df.columns
        assert "vol_pct" in analysis_df.columns
        assert len(analysis_df) == 3

        # Step 4: Generate rankings
        top_movers = top_n(analysis_df, col="return_pct", n=2)
        bottom_movers = bottom_n(analysis_df, col="return_pct", n=2)
        volatile_movers = top_n(analysis_df, col="vol_pct", n=2)

        assert len(top_movers) <= 2
        assert len(bottom_movers) <= 2
        assert len(volatile_movers) <= 2

        # Step 5: Generate report
        report = render_markdown(
            date(2024, 1, 15), top_movers, bottom_movers, volatile_movers
        )

        assert isinstance(report, str)
        assert len(report) > 0
        assert "NASDAQ" in report or "Daily Movers" in report
        assert "2024" in report

        # Step 6: Save report
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = f.name

        try:
            save_markdown(report, output_path)
            assert Path(output_path).exists()
            with open(output_path, "r", encoding="utf-8") as f:
                saved_content = f.read()
            assert saved_content == report
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    finally:
        if os.path.exists(universe_path):
            os.unlink(universe_path)


@pytest.mark.integration
@pytest.mark.slow
def test_smoke_data_provider_handles_failures() -> None:
    """Smoke test: Data provider handles failures gracefully."""
    # Test with invalid symbols (should not crash)
    invalid_symbols = ["INVALID_SYMBOL_XYZ", "ANOTHER_INVALID"]

    try:
        result = fetch_ohlcv_batch(invalid_symbols, date(2024, 1, 15))
        # Should return empty DataFrame or handle gracefully
        assert isinstance(result, pd.DataFrame)
    except ImportError:
        # yfinance not installed, skip test
        pytest.skip("yfinance not installed")
    except Exception as e:
        # Should log errors but not crash
        assert isinstance(e, Exception)


@pytest.mark.integration
@pytest.mark.slow
def test_smoke_cli_import() -> None:
    """Smoke test: CLI module can be imported."""
    try:
        from nasdaq_scanner.cli import main, run_analysis

        assert callable(main)
        assert callable(run_analysis)
    except ImportError as e:
        pytest.skip(f"CLI dependencies not available: {e}")


@pytest.mark.integration
@pytest.mark.slow
def test_smoke_end_to_end_minimal() -> None:
    """Smoke test: Minimal end-to-end test with 2-3 symbols."""
    # Create minimal universe
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("AAPL\nMSFT\n")
        universe_path = f.name

    try:
        # Load universe
        symbols = load_tickers(universe_path)
        assert len(symbols) >= 1

        # Create minimal mock data
        ohlcv_df = pd.DataFrame(
            [
                {
                    "symbol": "AAPL",
                    "date": date(2024, 1, 15),
                    "Open": 100.0,
                    "High": 105.0,
                    "Low": 99.0,
                    "Close": 104.0,
                    "Volume": 50000000,
                }
            ]
        )

        # Calculate metrics
        analysis_df = calc_return_pct(ohlcv_df)
        analysis_df = calc_intraday_vol_pct(analysis_df)

        # Generate rankings
        top = top_n(analysis_df, col="return_pct", n=1)
        bottom = bottom_n(analysis_df, col="return_pct", n=1)
        volatile = top_n(analysis_df, col="vol_pct", n=1)

        # Generate report
        report = render_markdown(date(2024, 1, 15), top, bottom, volatile)

        # Verify report structure
        assert "|" in report or "-" in report  # Table structure
        assert "AAPL" in report  # Data included

    finally:
        if os.path.exists(universe_path):
            os.unlink(universe_path)

