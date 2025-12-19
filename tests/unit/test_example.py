"""Example unit test to verify test setup."""

import pytest
from datetime import date


def test_example() -> None:
    """Simple test to verify pytest is working."""
    assert 1 + 1 == 2


def test_sample_date(sample_date: date) -> None:
    """Test using fixture from conftest."""
    assert sample_date == date(2024, 1, 15)


def test_sample_symbol(sample_symbol: str) -> None:
    """Test using symbol fixture."""
    assert sample_symbol == "AAPL"
    assert isinstance(sample_symbol, str)


@pytest.mark.unit
def test_marker_example() -> None:
    """Test with unit marker."""
    assert True

