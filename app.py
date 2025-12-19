"""Enhanced Streamlit app for NASDAQ Daily Movers & Volatility Analyzer.

This is the main Streamlit application with simplified UI:
- Date selection (default: today/most recent trading day)
- Top 10 Gainers / Losers / Volatility tables
- Buy Candidates / Sell Candidates cards with reasons
- User-friendly error messages
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
from nasdaq_scanner.core.signal_generator import generate_signals
from nasdaq_scanner.ui.components import (
    render_top10_tables,
    render_buy_sell_candidates,
    render_error_message,
)
from nasdaq_scanner.config import (
    CACHE_TTL_SECONDS,
    DEFAULT_VOLATILITY_WINDOW,
    DEFAULT_TOP_N,
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

# Date selection (default: today, will use most recent trading day)
st.sidebar.subheader("📅 날짜 선택")
analysis_date = st.sidebar.date_input(
    "분석 날짜",
    value=date.today(),
    max_value=date.today(),
    help="분석할 날짜를 선택하세요. 주말/공휴일인 경우 가장 최근 거래일로 자동 조정됩니다."
)

# Volatility window (simplified, not shown in sidebar for cleaner UI)
volatility_window = DEFAULT_VOLATILITY_WINDOW

# Number of top movers
n_top = st.sidebar.slider(
    "TOP N 종목 수",
    min_value=5,
    max_value=20,
    value=DEFAULT_TOP_N,
    help="상승/하락/변동성 상위 N개 종목을 표시합니다"
)

# Refresh button
refresh_button = st.sidebar.button(
    "🔄 분석 실행",
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

        # Handle empty data (holiday/weekend/no data)
        if price_df.empty:
            if len(failed_symbols) > 0:
                # Some symbols failed, but might be holiday
                render_error_message(
                    'holiday',
                    message=f"선택한 날짜: {analysis_date.strftime('%Y-%m-%d')}",
                    failed_symbols=failed_symbols
                )
            else:
                # No data at all
                render_error_message(
                    'no_data',
                    message=f"선택한 날짜: {analysis_date.strftime('%Y-%m-%d')}"
                )
            st.stop()

        # Check if we got data but it's from a different date (holiday adjustment)
        actual_dates = price_df['date'].unique()
        if len(actual_dates) > 0 and actual_dates[0] != analysis_date:
            st.info(
                f"ℹ️ 선택한 날짜({analysis_date.strftime('%Y-%m-%d')})는 거래일이 아닙니다. "
                f"가장 최근 거래일({actual_dates[0]})의 데이터를 표시합니다."
            )

        # Compute metrics
        with st.spinner("📊 지표 계산 중..."):
            metrics_df = compute_metrics_cached(price_df, volatility_window)

        if metrics_df.empty:
            render_error_message('empty_result')
            st.stop()

        # Handle partial failures
        if failed_symbols:
            render_error_message(
                'collection_failed',
                failed_symbols=failed_symbols
            )

        # Store in session state
        st.session_state['metrics_df'] = metrics_df
        st.session_state['price_df'] = price_df
        st.session_state['failed_symbols'] = failed_symbols
        st.session_state['analysis_date'] = analysis_date

        st.success(f"✅ 분석 완료: {len(metrics_df)}개 종목 분석됨")
        st.markdown("---")

    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        logger.exception(e)
        st.stop()

# Display results if available
if 'metrics_df' in st.session_state and not st.session_state['metrics_df'].empty:
    metrics_df = st.session_state['metrics_df']
    price_df = st.session_state['price_df']
    analysis_date = st.session_state.get('analysis_date', date.today())

    # Display analysis date
    st.subheader(f"📅 분석 날짜: {analysis_date.strftime('%Y-%m-%d')}")
    st.markdown("---")

    # ========================================================================
    # TOP 10 Tables
    # ========================================================================
    rankings = _analytics_service.get_top_rankings(metrics_df, n=n_top)
    render_top10_tables(rankings, n_top=n_top)

    st.markdown("---")

    # ========================================================================
    # Buy/Sell Candidates
    # ========================================================================
    # Use generate_signals from core/signal_generator.py
    # This uses the exact rules from README Signal Rules section
    with st.spinner("💡 매수/매도 후보 생성 중..."):
        signals = generate_signals(metrics_df, top_n=n_top)

    render_buy_sell_candidates(
        buy_candidates=signals['buy_candidates'],
        sell_candidates=signals['sell_candidates'],
    )

    st.markdown("---")

    # ========================================================================
    # Signal Rules Info
    # ========================================================================
    with st.expander("📊 Signal Rules (시그널 규칙) 정보"):
        st.markdown("""
        ### Buy Signals (매수 시그널)
        
        **규칙:** 상위 상승 + 변동성 상위 교집합
        
        1. **상위 상승 종목 선정**: 일간 수익률(`return`) 기준 상위 N개 (기본: 10개)
        2. **변동성 상위 종목 선정**: 변동성 proxy(`vol`) 기준 상위 N개 (기본: 10개)
        3. **교집합 선택**: 두 집합에 모두 포함된 종목만 매수 시그널로 선정
        
        **Reason (추천 근거):** `"상위 상승(X.XX%) + 변동성 상위(X.XXXX) 교집합"`
        
        ### Sell Signals (매도 시그널)
        
        **규칙:** 하락 top10 중 변동성 상위
        
        1. **하락 종목 선정**: 일간 수익률(`return`)이 음수인 종목 중 하락률이 큰 순서로 상위 N개 (기본: 10개)
        2. **변동성 기준 재정렬**: 선정된 하락 종목 중 변동성(`vol`)이 높은 순서로 정렬
        3. **상위 M개 선택**: 변동성이 높은 순서로 상위 M개 선택 (기본: 10개)
        
        **Reason (추천 근거):** `"하락(-X.XX%) 상위 중 변동성 높음(X.XXXX)"`
        
        ### 주의사항
        
        - **투자 자문 아님**: 모든 시그널은 규칙 기반 자동 생성이며, 투자 판단의 참고용입니다.
        - **과거 데이터 기반**: 현재 시점의 데이터만 사용하며, 미래 성과를 보장하지 않습니다.
        - **리스크 고려**: 변동성이 높은 종목은 수익과 손실 모두 클 수 있습니다.
        - **자체 판단 필수**: 모든 투자 결정은 사용자의 판단과 책임 하에 이루어져야 합니다.
        """)

else:
    # Initial state
    st.info(
        "👈 왼쪽 사이드바에서 설정을 입력하고 '🔄 분석 실행' 버튼을 클릭하세요."
    )

    st.markdown("### 📋 사용 방법")
    st.markdown("""
    1. **티커 소스 선택**: NASDAQ-100, CSV 파일, 또는 직접 입력
    2. **날짜 선택**: 분석할 날짜 선택 (기본: 오늘, 주말/공휴일은 자동으로 가장 최근 거래일 사용)
    3. **TOP N 설정**: 상승/하락/변동성 상위 N개 종목 수 설정
    4. **분석 실행**: 데이터 수집 및 분석 실행

    ### 📊 제공 기능
    - **상승 TOP 10**: 일간 수익률 상위 종목
    - **하락 TOP 10**: 일간 하락률 상위 종목
    - **변동성 TOP 10**: 변동성 상위 종목
    - **매수/매도 후보**: 규칙 기반 추천 종목 및 근거 (README Signal Rules 참조)
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
