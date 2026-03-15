"""
Enhanced Flask API for Gann Quant AI - Live Trading Ready
Provides comprehensive endpoints for frontend synchronization
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from loguru import logger
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time

# Import core components
from utils.config_loader import load_all_configs
from core.data_feed import DataFeed
from core.gann_engine import GannEngine
from core.ehlers_engine import EhlersEngine
from core.astro_engine import AstroEngine
from core.ml_engine import MLEngine
from core.signal_engine import AISignalEngine
from core.execution_engine import ExecutionEngine
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.portfolio_manager import PortfolioManager
from scanner.hybrid_scanner import HybridScanner
from backtest.backtester import Backtester
from backtest.metrics import calculate_performance_metrics
from live_trading import LiveTradingBot

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:5000"]
    }
})

# --- SocketIO for WebSocket Support ---
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- Global State ---
CONFIG = None
live_bot: Optional[LiveTradingBot] = None
price_stream_active = False
price_stream_thread = None

# --- Load Configurations ---
try:
    CONFIG = load_all_configs()
    if not CONFIG:
        raise RuntimeError("Configurations could not be loaded.")
    logger.success("All configurations loaded for Enhanced Flask API.")
except Exception as e:
    logger.error(f"FATAL: Could not load configurations. API cannot start. Error: {e}")
    CONFIG = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_data_feed():
    """Get initialized DataFeed instance"""
    return DataFeed(broker_config=CONFIG.get('broker_config', {}))

def get_engines():
    """Get all initialized engines as a dictionary"""
    return {
        'gann': GannEngine(gann_config=CONFIG.get('gann_config', {})),
        'ehlers': EhlersEngine(ehlers_config=CONFIG.get('ehlers_config', {})),
        'astro': AstroEngine(astro_config=CONFIG.get('astro_config', {})),
        'ml': MLEngine(CONFIG),
        'signal': AISignalEngine(CONFIG.get('strategy_config', {})),
    }

def format_timestamp(dt):
    """Format datetime to ISO string"""
    if isinstance(dt, pd.Timestamp):
        return dt.isoformat()
    elif isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)

# ============================================================================
# WEBSOCKET REAL-TIME PRICE FEED
# ============================================================================

def price_stream_worker():
    """Background worker for streaming real-time prices"""
    global price_stream_active
    
    data_feed = get_data_feed()
    
    while price_stream_active:
        try:
            # Fetch latest price for multiple symbols
            symbols = CONFIG.get('trading', {}).get('symbols', ['BTC-USD', 'ETH-USD'])
            
            for symbol in symbols:
                # Get recent data
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                price_data = data_feed.get_historical_data(symbol, '1m', start_date, end_date)
                
                if price_data is not None and not price_data.empty:
                    latest = price_data.iloc[-1]
                    prev = price_data.iloc[-2] if len(price_data) > 1 else latest
                    
                    price_update = {
                        'symbol': symbol,
                        'price': float(latest['close'  ]),
                        'open': float(latest['open']),
                        'high': float(latest['high']),
                        'low': float(latest['low']),
                        'volume': float(latest['volume']) if 'volume' in latest else 0,
                        'change': float(latest['close'] - prev['close']),
                        'changePercent': float(((latest['close'] - prev['close']) / prev['close']) * 100) if prev['close'] != 0 else 0,
                        'timestamp': format_timestamp(latest.name if hasattr(latest, 'name') else datetime.now())
                    }
                    
                    socketio.emit('price_update', price_update, namespace='/ws')
            
            # Sleep between updates
            time.sleep(2)  # 2-second updates
            
        except Exception as e:
            logger.error(f"Price stream error: {e}")
            time.sleep(5)

@socketio.on('connect', namespace='/ws')
def handle_connect():
    """Handle WebSocket connection"""
    global price_stream_active, price_stream_thread
    
    logger.info("WebSocket client connected")
    emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})
    
    # Start price stream if not already running
    if not price_stream_active:
        price_stream_active = True
        price_stream_thread = threading.Thread(target=price_stream_worker, daemon=True)
        price_stream_thread.start()
        logger.info("Price stream worker started")

@socketio.on('disconnect', namespace='/ws')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info("WebSocket client disconnected")

@socketio.on('subscribe', namespace='/ws')
def handle_subscribe(data):
    """Handle symbol subscription"""
    symbol = data.get('symbol')
    logger.info(f"Client subscribed to {symbol}")
    emit('subscribed', {'symbol': symbol, 'status': 'active'})

# ============================================================================
# EXISTING ENDPOINTS (MAINTAINED)
# ============================================================================

@app.route("/api/health", methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if CONFIG:
            return jsonify({
                "status": "healthy",
                "message": "Backend API is running",
                "timestamp": pd.Timestamp.now().isoformat(),
                "config_loaded": bool(CONFIG),
                "live_bot_status": live_bot.get_status() if live_bot else None
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
    """Get current configuration"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        # Return safe config (exclude sensitive data)
        safe_config = {}
        for key, value in CONFIG.items():
            if key in ['broker_config', 'risk_config']:
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

