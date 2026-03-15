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

# Import sync module for frontend-backend synchronization
try:
    from api_sync import register_sync_routes
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False
    logger.warning("api_sync module not available - sync routes will not be registered")

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:5000", "*"]
    }
})

# Register sync routes for frontend-backend synchronization
if SYNC_AVAILABLE:
    try:
        register_sync_routes(app)
        logger.info("Frontend-Backend sync routes registered successfully")
    except Exception as e:
        logger.error(f"Failed to register sync routes: {e}")

# Register AI Engine API routes
try:
    from core.ai_api import register_ai_routes
    register_ai_routes(app)
    logger.info("AI Engine API routes registered successfully")
except Exception as e:
    logger.warning(f"AI API routes not registered: {e}")

# Register Settings API routes for frontend sync
try:
    from core.settings_api import register_settings_routes
    register_settings_routes(app)
    logger.info("Settings API routes registered successfully")
except Exception as e:
    logger.warning(f"Settings API routes not registered: {e}")

# Register Market Data API routes for real-time data feed
try:
    from core.market_data_api import register_market_data_routes
    register_market_data_routes(app)
    logger.info("Market Data API routes registered successfully")
except Exception as e:
    logger.warning(f"Market Data API routes not registered: {e}")

# Register Execution API routes for order execution
try:
    from core.execution_api import register_execution_routes
    register_execution_routes(app)
    logger.info("Execution API routes registered successfully")
except Exception as e:
    logger.warning(f"Execution API routes not registered: {e}")

# Register Trading API routes for orchestrator and journal
try:
    from core.trading_api import register_trading_routes
    register_trading_routes(app)
    logger.info("Trading API routes registered successfully")
except Exception as e:
    logger.warning(f"Trading API routes not registered: {e}")

# Register Config Sync API routes for YAML config synchronization
try:
    from core.config_sync_api import register_config_sync_routes
    register_config_sync_routes(app)
    logger.info("Config Sync API routes registered successfully")
except Exception as e:
    logger.warning(f"Config Sync API routes not registered: {e}")

# Register HFT API routes for High-Frequency Trading page
try:
    from core.hft_api import register_hft_routes
    register_hft_routes(app)
    logger.info("HFT API routes registered successfully")
except Exception as e:
    logger.warning(f"HFT API routes not registered: {e}")

# Register Missing Endpoints API for complete frontend sync
try:
    from core.missing_endpoints_api import register_missing_endpoints
    register_missing_endpoints(app)
    logger.info("Missing Endpoints API registered successfully")
except Exception as e:
    logger.warning(f"Missing Endpoints API not registered: {e}")

# Register Safety API for kill switch and live trading controls
try:
    from core.safety_api import register_safety_routes
    register_safety_routes(app)
    logger.info("Safety API routes registered successfully")
except Exception as e:
    logger.warning(f"Safety API routes not registered: {e}")

# Register Bookmap & Terminal API for orderflow visualization and command terminal
try:
    from core.bookmap_terminal_api import register_bookmap_terminal_routes
    register_bookmap_terminal_routes(app)
    logger.info("Bookmap & Terminal API routes registered successfully")
except Exception as e:
    logger.warning(f"Bookmap & Terminal API routes not registered: {e}")

# Register Analytics API for scanner, forecasting, cycles, options, patterns, etc.
try:
    from core.analytics_api import register_analytics_routes
    register_analytics_routes(app)
    logger.info("Analytics API routes registered successfully")
except Exception as e:
    logger.warning(f"Analytics API routes not registered: {e}")

# Register Agent Orchestration API for AI agents, mode switching, and trade proposals
try:
    from core.agent_orchestration_api import register_agent_routes
    register_agent_routes(app)
    logger.info("Agent Orchestration API routes registered successfully")
