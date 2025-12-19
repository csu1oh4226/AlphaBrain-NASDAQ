"""Streamlit app for NASDAQ Daily Movers & Volatility Analyzer.

This is the main Streamlit application for the dashboard.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import sys
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nasdaq_scanner.cli import run_analysis
from nasdaq_scanner.core.recommender import (
    generate_recommendations,
    get_default_buy_rules,
    get_default_sell_rules,
    format_reasons,
)

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

# Sidebar - Input parameters
st.sidebar.header("⚙️ 분석 설정")

# Date input
analysis_date = st.sidebar.date_input(
    "분석 날짜",
    value=date.today(),
    max_value=date.today(),
    help="분석할 날짜를 선택하세요 (오늘 이전 날짜만 가능)"
)

# Universe file input
universe_file = st.sidebar.file_uploader(
    "티커 유니버스 파일 (CSV)",
    type=['csv'],
    help="symbol 컬럼을 포함한 CSV 파일을 업로드하세요"
)

# Number of top movers
n = st.sidebar.slider(
    "상위/하위 종목 수",
    min_value=5,
    max_value=50,
    value=10,
    help="상승/하락/변동성 상위 N개 종목을 표시합니다"
)

# Max recommendations
max_recommendations = st.sidebar.slider(
    "추천 종목 수",
    min_value=5,
    max_value=20,
    value=10,
    help="매수/매도 추천 종목 수"
)

# Run analysis button
run_button = st.sidebar.button("🚀 분석 실행", type="primary", use_container_width=True)

# Main content area
if run_button:
    if universe_file is None:
        st.error("❌ 티커 유니버스 파일을 업로드해주세요.")
        st.stop()

    # Save uploaded file temporarily
    temp_universe_path = Path("temp_universe.csv")
    with open(temp_universe_path, "wb") as f:
        f.write(universe_file.getbuffer())

    try:
        # Run analysis with return_results=True
        with st.spinner("📡 데이터 수집 및 분석 중..."):
            results = run_analysis(
                analysis_date=analysis_date,
                universe_path=str(temp_universe_path),
                n=n,
                output_path=None,
                export_csv=False,
                return_results=True,
            )

        if results is None:
            st.error("❌ 분석 결과를 가져올 수 없습니다.")
            st.stop()

        # Display stats
        stats = results['stats']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 종목 수", stats['total_symbols'])
        with col2:
            st.metric("성공적으로 수집", stats['successful_fetches'])
        with col3:
            st.metric("수집 실패", stats['failed_fetches'])

        st.markdown("---")

        # Generate recommendations
        with st.spinner("💡 추천 종목 생성 중..."):
            recommendations = generate_recommendations(
                results['analysis_df'],
                max_recommendations=max_recommendations
            )

        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 상위 종목",
            "📉 하위 종목",
            "📊 변동성",
            "💰 매수 추천",
            "⚠️ 매도/주의"
        ])

        # Tab 1: Top Movers
        with tab1:
            st.subheader("📈 상승률 상위 종목")
            if not results['top_movers'].empty:
                st.dataframe(
                    results['top_movers'][['symbol', 'return_pct', 'vol_pct', 'Open', 'High', 'Low', 'Close', 'Volume']],
                    use_container_width=True
                )
                # Chart
                chart_data = results['top_movers'][['symbol', 'return_pct']].set_index('symbol')
                st.bar_chart(chart_data)
            else:
                st.info("상승 종목 데이터가 없습니다.")

        # Tab 2: Bottom Movers
        with tab2:
            st.subheader("📉 하락률 상위 종목")
            if not results['bottom_movers'].empty:
                st.dataframe(
                    results['bottom_movers'][['symbol', 'return_pct', 'vol_pct', 'Open', 'High', 'Low', 'Close', 'Volume']],
                    use_container_width=True
                )
                # Chart
                chart_data = results['bottom_movers'][['symbol', 'return_pct']].set_index('symbol')
                st.bar_chart(chart_data)
            else:
                st.info("하락 종목 데이터가 없습니다.")

        # Tab 3: Volatile Movers
        with tab3:
            st.subheader("📊 변동성 상위 종목")
            if not results['volatile_movers'].empty:
                st.dataframe(
                    results['volatile_movers'][['symbol', 'vol_pct', 'return_pct', 'Open', 'High', 'Low', 'Close', 'Volume']],
                    use_container_width=True
                )
                # Chart
                chart_data = results['volatile_movers'][['symbol', 'vol_pct']].set_index('symbol')
                st.bar_chart(chart_data)
            else:
                st.info("변동성 데이터가 없습니다.")

        # Tab 4: Buy Recommendations
        with tab4:
            st.subheader("💰 매수 추천 종목")
            buy_df = recommendations['buy']
            if not buy_df.empty:
                # Format reasons
                display_df = buy_df.copy()
                display_df['추천 근거'] = display_df['reasons'].apply(
                    lambda r: format_reasons(r, recommendations['buy_rules'])
                )
                # Select columns to display
                cols_to_show = ['symbol', 'return_pct', 'vol_pct', '추천 근거']
                available_cols = [c for c in cols_to_show if c in display_df.columns]
                st.dataframe(
                    display_df[available_cols],
                    use_container_width=True
                )
                # Summary
                st.info(f"✅ 총 {len(buy_df)}개의 매수 추천 종목이 있습니다.")
            else:
                st.info("매수 추천 종목이 없습니다.")

        # Tab 5: Sell/Watch Recommendations
        with tab5:
            st.subheader("⚠️ 매도/주의 추천 종목")
            sell_df = recommendations['sell']
            if not sell_df.empty:
                # Format reasons
                display_df = sell_df.copy()
                display_df['추천 근거'] = display_df['reasons'].apply(
                    lambda r: format_reasons(r, recommendations['sell_rules'])
                )
                # Select columns to display
                cols_to_show = ['symbol', 'signal', 'return_pct', 'vol_pct', '추천 근거']
                available_cols = [c for c in cols_to_show if c in display_df.columns]
                st.dataframe(
                    display_df[available_cols],
                    use_container_width=True
                )
                # Summary
                st.warning(f"⚠️ 총 {len(sell_df)}개의 매도/주의 추천 종목이 있습니다.")
            else:
                st.info("매도/주의 추천 종목이 없습니다.")

        # Clean up temp file
        if temp_universe_path.exists():
            temp_universe_path.unlink()

    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.exception(e)
        if temp_universe_path.exists():
            temp_universe_path.unlink()

else:
    # Initial state - show instructions
    st.info("👈 왼쪽 사이드바에서 분석 설정을 입력하고 '분석 실행' 버튼을 클릭하세요.")

    st.markdown("### 📋 사용 방법")
    st.markdown("""
    1. **티커 유니버스 파일 업로드**: CSV 파일을 업로드하세요 (symbol 컬럼 포함)
    2. **분석 날짜 선택**: 분석할 날짜를 선택하세요
    3. **상위/하위 종목 수 설정**: 표시할 종목 수를 조정하세요
    4. **분석 실행**: '분석 실행' 버튼을 클릭하세요

    ### 📊 제공 기능
    - **상위 종목**: 일간 수익률 상위 종목
    - **하위 종목**: 일간 하락률 상위 종목
    - **변동성**: 일중 변동성 상위 종목
    - **매수 추천**: 규칙 기반 매수 후보 종목
    - **매도/주의**: 규칙 기반 매도/주의 후보 종목
    """)

    st.markdown("### ⚠️ 면책 조항")
    st.markdown("""
    이 도구는 투자 자문이 아닙니다. 모든 분석 결과는 참고용이며,
    투자 결정은 사용자의 판단에 따라 이루어져야 합니다.
    """)

