"""Unit tests for universe loader functions.

Tests for load_tickers function that reads ticker symbols from CSV files
with normalization rules (whitespace, duplicates, case, empty lines).
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from typing import List

# Import functions to test (will fail until implemented - RED phase)
from nasdaq_scanner.core.universe import load_tickers


class TestLoadTickers:
    """Tests for load_tickers function."""

    @pytest.mark.unit
    def test_load_tickers_basic_single_column(self) -> None:
        """Test loading tickers from CSV with single column."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("AAPL\n")
            f.write("MSFT\n")
            f.write("GOOGL\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert isinstance(result, list)
            assert len(result) == 3
            assert "AAPL" in result
            assert "MSFT" in result
            assert "GOOGL" in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_with_header(self) -> None:
        """Test loading tickers from CSV with header row."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("symbol\n")
            f.write("AAPL\n")
            f.write("MSFT\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 2
            assert "AAPL" in result
            assert "MSFT" in result
            assert "symbol" not in result  # Header should not be included
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_symbol_column(self) -> None:
        """Test loading tickers when CSV has 'symbol' column."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("symbol,name,exchange\n")
            f.write("AAPL,Apple Inc,NASDAQ\n")
            f.write("MSFT,Microsoft Corp,NASDAQ\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 2
            assert "AAPL" in result
            assert "MSFT" in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_whitespace_trimming(self) -> None:
        """Test that whitespace is trimmed from ticker symbols."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("  AAPL  \n")
            f.write(" MSFT \n")
            f.write("\tGOOGL\t\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 3
            assert "AAPL" in result  # Should be trimmed
            assert "MSFT" in result  # Should be trimmed
            assert "GOOGL" in result  # Should be trimmed
            # Should not contain whitespace
            assert not any(" " in ticker or "\t" in ticker for ticker in result)
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_lowercase_conversion(self) -> None:
        """Test that lowercase tickers are converted to uppercase."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("aapl\n")
            f.write("MSFT\n")
            f.write("googl\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 3
            assert "AAPL" in result  # Should be uppercase
            assert "MSFT" in result  # Already uppercase
            assert "GOOGL" in result  # Should be uppercase
            # All should be uppercase
            assert all(ticker.isupper() or not ticker.isalpha() for ticker in result)
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_duplicate_removal(self) -> None:
        """Test that duplicate tickers are removed."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("AAPL\n")
            f.write("MSFT\n")
            f.write("AAPL\n")  # Duplicate
            f.write("GOOGL\n")
            f.write("MSFT\n")  # Duplicate
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 3  # Should remove duplicates
            assert result.count("AAPL") == 1
            assert result.count("MSFT") == 1
            assert result.count("GOOGL") == 1
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_empty_lines_ignored(self) -> None:
        """Test that empty lines are ignored."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("AAPL\n")
            f.write("\n")  # Empty line
            f.write("MSFT\n")
            f.write("  \n")  # Whitespace-only line
            f.write("GOOGL\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 3
            assert "AAPL" in result
            assert "MSFT" in result
            assert "GOOGL" in result
            # Should not contain empty strings
            assert "" not in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_combined_normalization(self) -> None:
        """Test combined normalization rules (whitespace + case + duplicates)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("  aapl  \n")
            f.write("AAPL\n")  # Duplicate after trimming
            f.write(" msft \n")
            f.write("MSFT\n")  # Duplicate after trimming
            f.write("\n")  # Empty line
            f.write("googl\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 3  # Should remove duplicates after normalization
            assert "AAPL" in result
            assert "MSFT" in result
            assert "GOOGL" in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_empty_file(self) -> None:
        """Test loading from empty CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_file_not_found(self) -> None:
        """Test loading from non-existent file."""
        non_existent_path = "/nonexistent/path/tickers.csv"

        with pytest.raises((FileNotFoundError, IOError, OSError)):
            load_tickers(non_existent_path)

    @pytest.mark.unit
    def test_load_tickers_invalid_csv_format(self) -> None:
        """Test loading from invalid CSV format (if applicable)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("AAPL,MSFT,GOOGL\n")  # All in one line (might be valid or invalid)
            temp_path = f.name

        try:
            # Should either work (treat as single column) or raise error
            result = load_tickers(temp_path)
            # If it works, should extract tickers correctly
            assert isinstance(result, list)
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_preserves_order(self) -> None:
        """Test that ticker order is preserved (first occurrence kept for duplicates)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("AAPL\n")
            f.write("MSFT\n")
            f.write("GOOGL\n")
            f.write("AAPL\n")  # Duplicate
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            # Order should be preserved (first occurrence of duplicates)
            assert result[0] == "AAPL"
            assert result[1] == "MSFT"
            assert result[2] == "GOOGL"
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_special_characters(self) -> None:
        """Test handling of special characters in ticker symbols."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("BRK.A\n")  # Class A shares
            f.write("BRK.B\n")  # Class B shares
            f.write("MSFT\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 3
            assert "BRK.A" in result
            assert "BRK.B" in result
            assert "MSFT" in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_mixed_case_duplicates(self) -> None:
        """Test that case-insensitive duplicates are handled correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("aapl\n")
            f.write("AAPL\n")  # Duplicate after case conversion
            f.write("AaPl\n")  # Duplicate after case conversion
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            # After converting to uppercase, all should be the same
            assert len(result) == 1
            assert result[0] == "AAPL"
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_multiple_columns_first_column(self) -> None:
        """Test loading when CSV has multiple columns without 'symbol' column."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("ticker,name\n")
            f.write("AAPL,Apple Inc\n")
            f.write("MSFT,Microsoft Corp\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            # Should use first column if 'symbol' column doesn't exist
            assert len(result) == 2
            assert "AAPL" in result
            assert "MSFT" in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_whitespace_only_after_trim(self) -> None:
        """Test that lines that become empty after trimming are ignored."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("AAPL\n")
            f.write("   \n")  # Whitespace only
            f.write("\t\t\n")  # Tabs only
            f.write("MSFT\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert len(result) == 2
            assert "AAPL" in result
            assert "MSFT" in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_load_tickers_return_type(self) -> None:
        """Test that function returns a list of strings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("AAPL\n")
            f.write("MSFT\n")
            temp_path = f.name

        try:
            result = load_tickers(temp_path)

            assert isinstance(result, list)
            assert all(isinstance(ticker, str) for ticker in result)
        finally:
            os.unlink(temp_path)

