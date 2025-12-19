"""Reusable UI components for Streamlit dashboard.

This module contains reusable UI components to reduce duplication
and improve maintainability.
"""

import streamlit as st
import pandas as pd
from pandas import DataFrame
from typing import Dict, Any

from nasdaq_scanner.core.analytics import compute_daily_returns
from nasdaq_scanner.services.recommendation_service import RecommendationService
from nasdaq_scanner.config import (
    DECIMAL_PLACES_PRICE,
    DECIMAL_PLACES_PERCENTAGE,
)

# Initialize recommendation service
_recommendation_service = RecommendationService()

# Column name mappings for display
COLUMN_DISPLAY_NAMES = {
    'ticker': '티커',
    'vol_pct': '변동성 (%)',
    'return_pct': '수익률 (%)',
    'close': '종가',
    'volume': '거래량',
}


def render_stats_metrics(
    total_tickers: int,
    filtered_count: int,
    successful_fetches: int,
    failed_count: int,
) -> None:
    """Render statistics metrics in columns.

    Args:
        total_tickers: Total number of tickers.
        filtered_count: Number after filtering.
        successful_fetches: Number of successful data fetches.
        failed_count: Number of failed fetches.
    """
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 티커", total_tickers)
    with col2:
        st.metric("필터링 후", filtered_count)
    with col3:
        st.metric("수집 성공", successful_fetches)
    with col4:
        st.metric("수집 실패", failed_count)


def render_top_rankings_table(
    df: DataFrame,
    title: str,
    sort_column: str,
    ascending: bool = False,
) -> None:
    """Render a top rankings table.

    Args:
        df: DataFrame to display.
        title: Table title.
        sort_column: Column to sort by.
        ascending: Sort order.
    """
    st.subheader(title)
    if not df.empty:
        sorted_df = df.sort_values(sort_column, ascending=ascending)
        display_cols = ['ticker', 'return_pct', 'vol_pct', 'close', 'volume']
        available_cols = [c for c in display_cols if c in sorted_df.columns]

        # Rename columns for display
        display_df = sorted_df[available_cols].copy()
        display_df = display_df.rename(columns=COLUMN_DISPLAY_NAMES)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"{title} 데이터가 없습니다.")


def render_ticker_chart(
    ticker: str,
    price_df: DataFrame,
    metrics_df: DataFrame,
) -> None:
    """Render price and return charts for a selected ticker.

    Args:
        ticker: Selected ticker symbol.
        price_df: DataFrame with price data.
        metrics_df: DataFrame with metrics.
    """
    ticker_price_data = price_df[
        price_df['ticker'] == ticker
    ].sort_values('date')

    if ticker_price_data.empty:
        st.warning(f"{ticker}에 대한 데이터가 없습니다.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"💰 {ticker} 가격 차트")
        price_chart_data = ticker_price_data[['date', 'close']].set_index('date')
        st.line_chart(price_chart_data)

    with col2:
        st.subheader(f"📈 {ticker} 수익률 차트")
        returns = compute_daily_returns(ticker_price_data['close'])
        returns_df = pd.DataFrame({
            'date': ticker_price_data['date'].values,
            'return_pct': returns.values
        }).set_index('date')
        st.line_chart(returns_df)

    # Display metrics
    ticker_metrics = metrics_df[metrics_df['ticker'] == ticker]
    if not ticker_metrics.empty:
        metric = ticker_metrics.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("종가", f"${metric['close']:.{DECIMAL_PLACES_PRICE}f}")
        with col2:
            st.metric("수익률", f"{metric['return_pct']:.{DECIMAL_PLACES_PERCENTAGE}f}%")
        with col3:
            st.metric("변동성", f"{metric['vol_pct']:.{DECIMAL_PLACES_PERCENTAGE}f}%")
        with col4:
            st.metric("거래량", f"{metric['volume']:,}")


def render_recommendation_card(
    row: pd.Series,
    is_buy: bool = True,
) -> None:
    """Render a single recommendation card.

    Args:
        row: Series with recommendation data.
        is_buy: True for buy recommendation, False for sell.
    """
    ticker = row['ticker']
    st.markdown(f"### {ticker}")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(
            "수익률",
            f"{row.get('return_pct', 0):.{DECIMAL_PLACES_PERCENTAGE}f}%"
        )
    with col_b:
        st.metric(
            "변동성",
            f"{row.get('vol_pct', 0):.{DECIMAL_PLACES_PERCENTAGE}f}%"
        )
    with col_c:
        st.metric(
            "종가",
            f"${row.get('close', 0):.{DECIMAL_PLACES_PRICE}f}"
        )

    # Display reason
    reason = row.get('reason', '')
    if reason:
        if is_buy:
            st.info(f"📌 추천 근거: {reason}")
        else:
            st.warning(f"⚠️ 추천 근거: {reason}")
    else:
        # Extract reasons from metrics
        reasons = _recommendation_service.extract_recommendation_reasons(
            row, is_buy=is_buy
        )
        if reasons:
            reason_text = ', '.join(reasons)
            if is_buy:
                st.info(f"📌 추천 근거: {reason_text}")
            else:
                st.warning(f"⚠️ 추천 근거: {reason_text}")

    st.markdown("---")

