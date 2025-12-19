"""Streamlit UI for NASDAQ Stock Analysis.

This application provides an interactive interface for:
- Fetching OHLCV data using yfinance
- Calculating daily returns and volatility
- Ranking top movers
- Generating buy/sell signals
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from typing import List, Optional
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nasdaq_scanner.providers.fetch_ohlcv import fetch_ohlcv
from nasdaq_scanner.core.analysis_functions import (
    calc_daily_returns,
    calc_volatility_proxy,
    rank_movers,
)
from nasdaq_scanner.core.signal_generator import generate_signals
from nasdaq_scanner.providers.data_collector import get_nasdaq100_tickers, load_ticker_list

# Configure page
st.set_page_config(
    page_title="NASDAQ 주가 분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("📊 NASDAQ 주가 분석 대시보드")
st.markdown("---")

# ============================================================================
# Sidebar Configuration
# ============================================================================
st.sidebar.header("⚙️ 분석 설정")

# Ticker source selection
ticker_source_type = st.sidebar.radio(
    "티커 소스",
    options=["NASDAQ-100", "CSV 파일"],
    help="데이터를 가져올 티커 소스를 선택하세요"
)

ticker_list: Optional[List[str]] = None

if ticker_source_type == "NASDAQ-100":
    ticker_list = get_nasdaq100_tickers()
    st.sidebar.info(f"✅ {len(ticker_list)}개 NASDAQ-100 티커 선택됨")
elif ticker_source_type == "CSV 파일":
    universe_file = st.sidebar.file_uploader(
        "티커 유니버스 파일 (CSV)",
        type=['csv'],
        help="symbol 또는 ticker 컬럼을 포함한 CSV 파일을 업로드하세요"
    )
    if universe_file:
        try:
            # Read CSV from uploaded file
            df = pd.read_csv(universe_file)
            # Try to find ticker column
            if 'symbol' in df.columns:
                ticker_list = df['symbol'].astype(str).str.strip().str.upper().dropna().unique().tolist()
            elif 'ticker' in df.columns:
                ticker_list = df['ticker'].astype(str).str.strip().str.upper().dropna().unique().tolist()
            elif len(df.columns) > 0:
                # Use first column
                ticker_list = df.iloc[:, 0].astype(str).str.strip().str.upper().dropna().unique().tolist()
            else:
                ticker_list = []
            # Remove empty strings
            ticker_list = [t for t in ticker_list if t]
            if ticker_list:
                st.sidebar.info(f"✅ {len(ticker_list)}개 티커 로드됨")
            else:
                st.sidebar.warning("⚠️ 티커를 찾을 수 없습니다.")
        except Exception as e:
            st.sidebar.error(f"❌ CSV 파일 로드 실패: {str(e)}")
            ticker_list = None

# Period selection
st.sidebar.subheader("📅 기간 설정")
period = st.sidebar.selectbox(
    "Period",
    options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
    index=1,  # Default: 5d
    help="데이터 수집 기간을 선택하세요"
)

# Interval selection
interval = st.sidebar.selectbox(
    "Interval",
    options=["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"],
    index=8,  # Default: 1d
    help="데이터 간격을 선택하세요"
)

# Run Analysis button
run_button = st.sidebar.button("🚀 분석 실행", type="primary", use_container_width=True)

# ============================================================================
# Main Content
# ============================================================================

if run_button:
    if ticker_list is None or len(ticker_list) == 0:
        st.error("❌ 티커 리스트를 선택하거나 업로드해주세요.")
        st.stop()

    try:
        # Step 1: Fetch OHLCV data
        with st.spinner(f"📡 {len(ticker_list)}개 티커 데이터 수집 중..."):
            ohlcv_df = fetch_ohlcv(ticker_list, period=period, interval=interval)

        if ohlcv_df.empty:
            st.warning("⚠️ 수집된 데이터가 없습니다. 기간이나 티커를 확인해주세요.")
            st.stop()

        st.success(f"✅ {len(ohlcv_df)}개 행의 데이터 수집 완료")

        # Step 2: Calculate daily returns
        with st.spinner("📊 일간 수익률 계산 중..."):
            returns_df = calc_daily_returns(ohlcv_df)

        # Step 3: Calculate volatility proxy
        with st.spinner("📈 변동성 계산 중..."):
            metrics_df = calc_volatility_proxy(returns_df)

        # Step 4: Rank movers
        with st.spinner("🏆 랭킹 생성 중..."):
            rankings = rank_movers(metrics_df)

        # Step 5: Generate signals
        with st.spinner("💡 시그널 생성 중..."):
            signals = generate_signals(metrics_df)

        # Store results in session state for download
        st.session_state['ohlcv_df'] = ohlcv_df
        st.session_state['metrics_df'] = metrics_df
        st.session_state['rankings'] = rankings
        st.session_state['signals'] = signals

        # Display results
        st.markdown("---")

        # ====================================================================
        # Top 10 Tables
        # ====================================================================
        st.header("📈 TOP 10 랭킹")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📈 상승 TOP 10")
            gainers = rankings['gainers']
            if not gainers.empty:
                # Select columns to display
                display_cols = ['ticker', 'date', 'return', 'vol', 'close']
                available_cols = [c for c in display_cols if c in gainers.columns]
                st.dataframe(
                    gainers[available_cols].rename(columns={
                        'ticker': '티커',
                        'date': '날짜',
                        'return': '수익률 (%)',
                        'vol': '변동성',
                        'close': '종가'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("상승 종목 데이터가 없습니다.")

        with col2:
            st.subheader("📉 하락 TOP 10")
            losers = rankings['losers']
            if not losers.empty:
                display_cols = ['ticker', 'date', 'return', 'vol', 'close']
                available_cols = [c for c in display_cols if c in losers.columns]
                st.dataframe(
                    losers[available_cols].rename(columns={
                        'ticker': '티커',
                        'date': '날짜',
                        'return': '수익률 (%)',
                        'vol': '변동성',
                        'close': '종가'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("하락 종목 데이터가 없습니다.")

        with col3:
            st.subheader("📊 변동성 TOP 10")
            volatile = rankings['volatile']
            if not volatile.empty:
                display_cols = ['ticker', 'date', 'vol', 'return', 'close']
                available_cols = [c for c in display_cols if c in volatile.columns]
                st.dataframe(
                    volatile[available_cols].rename(columns={
                        'ticker': '티커',
                        'date': '날짜',
                        'vol': '변동성',
                        'return': '수익률 (%)',
                        'close': '종가'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("변동성 데이터가 없습니다.")

        st.markdown("---")

        # ====================================================================
        # Buy/Sell Candidates
        # ====================================================================
        st.header("💡 매수/매도 시그널")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💰 매수 후보")
            buy_candidates = signals['buy_candidates']
            if not buy_candidates.empty:
                display_cols = ['ticker', 'date', 'return', 'vol', 'close', 'reason']
                available_cols = [c for c in display_cols if c in buy_candidates.columns]
                st.dataframe(
                    buy_candidates[available_cols].rename(columns={
                        'ticker': '티커',
                        'date': '날짜',
                        'return': '수익률 (%)',
                        'vol': '변동성',
                        'close': '종가',
                        'reason': '추천 근거'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("매수 후보가 없습니다.")

        with col2:
            st.subheader("⚠️ 매도 후보")
            sell_candidates = signals['sell_candidates']
            if not sell_candidates.empty:
                display_cols = ['ticker', 'date', 'return', 'vol', 'close', 'reason']
                available_cols = [c for c in display_cols if c in sell_candidates.columns]
                st.dataframe(
                    sell_candidates[available_cols].rename(columns={
                        'ticker': '티커',
                        'date': '날짜',
                        'return': '수익률 (%)',
                        'vol': '변동성',
                        'close': '종가',
                        'reason': '추천 근거'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("매도 후보가 없습니다.")

        st.markdown("---")

        # ====================================================================
        # Selected Ticker Chart
        # ====================================================================
        st.header("📊 티커 상세 차트")

        # Get all available tickers from OHLCV data
        available_tickers = sorted(ohlcv_df['ticker'].unique().tolist())

        if available_tickers:
            selected_ticker = st.selectbox(
                "티커 선택",
                options=available_tickers,
                index=0,
                help="차트를 표시할 티커를 선택하세요"
            )

            if selected_ticker:
                ticker_data = ohlcv_df[ohlcv_df['ticker'] == selected_ticker].sort_values('date')

                if not ticker_data.empty:
                    st.subheader(f"💰 {selected_ticker} 종가 차트")
                    # Create chart data with date as index
                    chart_data = ticker_data[['date', 'close']].set_index('date')
                    st.line_chart(chart_data)

                    # Display latest metrics
                    ticker_metrics = metrics_df[metrics_df['ticker'] == selected_ticker]
                    if not ticker_metrics.empty:
                        latest = ticker_metrics.sort_values('date').iloc[-1]
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("종가", f"${latest['close']:.2f}")
                        with col2:
                            st.metric("수익률", f"{latest.get('return', 0):.2f}%")
                        with col3:
                            st.metric("변동성", f"{latest.get('vol', 0):.4f}")
                        with col4:
                            st.metric("고가", f"${latest.get('high', 0):.2f}")
                        with col5:
                            st.metric("저가", f"${latest.get('low', 0):.2f}")

        st.markdown("---")

        # ====================================================================
        # CSV Download
        # ====================================================================
        st.header("💾 결과 다운로드")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Download OHLCV data
            csv_ohlcv = ohlcv_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 OHLCV 데이터",
                data=csv_ohlcv,
                file_name="ohlcv_data.csv",
                mime="text/csv",
            )

        with col2:
            # Download metrics data
            csv_metrics = metrics_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 지표 데이터",
                data=csv_metrics,
                file_name="metrics_data.csv",
                mime="text/csv",
            )

        with col3:
            # Download buy candidates
            if not signals['buy_candidates'].empty:
                csv_buy = signals['buy_candidates'].to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 매수 후보",
                    data=csv_buy,
                    file_name="buy_candidates.csv",
                    mime="text/csv",
                )
            else:
                st.info("매수 후보 없음")

        with col4:
            # Download sell candidates
            if not signals['sell_candidates'].empty:
                csv_sell = signals['sell_candidates'].to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 매도 후보",
                    data=csv_sell,
                    file_name="sell_candidates.csv",
                    mime="text/csv",
                )
            else:
                st.info("매도 후보 없음")

    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.exception(e)

else:
    # Initial state
    st.info("👈 왼쪽 사이드바에서 설정을 입력하고 '🚀 분석 실행' 버튼을 클릭하세요.")

    st.markdown("### 📋 사용 방법")
    st.markdown("""
    1. **티커 소스 선택**: NASDAQ-100 또는 CSV 파일 업로드
    2. **기간 설정**: Period와 Interval 선택
    3. **분석 실행**: '🚀 분석 실행' 버튼 클릭
    4. **결과 확인**: 
       - 상승/하락/변동성 TOP 10 테이블
       - 매수/매도 시그널 테이블
       - 선택 티커 차트
    5. **결과 다운로드**: CSV 파일로 저장

    ### 📊 제공 기능
    - **OHLCV 데이터 수집**: yfinance를 통한 시장 데이터 수집
    - **일간 수익률 계산**: ticker별 일간 수익률 계산
    - **변동성 계산**: (high-low)/open 기반 변동성 proxy
    - **랭킹 생성**: 상승/하락/변동성 TOP 10
    - **시그널 생성**: 규칙 기반 매수/매도 후보 선정
    """)

    st.markdown("### ⚠️ 면책 조항")
    st.markdown("""
    이 도구는 투자 자문이 아닙니다. 모든 분석 결과는 참고용이며,
    투자 결정은 사용자의 판단에 따라 이루어져야 합니다.
    """)

