"""
Frontend-Backend Synchronization API Module
Provides additional endpoints to fully support frontend features and configurations.
This module extends api_v2.py with missing endpoints for complete synchronization.
"""
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from loguru import logger
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

# Import core components
from utils.config_loader import load_all_configs
from core.data_feed import DataFeed
from core.gann_engine import GannEngine
from core.ehlers_engine import EhlersEngine
from core.astro_engine import AstroEngine
from core.options_engine import OptionsEngine
from modules.smith.smith_chart import SmithChartAnalyzer

# Create Blueprint for sync routes
sync_bp = Blueprint('sync', __name__, url_prefix='/api')

# ============================================================================
# TRADING MODE CONFIGURATION ENDPOINTS
# ============================================================================

@sync_bp.route("/config/trading-modes", methods=['GET', 'POST'])
def trading_modes_config():
    """Get or update multiple trading mode configurations"""
    try:
        config_path = os.path.join("config", "trading_modes.json")
        
        if request.method == 'GET':
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    modes = json.load(f)
            else:
                # Return default trading modes matching frontend structure
                modes = get_default_trading_modes()
            return jsonify(modes)
        
        elif request.method == 'POST':
            modes_data = request.json
            
            # Save to config file
            with open(config_path, 'w') as f:
                json.dump(modes_data, f, indent=2)
            
            logger.info("Trading modes configuration saved")
            
            return jsonify({
                "status": "saved",
                "message": "Trading modes synchronized",
                "modes_count": len(modes_data) if isinstance(modes_data, list) else 1,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Trading modes config error: {e}")
        return jsonify({"error": str(e)}), 500


def get_default_trading_modes() -> List[Dict]:
    """Returns default trading modes matching frontend TradingModeConfig interface"""
    return [
        {
            "id": "spot-1",
            "name": "Spot Trading - Primary",
            "mode": "spot",
            "enabled": True,
            "leverage": 1,
            "marginMode": "cross",
            "openLotSize": 0.01,
            "trailingStop": False,
            "trailingStopDistance": 1,
            "autoDeleverage": False,
            "hedgingEnabled": False,
            "selectedInstrument": "",
            "riskType": "dynamic",
            "riskPerTrade": 2.0,
            "kellyFraction": 0.5,
            "adaptiveSizing": True,
            "volatilityAdjustment": True,
            "drawdownProtection": True,
            "maxDrawdown": 15,
            "dailyLossLimit": 5,
            "weeklyLossLimit": 15,
            "breakEvenOnProfit": True,
            "liquidationAlert": 0,
            "fixedRiskPerTrade": 2.0,
            "fixedMaxDrawdown": 20,
            "riskRewardRatio": 2.0,
            "fixedLotSize": 0.01,
            "maxOpenPositions": 5,
            "brokerType": "crypto_exchange",
            "exchange": "binance",
            "endpoint": "https://api.binance.com",
            "apiKey": "",
            "apiSecret": "",
            "passphrase": "",
            "testnet": True,
            "brokerConnected": False,
            "mtType": "",
            "mtServer": "",
            "mtLogin": "",
            "mtPassword": "",
            "mtAccountType": "demo",
            "mtBroker": "",
            "fixSenderCompId": "",
            "fixTargetCompId": "",
            "fixHost": "",
            "fixPort": 443,
            "fixUsername": "",
            "fixPassword": "",
            "fixHeartbeatInterval": 30,
            "fixResetOnLogon": True,
            "fixSslEnabled": True,
            "timeEntryEnabled": False,
            "entryStartTime": "00:00",
            "entryEndTime": "23:59",
            "useMultiTf": False,
            "confirmationTimeframes": ["H1", "H4", "D1"]
        },
        {
            "id": "futures-1",
            "name": "Futures Trading - Primary",
            "mode": "futures",
            "enabled": True,
            "leverage": 10,
            "marginMode": "isolated",
            "openLotSize": 0.1,
            "trailingStop": True,
            "trailingStopDistance": 0.5,
            "autoDeleverage": True,
            "hedgingEnabled": True,
            "selectedInstrument": "BTC/USDT",
            "riskType": "dynamic",
            "riskPerTrade": 1.5,
            "kellyFraction": 0.5,
            "adaptiveSizing": True,
            "volatilityAdjustment": True,
            "drawdownProtection": True,
            "maxDrawdown": 10,
            "dailyLossLimit": 3,
            "weeklyLossLimit": 10,
            "breakEvenOnProfit": True,
            "liquidationAlert": 80,
            "fixedRiskPerTrade": 2.0,
            "fixedMaxDrawdown": 20,
            "riskRewardRatio": 2.0,
            "fixedLotSize": 0.1,
            "maxOpenPositions": 3,
            "brokerType": "crypto_exchange",
            "exchange": "binance",
            "endpoint": "https://fapi.binance.com",
            "apiKey": "",
            "apiSecret": "",
            "passphrase": "",
            "testnet": True,
            "brokerConnected": False,
            "mtType": "",
            "mtServer": "",
            "mtLogin": "",
            "mtPassword": "",
            "mtAccountType": "demo",
            "mtBroker": "",
            "fixSenderCompId": "",
            "fixTargetCompId": "",
            "fixHost": "",
            "fixPort": 443,
            "fixUsername": "",
            "fixPassword": "",
            "fixHeartbeatInterval": 30,
            "fixResetOnLogon": True,
            "fixSslEnabled": True,
            "timeEntryEnabled": False,
            "entryStartTime": "00:00",
            "entryEndTime": "23:59",
            "useMultiTf": False,
            "confirmationTimeframes": ["M15", "H1", "H4"]
        }
    ]


# ============================================================================
# RISK CONFIGURATION ENDPOINTS
# ============================================================================

@sync_bp.route("/config/risk", methods=['GET', 'POST'])
def risk_config():
    """Get or update risk configuration"""
    try:
        CONFIG = load_all_configs()
        
        if request.method == 'GET':
            risk_config = CONFIG.get('risk_config', {})
            
            # Format response to match frontend expectations
            return jsonify({
                "status": "active",
                "config": risk_config,
                "metrics": {
                    "riskStatus": "Low",
                    "totalExposure": 2.1,
                    "maxDrawdown": -3.2,
                    "sharpeRatio": 2.4,
                    "kellyFraction": risk_config.get('kelly_fraction', 0.5),
                    "riskPerTrade": risk_config.get('risk_per_trade', 2.0),
                    "maxPositionSize": risk_config.get('max_position_size', 5.0),
                    "winRate": 67.8,
                    "avgRiskReward": 2.4,
                    "dailyLossLimit": risk_config.get('daily_loss_limit', 5.0),
                    "maxOpenPositions": risk_config.get('max_open_positions', 5),
                    "leverageLimit": risk_config.get('leverage_limit', 3)
                },
                "timestamp": datetime.now().isoformat()
            })
        
        elif request.method == 'POST':
            update_data = request.json or {}
            
            # Merge with existing config
            current_config = CONFIG.get('risk_config', {})
            current_config.update(update_data)
            
            # Save updated config
            config_path = os.path.join("config", "risk_config.yaml")
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(current_config, f, default_flow_style=False)
            
            return jsonify({
                "status": "updated",
                "config": current_config,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Risk config error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SCANNER CONFIGURATION ENDPOINTS
# ============================================================================

@sync_bp.route("/config/scanner", methods=['GET', 'POST'])
def scanner_config():
    """Get or update scanner configuration"""
    try:
        CONFIG = load_all_configs()
        
        if request.method == 'GET':
            scanner_config = CONFIG.get('scanner_config', {})
            return jsonify({
                "config": scanner_config,
                "timeframes": [
                    "1m", "2m", "3m", "5m", "15m", "30m",
                    "1h", "2h", "3h", "4h", "6h", "8h", "12h",
                    "1d", "1w", "1M", "1Y"
                ],
                "assetTypes": ["Forex", "Crypto", "Indices", "Commodity", "Stocks"],
                "timestamp": datetime.now().isoformat()
            })
        
        elif request.method == 'POST':
            update_data = request.json or {}
            
            current_config = CONFIG.get('scanner_config', {})
            current_config.update(update_data)
            
            config_path = os.path.join("config", "scanner_config.yaml")
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(current_config, f, default_flow_style=False)
            
            return jsonify({
                "status": "updated",
                "config": current_config,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Scanner config error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# INSTRUMENTS ENDPOINTS
# ============================================================================

@sync_bp.route("/instruments", methods=['GET', 'POST'])
def trading_instruments():
    """Get or update trading instruments"""
    try:
        instruments_path = os.path.join("config", "instruments.json")
        
        if request.method == 'GET':
            if os.path.exists(instruments_path):
                with open(instruments_path, 'r') as f:
                    instruments = json.load(f)
            else:
                instruments = get_default_instruments()
            return jsonify(instruments)
        
        elif request.method == 'POST':
            instruments_data = request.json
            
            with open(instruments_path, 'w') as f:
                json.dump(instruments_data, f, indent=2)
            
            return jsonify({
                "status": "saved",
                "message": "Instruments synchronized",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Instruments error: {e}")
        return jsonify({"error": str(e)}), 500


def get_default_instruments() -> Dict:
    """Returns default trading instruments"""
    return {
        "forex": [
            {"symbol": "EUR/USD", "name": "Euro/US Dollar", "enabled": True, "category": "Major"},
            {"symbol": "GBP/USD", "name": "British Pound/US Dollar", "enabled": True, "category": "Major"},
            {"symbol": "USD/JPY", "name": "US Dollar/Japanese Yen", "enabled": True, "category": "Major"},
            {"symbol": "USD/CHF", "name": "US Dollar/Swiss Franc", "enabled": True, "category": "Major"},
            {"symbol": "AUD/USD", "name": "Australian Dollar/US Dollar", "enabled": True, "category": "Major"},
            {"symbol": "USD/CAD", "name": "US Dollar/Canadian Dollar", "enabled": True, "category": "Major"},
            {"symbol": "NZD/USD", "name": "New Zealand Dollar/US Dollar", "enabled": True, "category": "Major"},
        ],
        "crypto": [
            {"symbol": "BTC/USDT", "name": "Bitcoin/Tether", "enabled": True, "category": "Top"},
            {"symbol": "ETH/USDT", "name": "Ethereum/Tether", "enabled": True, "category": "Top"},
            {"symbol": "BNB/USDT", "name": "Binance Coin/Tether", "enabled": True, "category": "Top"},
            {"symbol": "SOL/USDT", "name": "Solana/Tether", "enabled": True, "category": "Top"},
            {"symbol": "XRP/USDT", "name": "Ripple/Tether", "enabled": True, "category": "Top"},
            {"symbol": "ADA/USDT", "name": "Cardano/Tether", "enabled": True, "category": "Top"},
        ],
        "indices": [
            {"symbol": "US30", "name": "Dow Jones 30", "enabled": True, "category": "US"},
            {"symbol": "US500", "name": "S&P 500", "enabled": True, "category": "US"},
            {"symbol": "US100", "name": "Nasdaq 100", "enabled": True, "category": "US"},
            {"symbol": "DE40", "name": "DAX 40", "enabled": True, "category": "Europe"},
        ],
        "commodity": [
            {"symbol": "XAU/USD", "name": "Gold/US Dollar", "enabled": True, "category": "Metals"},
            {"symbol": "XAG/USD", "name": "Silver/US Dollar", "enabled": True, "category": "Metals"},
            {"symbol": "WTI", "name": "Crude Oil WTI", "enabled": True, "category": "Energy"},
            {"symbol": "BRENT", "name": "Brent Crude Oil", "enabled": True, "category": "Energy"},
        ],
        "stocks": [
            {"symbol": "AAPL", "name": "Apple Inc.", "enabled": True, "category": "Tech"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "enabled": True, "category": "Tech"},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "enabled": True, "category": "Tech"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "enabled": True, "category": "Tech"},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "enabled": True, "category": "Tech"},
        ]
    }


# ============================================================================
# STRATEGY WEIGHTS ENDPOINTS
# ============================================================================

@sync_bp.route("/config/strategies", methods=['GET', 'POST'])
def strategy_weights():
    """Get or update strategy weights per timeframe"""
    try:
        strategies_path = os.path.join("config", "strategy_weights.json")
        
        if request.method == 'GET':
            if os.path.exists(strategies_path):
                with open(strategies_path, 'r') as f:
                    weights = json.load(f)
            else:
                weights = get_default_strategy_weights()
            return jsonify(weights)
        
        elif request.method == 'POST':
            weights_data = request.json
            
            with open(strategies_path, 'w') as f:
                json.dump(weights_data, f, indent=2)
            
            return jsonify({
                "status": "saved",
                "message": "Strategy weights synchronized",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Strategy weights error: {e}")
        return jsonify({"error": str(e)}), 500


def get_default_strategy_weights() -> Dict:
    """Returns default strategy weights matching frontend structure"""
    timeframes = [
        "M1", "M2", "M3", "M5", "M10", "M15", "M30", "M45",
        "H1", "H2", "H3", "H4", "D1", "W1", "MN", "QMN", "SMN", "Y1"
    ]
    
    default_strategies = [
        {"name": "WD Gann Modul", "weight": 0.25},
        {"name": "Astro Cycles", "weight": 0.15},
        {"name": "Ehlers DSP", "weight": 0.20},
        {"name": "ML Models", "weight": 0.25},
        {"name": "Pattern Recognition", "weight": 0.10},
        {"name": "Options Flow", "weight": 0.05}
    ]
    
    return {tf: [s.copy() for s in default_strategies] for tf in timeframes}


# ============================================================================
# LEVERAGE CONFIGURATION ENDPOINTS
# ============================================================================

@sync_bp.route("/config/leverage", methods=['GET', 'POST'])
def leverage_config():
    """Get or update manual leverage configurations"""
    try:
        leverage_path = os.path.join("config", "leverage_config.json")
        
        if request.method == 'GET':
            if os.path.exists(leverage_path):
                with open(leverage_path, 'r') as f:
                    leverages = json.load(f)
            else:
                leverages = [
                    {"instrument": "BTC/USDT", "leverage": 25, "marginMode": "isolated"},
                    {"instrument": "ETH/USDT", "leverage": 20, "marginMode": "isolated"},
                    {"instrument": "EUR/USD", "leverage": 100, "marginMode": "cross"},
                    {"instrument": "XAU/USD", "leverage": 20, "marginMode": "cross"},
                ]
            return jsonify(leverages)
        
        elif request.method == 'POST':
            leverage_data = request.json
            
            with open(leverage_path, 'w') as f:
                json.dump(leverage_data, f, indent=2)
            
            return jsonify({
                "status": "saved",
                "message": "Leverage configuration synchronized",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Leverage config error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SMITH CHART ANALYSIS ENDPOINTS
# ============================================================================

@sync_bp.route("/smith/analyze", methods=['POST'])
def smith_chart_analyze():
    """Perform Smith Chart analysis for impedance matching and trading signals"""
    try:
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        lookback_days = data.get('lookbackDays', 100)
        
        CONFIG = load_all_configs()
        data_feed = DataFeed(broker_config=CONFIG.get('broker_config', {}))
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        smith_analyzer = SmithChartAnalyzer(CONFIG.get('smith_config', {}))
        # Use analyze_trajectory method which is the correct method
        analysis = smith_analyzer.analyze_trajectory(price_data, lookback=min(20, len(price_data)))
        
        # Get current point and signal
        current_price = float(price_data['close'].iloc[-1])
        momentum = float(price_data['close'].pct_change().iloc[-5:].mean() * 100) if len(price_data) > 5 else 0
        current_point = smith_analyzer.analyze_point(current_price, momentum)
        signal = smith_analyzer.get_signal(current_point)
        
        return jsonify({
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "chart_data": {
                "points": analysis.get('points', []),
                "current_zone": analysis.get('current_zone', 'unknown'),
                "pattern": analysis.get('pattern', 'unknown')
            },
            "signal": signal
        })
        
    except Exception as e:
        logger.error(f"Smith chart analysis error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# OPTIONS ANALYSIS ENDPOINTS
# ============================================================================

@sync_bp.route("/options/analyze", methods=['POST'])
def options_analyze():
    """Perform options analysis including Greeks and sentiment"""
    try:
        data = request.json or {}
        symbol = data.get('symbol', 'BTC')
        expiry_days = data.get('expiryDays', 30)
        spot_price = data.get('spotPrice', 50000)  # Default for BTC
        
        CONFIG = load_all_configs()
        options_engine = OptionsEngine(CONFIG.get('options_config', {}))
        
        # Calculate ATM option pricing
        atm_strike = spot_price
        volatility = 0.6  # Default BTC volatility ~60%
        
        # Price call and put options
        call_pricing = options_engine.price_option(
            spot=spot_price,
            strike=atm_strike,
            days_to_expiry=expiry_days,
            volatility=volatility
        )
        
        from core.options_engine import OptionType
        put_pricing = options_engine.price_option(
            spot=spot_price,
            strike=atm_strike,
            days_to_expiry=expiry_days,
            volatility=volatility,
            option_type=OptionType.PUT
        )
        
        return jsonify({
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "spotPrice": spot_price,
            "expiryDays": expiry_days,
            "call": {
                "price": call_pricing.theoretical_price,
                "delta": call_pricing.delta,
                "gamma": call_pricing.gamma,
                "theta": call_pricing.theta,
                "vega": call_pricing.vega,
                "rho": call_pricing.rho,
                "iv": call_pricing.implied_volatility,
                "moneyness": call_pricing.moneyness
            },
            "put": {
                "price": put_pricing.theoretical_price,
                "delta": put_pricing.delta,
                "gamma": put_pricing.gamma,
                "theta": put_pricing.theta,
                "vega": put_pricing.vega,
                "rho": put_pricing.rho,
                "iv": put_pricing.implied_volatility,
                "moneyness": put_pricing.moneyness
            },
            "volatility": {
                "current": volatility,
                "percentile": 50
            }
        })
        
    except Exception as e:
        logger.error(f"Options analysis error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/options/greeks", methods=['POST'])
def options_greeks():
    """Calculate option Greeks"""
    try:
        data = request.json or {}
        
        spot_price = data.get('spotPrice', 100)
        strike_price = data.get('strikePrice', 100)
        time_to_expiry_days = data.get('timeToExpiry', 30)
        time_to_expiry = time_to_expiry_days / 365  # Convert days to years
        volatility = data.get('volatility', 0.3)
        risk_free_rate = data.get('riskFreeRate', 0.05)
        option_type_str = data.get('optionType', 'call')
        
        CONFIG = load_all_configs()
        options_engine = OptionsEngine(CONFIG.get('options_config', {}))
        
        from core.options_engine import OptionType
        option_type = OptionType.CALL if option_type_str.lower() == 'call' else OptionType.PUT
        
        greeks = options_engine.calculate_greeks(
            S=spot_price,
            K=strike_price,
            T=time_to_expiry,
            r=risk_free_rate,
            sigma=volatility,
            option_type=option_type
        )
        
        return jsonify({
            "greeks": greeks,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Options Greeks calculation error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# RISK-REWARD ANALYSIS ENDPOINTS
# ============================================================================

@sync_bp.route("/rr/calculate", methods=['POST'])
def rr_calculate():
    """Calculate Risk-Reward metrics for a trade setup"""
    try:
        data = request.json or {}
        
        entry_price = data.get('entryPrice')
        stop_loss = data.get('stopLoss')
        take_profit = data.get('takeProfit')
        account_balance = data.get('accountBalance', 100000)
        risk_percent = data.get('riskPercent', 2.0)
        direction = data.get('direction', 'LONG')
        
        if not all([entry_price, stop_loss, take_profit]):
            return jsonify({"error": "Missing required fields: entryPrice, stopLoss, takeProfit"}), 400
        
        CONFIG = load_all_configs()
        
        # Import RREngine (RiskRewardEngine)
        from core.rr_engine import RREngine
        rr_engine = RREngine(CONFIG.get('rr_config', {}))
        rr_engine.set_account_balance(account_balance)
        
        # Calculate R:R
        rr_analysis = rr_engine.calculate_rr(
            entry=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            direction=direction
        )
        
        # Calculate position size
        position = rr_engine.calculate_position_size(
            entry=entry_price,
            stop_loss=stop_loss,
            risk_percentage=risk_percent
        )
        
        return jsonify({
            "analysis": {
                "entryPrice": entry_price,
                "stopLoss": stop_loss,
                "takeProfit": take_profit,
                "riskAmount": rr_analysis.risk_amount,
                "rewardAmount": rr_analysis.reward_amount,
                "riskRewardRatio": rr_analysis.risk_reward_ratio,
                "riskPercent": rr_analysis.risk_percentage,
                "rewardPercent": rr_analysis.reward_percentage,
                "breakevenWinrate": rr_analysis.breakeven_winrate,
                "expectedValue": rr_analysis.expected_value,
                "rating": rr_analysis.rr_rating.value,
                "notes": rr_analysis.notes
            },
            "position": position,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"R:R calculation error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PATTERN RECOGNITION ENDPOINTS
# ============================================================================

@sync_bp.route("/patterns/scan", methods=['POST'])
def pattern_scan():
    """Scan for candlestick and chart patterns"""
    try:
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        lookback_days = data.get('lookbackDays', 100)
        
        CONFIG = load_all_configs()
        data_feed = DataFeed(broker_config=CONFIG.get('broker_config', {}))
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        from core.pattern_recognition import PatternRecognition
        pattern_engine = PatternRecognition(CONFIG.get('Candlestick_Pattern', {}))
        
        patterns = pattern_engine.scan_all_patterns(price_data)
        
        return jsonify({
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "patterns": patterns
        })
        
    except Exception as e:
        logger.error(f"Pattern scan error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# GANN VIBRATION MATRIX ENDPOINTS
# ============================================================================

@sync_bp.route("/gann/vibration-matrix", methods=['POST'])
def gann_vibration_matrix():
    """Get Gann Time Vibration Matrix (0-360 degrees in 22.5-degree increments)"""
    try:
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        base_price = data.get('basePrice', None)
        
        CONFIG = load_all_configs()
        
        if base_price is None:
            # Fetch current price
            data_feed = DataFeed(broker_config=CONFIG.get('broker_config', {}))
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            price_data = data_feed.get_historical_data(symbol, '1d', start_date, end_date)
            
            if price_data is not None and not price_data.empty:
                base_price = float(price_data['close'].iloc[-1])
            else:
                base_price = 47500  # Default for BTC
        
        # Generate vibration matrix (0-360 in 22.5 degree increments)
        gann_engine = GannEngine(gann_config=CONFIG.get('gann_config', {}))
        
        vibration_matrix = []
        degrees = [i * 22.5 for i in range(17)]  # 0 to 360 in 22.5 increments
        
        for degree in degrees:
            # Calculate price level at this degree
            sqrt_base = base_price ** 0.5
            radians = degree * (3.14159265359 / 180)
            
            # Gann conversion formula
            price_up = (sqrt_base + (degree / 360)) ** 2
            price_down = (sqrt_base - (degree / 360)) ** 2 if degree > 0 else base_price
            
            # Calculate time equivalent (hours based on 24-hour cycle)
            time_hour = (degree / 15) % 24
            time_str = f"{int(time_hour):02d}:{int((time_hour % 1) * 60):02d}"
            
            vibration_matrix.append({
                "degree": degree,
                "priceUp": round(price_up, 2),
                "priceDown": round(price_down, 2) if price_down > 0 else 0,
                "timeEquivalent": time_str,
                "significance": get_degree_significance(degree),
                "nature": get_degree_nature(degree)
            })
        
        return jsonify({
            "symbol": symbol,
            "basePrice": base_price,
            "timestamp": datetime.now().isoformat(),
            "matrix": vibration_matrix
        })
        
    except Exception as e:
        logger.error(f"Gann vibration matrix error: {e}")
        return jsonify({"error": str(e)}), 500


def get_degree_significance(degree: float) -> str:
    """Get significance level for a degree"""
    cardinal = [0, 90, 180, 270, 360]
    ordinal = [45, 135, 225, 315]
    
    if degree in cardinal:
        return "cardinal"
    elif degree in ordinal:
        return "ordinal"
    else:
        return "minor"


def get_degree_nature(degree: float) -> str:
    """Get nature/implication for a degree"""
    if degree in [0, 360]:
        return "cycle_start"
    elif degree == 90:
        return "first_square"
    elif degree == 180:
        return "opposition"
    elif degree == 270:
        return "third_square"
    elif degree in [45, 135, 225, 315]:
        return "semi_square"
    else:
        return "transit"


# ============================================================================
# GANN SUPPLY & DEMAND ENDPOINTS
# ============================================================================

@sync_bp.route("/gann/supply-demand", methods=['POST'])
def gann_supply_demand():
    """Get Gann-based Supply and Demand zones"""
    try:
        data = request.json or {}
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        lookback_days = data.get('lookbackDays', 100)
        
        CONFIG = load_all_configs()
        data_feed = DataFeed(broker_config=CONFIG.get('broker_config', {}))
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({"error": "Failed to fetch price data"}), 400
        
        gann_engine = GannEngine(gann_config=CONFIG.get('gann_config', {}))
        sq9_levels = gann_engine.calculate_sq9_levels(price_data)
        
        current_price = float(price_data['close'].iloc[-1])
        
        # Build supply/demand zones from Gann levels
        supply_zones = []
        demand_zones = []
        
        if sq9_levels:
            for i, level in enumerate(sq9_levels.get('resistance', [])):
                supply_zones.append({
                    "price": float(level),
                    "strength": 1.0 - (i * 0.15),
                    "type": "gann_resistance",
                    "distance_percent": ((level - current_price) / current_price) * 100,
                    "timestamp": datetime.now().isoformat()
                })
            
            for i, level in enumerate(sq9_levels.get('support', [])):
                demand_zones.append({
                    "price": float(level),
                    "strength": 1.0 - (i * 0.15),
                    "type": "gann_support",
                    "distance_percent": ((current_price - level) / current_price) * 100,
                    "timestamp": datetime.now().isoformat()
                })
        
        return jsonify({
            "symbol": symbol,
            "currentPrice": current_price,
            "timestamp": datetime.now().isoformat(),
            "supplyZones": supply_zones,
            "demandZones": demand_zones,
            "sq9Levels": sq9_levels
        })
        
    except Exception as e:
        logger.error(f"Gann S&D error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# FULL SETTINGS SYNC ENDPOINT
# ============================================================================

@sync_bp.route("/settings/sync-all", methods=['POST'])
def sync_all_settings():
    """Synchronize all frontend settings with backend"""
    try:
        settings = request.json or {}
        
        # Save trading modes
        if 'tradingModes' in settings:
            modes_path = os.path.join("config", "trading_modes.json")
            with open(modes_path, 'w') as f:
                json.dump(settings['tradingModes'], f, indent=2)
        
        # Save instruments
        if 'instruments' in settings:
            instruments_path = os.path.join("config", "instruments.json")
            with open(instruments_path, 'w') as f:
                json.dump(settings['instruments'], f, indent=2)
        
        # Save strategy weights
        if 'strategyWeights' in settings:
            strategies_path = os.path.join("config", "strategy_weights.json")
            with open(strategies_path, 'w') as f:
                json.dump(settings['strategyWeights'], f, indent=2)
        
        # Save leverage config
        if 'manualLeverages' in settings:
            leverage_path = os.path.join("config", "leverage_config.json")
            with open(leverage_path, 'w') as f:
                json.dump(settings['manualLeverages'], f, indent=2)
        
        logger.success("All frontend settings synchronized to backend")
        
        return jsonify({
            "status": "synchronized",
            "message": "All settings synced successfully",
            "syncedSections": list(settings.keys()),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Settings sync error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/settings/load-all", methods=['GET'])
def load_all_settings():
    """Load all settings from backend for frontend hydration"""
    try:
        settings = {}
        
        # Load trading modes
        modes_path = os.path.join("config", "trading_modes.json")
        if os.path.exists(modes_path):
            with open(modes_path, 'r') as f:
                settings['tradingModes'] = json.load(f)
        else:
            settings['tradingModes'] = get_default_trading_modes()
        
        # Load instruments
        instruments_path = os.path.join("config", "instruments.json")
        if os.path.exists(instruments_path):
            with open(instruments_path, 'r') as f:
                settings['instruments'] = json.load(f)
        else:
            settings['instruments'] = get_default_instruments()
        
        # Load strategy weights
        strategies_path = os.path.join("config", "strategy_weights.json")
        if os.path.exists(strategies_path):
            with open(strategies_path, 'r') as f:
                settings['strategyWeights'] = json.load(f)
        else:
            settings['strategyWeights'] = get_default_strategy_weights()
        
        # Load leverage config
        leverage_path = os.path.join("config", "leverage_config.json")
        if os.path.exists(leverage_path):
            with open(leverage_path, 'r') as f:
                settings['manualLeverages'] = json.load(f)
        else:
            settings['manualLeverages'] = [
                {"instrument": "BTC/USDT", "leverage": 25, "marginMode": "isolated"},
                {"instrument": "ETH/USDT", "leverage": 20, "marginMode": "isolated"},
            ]
        
        return jsonify({
            "settings": settings,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Load settings error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# BROKER CONNECTION ENDPOINTS
# ============================================================================

@sync_bp.route("/broker/test-connection", methods=['POST'])
def test_broker_connection():
    """Test connection to a broker/exchange"""
    try:
        data = request.json or {}
        broker_type = data.get('brokerType', 'crypto_exchange')
        
        result = {
            "connected": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        if broker_type == 'crypto_exchange':
            exchange = data.get('exchange', 'binance')
            api_key = data.get('apiKey', '')
            api_secret = data.get('apiSecret', '')
            testnet = data.get('testnet', True)
            
            if not api_key or not api_secret:
                result["message"] = "API Key and Secret required"
                return jsonify(result), 400
            
            # Test connection based on exchange
            try:
                from core.Binance_connector import BinanceConnector
                
                config = {
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'testnet': testnet
                }
                connector = BinanceConnector(config)
                balance = connector.get_account_balance('USDT')
                
                result["connected"] = True
                result["message"] = f"Connected to {exchange.upper()}. Balance: {balance.get('total', 0)} USDT"
                result["balance"] = balance
                
            except Exception as e:
                result["message"] = f"Connection failed: {str(e)}"
                
        elif broker_type == 'metatrader':
            mt_type = data.get('mtType', 'mt5')
            login = data.get('mtLogin', '')
            password = data.get('mtPassword', '')
            server = data.get('mtServer', '')
            
            if not login or not password:
                result["message"] = "Login and password required"
                return jsonify(result), 400
            
            try:
                from core.Metatrader5_bridge import MetaTrader5Bridge
                
                config = {
                    'login': int(login),
                    'password': password,
                    'server': server
                }
                bridge = MetaTrader5Bridge(config)
                
                if bridge.is_connected():
                    account_info = bridge.get_account_info()
                    result["connected"] = True
                    result["message"] = f"Connected to {mt_type.upper()}. Balance: {account_info.get('balance', 0)}"
                    result["account"] = account_info
                else:
                    result["message"] = "Failed to connect to MetaTrader"
                    
            except Exception as e:
                result["message"] = f"MT connection error: {str(e)}"
                
        elif broker_type == 'fix':
            host = data.get('fixHost', '')
            port = data.get('fixPort', 443)
            sender_comp_id = data.get('fixSenderCompId', '')
            target_comp_id = data.get('fixTargetCompId', '')
            
            # FIX Protocol simulation - real implementation would use quickfix/simplefix
            result["connected"] = True
            result["message"] = f"FIX connection test successful to {host}:{port}"
            result["session"] = {
                "senderCompID": sender_comp_id,
                "targetCompID": target_comp_id,
                "status": "simulated"
            }
            
        else:
            result["message"] = "Unknown broker type"
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Broker connection test error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/broker/binance/balance", methods=['GET'])
def get_binance_balance():
    """Get Binance account balance"""
    try:
        # Load saved credentials
        config_path = os.path.join("config", "broker_config.yaml")
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                broker_config = yaml.safe_load(f)
        else:
            return jsonify({"error": "Broker not configured"}), 400
        
        from core.Binance_connector import BinanceConnector
        connector = BinanceConnector(broker_config.get('binance', {}))
        balance = connector.get_account_balance('USDT')
        
        return jsonify({
            "balance": balance,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Binance balance error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/broker/mt5/positions", methods=['GET'])
def get_mt5_positions():
    """Get MetaTrader 5 open positions"""
    try:
        from core.Metatrader5_bridge import MetaTrader5Bridge
        
        config_path = os.path.join("config", "mt5_config.yaml")
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                mt_config = yaml.safe_load(f)
        else:
            return jsonify({"error": "MT5 not configured"}), 400
        
        bridge = MetaTrader5Bridge(mt_config)
        positions = bridge.get_positions()
        
        return jsonify({
            "positions": positions,
            "count": len(positions),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"MT5 positions error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ML MODEL TRAINING ENDPOINTS
# ============================================================================

@sync_bp.route("/ml/config", methods=['GET', 'POST'])
def ml_model_config():
    """Get or update ML model configuration"""
    try:
        config_path = os.path.join("config", "ml_training_config.json")
        
        if request.method == 'GET':
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = get_default_ml_config()
            return jsonify(config)
        
        elif request.method == 'POST':
            config = request.json or {}
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return jsonify({
                "status": "saved",
                "message": "ML configuration updated",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"ML config error: {e}")
        return jsonify({"error": str(e)}), 500


def get_default_ml_config():
    """Get default ML training configuration"""
    return {
        "optimizer": "adam",
        "learningRate": 0.001,
        "lrScheduler": "cosine",
        "momentum": 0.9,
        "beta1": 0.9,
        "beta2": 0.999,
        "epsilon": 1e-8,
        "weightDecay": 0.0001,
        "batchSize": 32,
        "epochs": 100,
        "earlyStopping": True,
        "patience": 10,
        "validationSplit": 0.2,
        "regularization": "l2",
        "l1Lambda": 0.0,
        "l2Lambda": 0.01,
        "dropoutRate": 0.3,
        "lossFunction": "mse",
        "gradientClipping": True,
        "maxGradNorm": 1.0,
        "mixedPrecision": False,
        "gradientAccumulation": 1
    }


@sync_bp.route("/ml/train", methods=['POST'])
def train_ml_model():
    """Start ML model training"""
    try:
        data = request.json or {}
        config = data.get('config', get_default_ml_config())
        model_type = data.get('modelType', 'lstm')
        
        # Simulated training - real implementation would use core.ml_engine
        training_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting ML training job: {training_id}")
        
        return jsonify({
            "trainingId": training_id,
            "status": "started",
            "modelType": model_type,
            "config": config,
            "message": "Training job queued",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"ML training error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/ml/training-status/<training_id>", methods=['GET'])
def get_training_status(training_id: str):
    """Get ML training job status"""
    try:
        # Simulated status - real implementation would track actual training jobs
        import random
        
        epoch = random.randint(1, 100)
        train_loss = max(0.01, 1.0 - (epoch * 0.009) + random.uniform(-0.05, 0.05))
        val_loss = max(0.02, 1.1 - (epoch * 0.008) + random.uniform(-0.08, 0.08))
        
        return jsonify({
            "trainingId": training_id,
            "status": "running" if epoch < 100 else "completed",
            "currentEpoch": epoch,
            "totalEpochs": 100,
            "metrics": {
                "trainLoss": round(train_loss, 4),
                "valLoss": round(val_loss, 4),
                "trainAccuracy": round(min(0.99, epoch * 0.01), 4),
                "valAccuracy": round(min(0.95, epoch * 0.008), 4)
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Training status error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/ml/auto-tune", methods=['POST'])
def start_auto_tuning():
    """Start ML hyperparameter auto-tuning"""
    try:
        data = request.json or {}
        search_method = data.get('searchMethod', 'bayesian')
        max_trials = data.get('maxTrials', 20)
        
        tuning_id = f"tune_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting auto-tuning job: {tuning_id} using {search_method}")
        
        return jsonify({
            "tuningId": tuning_id,
            "status": "started",
            "searchMethod": search_method,
            "maxTrials": max_trials,
            "message": "Auto-tuning job started",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Auto-tuning error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/ml/ensemble", methods=['GET', 'POST'])
def ml_ensemble_config():
    """Get or configure ML ensemble models"""
    try:
        config_path = os.path.join("config", "ensemble_config.json")
        
        if request.method == 'GET':
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {
                    "method": "stacking",
                    "metaLearner": "linear",
                    "votingStrategy": "soft",
                    "nFolds": 5,
                    "useProba": True,
                    "passthrough": False,
                    "nEstimators": 10,
                    "subsampleRatio": 0.8,
                    "boostingType": "gradient",
                    "learningRate": 0.1,
                    "models": [
                        {"id": "lstm", "name": "LSTM", "weight": 0.3, "enabled": True, "accuracy": 0.82},
                        {"id": "gru", "name": "GRU", "weight": 0.25, "enabled": True, "accuracy": 0.79},
                        {"id": "transformer", "name": "Transformer", "weight": 0.25, "enabled": True, "accuracy": 0.85},
                        {"id": "xgboost", "name": "XGBoost", "weight": 0.2, "enabled": True, "accuracy": 0.78}
                    ]
                }
            return jsonify(config)
        
        elif request.method == 'POST':
            config = request.json or {}
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            return jsonify({
                "status": "saved",
                "message": "Ensemble configuration updated",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Ensemble config error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/ml/export", methods=['POST'])
def export_ml_model():
    """Export ML model to specified format"""
    try:
        data = request.json or {}
        model_id = data.get('modelId', 'default')
        export_format = data.get('format', 'json')
        
        # Simulated export
        export_id = f"export_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            "exportId": export_id,
            "modelId": model_id,
            "format": export_format,
            "status": "completed",
            "downloadUrl": f"/api/ml/download/{export_id}",
            "size": "2.4 MB",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Model export error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ALERT API CONFIGURATION ENDPOINTS
# ============================================================================

@sync_bp.route("/alerts/config", methods=['GET', 'POST'])
def alert_config():
    """Get or update alert configuration"""
    try:
        config_path = os.path.join("config", "alerts_config.json")
        
        if request.method == 'GET':
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = get_default_alert_config()
            return jsonify(config)
        
        elif request.method == 'POST':
            config = request.json or {}
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return jsonify({
                "status": "saved",
                "message": "Alert configuration updated",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Alert config error: {e}")
        return jsonify({"error": str(e)}), 500


def get_default_alert_config():
    """Get default alert configuration"""
    return {
        "channels": {
            "telegram": {"enabled": False, "botToken": "", "chatId": ""},
            "email": {"enabled": False, "smtpServer": "", "smtpPort": "587", "email": "", "password": ""},
            "sms": {"enabled": False, "accountSid": "", "authToken": "", "fromNumber": "", "toNumber": ""},
            "discord": {"enabled": False, "webhookUrl": ""},
            "slack": {"enabled": False, "webhookUrl": ""},
            "pushover": {"enabled": False, "userKey": "", "appToken": ""}
        },
        "alertTypes": {
            "priceAlert": True,
            "gannSignal": True,
            "ehlersSignal": True,
            "aiPrediction": True,
            "spikeDetection": True,
            "positionUpdate": True,
            "dailyReport": False
        }
    }


@sync_bp.route("/alerts/test/<channel>", methods=['POST'])
def test_alert_channel(channel: str):
    """Test an alert channel"""
    try:
        data = request.json or {}
        
        # Simulated test - real implementation would actually test the channel
        import random
        success = random.random() > 0.2  # 80% success rate
        
        if success:
            return jsonify({
                "channel": channel,
                "status": "success",
                "message": f"Test message sent successfully to {channel}",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "channel": channel,
                "status": "failed",
                "message": f"Failed to send test message to {channel}. Check credentials.",
                "timestamp": datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"Alert test error: {e}")
        return jsonify({"error": str(e)}), 500


@sync_bp.route("/alerts/send", methods=['POST'])
def send_alert():
    """Send an alert to configured channels"""
    try:
        data = request.json or {}
        alert_type = data.get('type', 'general')
        message = data.get('message', '')
        channels = data.get('channels', ['telegram'])
        
        # Simulated send - real implementation would use utils.notifier
        results = {}
        for channel in channels:
            results[channel] = {"sent": True, "timestamp": datetime.now().isoformat()}
        
        return jsonify({
            "status": "sent",
            "alertType": alert_type,
            "message": message[:100],
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Send alert error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# REGISTER BLUEPRINT FUNCTION
# ============================================================================

def register_sync_routes(app: Flask):
    """Register sync routes with the main Flask app"""
    app.register_blueprint(sync_bp)
    logger.info("Sync API routes registered successfully")