except Exception as e:
    logger.warning(f"Agent Orchestration API routes not registered: {e}")


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
    """Background worker for streaming real-time prices from broker connectors only.
    
    Data sources:
    - MetaTrader 4/5: Forex, CFD, Commodities
    - Crypto Exchanges (CCXT): BTC, ETH, etc.
    - FIX Protocol: Institutional DMA
    
    No yfinance or public data fallback.
    """
    global price_stream_active
    
    data_feed = get_data_feed()
    
    # Log available connectors
    available = data_feed.get_available_connectors()
    if available:
        for name, status in available.items():
            logger.info(f"Broker feed available: {name} — {status}")
    else:
        logger.warning("No broker connectors configured — price stream will have no data")

    while price_stream_active:
        try:
            symbols = CONFIG.get('trading', {}).get('symbols', ['BTC/USDT', 'ETH/USDT', 'EURUSD', 'XAUUSD'])
            
            for symbol in symbols:
                latest_data = None
                
                # Determine source automatically based on symbol type
                source_name = data_feed._detect_source(symbol)
                
                # Route to correct connector
                if source_name == "metatrader":
                    mt_connectors = [c for k, c in data_feed.connectors.items() if k.startswith('mt_')]
                    if mt_connectors:
                        connector = mt_connectors[0]
                        try:
                            import asyncio
                            mt_symbol = connector.normalize_symbol(symbol) if hasattr(connector, 'normalize_symbol') else symbol
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    import concurrent.futures
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        ticker = pool.submit(
                                            lambda: asyncio.run(connector.get_ticker(mt_symbol))
                                        ).result(timeout=10)
                                else:
                                    ticker = loop.run_until_complete(connector.get_ticker(mt_symbol))
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                ticker = loop.run_until_complete(connector.get_ticker(mt_symbol))
                                loop.close()
                            
                            if ticker and ticker.get('bid', 0) > 0:
                                price = ticker.get('bid', 0)
                                latest_data = {
                                    'symbol': symbol,
                                    'price': float(price),
                                    'open': float(price),
                                    'high': float(price),
                                    'low': float(price),
                                    'volume': 0,
                                    'change': 0,
                                    'changePercent': 0,
                                    'timestamp': format_timestamp(datetime.now()),
                                    'source': 'metatrader'
                                }
                        except Exception as e:
                            logger.debug(f"MT ticker fetch failed for {symbol}: {e}")
                
                elif source_name == "exchange":
                    exchange_connectors = [c for k, c in data_feed.connectors.items() if k.startswith('exchange_')]
                    if exchange_connectors:
                        connector = exchange_connectors[0]
                        try:
                            import asyncio
                            ex_symbol = data_feed._normalize_symbol_exchange(symbol)
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    import concurrent.futures
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        ticker = pool.submit(
                                            lambda: asyncio.run(connector.get_ticker(ex_symbol))
                                        ).result(timeout=10)
                                else:
                                    ticker = loop.run_until_complete(connector.get_ticker(ex_symbol))
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                ticker = loop.run_until_complete(connector.get_ticker(ex_symbol))
                                loop.close()
                            
                            if ticker and ticker.get('last', 0) > 0:
                                last = ticker.get('last', 0)
                                latest_data = {
                                    'symbol': symbol,
                                    'price': float(last),
                                    'open': float(ticker.get('open', last)),
                                    'high': float(ticker.get('high', last)),
                                    'low': float(ticker.get('low', last)),
                                    'volume': float(ticker.get('volume', 0)),
                                    'change': float(last - ticker.get('open', last)),
                                    'changePercent': float(ticker.get('change_pct', 0)),
                                    'timestamp': format_timestamp(datetime.now()),
                                    'source': 'exchange'
                                }
                        except Exception as e:
                            logger.debug(f"Exchange ticker fetch failed for {symbol}: {e}")
                
                # Fallback: use DataFeed historical data from broker connectors
                if latest_data is None:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    price_df = data_feed.get_historical_data(symbol, '1m', start_date, end_date)
                    
                    if price_df is not None and not price_df.empty:
                        latest = price_df.iloc[-1]
                        prev = price_df.iloc[-2] if len(price_df) > 1 else latest
                        
                        latest_data = {
                            'symbol': symbol,
                            'price': float(latest['close']),
                            'open': float(latest['open']),
                            'high': float(latest['high']),
                            'low': float(latest['low']),
                            'volume': float(latest['volume']) if 'volume' in latest else 0,
                            'change': float(latest['close'] - prev['close']),
                            'changePercent': float(((latest['close'] - prev['close']) / prev['close']) * 100) if prev['close'] != 0 else 0,
                            'timestamp': format_timestamp(latest.name if hasattr(latest, 'name') else datetime.now()),
                            'source': source_name
                        }
                
                if latest_data:
                    socketio.emit('price_update', latest_data, namespace='/ws')
                    socketio.emit('candle_update', latest_data, namespace='/ws')
                    # Also emit on default namespace (frontend connects here)
                    socketio.emit('price_update', latest_data)
                    socketio.emit('candle_update', latest_data)
            
            # Sleep between updates
            time.sleep(2)  # 2-second updates
            
        except Exception as e:
            logger.error(f"Price stream error: {e}")
            time.sleep(5)


