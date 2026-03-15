"""
Configuration Synchronization API
Full synchronization between frontend Settings page and all YAML config files.
"""
from flask import Blueprint, request, jsonify
from loguru import logger
from typing import Dict, Any, Optional
from datetime import datetime
import yaml
import os

config_sync_api = Blueprint('config_sync_api', __name__, url_prefix='/api/config')

# Path to config folder
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')

# ============================================================================
# YAML FILE HANDLERS
# ============================================================================

def load_yaml_config(filename: str) -> Optional[Dict[str, Any]]:
    """Load a YAML configuration file."""
    try:
        filepath = os.path.join(CONFIG_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return None
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        return None


def save_yaml_config(filename: str, config: Dict[str, Any]) -> bool:
    """Save a configuration to YAML file."""
    try:
        filepath = os.path.join(CONFIG_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        logger.info(f"Configuration saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        return False


def merge_config(existing: Dict, updates: Dict) -> Dict:
    """Deep merge updates into existing config."""
    result = existing.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result


# ============================================================================
# ALL CONFIGS ENDPOINTS
# ============================================================================

@config_sync_api.route('/all', methods=['GET'])
def get_all_configs():
    """Get all configurations from YAML files."""
    try:
        configs = {}
        config_files = [
            'astro_config.yaml',
            'bookmap_config.yaml',
            'broker_config.yaml',
            'data_sources_config.yaml',
            'ehlers_config.yaml',
            'gann_config.yaml',
            'hft_config.yaml',
            'ml_config.yaml',
            'notifier.yaml',
            'risk_config.yaml',
            'scanner_config.yaml',
            'strategy_config.yaml',
            'options_config.yaml',
            'terminal_config.yaml',
        ]
        
        for filename in config_files:
            config_key = filename.replace('_config', '').replace('.yaml', '')
            config = load_yaml_config(filename)
            if config:
                configs[config_key] = config
        
        return jsonify({
            'success': True,
            'configs': configs,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get all configs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/sync-all', methods=['POST'])
def sync_all_configs():
    """Sync all configurations from frontend to YAML files."""
    try:
        data = request.get_json()
        results = {}
        
        # Sync Trading Modes to broker_config.yaml
        if 'tradingModes' in data:
            broker_config = load_yaml_config('broker_config.yaml') or {}
            broker_config['trading_modes'] = data['tradingModes']
            results['broker'] = save_yaml_config('broker_config.yaml', broker_config)
        
        # Sync Strategy Weights to strategy_config.yaml
        if 'strategyWeights' in data:
            strategy_config = load_yaml_config('strategy_config.yaml') or {}
            
            # Get weights from first timeframe (H1 as default)
            tf_weights = data['strategyWeights'].get('H1', [])
            ensemble_weights = {}
            for w in tf_weights:
                name = w.get('name', '').lower().replace(' ', '_')
                if 'gann' in name:
                    ensemble_weights['gann_geometry'] = w.get('weight', 0.25)
                elif 'astro' in name:
                    ensemble_weights['astro_cycles'] = w.get('weight', 0.15)
                elif 'ehlers' in name:
                    ensemble_weights['ehlers_dsp'] = w.get('weight', 0.20)
                elif 'ml' in name:
                    ensemble_weights['ml_models'] = w.get('weight', 0.25)
                elif 'pattern' in name:
                    ensemble_weights['pattern_recognition'] = w.get('weight', 0.10)
                elif 'option' in name:
                    ensemble_weights['options_flow'] = w.get('weight', 0.05)
            
            if ensemble_weights:
                if 'ensemble' not in strategy_config:
                    strategy_config['ensemble'] = {}
                strategy_config['ensemble']['weights'] = ensemble_weights
            
            # Store full timeframe weights
            strategy_config['timeframe_weights'] = data['strategyWeights']
            results['strategy'] = save_yaml_config('strategy_config.yaml', strategy_config)
        
        # Sync Risk Settings to risk_config.yaml - Support Both Dynamic and Fixed Modes
        if 'riskSettings' in data:
            risk_config = load_yaml_config('risk_config.yaml') or {}
            risk_settings = data['riskSettings']
            
            # Initialize nested structures
            if 'position_sizing' not in risk_config:
                risk_config['position_sizing'] = {}
            if 'risk_limits' not in risk_config:
                risk_config['risk_limits'] = {}
            if 'drawdown' not in risk_config:
                risk_config['drawdown'] = {}
            if 'stop_loss' not in risk_config:
                risk_config['stop_loss'] = {}
            if 'take_profit' not in risk_config:
                risk_config['take_profit'] = {}
            
            # === RISK TYPE (dynamic vs fixed) ===
            risk_type = risk_settings.get('riskType', 'dynamic')
            risk_config['position_sizing']['method'] = 'kelly_criterion' if risk_type == 'dynamic' else 'fixed_percent'
            
            # === DYNAMIC RISK SETTINGS ===
            if risk_type == 'dynamic':
                # Risk Per Trade (%)
                if 'riskPerTrade' in risk_settings:
                    risk_config['position_sizing']['fixed_percent'] = risk_config['position_sizing'].get('fixed_percent', {})
                    risk_config['position_sizing']['fixed_percent']['risk_per_trade'] = risk_settings['riskPerTrade'] / 100
                    risk_config['position_sizing']['fixed_percent']['enabled'] = True
                
                # Kelly Criterion
                if 'kellyFraction' in risk_settings:
                    risk_config['position_sizing']['kelly'] = risk_config['position_sizing'].get('kelly', {})
                    risk_config['position_sizing']['kelly']['active_fraction'] = risk_settings['kellyFraction']
                    risk_config['position_sizing']['kelly']['enabled'] = True
                
                # Adaptive Sizing (Volatility Adjustment)
                if 'adaptiveSizing' in risk_settings:
                    risk_config['position_sizing']['volatility_adjusted'] = risk_config['position_sizing'].get('volatility_adjusted', {})
                    risk_config['position_sizing']['volatility_adjusted']['enabled'] = risk_settings['adaptiveSizing']
                
                # Max Drawdown
                if 'maxDrawdown' in risk_settings:
                    risk_config['drawdown']['limits'] = risk_config['drawdown'].get('limits', {})
                    risk_config['drawdown']['limits']['max_level'] = risk_settings['maxDrawdown'] / 100
                
                # Daily Loss Limit
                if 'dailyLossLimit' in risk_settings:
                    risk_config['risk_limits']['daily'] = risk_config['risk_limits'].get('daily', {})
                    risk_config['risk_limits']['daily']['max_loss_percent'] = risk_settings['dailyLossLimit'] / 100
                
                # Weekly Loss Limit
                if 'weeklyLossLimit' in risk_settings:
                    risk_config['risk_limits']['weekly'] = risk_config['risk_limits'].get('weekly', {})
                    risk_config['risk_limits']['weekly']['max_loss_percent'] = risk_settings['weeklyLossLimit'] / 100
            
            # === FIXED RISK SETTINGS ===
            else:
                # Fixed Risk Per Trade ($ or %)
                if 'fixedRiskPerTrade' in risk_settings:
                    risk_config['position_sizing']['fixed_percent'] = risk_config['position_sizing'].get('fixed_percent', {})
                    risk_config['position_sizing']['fixed_percent']['risk_per_trade'] = risk_settings['fixedRiskPerTrade'] / 100
                    risk_config['position_sizing']['fixed_percent']['enabled'] = True
                
                # Fixed Lot Size
                if 'fixedLotSize' in risk_settings:
                    risk_config['position_sizing']['fixed_lot'] = {
                        'enabled': True,
                        'lot_size': risk_settings['fixedLotSize']
                    }
                
                # Risk:Reward Ratio
                if 'riskRewardRatio' in risk_settings:
                    risk_config['take_profit']['methods'] = risk_config['take_profit'].get('methods', {})
                    risk_config['take_profit']['methods']['fixed_rr'] = {
                        'enabled': True,
                        'ratio': risk_settings['riskRewardRatio']
                    }
                
                # Fixed Max Drawdown (Hard Stop Loss $)
                if 'fixedMaxDrawdown' in risk_settings:
                    risk_config['drawdown']['limits'] = risk_config['drawdown'].get('limits', {})
                    risk_config['drawdown']['limits']['max_level'] = risk_settings['fixedMaxDrawdown'] / 100
            
            # === COMMON SETTINGS (Both Modes) ===
            # Max Open Positions
            if 'maxOpenPositions' in risk_settings:
                risk_config['risk_limits']['positions'] = risk_config['risk_limits'].get('positions', {})
                risk_config['risk_limits']['positions']['max_open_positions'] = risk_settings['maxOpenPositions']
            
            # Trailing Stop
            if 'trailingStop' in risk_settings:
                risk_config['stop_loss']['trailing'] = risk_config['stop_loss'].get('trailing', {})
                risk_config['stop_loss']['trailing']['enabled'] = risk_settings['trailingStop']
                if 'trailingStopDistance' in risk_settings:
                    risk_config['stop_loss']['trailing']['methods'] = risk_config['stop_loss']['trailing'].get('methods', {})
                    risk_config['stop_loss']['trailing']['methods']['fixed'] = {
                        'enabled': True,
                        'distance_pips': risk_settings['trailingStopDistance']
                    }
            
            # Breakeven on Profit
            if 'breakEvenOnProfit' in risk_settings:
                risk_config['stop_loss']['adjustment'] = risk_config['stop_loss'].get('adjustment', {})
                risk_config['stop_loss']['adjustment']['breakeven'] = {
                    'enabled': risk_settings['breakEvenOnProfit']
                }
            
            # Drawdown Protection
            if 'drawdownProtection' in risk_settings:
                risk_config['drawdown']['recovery'] = risk_config['drawdown'].get('recovery', {})
                risk_config['drawdown']['recovery']['enabled'] = risk_settings['drawdownProtection']
            
            # Liquidation Alert (Futures)
            if 'liquidationAlert' in risk_settings:
                risk_config['account_protection'] = risk_config.get('account_protection', {})
                risk_config['account_protection']['liquidation_alert_percent'] = risk_settings['liquidationAlert']
            
            results['risk'] = save_yaml_config('risk_config.yaml', risk_config)
        
        # Sync Instruments to scanner_config.yaml
        if 'instruments' in data:
            scanner_config = load_yaml_config('scanner_config.yaml') or {}
            
            if 'universe' not in scanner_config:
                scanner_config['universe'] = {}
            if 'instruments' not in scanner_config['universe']:
                scanner_config['universe']['instruments'] = {}
            
            for category, instruments in data['instruments'].items():
                if isinstance(instruments, list):
                    # Extract enabled symbols
                    enabled_symbols = [i['symbol'] for i in instruments if i.get('enabled', True)]
                    scanner_config['universe']['instruments'][category] = enabled_symbols
            
            results['scanner'] = save_yaml_config('scanner_config.yaml', scanner_config)
        
        # Sync Manual Leverages to broker_config.yaml
        if 'manualLeverages' in data:
            broker_config = load_yaml_config('broker_config.yaml') or {}
            broker_config['manual_leverages'] = data['manualLeverages']
            results['broker_leverage'] = save_yaml_config('broker_config.yaml', broker_config)
        
        # Sync Notification Settings
        if 'notificationSettings' in data:
            notifier_config = load_yaml_config('notifier.yaml') or {}
            notif_settings = data['notificationSettings']
            
            if 'telegram' in notif_settings:
                notifier_config['telegram'] = merge_config(
                    notifier_config.get('telegram', {}),
                    notif_settings['telegram']
                )
            
            if 'email' in notif_settings:
                notifier_config['email'] = merge_config(
                    notifier_config.get('email', {}),
                    notif_settings['email']
                )
            
            if 'webhook' in notif_settings:
                notifier_config['webhook'] = merge_config(
                    notifier_config.get('webhook', {}),
                    notif_settings['webhook']
                )
            
            results['notifier'] = save_yaml_config('notifier.yaml', notifier_config)

        # Sync ML Config
        if 'mlConfig' in data:
            ml_config = load_yaml_config('ml_config.yaml') or {}
            frontend_ml = data['mlConfig']
            
            # Ensure structure exists
            if 'features' not in ml_config:
                ml_config['features'] = {}
            if 'feature_sets' not in ml_config['features']:
                ml_config['features']['feature_sets'] = {}
            if 'transformations' not in ml_config['features']:
                ml_config['features']['transformations'] = {}
            if 'selection' not in ml_config['features']:
                ml_config['features']['selection'] = {}

            # Update feature sets
            ml_config['features']['feature_sets']['technical'] = {
                'enabled': frontend_ml.get('technical', {}).get('enabled', True),
                'indicators': frontend_ml.get('technical', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['gann'] = {
                'enabled': frontend_ml.get('gann', {}).get('enabled', True),
                'features': frontend_ml.get('gann', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['ehlers'] = {
                'enabled': frontend_ml.get('ehlers', {}).get('enabled', True),
                'features': frontend_ml.get('ehlers', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['astro'] = {
                'enabled': frontend_ml.get('astro', {}).get('enabled', True),
                'features': frontend_ml.get('astro', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['microstructure'] = {
                'enabled': frontend_ml.get('microstructure', {}).get('enabled', True),
                'features': frontend_ml.get('microstructure', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['time'] = {
                'enabled': frontend_ml.get('time', {}).get('enabled', True),
                'features': frontend_ml.get('time', {}).get('features', [])
            }

            # Update transformations
            transforms = frontend_ml.get('transformations', {})
            ml_config['features']['transformations']['lags'] = {'enabled': transforms.get('lags', True), 'periods': [1, 2, 3, 5, 10, 20]}
            ml_config['features']['transformations']['rolling'] = {'enabled': transforms.get('rolling', True), 'windows': [5, 10, 20, 50]}
            ml_config['features']['transformations']['differences'] = {'enabled': transforms.get('differences', True), 'orders': [1, 2]}
            ml_config['features']['transformations']['ratios'] = {'enabled': transforms.get('ratios', False)}

            # Update selection
            selection = frontend_ml.get('selection', {})
            ml_config['features']['selection']['enabled'] = selection.get('enabled', True)
            ml_config['features']['selection']['methods'] = [selection.get('method', 'correlation')]
            ml_config['features']['selection']['top_k'] = selection.get('topK', 50)
            ml_config['features']['selection']['correlation_threshold'] = selection.get('correlationThreshold', 0.95)

            results['ml'] = save_yaml_config('ml_config.yaml', ml_config)
        
        return jsonify({
            'success': True,
            'message': 'All configurations synchronized',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to sync all configs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# INDIVIDUAL CONFIG ENDPOINTS
# ============================================================================

@config_sync_api.route('/gann', methods=['GET'])
def get_gann_config():
    """Get Gann configuration."""
    config = load_yaml_config('gann_config.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/gann', methods=['POST'])
def update_gann_config():
    """Update Gann configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('gann_config.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('gann_config.yaml', merged):
            return jsonify({'success': True, 'message': 'Gann config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/astro', methods=['GET'])
def get_astro_config():
    """Get Astro configuration."""
    config = load_yaml_config('astro_config.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/astro', methods=['POST'])
def update_astro_config():
    """Update Astro configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('astro_config.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('astro_config.yaml', merged):
            return jsonify({'success': True, 'message': 'Astro config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/ehlers', methods=['GET'])
def get_ehlers_config():
    """Get Ehlers DSP configuration."""
    config = load_yaml_config('ehlers_config.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/ehlers', methods=['POST'])
def update_ehlers_config():
    """Update Ehlers DSP configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('ehlers_config.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('ehlers_config.yaml', merged):
            return jsonify({'success': True, 'message': 'Ehlers config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/ml', methods=['GET'])
def get_ml_config():
    """Get Machine Learning configuration."""
    config = load_yaml_config('ml_config.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/ml', methods=['POST'])
def update_ml_config():
    """Update Machine Learning configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('ml_config.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('ml_config.yaml', merged):
            return jsonify({'success': True, 'message': 'ML config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# NOTE: /risk GET/POST routes are handled by api_sync.py Blueprint
# which resolves to the same /api/config/risk path with richer response formatting.
# Removed to avoid Flask duplicate route conflicts.


# NOTE: /scanner GET/POST routes are handled by api_sync.py Blueprint
# which resolves to the same /api/config/scanner path with richer response formatting.
# Removed to avoid Flask duplicate route conflicts.


@config_sync_api.route('/strategy', methods=['GET'])
def get_strategy_config():
    """Get Strategy configuration."""
    config = load_yaml_config('strategy_config.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/strategy', methods=['POST'])
def update_strategy_config():
    """Update Strategy configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('strategy_config.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('strategy_config.yaml', merged):
            return jsonify({'success': True, 'message': 'Strategy config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/broker', methods=['GET'])
def get_broker_config():
    """Get Broker configuration."""
    config = load_yaml_config('broker_config.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/broker', methods=['POST'])
def update_broker_config():
    """Update Broker configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('broker_config.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('broker_config.yaml', merged):
            return jsonify({'success': True, 'message': 'Broker config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/notifier', methods=['GET'])
def get_notifier_config():
    """Get Notifier configuration."""
    config = load_yaml_config('notifier.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/notifier', methods=['POST'])
def update_notifier_config():
    """Update Notifier configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('notifier.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('notifier.yaml', merged):
            return jsonify({'success': True, 'message': 'Notifier config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/options', methods=['GET'])
def get_options_config():
    """Get Options configuration."""
    config = load_yaml_config('options_config.yaml')
    return jsonify({
        'success': True,
        'config': config,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/options', methods=['POST'])
def update_options_config():
    """Update Options configuration."""
    try:
        data = request.get_json()
        existing = load_yaml_config('options_config.yaml') or {}
        merged = merge_config(existing, data)
        
        if save_yaml_config('options_config.yaml', merged):
            return jsonify({'success': True, 'message': 'Options config updated'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# FRONTEND-SPECIFIC SYNC ENDPOINTS
# ============================================================================

# NOTE: /trading-modes GET/POST routes are handled by api_sync.py Blueprint
# which resolves to the same /api/config/trading-modes path.
# Removed to avoid Flask duplicate route conflicts.


@config_sync_api.route('/strategy-weights', methods=['GET'])
def get_strategy_weights():
    """Get strategy weights for frontend."""
    strategy_config = load_yaml_config('strategy_config.yaml') or {}
    
    # Get timeframe-specific weights if available
    tf_weights = strategy_config.get('timeframe_weights', {})
    
    # Fallback to ensemble weights
    if not tf_weights:
        ensemble_weights = strategy_config.get('ensemble', {}).get('weights', {})
        
        # Convert backend weights to frontend format
        default_strategies = [
            {"name": "WD Gann Modul", "weight": ensemble_weights.get('gann_geometry', 0.25)},
            {"name": "Astro Cycles", "weight": ensemble_weights.get('astro_cycles', 0.15)},
            {"name": "Ehlers DSP", "weight": ensemble_weights.get('ehlers_dsp', 0.20)},
            {"name": "ML Models", "weight": ensemble_weights.get('ml_models', 0.25)},
            {"name": "Pattern Recognition", "weight": ensemble_weights.get('pattern_recognition', 0.10)},
            {"name": "Options Flow", "weight": ensemble_weights.get('options_flow', 0.05)},
        ]
        
        # Create for each timeframe
        timeframes = ['M1', 'M2', 'M3', 'M5', 'M10', 'M15', 'M30', 'M45', 
                      'H1', 'H2', 'H3', 'H4', 'D1', 'W1', 'MN', 'QMN', 'SMN', 'Y1']
        tf_weights = {tf: default_strategies.copy() for tf in timeframes}
    
    return jsonify({
        'success': True,
        'weights': tf_weights,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/strategy-weights', methods=['POST'])
def save_strategy_weights():
    """Save strategy weights from frontend."""
    try:
        data = request.get_json()
        weights = data.get('weights', {})
        
        strategy_config = load_yaml_config('strategy_config.yaml') or {}
        strategy_config['timeframe_weights'] = weights
        
        # Also update ensemble weights from H1
        h1_weights = weights.get('H1', [])
        ensemble_weights = {}
        for w in h1_weights:
            name = w.get('name', '').lower()
            if 'gann' in name:
                ensemble_weights['gann_geometry'] = w.get('weight', 0.25)
            elif 'astro' in name:
                ensemble_weights['astro_cycles'] = w.get('weight', 0.15)
            elif 'ehlers' in name:
                ensemble_weights['ehlers_dsp'] = w.get('weight', 0.20)
            elif 'ml' in name:
                ensemble_weights['ml_models'] = w.get('weight', 0.25)
            elif 'pattern' in name:
                ensemble_weights['pattern_recognition'] = w.get('weight', 0.10)
            elif 'option' in name:
                ensemble_weights['options_flow'] = w.get('weight', 0.05)
        
        if 'ensemble' not in strategy_config:
            strategy_config['ensemble'] = {}
        strategy_config['ensemble']['weights'] = ensemble_weights
        
        if save_yaml_config('strategy_config.yaml', strategy_config):
            return jsonify({'success': True, 'message': 'Strategy weights saved'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/instruments', methods=['GET'])
def get_instruments():
    """Get instruments configuration for frontend."""
    scanner_config = load_yaml_config('scanner_config.yaml') or {}
    instruments = scanner_config.get('universe', {}).get('instruments', {})
    
    # Convert to frontend format with enabled flag
    frontend_instruments = {}
    for category, symbols in instruments.items():
        if isinstance(symbols, list):
            frontend_instruments[category] = [
                {"symbol": s, "name": s, "enabled": True, "category": category}
                for s in symbols
            ]
        elif isinstance(symbols, dict):
            # Handle nested categories like forex.majors
            all_symbols = []
            for subcategory, subsymbols in symbols.items():
                if isinstance(subsymbols, list):
                    all_symbols.extend([
                        {"symbol": s, "name": s, "enabled": True, "category": subcategory}
                        for s in subsymbols
                    ])
            frontend_instruments[category] = all_symbols
    
    return jsonify({
        'success': True,
        'instruments': frontend_instruments,
        'timestamp': datetime.now().isoformat()
    })


@config_sync_api.route('/instruments', methods=['POST'])
def save_instruments():
    """Save instruments configuration from frontend."""
    try:
        data = request.get_json()
        instruments = data.get('instruments', {})
        
        scanner_config = load_yaml_config('scanner_config.yaml') or {}
        
        if 'universe' not in scanner_config:
            scanner_config['universe'] = {}
        
        # Convert frontend format to YAML format
        yaml_instruments = {}
        for category, inst_list in instruments.items():
            if isinstance(inst_list, list):
                yaml_instruments[category] = [
                    i['symbol'] for i in inst_list if i.get('enabled', True)
                ]
        
        scanner_config['universe']['instruments'] = yaml_instruments
        
        if save_yaml_config('scanner_config.yaml', scanner_config):
            return jsonify({'success': True, 'message': 'Instruments saved'})
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# NOTE: /leverage GET/POST routes are handled by api_sync.py Blueprint
# which resolves to the same /api/config/leverage path.
# Removed to avoid Flask duplicate route conflicts.


# ============================================================================
# SETTINGS PAGE COMPLETE SYNC
# ============================================================================

@config_sync_api.route('/settings/load', methods=['GET'])
def load_settings_for_frontend():
    """Load all settings formatted for frontend Settings page."""
    try:
        broker_config = load_yaml_config('broker_config.yaml') or {}
        strategy_config = load_yaml_config('strategy_config.yaml') or {}
        risk_config = load_yaml_config('risk_config.yaml') or {}
        scanner_config = load_yaml_config('scanner_config.yaml') or {}
        notifier_config = load_yaml_config('notifier.yaml') or {}
        
        # Build frontend-compatible settings object
        settings = {
            'tradingModes': broker_config.get('trading_modes', []),
            'manualLeverages': broker_config.get('manual_leverages', []),
            'strategyWeights': strategy_config.get('timeframe_weights', {}),
            'instruments': scanner_config.get('universe', {}).get('instruments', {}),
            'riskConfig': {
                'positionSizing': risk_config.get('position_sizing', {}),
                'stopLoss': risk_config.get('stop_loss', {}),
                'takeProfit': risk_config.get('take_profit', {}),
                'riskLimits': risk_config.get('risk_limits', {}),
                'drawdown': risk_config.get('drawdown', {}),
            },
            'notificationConfig': {
                'telegram': notifier_config.get('telegram', {}),
                'email': notifier_config.get('email', {}),
                'webhook': notifier_config.get('webhook', {}),
                'discord': notifier_config.get('discord', {}),
                'events': notifier_config.get('events', {}),
            },
            'scannerConfig': {
                'mode': scanner_config.get('scanner', {}).get('mode', 'continuous'),
                'frequency': scanner_config.get('scanner', {}).get('frequency', {}),
                'timeframes': scanner_config.get('timeframes', {}),
            },
            'mlConfig': {
                'technical': {
                    'enabled': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('technical', {}).get('enabled', True),
                    'features': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('technical', {}).get('indicators', [])
                },
                'gann': {
                    'enabled': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('gann', {}).get('enabled', True),
                    'features': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('gann', {}).get('features', [])
                },
                'ehlers': {
                    'enabled': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('ehlers', {}).get('enabled', True),
                    'features': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('ehlers', {}).get('features', [])
                },
                'astro': {
                    'enabled': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('astro', {}).get('enabled', True),
                    'features': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('astro', {}).get('features', [])
                },
                'microstructure': {
                    'enabled': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('microstructure', {}).get('enabled', True),
                    'features': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('microstructure', {}).get('features', [])
                },
                'time': {
                    'enabled': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('time', {}).get('enabled', True),
                    'features': load_yaml_config('ml_config.yaml').get('features', {}).get('feature_sets', {}).get('time', {}).get('features', [])
                },
                'transformations': {
                    'lags': load_yaml_config('ml_config.yaml').get('features', {}).get('transformations', {}).get('lags', {}).get('enabled', True),
                    'rolling': load_yaml_config('ml_config.yaml').get('features', {}).get('transformations', {}).get('rolling', {}).get('enabled', True),
                    'differences': load_yaml_config('ml_config.yaml').get('features', {}).get('transformations', {}).get('differences', {}).get('enabled', True),
                    'ratios': load_yaml_config('ml_config.yaml').get('features', {}).get('transformations', {}).get('ratios', {}).get('enabled', True)
                },
                'selection': {
                    'enabled': load_yaml_config('ml_config.yaml').get('features', {}).get('selection', {}).get('enabled', True),
                    'method': (load_yaml_config('ml_config.yaml').get('features', {}).get('selection', {}).get('methods', ['correlation']) or ['correlation'])[0],
                    'topK': load_yaml_config('ml_config.yaml').get('features', {}).get('selection', {}).get('top_k', 50),
                    'correlationThreshold': load_yaml_config('ml_config.yaml').get('features', {}).get('selection', {}).get('correlation_threshold', 0.95)
                }
            }
        }
        
        return jsonify({
            'success': True,
            'settings': settings,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@config_sync_api.route('/settings/save', methods=['POST'])
def save_settings_from_frontend():
    """Save all settings from frontend Settings page to YAML files."""
    try:
        data = request.get_json()
        results = {}
        
        # Save Trading Modes
        if 'tradingModes' in data:
            broker_config = load_yaml_config('broker_config.yaml') or {}
            broker_config['trading_modes'] = data['tradingModes']
            results['broker'] = save_yaml_config('broker_config.yaml', broker_config)
        
        # Save Manual Leverages
        if 'manualLeverages' in data:
            broker_config = load_yaml_config('broker_config.yaml') or {}
            broker_config['manual_leverages'] = data['manualLeverages']
            save_yaml_config('broker_config.yaml', broker_config)
        
        # Save Strategy Weights
        if 'strategyWeights' in data:
            strategy_config = load_yaml_config('strategy_config.yaml') or {}
            strategy_config['timeframe_weights'] = data['strategyWeights']
            results['strategy'] = save_yaml_config('strategy_config.yaml', strategy_config)
        
        # Save Instruments
        if 'instruments' in data:
            scanner_config = load_yaml_config('scanner_config.yaml') or {}
            if 'universe' not in scanner_config:
                scanner_config['universe'] = {}
            scanner_config['universe']['instruments'] = data['instruments']
            results['scanner'] = save_yaml_config('scanner_config.yaml', scanner_config)

        # Save ML Config
        if 'mlConfig' in data:
            ml_config = load_yaml_config('ml_config.yaml') or {}
            frontend_ml = data['mlConfig']
            
            # Ensure structure exists
            if 'features' not in ml_config:
                ml_config['features'] = {}
            if 'feature_sets' not in ml_config['features']:
                ml_config['features']['feature_sets'] = {}
            if 'transformations' not in ml_config['features']:
                ml_config['features']['transformations'] = {}
            if 'selection' not in ml_config['features']:
                ml_config['features']['selection'] = {}

            # Update feature sets
            ml_config['features']['feature_sets']['technical'] = {
                'enabled': frontend_ml.get('technical', {}).get('enabled', True),
                'indicators': frontend_ml.get('technical', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['gann'] = {
                'enabled': frontend_ml.get('gann', {}).get('enabled', True),
                'features': frontend_ml.get('gann', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['ehlers'] = {
                'enabled': frontend_ml.get('ehlers', {}).get('enabled', True),
                'features': frontend_ml.get('ehlers', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['astro'] = {
                'enabled': frontend_ml.get('astro', {}).get('enabled', True),
                'features': frontend_ml.get('astro', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['microstructure'] = {
                'enabled': frontend_ml.get('microstructure', {}).get('enabled', True),
                'features': frontend_ml.get('microstructure', {}).get('features', [])
            }
            ml_config['features']['feature_sets']['time'] = {
                'enabled': frontend_ml.get('time', {}).get('enabled', True),
                'features': frontend_ml.get('time', {}).get('features', [])
            }

            # Update transformations
            transforms = frontend_ml.get('transformations', {})
            ml_config['features']['transformations']['lags'] = {'enabled': transforms.get('lags', True), 'periods': [1, 2, 3, 5, 10, 20]}
            ml_config['features']['transformations']['rolling'] = {'enabled': transforms.get('rolling', True), 'windows': [5, 10, 20, 50]}
            ml_config['features']['transformations']['differences'] = {'enabled': transforms.get('differences', True), 'orders': [1, 2]}
            ml_config['features']['transformations']['ratios'] = {'enabled': transforms.get('ratios', False)}

            # Update selection
            selection = frontend_ml.get('selection', {})
            ml_config['features']['selection']['enabled'] = selection.get('enabled', True)
            ml_config['features']['selection']['methods'] = [selection.get('method', 'correlation')]
            ml_config['features']['selection']['top_k'] = selection.get('topK', 50)
            ml_config['features']['selection']['correlation_threshold'] = selection.get('correlationThreshold', 0.95)

            results['ml'] = save_yaml_config('ml_config.yaml', ml_config)
        
        return jsonify({
            'success': True,
            'message': 'All settings saved to config files',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# REGISTRATION
# ============================================================================

def register_config_sync_routes(app):
    """Register config sync API routes with Flask app."""
    app.register_blueprint(config_sync_api)
    logger.info("Config Sync API routes registered")
