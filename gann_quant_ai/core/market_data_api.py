"""
Market Data API Endpoints
Real-time and historical market data from MT4/MT5, FIX, and exchanges.
"""
from flask import Blueprint, request, jsonify
from loguru import logger
from typing import Dict, List, Any
from datetime import datetime
import asyncio
import json

market_data_api = Blueprint('market_data_api', __name__, url_prefix='/api/market')

# Global data feed instance
_data_feed = None


def get_data_feed():
    """Get or create data feed instance."""
    global _data_feed
    if _data_feed is None:
        from core.realtime_data_feed import RealTimeDataFeed
        _data_feed = RealTimeDataFeed()
    return _data_feed


@market_data_api.route('/sources', methods=['GET'])
def get_data_sources():
    """Get available data sources."""
    feed = get_data_feed()
    sources = feed.get_data_sources()
    
    return jsonify({
        'success': True,
        'sources': sources,
        'primary': feed.primary_source.value,
        'subscribed_symbols': feed.get_subscribed_symbols()
    })


@market_data_api.route('/sources/primary', methods=['POST'])
def set_primary_source():
    """Set primary data source."""
    try:
        data = request.get_json()
        source = data.get('source', 'crypto_exchange')
        
        from core.realtime_data_feed import DataSource
        feed = get_data_feed()
        feed.set_primary_source(DataSource(source))
        
        return jsonify({
            'success': True,
            'primary': source
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/subscribe', methods=['POST'])
def subscribe_symbols():
    """Subscribe to real-time data for symbols."""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
        
        feed = get_data_feed()
        feed.start()
        
        # Run async subscription
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(feed.subscribe_ticks(symbols))
        loop.close()
        
        return jsonify({
            'success': True,
            'subscribed': symbols,
            'message': f'Subscribed to {len(symbols)} symbols'
        })
        
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/unsubscribe', methods=['POST'])
def unsubscribe_symbols():
    """Unsubscribe from symbols."""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        feed = get_data_feed()
        # Remove from queues
        for symbol in symbols:
            if symbol in feed._tick_queues:
                del feed._tick_queues[symbol]
        
        return jsonify({
            'success': True,
            'unsubscribed': symbols
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/tick/<symbol>', methods=['GET'])
def get_tick(symbol: str):
    """Get latest tick for a symbol."""
    feed = get_data_feed()
    tick = feed.get_latest_tick(symbol)
    
    if tick:
        return jsonify({
            'success': True,
            'tick': {
                'symbol': tick.symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'spread': tick.spread,
                'volume': tick.volume,
                'timestamp': tick.timestamp.isoformat(),
                'source': tick.source.value
            }
        })
    else:
        return jsonify({
            'success': True,
            'tick': None,
            'message': 'No tick data available'
        })


@market_data_api.route('/price/<symbol>', methods=['GET'])
def get_price(symbol: str):
    """Get current price for a symbol."""
    try:
        feed = get_data_feed()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        price = loop.run_until_complete(feed.get_current_price(symbol))
        loop.close()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'price': price,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/ohlcv/<symbol>', methods=['GET'])
def get_ohlcv(symbol: str):
    """Get historical OHLCV data."""
    try:
        timeframe = request.args.get('timeframe', '1h')
        limit = int(request.args.get('limit', 100))
        source = request.args.get('source', None)
        
        feed = get_data_feed()
        
        from core.realtime_data_feed import DataSource
        data_source = DataSource(source) if source else None
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        df = loop.run_until_complete(
            feed.get_historical_data(symbol, timeframe, limit, data_source)
        )
        loop.close()
        
        if df is not None and len(df) > 0:
            # Convert to list of dicts
            df_reset = df.reset_index()
            df_reset['timestamp'] = df_reset['timestamp'].astype(str) if 'timestamp' in df_reset.columns else df_reset.index.astype(str)
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'timeframe': timeframe,
                'count': len(df),
                'data': df_reset.to_dict(orient='records')
            })
        else:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'timeframe': timeframe,
                'count': 0,
                'data': []
            })
            
    except Exception as e:
        logger.error(f"OHLCV error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/orderbook/<symbol>', methods=['GET'])
def get_orderbook(symbol: str):
    """Get order book for a symbol."""
    try:
        limit = int(request.args.get('limit', 20))
        
        feed = get_data_feed()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        orderbook = loop.run_until_complete(feed.get_orderbook(symbol, limit))
        loop.close()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'orderbook': orderbook
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/connector/mt', methods=['POST'])
def configure_mt_connector():
    """Configure MetaTrader connector for data feed."""
    try:
        data = request.get_json()
        
        from connectors.metatrader_connector import (
            MetaTraderConnector, MTCredentials, MTVersion
        )
        
        version = MTVersion.MT5 if data.get('version', 'mt5').lower() == 'mt5' else MTVersion.MT4
        
        credentials = MTCredentials(
            login=data.get('login', ''),
            password=data.get('password', ''),
            server=data.get('server', ''),
            version=version,
            account_type=data.get('account_type', 'demo'),
            broker=data.get('broker', '')
        )
        
        connector = MetaTraderConnector(credentials)
        
        # Connect
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connected = loop.run_until_complete(connector.connect())
        loop.close()
        
        if connected:
            feed = get_data_feed()
            feed.set_metatrader_connector(connector)
            
            return jsonify({
                'success': True,
                'connected': True,
                'message': f'MetaTrader {version.value.upper()} connected',
                'account_info': {
                    'login': connector.account_info.login,
                    'balance': connector.account_info.balance,
                    'equity': connector.account_info.equity,
                    'leverage': connector.account_info.leverage,
                    'currency': connector.account_info.currency
                }
            })
        else:
            return jsonify({
                'success': False,
                'connected': False,
                'error': 'Failed to connect to MetaTrader'
            })
            
    except Exception as e:
        logger.error(f"MT connector error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/connector/fix', methods=['POST'])
def configure_fix_connector():
    """Configure FIX protocol connector for data feed."""
    try:
        data = request.get_json()
        
        from connectors.fix_connector import FIXConnector, FIXCredentials, FIXVersion
        
        version = FIXVersion.FIX44
        if data.get('version') == 'FIX.4.2':
            version = FIXVersion.FIX42
        elif data.get('version') == 'FIXT.1.1':
            version = FIXVersion.FIX50
        
        credentials = FIXCredentials(
            host=data.get('host', ''),
            port=int(data.get('port', 443)),
            sender_comp_id=data.get('sender_comp_id', ''),
            target_comp_id=data.get('target_comp_id', ''),
            username=data.get('username', ''),
            password=data.get('password', ''),
            heartbeat_interval=int(data.get('heartbeat_interval', 30)),
            ssl_enabled=data.get('ssl_enabled', True),
            fix_version=version
        )
        
        connector = FIXConnector(credentials)
        
        # Connect
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connected = loop.run_until_complete(connector.connect())
        loop.close()
        
        if connected:
            feed = get_data_feed()
            feed.set_fix_connector(connector)
            
            return jsonify({
                'success': True,
                'connected': True,
                'message': f'FIX session established: {credentials.sender_comp_id} -> {credentials.target_comp_id}'
            })
        else:
            return jsonify({
                'success': False,
                'connected': False,
                'error': 'Failed to establish FIX session'
            })
            
    except Exception as e:
        logger.error(f"FIX connector error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/connector/exchange', methods=['POST'])
def configure_exchange_connector():
    """Configure crypto exchange connector for data feed."""
    try:
        data = request.get_json()
        
        from connectors.exchange_connector import (
            ExchangeConnectorFactory, ExchangeCredentials
        )
        
        exchange = data.get('exchange', 'binance')
        
        credentials = ExchangeCredentials(
            api_key=data.get('api_key', ''),
            api_secret=data.get('api_secret', ''),
            passphrase=data.get('passphrase', ''),
            testnet=data.get('testnet', True)
        )
        
        connector = ExchangeConnectorFactory.create(
            exchange_id=exchange,
            credentials=credentials,
            mode=data.get('mode', 'spot')
        )
        
        # Connect
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connected = loop.run_until_complete(connector.connect())
        loop.close()
        
        if connected:
            feed = get_data_feed()
            feed.add_exchange_connector(exchange, connector)
            
            return jsonify({
                'success': True,
                'connected': True,
                'message': f'Connected to {exchange}',
                'exchange': exchange,
                'mode': data.get('mode', 'spot')
            })
        else:
            return jsonify({
                'success': False,
                'connected': False,
                'error': f'Failed to connect to {exchange}'
            })
            
    except Exception as e:
        logger.error(f"Exchange connector error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@market_data_api.route('/stream/start', methods=['POST'])
def start_stream():
    """Start data streaming."""
    feed = get_data_feed()
    feed.start()
    
    return jsonify({
        'success': True,
        'streaming': True,
        'message': 'Data streaming started'
    })


@market_data_api.route('/stream/stop', methods=['POST'])
def stop_stream():
    """Stop data streaming."""
    feed = get_data_feed()
    feed.stop()
    
    return jsonify({
        'success': True,
        'streaming': False,
        'message': 'Data streaming stopped'
    })


@market_data_api.route('/stream/status', methods=['GET'])
def stream_status():
    """Get streaming status."""
    feed = get_data_feed()
    
    return jsonify({
        'success': True,
        'running': feed._running,
        'sources': feed.get_data_sources(),
        'primary': feed.primary_source.value,
        'subscribed_symbols': feed.get_subscribed_symbols(),
        'active_streams': len(feed._stream_threads)
    })


def register_market_data_routes(app):
    """Register market data API routes with Flask app."""
    app.register_blueprint(market_data_api)
    logger.info("Market Data API routes registered")
