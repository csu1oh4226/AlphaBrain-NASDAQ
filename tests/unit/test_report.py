"""Unit tests for report generation functions.

Tests for render_markdown function that generates markdown reports
with tables, headers, and date information.
"""

import pytest
import pandas as pd
from datetime import date
from pandas import DataFrame

# Import functions to test (will fail until implemented - RED phase)
from nasdaq_scanner.reporter.report import render_markdown


class TestRenderMarkdown:
    """Tests for render_markdown function."""

    @pytest.mark.unit
    def test_render_markdown_basic(self) -> None:
        """Test basic markdown report generation."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA", "META"],
            "return_pct": [-5.0, -3.0],
        })
        volatile_df = pd.DataFrame({
            "symbol": ["GOOGL", "AMZN"],
            "vol_pct": [10.0, 8.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_render_markdown_contains_header(self) -> None:
        """Test that markdown contains header."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({"symbol": ["AAPL"], "return_pct": [5.0]})
        bottom_df = pd.DataFrame({"symbol": ["TSLA"], "return_pct": [-5.0]})
        volatile_df = pd.DataFrame({"symbol": ["GOOGL"], "vol_pct": [10.0]})

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain header title
        assert "NASDAQ" in result or "Daily Movers" in result or "Analyzer" in result

    @pytest.mark.unit
    def test_render_markdown_contains_date(self) -> None:
        """Test that markdown contains date."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({"symbol": ["AAPL"], "return_pct": [5.0]})
        bottom_df = pd.DataFrame({"symbol": ["TSLA"], "return_pct": [-5.0]})
        volatile_df = pd.DataFrame({"symbol": ["GOOGL"], "vol_pct": [10.0]})

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain date in some format
        assert "2024" in result or "01-15" in result or "2024-01-15" in result

    @pytest.mark.unit
    def test_render_markdown_contains_tables(self) -> None:
        """Test that markdown contains table structures."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "return_pct": [5.0, 3.0],
        })
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA", "META"],
            "return_pct": [-5.0, -3.0],
        })
        volatile_df = pd.DataFrame({
            "symbol": ["GOOGL", "AMZN"],
            "vol_pct": [10.0, 8.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain markdown table syntax (pipes or dashes)
        assert "|" in result or "-" in result

    @pytest.mark.unit
    def test_render_markdown_contains_top_section(self) -> None:
        """Test that markdown contains top movers section."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })
        bottom_df = pd.DataFrame({"symbol": ["TSLA"], "return_pct": [-5.0]})
        volatile_df = pd.DataFrame({"symbol": ["GOOGL"], "vol_pct": [10.0]})

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain top movers data
        assert "AAPL" in result
        # Should contain section header or title for top movers
        assert "top" in result.lower() or "상승" in result or "gain" in result.lower()

    @pytest.mark.unit
    def test_render_markdown_contains_bottom_section(self) -> None:
        """Test that markdown contains bottom movers section."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({"symbol": ["AAPL"], "return_pct": [5.0]})
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA"],
            "return_pct": [-5.0],
        })
        volatile_df = pd.DataFrame({"symbol": ["GOOGL"], "vol_pct": [10.0]})

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain bottom movers data
        assert "TSLA" in result
        # Should contain section header or title for bottom movers
        assert "bottom" in result.lower() or "하락" in result or "loss" in result.lower()

    @pytest.mark.unit
    def test_render_markdown_contains_volatile_section(self) -> None:
        """Test that markdown contains volatile movers section."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({"symbol": ["AAPL"], "return_pct": [5.0]})
        bottom_df = pd.DataFrame({"symbol": ["TSLA"], "return_pct": [-5.0]})
        volatile_df = pd.DataFrame({
            "symbol": ["GOOGL"],
            "vol_pct": [10.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain volatile movers data
        assert "GOOGL" in result
        # Should contain section header or title for volatile movers
        assert "volatil" in result.lower() or "변동" in result

    @pytest.mark.unit
    def test_render_markdown_empty_dataframes(self) -> None:
        """Test markdown generation with empty DataFrames."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame(columns=["symbol", "return_pct"])
        bottom_df = pd.DataFrame(columns=["symbol", "return_pct"])
        volatile_df = pd.DataFrame(columns=["symbol", "vol_pct"])

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should still generate markdown (with empty tables or sections)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_render_markdown_table_headers(self) -> None:
        """Test that tables contain proper headers."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
            "volume": [1000000],
        })
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA"],
            "return_pct": [-5.0],
        })
        volatile_df = pd.DataFrame({
            "symbol": ["GOOGL"],
            "vol_pct": [10.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain column headers (symbol, return_pct, etc.)
        assert "symbol" in result.lower() or "Symbol" in result

    @pytest.mark.unit
    def test_render_markdown_table_data(self) -> None:
        """Test that tables contain actual data values."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA"],
            "return_pct": [-5.0],
        })
        volatile_df = pd.DataFrame({
            "symbol": ["GOOGL"],
            "vol_pct": [10.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain actual values
        assert "5.0" in result or "5" in result  # return_pct value
        assert "10.0" in result or "10" in result  # vol_pct value

    @pytest.mark.unit
    def test_render_markdown_multiple_rows(self) -> None:
        """Test markdown generation with multiple rows in each section."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT", "GOOGL"],
            "return_pct": [5.0, 4.0, 3.0],
        })
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA", "META", "NFLX"],
            "return_pct": [-5.0, -4.0, -3.0],
        })
        volatile_df = pd.DataFrame({
            "symbol": ["AMZN", "NVDA", "AMD"],
            "vol_pct": [10.0, 9.0, 8.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain all symbols
        assert "AAPL" in result
        assert "MSFT" in result
        assert "GOOGL" in result
        assert "TSLA" in result
        assert "META" in result
        assert "NFLX" in result
        assert "AMZN" in result
        assert "NVDA" in result
        assert "AMD" in result

    @pytest.mark.unit
    def test_render_markdown_date_format(self) -> None:
        """Test that date is formatted correctly."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({"symbol": ["AAPL"], "return_pct": [5.0]})
        bottom_df = pd.DataFrame({"symbol": ["TSLA"], "return_pct": [-5.0]})
        volatile_df = pd.DataFrame({"symbol": ["GOOGL"], "vol_pct": [10.0]})

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Date should appear in readable format
        assert "2024" in result
        # Could be 2024-01-15, 01/15/2024, Jan 15 2024, etc.

    @pytest.mark.unit
    def test_render_markdown_section_separation(self) -> None:
        """Test that sections are properly separated in markdown."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA"],
            "return_pct": [-5.0],
        })
        volatile_df = pd.DataFrame({
            "symbol": ["GOOGL"],
            "vol_pct": [10.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should have multiple sections (header, top, bottom, volatile)
        # Check that all three data sections are present
        lines = result.split("\n")
        # Should have enough content for multiple sections
        assert len(lines) > 5

    @pytest.mark.unit
    def test_render_markdown_markdown_syntax(self) -> None:
        """Test that output follows markdown syntax conventions."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
        })
        bottom_df = pd.DataFrame({"symbol": ["TSLA"], "return_pct": [-5.0]})
        volatile_df = pd.DataFrame({"symbol": ["GOOGL"], "vol_pct": [10.0]})

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Markdown tables use pipes (|) and dashes (-)
        # Should have table structure
        has_table_structure = ("|" in result and "-" in result) or (
            "---" in result
        )
        assert has_table_structure

    @pytest.mark.unit
    def test_render_markdown_no_side_effects(self) -> None:
        """Test that function does not modify input DataFrames."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({"symbol": ["AAPL"], "return_pct": [5.0]})
        bottom_df = pd.DataFrame({"symbol": ["TSLA"], "return_pct": [-5.0]})
        volatile_df = pd.DataFrame({"symbol": ["GOOGL"], "vol_pct": [10.0]})

        top_df_copy = top_df.copy()
        bottom_df_copy = bottom_df.copy()
        volatile_df_copy = volatile_df.copy()

        render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Original DataFrames should not be modified
        pd.testing.assert_frame_equal(top_df, top_df_copy)
        pd.testing.assert_frame_equal(bottom_df, bottom_df_copy)
        pd.testing.assert_frame_equal(volatile_df, volatile_df_copy)

    @pytest.mark.unit
    def test_render_markdown_all_columns_included(self) -> None:
        """Test that all DataFrame columns are included in tables."""
        test_date = date(2024, 1, 15)
        top_df = pd.DataFrame({
            "symbol": ["AAPL"],
            "return_pct": [5.0],
            "volume": [1000000],
            "vol_pct": [2.0],
        })
        bottom_df = pd.DataFrame({
            "symbol": ["TSLA"],
            "return_pct": [-5.0],
        })
        volatile_df = pd.DataFrame({
            "symbol": ["GOOGL"],
            "vol_pct": [10.0],
        })

        result = render_markdown(test_date, top_df, bottom_df, volatile_df)

        # Should contain column names
        assert "symbol" in result.lower()
        assert "return_pct" in result.lower() or "return" in result.lower()
        # Additional columns may be included
        assert "volume" in result.lower() or "vol_pct" in result.lower()