@app.route("/api/run_backtest", methods=['POST'])
def run_backtest_endpoint():
    """Run backtest (existing endpoint maintained)"""
    if not CONFIG:
        return jsonify({"error": "Server configuration is missing."}), 500

    params = request.json
    logger.info(f"Received backtest request with params: {params}")

    start_date = params.get("startDate", "2022-01-01")
    end_date = params.get("endDate", "2023-12-31")
    initial_capital = float(params.get("initialCapital", 100000.0))
    symbol = params.get("symbol", "BTC-USD")

    try:
        data_feed = get_data_feed()
        price_data = data_feed.get_historical_data(symbol, "1d", start_date, end_date)
        if price_data is None:
            return jsonify({"error": f"Failed to fetch price data for {symbol}."}), 400

        engines = get_engines()
        
        gann_levels = engines['gann'].calculate_sq9_levels(price_data)
        data_with_indicators = engines['ehlers'].calculate_all_indicators(price_data)
        astro_events = engines['astro'].analyze_dates(price_data.index)
        ml_predictions = engines['ml'].get_predictions(data_with_indicators, gann_levels, astro_events)
        
        if ml_predictions is not None:
            data_with_indicators = data_with_indicators.join(ml_predictions)

        signals = engines['signal'].generate_signals(data_with_indicators, gann_levels, astro_events)

        CONFIG['backtest_config']['initial_capital'] = initial_capital
        backtester = Backtester(CONFIG)
        results = backtester.run(data_with_indicators, signals)

        performance = {}
        if not results['trades'].empty:
            raw_metrics = calculate_performance_metrics(
                results['equity_curve'], results['trades'], results['initial_capital']
            )
            performance = {
                "totalReturn": float(raw_metrics.get('Total Return (%)', 0)) / 100,
                "sharpeRatio": float(raw_metrics.get('Sharpe Ratio', 0)),
                "maxDrawdown": float(raw_metrics.get('Max Drawdown (%)', 0)) / 100,
                "winRate": float(raw_metrics.get('Win Rate (%)', 0)) / 100,
                "profitFactor": float(raw_metrics.get('Profit Factor', 0)) if raw_metrics.get('Profit Factor', 'inf') != 'inf' else 999.99,
                "totalTrades": int(float(raw_metrics.get('Total Trades', 0))),
            }

        results['trades']['entry_date'] = results['trades']['entry_date'].dt.strftime('%Y-%m-%d')
        results['trades']['exit_date'] = results['trades']['exit_date'].dt.strftime('%Y-%m-%d')

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

        logger.success("Backtest completed successfully")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# MARKET DATA ENDPOINTS
# ============================================================================

