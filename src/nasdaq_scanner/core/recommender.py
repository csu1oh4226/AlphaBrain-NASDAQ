"""Recommendation module for generating buy/sell signals based on rules.

This module provides functions to generate buy and sell recommendations
using rule-based analysis with clear reasoning.
"""

import pandas as pd
from pandas import DataFrame
from typing import List, Dict, Any

from nasdaq_scanner.core.signals import generate_signals


def get_default_buy_rules() -> List[Dict[str, Any]]:
    """Get default rules for buy recommendations.

    Returns:
        List of rule dictionaries for buy signals.
    """
    return [
        {
            'name': 'high_return_top10',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                row.get('return_pct', 0) > 5.0
            ),
            'action': 'buy',
            'description': '일간 수익률 5% 이상'
        },
        {
            'name': 'high_volatility_high_return',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                pd.notna(row.get('vol_pct')) and
                row.get('return_pct', 0) > 3.0 and
                row.get('vol_pct', 0) > 4.0
            ),
            'action': 'buy',
            'description': '수익률 3% 이상 + 변동성 4% 이상'
        },
        {
            'name': 'moderate_gain',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                2.0 < row.get('return_pct', 0) <= 5.0
            ),
            'action': 'buy',
            'description': '수익률 2-5% (적정 상승)'
        },
    ]


def get_default_sell_rules() -> List[Dict[str, Any]]:
    """Get default rules for sell/watch recommendations.

    Returns:
        List of rule dictionaries for sell/watch signals.
    """
    return [
        {
            'name': 'sharp_decline',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                row.get('return_pct', 0) < -5.0
            ),
            'action': 'sell',
            'description': '일간 하락률 5% 이상 (급락 주의)'
        },
        {
            'name': 'high_volatility_decline',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                pd.notna(row.get('vol_pct')) and
                row.get('return_pct', 0) < -3.0 and
                row.get('vol_pct', 0) > 5.0
            ),
            'action': 'sell',
            'description': '하락률 3% 이상 + 변동성 5% 이상 (불안정)'
        },
        {
            'name': 'moderate_decline',
            'condition': lambda row: (
                pd.notna(row.get('return_pct')) and
                -5.0 <= row.get('return_pct', 0) < -2.0
            ),
            'action': 'watch',
            'description': '하락률 2-5% (주의 관찰)'
        },
    ]


def generate_recommendations(
    analysis_df: DataFrame,
    buy_rules: Optional[List[Dict[str, Any]]] = None,
    sell_rules: Optional[List[Dict[str, Any]]] = None,
    max_recommendations: int = 10,
) -> Dict[str, DataFrame]:
    """Generate buy and sell recommendations based on rules.

    Args:
        analysis_df: DataFrame with metrics (must contain 'symbol', 'return_pct', 'vol_pct').
        buy_rules: List of buy rule dictionaries. If None, uses default rules.
        sell_rules: List of sell rule dictionaries. If None, uses default rules.
        max_recommendations: Maximum number of recommendations per category.

    Returns:
        Dictionary with:
        {
            'buy': DataFrame with buy recommendations (columns: symbol, signal, reasons, ...),
            'sell': DataFrame with sell/watch recommendations,
            'buy_rules': List of applied buy rules,
            'sell_rules': List of applied sell rules
        }

    Examples:
        >>> df = pd.DataFrame({
        ...     'symbol': ['AAPL', 'TSLA'],
        ...     'return_pct': [6.0, -6.0],
        ...     'vol_pct': [3.0, 6.0]
        ... })
        >>> results = generate_recommendations(df)
        >>> len(results['buy']) > 0
        True
    """
    if buy_rules is None:
        buy_rules = get_default_buy_rules()
    if sell_rules is None:
        sell_rules = get_default_sell_rules()

    # Generate buy signals
    buy_signals_df = generate_signals(analysis_df, buy_rules)
    buy_recommendations = buy_signals_df[
        buy_signals_df['signal'] == 'buy'
    ].copy()

    # Generate sell/watch signals
    sell_signals_df = generate_signals(analysis_df, sell_rules)
    sell_recommendations = sell_signals_df[
        sell_signals_df['signal'].isin(['sell', 'watch'])
    ].copy()

    # Sort by return_pct (descending for buy, ascending for sell)
    if not buy_recommendations.empty and 'return_pct' in buy_recommendations.columns:
        buy_recommendations = buy_recommendations.sort_values(
            'return_pct', ascending=False
        ).head(max_recommendations)

    if not sell_recommendations.empty and 'return_pct' in sell_recommendations.columns:
        sell_recommendations = sell_recommendations.sort_values(
            'return_pct', ascending=True
        ).head(max_recommendations)

    return {
        'buy': buy_recommendations,
        'sell': sell_recommendations,
        'buy_rules': buy_rules,
        'sell_rules': sell_rules,
    }


def format_reasons(reasons: List[str], rules: List[Dict[str, Any]]) -> str:
    """Format reasons list into human-readable string.

    Args:
        reasons: List of rule names that matched.
        rules: List of rule dictionaries (to get descriptions).

    Returns:
        Formatted string with rule descriptions.
    """
    rule_dict = {rule['name']: rule.get('description', rule['name']) for rule in rules}
    descriptions = [rule_dict.get(name, name) for name in reasons]
    return ', '.join(descriptions) if descriptions else 'No specific reason'

