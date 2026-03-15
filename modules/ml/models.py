"""
ML Models Module
Machine learning model implementations
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class ModelPrediction:
    prediction: int  # 1 = bullish, -1 = bearish, 0 = neutral
    probability: float
    confidence: float
    features_importance: Dict[str, float]


class BaseModel:
    """Base class for ML models."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.is_trained = False
        self.model = None
    
    def train(self, X: np.ndarray, y: np.ndarray):
        raise NotImplementedError
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class LinearModel(BaseModel):
    """Simple linear regression model."""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.weights = None
        self.bias = 0
        logger.info("LinearModel initialized")
    
    def train(self, X: np.ndarray, y: np.ndarray):
        # Simple OLS fitting
        X_with_bias = np.column_stack([np.ones(len(X)), X])
        try:
            coeffs = np.linalg.lstsq(X_with_bias, y, rcond=None)[0]
            self.bias = coeffs[0]
            self.weights = coeffs[1:]
            self.is_trained = True
        except Exception as e:
            logger.error(f"Training failed: {e}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            return np.zeros(len(X))
        return self.bias + X @ self.weights
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        preds = self.predict(X)
        # Sigmoid for probability
        probs = 1 / (1 + np.exp(-preds))
        return np.column_stack([1 - probs, probs])


class RandomForestLite(BaseModel):
    """Lightweight random forest implementation."""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.n_trees = self.config.get('n_trees', 10)
        self.max_depth = self.config.get('max_depth', 5)
        self.trees = []
        logger.info("RandomForestLite initialized")
    
    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> Dict:
        """Build a simple decision tree."""
        if depth >= self.max_depth or len(np.unique(y)) == 1 or len(y) < 5:
            return {'leaf': True, 'value': np.mean(y)}
        
        # Random feature and split point
        n_features = X.shape[1]
        feature_idx = np.random.randint(0, n_features)
        split = np.median(X[:, feature_idx])
        
        left_mask = X[:, feature_idx] <= split
        right_mask = ~left_mask
        
        if sum(left_mask) == 0 or sum(right_mask) == 0:
            return {'leaf': True, 'value': np.mean(y)}
        
        return {
            'leaf': False,
            'feature': feature_idx,
            'split': split,
            'left': self._build_tree(X[left_mask], y[left_mask], depth + 1),
            'right': self._build_tree(X[right_mask], y[right_mask], depth + 1)
        }
    
    def _predict_tree(self, tree: Dict, x: np.ndarray) -> float:
        """Predict with single tree."""
        if tree['leaf']:
            return tree['value']
        
        if x[tree['feature']] <= tree['split']:
            return self._predict_tree(tree['left'], x)
        return self._predict_tree(tree['right'], x)
    
    def train(self, X: np.ndarray, y: np.ndarray):
        self.trees = []
        n_samples = len(X)
        
        for _ in range(self.n_trees):
            # Bootstrap sample
            indices = np.random.choice(n_samples, n_samples, replace=True)
            X_boot = X[indices]
            y_boot = y[indices]
            
            tree = self._build_tree(X_boot, y_boot)
            self.trees.append(tree)
        
        self.is_trained = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained or not self.trees:
            return np.zeros(len(X))
        
        predictions = np.zeros(len(X))
        for i, x in enumerate(X):
            preds = [self._predict_tree(tree, x) for tree in self.trees]
            predictions[i] = np.mean(preds)
        
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        preds = self.predict(X)
        probs = 1 / (1 + np.exp(-preds))
        return np.column_stack([1 - probs, probs])


class EnsembleModel(BaseModel):
    """Ensemble of multiple models."""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.models = [
            LinearModel(config),
            RandomForestLite(config)
        ]
        self.weights = [0.4, 0.6]
        logger.info("EnsembleModel initialized")
    
    def train(self, X: np.ndarray, y: np.ndarray):
        for model in self.models:
            model.train(X, y)
        self.is_trained = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        predictions = np.zeros(len(X))
        for model, weight in zip(self.models, self.weights):
            predictions += weight * model.predict(X)
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        probs = np.zeros((len(X), 2))
        for model, weight in zip(self.models, self.weights):
            probs += weight * model.predict_proba(X)
        return probs


def create_model(model_type: str = 'ensemble', config: Dict = None) -> BaseModel:
    """Factory function to create models."""
    models = {
        'linear': LinearModel,
        'random_forest': RandomForestLite,
        'ensemble': EnsembleModel
    }
    
    model_class = models.get(model_type, EnsembleModel)
    return model_class(config)


if __name__ == "__main__":
    # Test
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(100) * 0.1 > 0).astype(float)
    
    model = create_model('ensemble')
    model.train(X[:80], y[:80])
    
    preds = model.predict(X[80:])
    probs = model.predict_proba(X[80:])
    
    print(f"Predictions shape: {preds.shape}")
    print(f"Probabilities shape: {probs.shape}")
    print(f"Sample predictions: {preds[:5]}")
