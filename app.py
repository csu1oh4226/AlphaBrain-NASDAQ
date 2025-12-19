"""Enhanced Streamlit app for NASDAQ Daily Movers & Volatility Analyzer.

This is the main Streamlit application with layered architecture:
- UI Layer: Streamlit components and user interaction
- Service Layer: Business logic orchestration
- Data Layer: Data collection and caching
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import sys
import logging
from typing import Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nasdaq_scanner.services.analytics_service import AnalyticsService
from nasdaq_scanner.services.recommendation_service import RecommendationService
from nasdaq_scanner.ui.components import (
    render_top_rankings_table,
    render_ticker_chart,
    render_recommendation_card,
    render_stats_metrics,
)
from nasdaq_scanner.config import (
    CACHE_TTL_SECONDS,
    DEFAULT_VOLATILITY_WINDOW,
    MIN_VOLATILITY_WINDOW,
    MAX_VOLATILITY_WINDOW,
    DEFAULT_MIN_RETURN_PCT,
    DEFAULT_MAX_RETURN_PCT,
    DEFAULT_MIN_VOL_PCT,
    MIN_RETURN_PCT_LIMIT,
    MAX_RETURN_PCT_LIMIT,
    MAX_VOL_PCT_LIMIT,
    DEFAULT_TOP_N,
    MIN_TOP_N,
    MAX_TOP_N,
    DEFAULT_RECOMMENDATION_COUNT,
    DEFAULT_DATE_RANGE_DAYS,
    MAX_FAILED_SYMBOLS_DISPLAY,
    TEMP_UNIVERSE_FILENAME,
    TICKER_SOURCE_NASDAQ100,
    TICKER_SOURCE_CSV,
    TICKER_SOURCE_MANUAL,
    DEFAULT_TICKER_INPUT,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
_analytics_service = AnalyticsService()
_recommendation_service = RecommendationService()

# Configure page
st.set_page_config(
    page_title="NASDAQ 주가 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("📊 NASDAQ Daily Movers & Volatility Analyzer")
st.markdown("---")

# ============================================================================
# Sidebar Configuration
# ============================================================================
st.sidebar.header("⚙️ 분석 설정")

# Ticker source selection
ticker_source_type = st.sidebar.radio(
    "티커 소스",
    options=[TICKER_SOURCE_NASDAQ100, TICKER_SOURCE_CSV, TICKER_SOURCE_MANUAL],
    help="데이터를 가져올 티커 소스를 선택하세요"
)

ticker_source: Optional[Any] = None
if ticker_source_type == TICKER_SOURCE_NASDAQ100:
    ticker_source = TICKER_SOURCE_NASDAQ100
elif ticker_source_type == TICKER_SOURCE_CSV:
    universe_file = st.sidebar.file_uploader(
        "티커 유니버스 파일 (CSV)",
        type=['csv'],
        help="symbol 컬럼을 포함한 CSV 파일을 업로드하세요"
    )
    if universe_file:
        temp_path = Path(TEMP_UNIVERSE_FILENAME)
        with open(temp_path, "wb") as f:
            f.write(universe_file.getbuffer())
        ticker_source = str(temp_path)
elif ticker_source_type == TICKER_SOURCE_MANUAL:
    ticker_input = st.sidebar.text_area(
        "티커 리스트 (쉼표로 구분)",
        value=DEFAULT_TICKER_INPUT,
        help="티커 심볼을 쉼표로 구분하여 입력하세요"
    )
    if ticker_input:
        ticker_source = [
            t.strip().upper() for t in ticker_input.split(",") if t.strip()
        ]

# Date range selection
st.sidebar.subheader("📅 날짜 범위")
use_date_range = st.sidebar.checkbox("날짜 범위 사용", value=False)

if use_date_range:
    start_date = st.sidebar.date_input(
        "시작 날짜",
        value=date.today() - timedelta(days=DEFAULT_DATE_RANGE_DAYS),
        max_value=date.today(),
    )
    end_date = st.sidebar.date_input(
        "종료 날짜",
        value=date.today(),
        max_value=date.today(),
    )
    if start_date > end_date:
        st.sidebar.error("시작 날짜는 종료 날짜보다 이전이어야 합니다.")
        st.stop()
    analysis_date = end_date
else:
    analysis_date = st.sidebar.date_input(
        "분석 날짜",
        value=date.today(),
        max_value=date.today(),
        help="분석할 날짜를 선택하세요"
    )

# Volatility window
st.sidebar.subheader("📊 변동성 설정")
volatility_window = st.sidebar.slider(
    "변동성 윈도우 (일)",
    min_value=MIN_VOLATILITY_WINDOW,
    max_value=MAX_VOLATILITY_WINDOW,
    value=DEFAULT_VOLATILITY_WINDOW,
    help="변동성 계산에 사용할 기간(일)을 설정하세요"
)

# Filters
st.sidebar.subheader("🔍 필터")
min_return_pct = st.sidebar.number_input(
    "최소 수익률 (%)",
    min_value=MIN_RETURN_PCT_LIMIT,
    max_value=MAX_RETURN_PCT_LIMIT,
    value=DEFAULT_MIN_RETURN_PCT,
    step=0.1,
    help="표시할 최소 수익률 필터"
)
max_return_pct = st.sidebar.number_input(
    "최대 수익률 (%)",
    min_value=MIN_RETURN_PCT_LIMIT,
    max_value=MAX_RETURN_PCT_LIMIT,
    value=DEFAULT_MAX_RETURN_PCT,
    step=0.1,
    help="표시할 최대 수익률 필터"
)
min_vol_pct = st.sidebar.number_input(
    "최소 변동성 (%)",
    min_value=0.0,
    max_value=MAX_VOL_PCT_LIMIT,
    value=DEFAULT_MIN_VOL_PCT,
    step=0.1,
    help="표시할 최소 변동성 필터"
)

# Number of top movers
n_top = st.sidebar.slider(
    "TOP N 종목 수",
    min_value=MIN_TOP_N,
    max_value=MAX_TOP_N,
    value=DEFAULT_TOP_N,
    help="상승/하락/변동성 상위 N개 종목을 표시합니다"
)

# Refresh button
refresh_button = st.sidebar.button(
    "🔄 새로고침",
    type="primary",
    use_container_width=True
)

# ============================================================================
# Cached Data Functions
# ============================================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS)
def fetch_market_data_cached(
    ticker_source: Any,
    target_date: date,
) -> tuple[pd.DataFrame, list[str]]:
    """Fetch market data with caching.

    Args:
        ticker_source: Source of ticker list.
        target_date: Target date for data collection.

    Returns:
        Tuple of (price DataFrame, failed symbols list).
    """
    try:
        return _analytics_service.collect_market_data(ticker_source, target_date)
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def compute_metrics_cached(
    price_df: pd.DataFrame,
    volatility_window: int,
) -> pd.DataFrame:
    """Compute metrics with caching.

    Args:
        price_df: DataFrame with price data.
        volatility_window: Window size for volatility calculation.

    Returns:
        DataFrame with computed metrics.
    """
    return _analytics_service.compute_metrics(price_df, volatility_window)


# ============================================================================
# Main Content
# ============================================================================

if refresh_button or st.session_state.get('auto_refresh', False):
    if ticker_source is None:
        st.error("❌ 티커 소스를 선택해주세요.")
        st.stop()

    try:
        # Fetch market data
        with st.spinner("📡 시장 데이터 수집 중..."):
            price_df, failed_symbols = fetch_market_data_cached(
                ticker_source, analysis_date
            )

        if price_df.empty:
            st.warning(
                "⚠️ 수집된 데이터가 없습니다. 날짜나 티커 소스를 확인해주세요."
            )
            st.stop()

        # Compute metrics
        with st.spinner("📊 지표 계산 중..."):
            metrics_df = compute_metrics_cached(price_df, volatility_window)

        if metrics_df.empty:
            st.warning("⚠️ 계산된 지표가 없습니다.")
            st.stop()

        # Apply filters
        filtered_df = _analytics_service.apply_filters(
            metrics_df, min_return_pct, max_return_pct, min_vol_pct
        )

        # Store in session state
        st.session_state['metrics_df'] = filtered_df
        st.session_state['price_df'] = price_df
        st.session_state['failed_symbols'] = failed_symbols

        # Display stats
        render_stats_metrics(
            total_tickers=len(metrics_df),
            filtered_count=len(filtered_df),
            successful_fetches=len(price_df['ticker'].unique()),
            failed_count=len(failed_symbols),
        )

        if failed_symbols:
            with st.expander("❌ 실패한 티커 목록"):
                display_count = min(len(failed_symbols), MAX_FAILED_SYMBOLS_DISPLAY)
                st.write(", ".join(failed_symbols[:display_count]))
                if len(failed_symbols) > MAX_FAILED_SYMBOLS_DISPLAY:
                    remaining = len(failed_symbols) - MAX_FAILED_SYMBOLS_DISPLAY
                    st.write(f"... 및 {remaining}개 더")

        st.markdown("---")

    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.exception(e)
        st.stop()

# Display results if available
if 'metrics_df' in st.session_state and not st.session_state['metrics_df'].empty:
    metrics_df = st.session_state['metrics_df']
    price_df = st.session_state['price_df']

    # ========================================================================
    # TOP 10 Tables
    # ========================================================================
    st.header("📈 TOP 10 랭킹")

    rankings = _analytics_service.get_top_rankings(metrics_df, n=n_top)

    col1, col2, col3 = st.columns(3)

    with col1:
        render_top_rankings_table(
            rankings['volatile'],
            "📊 변동성 TOP 10",
            'vol_pct',
            ascending=False,
        )

    with col2:
        render_top_rankings_table(
            rankings['gainers'],
            "📈 상승 TOP 10",
            'return_pct',
            ascending=False,
        )

    with col3:
        render_top_rankings_table(
            rankings['losers'],
            "📉 하락 TOP 10",
            'return_pct',
            ascending=True,
        )

    st.markdown("---")

    # ========================================================================
    # Selected Ticker Chart
    # ========================================================================
    st.header("📊 티커 상세 차트")

    available_tickers = sorted(metrics_df['ticker'].unique().tolist())

    if available_tickers:
        selected_ticker = st.selectbox(
            "티커 선택",
            options=available_tickers,
            index=0,
            help="차트를 표시할 티커를 선택하세요"
        )

        if selected_ticker:
            render_ticker_chart(selected_ticker, price_df, metrics_df)

    st.markdown("---")

    # ========================================================================
    # Recommendations Section
    # ========================================================================
    st.header("💡 추천 종목")

    try:
        with st.spinner("💡 추천 종목 생성 중..."):
            recommendations = _recommendation_service.generate_recommendations(
                metrics_df, max_count=DEFAULT_RECOMMENDATION_COUNT
            )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💰 매수 추천 (TOP 5)")
            buy_df = recommendations['buy']
            if not buy_df.empty:
                for idx, row in buy_df.iterrows():
                    render_recommendation_card(row, is_buy=True)
            else:
                st.info("매수 추천 종목이 없습니다.")

        with col2:
            st.subheader("⚠️ 매도 추천 (TOP 5)")
            sell_df = recommendations['sell']
            if not sell_df.empty:
                for idx, row in sell_df.iterrows():
                    render_recommendation_card(row, is_buy=False)
            else:
                st.info("매도 추천 종목이 없습니다.")

    except Exception as e:
        st.error(f"추천 생성 중 오류: {str(e)}")
        logger.exception(e)

else:
    # Initial state
    st.info(
        "👈 왼쪽 사이드바에서 설정을 입력하고 '🔄 새로고침' 버튼을 클릭하세요."
    )

    st.markdown("### 📋 사용 방법")
    st.markdown("""
    1. **티커 소스 선택**: NASDAQ-100, CSV 파일, 또는 직접 입력
    2. **날짜 범위 설정**: 단일 날짜 또는 날짜 범위 선택
    3. **변동성 윈도우 설정**: 변동성 계산 기간 설정
    4. **필터 설정**: 수익률 및 변동성 필터 적용
    5. **새로고침**: 데이터 수집 및 분석 실행

    ### 📊 제공 기능
    - **변동성 TOP 10**: 변동성 상위 종목
    - **상승 TOP 10**: 수익률 상위 종목
    - **하락 TOP 10**: 하락률 상위 종목
    - **티커 상세 차트**: 선택한 티커의 가격 및 수익률 차트
    - **매수/매도 추천**: 규칙 기반 추천 종목 및 근거
    """)

    st.markdown("### ⚠️ 면책 조항")
    st.markdown("""
    이 도구는 투자 자문이 아닙니다. 모든 분석 결과는 참고용이며,
    투자 결정은 사용자의 판단에 따라 이루어져야 합니다.
    """)

# Clean up temp file if exists
temp_path = Path(TEMP_UNIVERSE_FILENAME)
if temp_path.exists():
    try:
        temp_path.unlink()
    except Exception:
        pass
