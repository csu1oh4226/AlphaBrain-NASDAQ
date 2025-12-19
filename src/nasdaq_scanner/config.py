"""Configuration constants for the NASDAQ Scanner application.

This module contains all magic numbers, default values, and configuration
constants used throughout the application.
"""

from typing import List

# Cache Configuration
CACHE_TTL_SECONDS: int = 3600  # 1 hour cache TTL

# Data Collection
DEFAULT_MAX_RETRIES: int = 2
MIN_DATA_POINTS_FOR_ANALYSIS: int = 2

# YFinance Provider Configuration
YFINANCE_HISTORY_LOOKBACK_DAYS: int = 5  # Days to look back for history data
YFINANCE_HISTORY_LOOKAHEAD_DAYS: int = 1  # Days to look ahead for history data

# Price Data Column Names
PRICE_DATA_COLUMNS: List[str] = ["ticker", "date", "close", "volume"]

# Volatility Configuration
DEFAULT_VOLATILITY_WINDOW: int = 5
MIN_VOLATILITY_WINDOW: int = 1
MAX_VOLATILITY_WINDOW: int = 30

# Filter Defaults
DEFAULT_MIN_RETURN_PCT: float = -100.0
DEFAULT_MAX_RETURN_PCT: float = 100.0
DEFAULT_MIN_VOL_PCT: float = 0.0
MAX_RETURN_PCT_LIMIT: float = 100.0
MIN_RETURN_PCT_LIMIT: float = -100.0
MAX_VOL_PCT_LIMIT: float = 100.0

# Top Movers Configuration
DEFAULT_TOP_N: int = 10
MIN_TOP_N: int = 5
MAX_TOP_N: int = 20

# Recommendation Configuration
DEFAULT_RECOMMENDATION_COUNT: int = 5
MAX_RECOMMENDATION_COUNT: int = 20

# Date Range Configuration
DEFAULT_DATE_RANGE_DAYS: int = 30

# Display Configuration
MAX_FAILED_SYMBOLS_DISPLAY: int = 20
DECIMAL_PLACES_PRICE: int = 2
DECIMAL_PLACES_PERCENTAGE: int = 2

# Recommendation Thresholds
BUY_THRESHOLD_HIGH_RETURN: float = 5.0
BUY_THRESHOLD_MODERATE_RETURN: float = 3.0
BUY_THRESHOLD_LOW_RETURN: float = 2.0
BUY_THRESHOLD_HIGH_VOLATILITY: float = 4.0
BUY_THRESHOLD_LOW_VOLATILITY: float = 3.0

SELL_THRESHOLD_SHARP_DECLINE: float = -5.0
SELL_THRESHOLD_MODERATE_DECLINE: float = -3.0
SELL_THRESHOLD_DECLINE: float = -2.0
SELL_THRESHOLD_HIGH_VOLATILITY: float = 5.0

# Temporary File Configuration
TEMP_UNIVERSE_FILENAME: str = "temp_universe.csv"

# Ticker Source Types
TICKER_SOURCE_NASDAQ100: str = "nasdaq-100"
TICKER_SOURCE_CSV: str = "CSV 파일"
TICKER_SOURCE_MANUAL: str = "직접 입력"

# Default Ticker List
DEFAULT_TICKER_INPUT: str = "AAPL, MSFT, GOOGL, AMZN, TSLA"

