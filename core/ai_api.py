"""
AI Engine API Endpoints
Complete backend API for AI/ML functionality.

These endpoints provide access to:
- Feature Fusion Engine
- Training Pipeline
- Multiple ML Models
- Gann Analysis
- Ehlers DSP
- Astrology/Synodic Cycles
"""
from flask import Blueprint, request, jsonify
from loguru import logger
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

# Create Blueprint
ai_api = Blueprint('ai_api', __name__, url_prefix='/api/ai')


def get_ai_engines():
    """Get or initialize AI engines."""
    from core.feature_fusion_engine import FeatureFusionEngine
    from core.training_pipeline import TrainingPipeline, PredictionService
    
    return {
        'feature_fusion': FeatureFusionEngine(),
        'training_pipeline': TrainingPipeline(),
        'prediction_service': PredictionService()
    }


# =============================================================================
# TRAINING ENDPOINTS
# =============================================================================

@ai_api.route('/train', methods=['POST'])
def train_models():
    """
    Train ML models on provided data.
    
    Request body:
    {
        "symbol": "BTC-USD",
        "timeframe": "1d",
        "start_date": "2022-01-01",
        "end_date": "2024-01-01",
        "models": ["lightgbm", "xgboost", "mlp"],  // optional, default all
        "config": {}  // optional training config
    }
    """
    try:
        data = request.get_json() or {}
        
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        start_date = data.get('start_date', '2022-01-01')
        end_date = data.get('end_date')
        models_to_train = data.get('models')
        config = data.get('config', {})
        
        logger.info(f"Training request: {symbol} {timeframe}")
        
        # Get price data
        from core.data_feed import DataFeed
        data_feed = DataFeed({})
        price_data = data_feed.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if price_data is None or price_data.empty:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch price data'
            }), 400
        
        # Build features
        from core.feature_fusion_engine import FeatureFusionEngine
        fusion_engine = FeatureFusionEngine(config)
        
        # Get Gann levels
        from core.gann_engine import GannEngine
        gann_engine = GannEngine({'square_of_9': {'levels_to_generate': 5}})
        gann_data = gann_engine.calculate_sq9_levels(price_data)
        
        # Get Ehlers indicators
        from core.ehlers_engine import EhlersEngine
        ehlers_engine = EhlersEngine({
            'fisher_transform': {'period': 10},
            'mama': {'fast_limit': 0.5, 'slow_limit': 0.05}
        })
        ehlers_data = ehlers_engine.calculate_all_indicators(price_data)
        
        # Build fused features
        features = fusion_engine.build_features(
            price_data,
            gann_data=gann_data,
            ehlers_data=ehlers_data
        )
        
        # Train models
        from core.training_pipeline import TrainingPipeline
        pipeline = TrainingPipeline(config)
        data_splits = pipeline.prepare_data(features)
        results = pipeline.train_all_models(data_splits, models_to_train)
        
        # Save pipeline
        pipeline.save_pipeline()
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'timeframe': timeframe,
            'n_samples': len(features),
            'n_features': len(features.columns) - 1,
            'training_results': results,
            'best_model': pipeline.best_model_name,
            'pipeline_summary': pipeline.get_pipeline_summary()
        })
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_api.route('/predict', methods=['POST'])
def predict():
    """
    Generate predictions for current market data.
    
    Request body:
    {
        "symbol": "BTC-USD",
        "timeframe": "1d",
        "use_ensemble": true,
        "model": "lightgbm"  // optional, specific model
    }
    """
    try:
        data = request.get_json() or {}
        
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        use_ensemble = data.get('use_ensemble', True)
        model_name = data.get('model')
        
        logger.info(f"Prediction request: {symbol} {timeframe}")
        
        # Load pipeline
        from core.training_pipeline import TrainingPipeline, PredictionService
        pipeline = TrainingPipeline()
        
        if not pipeline.load_pipeline():
            return jsonify({
                'status': 'error',
                'message': 'No trained pipeline found. Please train first.'
            }), 400
        
        # Get recent price data
        from core.data_feed import DataFeed
        data_feed = DataFeed({})
        price_data = data_feed.get_historical_data(symbol, timeframe, limit=200)
        
        if price_data is None or price_data.empty:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch price data'
            }), 400
        
        # Build features
        from core.feature_fusion_engine import FeatureFusionEngine
        fusion_engine = FeatureFusionEngine()
        features = fusion_engine.build_features(price_data)
        
        # Remove target for prediction
        X = features.drop('target', axis=1, errors='ignore')
        
        # Generate predictions
        prediction_service = PredictionService(pipeline)
        result = prediction_service.predict(X, use_ensemble=use_ensemble)
        
        # Add current price info
        current_price = float(price_data['close'].iloc[-1])
        result['current_price'] = current_price
        result['symbol'] = symbol
        result['timeframe'] = timeframe
        
        # Get latest signal
        if result['status'] == 'success' and result['signals']:
            latest_signal = result['signals'][-1]
            result['latest_signal'] = latest_signal
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@ai_api.route('/pipeline/status', methods=['GET'])
def pipeline_status():
    """Get current training pipeline status."""
    try:
        from core.training_pipeline import TrainingPipeline
        pipeline = TrainingPipeline()
        
        if pipeline.load_pipeline():
            return jsonify({
                'status': 'success',
                'pipeline_loaded': True,
                'summary': pipeline.get_pipeline_summary()
            })
        else:
            return jsonify({
                'status': 'success',
                'pipeline_loaded': False,
                'message': 'No trained pipeline found'
            })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# FEATURE FUSION ENDPOINTS
