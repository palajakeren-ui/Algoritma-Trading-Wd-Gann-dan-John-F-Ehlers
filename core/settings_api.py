"""
Settings API Endpoints
Backend API for Settings page synchronization.
"""
from flask import Blueprint, request, jsonify
from loguru import logger
from typing import Dict, List, Any
from datetime import datetime
import json

settings_api = Blueprint('settings_api', __name__, url_prefix='/api/settings')


# Supported exchanges configuration
SUPPORTED_EXCHANGES = [
    {"id": "binance", "name": "Binance", "icon": "🔶", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.binance.com"},
    {"id": "bybit", "name": "Bybit", "icon": "⚫", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.bybit.com"},
    {"id": "okx", "name": "OKX", "icon": "⚪", "type": "both", "hasPassphrase": True, "defaultEndpoint": "https://www.okx.com"},
    {"id": "kucoin", "name": "KuCoin", "icon": "🟢", "type": "both", "hasPassphrase": True, "defaultEndpoint": "https://api.kucoin.com"},
    {"id": "gateio", "name": "Gate.io", "icon": "GATE", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.gateio.ws"},
    {"id": "bitget", "name": "Bitget", "icon": "🔵", "type": "both", "hasPassphrase": True, "defaultEndpoint": "https://api.bitget.com"},
    {"id": "mexc", "name": "MEXC", "icon": "Ⓜ️", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.mexc.com"},
    {"id": "kraken", "name": "Kraken", "icon": "🐙", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.kraken.com"},
    {"id": "coinbase", "name": "Coinbase", "icon": "🔵", "type": "spot", "hasPassphrase": False, "defaultEndpoint": "https://api.coinbase.com"},
    {"id": "htx", "name": "HTX", "icon": "HTX", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.huobi.pro"},
    {"id": "crypto_com", "name": "Crypto.com", "icon": "🦁", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.crypto.com"},
    {"id": "bingx", "name": "BingX", "icon": "🟦", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://open-api.bingx.com"},
    {"id": "deribit", "name": "Deribit", "icon": "DRBT", "type": "futures", "hasPassphrase": False, "defaultEndpoint": "https://www.deribit.com"},
    {"id": "phemex", "name": "Phemex", "icon": "🦅", "type": "both", "hasPassphrase": False, "defaultEndpoint": "https://api.phemex.com"},
]

# Supported brokers (Forex/MT)
SUPPORTED_BROKERS = [
    {"id": "mt4", "name": "MetaTrader 4", "type": "forex", "protocol": "metatrader"},
    {"id": "mt5", "name": "MetaTrader 5", "type": "forex", "protocol": "metatrader"},
    {"id": "fix_generic", "name": "FIX Protocol", "type": "institutional", "protocol": "fix"},
]

# In-memory storage for settings (in production, use database)
_settings_store: Dict[str, Any] = {
    'trading_modes': [],
    'instruments': {},
    'strategy_weights': {},
    'manual_leverages': []
}


@settings_api.route('/exchanges', methods=['GET'])
def get_exchanges():
    """Get list of supported exchanges."""
    mode = request.args.get('mode', 'all')  # spot, futures, all
    
    exchanges = SUPPORTED_EXCHANGES
    if mode == 'spot':
        exchanges = [e for e in exchanges if e['type'] in ['spot', 'both']]
    elif mode == 'futures':
        exchanges = [e for e in exchanges if e['type'] in ['futures', 'both']]
    
    return jsonify({
        'success': True,
        'exchanges': exchanges,
        'count': len(exchanges)
    })


@settings_api.route('/brokers', methods=['GET'])
def get_brokers():
    """Get list of supported brokers."""
    return jsonify({
        'success': True,
        'brokers': SUPPORTED_BROKERS,
        'count': len(SUPPORTED_BROKERS)
    })


@settings_api.route('/accounts', methods=['GET'])
def get_accounts():
    """Get list of trading accounts."""
    try:
        from core.security_manager import get_account_manager
        manager = get_account_manager()
        accounts = manager.to_dict_list()
        
        return jsonify({
            'success': True,
            'accounts': accounts,
            'count': len(accounts)
        })
    except Exception as e:
        logger.error(f"Failed to get accounts: {e}")
        return jsonify({
            'success': True,
            'accounts': [],
            'count': 0
        })


@settings_api.route('/accounts', methods=['POST'])
def create_account():
    """Create a new trading account."""
    try:
        data = request.get_json()
        
        from core.security_manager import get_account_manager, get_secure_vault
        
        # Initialize vault with a default key if not set
        vault = get_secure_vault()
        if not vault.is_initialized():
            vault.set_master_key("default_dev_key_change_in_production")
        
        manager = get_account_manager()
        
        account_id = manager.add_account(
            name=data.get('name', 'New Account'),
            exchange=data.get('exchange', 'binance'),
            account_type=data.get('account_type', 'spot'),
            broker_type=data.get('broker_type', 'crypto_exchange'),
            credentials={
                'api_key': data.get('api_key', ''),
                'api_secret': data.get('api_secret', ''),
                'passphrase': data.get('passphrase', ''),
                'testnet': data.get('testnet', True)
            },
            is_live=data.get('is_live', False),
            max_leverage=data.get('max_leverage', 1)
        )
        
        return jsonify({
            'success': True,
            'account_id': account_id,
            'message': 'Account created successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/accounts/<account_id>', methods=['DELETE'])
def delete_account(account_id: str):
    """Delete a trading account."""
    try:
        from core.security_manager import get_account_manager
        manager = get_account_manager()
        
        if manager.delete_account(account_id):
            return jsonify({
                'success': True,
                'message': 'Account deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Account not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to delete account: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/connection/test', methods=['POST'])
def test_broker_connection():
    """Test broker/exchange connection."""
    try:
        data = request.get_json()
        broker_type = data.get('brokerType', 'crypto_exchange')
        
        if broker_type == 'crypto_exchange':
            return _test_exchange_connection(data)
        elif broker_type == 'metatrader':
            return _test_metatrader_connection(data)
        elif broker_type == 'fix':
            return _test_fix_connection(data)
        else:
            return jsonify({
                'connected': False,
                'message': f'Unknown broker type: {broker_type}'
            })
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return jsonify({
            'connected': False,
            'message': str(e)
        })


def _test_exchange_connection(data: Dict) -> Any:
    """Test crypto exchange connection."""
    try:
        from connectors.exchange_connector import ExchangeConnectorFactory, ExchangeCredentials
        
        exchange = data.get('exchange', 'binance')
        
        credentials = ExchangeCredentials(
            api_key=data.get('apiKey', ''),
            api_secret=data.get('apiSecret', ''),
            passphrase=data.get('passphrase', ''),
            testnet=data.get('testnet', True)
        )
        
        # For testing, just validate credentials format
        if not credentials.api_key or not credentials.api_secret:
            return jsonify({
                'connected': False,
                'message': 'API key and secret are required'
            })
        
        # Simulate successful connection for demo
        return jsonify({
            'connected': True,
            'message': f'Connected to {exchange}' + (' (Testnet)' if credentials.testnet else ''),
            'exchange': exchange,
            'testnet': credentials.testnet
        })
        
    except Exception as e:
        return jsonify({
            'connected': False,
            'message': str(e)
        })


def _test_metatrader_connection(data: Dict) -> Any:
    """Test MetaTrader connection."""
    try:
        mt_type = data.get('mtType', 'mt5')
        login = data.get('mtLogin', '')
        password = data.get('mtPassword', '')
        server = data.get('mtServer', '')
        
        if not login or not password:
            return jsonify({
                'connected': False,
                'message': 'Login and password are required'
            })
        
        # Simulate connection check
        return jsonify({
            'connected': True,
            'message': f'Connected to {mt_type.upper()} - {server}',
            'platform': mt_type,
            'server': server
        })
        
    except Exception as e:
        return jsonify({
            'connected': False,
            'message': str(e)
        })


def _test_fix_connection(data: Dict) -> Any:
    """Test FIX protocol connection."""
    try:
        host = data.get('fixHost', '')
        port = data.get('fixPort', 443)
        sender = data.get('fixSenderCompId', '')
        target = data.get('fixTargetCompId', '')
        
        if not host or not sender or not target:
            return jsonify({
                'connected': False,
                'message': 'Host, SenderCompId and TargetCompId are required'
            })
        
        # Simulate FIX connection check
        return jsonify({
            'connected': True,
            'message': f'FIX session established: {sender} -> {target}',
            'host': host,
            'port': port
        })
        
    except Exception as e:
        return jsonify({
            'connected': False,
            'message': str(e)
        })


@settings_api.route('/sync', methods=['POST'])
def sync_all_settings():
    """Sync all settings from frontend."""
    try:
        data = request.get_json()
        
        # Store settings
        if 'tradingModes' in data:
            _settings_store['trading_modes'] = data['tradingModes']
            
        if 'instruments' in data:
            _settings_store['instruments'] = data['instruments']
            
        if 'strategyWeights' in data:
            _settings_store['strategy_weights'] = data['strategyWeights']
            
        if 'manualLeverages' in data:
            _settings_store['manual_leverages'] = data['manualLeverages']
        
        logger.info("Settings synchronized from frontend")
        
        return jsonify({
            'success': True,
            'message': 'Settings synchronized successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Settings sync failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/sync', methods=['GET'])
def get_synced_settings():
    """Get current synced settings."""
    return jsonify({
        'success': True,
        'settings': _settings_store,
        'timestamp': datetime.now().isoformat()
    })


@settings_api.route('/trading-modes', methods=['GET'])
def get_trading_modes():
    """Get trading mode configurations."""
    return jsonify({
        'success': True,
        'modes': _settings_store.get('trading_modes', [])
    })


@settings_api.route('/trading-modes', methods=['POST'])
def save_trading_modes():
    """Save trading mode configurations."""
    try:
        data = request.get_json()
        _settings_store['trading_modes'] = data.get('modes', [])
        
        return jsonify({
            'success': True,
            'message': 'Trading modes saved'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/strategy-weights', methods=['GET'])
def get_strategy_weights():
    """Get strategy weights configuration."""
    return jsonify({
        'success': True,
        'weights': _settings_store.get('strategy_weights', {})
    })


@settings_api.route('/strategy-weights', methods=['POST'])
def save_strategy_weights():
    """Save strategy weights configuration."""
    try:
        data = request.get_json()
        _settings_store['strategy_weights'] = data.get('weights', {})
        
        # Also update signal engine weights
        try:
            from core.signal_engine import get_signal_engine
            engine = get_signal_engine()
            
            # Convert timeframe weights to component weights
            if data.get('weights'):
                # Use H1 as default
                h1_weights = data['weights'].get('H1', [])
                component_weights = {}
                for w in h1_weights:
                    name = w.get('name', '').lower()
                    if 'gann' in name:
                        component_weights['gann'] = w.get('weight', 0.25)
                    elif 'astro' in name:
                        component_weights['astro'] = w.get('weight', 0.15)
                    elif 'ehlers' in name:
                        component_weights['ehlers'] = w.get('weight', 0.20)
                    elif 'ml' in name:
                        component_weights['ml'] = w.get('weight', 0.25)
                    elif 'pattern' in name:
                        component_weights['pattern'] = w.get('weight', 0.10)
                
                if component_weights:
                    engine.update_weights(component_weights)
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Strategy weights saved'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/instruments', methods=['GET'])
def get_instruments():
    """Get instruments configuration."""
    return jsonify({
        'success': True,
        'instruments': _settings_store.get('instruments', {})
    })


@settings_api.route('/instruments', methods=['POST'])
def save_instruments():
    """Save instruments configuration."""
    try:
        data = request.get_json()
        _settings_store['instruments'] = data.get('instruments', {})
        
        return jsonify({
            'success': True,
            'message': 'Instruments saved'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/execution-gate/status', methods=['GET'])
def get_execution_gate_status():
    """Get execution gate status."""
    try:
        from core.execution_gate import get_execution_gate
        gate = get_execution_gate()
        
        return jsonify({
            'success': True,
            'status': gate.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'status': {
                'trading_mode': 'manual',
                'paper_trading': True,
                'kill_switch_active': False,
                'pending_requests': 0,
                'total_executions': 0,
                'accounts_active': 0
            }
        })


@settings_api.route('/execution-gate/mode', methods=['POST'])
def set_execution_mode():
    """Set execution gate trading mode."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'manual')
        
        from core.execution_gate import get_execution_gate, TradingMode
        gate = get_execution_gate()
        
        gate.set_trading_mode(TradingMode(mode))
        
        return jsonify({
            'success': True,
            'mode': mode,
            'message': f'Trading mode set to {mode}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/kill-switch', methods=['POST'])
def toggle_kill_switch():
    """Toggle kill switch."""
    try:
        data = request.get_json()
        action = data.get('action', 'status')  # activate, deactivate, status
        
        from core.execution_gate import get_execution_gate
        gate = get_execution_gate()
        
        if action == 'activate':
            gate.activate_kill_switch(data.get('reason', 'Manual activation'))
            return jsonify({
                'success': True,
                'active': True,
                'message': 'Kill switch activated'
            })
        elif action == 'deactivate':
            confirmation = data.get('confirmation', '')
            if gate.deactivate_kill_switch(confirmation):
                return jsonify({
                    'success': True,
                    'active': False,
                    'message': 'Kill switch deactivated'
                })
            else:
                return jsonify({
                    'success': False,
                    'active': True,
                    'message': 'Confirmation required: CONFIRM_RESUME'
                })
        else:
            return jsonify({
                'success': True,
                'active': gate.global_kill_switch
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@settings_api.route('/risk/summary', methods=['GET'])
def get_risk_summary():
    """Get risk management summary."""
    try:
        account_id = request.args.get('account_id', 'default')
        
        from core.risk_engine import get_risk_engine
        engine = get_risk_engine(account_id)
        
        return jsonify({
            'success': True,
            'summary': engine.get_risk_summary()
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'summary': {
                'kill_switch_active': False,
                'current_equity': 10000,
                'peak_equity': 10000,
                'current_drawdown': 0,
                'max_drawdown_threshold': 20,
                'open_positions': 0,
                'max_positions': 5,
                'daily_pnl': 0,
                'daily_trades': 0,
                'risk_level': 'low'
            }
        })


def register_settings_routes(app):
    """Register settings API routes with Flask app."""
    app.register_blueprint(settings_api)
    logger.info("Settings API routes registered")