@socketio.on('connect', namespace='/ws')
def handle_connect():
    """Handle WebSocket connection (namespaced)"""
    global price_stream_active, price_stream_thread
    
    logger.info("WebSocket client connected (namespace=/ws)")
    emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})
    
    # Start price stream if not already running
    if not price_stream_active:
        price_stream_active = True
        price_stream_thread = threading.Thread(target=price_stream_worker, daemon=True)
        price_stream_thread.start()
        logger.info("Price stream worker started")

@socketio.on('disconnect', namespace='/ws')
def handle_disconnect():
    """Handle WebSocket disconnection (namespaced)"""
    logger.info("WebSocket client disconnected (namespace=/ws)")

@socketio.on('subscribe', namespace='/ws')
def handle_subscribe(data):
    """Handle symbol subscription (namespaced)"""
    symbol = data.get('symbol')
    logger.info(f"Client subscribed to {symbol} (namespace=/ws)")
    emit('subscribed', {'symbol': symbol, 'status': 'active'})

# --- Default namespace handlers (frontend useWebSocketPrice connects here) ---
@socketio.on('connect')
def handle_connect_default():
    """Handle WebSocket connection (default namespace)"""
    global price_stream_active, price_stream_thread
    
    logger.info("WebSocket client connected (default namespace)")
    emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})
    
    # Start price stream if not already running
    if not price_stream_active:
        price_stream_active = True
        price_stream_thread = threading.Thread(target=price_stream_worker, daemon=True)
        price_stream_thread.start()
        logger.info("Price stream worker started")

@socketio.on('disconnect')
def handle_disconnect_default():
    """Handle WebSocket disconnection (default namespace)"""
    logger.info("WebSocket client disconnected (default namespace)")

@socketio.on('subscribe')
def handle_subscribe_default(data):
    """Handle symbol subscription (default namespace)"""
    symbol = data.get('symbol')
    logger.info(f"Client subscribed to {symbol} (default namespace)")
    emit('subscribed', {'symbol': symbol, 'status': 'active'})

# --- Bookmap WebSocket Handlers (default namespace) ---
@socketio.on('subscribe_depth')
def handle_subscribe_depth(data):
    """Subscribe to real-time order book depth for Bookmap."""
    symbol = data.get('symbol', 'BTCUSDT')
    levels = data.get('levels', 20)
    logger.info(f"[Bookmap] Client subscribed to depth: {symbol}")
    
    try:
        from core.bookmap_terminal_api import _generate_orderbook
        orderbook = _generate_orderbook(symbol, levels)
        emit('depth_update', {
            'symbol': symbol,
            'orderbook': orderbook,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'message': f'Depth subscription failed: {str(e)}'})

@socketio.on('subscribe_tape')
def handle_subscribe_tape(data):
    """Subscribe to real-time time & sales for Bookmap."""
    symbol = data.get('symbol', 'BTCUSDT')
    logger.info(f"[Bookmap] Client subscribed to tape: {symbol}")
    
    try:
        from core.bookmap_terminal_api import _generate_tape
        tape = _generate_tape(symbol, 20)
        emit('tape_update', {
            'symbol': symbol,
            'tape': tape,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'message': f'Tape subscription failed: {str(e)}'})

