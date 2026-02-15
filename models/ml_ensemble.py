"""
ML Ensemble Model Module
Ensemble methods combining multiple models
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger


class EnsembleModel:
    """
    Ensemble model combining multiple predictors.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.models = {}
        self.weights = {}
        
        logger.info("EnsembleModel initialized")
    
    def add_model(self, name: str, model, weight: float = 1.0):
        """Add a model to the ensemble"""
        self.models[name] = model
        self.weights[name] = weight
        logger.info(f"Added model '{name}' with weight {weight}")
    
    def remove_model(self, name: str):
        """Remove a model from ensemble"""
        if name in self.models:
            del self.models[name]
            del self.weights[name]
            logger.info(f"Removed model '{name}'")
    
    def predict(self, X: pd.DataFrame, method: str = 'weighted_average') -> np.ndarray:
        """Generate ensemble prediction"""
        if not self.models:
            logger.warning("No models in ensemble")
            return np.array([])
        
        predictions = {}
        
        for name, model in self.models.items():
            try:
                pred = model.predict(X)
                predictions[name] = pred
            except Exception as e:
                logger.warning(f"Model {name} prediction failed: {e}")
        
        if not predictions:
            return np.array([])
        
        if method == 'weighted_average':
            return self._weighted_average(predictions)
        elif method == 'voting':
            return self._voting(predictions)
        elif method == 'stacking':
            return self._stacking(predictions)
        else:
            return self._simple_average(predictions)
    
    def _weighted_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Weighted average of predictions"""
        total_weight = sum(self.weights[name] for name in predictions.keys())
        
        result = np.zeros(len(list(predictions.values())[0]))
        
        for name, pred in predictions.items():
            weight = self.weights[name] / total_weight
            result += pred * weight
        
        return result
    
    def _simple_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Simple average of predictions"""
        stacked = np.stack(list(predictions.values()))
        return np.mean(stacked, axis=0)
    
    def _voting(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Majority voting for classification"""
        stacked = np.stack(list(predictions.values()))
        # Get mode along axis 0
        from scipy import stats
        result, _ = stats.mode(stacked, axis=0)
        return result.flatten()
    
    def _stacking(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Stacking predictions (simplified)"""
        # For simplicity, just weighted average
        return self._weighted_average(predictions)
    
    def get_model_contributions(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Get individual model contributions"""
        contributions = {}
        
        for name, model in self.models.items():
            try:
                pred = model.predict(X)
                contributions[name] = pred
            except Exception:
                pass
        
        return contributions
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Evaluate ensemble performance"""
        predictions = self.predict(X)
        
        if len(predictions) == 0:
            return {'error': 'No predictions generated'}
        
        # Classification metrics
        if len(np.unique(y)) <= 10:  # Likely classification
            accuracy = np.mean(np.round(predictions) == y)
            return {
                'accuracy': accuracy,
                'n_models': len(self.models)
            }
        else:  # Regression
            mse = np.mean((predictions - y) ** 2)
            mae = np.mean(np.abs(predictions - y))
            return {
                'mse': mse,
                'mae': mae,
                'n_models': len(self.models)
            }


class VotingEnsemble(EnsembleModel):
    """Voting ensemble for classification"""
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return super().predict(X, method='voting')


class StackingEnsemble(EnsembleModel):
    """Stacking ensemble with meta-learner"""
    
    def __init__(self, config: Dict = None, meta_learner=None):
        super().__init__(config)
        self.meta_learner = meta_learner
    
    def train_meta(self, X: pd.DataFrame, y: pd.Series):
        """Train the meta-learner on base model predictions"""
        base_predictions = []
        
        for name, model in self.models.items():
            pred = model.predict(X)
            base_predictions.append(pred)
        
        if base_predictions and self.meta_learner is not None:
            meta_X = np.column_stack(base_predictions)
            self.meta_learner.fit(meta_X, y)
            logger.info("Meta-learner trained")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        base_predictions = []
        
        for name, model in self.models.items():
            pred = model.predict(X)
            base_predictions.append(pred)
        
        if base_predictions and self.meta_learner is not None:
            meta_X = np.column_stack(base_predictions)
            return self.meta_learner.predict(meta_X)
        
        return self._weighted_average(dict(zip(self.models.keys(), base_predictions)))


class GradientBoostingClassifier:
    """
    Pure Python Gradient Boosting implementation.
    Fallback when scikit-learn or LightGBM not available.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 3,
        learning_rate: float = 0.1
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.trees = []
        self.initial_pred = 0
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit gradient boosting model."""
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values
            
        n_samples = len(X)
        
        # Initialize with log odds
        pos_ratio = np.mean(y)
        self.initial_pred = np.log((pos_ratio + 1e-8) / (1 - pos_ratio + 1e-8))
        
        F = np.full(n_samples, self.initial_pred)
        
        for i in range(self.n_estimators):
            # Calculate pseudo-residuals
            probs = 1 / (1 + np.exp(-F))
            residuals = y - probs
            
            # Build tree to fit residuals
            tree = self._build_tree(X, residuals, depth=0)
            self.trees.append(tree)
            
            # Update predictions
            for j in range(n_samples):
                F[j] += self.learning_rate * self._predict_tree(tree, X[j])
        
        return self
    
    def _build_tree(self, X: np.ndarray, residuals: np.ndarray, depth: int) -> Dict:
        """Build a simple regression tree."""
        if depth >= self.max_depth or len(X) < 5:
            return {'leaf': True, 'value': np.mean(residuals)}
        
        # Random feature selection for split
        n_features = X.shape[1]
        feature_idx = np.random.randint(0, n_features)
        threshold = np.median(X[:, feature_idx])
        
        left_mask = X[:, feature_idx] <= threshold
        right_mask = ~left_mask
        
        if sum(left_mask) == 0 or sum(right_mask) == 0:
            return {'leaf': True, 'value': np.mean(residuals)}
        
        return {
            'leaf': False,
            'feature': feature_idx,
            'threshold': threshold,
            'left': self._build_tree(X[left_mask], residuals[left_mask], depth + 1),
            'right': self._build_tree(X[right_mask], residuals[right_mask], depth + 1)
        }
    
    def _predict_tree(self, tree: Dict, x: np.ndarray) -> float:
        """Predict with single tree."""
        if tree['leaf']:
            return tree['value']
        
        if x[tree['feature']] <= tree['threshold']:
            return self._predict_tree(tree['left'], x)
        return self._predict_tree(tree['right'], x)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        if isinstance(X, pd.DataFrame):
            X = X.values
            
        n_samples = len(X)
        F = np.full(n_samples, self.initial_pred)
        
        for tree in self.trees:
            for i in range(n_samples):
                F[i] += self.learning_rate * self._predict_tree(tree, X[i])
        
        probs = 1 / (1 + np.exp(-F))
        return np.column_stack([1 - probs, probs])
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict classes."""
        probs = self.predict_proba(X)
        return (probs[:, 1] >= 0.5).astype(int)

