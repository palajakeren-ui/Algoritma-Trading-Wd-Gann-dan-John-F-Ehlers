from flask import Flask, request, jsonify
from flask_cors import CORS
from loguru import logger
import pandas as pd

# Import core components and config loader
from utils.config_loader import load_all_configs
from core.data_feed import DataFeed
from core.gann_engine import GannEngine
from core.ehlers_engine import EhlersEngine
from core.astro_engine import AstroEngine
from core.ml_engine import MLEngine
from core.signal_engine import AISignalEngine
from backtest.backtester import Backtester
from backtest.metrics import calculate_performance_metrics

# Import comprehensive API blueprints
from api_comprehensive import (
    trading_api, positions_api, orders_api, risk_api, scanner_api,
    portfolio_api, forecast_api, cycles_api, config_sync_api,
    gann_api, ehlers_api, astro_api, ml_api, broker_api,
    options_api, alerts_api, patterns_api, smith_api, rr_api,
    reports_api, agent_api, settings_api, strategies_api,
    instruments_api, market_data_api
)

# --- Flask App Initialization ---
app = Flask(__name__)
# Allow requests from the default Vite dev server port
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Register Comprehensive API Blueprints ---
app.register_blueprint(trading_api, url_prefix='/api/trading')
app.register_blueprint(positions_api, url_prefix='/api/positions')
app.register_blueprint(orders_api, url_prefix='/api/orders')
app.register_blueprint(risk_api, url_prefix='/api/risk')
app.register_blueprint(scanner_api, url_prefix='/api/scanner')
app.register_blueprint(portfolio_api, url_prefix='/api/portfolio')
app.register_blueprint(forecast_api, url_prefix='/api/forecast')
app.register_blueprint(cycles_api, url_prefix='/api/cycles')
app.register_blueprint(config_sync_api, url_prefix='/api/config')
app.register_blueprint(gann_api, url_prefix='/api/gann')
app.register_blueprint(ehlers_api, url_prefix='/api/ehlers')
app.register_blueprint(astro_api, url_prefix='/api/astro')
app.register_blueprint(ml_api, url_prefix='/api/ml')
app.register_blueprint(broker_api, url_prefix='/api/broker')
app.register_blueprint(options_api, url_prefix='/api/options')
app.register_blueprint(alerts_api, url_prefix='/api/alerts')
app.register_blueprint(patterns_api, url_prefix='/api/patterns')
app.register_blueprint(smith_api, url_prefix='/api/smith')
app.register_blueprint(rr_api, url_prefix='/api/rr')
app.register_blueprint(reports_api, url_prefix='/api/reports')
app.register_blueprint(agent_api, url_prefix='/api/agent')
app.register_blueprint(settings_api, url_prefix='/api/settings')
app.register_blueprint(strategies_api, url_prefix='/api/strategies')
app.register_blueprint(instruments_api, url_prefix='/api/instruments')
app.register_blueprint(market_data_api, url_prefix='/api/market-data')

logger.info("All API blueprints registered successfully")

# --- Load Configurations ---
# Load all configs at startup to be shared across requests
try:
    CONFIG = load_all_configs()
    if not CONFIG:
        raise RuntimeError("Configurations could not be loaded.")
    logger.success("All configurations loaded for Flask API.")
except Exception as e:
    logger.error(f"FATAL: Could not load configurations. API cannot start. Error: {e}")
    CONFIG = None

# --- API Endpoints ---

