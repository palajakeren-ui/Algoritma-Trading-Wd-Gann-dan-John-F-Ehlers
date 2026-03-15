"""
Bookmap & Open Terminal API Endpoints
Provides backend data for:
- Bookmap: Order book depth, DOM, heatmap snapshots, time & sales
- Open Terminal: Command execution, watchlist, fundamental data, news feed
Driven by config/terminal_config.yaml and config/bookmap_config.yaml
"""
from flask import Blueprint, request, jsonify
from loguru import logger
from datetime import datetime, timedelta
import random
import math
import json
import os
import yaml

# Yahoo Finance data feed
try:
    from core.yahoo_finance_feed import get_yahoo_fundamental, get_yahoo_quote, get_yahoo_status, clear_cache as yahoo_clear_cache
    _HAS_YAHOO_FEED = True
except ImportError:
    _HAS_YAHOO_FEED = False
    logger.warning("yahoo_finance_feed module not available")

# News & Market Alert Service
try:
    from core import news_alert_service as _alert_svc
    _HAS_ALERT_SVC = True
except ImportError:
    _HAS_ALERT_SVC = False
    logger.warning("news_alert_service module not available")

bookmap_terminal_api = Blueprint('bookmap_terminal_api', __name__, url_prefix='/api')

# ============================================================================
# YAML CONFIGURATION LOADER
# ============================================================================
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
_terminal_config = {}
_bookmap_config = {}
_data_sources_config = {}

def _load_configs():
    """Load terminal_config.yaml, bookmap_config.yaml, and data_sources_config.yaml."""
    global _terminal_config, _bookmap_config, _data_sources_config, _watchlist
    
    # Load terminal config
    tc_path = os.path.join(_CONFIG_DIR, 'terminal_config.yaml')
    if os.path.exists(tc_path):
        try:
            with open(tc_path, 'r', encoding='utf-8') as f:
                _terminal_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded terminal_config.yaml (v{_terminal_config.get('version', '?')})")
        except Exception as e:
            logger.warning(f"Failed to load terminal_config.yaml: {e}")
    
    # Load bookmap config
    bm_path = os.path.join(_CONFIG_DIR, 'bookmap_config.yaml')
    if os.path.exists(bm_path):
        try:
            with open(bm_path, 'r', encoding='utf-8') as f:
                _bookmap_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded bookmap_config.yaml (v{_bookmap_config.get('version', '?')})")
        except Exception as e:
            logger.warning(f"Failed to load bookmap_config.yaml: {e}")
    
    # Load data sources config
    ds_path = os.path.join(_CONFIG_DIR, 'data_sources_config.yaml')
    if os.path.exists(ds_path):
        try:
            with open(ds_path, 'r', encoding='utf-8') as f:
                _data_sources_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded data_sources_config.yaml (v{_data_sources_config.get('version', '?')})")
        except Exception as e:
            logger.warning(f"Failed to load data_sources_config.yaml: {e}")
    
    # Sync watchlist from config
    wl_cfg = _terminal_config.get('watchlist', {}).get('default_instruments', [])
    if wl_cfg:
        _watchlist.clear()
        for item in wl_cfg:
            _watchlist.append({"symbol": item["symbol"], "name": item.get("name", item["symbol"])})
        logger.info(f"Watchlist loaded from config: {len(_watchlist)} instruments")
    
    # Sync additional instrument prices from data_sources_config
    additional = _data_sources_config.get('additional_instruments', {})
    for category in additional.values():
        if isinstance(category, list):
            for item in category:
                sym = item.get('symbol', '')
                seed = item.get('price_seed', 100.0)
                if sym and sym not in _base_prices:
                    _base_prices[sym] = seed

# NOTE: _load_configs() is called below after _watchlist and _base_prices are defined

# ============================================================================
# IN-MEMORY STATE (simulated data when no live exchange connected)
# ============================================================================
_watchlist = [
    {"symbol": "BTCUSDT", "name": "Bitcoin/USDT"},
    {"symbol": "ETHUSDT", "name": "Ethereum/USDT"},
    {"symbol": "SOLUSDT", "name": "Solana/USDT"},
    {"symbol": "BNBUSDT", "name": "BNB/USDT"},
    {"symbol": "XRPUSDT", "name": "XRP/USDT"},
    {"symbol": "XAUUSD", "name": "Gold Spot/USD"},
    {"symbol": "EURUSD", "name": "Euro/USD"},
    {"symbol": "SPX", "name": "S&P 500"},
]

_base_prices = {
    "BTCUSDT": 96450, "ETHUSDT": 3420, "SOLUSDT": 178, "BNBUSDT": 612,
    "XRPUSDT": 2.42, "XAUUSD": 2345, "EURUSD": 1.0842, "SPX": 5890,
}

_command_history = []

# Sync watchlist from config on load
_load_configs()


def _get_base_price(symbol: str) -> float:
    """Get the base price for a symbol (for simulation)."""
    return _base_prices.get(symbol, 100.0)


def _generate_orderbook(symbol: str, levels: int = 20):
    """Generate realistic order book data."""
    mid = _get_base_price(symbol)
    tick = mid * 0.00005 if mid > 100 else 0.0001
    
    bids = []
    asks = []
    bid_cum = 0
    ask_cum = 0
    
    for i in range(levels):
        # Bids (descending from mid)
        bid_px = mid - tick * (i + 1) * (1 + random.random() * 0.3)
        bid_sz = round(random.uniform(0.5, 50) * (1 + random.random() * (5 if random.random() < 0.08 else 1)), 2)
        bid_cum += bid_sz
        bids.append({
            "price": round(bid_px, 2 if mid > 100 else 4),
            "size": bid_sz,
            "cumulative": round(bid_cum, 2),
            "orders": random.randint(1, 15)
        })
        
        # Asks (ascending from mid)
        ask_px = mid + tick * (i + 1) * (1 + random.random() * 0.3)
        ask_sz = round(random.uniform(0.5, 50) * (1 + random.random() * (5 if random.random() < 0.08 else 1)), 2)
        ask_cum += ask_sz
        asks.append({
            "price": round(ask_px, 2 if mid > 100 else 4),
            "size": ask_sz,
            "cumulative": round(ask_cum, 2),
            "orders": random.randint(1, 15)
        })
    
    return {"bids": bids, "asks": asks, "mid": mid, "spread": round(asks[0]["price"] - bids[0]["price"], 6)}


def _generate_tape(symbol: str, count: int = 50):
    """Generate realistic time & sales data."""
    mid = _get_base_price(symbol)
    tape = []
    now = datetime.now()
    
    for i in range(count):
        ts = now - timedelta(seconds=i * random.uniform(0.1, 2))
        side = "B" if random.random() > 0.48 else "S"
        offset = mid * random.uniform(-0.0003, 0.0003)
        px = round(mid + offset, 2 if mid > 100 else 4)
        sz = round(random.uniform(0.001, 5) * (1 + (random.random() * 20 if random.random() < 0.05 else 0)), 4)
        
        aggressor = "buyer" if side == "B" else "seller"
        tape.append({
            "timestamp": ts.strftime("%H:%M:%S.%f")[:-3],
            "price": px,
            "size": sz,
            "side": side,
            "aggressor": aggressor,
            "value": round(px * sz, 2)
        })
    
    return tape


