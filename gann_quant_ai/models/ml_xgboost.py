"""
ML XGBoost Model Module
XGBoost implementation for price prediction
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("XGBoost not installed")


class XGBoostModel:
    """
    XGBoost model for price direction prediction.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model = None
        self.feature_names = None
        
        self.default_params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'use_label_encoder': False,
            'random_state': 42
        }
        
        logger.info("XGBoostModel initialized")
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        params: Dict = None,
        validation_split: float = 0.2
    ) -> Dict:
        """Train XGBoost model"""
        if not HAS_XGBOOST:
            logger.error("XGBoost not installed")
            return {'error': 'XGBoost not installed'}
        
        self.feature_names = list(X.columns)
        
        # Merge params
        model_params = {**self.default_params, **(params or {})}
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Create model
        self.model = xgb.XGBClassifier(**model_params)
        
        # Train with early stopping
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)
        
        logger.info(f"XGBoost trained - Train: {train_score:.4f}, Val: {val_score:.4f}")
        
        return {
            'train_accuracy': train_score,
            'validation_accuracy': val_score,
            'best_iteration': self.model.best_iteration if hasattr(self.model, 'best_iteration') else None
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class labels"""
        if self.model is None:
            logger.error("Model not trained")
            return np.array([])
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities"""
        if self.model is None:
            logger.error("Model not trained")
            return np.array([])
        
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        if self.model is None or self.feature_names is None:
            return {}
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def save(self, filepath: str):
        """Save model to file"""
        if self.model is not None and HAS_XGBOOST:
            self.model.save_model(filepath)
            logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from file"""
        if HAS_XGBOOST:
            self.model = xgb.XGBClassifier()
            self.model.load_model(filepath)
            logger.info(f"Model loaded from {filepath}")


class XGBoostRegressor:
    """XGBoost for price regression"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model = None
        
        self.default_params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'objective': 'reg:squarederror',
            'random_state': 42
        }
        
        logger.info("XGBoostRegressor initialized")
    
    def train(self, X: pd.DataFrame, y: pd.Series, params: Dict = None) -> Dict:
        """Train regression model"""
        if not HAS_XGBOOST:
            return {'error': 'XGBoost not installed'}
        
        model_params = {**self.default_params, **(params or {})}
        self.model = xgb.XGBRegressor(**model_params)
        self.model.fit(X, y)
        
        score = self.model.score(X, y)
        logger.info(f"XGBoost regressor trained - R²: {score:.4f}")
        
        return {'r2_score': score}
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict values"""
        if self.model is None:
            return np.array([])
        return self.model.predict(X)