@app.route("/api/run_backtest", methods=['POST'])
def run_backtest_endpoint():
    """
    Endpoint to run a backtest with specified parameters.
    """
    if not CONFIG:
        return jsonify({"error": "Server configuration is missing."}), 500

    params = request.json
    logger.info(f"Received backtest request with params: {params}")

    # Extract parameters from request
    start_date = params.get("startDate", "2022-01-01")
    end_date = params.get("endDate", "2023-12-31")
    initial_capital = float(params.get("initialCapital", 100000.0))
    symbol = params.get("symbol", "BTC-USD") # Allow symbol to be passed in future

    try:
        # This logic is adapted from the integration_test script
        data_feed = DataFeed(broker_config=CONFIG.get('broker_config', {}))
        price_data = data_feed.get_historical_data(symbol, "1d", start_date, end_date)
        if price_data is None:
            return jsonify({"error": f"Failed to fetch price data for {symbol}."}), 400

        gann_engine = GannEngine(gann_config=CONFIG.get('gann_config', {}))
        ehlers_engine = EhlersEngine(ehlers_config=CONFIG.get('ehlers_config', {}))
        astro_engine = AstroEngine(astro_config=CONFIG.get('astro_config', {}))
        ml_engine = MLEngine(CONFIG)
        signal_engine = AISignalEngine(CONFIG.get('strategy_config', {}))

        gann_levels = gann_engine.calculate_sq9_levels(price_data)
        data_with_indicators = ehlers_engine.calculate_all_indicators(price_data)
        astro_events = astro_engine.analyze_dates(price_data.index)

        ml_predictions = ml_engine.get_predictions(data_with_indicators, gann_levels, astro_events)
        if ml_predictions is not None:
            data_with_indicators = data_with_indicators.join(ml_predictions)

        signals = signal_engine.generate_signals(data_with_indicators, gann_levels, astro_events)

        # Update backtest config with capital from request
        CONFIG['backtest_config']['initial_capital'] = initial_capital
        backtester = Backtester(CONFIG)
        results = backtester.run(data_with_indicators, signals)

        performance = {}
        if not results['trades'].empty:
            raw_metrics = calculate_performance_metrics(
                results['equity_curve'], results['trades'], results['initial_capital']
            )
            # Transform to frontend-expected format (camelCase, numeric values)
            performance = {
                "totalReturn": float(raw_metrics.get('Total Return (%)', 0)) / 100,  # Convert % to decimal
                "sharpeRatio": float(raw_metrics.get('Sharpe Ratio', 0)),
                "maxDrawdown": float(raw_metrics.get('Max Drawdown (%)', 0)) / 100,  # Convert % to decimal
                "winRate": float(raw_metrics.get('Win Rate (%)', 0)) / 100,  # Convert % to decimal
                "profitFactor": float(raw_metrics.get('Profit Factor', 0)) if raw_metrics.get('Profit Factor', 'inf') != 'inf' else 999.99,
                "totalTrades": int(float(raw_metrics.get('Total Trades', 0))),
            }

        # Convert DataFrames to JSON-serializable format
        results['trades']['entry_date'] = results['trades']['entry_date'].dt.strftime('%Y-%m-%d')
        results['trades']['exit_date'] = results['trades']['exit_date'].dt.strftime('%Y-%m-%d')

        # Transform equity curve to match frontend expected format
        equity_data = results['equity_curve'].reset_index()
        equity_curve_formatted = [
            {"date": row['timestamp'].strftime('%Y-%m-%d'), "equity": float(row['equity'])}
            for _, row in equity_data.iterrows()
        ]

        response_data = {
            "performanceMetrics": performance,
            "equityCurve": equity_curve_formatted,
            "trades": results['trades'].to_dict(orient='records'),
        }

        logger.success("Backtest completed successfully and results returned.")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"An error occurred during backtest: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=['GET'])
def health_check():
    """Health check endpoint for frontend monitoring"""
    try:
        if CONFIG:
            return jsonify({
                "status": "healthy",
                "message": "Backend API is running",
                "timestamp": pd.Timestamp.now().isoformat(),
                "config_loaded": bool(CONFIG)
            })
        else:
            return jsonify({
                "status": "unhealthy",
                "message": "Configuration not loaded",
                "timestamp": pd.Timestamp.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "timestamp": pd.Timestamp.now().isoformat()
        }), 500