def _generate_heatmap_snapshot(symbol: str, bars: int = 100, levels: int = 40):
    """Generate bookmap heatmap data: historical depth over time."""
    mid = _get_base_price(symbol)
    tick = mid * 0.0001
    data = []
    now = datetime.now()
    
    for t in range(bars):
        ts = now - timedelta(seconds=(bars - t) * 2)
        drift = mid * 0.0001 * math.sin(t * 0.1) + random.uniform(-mid * 0.0002, mid * 0.0002)
        cur_mid = mid + drift
        
        row = {
            "timestamp": ts.isoformat(),
            "mid": round(cur_mid, 2),
            "levels": []
        }
        
        for l in range(levels):
            offset = (l - levels // 2) * tick
            price = cur_mid + offset
            volume = max(0, random.gauss(20, 15) + (50 if abs(l - levels // 2) < 3 else 0))
            
            if random.random() < 0.02:
                volume *= random.uniform(3, 8)  # Whale order
            
            row["levels"].append({
                "price": round(price, 2 if mid > 100 else 4),
                "volume": round(max(0, volume), 2)
            })
        
        data.append(row)
    
    return data


def _generate_footprint(symbol: str, bars: int = 30):
    """Generate footprint/cluster chart data."""
    mid = _get_base_price(symbol)
    tick = mid * 0.0002
    footprint = []
    now = datetime.now()
    
    for t in range(bars):
        ts = now - timedelta(minutes=(bars - t))
        drift = random.uniform(-mid * 0.001, mid * 0.001)
        bar_mid = mid + drift
        
        clusters = []
        for l in range(-10, 11):
            price = bar_mid + l * tick
            buy_vol = max(0, round(random.gauss(15, 10), 1))
            sell_vol = max(0, round(random.gauss(15, 10), 1))
            delta = round(buy_vol - sell_vol, 1)
            
            clusters.append({
                "price": round(price, 2 if mid > 100 else 4),
                "buyVolume": buy_vol,
                "sellVolume": sell_vol,
                "delta": delta,
                "totalVolume": round(buy_vol + sell_vol, 1)
            })
        
        bar_open = bar_mid - random.uniform(0, mid * 0.001)
        bar_close = bar_mid + random.uniform(-mid * 0.001, mid * 0.001)
        
        footprint.append({
            "timestamp": ts.isoformat(),
            "open": round(bar_open, 2),
            "high": round(max(bar_open, bar_close) + mid * 0.0002, 2),
            "low": round(min(bar_open, bar_close) - mid * 0.0002, 2),
            "close": round(bar_close, 2),
            "volume": round(sum(c["totalVolume"] for c in clusters), 1),
            "delta": round(sum(c["delta"] for c in clusters), 1),
            "clusters": clusters
        })
    
    return footprint


# ============================================================================
# BOOKMAP ENDPOINTS
# ============================================================================

@bookmap_terminal_api.route('/bookmap/depth/<symbol>', methods=['GET'])
def get_bookmap_depth(symbol: str):
    """Get order book depth (DOM) for Bookmap visualization."""
    try:
        levels = int(request.args.get('levels', 20))
        
        # Try real data first
        try:
            from core.realtime_data_feed import RealTimeDataFeed
            import asyncio
            feed = RealTimeDataFeed()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            orderbook = loop.run_until_complete(feed.get_orderbook(symbol, levels))
            loop.close()
            
            if orderbook and orderbook.get('bids') and orderbook.get('asks'):
                return jsonify({
                    'success': True,
                    'symbol': symbol,
                    'source': 'live',
                    'orderbook': orderbook,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            logger.debug(f"Live orderbook not available for {symbol}: {e}")
        
        # Fallback to simulation
        orderbook = _generate_orderbook(symbol, levels)
        return jsonify({
            'success': True,
            'symbol': symbol,
            'source': 'simulated',
            'orderbook': orderbook,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Bookmap depth error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/bookmap/tape/<symbol>', methods=['GET'])
def get_bookmap_tape(symbol: str):
    """Get time & sales (tape) data."""
    try:
        count = int(request.args.get('count', 50))
        tape = _generate_tape(symbol, count)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'count': len(tape),
            'tape': tape,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Tape data error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/bookmap/heatmap/<symbol>', methods=['GET'])
def get_bookmap_heatmap(symbol: str):
    """Get heatmap snapshot data for Bookmap rendering."""
    try:
        bars = int(request.args.get('bars', 100))
        levels = int(request.args.get('levels', 40))
        heatmap = _generate_heatmap_snapshot(symbol, bars, levels)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'bars': len(heatmap),
            'heatmap': heatmap,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Heatmap data error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/bookmap/footprint/<symbol>', methods=['GET'])
def get_bookmap_footprint(symbol: str):
    """Get footprint/cluster chart data."""
    try:
        bars = int(request.args.get('bars', 30))
        footprint = _generate_footprint(symbol, bars)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'bars': len(footprint),
            'footprint': footprint,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Footprint data error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/bookmap/detection/<symbol>', methods=['GET'])
def get_bookmap_detection(symbol: str):
    """Detect icebergs, spoofing, stop runs in order flow."""
    try:
        mid = _get_base_price(symbol)
        detections = []
        now = datetime.now()
        
        # Generate realistic detections
        detection_types = [
            {"type": "iceberg", "description": "Hidden large order detected", "severity": "high"},
            {"type": "spoofing", "description": "Layered orders pulling away", "severity": "critical"},
            {"type": "stop_run", "description": "Stop hunt beyond key level", "severity": "medium"},
            {"type": "whale", "description": "Large institutional order", "severity": "high"},
            {"type": "absorption", "description": "Price absorbed at key level", "severity": "medium"},
        ]
        
        for i in range(random.randint(2, 8)):
            det = random.choice(detection_types)
            offset = mid * random.uniform(-0.005, 0.005)
            
            detections.append({
                "id": f"det_{i}",
                "type": det["type"],
                "description": det["description"],
                "severity": det["severity"],
                "price": round(mid + offset, 2 if mid > 100 else 4),
                "size": round(random.uniform(10, 500), 2),
                "side": random.choice(["bid", "ask"]),
                "timestamp": (now - timedelta(seconds=random.randint(1, 300))).isoformat(),
                "confidence": round(random.uniform(0.6, 0.98), 2)
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'detections': detections,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/bookmap/cvd/<symbol>', methods=['GET'])
def get_bookmap_cvd(symbol: str):
    """Get Cumulative Volume Delta data."""
    try:
        bars = int(request.args.get('bars', 60))
        data = []
        cvd = 0
        now = datetime.now()
        
        for i in range(bars):
            ts = now - timedelta(minutes=(bars - i))
            buy_vol = random.uniform(50, 500)
            sell_vol = random.uniform(50, 500)
            delta = buy_vol - sell_vol
            cvd += delta
            
            data.append({
                "timestamp": ts.isoformat(),
                "buyVolume": round(buy_vol, 1),
                "sellVolume": round(sell_vol, 1),
                "delta": round(delta, 1),
                "cvd": round(cvd, 1)
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'bars': len(data),
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"CVD data error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# OPEN TERMINAL ENDPOINTS
# ============================================================================

@bookmap_terminal_api.route('/terminal/command', methods=['POST'])
def execute_terminal_command():
    """Execute a terminal command and return result."""
    try:
        data = request.get_json() or {}
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'error': 'No command provided'}), 400
        
        result = _process_command(command)
        
        _command_history.append({
            "command": command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'command': command,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Terminal command error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/terminal/history', methods=['GET'])
def get_command_history():
    """Get terminal command history."""
    limit = int(request.args.get('limit', 50))
    return jsonify({
        'success': True,
        'history': _command_history[-limit:],
        'count': len(_command_history)
    })


@bookmap_terminal_api.route('/terminal/watchlist', methods=['GET'])
def get_watchlist():
    """Get terminal watchlist."""
    symbols_data = []
    for item in _watchlist:
        sym = item["symbol"]
        base = _get_base_price(sym)
        change = base * random.uniform(-0.03, 0.03)
        
        symbols_data.append({
            **item,
            "price": round(base + change * 0.3, 2 if base > 100 else 4),
            "change": round(change, 2 if base > 100 else 4),
            "changePercent": round((change / base) * 100, 2),
            "bid": round(base + change * 0.3 - base * 0.00005, 2 if base > 100 else 4),
            "ask": round(base + change * 0.3 + base * 0.00005, 2 if base > 100 else 4),
            "volume": round(random.uniform(1e8, 3e10), 0),
            "high": round(base * 1.01, 2 if base > 100 else 4),
            "low": round(base * 0.99, 2 if base > 100 else 4),
        })
    
    return jsonify({
        'success': True,
        'watchlist': symbols_data,
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/watchlist', methods=['POST'])
def update_watchlist():
    """Add symbol to watchlist."""
    global _watchlist
    data = request.get_json() or {}
    symbol = data.get('symbol', '').upper()
    name = data.get('name', symbol)
    
    if not symbol:
        return jsonify({'success': False, 'error': 'No symbol provided'}), 400
    
    if any(w["symbol"] == symbol for w in _watchlist):
        return jsonify({'success': False, 'error': f'{symbol} already in watchlist'}), 400
    
    _watchlist.append({"symbol": symbol, "name": name})
    _base_prices[symbol] = data.get('price', 100.0)
    
    return jsonify({
        'success': True,
        'message': f'{symbol} added to watchlist',
        'watchlist_count': len(_watchlist)
    })


@bookmap_terminal_api.route('/terminal/watchlist/<symbol>', methods=['DELETE'])
def remove_from_watchlist(symbol: str):
    """Remove symbol from watchlist."""
    global _watchlist
    symbol = symbol.upper()
    _watchlist = [w for w in _watchlist if w["symbol"] != symbol]
    
    return jsonify({
        'success': True,
        'message': f'{symbol} removed from watchlist',
        'watchlist_count': len(_watchlist)
    })


@bookmap_terminal_api.route('/terminal/fundamental/<symbol>', methods=['GET'])
def get_fundamental_data(symbol: str):
    """Get fundamental analysis data — Yahoo Finance + config-driven."""
    base = _get_base_price(symbol)
    category = _get_asset_category(symbol)
    
    # ── Yahoo Finance data (live or simulated) ──
    yahoo_data = {}
    if _HAS_YAHOO_FEED:
        try:
            yahoo_data = get_yahoo_fundamental(symbol, base)
        except Exception as e:
            logger.warning(f"Yahoo feed error for {symbol}: {e}")
    
    # ── Config-based description fallback ──
    fa_cfg = _terminal_config.get('fundamental', {})
    desc_cfg = fa_cfg.get('descriptions', {})
    description = yahoo_data.get('description') or desc_cfg.get(symbol, _get_asset_description(symbol))
    
    # Build metrics based on asset category
    is_crypto = category == "Cryptocurrency"
    is_forex = category == "Forex"
    is_index = category == "Index"
    
    # ── Crypto on-chain metrics (from Yahoo or simulated) ──
    crypto_metrics = None
    if is_crypto:
        crypto_metrics = {
            "nvtRatio": yahoo_data.get('nvtRatio', round(random.uniform(15, 80), 1)),
            "stockToFlow": yahoo_data.get('stockToFlow', 56.2 if "BTC" in symbol else None),
            "activeAddresses": yahoo_data.get('activeAddresses', round(random.uniform(300000, 1200000))),
            "hashRate": yahoo_data.get('hashRate', "623 EH/s" if "BTC" in symbol else None),
            "stakingApy": yahoo_data.get('stakingApy', None if "BTC" in symbol else round(random.uniform(3, 8), 1)),
            "tvlDefi": yahoo_data.get('tvlDefi', round(random.uniform(5e9, 50e9), 0)),
            "volatility30d": yahoo_data.get('volatility30d', round(random.uniform(30, 80), 1)),
            "sharpeRatio1y": yahoo_data.get('sharpeRatio1y', round(random.uniform(0.5, 2.5), 2)),
            "burnRate": yahoo_data.get('burnRate'),
            "tps": yahoo_data.get('tps'),
            "dominance": yahoo_data.get('dominance', round(random.uniform(0.5, 5), 2)),
        }
    
    # ── Equity/Index metrics (from Yahoo or simulated) ──
    equity_metrics = None
    if not is_crypto and not is_forex:
        equity_metrics = {
            "peRatio": yahoo_data.get('peRatio', round(random.uniform(10, 35), 1)),
            "forwardPe": yahoo_data.get('forwardPe'),
            "pbRatio": yahoo_data.get('pbRatio', round(random.uniform(1.5, 6), 1)),
            "psRatio": yahoo_data.get('psRatio'),
            "pegRatio": yahoo_data.get('pegRatio'),
            "epsTtm": yahoo_data.get('eps', round(base * random.uniform(0.03, 0.06), 2)),
            "forwardEps": yahoo_data.get('forwardEps'),
            "dividendYield": yahoo_data.get('dividendYield', round(random.uniform(0, 3), 1)),
            "beta": yahoo_data.get('beta', round(random.uniform(0.8, 1.5), 2)),
            "debtToEquity": yahoo_data.get('debtToEquity', round(random.uniform(20, 150), 1)),
            "roe": yahoo_data.get('roe', round(random.uniform(12, 25), 1)),
            "roa": yahoo_data.get('roa'),
            "profitMargin": yahoo_data.get('profitMargin', round(random.uniform(15, 35), 1)),
            "grossMargin": yahoo_data.get('grossMargin'),
            "operatingMargin": yahoo_data.get('operatingMargin'),
            "revenueGrowth": yahoo_data.get('revenueGrowth', round(random.uniform(-5, 30), 1)),
            "earningsGrowth": yahoo_data.get('earningsGrowth', round(random.uniform(-10, 40), 1)),
            "revenue": yahoo_data.get('revenue'),
            "netIncome": yahoo_data.get('netIncome'),
            "freeCashFlow": yahoo_data.get('freeCashFlow'),
            "totalCash": yahoo_data.get('totalCash'),
            "totalDebt": yahoo_data.get('totalDebt'),
            "currentRatio": yahoo_data.get('currentRatio'),
            "sharesOutstanding": yahoo_data.get('sharesOutstanding'),
            "shortRatio": yahoo_data.get('shortRatio'),
            "insiderHolding": yahoo_data.get('insiderHolding'),
            "institutionHolding": yahoo_data.get('institutionHolding'),
            "employees": yahoo_data.get('employees'),
        }
    
    # ── Forex metrics ──
    forex_metrics = None
    if is_forex:
        forex_metrics = {
            "spread": yahoo_data.get('spread'),
            "spreadPips": yahoo_data.get('spreadPips'),
            "swapLong": yahoo_data.get('swapLong'),
            "swapShort": yahoo_data.get('swapShort'),
            "pipValue": yahoo_data.get('pipValue'),
            "dailyRange": yahoo_data.get('dailyRange'),
            "interestRateBase": yahoo_data.get('interestRateBase'),
            "interestRateQuote": yahoo_data.get('interestRateQuote'),
            "carryReturn": yahoo_data.get('carryReturn'),
            "correlation_DXY": yahoo_data.get('correlation_DXY'),
            "volatility30d": yahoo_data.get('volatility30d'),
        }
    
    # ── Bond metrics ──
    bond_metrics = None
    is_bond = category == "Bond" or symbol in ("US10Y","US2Y","US5Y","US30Y","DE10Y","GB10Y","JP10Y","IT10Y","FR10Y","AU10Y","TLT","HYG")
    if is_bond:
        bond_metrics = {
            "yieldToMaturity": yahoo_data.get('yieldToMaturity', base),
            "couponRate": yahoo_data.get('couponRate'),
            "duration": yahoo_data.get('duration'),
            "modifiedDuration": yahoo_data.get('modifiedDuration'),
            "convexity": yahoo_data.get('convexity'),
            "creditRating": yahoo_data.get('creditRating', 'AAA'),
            "maturityDate": yahoo_data.get('maturityDate'),
            "spreadToBenchmark": yahoo_data.get('spreadToBenchmark'),
            "yieldCurveSlope": yahoo_data.get('yieldCurveSlope'),
        }
    
    # ── Commodity metrics ──
    commodity_metrics = None
    is_commodity = category == "Commodity" or symbol.endswith("USD") and not is_forex and not is_crypto
    if is_commodity and not is_forex:
        commodity_metrics = {
            "contractMonth": yahoo_data.get('contractMonth'),
            "openInterest": yahoo_data.get('openInterest'),
            "contango": yahoo_data.get('contango'),
            "inventoryLevel": yahoo_data.get('inventoryLevel'),
            "seasonalPattern": yahoo_data.get('seasonalPattern'),
            "volatility30d": yahoo_data.get('volatility30d'),
        }
    
    # ── Analyst consensus (Yahoo or config) ──
    consensus_cfg = fa_cfg.get('analyst_consensus', {})
    analyst_consensus = None
    if consensus_cfg.get('enabled', True):
        rec_key = yahoo_data.get('recommendationKey', '')
        n_analysts = yahoo_data.get('numberOfAnalystOpinions')
        if n_analysts and n_analysts > 0:
            # Use Yahoo analyst data
            analyst_consensus = {
                "totalAnalysts": n_analysts,
                "recommendation": (rec_key or 'hold').upper().replace('_', ' '),
                "recommendationScore": yahoo_data.get('recommendationMean'),
                "targetHigh": yahoo_data.get('targetHighPrice'),
                "targetLow": yahoo_data.get('targetLowPrice'),
                "targetMean": yahoo_data.get('targetMeanPrice'),
                "targetMedian": yahoo_data.get('targetMedianPrice'),
            }
        else:
            # Fallback simulated
            total = random.randint(15, 30)
            buy_pct = random.uniform(0.4, 0.7)
            sell_pct = random.uniform(0.05, 0.2)
            analyst_consensus = {
                "totalAnalysts": total,
                "buy": round(total * buy_pct),
                "hold": round(total * (1 - buy_pct - sell_pct)),
                "sell": round(total * sell_pct),
                "targetMean": round(base * random.uniform(1.05, 1.2), 2),
                "recommendation": "BUY" if buy_pct > 0.5 else "HOLD",
            }
    
    # ── ESG scores ──
    esg_cfg = fa_cfg.get('esg', {})
    esg = None
    if esg_cfg.get('enabled', True) and not is_crypto and not is_forex:
        esg = {
            "environmental": random.randint(60, 90),
            "social": random.randint(55, 85),
            "governance": random.randint(65, 95),
            "total": random.randint(60, 90),
        }
    
    # ── Build final response ──
    fundamental = {
        "symbol": symbol,
        "name": yahoo_data.get('name', description.split('.')[0] if description else symbol),
        "category": category,
        "sector": yahoo_data.get('sector', category),
        "industry": yahoo_data.get('industry', ''),
        "description": description,
        "dataSource": yahoo_data.get('_source', 'config_fallback'),
        "marketCap": yahoo_data.get('marketCap', round(random.uniform(1e10, 2e12), 0)),
        "volume24h": yahoo_data.get('volume', round(random.uniform(1e8, 3e10), 0)),
        "52wHigh": yahoo_data.get('52wHigh', round(base * random.uniform(1.1, 2.5), 2)),
        "52wLow": yahoo_data.get('52wLow', round(base * random.uniform(0.01, 0.5), 2)),
        "fiftyDayAvg": yahoo_data.get('fiftyDayAvg'),
        "twoHundredDayAvg": yahoo_data.get('twoHundredDayAvg'),
        "change7d": yahoo_data.get('change7d', round(random.uniform(-15, 25), 2)),
        "change30d": yahoo_data.get('change30d', round(random.uniform(-25, 50), 2)),
        "cryptoMetrics": crypto_metrics,
        "equityMetrics": equity_metrics,
        "forexMetrics": forex_metrics,
        "bondMetrics": bond_metrics,
        "commodityMetrics": commodity_metrics,
        "analystConsensus": analyst_consensus,
        "esg": esg,
    }
    
    return jsonify({
        'success': True,
        'fundamental': fundamental,
        'source': yahoo_data.get('_source', 'config_fallback'),
        'cached': yahoo_data.get('_cached', False),
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/news', methods=['GET'])
def get_terminal_news():
    """Get latest market news."""
    symbol = request.args.get('symbol', None)
    limit = int(request.args.get('limit', 20))
    
    news_items = [
        {"id": "1", "ts": "14:32", "src": "RTRS", "urg": "FLASH", "text": "FED HOLDS RATES STEADY AT 5.25-5.50%; SIGNALS POSSIBLE CUT Q2"},
        {"id": "2", "ts": "14:28", "src": "BBG", "urg": "FLASH", "text": "BITCOIN ETF RECORD $523M INFLOW – LARGEST SINCE NOV 2025"},
        {"id": "3", "ts": "14:15", "src": "RTRS", "urg": "ALERT", "text": "US NFP 187K VS EST 180K; UNEMPLOYMENT RATE 3.8% VS EST 3.9%"},
        {"id": "4", "ts": "13:58", "src": "CDESK", "urg": "ALERT", "text": "ETHEREUM DENCUN UPGRADE LIVE – L2 GAS FEES DROP 60%"},
        {"id": "5", "ts": "13:45", "src": "BBG", "urg": "INFO", "text": "ECB LAGARDE: INFLATION PROGRESS ENCOURAGING BUT NOT YET SUFFICIENT"},
        {"id": "6", "ts": "13:30", "src": "RTRS", "urg": "INFO", "text": "CHINA CAIXIN PMI 51.2 VS EST 50.5 – EXPANSION ACCELERATES"},
        {"id": "7", "ts": "13:12", "src": "BBG", "urg": "ALERT", "text": "GRAYSCALE FILES SOLANA ETF APPLICATION WITH SEC"},
        {"id": "8", "ts": "12:55", "src": "RTRS", "urg": "INFO", "text": "CRUDE OIL +1.5% ON REPORTS OPEC+ EXTENDS PRODUCTION CUTS"},
        {"id": "9", "ts": "12:40", "src": "FT", "urg": "INFO", "text": "US 10Y YIELD RISES TO 4.28% AFTER STRONG JOBS DATA"},
        {"id": "10", "ts": "12:22", "src": "BBG", "urg": "INFO", "text": "APPLE ANNOUNCES $110B SHARE BUYBACK – LARGEST IN US HISTORY"},
        {"id": "11", "ts": "12:05", "src": "RTRS", "urg": "ALERT", "text": "NASDAQ HITS NEW ALL-TIME HIGH ABOVE 19,200"},
        {"id": "12", "ts": "11:48", "src": "BBG", "urg": "INFO", "text": "OPEC+ PRODUCTION QUOTA UNCHANGED FOR Q1 2026"},
        {"id": "13", "ts": "11:30", "src": "FT", "urg": "INFO", "text": "EUROPEAN GAS PRICES FALL 3% ON MILD WEATHER FORECAST"},
        {"id": "14", "ts": "11:15", "src": "CDESK", "urg": "ALERT", "text": "SOLANA TVL REACHES $15B – NEW ALL-TIME HIGH"},
        {"id": "15", "ts": "11:00", "src": "RTRS", "urg": "INFO", "text": "JAPAN BOJ MAINTAINS NEGATIVE RATE POLICY; YEN WEAKENS"},
    ]
    
    return jsonify({
        'success': True,
        'news': news_items[:limit],
        'count': min(len(news_items), limit),
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/options/<symbol>', methods=['GET'])
def get_options_monitor(symbol: str):
    """Get options chain overview for a symbol (config-driven)."""
    base = _get_base_price(symbol)
    omon_cfg = _terminal_config.get('options_monitor', {})
    
    strikes_count = omon_cfg.get('strikes_count', 12)
    strike_interval = omon_cfg.get('strike_interval_pct', 0.01)
    expiry_days = omon_cfg.get('default_expiry_days', 30)
    greeks_model = omon_cfg.get('greeks_model', 'Black-Scholes')
    risk_free_rate = omon_cfg.get('risk_free_rate', 0.045)
    
    half = strikes_count // 2
    strikes = []
    total_call_vol = 0
    total_put_vol = 0
    
    for i in range(-half, half + 1):
        strike = round(base * (1 + i * strike_interval), 2)
        
        call_iv = round(random.uniform(20, 80), 1)
        put_iv = round(random.uniform(20, 80), 1)
        c_vol = random.randint(10, 5000)
        p_vol = random.randint(10, 5000)
        total_call_vol += c_vol
        total_put_vol += p_vol
        
        strikes.append({
            "strike": strike,
            "call": {
                "bid": round(max(0, (base - strike) + random.uniform(0.5, 5)), 2),
                "ask": round(max(0.01, (base - strike) + random.uniform(1, 6)), 2),
                "volume": c_vol,
                "oi": random.randint(100, 50000),
                "iv": call_iv,
                "delta": round(max(-1, min(1, 0.5 - i * 0.1 + random.uniform(-0.05, 0.05))), 3),
                "gamma": round(random.uniform(0.001, 0.05), 4),
                "theta": round(-random.uniform(0.01, 2), 3),
                "vega": round(random.uniform(0.01, 5), 3),
            },
            "put": {
                "bid": round(max(0, (strike - base) + random.uniform(0.5, 5)), 2),
                "ask": round(max(0.01, (strike - base) + random.uniform(1, 6)), 2),
                "volume": p_vol,
                "oi": random.randint(100, 50000),
                "iv": put_iv,
                "delta": round(max(-1, min(0, -0.5 + i * 0.1 + random.uniform(-0.05, 0.05))), 3),
                "gamma": round(random.uniform(0.001, 0.05), 4),
                "theta": round(-random.uniform(0.01, 2), 3),
                "vega": round(random.uniform(0.01, 5), 3),
            }
        })
    
    pcr = round(total_put_vol / max(1, total_call_vol), 2)
    max_pain_idx = len(strikes) // 2
    max_pain = strikes[max_pain_idx]["strike"] if strikes else base
    
    return jsonify({
        'success': True,
        'symbol': symbol,
        'expiry': (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d'),
        'strikes': strikes,
        'putCallRatio': pcr,
        'maxPain': max_pain,
        'greeksModel': greeks_model,
        'riskFreeRate': risk_free_rate,
        'config': {
            'strikesCount': strikes_count,
            'strikeIntervalPct': strike_interval,
            'expiryDays': expiry_days,
            'showPcr': omon_cfg.get('show_pcr', True),
            'showMaxPain': omon_cfg.get('show_max_pain', True),
            'showIvSkew': omon_cfg.get('show_iv_skew', True),
        },
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# COMMAND PROCESSOR
# ============================================================================

def _process_command(command: str) -> dict:
    """Process a terminal command and return structured result."""
    parts = command.upper().split()
    cmd = parts[0] if parts else ""
    args = parts[1:] if len(parts) > 1 else []
    
    handlers = {
        "HELP": _cmd_help,
        "PRICE": _cmd_price,
        "QUOTE": _cmd_price,
        "Q": _cmd_price,
        "BUY": _cmd_order,
        "SELL": _cmd_order,
        "POS": _cmd_positions,
        "POSITIONS": _cmd_positions,
        "RISK": _cmd_risk,
        "STATUS": _cmd_status,
        "SCAN": _cmd_scan,
        "GANN": _cmd_gann,
        "ASTRO": _cmd_astro,
        "NEWS": _cmd_news,
        "CLEAR": _cmd_clear,
        "TIME": _cmd_time,
        "BALANCE": _cmd_balance,
        "PNL": _cmd_pnl,
    }
    
    handler = handlers.get(cmd, _cmd_unknown)
    return handler(cmd, args)


def _cmd_help(cmd, args):
    return {
        "type": "info",
        "output": [
            "╔══════════════════════════════════════╗",
            "║  GANN QUANT AI – TERMINAL COMMANDS   ║",
            "╚══════════════════════════════════════╝",
            "",
            "PRICE <SYM>    – Get price quote",
            "BUY <SYM> <QTY> – Place buy order",
            "SELL <SYM> <QTY> – Place sell order",
            "POS            – Show open positions",
            "RISK           – Show risk metrics",
            "SCAN           – Run market scanner",
            "GANN <SYM>     – Gann analysis",
            "ASTRO          – Astro signals",
            "NEWS           – Latest headlines",
            "BALANCE        – Account balance",
            "PNL            – P&L summary",
            "STATUS         – System status",
            "TIME           – Server time",
            "CLEAR          – Clear terminal",
            "HELP           – This help",
        ]
    }


def _cmd_price(cmd, args):
    if not args:
        return {"type": "error", "output": ["Usage: PRICE <SYMBOL>", "Example: PRICE BTCUSDT"]}
    
    sym = args[0]
    base = _get_base_price(sym)
    change = base * random.uniform(-0.02, 0.02)
    
    return {
        "type": "data",
        "output": [
            f"═══ {sym} ═══",
            f"  Price:  ${base + change:,.2f}",
            f"  Change: {change:+,.2f} ({(change/base)*100:+.2f}%)",
            f"  Bid:    ${base + change - base*0.00005:,.2f}",
            f"  Ask:    ${base + change + base*0.00005:,.2f}",
            f"  High:   ${base * 1.01:,.2f}",
            f"  Low:    ${base * 0.99:,.2f}",
        ]
    }


def _cmd_order(cmd, args):
    if len(args) < 2:
        return {"type": "error", "output": [f"Usage: {cmd} <SYMBOL> <QUANTITY>", f"Example: {cmd} BTCUSDT 0.1"]}
    
    sym, qty = args[0], args[1]
    base = _get_base_price(sym)
    
    return {
        "type": "success",
        "output": [
            f"✓ ORDER PLACED",
            f"  Side:   {cmd}",
            f"  Symbol: {sym}",
            f"  Qty:    {qty}",
            f"  Price:  ${base:,.2f} (MARKET)",
            f"  Status: FILLED",
            f"  ID:     ORD-{random.randint(100000, 999999)}",
        ]
    }


def _cmd_positions(cmd, args):
    return {
        "type": "data",
        "output": [
            "═══ OPEN POSITIONS ═══",
            f"  BTCUSDT  LONG   0.5  Entry: $96,200  P&L: +${random.randint(50, 800):,}",
            f"  ETHUSDT  SHORT  2.0  Entry: $3,450   P&L: {'-' if random.random() > 0.5 else '+'}${random.randint(20, 300):,}",
            f"  XAUUSD   LONG   1.0  Entry: $2,330   P&L: +${random.randint(10, 200):,}",
            f"",
            f"  Total Positions: 3",
            f"  Net Exposure: ${random.randint(40000, 60000):,}",
        ]
    }


def _cmd_risk(cmd, args):
    return {
        "type": "data",
        "output": [
            "═══ RISK METRICS ═══",
            f"  Portfolio Heat:  {random.uniform(3, 12):.1f}%",
            f"  Daily P&L:      +${random.randint(100, 2000):,}",
            f"  Max Drawdown:   {random.uniform(1, 8):.1f}%",
            f"  Sharpe Ratio:   {random.uniform(0.5, 3):.2f}",
            f"  Win Rate:       {random.uniform(45, 72):.1f}%",
            f"  Risk/Reward:    1:{random.uniform(1.5, 3.5):.1f}",
            f"  VaR (95%):      ${random.randint(500, 3000):,}",
        ]
    }


def _cmd_status(cmd, args):
    return {
        "type": "info",
        "output": [
            "═══ SYSTEM STATUS ═══",
            f"  API:        ● ONLINE",
            f"  WebSocket:  ● CONNECTED",
            f"  Data Feed:  ● ACTIVE",
            f"  Gann:       ● READY",
            f"  Ehlers:     ● READY",
            f"  Astro:      ● READY",
            f"  ML Engine:  ● TRAINED",
            f"  Scanner:    ● SCANNING",
            f"  Uptime:     {random.randint(1, 72)}h {random.randint(0, 59)}m",
            f"  Latency:    {random.uniform(0.5, 5):.1f}ms",
        ]
    }


def _cmd_scan(cmd, args):
    return {
        "type": "success",
        "output": [
            "═══ SCANNER RESULTS ═══",
            f"  BTCUSDT  ▲ BUY   Score: {random.uniform(70, 95):.0f}%  Gann+Ehlers confluence",
            f"  SOLUSDT  ▲ BUY   Score: {random.uniform(65, 90):.0f}%  Breakout pattern",
            f"  XAUUSD   ▼ SELL  Score: {random.uniform(60, 85):.0f}%  Resistance rejection",
            f"  ETHUSDT  ● HOLD  Score: {random.uniform(40, 60):.0f}%  Consolidation",
            f"",
            f"  Scanned: {len(_watchlist)} instruments",
            f"  Signals: 3 actionable",
        ]
    }


def _cmd_gann(cmd, args):
    sym = args[0] if args else "BTCUSDT"
    base = _get_base_price(sym)
    
    return {
        "type": "data",
        "output": [
            f"═══ GANN ANALYSIS: {sym} ═══",
            f"  SQ9 Support:    ${base * 0.97:,.2f}",
            f"  SQ9 Resistance: ${base * 1.03:,.2f}",
            f"  1x1 Angle:      ${base * 0.985:,.2f}",
            f"  2x1 Angle:      ${base * 1.02:,.2f}",
            f"  Time Cycle:     Next turn in {random.randint(3, 21)} bars",
            f"  Vibration:      {random.uniform(0.6, 0.95):.2f}",
            f"  Signal:         {'BULLISH' if random.random() > 0.4 else 'BEARISH'}",
        ]
    }


def _cmd_astro(cmd, args):
    return {
        "type": "data",
        "output": [
            "═══ ASTRO SIGNALS ═══",
            f"  Moon Phase:     {'Waxing Gibbous' if random.random() > 0.5 else 'Waning Crescent'}",
            f"  Mercury:        {'Retrograde ⚠' if random.random() > 0.7 else 'Direct ✓'}",
            f"  Jupiter-Saturn: {random.uniform(85, 120):.1f}° (approaching square)",
            f"  Mars Aspect:    {'Conjunction with Venus' if random.random() > 0.5 else 'Square Neptune'}",
            f"  Bradley Index:  {random.uniform(-50, 50):+.1f}",
            f"  Next Turn Date: {(datetime.now() + timedelta(days=random.randint(2, 15))).strftime('%Y-%m-%d')}",
            f"  Sentiment:      {'Bullish bias' if random.random() > 0.4 else 'Bearish caution'}",
        ]
    }


def _cmd_news(cmd, args):
    return {
        "type": "info",
        "output": [
            "═══ LATEST NEWS ═══",
            "  [FLASH] FED HOLDS RATES STEADY AT 5.25-5.50%",
            "  [FLASH] BITCOIN ETF RECORD $523M INFLOW",
            "  [ALERT] US NFP 187K VS EST 180K",
            "  [ALERT] ETHEREUM DENCUN UPGRADE LIVE",
            "  [INFO]  ECB: INFLATION PROGRESS ENCOURAGING",
        ]
    }


def _cmd_clear(cmd, args):
    return {"type": "clear", "output": []}


def _cmd_time(cmd, args):
    now = datetime.now()
    return {
        "type": "info",
        "output": [
            f"  Server Time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"  NY Session:  {'OPEN' if 13 <= now.hour <= 22 else 'CLOSED'}",
            f"  LDN Session: {'OPEN' if 8 <= now.hour <= 17 else 'CLOSED'}",
            f"  TKY Session: {'OPEN' if 0 <= now.hour <= 9 else 'CLOSED'}",
        ]
    }


def _cmd_balance(cmd, args):
    return {
        "type": "data",
        "output": [
            "═══ ACCOUNT BALANCE ═══",
            f"  Balance:   ${random.randint(80000, 120000):,}",
            f"  Equity:    ${random.randint(85000, 125000):,}",
            f"  Margin:    ${random.randint(5000, 20000):,}",
            f"  Free:      ${random.randint(60000, 100000):,}",
            f"  Leverage:  10:1",
        ]
    }


def _cmd_pnl(cmd, args):
    return {
        "type": "data",
        "output": [
            "═══ P&L SUMMARY ═══",
            f"  Today:     +${random.randint(100, 3000):,}  ({random.uniform(0.1, 3):.1f}%)",
            f"  This Week: +${random.randint(500, 8000):,}  ({random.uniform(0.5, 8):.1f}%)",
            f"  This Month:+${random.randint(1000, 15000):,} ({random.uniform(1, 15):.1f}%)",
            f"  Win Rate:   {random.uniform(50, 72):.1f}%",
            f"  Trades:     {random.randint(20, 80)}",
        ]
    }


def _cmd_unknown(cmd, args):
    return {
        "type": "error",
        "output": [f"Unknown command: {cmd}", "Type HELP for available commands."]
    }


# ============================================================================
# HELPERS
# ============================================================================

def _get_asset_category(symbol: str) -> str:
    if "BTC" in symbol or "ETH" in symbol or "SOL" in symbol or "BNB" in symbol or "XRP" in symbol:
        return "Cryptocurrency"
    elif "XAU" in symbol or "XAG" in symbol:
        return "Commodity"
    elif "EUR" in symbol or "GBP" in symbol or "JPY" in symbol:
        return "Forex"
    elif "SPX" in symbol or "NDX" in symbol or "DJI" in symbol:
        return "Index"
    return "Other"


def _get_asset_description(symbol: str) -> str:
    descriptions = {
        "BTCUSDT": "Bitcoin is the first decentralized cryptocurrency, created in 2009.",
        "ETHUSDT": "Ethereum is a decentralized platform for smart contracts and DApps.",
        "SOLUSDT": "Solana is a high-performance blockchain supporting smart contracts.",
        "BNBUSDT": "BNB is the native token of the Binance ecosystem.",
        "XRPUSDT": "XRP is a digital payment protocol and cryptocurrency.",
        "XAUUSD": "Gold Spot price against the US Dollar.",
        "EURUSD": "Euro vs US Dollar, the most traded currency pair.",
        "SPX": "The S&P 500 Index tracks 500 largest US companies.",
    }
    return descriptions.get(symbol, f"Market data for {symbol}")


# ============================================================================
# CONFIG & CALENDAR ENDPOINTS
# ============================================================================

@bookmap_terminal_api.route('/terminal/config', methods=['GET'])
def get_terminal_config():
    """Get terminal configuration."""
    return jsonify({
        'success': True,
        'config': _terminal_config,
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/config', methods=['PUT'])
def update_terminal_config():
    """Update terminal configuration (partial update)."""
    global _terminal_config
    try:
        updates = request.get_json() or {}
        
        # Deep merge updates into existing config
        def deep_merge(base, update):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(_terminal_config, updates)
        
        # Save to file
        tc_path = os.path.join(_CONFIG_DIR, 'terminal_config.yaml')
        with open(tc_path, 'w', encoding='utf-8') as f:
            yaml.dump(_terminal_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("Terminal config updated and saved")
        return jsonify({'success': True, 'message': 'Config updated'})
        
    except Exception as e:
        logger.error(f"Config update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/bookmap/config', methods=['GET'])
def get_bookmap_config():
    """Get bookmap configuration."""
    return jsonify({
        'success': True,
        'config': _bookmap_config,
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/calendar', methods=['GET'])
def get_economic_calendar():
    """Get economic calendar events."""
    cal_cfg = _terminal_config.get('economic_calendar', {})
    max_events = int(request.args.get('limit', cal_cfg.get('max_events', 20)))
    
    # Simulated upcoming events (would connect to real data provider)
    now = datetime.now()
    events = [
        {
            "id": "ev_1",
            "time": (now + timedelta(hours=1)).strftime('%H:%M'),
            "date": now.strftime('%Y-%m-%d'),
            "event": "FOMC Meeting Minutes",
            "country": "US",
            "impact": "HIGH",
            "actual": None,
            "forecast": None,
            "previous": None,
            "category": "FOMC_DECISION",
        },
        {
            "id": "ev_2",
            "time": (now + timedelta(hours=2, minutes=30)).strftime('%H:%M'),
            "date": now.strftime('%Y-%m-%d'),
            "event": "US Initial Jobless Claims",
            "country": "US",
            "impact": "MED",
            "actual": None,
            "forecast": "210K",
            "previous": "215K",
            "category": "JOBLESS_CLAIMS",
        },
        {
            "id": "ev_3",
            "time": (now + timedelta(hours=3)).strftime('%H:%M'),
            "date": now.strftime('%Y-%m-%d'),
            "event": "ISM Manufacturing PMI",
            "country": "US",
            "impact": "HIGH",
            "actual": None,
            "forecast": "49.5",
            "previous": "49.2",
            "category": "ISM_MANUFACTURING",
        },
        {
            "id": "ev_4",
            "time": (now + timedelta(hours=6)).strftime('%H:%M'),
            "date": now.strftime('%Y-%m-%d'),
            "event": "Fed Chair Powell Speech",
            "country": "US",
            "impact": "HIGH",
            "actual": None,
            "forecast": None,
            "previous": None,
            "category": "FED_SPEECH",
        },
        {
            "id": "ev_5",
            "time": "08:30",
            "date": (now + timedelta(days=1)).strftime('%Y-%m-%d'),
            "event": "EU GDP (QoQ)",
            "country": "EU",
            "impact": "MED",
            "actual": None,
            "forecast": "0.3%",
            "previous": "0.1%",
            "category": "GDP",
        },
        {
            "id": "ev_6",
            "time": "13:30",
            "date": (now + timedelta(days=1)).strftime('%Y-%m-%d'),
            "event": "US CPI (YoY)",
            "country": "US",
            "impact": "HIGH",
            "actual": None,
            "forecast": "2.9%",
            "previous": "3.0%",
            "category": "CPI",
        },
        {
            "id": "ev_7",
            "time": "08:00",
            "date": (now + timedelta(days=2)).strftime('%Y-%m-%d'),
            "event": "UK Retail Sales (MoM)",
            "country": "UK",
            "impact": "MED",
            "actual": None,
            "forecast": "0.5%",
            "previous": "-0.3%",
            "category": "RETAIL_SALES",
        },
        {
            "id": "ev_8",
            "time": "00:30",
            "date": (now + timedelta(days=2)).strftime('%Y-%m-%d'),
            "event": "BOJ Interest Rate Decision",
            "country": "JP",
            "impact": "HIGH",
            "actual": None,
            "forecast": "-0.10%",
            "previous": "-0.10%",
            "category": "BOJ_DECISION",
        },
    ]
    
    # Get tracked event types from config
    tracked = cal_cfg.get('tracked_events', [])
    countries = cal_cfg.get('countries', [])
    
    # Filter by config if set
    filtered = events
    if tracked:
        filtered = [e for e in filtered if e.get('category') in tracked]
    if countries:
        filtered = [e for e in filtered if e.get('country') in countries]
    
    return jsonify({
        'success': True,
        'events': filtered[:max_events],
        'count': len(filtered[:max_events]),
        'impactLevels': cal_cfg.get('impact_levels', []),
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/sessions', methods=['GET'])
def get_market_sessions():
    """Get current market session status."""
    sessions_cfg = _terminal_config.get('market_sessions', [])
    now = datetime.utcnow()
    current_hour = now.hour
    current_min = now.minute
    current_time = current_hour * 60 + current_min
    
    sessions = []
    for sess in sessions_cfg:
        open_parts = sess.get('open_utc', '00:00').split(':')
        close_parts = sess.get('close_utc', '23:59').split(':')
        open_time = int(open_parts[0]) * 60 + int(open_parts[1])
        close_time = int(close_parts[0]) * 60 + int(close_parts[1])
        
        # Handle overnight sessions (e.g., Sydney 22:00 - 05:00)
        if open_time > close_time:
            is_open = current_time >= open_time or current_time <= close_time
        else:
            is_open = open_time <= current_time <= close_time
        
        sessions.append({
            "name": sess.get('name'),
            "code": sess.get('code'),
            "openUtc": sess.get('open_utc'),
            "closeUtc": sess.get('close_utc'),
            "timezone": sess.get('timezone'),
            "isOpen": is_open,
            "status": "OPEN" if is_open else "CLOSED",
        })
    
    return jsonify({
        'success': True,
        'sessions': sessions,
        'serverTimeUtc': now.strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/reload-config', methods=['POST'])
def reload_terminal_config():
    """Reload configuration from YAML files."""
    try:
        _load_configs()
        return jsonify({
            'success': True,
            'message': 'Configuration reloaded',
            'terminalVersion': _terminal_config.get('version', 'unknown'),
            'bookmapVersion': _bookmap_config.get('version', 'unknown'),
            'dataSourcesVersion': _data_sources_config.get('version', 'unknown'),
        })
    except Exception as e:
        logger.error(f"Config reload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bookmap_terminal_api.route('/terminal/data-sources', methods=['GET'])
def get_data_sources():
    """Get data sources configuration (exchanges, fundamentals, technicals)."""
    ds = _data_sources_config
    
    # Build summary of data sources
    exchanges = {}
    for key, val in ds.get('exchanges', {}).items():
        if isinstance(val, dict):
            exchanges[key] = {
                'name': val.get('name'),
                'type': val.get('type'),
                'enabled': val.get('enabled', False),
                'apiBase': val.get('api_base'),
                'symbols': val.get('symbols', []),
                'supportedIntervals': val.get('supported_intervals', []),
            }
    
    fundamental = {}
    for key, val in ds.get('fundamental', {}).items():
        if isinstance(val, dict):
            fundamental[key] = {
                'name': val.get('name'),
                'type': val.get('type'),
                'enabled': val.get('enabled', False),
                'metricsProvided': val.get('metrics_provided', []),
            }
    
    technical = {}
    tech_cfg = ds.get('technical', {})
    for key, val in tech_cfg.items():
        if isinstance(val, dict):
            indicators = val.get('indicators', [])
            if isinstance(indicators, dict):
                # Flatten nested indicator groups
                flat = []
                for group_name, group_items in indicators.items():
                    if isinstance(group_items, list):
                        for ind in group_items:
                            flat.append({
                                'name': ind.get('name'),
                                'description': ind.get('description'),
                                'group': group_name,
                                'params': ind.get('params', []),
                            })
                indicators = flat
            elif isinstance(indicators, list):
                indicators = [{
                    'name': ind.get('name'),
                    'description': ind.get('description'),
                } for ind in indicators]
            
            technical[key] = {
                'description': val.get('description'),
                'enabled': val.get('enabled', False),
                'indicators': indicators,
            }
    
    news = {}
    for key, val in ds.get('news_sources', {}).items():
        if isinstance(val, dict):
            news[key] = {
                'name': val.get('name'),
                'type': val.get('type'),
                'enabled': val.get('enabled', False),
            }
    
    return jsonify({
        'success': True,
        'version': ds.get('version', 'unknown'),
        'exchanges': exchanges,
        'fundamental': fundamental,
        'technical': technical,
        'news': news,
        'refreshIntervals': ds.get('refresh_intervals', {}),
        'simulation': ds.get('simulation', {}),
        'timestamp': datetime.now().isoformat()
    })


@bookmap_terminal_api.route('/terminal/yahoo/quote/<symbol>', methods=['GET'])
def get_yahoo_price_quote(symbol: str):
    """Get quick Yahoo Finance price quote."""
    if _HAS_YAHOO_FEED:
        try:
            data = get_yahoo_quote(symbol)
            return jsonify(data)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'Yahoo feed not available'}), 503


@bookmap_terminal_api.route('/terminal/yahoo/status', methods=['GET'])
def get_yahoo_feed_status():
    """Get Yahoo Finance feed status and capabilities."""
    if _HAS_YAHOO_FEED:
        status = get_yahoo_status()
        return jsonify({'success': True, **status})
    return jsonify({
        'success': True,
        'yfinanceInstalled': False,
        'mode': 'simulated',
        'message': 'Install yfinance for live data: pip install yfinance'
    })


@bookmap_terminal_api.route('/terminal/yahoo/cache/clear', methods=['POST'])
def clear_yahoo_cache():
    """Clear Yahoo Finance data cache."""
    symbol = request.args.get('symbol')
    if _HAS_YAHOO_FEED:
        yahoo_clear_cache(symbol)
        return jsonify({'success': True, 'cleared': symbol or 'all'})
    return jsonify({'success': True, 'message': 'No cache to clear'})


@bookmap_terminal_api.route('/terminal/instruments', methods=['GET'])
def get_available_instruments():
    """Get catalog of instruments available to add to watchlist."""
    query = request.args.get('q', '').upper()
    category = request.args.get('category', '')
    
    additional = _data_sources_config.get('additional_instruments', {})
    instruments = []
    
    for cat_name, cat_items in additional.items():
        if category and cat_name != category:
            continue
        if isinstance(cat_items, list):
            for item in cat_items:
                sym = item.get('symbol', '')
                name = item.get('name', sym)
                # Check if already in watchlist
                in_watchlist = any(w['symbol'] == sym for w in _watchlist)
                
                # Apply search filter
                if query and query not in sym.upper() and query not in name.upper():
                    continue
                
                instruments.append({
                    'symbol': sym,
                    'name': name,
                    'exchange': item.get('exchange', ''),
                    'category': cat_name,
                    'priceSeed': item.get('price_seed', 100.0),
                    'inWatchlist': in_watchlist,
                })
    
    return jsonify({
        'success': True,
        'instruments': instruments,
        'count': len(instruments),
        'categories': list(additional.keys()),
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# NEWS & MARKET ALERT ENDPOINTS
# ============================================================================

@bookmap_terminal_api.route('/alerts/status', methods=['GET'])
def get_alerts_status():
    """Get alert system status, channel readiness, and statistics."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    return jsonify({
        'success': True,
        'channels': _alert_svc.get_channels_status(),
        'stats': _alert_svc.get_alert_stats(),
        'globalEnabled': _alert_svc.get_config().get('global', {}).get('enabled', True),
        'timestamp': datetime.now().isoformat(),
    })


@bookmap_terminal_api.route('/alerts/history', methods=['GET'])
def get_alerts_history():
    """Get alert history with optional filters."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    limit = request.args.get('limit', 50, type=int)
    severity = request.args.get('severity', '')
    category = request.args.get('category', '')
    symbol = request.args.get('symbol', '')
    alerts = _alert_svc.get_alert_history(limit, severity, category, symbol)
    return jsonify({
        'success': True,
        'alerts': alerts,
        'count': len(alerts),
        'timestamp': datetime.now().isoformat(),
    })


@bookmap_terminal_api.route('/alerts/history/clear', methods=['POST'])
def clear_alerts_history():
    """Clear alert history."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    _alert_svc.clear_history()
    return jsonify({'success': True, 'message': 'Alert history cleared'})


@bookmap_terminal_api.route('/alerts/dispatch', methods=['POST'])
def dispatch_manual_alert():
    """Manually dispatch an alert to configured channels."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    data = request.get_json(force=True) or {}
    result = _alert_svc.dispatch_alert(
        alert_type=data.get('type', 'manual'),
        title=data.get('title', 'Manual Alert'),
        message=data.get('message', ''),
        severity=data.get('severity', 'MEDIUM'),
        symbol=data.get('symbol', ''),
        category=data.get('category', 'general'),
        data=data.get('data'),
        channels=data.get('channels'),
    )
    return jsonify({'success': True, 'alert': result})


@bookmap_terminal_api.route('/alerts/channels', methods=['GET'])
def get_alert_channels():
    """Get all channel configurations (credentials masked)."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    cfg = _alert_svc.get_config()
    channels = cfg.get('channels', {})
    # Mask sensitive fields
    masked = {}
    _sensitive = ('password', 'auth_token', 'bot_token', 'webhook_url',
                  'account_sid', 'Authorization')
    for ch_name, ch_cfg in channels.items():
        m = {}
        for k, v in ch_cfg.items():
            if k in _sensitive and isinstance(v, str) and v:
                m[k] = v[:4] + '•' * (len(v) - 8) + v[-4:] if len(v) > 8 else '••••'
            elif k == 'headers' and isinstance(v, dict):
                m[k] = {hk: (hv[:4] + '••••' if hk in _sensitive and hv else hv)
                        for hk, hv in v.items()}
            else:
                m[k] = v
        masked[ch_name] = m
    return jsonify({
        'success': True,
        'channels': masked,
        'status': _alert_svc.get_channels_status(),
    })


@bookmap_terminal_api.route('/alerts/channels/<channel_name>', methods=['PUT'])
def update_alert_channel(channel_name: str):
    """Update a specific channel's configuration."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    data = request.get_json(force=True) or {}
    ok = _alert_svc.update_channel_config(channel_name, data)
    return jsonify({'success': ok, 'channel': channel_name})


@bookmap_terminal_api.route('/alerts/channels/<channel_name>/test', methods=['POST'])
def test_alert_channel(channel_name: str):
    """Send a test alert to a specific channel."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    result = _alert_svc.test_channel(channel_name)
    return jsonify(result)


@bookmap_terminal_api.route('/alerts/price', methods=['GET'])
def get_price_alerts():
    """Get all configured price alerts."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    symbol = request.args.get('symbol', '')
    alerts = _alert_svc.get_price_alerts(symbol)
    return jsonify({'success': True, 'alerts': alerts, 'count': len(alerts)})


@bookmap_terminal_api.route('/alerts/price', methods=['POST'])
def add_price_alert_endpoint():
    """Add a new price target alert."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    data = request.get_json(force=True) or {}
    alert = _alert_svc.add_price_alert(
        symbol=data.get('symbol', ''),
        target_price=data.get('targetPrice', 0),
        direction=data.get('direction', 'above'),
        channels=data.get('channels'),
        note=data.get('note', ''),
    )
    return jsonify({'success': True, 'alert': alert})


@bookmap_terminal_api.route('/alerts/price/<alert_id>', methods=['DELETE'])
def delete_price_alert(alert_id: str):
    """Remove a price alert."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    ok = _alert_svc.remove_price_alert(alert_id)
    return jsonify({'success': ok, 'alertId': alert_id})


@bookmap_terminal_api.route('/alerts/rules', methods=['GET'])
def get_alert_rules_endpoint():
    """Get configured alert rules."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    rules = _alert_svc.get_alert_rules()
    return jsonify({'success': True, 'rules': rules})


@bookmap_terminal_api.route('/alerts/rules/<rule_name>', methods=['PUT'])
def update_alert_rule_endpoint(rule_name: str):
    """Update a specific alert rule."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    data = request.get_json(force=True) or {}
    ok = _alert_svc.update_alert_rule(rule_name, data)
    return jsonify({'success': ok, 'rule': rule_name})


@bookmap_terminal_api.route('/alerts/news/feed', methods=['GET'])
def get_news_feed():
    """Get simulated market news feed."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    limit = request.args.get('limit', 10, type=int)
    feed = _alert_svc.get_simulated_news_feed(limit)
    return jsonify({'success': True, 'news': feed, 'count': len(feed)})


@bookmap_terminal_api.route('/alerts/global/toggle', methods=['POST'])
def toggle_global_alerts():
    """Toggle global alert enabled/disabled."""
    if not _HAS_ALERT_SVC:
        return jsonify({'success': False, 'error': 'Alert service not available'}), 503
    data = request.get_json(force=True) or {}
    cfg = _alert_svc.get_config()
    if 'global' not in cfg:
        cfg['global'] = {}
    enabled = data.get('enabled', not cfg['global'].get('enabled', True))
    cfg['global']['enabled'] = enabled
    _alert_svc.save_config(cfg)
    return jsonify({'success': True, 'enabled': enabled})


# ============================================================================
# REGISTRATION
# ============================================================================

def register_bookmap_terminal_routes(app):
    """Register Bookmap & Terminal API routes with Flask app."""
    app.register_blueprint(bookmap_terminal_api)
    logger.info("Bookmap & Terminal API routes registered successfully")
    logger.info(f"Terminal config version: {_terminal_config.get('version', 'not loaded')}")
    logger.info(f"Bookmap config version: {_bookmap_config.get('version', 'not loaded')}")
    logger.info(f"Data sources config version: {_data_sources_config.get('version', 'not loaded')}")

