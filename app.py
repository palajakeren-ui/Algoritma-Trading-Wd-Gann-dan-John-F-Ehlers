import streamlit as st
import pandas as pd
import json
from loguru import logger

# Import core components
from core.data_feed import DataFeed
from core.gann_engine import GannEngine
from core.ehlers_engine import EhlersEngine
from core.astro_engine import AstroEngine
from core.signal_engine import AISignalEngine
from backtest.backtester import Backtester
from backtest.metrics import calculate_performance_metrics
from gui.charting import plot_backtest_results # This will be created next
from utils.config_loader import load_all_configs # A new helper to load configs

st.set_page_config(layout="wide")

# --- Page Title ---
st.title("Gann Quant AI - Trading System Dashboard")

# --- Main Application Logic ---
def run_backtest_session(config):
    """
    A modified version of the backtest logic from run.py, adapted for Streamlit.
    """
    with st.spinner("Running backtest, please wait..."):
        st.write("---")
        st.subheader("Backtest Log")

        # Using st.text for log-like output
        log_container = st.empty()
        log_container.text("Initializing components...")

        # 1. Initialize components
        data_feed = DataFeed(broker_config=config.get('broker_config', {}))
        gann_engine = GannEngine(gann_config=config.get('gann_config', {}))
        ehlers_engine = EhlersEngine(ehlers_config=config.get('ehlers_config', {}))
        astro_engine = AstroEngine(astro_config=config.get('astro_config', {}))
        signal_engine = AISignalEngine(config=config.get('strategy_config', {}))

        # 2. Get historical data
        symbol = "BTC-USD"
        start_date = "2021-01-01"
        end_date = "2023-01-01"
        log_container.text(f"Fetching data for {symbol} from {start_date} to {end_date}...")

        price_data = data_feed.get_historical_data(symbol, "1d", start_date, end_date)
        if price_data is None:
            st.error("Failed to fetch price data.")
            return

        # 3. Perform analysis
        log_container.text("Performing Gann, Ehlers, and Astro analysis...")
        gann_levels = gann_engine.calculate_sq9_levels(price_data)
        data_with_indicators = ehlers_engine.calculate_all_indicators(price_data)
        astro_events = astro_engine.analyze_dates(price_data.index)

        # 4. Generate signals
        log_container.text("Generating trading signals...")
        signals = signal_engine.generate_signals(data_with_indicators, gann_levels, astro_events)
        if signals.empty:
            st.warning("No signals were generated for this period.")
            return

        # 5. Run backtest
        log_container.text("Executing backtest simulation...")
        backtester = Backtester(config.get('risk_config', {}), initial_capital=100000)
        results = backtester.run(data_with_indicators, signals)

        # 6. Calculate metrics
        log_container.text("Calculating performance metrics...")
        performance = calculate_performance_metrics(
            results['equity_curve'], results['trades'], results['initial_capital']
        )

        log_container.success("Backtest completed successfully!")

    # --- Display Results ---
    st.subheader("Backtest Performance Metrics")
    st.json(performance)

    st.subheader("Interactive Chart")
    fig = plot_backtest_results(price_data, results['equity_curve'], results['trades'])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Trade Log")
    st.dataframe(results['trades'])


# --- Main Page UI ---
if 'config' not in st.session_state:
    st.session_state.config = load_all_configs()

if st.session_state.config:
    if st.button("🚀 Run New Backtest"):
        run_backtest_session(st.session_state.config)
else:
    st.error("Failed to load configuration files. Please check the `config` directory.")