@app.route("/api/config", methods=['GET'])
def get_config():
    """Get current configuration for frontend"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        # Return safe config (exclude sensitive data)
        safe_config = {}
        for key, value in CONFIG.items():
            if key in ['broker_config', 'risk_config']:
                # Only show non-sensitive config
                safe_config[key] = {
                    k: v for k, v in value.items() 
                    if k not in ['api_key', 'secret', 'password']
                }
            else:
                safe_config[key] = value
        
        return jsonify(safe_config)
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/market-data/<symbol>", methods=['POST'])
def get_market_data(symbol):
    """Get market data for a symbol"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json
        timeframe = data.get('timeframe', '1d')
        start_date = data.get('startDate', '2022-01-01')
        end_date = data.get('endDate', '2023-12-31')
        
        data_feed = DataFeed(broker_config=CONFIG.get('broker_config', {}))
        price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if price_data is None:
            return jsonify({"error": f"Failed to fetch price data for {symbol}"}), 400
        
        # Convert to the format expected by frontend
        market_data = []
        for index, row in price_data.iterrows():
            market_data.append({
                'time': index.strftime('%Y-%m-%d %H:%M:%S'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume'])
            })
        
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Failed to get market data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/gann-levels/<symbol>", methods=['POST'])
def get_gann_levels(symbol):
    """Get Gann Square of 9 levels for a symbol at a specific price"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json
        current_price = data.get('price', 0)
        
        if current_price <= 0:
            return jsonify({"error": "Invalid price provided"}), 400
        
        gann_engine = GannEngine(gann_config=CONFIG.get('gann_config', {}))
        
        # Create mock price data for calculation
        import pandas as pd
        mock_data = pd.DataFrame({
            'open': [current_price],
            'high': [current_price * 1.01],
            'low': [current_price * 0.99],
            'close': [current_price]
        })
        
        sq9_levels = gann_engine.calculate_sq9_levels(mock_data)
        
        if not sq9_levels:
            return jsonify({"error": "Failed to calculate Gann levels"}), 400
        
        # Transform to frontend expected format
        gann_levels = []
        
        # Add support levels
        for i, level in enumerate(sq9_levels.get('support', [])):
            gann_levels.append({
                "angle": (i + 1) * 45,  # Approximate angle representation
                "price": float(level),
                "type": "support" if i % 2 == 0 else "minor"
            })
        
        # Add resistance levels
        for i, level in enumerate(sq9_levels.get('resistance', [])):
            gann_levels.append({
                "angle": 180 + (i + 1) * 45,  # Approximate angle representation
                "price": float(level),
                "type": "resistance" if i % 2 == 0 else "major"
            })
        
        return jsonify(gann_levels)
    except Exception as e:
        logger.error(f"Failed to get Gann levels: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/signals/<symbol>", methods=['GET'])
def get_signals(symbol):
    """Get trading signals for a symbol"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data_feed = DataFeed(broker_config=CONFIG.get('broker_config', {}))
        
        # Get recent data for signal generation
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None:
            return jsonify({"error": f"Failed to fetch price data for {symbol}"}), 400
        
        # Generate signals using the signal engine
        gann_engine = GannEngine(gann_config=CONFIG.get('gann_config', {}))
        ehlers_engine = EhlersEngine(ehlers_config=CONFIG.get('ehlers_config', {}))
        astro_engine = AstroEngine(astro_config=CONFIG.get('astro_config', {}))
        signal_engine = AISignalEngine(CONFIG.get('strategy_config', {}))
        
        gann_levels = gann_engine.calculate_sq9_levels(price_data)
        data_with_indicators = ehlers_engine.calculate_all_indicators(price_data)
        astro_events = astro_engine.analyze_dates(price_data.index)
        
        signals_df = signal_engine.generate_signals(data_with_indicators, gann_levels, astro_events)
        
        # Transform to frontend expected format
        signals = []
        if not signals_df.empty:
            for timestamp, row in signals_df.iterrows():
                signals.append({
                    "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "symbol": symbol,
                    "signal": row['signal'],
                    "strength": 0.75,  # Default strength since not in original format
                    "price": float(row['price']),
                    "message": row.get('reason', f"{row['signal']} signal generated")
                })
        
        return jsonify(signals)
    except Exception as e:
        logger.error(f"Failed to get signals: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Gann Quant AI Flask API server...")
    logger.info(f"Registered routes: {len(app.url_map._rules)} endpoints")
    # Note: For development, this is fine. For production, use a proper WSGI server like Gunicorn.
    app.run(host="0.0.0.0", port=5000, debug=True)
