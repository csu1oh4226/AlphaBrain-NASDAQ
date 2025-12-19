"""Enhanced Streamlit app for KOSDAQ Daily Movers & Volatility Analyzer.

This is the main Streamlit application with robust error handling and user feedback:
- FinanceDataReader for KOSDAQ data (KQ11 index and individual stocks)
- Individual sequential ticker requests to avoid rate limiting
- Status display (total/success/failed tickers)
- Failure reason summary
- Retry button for failed tickers
- Observation stocks TOP5 and Warning stocks TOP5
- Comprehensive logging and debugging
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import sys
import logging
from typing import Any, Optional, Dict, List
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nasdaq_scanner.services.analytics_service import AnalyticsService
from nasdaq_scanner.core.stock_name_mapper import add_stock_names_to_dataframe
from nasdaq_scanner.config import (
    CACHE_TTL_SECONDS,
    DEFAULT_VOLATILITY_WINDOW,
    DEFAULT_TOP_N,
    TEMP_UNIVERSE_FILENAME,
    TICKER_SOURCE_KOSPI_INDEX,
    TICKER_SOURCE_KOSPI_TOP,
    TICKER_SOURCE_KOSDAQ_INDEX,
    TICKER_SOURCE_KOSDAQ_TOP,
    TICKER_SOURCE_CSV,
    TICKER_SOURCE_MANUAL,
    DEFAULT_TICKER_INPUT,
    MAX_FAILED_SYMBOLS_DISPLAY,
    DECIMAL_PLACES_PRICE,
    DECIMAL_PLACES_PERCENTAGE,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Initialize services
_analytics_service = AnalyticsService()

# Configure page
st.set_page_config(
    page_title="ALPHABRAIN KOSDAQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("📊 ALPHABRAIN KOSDAQ")
st.markdown("---")

# ============================================================================
# Sidebar Configuration
# ============================================================================
st.sidebar.header("⚙️ 분석 설정")

# Debug mode
debug_mode = st.sidebar.checkbox("🔍 디버그 모드", value=False, help="상세한 로그를 표시합니다")

# Market selection
market_type = st.sidebar.radio(
    "시장 선택",
    options=["KOSPI", "KOSDAQ"],
    help="분석할 시장을 선택하세요"
)

# Ticker source selection
ticker_source_type = st.sidebar.radio(
    "티커 소스",
    options=["지수", "상위 종목", TICKER_SOURCE_CSV, TICKER_SOURCE_MANUAL],
    help="데이터를 가져올 티커 소스를 선택하세요"
)

ticker_source: Optional[Any] = None
total_tickers = 0

if ticker_source_type == "지수":
    if market_type == "KOSPI":
        ticker_source = TICKER_SOURCE_KOSPI_INDEX
        total_tickers = 1
        st.sidebar.info("📊 KOSPI 종합지수(KS11) 데이터를 분석합니다.")
    else:  # KOSDAQ
        ticker_source = TICKER_SOURCE_KOSDAQ_INDEX
        total_tickers = 1
        st.sidebar.info("📊 KOSDAQ 종합지수(KQ11) 데이터를 분석합니다.")
elif ticker_source_type == "상위 종목":
    if market_type == "KOSPI":
        ticker_source = TICKER_SOURCE_KOSPI_TOP
        total_tickers = 100
        st.sidebar.info("📊 KOSPI 시가총액 상위 종목을 분석합니다.")
    else:  # KOSDAQ
        ticker_source = TICKER_SOURCE_KOSDAQ_TOP
        total_tickers = 100
        st.sidebar.info("📊 KOSDAQ 시가총액 상위 종목을 분석합니다.")
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
        # Try to count tickers from CSV
        try:
            df_temp = pd.read_csv(temp_path)
            total_tickers = len(df_temp) if 'symbol' in df_temp.columns else len(df_temp)
        except:
            total_tickers = 0
elif ticker_source_type == TICKER_SOURCE_MANUAL:
    ticker_input = st.sidebar.text_area(
        "티커 리스트 (쉼표로 구분)",
        value=DEFAULT_TICKER_INPUT,
        help="티커 심볼을 쉼표로 구분하여 입력하세요"
    )
    if ticker_input:
        ticker_list = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
        ticker_source = ticker_list
        total_tickers = len(ticker_list)

# Date selection
st.sidebar.subheader("📅 날짜 선택")
analysis_date = st.sidebar.date_input(
    "분석 날짜",
    value=date.today(),
    max_value=date.today(),
    help="분석할 날짜를 선택하세요. 주말/공휴일인 경우 가장 최근 거래일로 자동 조정됩니다."
)

# Number of top movers
n_top = st.sidebar.slider(
    "TOP N 종목 수",
    min_value=5,
    max_value=20,
    value=DEFAULT_TOP_N,
    help="상승/하락/변동성 상위 N개 종목을 표시합니다"
)

# Run Analysis button
run_button = st.sidebar.button(
    "🚀 분석 실행",
    type="primary",
    use_container_width=True
)

# ============================================================================
# Helper Functions
# ============================================================================

def categorize_failures(failed_symbols: List[str], failure_reasons: Dict[str, str]) -> Dict[str, List[str]]:
    """Categorize failed symbols by failure reason.
    
    Args:
        failed_symbols: List of failed ticker symbols.
        failure_reasons: Dictionary mapping symbols to failure reasons.
    
    Returns:
        Dictionary with categorized failures.
    """
    categories = {
        'rate_limit': [],
        'network': [],
        'invalid': [],
        'no_data': [],
        'other': [],
    }
    
    for symbol in failed_symbols:
        reason = failure_reasons.get(symbol, 'other')
        if 'rate limit' in reason.lower() or '429' in reason:
            categories['rate_limit'].append(symbol)
        elif 'network' in reason.lower() or 'timeout' in reason.lower():
            categories['network'].append(symbol)
        elif 'invalid' in reason.lower() or 'not found' in reason.lower():
            categories['invalid'].append(symbol)
        elif 'no data' in reason.lower():
            categories['no_data'].append(symbol)
        else:
            categories['other'].append(symbol)
    
    return categories


def render_status_metrics(total: int, success: int, failed: int) -> None:
    """Render status metrics at the top of the page.
    
    Args:
        total: Total number of tickers.
        success: Number of successful fetches.
        failed: Number of failed fetches.
    """
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 티커", total, delta=None)
    with col2:
        st.metric("수집 성공", success, delta=f"{success/total*100:.1f}%" if total > 0 else None)
    with col3:
        st.metric("수집 실패", failed, delta=f"-{failed/total*100:.1f}%" if total > 0 else None)


def render_failure_summary(failed_symbols: List[str], failure_reasons: Dict[str, str]) -> None:
    """Render failure summary with categorized reasons.
    
    Args:
        failed_symbols: List of failed ticker symbols.
        failure_reasons: Dictionary mapping symbols to failure reasons.
    """
    if not failed_symbols:
        return
    
    categories = categorize_failures(failed_symbols, failure_reasons)
    
    st.subheader("⚠️ 데이터 수집 실패 요약")
    
    # Summary boxes
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if categories['rate_limit']:
            st.error(f"Rate Limit: {len(categories['rate_limit'])}")
    with col2:
        if categories['network']:
            st.error(f"Network: {len(categories['network'])}")
    with col3:
        if categories['invalid']:
            st.warning(f"Invalid: {len(categories['invalid'])}")
    with col4:
        if categories['no_data']:
            st.info(f"No Data: {len(categories['no_data'])}")
    with col5:
        if categories['other']:
            st.warning(f"Other: {len(categories['other'])}")
    
    # Failed tickers list (collapsible)
    with st.expander(f"실패한 티커 목록 ({len(failed_symbols)}개)", expanded=False):
        display_count = min(len(failed_symbols), MAX_FAILED_SYMBOLS_DISPLAY)
        for symbol in failed_symbols[:display_count]:
            reason = failure_reasons.get(symbol, 'Unknown')
            st.text(f"{symbol}: {reason}")
        if len(failed_symbols) > MAX_FAILED_SYMBOLS_DISPLAY:
            st.text(f"... 및 {len(failed_symbols) - MAX_FAILED_SYMBOLS_DISPLAY}개 더")


def render_recommendations(observations: pd.DataFrame, warnings: pd.DataFrame) -> None:
    """Render observation and warning stocks.
    
    Args:
        observations: DataFrame with observation stocks (high return + high volatility).
        warnings: DataFrame with warning stocks (sharp decline + high volatility).
    """
    st.header("💡 데이터 기반 관찰 (투자 조언 아님)")
    
    # Get market type from session state
    market_type_display = st.session_state.get('market_type', 'KOSDAQ')
    
    # Helper function to format numbers with commas
    def format_number(value):
        """Format number with thousand separators."""
        if pd.isna(value):
            return value
        try:
            if isinstance(value, (int, float)):
                return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
            return str(value)
        except:
            return value
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 관찰 종목 TOP 5")
        if not observations.empty:
            # Add stock names
            display_df = add_stock_names_to_dataframe(observations.head(5), market=market_type_display)
            
            for idx, row in display_df.iterrows():
                with st.container():
                    # Display stock name with ticker
                    stock_name = row.get('name', row['ticker'])
                    if pd.notna(stock_name) and stock_name != row['ticker']:
                        display_name = f"{stock_name} ({row['ticker']})"
                    else:
                        display_name = row['ticker']
                    
                    st.markdown(f"### {display_name}")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("수익률", f"{row['return']:.{DECIMAL_PLACES_PERCENTAGE}f}%")
                    with col_b:
                        st.metric("변동성", f"{row['vol']:.{DECIMAL_PLACES_PERCENTAGE}f}%")
                    with col_c:
                        close_formatted = format_number(row['close'])
                        st.metric("종가", f"₩{close_formatted}")
                    st.info(f"**관찰 근거:** 상승률 {row['return']:.2f}% + 변동성 {row['vol']:.2f}%")
                    st.markdown("---")
        else:
            st.info("관찰 종목이 없습니다.")
    
    with col2:
        st.subheader("⚠️ 주의 종목 TOP 5")
        if not warnings.empty:
            # Add stock names
            display_df = add_stock_names_to_dataframe(warnings.head(5), market=market_type_display)
            
            for idx, row in display_df.iterrows():
                with st.container():
                    # Display stock name with ticker
                    stock_name = row.get('name', row['ticker'])
                    if pd.notna(stock_name) and stock_name != row['ticker']:
                        display_name = f"{stock_name} ({row['ticker']})"
                    else:
                        display_name = row['ticker']
                    
                    st.markdown(f"### {display_name}")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("수익률", f"{row['return']:.{DECIMAL_PLACES_PERCENTAGE}f}%")
                    with col_b:
                        st.metric("변동성", f"{row['vol']:.{DECIMAL_PLACES_PERCENTAGE}f}%")
                    with col_c:
                        close_formatted = format_number(row['close'])
                        st.metric("종가", f"₩{close_formatted}")
                    st.warning(f"**주의 근거:** 하락률 {row['return']:.2f}% + 변동성 {row['vol']:.2f}%")
                    st.markdown("---")
        else:
            st.info("주의 종목이 없습니다.")
    
    # Disclaimer
    st.warning("""
    **⚠️ 면책 조항:**
    
    - 이 분석은 **데이터 기반 관찰**이며, **투자 조언이 아닙니다**.
    - 모든 투자 결정은 사용자의 판단과 책임 하에 이루어져야 합니다.
    - 과거 데이터 기반이며, 미래 성과를 보장하지 않습니다.
    - 변동성이 높은 종목은 수익과 손실 모두 클 수 있습니다.
    """)


# ============================================================================
# Main Content
# ============================================================================

if run_button:
    if ticker_source is None:
        st.error("❌ 티커 소스를 선택해주세요.")
        st.stop()

    # Store market type in session state
    st.session_state['market_type'] = market_type

    # Initialize session state for failure tracking
    if 'failure_reasons' not in st.session_state:
        st.session_state['failure_reasons'] = {}

    try:
        # Fetch market data
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if ticker_source in [TICKER_SOURCE_KOSPI_INDEX, TICKER_SOURCE_KOSDAQ_INDEX]:
            market_name = "KOSPI" if ticker_source == TICKER_SOURCE_KOSPI_INDEX else "KOSDAQ"
            status_text.text(f"📡 {market_name} 지수 데이터 수집 중...")
        elif ticker_source in [TICKER_SOURCE_KOSPI_TOP, TICKER_SOURCE_KOSDAQ_TOP]:
            market_name = "KOSPI" if ticker_source == TICKER_SOURCE_KOSPI_TOP else "KOSDAQ"
            status_text.text(f"📡 {market_name} 종목 데이터 수집 중... (개별 순차 요청)")
        else:
            status_text.text("📡 시장 데이터 수집 중... (개별 순차 요청, 각 요청 사이 0.3-0.7초 대기)")
        
        if debug_mode:
            logger.info(f"Starting data collection for {ticker_source} on {analysis_date}")
        
        price_df, failed_symbols = _analytics_service.collect_market_data(
            ticker_source, analysis_date
        )
        
        progress_bar.progress(1.0)
        status_text.empty()

        # Calculate statistics
        success_count = len(price_df) if not price_df.empty else 0
        failed_count = len(failed_symbols)
        actual_total = success_count + failed_count

        # Display status metrics
        render_status_metrics(actual_total, success_count, failed_count)

        # Handle empty data
        if price_df.empty:
            st.error("❌ **데이터 수집 실패**")
            st.warning(
                "시장 데이터를 수집할 수 없습니다. 다음을 확인해주세요:\n"
                "- 인터넷 연결 상태\n"
                "- 선택한 날짜가 거래일인지 확인 (주말/공휴일 제외)\n"
                "- 티커 심볼이 올바른지 확인"
            )
            
            if failed_symbols:
                render_failure_summary(failed_symbols, st.session_state.get('failure_reasons', {}))
                
                # Retry button
                if st.button("🔄 실패한 티커만 재시도", type="primary"):
                    st.session_state['retry_failed'] = True
                    st.rerun()
            
            st.stop()

        # Check if date was adjusted (holiday/weekend)
        actual_dates = price_df['date'].unique()
        if len(actual_dates) > 0:
            actual_date = actual_dates[0]
            if isinstance(actual_date, pd.Timestamp):
                actual_date = actual_date.date()
            elif isinstance(actual_date, str):
                actual_date = pd.to_datetime(actual_date).date()
            elif hasattr(actual_date, 'date') and callable(getattr(actual_date, 'date')):
                actual_date = actual_date.date()
            
            if isinstance(actual_date, date) and actual_date != analysis_date:
                st.info(
                    f"ℹ️ 선택한 날짜({analysis_date.strftime('%Y-%m-%d')})는 거래일이 아닙니다. "
                    f"가장 최근 거래일({actual_date.strftime('%Y-%m-%d')})의 데이터를 표시합니다."
                )

        # Display failure summary if any
        if failed_symbols:
            render_failure_summary(failed_symbols, st.session_state.get('failure_reasons', {}))
            
            # Retry button
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔄 실패한 티커만 재시도", type="secondary"):
                    st.session_state['retry_failed'] = True
                    st.rerun()

        # Compute metrics
        with st.spinner("📊 지표 계산 중..."):
            metrics_df = _analytics_service.compute_metrics(price_df, volatility_window=DEFAULT_VOLATILITY_WINDOW)

        if metrics_df.empty:
            st.warning("⚠️ **분석 결과 없음**")
            st.info("선택한 조건에 맞는 종목이 없습니다.")
            
            # Debug information
            if debug_mode:
                with st.expander("🔍 디버그: 수집된 데이터 확인"):
                    st.write(f"수집된 데이터 행 수: {len(price_df)}")
                    st.write(f"컬럼: {list(price_df.columns)}")
                    if not price_df.empty:
                        st.dataframe(price_df.head(10))
                        st.write("데이터 타입:")
                        st.write(price_df.dtypes)
                        # Check for NaN or invalid values
                        st.write("NaN 값 확인:")
                        st.write(price_df.isna().sum())
                        # Check sample values
                        st.write("샘플 데이터:")
                        st.write(price_df[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']].head())
            
            st.stop()

        # Get rankings
        with st.spinner("📈 랭킹 생성 중..."):
            rankings = _analytics_service.get_top_rankings(metrics_df, n=n_top)

        # Get recommendations (buy/sell signals)
        with st.spinner("💡 매수/매도 시그널 생성 중..."):
            recommendations = _analytics_service.get_recommendations(metrics_df, top_n=n_top)

        # Store in session state
        st.session_state['metrics_df'] = metrics_df
        st.session_state['price_df'] = price_df
        st.session_state['failed_symbols'] = failed_symbols
        st.session_state['analysis_date'] = analysis_date
        st.session_state['rankings'] = rankings
        st.session_state['recommendations'] = recommendations

        st.success(f"✅ 분석 완료: {len(metrics_df)}개 종목 분석됨")
        st.markdown("---")

    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        if debug_mode:
            st.exception(e)
        logger.exception(e)
        st.stop()

# Display results if available
if 'metrics_df' in st.session_state and not st.session_state['metrics_df'].empty:
    metrics_df = st.session_state['metrics_df']
    price_df = st.session_state['price_df']
    analysis_date = st.session_state.get('analysis_date', date.today())
    rankings = st.session_state.get('rankings', {})
    recommendations = st.session_state.get('recommendations', {})
    failed_symbols = st.session_state.get('failed_symbols', [])
    
    # Get market type from session state or default to KOSDAQ
    market_type_display = st.session_state.get('market_type', 'KOSDAQ')

    # Display analysis date
    st.subheader(f"📅 분석 날짜: {analysis_date.strftime('%Y-%m-%d')}")
    st.markdown("---")

    # Helper function to format numbers with commas
    def format_number(value):
        """Format number with thousand separators."""
        if pd.isna(value):
            return value
        try:
            if isinstance(value, (int, float)):
                return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
            return str(value)
        except:
            return value

    # Helper function to prepare dataframe for display
    def prepare_display_df(df, include_name=True):
        """Prepare dataframe for display with stock names and formatted numbers."""
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # Add stock names
        if include_name and 'ticker' in result_df.columns:
            result_df = add_stock_names_to_dataframe(result_df, market=market_type_display)
            # Create display column: "종목명 (티커)"
            if 'name' in result_df.columns:
                result_df['종목명'] = result_df.apply(
                    lambda row: f"{row['name']} ({row['ticker']})" if pd.notna(row.get('name')) else row['ticker'],
                    axis=1
                )
            else:
                result_df['종목명'] = result_df['ticker']
        
        # Format numbers
        if 'close' in result_df.columns:
            result_df['close'] = result_df['close'].apply(format_number)
        if 'volume' in result_df.columns:
            result_df['volume'] = result_df['volume'].apply(format_number)
        
        return result_df

    # ========================================================================
    # TOP N Tables
    # ========================================================================
    st.header("📈 TOP N 랭킹")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📈 상승 TOP 10")
        if not rankings.get('gainers', pd.DataFrame()).empty:
            gainers_df = rankings['gainers'].head(10)
            display_df = prepare_display_df(gainers_df)
            
            display_cols = ['종목명', 'return', 'vol', 'close', 'volume']
            available_cols = [c for c in display_cols if c in display_df.columns]
            st.dataframe(
                display_df[available_cols].rename(columns={
                    '종목명': '종목명',
                    'return': '수익률 (%)',
                    'vol': '변동성 (%)',
                    'close': '종가',
                    'volume': '거래량'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("데이터가 없습니다.")
    
    with col2:
        st.subheader("📉 하락 TOP 10")
        if not rankings.get('losers', pd.DataFrame()).empty:
            losers_df = rankings['losers'].head(10)
            display_df = prepare_display_df(losers_df)
            
            display_cols = ['종목명', 'return', 'vol', 'close']
            available_cols = [c for c in display_cols if c in display_df.columns]
            st.dataframe(
                display_df[available_cols].rename(columns={
                    '종목명': '종목명',
                    'return': '수익률 (%)',
                    'vol': '변동성 (%)',
                    'close': '종가'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("데이터가 없습니다.")
    
    with col3:
        st.subheader("⚠️ 변동성 상위 종목")
        if not rankings.get('volatile', pd.DataFrame()).empty:
            volatile_df = rankings['volatile'].head(10)
            display_df = prepare_display_df(volatile_df)
            
            display_cols = ['종목명', 'vol', 'return', 'close']
            available_cols = [c for c in display_cols if c in display_df.columns]
            st.dataframe(
                display_df[available_cols].rename(columns={
                    '종목명': '종목명',
                    'vol': '변동성 (%)',
                    'return': '수익률 (%)',
                    'close': '종가'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("데이터가 없습니다.")

    st.markdown("---")

    # ========================================================================
    # Recommendations
    # ========================================================================
    render_recommendations(
        recommendations.get('observations', pd.DataFrame()),
        recommendations.get('warnings', pd.DataFrame())
    )

    st.markdown("---")

    # ========================================================================
    # Debug Information
    # ========================================================================
    if debug_mode:
        with st.expander("🔍 디버그 정보"):
            st.subheader("수집된 데이터")
            st.dataframe(price_df.head(10))
            st.subheader("계산된 지표")
            st.dataframe(metrics_df.head(10))
            if failed_symbols:
                st.subheader("실패한 티커")
                st.write(failed_symbols)

else:
    # Initial state
    st.info(
        "👈 왼쪽 사이드바에서 설정을 입력하고 '🚀 분석 실행' 버튼을 클릭하세요."
    )

    st.markdown("### 📋 사용 방법")
    st.markdown("""
    1. **티커 소스 선택**: KOSPI/KOSDAQ 지수, 상위 종목, CSV 파일, 또는 직접 입력
    2. **날짜 선택**: 분석할 날짜 선택 (기본: 오늘, 주말/공휴일은 자동으로 가장 최근 거래일 사용)
    3. **TOP N 설정**: 상승/하락/변동성 상위 N개 종목 수 설정
    4. **분석 실행**: 데이터 수집 및 분석 실행

    ### 📊 제공 기능
    - **상승 TOP N**: 일간 수익률 상위 종목
    - **하락 TOP N**: 일간 하락률 상위 종목
    - **변동성 TOP N**: 변동성 상위 종목
    - **관찰 종목 TOP 5**: 상승률 + 변동성 상위 교집합
    - **주의 종목 TOP 5**: 급락 + 고변동성 종목
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