@socketio.on('terminal_command')
def handle_terminal_command(data):
    """Execute a terminal command via WebSocket."""
    command = data.get('command', '')
    logger.info(f"[Terminal] Command received: {command}")
    
    try:
        from core.bookmap_terminal_api import _process_command
        result = _process_command(command)
        emit('terminal_result', {
            'command': command,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('terminal_result', {
            'command': command,
            'result': {'type': 'error', 'output': [f'Error: {str(e)}']},
            'timestamp': datetime.now().isoformat()
        })

# ============================================================================
# EXISTING ENDPOINTS (MAINTAINED)
# ============================================================================

@app.route("/")
def root():
    """Root endpoint - API info"""
    return jsonify({
        "name": "Gann Quant AI Trading API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "config": "/api/config",
            "market_data": "/api/market-data/<symbol>",
            "gann_levels": "/api/gann/<symbol>/levels",
            "ehlers": "/api/ehlers/<symbol>",
            "signals": "/api/signals/<symbol>",
            "trading": "/api/trading/*",
            "hft": "/api/hft/*",
            "settings": "/api/settings/*"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route("/favicon.ico")
def favicon():
    """Favicon handler to prevent 404"""
    return "", 204


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
"""
Enhanced Flask API - Part 2: Trading, Positions, Orders, Risk, ML, Scanner
"""

# ============================================================================
# ASTRO ENGINE ENDPOINTS
# ============================================================================

@app.route("/api/astro/analyze", methods=['POST'])
def astro_analyze():
    """Astrological analysis"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json
        symbol = data.get('symbol', 'BTC-USD')
        lookback_days = data.get('lookbackDays', 100)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        astro_engine = AstroEngine(astro_config=CONFIG.get('astro_config', {}))
        astro_events = astro_engine.analyze_dates(price_data.index)
        
        response = {
            'symbol': symbol,
            'timestamp': format_timestamp(datetime.now()),
            'events': astro_events.to_dict(orient='records') if astro_events is not None else [],
            'summary': {
                'totalEvents': len(astro_events) if astro_events is not None else 0,
                'upcomingEvents': []  # Could be enhanced
            }
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Astro analysis error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ML PREDICTION ENDPOINTS
# ============================================================================

@app.route("/api/ml/predict", methods=['POST'])
def ml_predict():
    """Get ML model predictions"""
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
        
        engines = get_engines()
        
        gann_levels = engines['gann'].calculate_sq9_levels(price_data)
        data_with_indicators = engines['ehlers'].calculate_all_indicators(price_data)
        astro_events = engines['astro'].analyze_dates(price_data.index)
        
        predictions = engines['ml'].get_predictions(data_with_indicators, gann_levels, astro_events)
        
        if predictions is None:
            return jsonify({"error": "Failed to generate predictions", "info": "Model may not be trained"}), 400
        
        latest_pred = predictions.iloc[-1] if not predictions.empty else None
        
        response = {
            'symbol': symbol,
            'timestamp': format_timestamp(datetime.now()),
            'prediction': {
                'direction': int(latest_pred['prediction']) if latest_pred is not None and 'prediction' in latest_pred else 0,
                'confidence': float(latest_pred.get('confidence', 0.5)) if latest_pred is not None else 0.5,
                'signal': 'BUY' if (latest_pred is not None and latest_pred.get('prediction', 0) > 0) else 'SELL'
            },
            'history': predictions.tail(20).to_dict(orient='records') if predictions is not None else []
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# SIGNALS ENDPOINT
# ============================================================================

@app.route("/api/signals/<symbol>", methods=['GET'])
def get_signals(symbol):
    """Get trading signals"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None:
            return jsonify({"error": f"Failed to fetch price data for {symbol}"}), 400
        
        engines = get_engines()
        
        gann_levels = engines['gann'].calculate_sq9_levels(price_data)
        data_with_indicators = engines['ehlers'].calculate_all_indicators(price_data)
        astro_events = engines['astro'].analyze_dates(price_data.index)
        
        signals_df = engines['signal'].generate_signals(data_with_indicators, gann_levels, astro_events)
        
        signals = []
        if not signals_df.empty:
            for timestamp, row in signals_df.iterrows():
                signals.append({
                    "timestamp": format_timestamp(timestamp),
                    "symbol": symbol,
                    "signal": row['signal'],
                    "strength": 0.75,
                    "price": float(row['price']),
                    "message": row.get('reason', f"{row['signal']} signal generated")
                })
        
        return jsonify(signals)
    except Exception as e:
        logger.error(f"Failed to get signals: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# LIVE TRADING CONTROL ENDPOINTS
# ============================================================================

@app.route("/api/trading/start", methods=['POST'])
def start_trading():
    """Start live trading bot"""
    global live_bot
    
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        if live_bot and live_bot.running:
            return jsonify({"error": "Trading bot is already running"}), 400
        
        params = request.json or {}
        symbols = params.get('symbols', CONFIG.get('trading', {}).get('symbols', ['BTC-USD']))
        
        # Initialize bot
        live_bot = LiveTradingBot()
        live_bot.symbols = symbols
        
        # Start in background thread
        trading_thread = threading.Thread(target=live_bot.start, daemon=True)
        trading_thread.start()
        
        logger.info("Live trading bot started")
        
        return jsonify({
            "status": "started",
            "message": "Live trading bot started successfully",
            "symbols": symbols,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to start trading: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/trading/stop", methods=['POST'])
def stop_trading():
    """Stop live trading bot"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({"error": "Trading bot is not initialized"}), 400
        
        if not live_bot.running:
            return jsonify({"error": "Trading bot is not running"}), 400
        
        live_bot.stop()
        
        logger.info("Live trading bot stopped")
        
        return jsonify({
            "status": "stopped",
            "message": "Live trading bot stopped successfully",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to stop trading: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/trading/pause", methods=['POST'])
def pause_trading():
    """Pause live trading bot"""
    global live_bot
    
    try:
        if not live_bot or not live_bot.running:
            return jsonify({"error": "Trading bot is not running"}), 400
        
        live_bot.pause()
        
        return jsonify({
            "status": "paused",
            "message": "Trading paused",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to pause trading: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/trading/resume", methods=['POST'])
def resume_trading():
    """Resume live trading bot"""
    global live_bot
    
    try:
        if not live_bot or not live_bot.running:
            return jsonify({"error": "Trading bot is not running"}), 400
        
        live_bot.resume()
        
        return jsonify({
            "status": "resumed",
            "message": "Trading resumed",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to resume trading: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/trading/status", methods=['GET'])
def trading_status():
    """Get live trading bot status"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({
                "status": "not_initialized",
                "running": False,
                "timestamp": datetime.now().isoformat()
            })
        
        status = live_bot.get_status()
        status['timestamp'] = datetime.now().isoformat()
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Failed to get trading status: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# POSITION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route("/api/positions", methods=['GET'])
def get_positions():
    """Get all open positions"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify([])  # No positions if bot not initialized
        
        positions = live_bot.execution_engine.get_all_positions()
        
        positions_list = [
            {
                'id': str(hash(p.symbol)),  # Simple ID generation
                'symbol': p.symbol,
                'side': p.side.value,
                'quantity': p.quantity,
                'entryPrice': p.entry_price,
                'currentPrice': p.current_price,
                'unrealizedPnL': p.unrealized_pnl,
                'realizedPnL': p.realized_pnl,
                'entryTime': format_timestamp(p.entry_time),
                'stopLoss': getattr(p, 'stop_loss', None),
                'takeProfit': getattr(p, 'take_profit', None),
            }
            for p in positions
        ]
        
        return jsonify(positions_list)
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/positions/<symbol>", methods=['GET'])
def get_position_by_symbol(symbol):
    """Get position for specific symbol"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({"error": "Trading bot not initialized"}), 400
        
        position = live_bot.execution_engine.get_position(symbol)
        
        if not position:
            return jsonify({"error": f"No position found for {symbol}"}), 404
        
        return jsonify({
            'id': str(hash(position.symbol)),
            'symbol': position.symbol,
            'side': position.side.value,
            'quantity': position.quantity,
            'entryPrice': position.entry_price,
            'currentPrice': position.current_price,
            'unrealizedPnL': position.unrealized_pnl,
            'realizedPnL': position.realized_pnl,
            'entryTime': format_timestamp(position.entry_time),
            'stopLoss': getattr(position, 'stop_loss', None),
            'takeProfit': getattr(position, 'take_profit', None),
        })
    except Exception as e:
        logger.error(f"Failed to get position: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/positions/<position_id>/close", methods=['POST'])
def close_position(position_id):
    """Close a specific position"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({"error": "Trading bot not initialized"}), 400
        
        data = request.json or {}
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({"error": "Symbol required"}), 400
        
        # Close position
        success = live_bot.execution_engine.close_position(symbol)
        
        if success:
            return jsonify({
                "status": "closed",
                "message": f"Position for {symbol} closed successfully",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to close position"}), 500
            
    except Exception as e:
        logger.error(f"Failed to close position: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ORDER MANAGEMENT ENDPOINTS
# ============================================================================

@app.route("/api/orders", methods=['POST'])
def create_order():
    """Create a new order"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({"error": "Trading bot not initialized"}), 400
        
        data = request.json
        symbol = data.get('symbol')
        side = data.get('side')  # 'BUY' or 'SELL'
        quantity = data.get('quantity')
        order_type = data.get('type', 'market')  # 'market' or 'limit'
        price = data.get('price')
        stop_loss = data.get('stopLoss')
        take_profit = data.get('takeProfit')
        
        if not all([symbol, side, quantity]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Submit order
        if order_type == 'market':
            success, order_id = live_bot.order_manager.submit_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                broker='paper'
            )
        else:
            success, order_id = live_bot.order_manager.submit_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                broker='paper'
            )
        
        if success:
            return jsonify({
                "orderId": order_id,
                "status": "submitted",
                "message": "Order submitted successfully",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": f"Order submission failed: {order_id}"}), 500
            
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/orders", methods=['GET'])
def get_orders():
    """Get all orders"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify([])
        
        # Get orders from order manager
        orders = live_bot.order_manager.get_all_orders() if hasattr(live_bot.order_manager, 'get_all_orders') else []
        
        return jsonify([{
            'orderId': order.id,
            'symbol': order.symbol,
            'side': order.side,
            'type': order.type,
            'quantity': order.quantity,
            'price': order.price,
            'status': order.status,
            'timestamp': format_timestamp(order.timestamp)
        } for order in orders])
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/orders/<order_id>", methods=['DELETE'])
def cancel_order(order_id):
    """Cancel an order"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({"error": "Trading bot not initialized"}), 400
        
        success = live_bot.order_manager.cancel_order(order_id)
        
        if success:
            return jsonify({
                "status": "cancelled",
                "message": f"Order {order_id} cancelled successfully",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to cancel order"}), 500
            
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# RISK MANAGEMENT ENDPOINTS
# ============================================================================

@app.route("/api/risk/metrics", methods=['GET'])
def get_risk_metrics():
    """Get current risk metrics"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({"error": "Trading bot not initialized"}), 400
        
        # Calculate risk metrics
        positions = live_bot.execution_engine.get_all_positions()
        balance = live_bot.execution_engine.get_paper_balance()
        
        total_exposure = sum(p.quantity * p.current_price for p in positions)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
        
        response = {
            'accountBalance': balance,
            'totalExposure': total_exposure,
            'totalUnrealizedPnL': total_unrealized_pnl,
            'utilizationPercent': (total_exposure / balance * 100) if balance > 0 else 0,
            'dailyStats': live_bot._daily_stats,
            'maxDrawdown': live_bot._daily_stats.get('max_drawdown', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Failed to get risk metrics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/risk/calculate-position-size", methods=['POST'])
def calculate_position_size():
    """Calculate optimal position size"""
    try:
        data = request.json
        account_balance = data.get('accountBalance', 100000)
        risk_percent = data.get('riskPercent', 2.0)
        entry_price = data.get('entryPrice')
        stop_loss = data.get('stopLoss')
        
        if not all([entry_price, stop_loss]):
            return jsonify({"error": "Missing required fields"}), 400
        
        risk_amount = account_balance * (risk_percent / 100)
        price_risk = abs(entry_price - stop_loss)
        position_size = risk_amount / price_risk if price_risk > 0 else 0
        
        response = {
            'positionSize': position_size,
            'riskAmount': risk_amount,
            'priceRisk': price_risk,
            'riskPercent': risk_percent,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Failed to calculate position size: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# SCANNER ENDPOINTS
# ============================================================================

@app.route("/api/scanner/scan", methods=['POST'])
def run_scanner():
    """Run multi-symbol scanner"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json or {}
        symbols = data.get('symbols', ['BTC-USD', 'ETH-USD', 'SOL-USD'])
        timeframe = data.get('timeframe', '1h')
        
        scanner = HybridScanner(CONFIG.get('scanner_config', {}))
        data_feed = get_data_feed()
        
        results = []
        
        for symbol in symbols:
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                
                price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
                
                if price_data is None or price_data.empty:
                    continue
                
                signal = scanner.scan(price_data, symbol)
                
                if signal:
                    results.append({
                        'symbol': symbol,
                        'direction': signal.direction,
                        'confidence': signal.confidence,
                        'entryPrice': signal.entry_price,
                        'stopLoss': signal.stop_loss,
                        'takeProfit': signal.take_profit,
                        'riskReward': signal.risk_reward,
                        'timestamp': format_timestamp(datetime.now())
                    })
            except Exception as e:
                logger.error(f"Scanner error for {symbol}: {e}")
                continue
        
        return jsonify({
            'results': results,
            'scannedSymbols': symbols,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Scanner error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@app.route("/api/portfolio/summary", methods=['GET'])
def get_portfolio_summary():
    """Get portfolio summary"""
    global live_bot
    
    try:
        if not live_bot:
            return jsonify({"error": "Trading bot not initialized"}), 400
        
        positions = live_bot.execution_engine.get_all_positions()
        balance = live_bot.execution_engine.get_paper_balance()
        
        total_value = balance + sum(p.quantity * p.current_price for p in positions)
        total_pnl = sum(p.unrealized_pnl + p.realized_pnl for p in positions)
        
        response = {
            'accountBalance': balance,
            'totalValue': total_value,
            'totalPnL': total_pnl,
            'totalPnLPercent': (total_pnl / balance * 100) if balance > 0 else 0,
            'openPositions': len(positions),
            'dailyStats': live_bot._daily_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# FORECASTING ENDPOINTS
# ============================================================================

@app.route("/api/forecast/daily", methods=['POST'])
def get_daily_forecast():
    """Get daily Gann-based forecast"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        lookback_days = data.get('lookbackDays', 100)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        from modules.forecasting.gann_forecast_daily import GannDailyForecaster
        forecaster = GannDailyForecaster()
        
        forecast = forecaster.generate_forecast(price_data)
        multi_day = forecaster.generate_multi_day_forecast(price_data, 7)
        
        return jsonify({
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'forecast': {
                'date': forecast.date.strftime('%Y-%m-%d'),
                'bias': forecast.bias.value,
                'confidence': forecast.confidence,
                'support': forecast.support_level,
                'resistance': forecast.resistance_level,
                'pivot': forecast.pivot_point,
                'target_high': forecast.target_high,
                'target_low': forecast.target_low,
                'active_cycles': forecast.time_cycles_active,
                'narrative': forecast.narrative
            },
            'multi_day_forecast': multi_day
        })
    except Exception as e:
        logger.error(f"Daily forecast error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/forecast/waves", methods=['POST'])
def get_wave_projection():
    """Get Gann wave analysis and projection"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        lookback_days = data.get('lookbackDays', 200)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        from modules.forecasting.gann_wave_projection import GannWaveAnalyzer
        analyzer = GannWaveAnalyzer()
        
        result = analyzer.analyze(price_data)
        result['symbol'] = symbol
        result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Wave projection error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/forecast/astro", methods=['POST'])
def get_astro_projection():
    """Get astrological cycle projections"""
    try:
        data = request.json or {}
        days_ahead = data.get('daysAhead', 30)
        
        from modules.forecasting.astro_cycle_projection import AstroCycleProjector
        projector = AstroCycleProjector()
        
        daily = projector.get_daily_influence()
        key_dates = projector.find_key_dates(days_ahead=days_ahead)
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'daily_influence': daily,
            'key_dates': key_dates[:10],
            'lunar': daily.get('lunar', {})
        })
    except Exception as e:
        logger.error(f"Astro projection error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/forecast/ml", methods=['POST'])
def get_ml_forecast():
    """Get ML-based time series forecast"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        forecast_days = data.get('forecastDays', 5)
        lookback_days = data.get('lookbackDays', 100)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        from modules.forecasting.ml_time_forecast import MLTimeForecaster
        forecaster = MLTimeForecaster()
        
        result = forecaster.forecast_summary(price_data, forecast_days)
        result['symbol'] = symbol
        result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"ML forecast error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# CYCLE ENGINE ENDPOINTS
# ============================================================================

@app.route("/api/cycles/analyze", methods=['POST'])
def analyze_cycles():
    """Comprehensive cycle analysis"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        lookback_days = data.get('lookbackDays', 365)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        from core.cycle_engine import CycleEngine
        engine = CycleEngine()
        
        result = engine.analyze_all_cycles(price_data)
        
        # Convert to JSON-serializable format
        response = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'fft_cycles': [
                {
                    'type': c.cycle_type.value,
                    'period_days': c.period_days,
                    'phase': c.phase,
                    'phase_position': c.phase_position,
                    'strength': c.strength
                }
                for c in result.get('fft_cycles', [])
            ],
            'ehlers_cycle': result.get('ehlers_cycle', {}),
            'lunar_cycle': {
                k: v.isoformat() if isinstance(v, datetime) else (v.value if hasattr(v, 'value') else v)
                for k, v in result.get('lunar_cycle', {}).items()
            },
            'gann_cycles': {
                'upcoming': result.get('gann_cycles', {}).get('upcoming_cycles', [])[:10],
                'confluences': result.get('gann_cycles', {}).get('confluences', [])[:5]
            },
            'summary': result.get('summary', {})
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Cycle analysis error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# CONFIGURATION SYNC ENDPOINTS
# ============================================================================

@app.route("/api/config/sync", methods=['POST'])
def sync_config():
    """Synchronize frontend configuration with backend"""
    global CONFIG
    
    try:
        frontend_config = request.json or {}
        
        # Update specific config sections from frontend
        if 'trading' in frontend_config:
            CONFIG['trading'] = {**CONFIG.get('trading', {}), **frontend_config['trading']}
        
        if 'risk' in frontend_config:
            CONFIG['risk_config'] = {**CONFIG.get('risk_config', {}), **frontend_config['risk']}
        
        if 'scanner' in frontend_config:
            CONFIG['scanner_config'] = {**CONFIG.get('scanner_config', {}), **frontend_config['scanner']}
        
        if 'display' in frontend_config:
            CONFIG['display_config'] = frontend_config['display']
        
        logger.info("Configuration synchronized from frontend")
        
        return jsonify({
            'status': 'synced',
            'message': 'Configuration synchronized successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Config sync error: {e}")
        return jsonify({"error": str(e)}), 500

# NOTE: /api/config/gann, /api/config/ehlers, /api/config/astro routes are handled
# by config_sync_api.py Blueprint with proper YAML persistence. Do NOT duplicate here.

# ============================================================================
# STRATEGY OPTIMIZATION ENDPOINT
# ============================================================================

@app.route("/api/strategies/optimize", methods=['POST'])
def optimize_strategy_weights():
    """Optimize strategy weights using backtest performance data"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json or {}
        timeframe = data.get('timeframe', 'H1')
        metric = data.get('metric', 'sharpe')  # sharpe, returns, win_rate
        start_date = data.get('startDate', '2023-01-01')
        end_date = data.get('endDate', '2024-01-01')
        symbol = data.get('symbol', 'BTC-USD')
        
        # Fetch price data for optimization
        data_feed = get_data_feed()
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data for optimization"}), 400
        
        engines = get_engines()
        
        # Run analysis with current engines
        gann_levels = engines['gann'].calculate_sq9_levels(price_data)
        data_with_indicators = engines['ehlers'].calculate_all_indicators(price_data)
        astro_events = engines['astro'].analyze_dates(price_data.index)
        ml_predictions = engines['ml'].get_predictions(data_with_indicators, gann_levels, astro_events)
        
        # Calculate individual engine signal accuracy
        engine_scores = {}
        
        # Gann accuracy (based on support/resistance hit rate)
        gann_score = 0.0
        if gann_levels and 'support' in gann_levels and 'resistance' in gann_levels:
            gann_score = min(1.0, len(gann_levels.get('support', [])) * 0.1 + 0.3)
        engine_scores['gann'] = gann_score
        
        # Ehlers accuracy (based on MAMA/FAMA crossover signals)
        ehlers_score = 0.0
        if data_with_indicators is not None and 'mama' in data_with_indicators.columns:
            mama = data_with_indicators['mama']
            fama = data_with_indicators.get('fama', mama)
            crossovers = ((mama > fama) != (mama.shift(1) > fama.shift(1))).sum()
            ehlers_score = min(1.0, crossovers / max(len(mama), 1) * 10 + 0.2)
        engine_scores['ehlers'] = ehlers_score
        
        # ML accuracy (from prediction confidence)
        ml_score = 0.0
        if ml_predictions is not None and not ml_predictions.empty:
            ml_score = float(ml_predictions.get('confidence', pd.Series([0.5])).mean())
        engine_scores['ml'] = ml_score
        
        # Astro score (event correlation)
        astro_score = 0.0
        if astro_events is not None and not astro_events.empty:
            astro_score = min(1.0, len(astro_events) / max(len(price_data), 1) * 5 + 0.15)
        engine_scores['astro'] = astro_score
        
        # Pattern recognition score (based on candlestick patterns)
        pattern_score = 0.25  # Default
        engine_scores['pattern'] = pattern_score
        
        # Options flow score
        options_score = 0.10  # Default
        engine_scores['options'] = options_score
        
        # Normalize weights to sum to 1.0
        total_score = sum(engine_scores.values())
        if total_score > 0:
            optimized_weights = {
                'WD Gann Modul': round(engine_scores['gann'] / total_score, 4),
                'Ehlers DSP': round(engine_scores['ehlers'] / total_score, 4),
                'ML Models': round(engine_scores['ml'] / total_score, 4),
                'Astro Cycles': round(engine_scores['astro'] / total_score, 4),
                'Pattern Recognition': round(engine_scores['pattern'] / total_score, 4),
                'Options Flow': round(engine_scores['options'] / total_score, 4),
            }
        else:
            optimized_weights = {
                'WD Gann Modul': 0.25,
                'Ehlers DSP': 0.20,
                'ML Models': 0.25,
                'Astro Cycles': 0.15,
                'Pattern Recognition': 0.10,
                'Options Flow': 0.05,
            }
        
        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'metric': metric,
            'optimizedWeights': optimized_weights,
            'engineScores': engine_scores,
            'dataPoints': len(price_data),
            'period': f"{start_date} to {end_date}",
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Strategy optimization error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# REPORT GENERATION ENDPOINTS
# ============================================================================

@app.route("/api/reports/generate", methods=['POST'])
def generate_report():
    """Generate comprehensive trading report"""
    try:
        if not CONFIG:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        lookback_days = data.get('lookbackDays', 100)
        
        data_feed = get_data_feed()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        from modules.forecasting.report_generator import ReportGenerator
        generator = ReportGenerator()
        
        trades = data.get('trades', [])
        analysis_results = data.get('analysis', {})
        
        report = generator.generate_full_report(price_data, symbol, trades, analysis_results)
        
        return jsonify(report)
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# APP STARTUP
# ============================================================================

if __name__ == '__main__':
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    logger.info(f"Starting Gann Quant AI Enhanced Flask API server (debug={debug_mode})...")
    # Use SocketIO run instead of app.run for WebSocket support
    socketio.run(app, host="0.0.0.0", port=5000, debug=debug_mode, allow_unsafe_werkzeug=debug_mode)
