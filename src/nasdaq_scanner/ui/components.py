"""Reusable UI components for Streamlit dashboard.

This module contains reusable UI components to reduce duplication
and improve maintainability.
"""

import streamlit as st
import pandas as pd
from pandas import DataFrame
from typing import Dict, Any, List

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
        # Support both 'return'/'vol' and 'return_pct'/'vol_pct' column names
        display_cols = ['ticker']
        if 'return' in sorted_df.columns:
            display_cols.extend(['return', 'vol', 'close'])
        elif 'return_pct' in sorted_df.columns:
            display_cols.extend(['return_pct', 'vol_pct', 'close'])
        if 'volume' in sorted_df.columns:
            display_cols.append('volume')
        
        available_cols = [c for c in display_cols if c in sorted_df.columns]

        # Rename columns for display
        display_df = sorted_df[available_cols].copy()
        # Map both old and new column names
        rename_map = COLUMN_DISPLAY_NAMES.copy()
        rename_map.update({
            'return': '수익률 (%)',
            'vol': '변동성 (%)',
        })
        display_df = display_df.rename(columns=rename_map)

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
        row: Series with recommendation data (should contain 'reason' column from generate_signals).
        is_buy: True for buy recommendation, False for sell.
    """
    ticker = row.get('ticker', 'N/A')
    
    # Use card container for better visual separation
    with st.container():
        if is_buy:
            st.markdown(f"### 💰 {ticker}")
        else:
            st.markdown(f"### ⚠️ {ticker}")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            # Use 'return' if available, otherwise 'return_pct'
            return_val = row.get('return', row.get('return_pct', 0))
            st.metric(
                "수익률",
                f"{return_val:.{DECIMAL_PLACES_PERCENTAGE}f}%"
            )
        with col_b:
            # Use 'vol' if available, otherwise 'vol_pct'
            vol_val = row.get('vol', row.get('vol_pct', 0))
            st.metric(
                "변동성",
                f"{vol_val:.{DECIMAL_PLACES_PERCENTAGE}f}%"
            )
        with col_c:
            st.metric(
                "종가",
                f"${row.get('close', 0):.{DECIMAL_PLACES_PRICE}f}"
            )

        # Display reason (from generate_signals, matches README Signal Rules format)
        reason = row.get('reason', '')
        if reason:
            if is_buy:
                st.info(f"📌 **추천 근거:** {reason}")
            else:
                st.warning(f"⚠️ **추천 근거:** {reason}")
        else:
            # Fallback: Extract reasons from metrics if 'reason' not available
            reasons = _recommendation_service.extract_recommendation_reasons(
                row, is_buy=is_buy
            )
            if reasons:
                reason_text = ', '.join(reasons)
                if is_buy:
                    st.info(f"📌 **추천 근거:** {reason_text}")
                else:
                    st.warning(f"⚠️ **추천 근거:** {reason_text}")
            else:
                if is_buy:
                    st.info("📌 추천 근거: 규칙 기반 매수 시그널")
                else:
                    st.warning("⚠️ 추천 근거: 규칙 기반 매도 시그널")

        st.markdown("---")


def render_top10_tables(
    rankings: Dict[str, DataFrame],
    n_top: int = 10,
) -> None:
    """Render Top 10 Gainers, Losers, and Volatility tables.

    Args:
        rankings: Dictionary with keys 'gainers', 'losers', 'volatile'.
        n_top: Number of top movers to display (default: 10).
    """
    st.header("📈 TOP 10 랭킹")

    col1, col2, col3 = st.columns(3)

    with col1:
        render_top_rankings_table(
            rankings.get('gainers', pd.DataFrame()),
            "📈 상승 TOP 10",
            'return' if 'return' in rankings.get('gainers', pd.DataFrame()).columns else 'return_pct',
            ascending=False,
        )

    with col2:
        render_top_rankings_table(
            rankings.get('losers', pd.DataFrame()),
            "📉 하락 TOP 10",
            'return' if 'return' in rankings.get('losers', pd.DataFrame()).columns else 'return_pct',
            ascending=True,
        )

    with col3:
        render_top_rankings_table(
            rankings.get('volatile', pd.DataFrame()),
            "📊 변동성 TOP 10",
            'vol' if 'vol' in rankings.get('volatile', pd.DataFrame()).columns else 'vol_pct',
            ascending=False,
        )


def render_buy_sell_candidates(
    buy_candidates: DataFrame,
    sell_candidates: DataFrame,
) -> None:
    """Render Buy and Sell Candidates cards.

    Args:
        buy_candidates: DataFrame with buy candidates (should contain 'reason' column).
        sell_candidates: DataFrame with sell candidates (should contain 'reason' column).
    """
    st.header("💡 매수/매도 후보")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 매수 후보")
        if not buy_candidates.empty:
            for idx, row in buy_candidates.iterrows():
                render_recommendation_card(row, is_buy=True)
        else:
            st.info("매수 후보가 없습니다.")

    with col2:
        st.subheader("⚠️ 매도 후보")
        if not sell_candidates.empty:
            for idx, row in sell_candidates.iterrows():
                render_recommendation_card(row, is_buy=False)
        else:
            st.info("매도 후보가 없습니다.")


def render_error_message(
    error_type: str,
    message: str = "",
    failed_symbols: list = None,
) -> None:
    """Render user-friendly error messages.

    Args:
        error_type: Type of error ('no_data', 'holiday', 'collection_failed', 'empty_result').
        message: Additional error message.
        failed_symbols: List of failed ticker symbols (optional).
    """
    if error_type == 'no_data':
        st.error("❌ **데이터 수집 실패**")
        st.warning(
            "시장 데이터를 수집할 수 없습니다. 다음을 확인해주세요:\n"
            "- 인터넷 연결 상태\n"
            "- 선택한 날짜가 거래일인지 확인 (주말/공휴일 제외)\n"
            "- 티커 심볼이 올바른지 확인"
        )
        if message:
            st.info(f"상세 정보: {message}")

    elif error_type == 'holiday':
        st.warning("⚠️ **휴장일 또는 주말**")
        st.info(
            "선택한 날짜는 거래일이 아닙니다. 가장 최근 거래일로 자동 조정됩니다.\n"
            "또는 다른 날짜를 선택해주세요."
        )
        if message:
            st.info(f"선택한 날짜: {message}")

    elif error_type == 'collection_failed':
        st.error("❌ **데이터 수집 부분 실패**")
        st.warning(f"일부 티커의 데이터 수집에 실패했습니다.")
        if failed_symbols:
            display_count = min(len(failed_symbols), 20)
            st.write(f"실패한 티커 ({len(failed_symbols)}개): {', '.join(failed_symbols[:display_count])}")
            if len(failed_symbols) > 20:
                st.write(f"... 및 {len(failed_symbols) - 20}개 더")
        if message:
            st.info(f"상세 정보: {message}")

    elif error_type == 'empty_result':
        st.warning("⚠️ **분석 결과 없음**")
        st.info(
            "선택한 조건에 맞는 종목이 없습니다. 다음을 시도해보세요:\n"
            "- 필터 조건 완화 (최소 수익률/변동성 조정)\n"
            "- 다른 날짜 선택\n"
            "- 티커 소스 변경"
        )
        if message:
            st.info(f"상세 정보: {message}")

    else:
        st.error(f"❌ **오류 발생**")
        if message:
            st.error(message)

