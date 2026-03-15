"""
Hybrid Meta Model (Stacking Ensemble)
Combines multiple base models using a meta-learner for optimal predictions.

This is a production-ready stacking ensemble that combines:
- LightGBM / Gradient Boosting
- XGBoost
- MLP Neural Network
- LSTM
- Random Forest
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple, Any
import pickle
import os
from dataclasses import dataclass


@dataclass
class ModelWeight:
    """Weight configuration for ensemble model."""
    name: str
    weight: float
    is_active: bool


class HybridMetaModel:
    """
    Hybrid Meta Model using stacking ensemble approach.
    
    Architecture:
    1. Level 0: Base models (LightGBM, XGBoost, MLP, LSTM, RF)
    2. Level 1: Meta-learner (blends base model predictions)
    
    The meta-learner is trained on out-of-fold predictions from base models.
    """
    
    def __init__(self, config: Dict = None, model_path: str = None):
        """
        Initialize Hybrid Meta Model.
        
        Args:
            config (Dict): Model configuration
            model_path (str): Path to saved model
        """
        self.config = config or {}
        self.model_path = model_path or "outputs/models/hybrid_meta_model.pkl"
        self.base_models = {}
        self.meta_model = None
        self.model_weights = {}
        self.is_trained = False
        self.n_folds = self.config.get('n_folds', 5)
        
        # Initialize model weights
        default_weights = {
            'lightgbm': 0.30,
            'xgboost': 0.25,
            'mlp': 0.20,
            'lstm': 0.15,
            'random_forest': 0.10
        }
        self.model_weights = self.config.get('model_weights', default_weights)
        
        logger.info(f"HybridMetaModel initialized with {len(self.model_weights)} base models")
    
    def _init_base_models(self, input_dim: int):
        """Initialize base models."""
        try:
            from models.ml_lightgbm import LightGBMModel
            self.base_models['lightgbm'] = LightGBMModel(self.config)
        except:
            logger.warning("LightGBM not available")
        
        try:
            from models.ml_xgboost import XGBoostModel
            self.base_models['xgboost'] = XGBoostModel(self.config)
        except:
            logger.warning("XGBoost not available")
        
        try:
            from models.ml_mlp import MLPModel
            self.base_models['mlp'] = MLPModel({
                'hidden_layers': [128, 64],
                'epochs': 50
            })
        except:
            logger.warning("MLP not available")
        
        try:
            from models.ml_lstm import LSTMModel
            self.base_models['lstm'] = LSTMModel(self.config)
        except:
            logger.warning("LSTM not available")
        
        try:
            from models.ml_randomforest import RandomForestModel
            self.base_models['random_forest'] = RandomForestModel()
        except:
            logger.warning("Random Forest not available")
        
        # Fallback if no models available
        if not self.base_models:
            self.base_models['simple'] = SimpleLinearModel()
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None
    ) -> Dict:
        """
        Train hybrid meta model.
        
        Process:
        1. Generate out-of-fold predictions for each base model
        2. Stack predictions as features for meta-learner
        3. Train meta-learner on stacked features
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (pd.Series): Training labels
            X_val (pd.DataFrame): Validation features
            y_val (pd.Series): Validation labels
            
        Returns:
            Dict: Training metrics
        """
        logger.info(f"Training Hybrid Meta Model with {len(X_train)} samples")
        
        # Initialize base models
        self._init_base_models(X_train.shape[1])
        
        # Generate out-of-fold predictions
        oof_predictions = self._generate_oof_predictions(X_train, y_train)
        
        # Train meta-learner
        meta_features = pd.DataFrame(oof_predictions)
        self.meta_model = MetaLearner(self.model_weights)
        self.meta_model.train(meta_features, y_train)
        
        # Retrain base models on full training data
        for name, model in self.base_models.items():
            logger.info(f"Training {name} on full training set")
            try:
                model.train(X_train, y_train, X_val, y_val)
            except Exception as e:
                logger.error(f"Failed to train {name}: {e}")
        
        self.is_trained = True
        
        # Calculate metrics
        train_pred = self.predict(X_train)
        train_acc = np.mean((train_pred >= 0.5) == y_train)
        
        metrics = {
            'train_accuracy': train_acc,
            'n_base_models': len(self.base_models),
            'base_models': list(self.base_models.keys())
        }
        
        if X_val is not None and y_val is not None:
            val_pred = self.predict(X_val)
            val_acc = np.mean((val_pred >= 0.5) == y_val)
            metrics['val_accuracy'] = val_acc
        
        logger.success(f"Hybrid Meta Model training complete. Accuracy: {train_acc:.4f}")
        return metrics
    
    def _generate_oof_predictions(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Dict[str, np.ndarray]:
        """
        Generate out-of-fold predictions using k-fold cross-validation.
        
        Args:
            X (pd.DataFrame): Features
            y (pd.Series): Labels
            
        Returns:
            Dict[str, np.ndarray]: OOF predictions for each model
        """
        n_samples = len(X)
        fold_size = n_samples // self.n_folds
        indices = np.arange(n_samples)
        np.random.shuffle(indices)
        
        oof_predictions = {name: np.zeros(n_samples) for name in self.base_models}
        
        for fold in range(self.n_folds):
            val_start = fold * fold_size
            val_end = val_start + fold_size if fold < self.n_folds - 1 else n_samples
            
            val_idx = indices[val_start:val_end]
            train_idx = np.concatenate([indices[:val_start], indices[val_end:]])
            
            X_train_fold = X.iloc[train_idx]
            y_train_fold = y.iloc[train_idx]
            X_val_fold = X.iloc[val_idx]
            
            for name, model in self.base_models.items():
                try:
                    # Train on fold
                    model.train(X_train_fold, y_train_fold)
                    
                    # Predict on validation
                    preds = model.predict(X_val_fold)
                    oof_predictions[name][val_idx] = preds
                except Exception as e:
                    logger.warning(f"Fold {fold}: {name} failed - {e}")
                    oof_predictions[name][val_idx] = 0.5
        
        return oof_predictions
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions using ensemble.
        
        Args:
            X (pd.DataFrame): Features
            
        Returns:
            np.ndarray: Blended prediction probabilities
        """
        if not self.is_trained:
            return np.full(len(X), 0.5)
        
        # Get predictions from all base models
        base_predictions = {}
        for name, model in self.base_models.items():
            try:
                base_predictions[name] = model.predict(X)
            except Exception as e:
                logger.warning(f"Prediction failed for {name}: {e}")
                base_predictions[name] = np.full(len(X), 0.5)
        
        # Stack predictions
        meta_features = pd.DataFrame(base_predictions)
        
        # Blend using meta-learner
        if self.meta_model is not None:
            return self.meta_model.predict(meta_features)
        else:
            # Fallback to weighted average
            return self._weighted_average(base_predictions)
    
    def _weighted_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate weighted average of predictions."""
        result = np.zeros(len(list(predictions.values())[0]))
        total_weight = 0
        
        for name, preds in predictions.items():
            weight = self.model_weights.get(name, 0.1)
            result += weight * preds
            total_weight += weight
        
        return result / total_weight
    
    def predict_with_confidence(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict with confidence intervals based on model agreement.
        
        Args:
            X (pd.DataFrame): Features
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Predictions and confidence scores
        """
        # Get predictions from all models
        all_predictions = []
        for name, model in self.base_models.items():
            try:
                preds = model.predict(X)
                all_predictions.append(preds)
            except:
                pass
        
        if not all_predictions:
            return np.full(len(X), 0.5), np.zeros(len(X))
        
        predictions_array = np.array(all_predictions)
        
        # Mean prediction
        mean_pred = np.mean(predictions_array, axis=0)
        
        # Confidence = 1 - std (higher agreement = higher confidence)
        std_pred = np.std(predictions_array, axis=0)
        confidence = 1 - np.clip(std_pred / 0.5, 0, 1)  # Normalize
        
        return mean_pred, confidence
    
    def get_model_contributions(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Get individual model contributions to final prediction.
        
        Args:
            X (pd.DataFrame): Features
            
        Returns:
            Dict[str, np.ndarray]: Contributions from each model
        """
        contributions = {}
        
        for name, model in self.base_models.items():
            try:
                preds = model.predict(X)
                weight = self.model_weights.get(name, 0.1)
                contributions[name] = preds * weight
            except:
                contributions[name] = np.zeros(len(X))
        
        return contributions
    
    def save_model(self, path: str = None):
        """Save model to disk."""
        save_path = path or self.model_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump({
                'base_models': self.base_models,
                'meta_model': self.meta_model,
                'model_weights': self.model_weights,
                'config': self.config
            }, f)
        
        logger.info(f"Hybrid model saved to {save_path}")
    
    def load_model(self, path: str = None):
        """Load model from disk."""
        load_path = path or self.model_path
        
        if not os.path.exists(load_path):
            return False
        
        with open(load_path, 'rb') as f:
            data = pickle.load(f)
            self.base_models = data['base_models']
            self.meta_model = data.get('meta_model')
            self.model_weights = data.get('model_weights', {})
            self.config = data.get('config', {})
        
        self.is_trained = True
        return True


class MetaLearner:
    """Meta-learner for stacking ensemble."""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {}
        self.learned_weights = None
        self.bias = 0
    
    def train(self, meta_features: pd.DataFrame, y: pd.Series):
        """Train meta-learner."""
        X = meta_features.values
        y = y.values
        
        # Simple linear combination learning
        # Ridge regression style
        lambda_reg = 0.1
        
        XtX = X.T @ X + lambda_reg * np.eye(X.shape[1])
        Xty = X.T @ y
        
        try:
            self.learned_weights = np.linalg.solve(XtX, Xty)
        except:
            self.learned_weights = np.ones(X.shape[1]) / X.shape[1]
        
        # Calculate bias
        predictions = X @ self.learned_weights
        self.bias = np.mean(y) - np.mean(predictions)
    
    def predict(self, meta_features: pd.DataFrame) -> np.ndarray:
        """Generate predictions."""
        X = meta_features.values
        
        if self.learned_weights is None:
            return np.mean(X, axis=1)
        
        predictions = X @ self.learned_weights + self.bias
        return np.clip(predictions, 0, 1)


class SimpleLinearModel:
    """Fallback simple linear model."""
    
    def __init__(self):
        self.weights = None
        self.bias = 0
        self.mean = None
        self.std = None
    
    def train(self, X: pd.DataFrame, y: pd.Series, X_val=None, y_val=None):
        """Train simple linear model."""
        X_arr = X.values
        y_arr = y.values
        
        self.mean = np.mean(X_arr, axis=0)
        self.std = np.std(X_arr, axis=0) + 1e-8
        
        X_norm = (X_arr - self.mean) / self.std
        
        # Ridge regression
        lambda_reg = 1.0
        XtX = X_norm.T @ X_norm + lambda_reg * np.eye(X_norm.shape[1])
        Xty = X_norm.T @ y_arr
        
        try:
            self.weights = np.linalg.solve(XtX, Xty)
        except:
            self.weights = np.zeros(X_norm.shape[1])
        
        self.bias = np.mean(y_arr)
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate predictions."""
        if self.weights is None:
            return np.full(len(X), 0.5)
        
        X_arr = X.values
        X_norm = (X_arr - self.mean) / self.std
        
        predictions = X_norm @ self.weights + self.bias
        return 1 / (1 + np.exp(-predictions))  # Sigmoid


if __name__ == "__main__":
    # Test
    np.random.seed(42)
    n_samples = 1000
    n_features = 20
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series((X['feature_0'] + X['feature_1'] * 0.5 > 0).astype(int))
    
    # Split
    train_size = int(0.8 * n_samples)
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    
    # Train
    model = HybridMetaModel({'n_folds': 3})
    metrics = model.train(X_train, y_train, X_val, y_val)
    
    print("Training Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    
    # Predict with confidence
    preds, confidence = model.predict_with_confidence(X_val)
    print(f"\nPrediction range: [{preds.min():.4f}, {preds.max():.4f}]")
    print(f"Confidence range: [{confidence.min():.4f}, {confidence.max():.4f}]")
