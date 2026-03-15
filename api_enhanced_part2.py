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
# APP STARTUP
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting Gann Quant AI Enhanced Flask API server with WebSocket support...")
    # Use SocketIO run instead of app.run for WebSocket support
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
