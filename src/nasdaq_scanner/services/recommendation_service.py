"""Recommendation service layer for generating trade recommendations.

This module provides a service layer for generating and formatting
buy/sell recommendations with clear reasoning.
"""

import pandas as pd
from pandas import DataFrame
from typing import Dict, Any, List

from nasdaq_scanner.core.analytics import recommend_trades
from nasdaq_scanner.config import (
    DEFAULT_RECOMMENDATION_COUNT,
    BUY_THRESHOLD_HIGH_RETURN,
    BUY_THRESHOLD_MODERATE_RETURN,
    BUY_THRESHOLD_LOW_RETURN,
    BUY_THRESHOLD_HIGH_VOLATILITY,
    BUY_THRESHOLD_LOW_VOLATILITY,
    SELL_THRESHOLD_SHARP_DECLINE,
    SELL_THRESHOLD_MODERATE_DECLINE,
    SELL_THRESHOLD_DECLINE,
    SELL_THRESHOLD_HIGH_VOLATILITY,
)


class RecommendationService:
    """Service for generating trade recommendations."""

    def generate_recommendations(
        self,
        metrics_df: DataFrame,
        max_count: int = DEFAULT_RECOMMENDATION_COUNT,
    ) -> Dict[str, DataFrame]:
        """Generate buy and sell recommendations.

        Args:
            metrics_df: DataFrame with metrics.
            max_count: Maximum number of recommendations per category.

        Returns:
            Dictionary with 'buy' and 'sell' DataFrames.
        """
        recommendations = recommend_trades(metrics_df)

        # Limit to max_count
        buy_df = recommendations['buy'].head(max_count)
        sell_df = recommendations['sell'].head(max_count)

        return {
            'buy': buy_df,
            'sell': sell_df,
        }

    def extract_recommendation_reasons(
        self,
        row: pd.Series,
        is_buy: bool = True,
    ) -> List[str]:
        """Extract recommendation reasons from row data.

        Args:
            row: Series with ticker metrics.
            is_buy: True for buy recommendations, False for sell.

        Returns:
            List of reason strings.
        """
        reasons = []

        if is_buy:
            return_pct = row.get('return_pct', 0)
            vol_pct = row.get('vol_pct', 0)
            volatility = row.get('volatility', 0)

            if return_pct > BUY_THRESHOLD_HIGH_RETURN:
                reasons.append("높은 수익률")
            elif return_pct > BUY_THRESHOLD_MODERATE_RETURN:
                reasons.append("적정 수익률")
            elif return_pct > BUY_THRESHOLD_LOW_RETURN:
                reasons.append("양호한 수익률")

            if vol_pct > BUY_THRESHOLD_HIGH_VOLATILITY:
                reasons.append("높은 변동성")
            elif volatility < BUY_THRESHOLD_LOW_VOLATILITY:
                reasons.append("낮은 변동성 (안정적)")

        else:  # sell
            return_pct = row.get('return_pct', 0)
            vol_pct = row.get('vol_pct', 0)
            volatility = row.get('volatility', 0)

            if return_pct < SELL_THRESHOLD_SHARP_DECLINE:
                reasons.append("급락")
            elif return_pct < SELL_THRESHOLD_MODERATE_DECLINE:
                reasons.append("급격한 하락")
            elif return_pct < SELL_THRESHOLD_DECLINE:
                reasons.append("하락 추세")

            if vol_pct > SELL_THRESHOLD_HIGH_VOLATILITY:
                reasons.append("높은 변동성 (불안정)")
            elif volatility > SELL_THRESHOLD_HIGH_VOLATILITY:
                reasons.append("높은 변동성")

        return reasons

