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
    top_movers,
)
from nasdaq_scanner.config import (
    DEFAULT_MAX_RETRIES,
    MIN_DATA_POINTS_FOR_ANALYSIS,
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

        Args:
            price_df: DataFrame with columns: ticker, date, close, volume.
            volatility_window: Window size for volatility calculation.

        Returns:
            DataFrame with computed metrics:
            - ticker, date, close, volume
            - return_pct: Daily return percentage
            - vol_pct: Intraday volatility percentage
            - volatility: Rolling volatility
        """
        if price_df.empty:
            return pd.DataFrame()

        results = []

        for ticker in price_df['ticker'].unique():
            ticker_data = price_df[price_df['ticker'] == ticker].sort_values('date')

            if len(ticker_data) < MIN_DATA_POINTS_FOR_ANALYSIS:
                continue

            # Compute daily returns
            returns = compute_daily_returns(ticker_data['close'])

            # Compute volatility
            volatility = compute_volatility(returns, volatility_window)

            # Get latest values
            latest = ticker_data.iloc[-1]
            latest_return = (
                returns.iloc[-1] if not pd.isna(returns.iloc[-1]) else 0.0
            )
            latest_volatility = (
                volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else 0.0
            )

            # Calculate intraday volatility using price range
            if len(ticker_data) >= MIN_DATA_POINTS_FOR_ANALYSIS:
                price_range = ticker_data['close'].max() - ticker_data['close'].min()
                base_price = ticker_data['close'].iloc[0]
                vol_pct = (price_range / base_price * 100) if base_price > 0 else 0.0
            else:
                vol_pct = 0.0

            results.append({
                'ticker': ticker,
                'date': latest['date'],
                'close': latest['close'],
                'volume': latest['volume'],
                'return_pct': latest_return,
                'vol_pct': vol_pct,
                'volatility': latest_volatility,
            })

        return pd.DataFrame(results)

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
        n: int,
    ) -> Dict[str, DataFrame]:
        """Get top rankings for volatility, gainers, and losers.

        Args:
            metrics_df: DataFrame with metrics.
            n: Number of top movers to return.

        Returns:
            Dictionary with keys:
            - 'volatile': Top N by volatility
            - 'gainers': Top N by return (descending)
            - 'losers': Top N by return (ascending)
        """
        # Volatile movers (by vol_pct)
        volatile = top_movers(metrics_df, n=n, direction='up')
        if not volatile.empty:
            volatile = volatile.sort_values('vol_pct', ascending=False).head(n)

        # Gainers (by return_pct descending)
        gainers = top_movers(metrics_df, n=n, direction='up')
        if not gainers.empty:
            gainers = gainers.sort_values('return_pct', ascending=False).head(n)

        # Losers (by return_pct ascending)
        losers = top_movers(metrics_df, n=n, direction='down')
        if not losers.empty:
            losers = losers.sort_values('return_pct', ascending=True).head(n)

        return {
            'volatile': volatile,
            'gainers': gainers,
            'losers': losers,
        }

