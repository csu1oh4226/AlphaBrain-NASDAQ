"""Analytics service layer for computing metrics and rankings.

This module provides a service layer that orchestrates data collection,
metric computation, and ranking generation.
"""

import pandas as pd
import numpy as np
from datetime import date
from typing import Dict, Any, List, Tuple
from pandas import DataFrame

from nasdaq_scanner.providers import collect_data
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
            Tuple of (price DataFrame with OHLCV columns, failed symbols list).
        """
        return collect_data(
            ticker_source,
            target_date,
            max_retries=self.max_retries,
        )

    def compute_metrics(
        self,
        price_df: DataFrame,
        volatility_window: int = 1,  # Not used, kept for compatibility
    ) -> DataFrame:
        """Compute metrics from OHLCV price data.

        Uses core/analysis_functions.py for consistent calculation:
        - calc_daily_returns(): Adds 'return' column ((Close - Open) / Open * 100)
        - calc_volatility_proxy(): Adds 'vol' column ((High - Low) / Open * 100)

        Args:
            price_df: DataFrame with columns: ticker, date, open, high, low, close, volume.
            volatility_window: Window size for volatility calculation (unused, kept for compatibility).

        Returns:
            DataFrame with computed metrics:
            - ticker, date, open, high, low, close, volume
            - return: Daily return percentage (from calc_daily_returns)
            - vol: Intraday volatility percentage (from calc_volatility_proxy)
        """
        if price_df.empty:
            return pd.DataFrame()

        # Validate required columns
        required_cols = ["ticker", "date", "open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in price_df.columns]
        if missing_cols:
            # If OHLC data not available, return empty
            return pd.DataFrame()

        # Use core/analysis_functions.py for consistent calculation
        # Step 1: Calculate daily returns (adds 'return' column)
        df_with_returns = calc_daily_returns(price_df)

        # Step 2: Calculate volatility proxy (adds 'vol' column) - Range volatility (High-Low)/Open
        df_with_vol_range = calc_volatility_proxy(df_with_returns)

        # Step 3: Calculate volatility using standard deviation (adds 'vol_std' column)
        # For rolling standard deviation, we need multiple days of data
        from nasdaq_scanner.core.analysis_functions import calc_volatility_std
        df_with_vol_std = calc_volatility_std(df_with_vol_range, window=5)
        
        # Use vol_std as primary volatility measure, fallback to range volatility
        if 'vol_std' in df_with_vol_std.columns:
            # For single day data, use range volatility; for multiple days, use std
            df_with_vol_std['vol'] = df_with_vol_std['vol_std'].fillna(df_with_vol_std.get('vol', 0))
        else:
            df_with_vol_std['vol'] = df_with_vol_range.get('vol', 0)
        
        df_with_metrics = df_with_vol_std

        # Filter out NaN and inf values
        df_clean = df_with_metrics[
            df_with_metrics["return"].notna() &
            df_with_metrics["vol"].notna() &
            np.isfinite(df_with_metrics["return"]) &
            np.isfinite(df_with_metrics["vol"])
        ].copy()

        if df_clean.empty:
            # Log why data was filtered out
            logger.warning(f"All data filtered out after metrics calculation. Original rows: {len(df_with_metrics)}")
            if not df_with_metrics.empty:
                logger.debug(f"Return NaN count: {df_with_metrics['return'].isna().sum()}")
                logger.debug(f"Vol NaN count: {df_with_metrics['vol'].isna().sum()}")
                logger.debug(f"Return inf count: {np.isinf(df_with_metrics['return']).sum() if 'return' in df_with_metrics.columns else 0}")
                logger.debug(f"Vol inf count: {np.isinf(df_with_metrics['vol']).sum() if 'vol' in df_with_metrics.columns else 0}")
                # Check for zero open prices
                zero_open_count = (df_with_metrics['open'] == 0).sum() if 'open' in df_with_metrics.columns else 0
                logger.debug(f"Zero open price count: {zero_open_count}")
            return pd.DataFrame()

        # Return latest data for each ticker (for ranking)
        # For single day analysis, we just need the latest date's data
        latest_data = []
        for ticker in df_clean['ticker'].unique():
            ticker_data = df_clean[df_clean['ticker'] == ticker].sort_values('date')
            if not ticker_data.empty:
                # Use latest date's data
                latest = ticker_data.iloc[-1]
                latest_data.append(latest)

        if not latest_data:
            logger.warning("No valid data after filtering")
            return pd.DataFrame()

        result_df = pd.DataFrame(latest_data)
        
        # Ensure we have required columns
        required_result_cols = ["ticker", "date", "return", "vol"]
        missing_result_cols = [col for col in required_result_cols if col not in result_df.columns]
        if missing_result_cols:
            logger.error(f"Missing required columns in result: {missing_result_cols}")
            return pd.DataFrame()
        
        # Ensure vol column has valid values (fill NaN with 0 for range volatility)
        if 'vol' in result_df.columns:
            result_df['vol'] = result_df['vol'].fillna(0)
        
        return result_df

    def get_top_rankings(
        self,
        metrics_df: DataFrame,
        n: int = DEFAULT_TOP_N,
    ) -> Dict[str, DataFrame]:
        """Get top rankings for volatility, gainers, and losers.

        Uses core/analysis_functions.py::rank_movers() for consistent ranking.

        Args:
            metrics_df: DataFrame with metrics (columns: ticker, date, return, vol).
            n: Number of top movers to return (default: 10).

        Returns:
            Dictionary with keys:
            - 'volatile': Top N by vol (descending)
            - 'gainers': Top N by return (descending)
            - 'losers': Top N by return (ascending)
        """
        if metrics_df.empty:
            return {
                'volatile': pd.DataFrame(),
                'gainers': pd.DataFrame(),
                'losers': pd.DataFrame(),
            }

        # Use core/analysis_functions.py::rank_movers() for consistent ranking
        rankings = rank_movers(metrics_df, top_n=n)

        return {
            'volatile': rankings['volatile'],
            'gainers': rankings['gainers'],
            'losers': rankings['losers'],
        }

    def get_recommendations(
        self,
        metrics_df: DataFrame,
        top_n: int = 5,
    ) -> Dict[str, DataFrame]:
        """Get investment recommendations (observations, not advice).

        Args:
            metrics_df: DataFrame with metrics (columns: ticker, date, return, vol).
            top_n: Number of recommendations per category (default: 5).

        Returns:
            Dictionary with keys:
            - 'observations': Top N stocks with high return + high volatility (intersection)
            - 'warnings': Top N stocks with sharp decline + high volatility
        """
        if metrics_df.empty:
            return {
                'observations': pd.DataFrame(),
                'warnings': pd.DataFrame(),
            }

        # Filter valid data
        df_clean = metrics_df[
            metrics_df["return"].notna() &
            metrics_df["vol"].notna() &
            np.isfinite(metrics_df["return"]) &
            np.isfinite(metrics_df["vol"])
        ].copy()

        if df_clean.empty:
            return {
                'observations': pd.DataFrame(),
                'warnings': pd.DataFrame(),
            }

        # Observations: High return + High volatility (intersection)
        top_gainers = df_clean.nlargest(top_n * 2, 'return')
        top_volatile = df_clean.nlargest(top_n * 2, 'vol')
        
        gainer_tickers = set(top_gainers['ticker'].unique())
        volatile_tickers = set(top_volatile['ticker'].unique())
        observation_tickers = gainer_tickers & volatile_tickers

        if observation_tickers:
            observations = df_clean[df_clean['ticker'].isin(observation_tickers)].copy()
            observations = observations.nlargest(top_n, 'return')
        else:
            observations = pd.DataFrame()

        # Warnings: Sharp decline + High volatility
        losers = df_clean[df_clean['return'] < 0].copy()
        if not losers.empty:
            # Top losers by return (most negative)
            top_losers = losers.nsmallest(top_n * 2, 'return')
            # From top losers, select by volatility
            warnings = top_losers.nlargest(top_n, 'vol')
        else:
            warnings = pd.DataFrame()

        return {
            'observations': observations,
            'warnings': warnings,
        }
