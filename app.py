"""Enhanced Streamlit app for NASDAQ Daily Movers & Volatility Analyzer.

This is the main Streamlit application with enhanced features:
- Date range selection
- Volatility window configuration
- Filters
- Caching for performance
- Interactive charts
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path
import sys
import logging
from typing import Dict, Any, List, Tuple, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nasdaq_scanner.providers import collect_data, load_ticker_list
from nasdaq_scanner.core.analytics import (
    compute_daily_returns,
    compute_volatility,
    top_movers,
    recommend_trades,
)
from nasdaq_scanner.core.metrics import calc_return_pct, calc_intraday_vol_pct
from nasdaq_scanner.core.recommender import format_reasons

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    options=["NASDAQ-100", "CSV 파일", "직접 입력"],
    help="데이터를 가져올 티커 소스를 선택하세요"
)

ticker_source = None
if ticker_source_type == "NASDAQ-100":
    ticker_source = "nasdaq-100"
elif ticker_source_type == "CSV 파일":
    universe_file = st.sidebar.file_uploader(
        "티커 유니버스 파일 (CSV)",
        type=['csv'],
        help="symbol 컬럼을 포함한 CSV 파일을 업로드하세요"
    )
    if universe_file:
        # Save temporarily
        temp_path = Path("temp_universe.csv")
        with open(temp_path, "wb") as f:
            f.write(universe_file.getbuffer())
        ticker_source = str(temp_path)
elif ticker_source_type == "직접 입력":
    ticker_input = st.sidebar.text_area(
        "티커 리스트 (쉼표로 구분)",
        value="AAPL, MSFT, GOOGL, AMZN, TSLA",
        help="티커 심볼을 쉼표로 구분하여 입력하세요"
    )
    if ticker_input:
        ticker_source = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Date range selection
st.sidebar.subheader("📅 날짜 범위")
use_date_range = st.sidebar.checkbox("날짜 범위 사용", value=False)

if use_date_range:
    start_date = st.sidebar.date_input(
        "시작 날짜",
        value=date.today() - timedelta(days=30),
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
    analysis_date = end_date  # Use end date for analysis
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
    min_value=1,
    max_value=30,
    value=5,
    help="변동성 계산에 사용할 기간(일)을 설정하세요"
)

# Filters
st.sidebar.subheader("🔍 필터")
min_return_pct = st.sidebar.number_input(
    "최소 수익률 (%)",
    min_value=-100.0,
    max_value=100.0,
    value=-100.0,
    step=0.1,
    help="표시할 최소 수익률 필터"
)
max_return_pct = st.sidebar.number_input(
    "최대 수익률 (%)",
    min_value=-100.0,
    max_value=100.0,
    value=100.0,
    step=0.1,
    help="표시할 최대 수익률 필터"
)
min_vol_pct = st.sidebar.number_input(
    "최소 변동성 (%)",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=0.1,
    help="표시할 최소 변동성 필터"
)

# Number of top movers
n_top = st.sidebar.slider(
    "TOP N 종목 수",
    min_value=5,
    max_value=20,
    value=10,
    help="상승/하락/변동성 상위 N개 종목을 표시합니다"
)

# Refresh button
refresh_button = st.sidebar.button("🔄 새로고침", type="primary", use_container_width=True)

# ============================================================================
# Cached Data Functions
# ============================================================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_market_data_cached(
    ticker_source: Any,
    target_date: date,
) -> Tuple[pd.DataFrame, List[str]]:
    """Fetch market data with caching."""
    try:
        df, failed = collect_data(ticker_source, target_date, max_retries=2)
        return df, failed
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise


@st.cache_data(ttl=3600)
def compute_metrics_cached(
    price_df: pd.DataFrame,
    volatility_window: int,
) -> pd.DataFrame:
    """Compute metrics with caching."""
    if price_df.empty:
        return pd.DataFrame()
    
    # Group by ticker and compute metrics
    results = []
    
    for ticker in price_df['ticker'].unique():
        ticker_data = price_df[price_df['ticker'] == ticker].sort_values('date')
        
        if len(ticker_data) < 2:
            continue
        
        # Compute daily returns
        returns = compute_daily_returns(ticker_data['close'])
        
        # Compute volatility
        volatility = compute_volatility(returns, volatility_window)
        
        # Get latest values
        latest = ticker_data.iloc[-1]
        latest_return = returns.iloc[-1] if not pd.isna(returns.iloc[-1]) else 0.0
        latest_volatility = volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else 0.0
        
        # Calculate intraday volatility (if we have high/low data)
        # For now, use close price range
        if len(ticker_data) >= 2:
            price_range = ticker_data['close'].max() - ticker_data['close'].min()
            vol_pct = (price_range / ticker_data['close'].iloc[0]) * 100 if ticker_data['close'].iloc[0] > 0 else 0.0
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
            price_df, failed_symbols = fetch_market_data_cached(ticker_source, analysis_date)
        
        if price_df.empty:
            st.warning("⚠️ 수집된 데이터가 없습니다. 날짜나 티커 소스를 확인해주세요.")
            st.stop()
        
        # Compute metrics
        with st.spinner("📊 지표 계산 중..."):
            metrics_df = compute_metrics_cached(price_df, volatility_window)
        
        if metrics_df.empty:
            st.warning("⚠️ 계산된 지표가 없습니다.")
            st.stop()
        
        # Apply filters
        filtered_df = metrics_df[
            (metrics_df['return_pct'] >= min_return_pct) &
            (metrics_df['return_pct'] <= max_return_pct) &
            (metrics_df['vol_pct'] >= min_vol_pct)
        ].copy()
        
        # Store in session state
        st.session_state['metrics_df'] = filtered_df
        st.session_state['price_df'] = price_df
        st.session_state['failed_symbols'] = failed_symbols
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("전체 티커", len(metrics_df))
        with col2:
            st.metric("필터링 후", len(filtered_df))
        with col3:
            st.metric("수집 성공", len(price_df['ticker'].unique()))
        with col4:
            st.metric("수집 실패", len(failed_symbols))
        
        if failed_symbols:
            with st.expander("❌ 실패한 티커 목록"):
                st.write(", ".join(failed_symbols[:20]))
                if len(failed_symbols) > 20:
                    st.write(f"... 및 {len(failed_symbols) - 20}개 더")
        
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 변동성 TOP 10")
        volatile_top = top_movers(metrics_df, n=n_top, direction='up')
        if not volatile_top.empty:
            # Sort by vol_pct descending
            volatile_top = volatile_top.sort_values('vol_pct', ascending=False).head(n_top)
            display_cols = ['ticker', 'vol_pct', 'return_pct', 'close', 'volume']
            available_cols = [c for c in display_cols if c in volatile_top.columns]
            st.dataframe(
                volatile_top[available_cols].rename(columns={
                    'ticker': '티커',
                    'vol_pct': '변동성 (%)',
                    'return_pct': '수익률 (%)',
                    'close': '종가',
                    'volume': '거래량'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("변동성 데이터가 없습니다.")
    
    with col2:
        st.subheader("📈 상승 TOP 10")
        gainers_top = top_movers(metrics_df, n=n_top, direction='up')
        if not gainers_top.empty:
            # Sort by return_pct descending
            gainers_top = gainers_top.sort_values('return_pct', ascending=False).head(n_top)
            display_cols = ['ticker', 'return_pct', 'vol_pct', 'close', 'volume']
            available_cols = [c for c in display_cols if c in gainers_top.columns]
            st.dataframe(
                gainers_top[available_cols].rename(columns={
                    'ticker': '티커',
                    'return_pct': '수익률 (%)',
                    'vol_pct': '변동성 (%)',
                    'close': '종가',
                    'volume': '거래량'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("상승 종목 데이터가 없습니다.")
    
    with col3:
        st.subheader("📉 하락 TOP 10")
        losers_top = top_movers(metrics_df, n=n_top, direction='down')
        if not losers_top.empty:
            # Sort by return_pct ascending
            losers_top = losers_top.sort_values('return_pct', ascending=True).head(n_top)
            display_cols = ['ticker', 'return_pct', 'vol_pct', 'close', 'volume']
            available_cols = [c for c in display_cols if c in losers_top.columns]
            st.dataframe(
                losers_top[available_cols].rename(columns={
                    'ticker': '티커',
                    'return_pct': '수익률 (%)',
                    'vol_pct': '변동성 (%)',
                    'close': '종가',
                    'volume': '거래량'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("하락 종목 데이터가 없습니다.")
    
    st.markdown("---")
    
    # ========================================================================
    # Selected Ticker Chart
    # ========================================================================
    st.header("📊 티커 상세 차트")
    
    # Get all available tickers
    available_tickers = sorted(metrics_df['ticker'].unique().tolist())
    
    if available_tickers:
        selected_ticker = st.selectbox(
            "티커 선택",
            options=available_tickers,
            index=0,
            help="차트를 표시할 티커를 선택하세요"
        )
        
        if selected_ticker:
            ticker_price_data = price_df[price_df['ticker'] == selected_ticker].sort_values('date')
            
            if not ticker_price_data.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"💰 {selected_ticker} 가격 차트")
                    price_chart_data = ticker_price_data[['date', 'close']].set_index('date')
                    st.line_chart(price_chart_data)
                
                with col2:
                    st.subheader(f"📈 {selected_ticker} 수익률 차트")
                    # Calculate returns
                    returns = compute_daily_returns(ticker_price_data['close'])
                    returns_df = pd.DataFrame({
                        'date': ticker_price_data['date'].values,
                        'return_pct': returns.values
                    }).set_index('date')
                    st.line_chart(returns_df)
                
                # Display metrics for selected ticker
                ticker_metrics = metrics_df[metrics_df['ticker'] == selected_ticker]
                if not ticker_metrics.empty:
                    metric = ticker_metrics.iloc[0]
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("종가", f"${metric['close']:.2f}")
                    with col2:
                        st.metric("수익률", f"{metric['return_pct']:.2f}%")
                    with col3:
                        st.metric("변동성", f"{metric['vol_pct']:.2f}%")
                    with col4:
                        st.metric("거래량", f"{metric['volume']:,}")
    
    st.markdown("---")
    
    # ========================================================================
    # Recommendations Section
    # ========================================================================
    st.header("💡 추천 종목")
    
    try:
        with st.spinner("💡 추천 종목 생성 중..."):
            recommendations = recommend_trades(metrics_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 매수 추천 (TOP 5)")
            buy_df = recommendations['buy'].head(5)
            if not buy_df.empty:
                for idx, row in buy_df.iterrows():
                    with st.container():
                        st.markdown(f"### {row['ticker']}")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("수익률", f"{row.get('return_pct', 0):.2f}%")
                        with col_b:
                            st.metric("변동성", f"{row.get('vol_pct', 0):.2f}%")
                        with col_c:
                            st.metric("종가", f"${row.get('close', 0):.2f}")
                        
                        # Display reason
                        reason = row.get('reason', '')
                        if reason:
                            st.info(f"📌 추천 근거: {reason}")
                        else:
                            # Extract from metrics
                            reasons = []
                            if row.get('return_pct', 0) > 5.0:
                                reasons.append("높은 수익률")
                            if row.get('vol_pct', 0) > 4.0:
                                reasons.append("높은 변동성")
                            if row.get('volatility', 0) < 3.0:
                                reasons.append("낮은 변동성 (안정적)")
                            if reasons:
                                st.info(f"📌 추천 근거: {', '.join(reasons)}")
                        st.markdown("---")
            else:
                st.info("매수 추천 종목이 없습니다.")
        
        with col2:
            st.subheader("⚠️ 매도 추천 (TOP 5)")
            sell_df = recommendations['sell'].head(5)
            if not sell_df.empty:
                for idx, row in sell_df.iterrows():
                    with st.container():
                        st.markdown(f"### {row['ticker']}")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("수익률", f"{row.get('return_pct', 0):.2f}%")
                        with col_b:
                            st.metric("변동성", f"{row.get('vol_pct', 0):.2f}%")
                        with col_c:
                            st.metric("종가", f"${row.get('close', 0):.2f}")
                        
                        # Display reason
                        reason = row.get('reason', '')
                        if reason:
                            st.warning(f"⚠️ 추천 근거: {reason}")
                        else:
                            # Extract from metrics
                            reasons = []
                            if row.get('return_pct', 0) < -5.0:
                                reasons.append("급락")
                            if row.get('vol_pct', 0) > 5.0:
                                reasons.append("높은 변동성 (불안정)")
                            if row.get('volatility', 0) > 5.0:
                                reasons.append("높은 변동성")
                            if reasons:
                                st.warning(f"⚠️ 추천 근거: {', '.join(reasons)}")
                        st.markdown("---")
            else:
                st.info("매도 추천 종목이 없습니다.")
    
    except Exception as e:
        st.error(f"추천 생성 중 오류: {str(e)}")
        logger.exception(e)

else:
    # Initial state
    st.info("👈 왼쪽 사이드바에서 설정을 입력하고 '🔄 새로고침' 버튼을 클릭하세요.")
    
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
temp_path = Path("temp_universe.csv")
if temp_path.exists():
    try:
        temp_path.unlink()
    except:
        pass
