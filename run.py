import argparse
import yaml
from loguru import logger
from typing import Dict

# Import core components
from core.data_feed import DataFeed
from core.gann_engine import GannEngine
from core.ehlers_engine import EhlersEngine
from core.astro_engine import AstroEngine
from core.ml_engine import MLEngine
from core.signal_engine import AISignalEngine
from backtest.backtester import Backtester
from backtest.metrics import calculate_performance_metrics
import json
import os

# Get the absolute path of the directory containing run.py
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(SCRIPT_DIR, 'config')

def load_config(file_name: str) -> Dict:
    """Loads a YAML configuration file from the config directory."""
    path = os.path.join(CONFIG_DIR, file_name)
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at: {path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration from {path}: {e}")
        return {}

def run_backtest(config: Dict):
    """
    Orchestrates the backtesting process.
    """
    logger.info("Starting backtest run...")

    # 1. Initialize components
    data_feed = DataFeed(broker_config=config.get('broker_config', {}))
    gann_engine = GannEngine(gann_config=config.get('gann_config', {}))
    ehlers_engine = EhlersEngine(ehlers_config=config.get('ehlers_config', {}))
    astro_engine = AstroEngine(astro_config=config.get('astro_config', {}))
    ml_engine = MLEngine(config) # Pass the full config
    signal_engine = AISignalEngine(config.get('strategy_config', {}))

    # 2. Get historical data
    # For now, we'll hardcode a symbol and date range for testing.
    # In a real scenario, this would be driven by the backtest config.
    symbol = "BTC-USD"
    start_date = "2022-01-01"
    end_date = "2023-01-01"

    price_data = data_feed.get_historical_data(
        symbol=symbol,
        timeframe="1d",
        start_date=start_date,
        end_date=end_date
    )

    if price_data is None or price_data.empty:
        logger.error("Failed to fetch historical data. Aborting backtest.")
        return

    # 3. Perform analysis
    gann_levels = gann_engine.calculate_sq9_levels(price_data)
    data_with_indicators = ehlers_engine.calculate_all_indicators(price_data)
    astro_events = astro_engine.analyze_dates(price_data.index)
    ml_predictions = ml_engine.get_predictions(data_with_indicators, gann_levels, astro_events)

    # Merge predictions into the main data frame
    if ml_predictions is not None:
        data_with_indicators = data_with_indicators.join(ml_predictions)

    # 4. Generate signals
    signals = signal_engine.generate_signals(data_with_indicators, gann_levels, astro_events)

    if signals.empty:
        logger.warning("No signals were generated. Backtest cannot proceed.")
        return

    # 5. Run the backtester
    logger.info("Signals generated. Handing off to the backtester...")
    backtester = Backtester(config.get('risk_config', {}))
    results = backtester.run(price_data, signals)

    # 6. Calculate and display performance metrics
    if results and not results['trades'].empty:
        performance = calculate_performance_metrics(
            equity_curve=results['equity_curve'],
            trades=results['trades'],
            initial_capital=results['initial_capital']
        )
        print("\n--- Backtest Performance Metrics ---")
        print(json.dumps(performance, indent=2))
        print("------------------------------------")

        # In a real GUI, you would plot results['equity_curve']

    logger.success("Backtest run finished.")


def run_live():
    """Orchestrates the live trading process."""
    logger.info("Live trading mode is not yet implemented.")

def main():
    """
    Main entry point for the application.
    Parses command-line arguments and launches the appropriate mode.
    """
    parser = argparse.ArgumentParser(description="Gann Quant AI Trading Bot")
    parser.add_argument(
        "mode",
        choices=["live", "backtest", "scanner", "trainer", "optimize"],
        help="The mode to run the application in."
    )
    args = parser.parse_args()

    # Load all configurations
    logger.info("Loading all configurations...")
    config = {
        'strategy_config': load_config('strategy_config.yaml'),
        'broker_config': load_config('broker_config.yaml'),
        'gann_config': load_config('gann_config.yaml'),
        'risk_config': load_config('risk_config.yaml'),
        # ... load other configs as needed
    }

    if not all(config.values()):
        logger.error("One or more configuration files failed to load. Exiting.")
        return

    if args.mode == "backtest":
        run_backtest(config)
    elif args.mode == "scanner":
        from scanner.market_scanner import MarketScanner
        scanner = MarketScanner(config)
        scanner.run_scan()
    elif args.mode == "trainer":
        run_trainer(config)
    elif args.mode == "live":
        run_live()
    else:
        logger.warning(f"Mode '{args.mode}' is not yet implemented.")


def run_trainer(config: Dict):
    """
    Orchestrates the ML model training process.
    """
    logger.info("--- Starting ML Trainer Mode ---")

    # 1. Initialize components
    data_feed = DataFeed(broker_config=config.get('broker_config', {}))
    gann_engine = GannEngine(gann_config=config.get('gann_config', {}))
    ehlers_engine = EhlersEngine(ehlers_config=config.get('ehlers_config', {}))
    astro_engine = AstroEngine(astro_config=config.get('astro_config', {}))
    ml_engine = MLEngine(config)

    # 2. Fetch a large dataset for training
    price_data = data_feed.get_historical_data(
        symbol="BTC-USD",
        timeframe="1d",
        start_date="2018-01-01",
        end_date="2023-12-31"
    )
    if price_data is None:
        logger.error("Could not fetch data for training. Aborting.")
        return

    # 3. Perform analysis to generate features
    gann_levels = gann_engine.calculate_sq9_levels(price_data)
    data_with_indicators = ehlers_engine.calculate_all_indicators(price_data)
    astro_events = astro_engine.analyze_dates(price_data.index)

    # 4. Train the model
    ml_engine.train_model(data_with_indicators, gann_levels, astro_events)

if __name__ == "__main__":
    main()
