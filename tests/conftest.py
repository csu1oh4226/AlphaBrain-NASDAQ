"""Pytest configuration and shared fixtures."""

import pytest
from datetime import date, datetime
from typing import Dict, Any


@pytest.fixture
def sample_date() -> date:
    """Sample date for testing."""
    return date(2024, 1, 15)


@pytest.fixture
def sample_symbol() -> str:
    """Sample stock symbol."""
    return "AAPL"


@pytest.fixture
def sample_ohlcv_data() -> Dict[str, Any]:
    """Sample OHLCV data for testing."""
    return {
        "symbol": "AAPL",
        "date": date(2024, 1, 15),
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 104.0,
        "volume": 50000000,
    }


@pytest.fixture
def sample_symbols_list() -> list[str]:
    """Sample list of NASDAQ symbols."""
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC"]