@app.route("/api/market-data/<symbol>", methods=['POST'])
def get_market_data(symbol):
    """Get historical market data"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json
        timeframe = data.get('timeframe', '1d')
        start_date = data.get('startDate', '2022-01-01')
        end_date = data.get('endDate', '2023-12-31')
        
        data_feed = get_data_feed()
        price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if price_data is None:
            return jsonify({"error": f"Failed to fetch price data for {symbol}"}), 400
        
        market_data = []
        for index, row in price_data.iterrows():
            market_data.append({
                'time': format_timestamp(index),
                'date': index.strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']) if 'volume' in row else 0
            })
        
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Failed to get market data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/market-data/<symbol>/latest", methods=['GET'])
def get_latest_price(symbol):
    """Get latest price for a symbol"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1m', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": f"Failed to fetch price data for {symbol}"}), 400
        
        latest = price_data.iloc[-1]
        prev = price_data.iloc[-2] if len(price_data) > 1 else latest
        
        return jsonify({
            'symbol': symbol,
            'price': float(latest['close']),
            'open': float(latest['open']),
            'high': float(latest['high']),
            'low': float(latest['low']),
            'volume': float(latest['volume']) if 'volume' in latest else 0,
            'change': float(latest['close'] - prev['close']),
            'changePercent': float(((latest['close'] - prev['close']) / prev['close']) * 100) if prev['close'] != 0 else 0,
            'timestamp': format_timestamp(latest.name if hasattr(latest, 'name') else datetime.now())
        })
    except Exception as e:
        logger.error(f"Failed to get latest price: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# GANN ANALYSIS ENDPOINTS
# ============================================================================

@app.route("/api/gann-levels/<symbol>", methods=['POST'])
def get_gann_levels(symbol):
    """Get Gann Square of 9 levels"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json
        current_price = data.get('price', 0)
        
        if current_price <= 0:
            return jsonify({"error": "Invalid price provided"}), 400
        
        gann_engine = GannEngine(gann_config=CONFIG.get('gann_config', {}))
        
        mock_data = pd.DataFrame({
            'open': [current_price],
            'high': [current_price * 1.01],
            'low': [current_price * 0.99],
            'close': [current_price]
        })
        
        sq9_levels = gann_engine.calculate_sq9_levels(mock_data)
        
        if not sq9_levels:
            return jsonify({"error": "Failed to calculate Gann levels"}), 400
        
        gann_levels = []
        
        for i, level in enumerate(sq9_levels.get('support', [])):
            gann_levels.append({
                "angle": (i + 1) * 45,
                "degree": (i + 1) * 45,
                "price": float(level),
                "type": "support" if i % 2 == 0 else "minor",
                "strength": 1.0 - (i * 0.15)
            })
        
        for i, level in enumerate(sq9_levels.get('resistance', [])):
            gann_levels.append({
                "angle": 180 + (i + 1) * 45,
                "degree": 180 + (i + 1) * 45,
                "price": float(level),
                "type": "resistance" if i % 2 == 0 else "major",
                "strength": 1.0 - (i * 0.15)
            })
        
        return jsonify(gann_levels)
    except Exception as e:
        logger.error(f"Failed to get Gann levels: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/gann/full-analysis", methods=['POST'])
def gann_full_analysis():
    """Comprehensive Gann analysis including SQ9, angles, time cycles"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        lookback_days = data.get('lookbackDays', 100)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if price_data is None:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        gann_engine = GannEngine(gann_config=CONFIG.get('gann_config', {}))
        
        sq9_levels = gann_engine.calculate_sq9_levels(price_data)
        gann_angles = gann_engine.calculate_gann_angles(price_data)
        
        current_price = float(price_data['close'].iloc[-1])
        
        response = {
            'symbol': symbol,
            'currentPrice': current_price,
            'timestamp': format_timestamp(datetime.now()),
            'sq9Levels': sq9_levels,
            'gannAngles': gann_angles.to_dict(orient='records') if gann_angles is not None else [],
            'analysis': {
                'nearestSupport': min([l for l in sq9_levels.get('support', []) if l < current_price], default=current_price * 0.95),
                'nearestResistance': min([l for l in sq9_levels.get('resistance', []) if l > current_price], default=current_price * 1.05),
            }
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Gann full analysis error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# EHLERS DSP ENDPOINTS
# ============================================================================

@app.route("/api/ehlers/analyze", methods=['POST'])
def ehlers_analyze():
    """Ehlers DSP analysis"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        lookback_days = data.get('lookbackDays', 100)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if price_data is None:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        ehlers_engine = EhlersEngine(ehlers_config=CONFIG.get('ehlers_config', {}))
        indicators = ehlers_engine.calculate_all_indicators(price_data)
        
        # Format response
        latest = indicators.iloc[-1]
        history = indicators.tail(50).reset_index()
        
        response = {
            'symbol': symbol,
            'timestamp': format_timestamp(datetime.now()),
            'current': {
                'mama': float(latest.get('mama', 0)),
                'fama': float(latest.get('fama', 0)),
                'cycle': float(latest.get('cycle', 0)) if 'cycle' in latest else None,
            },
            'history': [
                {
                    'time': format_timestamp(row.get('timestamp', row.get('index', ''))),
                    'mama': float(row.get('mama', 0)),
                    'fama': float(row.get('fama', 0)),
                    'price': float(row.get('close', 0)),
                }
                for _, row in history.iterrows()
            ]
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Ehlers analysis error: {e}")
        return jsonify({"error": str(e)}), 500

# (Continued in next part due to length...)