# =============================================================================

@ai_api.route('/features/build', methods=['POST'])
def build_features():
    """
    Build fused ML features from price data.
    
    Request body:
    {
        "symbol": "BTC-USD",
        "timeframe": "1d",
        "limit": 200
    }
    """
    try:
        data = request.get_json() or {}
        
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        limit = data.get('limit', 200)
        
        # Get price data
        from core.data_feed import DataFeed
        data_feed = DataFeed({})
        price_data = data_feed.get_historical_data(symbol, timeframe, limit=limit)
        
        if price_data is None or price_data.empty:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch price data'
            }), 400
        
        # Build features
        from core.feature_fusion_engine import FeatureFusionEngine
        fusion_engine = FeatureFusionEngine()
        features = fusion_engine.build_features(price_data)
        
        # Get feature names and stats
        feature_names = fusion_engine.get_feature_names()
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'timeframe': timeframe,
            'n_samples': len(features),
            'n_features': len(feature_names),
            'feature_names': feature_names,
            'latest_features': features.iloc[-1].to_dict() if len(features) > 0 else {}
        })
        
    except Exception as e:
        logger.error(f"Feature build error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# GANN ANALYSIS ENDPOINTS
# =============================================================================

@ai_api.route('/gann/square-of-9', methods=['POST'])
def gann_sq9():
    """Calculate Gann Square of 9 levels."""
    try:
        data = request.get_json() or {}
        price = float(data.get('price', 0))
        n_levels = int(data.get('n_levels', 5))
        
        if price <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Price must be positive'
            }), 400
        
        from modules.gann.square_of_9 import SquareOf9
        sq9 = SquareOf9(price)
        levels = sq9.get_levels(n_levels)
        
        return jsonify({
            'status': 'success',
            'initial_price': price,
            'support': levels['support'],
            'resistance': levels['resistance']
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ai_api.route('/gann/square-of-24', methods=['POST'])
def gann_sq24():
    """Calculate Gann Square of 24 levels."""
    try:
        data = request.get_json() or {}
        price = float(data.get('price', 0))
        n_levels = int(data.get('n_levels', 5))
        
        if price <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Price must be positive'
            }), 400
        
        from modules.gann.square_of_24 import SquareOf24
        sq24 = SquareOf24(price)
        levels = sq24.get_levels(n_levels)
        time_harmonics = sq24.get_time_harmonics()
        price_angles = sq24.get_price_angles()
        
        return jsonify({
            'status': 'success',
            'initial_price': price,
            'support': levels['support'],
            'resistance': levels['resistance'],
            'time_harmonics': time_harmonics,
            'price_angles': price_angles[:10]  # First 10 angles
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ai_api.route('/gann/time-price-geometry', methods=['POST'])
def gann_geometry():
    """Calculate Gann Time-Price Geometry."""
    try:
        data = request.get_json() or {}
        pivot_price = float(data.get('pivot_price', 0))
        current_price = float(data.get('current_price', 0))
        pivot_time = int(data.get('pivot_time', 0))
        current_time = int(data.get('current_time', 100))
        
        if pivot_price <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Pivot price must be positive'
            }), 400
        
        from modules.gann.time_price_geometry import TimePriceGeometry
        tpg = TimePriceGeometry()
        
        # Calculate support/resistance from angles
        if current_price > 0:
            sr_levels = tpg.find_support_resistance(
                current_price, pivot_price, pivot_time, current_time
            )
        else:
            sr_levels = {'support': [], 'resistance': []}
        
        # Calculate time targets
        time_targets = tpg.calculate_time_targets(datetime.now(), n_cycles=10)
        
        # Price squares
        price_squares = tpg.get_price_squares(pivot_price, n_squares=8)
        
        # Vibration levels
        high = max(pivot_price * 1.1, current_price * 1.05) if current_price > 0 else pivot_price * 1.1
        low = min(pivot_price * 0.9, current_price * 0.95) if current_price > 0 else pivot_price * 0.9
        vibration_levels = tpg.calculate_vibration_levels(high, low)
        
        return jsonify({
            'status': 'success',
            'pivot_price': pivot_price,
            'current_price': current_price,
            'support_levels': sr_levels['support'][:5],
            'resistance_levels': sr_levels['resistance'][:5],
            'time_targets': [
                {'days': t['days'], 'date': t['date_str'], 'significance': t['significance']}
                for t in time_targets
            ],
            'price_squares': price_squares,
            'vibration_levels': vibration_levels
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =============================================================================
# EHLERS DSP ENDPOINTS
# =============================================================================

@ai_api.route('/ehlers/analyze', methods=['POST'])
def ehlers_full_analysis():
    """
    Complete Ehlers DSP analysis.
    
    Request body:
    {
        "symbol": "BTC-USD",
        "timeframe": "1d",
        "indicators": ["all"] or ["fisher", "mama", "bandpass", ...]
    }
    """
    try:
        data = request.get_json() or {}
        
        symbol = data.get('symbol', 'BTC-USD')
        timeframe = data.get('timeframe', '1d')
        indicators = data.get('indicators', ['all'])
        
        # Get price data
        from core.data_feed import DataFeed
        data_feed = DataFeed({})
        price_data = data_feed.get_historical_data(symbol, timeframe, limit=200)
        
        if price_data is None or price_data.empty:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch price data'
            }), 400
        
        results = {}
        
        # Fisher Transform
        if 'all' in indicators or 'fisher' in indicators:
            from modules.ehlers.fisher_transform import fisher_transform
            fisher = fisher_transform(price_data, period=10)
            results['fisher'] = {
                'current': float(fisher['fisher'].iloc[-1]),
                'signal': float(fisher['fisher_signal'].iloc[-1]),
                'direction': 'bullish' if fisher['fisher'].iloc[-1] > fisher['fisher_signal'].iloc[-1] else 'bearish'
            }
        
        # MAMA/FAMA
        if 'all' in indicators or 'mama' in indicators:
            from modules.ehlers.mama import mama
            mama_result = mama(price_data)
            results['mama'] = {
                'mama': float(mama_result['mama'].iloc[-1]),
                'fama': float(mama_result['fama'].iloc[-1]),
                'direction': 'bullish' if mama_result['mama'].iloc[-1] > mama_result['fama'].iloc[-1] else 'bearish'
            }
        
        # Bandpass Filter
        if 'all' in indicators or 'bandpass' in indicators:
            from modules.ehlers.bandpass_filter import bandpass_filter
            bp = bandpass_filter(price_data, period=20)
            results['bandpass'] = {
                'value': float(bp['bandpass'].iloc[-1]),
                'signal': int(bp['bp_signal'].iloc[-1])
            }
        
        # Smoothed RSI
        if 'all' in indicators or 'smoothed_rsi' in indicators:
            from modules.ehlers.smoothed_rsi import smoothed_rsi
            srsi = smoothed_rsi(price_data)
            results['smoothed_rsi'] = {
                'value': float(srsi['smoothed_rsi'].iloc[-1]),
                'overbought': bool(srsi['rsi_overbought'].iloc[-1]),
                'oversold': bool(srsi['rsi_oversold'].iloc[-1])
            }
        
        # Instantaneous Trendline
        if 'all' in indicators or 'itrend' in indicators:
            from modules.ehlers.instantaneous_trendline import instantaneous_trendline
            itrend = instantaneous_trendline(price_data)
            results['itrend'] = {
                'value': float(itrend['itrend'].iloc[-1]),
                'trigger': float(itrend['itrend_trigger'].iloc[-1]),
                'bullish': bool(itrend['itrend_bullish'].iloc[-1])
            }
        
        # Hilbert Transform
        if 'all' in indicators or 'hilbert' in indicators:
            from modules.ehlers.hilbert_transform import hilbert_transform
            ht = hilbert_transform(price_data)
            results['hilbert'] = {
                'period': float(ht['hilbert_period'].iloc[-1]),
                'phase': float(ht['hilbert_phase'].iloc[-1])
            }
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'timeframe': timeframe,
            'current_price': float(price_data['close'].iloc[-1]),
            'indicators': results
        })
        
    except Exception as e:
        logger.error(f"Ehlers analysis error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =============================================================================
# ASTROLOGY/SYNODIC ENDPOINTS
# =============================================================================

@ai_api.route('/astro/synodic-cycles', methods=['GET'])
def synodic_cycles():
    """Get current synodic cycle analysis."""
    try:
        from modules.astro.synodic_cycles import SynodicCycleCalculator
        calc = SynodicCycleCalculator()
        
        # Current phases
        phases = calc.get_current_cycle_phases()
        
        # Time harmonics
        harmonics = calc.get_time_harmonics(datetime.now(), n_projections=15)
        
        # Time clusters (next 90 days)
        clusters = calc.calculate_time_clusters(datetime.now(), days_forward=90)
        top_clusters = clusters[clusters['is_cluster']].nlargest(10, 'convergence_score')
        
        return jsonify({
            'status': 'success',
            'current_phases': phases,
            'time_harmonics': [
                {'date': h['date_str'], 'days': h['days'], 'significance': h['significance']}
                for h in harmonics
            ],
            'time_clusters': [
                {'date': row['date'].strftime('%Y-%m-%d'), 'score': float(row['normalized_score'])}
                for _, row in top_clusters.iterrows()
            ]
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ai_api.route('/astro/time-harmonics', methods=['POST'])
def time_harmonics():
    """Calculate time harmonics from a pivot date."""
    try:
        data = request.get_json() or {}
        pivot_date_str = data.get('pivot_date')
        
        if pivot_date_str:
            pivot_date = datetime.fromisoformat(pivot_date_str)
        else:
            pivot_date = datetime.now()
        
        from modules.astro.time_harmonics import TimeHarmonicsCalculator
        calc = TimeHarmonicsCalculator()
        
        analysis = calc.get_composite_time_analysis(pivot_date, days_forward=90)
        
        return jsonify({
            'status': 'success',
            **analysis
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =============================================================================
# MODEL MANAGEMENT ENDPOINTS
# =============================================================================

@ai_api.route('/models/list', methods=['GET'])
def list_models():
    """List available ML models and their status."""
    available_models = []
    
    model_info = {
        'lightgbm': {'name': 'LightGBM', 'type': 'gradient_boosting'},
        'xgboost': {'name': 'XGBoost', 'type': 'gradient_boosting'},
        'mlp': {'name': 'MLP Neural Network', 'type': 'deep_learning'},
        'lstm': {'name': 'LSTM', 'type': 'deep_learning'},
        'transformer': {'name': 'Transformer', 'type': 'deep_learning'},
        'neural_ode': {'name': 'Neural ODE', 'type': 'deep_learning'},
        'hybrid_meta': {'name': 'Hybrid Meta (Stacking)', 'type': 'ensemble'},
        'random_forest': {'name': 'Random Forest', 'type': 'tree_based'}
    }
    
    for key, info in model_info.items():
        try:
            # Check if model class exists
            if key == 'lightgbm':
                from models.ml_lightgbm import LightGBMModel
                available = True
            elif key == 'xgboost':
                from models.ml_xgboost import XGBoostModel
                available = True
            elif key == 'mlp':
                from models.ml_mlp import MLPModel
                available = True
            elif key == 'lstm':
                from models.ml_lstm import LSTMModel
                available = True
            elif key == 'transformer':
                from models.ml_transformer import TransformerModel
                available = True
            elif key == 'neural_ode':
                from models.ml_neural_ode import NeuralODEModel
                available = True
            elif key == 'hybrid_meta':
                from models.ml_hybrid_meta import HybridMetaModel
                available = True
            elif key == 'random_forest':
                from models.ml_randomforest import RandomForestModel
                available = True
            else:
                available = False
        except:
            available = False
        
        available_models.append({
            'id': key,
            **info,
            'available': available
        })
    
    return jsonify({
        'status': 'success',
        'models': available_models,
        'total': len(available_models),
        'available_count': sum(1 for m in available_models if m['available'])
    })


def register_ai_routes(app):
    """Register AI routes with Flask app."""
    app.register_blueprint(ai_api)
    logger.info("AI API routes registered")
