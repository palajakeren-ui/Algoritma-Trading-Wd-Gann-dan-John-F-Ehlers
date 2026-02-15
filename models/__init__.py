"""
ML Models Module
Machine Learning model implementations for trading predictions.

Available Models:
- LightGBM: Fast gradient boosting
- XGBoost: Extreme gradient boosting
- MLP: Multi-layer perceptron neural network
- LSTM: Long short-term memory neural network
- Transformer: Attention-based neural network
- Neural ODE: Continuous-time neural network
- Hybrid Meta: Stacking ensemble of multiple models
- Random Forest: Tree-based ensemble
- Linear: Simple linear model
"""

from .ml_ensemble import GradientBoostingClassifier as EnsembleGradientBoosting
from .ml_randomforest import RandomForestModel
from .ml_xgboost import XGBoostModel
from .ml_lstm import LSTMModel
from .ml_transformer import TransformerModel
from .ml_lightgbm import LightGBMModel, GradientBoostingClassifier
from .ml_mlp import MLPModel, NumpyMLP
from .ml_neural_ode import NeuralODEModel, NumpyNeuralODE
from .ml_hybrid_meta import HybridMetaModel, MetaLearner, SimpleLinearModel
from .options_pricer import OptionsPricer
from .quantum_module import QuantumInspiredOptimizer

__all__ = [
    # Core Models
    'LightGBMModel',
    'XGBoostModel',
    'MLPModel',
    'LSTMModel',
    'TransformerModel',
    'NeuralODEModel',
    'HybridMetaModel',
    'RandomForestModel',
    
    # Support Classes
    'GradientBoostingClassifier',
    'EnsembleGradientBoosting',
    'NumpyMLP',
    'NumpyNeuralODE',
    'MetaLearner',
    'SimpleLinearModel',
    
    # Other Modules
    'OptionsPricer',
    'QuantumInspiredOptimizer',
]

# Model registry for easy access
MODEL_REGISTRY = {
    'lightgbm': LightGBMModel,
    'xgboost': XGBoostModel,
    'mlp': MLPModel,
    'lstm': LSTMModel,
    'transformer': TransformerModel,
    'neural_ode': NeuralODEModel,
    'hybrid_meta': HybridMetaModel,
    'random_forest': RandomForestModel,
}


def get_model(model_name: str, config: dict = None):
    """
    Factory function to get a model by name.
    
    Args:
        model_name (str): Name of the model
        config (dict): Model configuration
        
    Returns:
        Model instance
    """
    model_class = MODEL_REGISTRY.get(model_name.lower())
    if model_class is None:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(MODEL_REGISTRY.keys())}")
    return model_class(config or {})


def list_available_models():
    """Return list of available model names."""
    return list(MODEL_REGISTRY.keys())
