"""Analytics service layer for computing metrics and rankings.

This module provides a service layer that orchestrates data collection,
metric computation, and ranking generation.
"""

import pandas as pd
from datetime import date
from typing import Dict, Any, List, Tuple
from pandas import DataFrame

from nasdaq_scanner.providers import collect_data
from nasdaq_scanner.core.analytics import (
    compute_daily_returns,
    compute_volatility,
)
from nasdaq_scanner.core.analysis_functions import (
    calc_daily_returns,
    calc_volatility_proxy,
    rank_movers,
)
from nasdaq_scanner.config import (
    DEFAULT_MAX_RETRIES,
    MIN_DATA_POINTS_FOR_ANALYSIS,
    DEFAULT_TOP_N,
)


class AnalyticsService:
    """Service for computing analytics metrics and rankings."""

    def __init__(self, max_retries: int = DEFAULT_MAX_RETRIES):
        """Initialize analytics service.

        Args:
            max_retries: Maximum number of retries for data collection.
        """
        self.max_retries = max_retries

    def collect_market_data(
        self,
        ticker_source: Any,
        target_date: date,
    ) -> Tuple[DataFrame, List[str]]:
        """Collect market data for tickers.

        Args:
            ticker_source: Source of ticker list (str, Path, or List[str]).
            target_date: Target date for data collection.

        Returns:
            Tuple of (price DataFrame, failed symbols list).
        """
        return collect_data(
            ticker_source,
            target_date,
            max_retries=self.max_retries,
        )

    def compute_metrics(
        self,
        price_df: DataFrame,
        volatility_window: int,
    ) -> DataFrame:
        """Compute metrics from price data.

        Uses core/analysis_functions.py for consistent calculation:
        - calc_daily_returns(): Adds 'return' column (daily return %)
        - calc_volatility_proxy(): Adds 'vol' column (intraday volatility %)

        Args:
            price_df: DataFrame with columns: ticker, date, close, volume.
            volatility_window: Window size for volatility calculation (unused, kept for compatibility).

        Returns:
            DataFrame with computed metrics:
            - ticker, date, close, volume
            - return: Daily return percentage (from calc_daily_returns)
            - vol: Intraday volatility percentage (from calc_volatility_proxy)
        """
        if price_df.empty:
            return pd.DataFrame()

        # Use core/analysis_functions.py for consistent calculation
        # Step 1: Calculate daily returns (adds 'return' column)
        df_with_returns = calc_daily_returns(price_df)

        # Step 2: Calculate volatility proxy (adds 'vol' column)
        # Note: calc_volatility_proxy requires 'open', 'high', 'low' columns
        # If not available, use price range as fallback
        if all(col in df_with_returns.columns for col in ['open', 'high', 'low']):
            df_with_metrics = calc_volatility_proxy(df_with_returns)
        else:
            # If OHLC data not available, use price range as volatility proxy
            df_with_metrics = df_with_returns.copy()
            # Calculate vol as price range / close * 100 (percentage)
            for ticker in df_with_metrics['ticker'].unique():
                ticker_mask = df_with_metrics['ticker'] == ticker
                ticker_data = df_with_metrics[ticker_mask].sort_values('date')
                if len(ticker_data) >= MIN_DATA_POINTS_FOR_ANALYSIS:
                    price_range = ticker_data['close'].max() - ticker_data['close'].min()
                    base_price = ticker_data['close'].iloc[0]
                    vol_pct = (price_range / base_price * 100) if base_price > 0 else 0.0
                    df_with_metrics.loc[ticker_mask, 'vol'] = vol_pct
                else:
                    df_with_metrics.loc[ticker_mask, 'vol'] = 0.0

        # Return latest data for each ticker (for ranking)
        # This matches the expected format for rank_movers(): ticker, date, close, return, vol
        latest_data = []
        for ticker in df_with_metrics['ticker'].unique():
            ticker_data = df_with_metrics[df_with_metrics['ticker'] == ticker].sort_values('date')
            if len(ticker_data) >= MIN_DATA_POINTS_FOR_ANALYSIS:
                latest = ticker_data.iloc[-1]
                # Ensure we have return and vol columns
                if 'return' not in latest.index or pd.isna(latest.get('return')):
                    continue  # Skip if no valid return
                latest_data.append(latest)

        if not latest_data:
            return pd.DataFrame()

        result_df = pd.DataFrame(latest_data)
        return result_df

    def apply_filters(
        self,
        metrics_df: DataFrame,
        min_return_pct: float,
        max_return_pct: float,
        min_vol_pct: float,
    ) -> DataFrame:
        """Apply filters to metrics DataFrame.

        Args:
            metrics_df: DataFrame with metrics.
            min_return_pct: Minimum return percentage filter.
            max_return_pct: Maximum return percentage filter.
            min_vol_pct: Minimum volatility percentage filter.

        Returns:
            Filtered DataFrame.
        """
        return metrics_df[
            (metrics_df['return_pct'] >= min_return_pct) &
            (metrics_df['return_pct'] <= max_return_pct) &
            (metrics_df['vol_pct'] >= min_vol_pct)
        ].copy()

    def get_top_rankings(
        self,
        metrics_df: DataFrame,
        n: int = DEFAULT_TOP_N,
    ) -> Dict[str, DataFrame]:
        """Get top rankings for volatility, gainers, and losers.

        Uses core/analysis_functions.py::rank_movers() for consistent ranking.

        Args:
            metrics_df: DataFrame with metrics (columns: ticker, date, close, return, vol).
            n: Number of top movers to return (default: 10).

        Returns:
            Dictionary with keys:
            - 'volatile': Top N by vol (descending)
            - 'gainers': Top N by return (descending)
            - 'losers': Top N by return (ascending)
        """
        if metrics_df.empty:
            return {
                'volatile': pd.DataFrame(columns=metrics_df.columns),
                'gainers': pd.DataFrame(columns=metrics_df.columns),
                'losers': pd.DataFrame(columns=metrics_df.columns),
            }

        # Use core/analysis_functions.py::rank_movers() for consistent ranking
        # This function expects: ticker, return, vol columns
        rankings = rank_movers(metrics_df, top_n=n)

        return {
            'volatile': rankings['volatile'],
            'gainers': rankings['gainers'],
            'losers': rankings['losers'],
        }

