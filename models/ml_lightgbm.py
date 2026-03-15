"""
LightGBM Model Module
High-performance gradient boosting framework for trading predictions.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple, Any
import pickle
import os
from pathlib import Path


class LightGBMModel:
    """
    LightGBM-based prediction model for trading signals.
    
    LightGBM is particularly well-suited for trading applications due to:
    - Fast training speed
    - Low memory usage
    - High accuracy
    - Support for handling categorical features
    """
    
    def __init__(self, config: Dict = None, model_path: str = None):
        """
        Initialize LightGBM model.
        
        Args:
            config (Dict): Model configuration
            model_path (str): Path to saved model
        """
        self.config = config or {}
        self.model_path = model_path or "outputs/models/lightgbm_model.pkl"
        self.model = None
        self.feature_importance = None
        self.is_trained = False
        
        # Default hyperparameters
        self.params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'max_depth': 8,
            'min_child_samples': 20,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'n_estimators': 500,
            'early_stopping_rounds': 50,
            'verbose': -1
        }
        
        # Override with config
        if 'lightgbm_params' in self.config:
            self.params.update(self.config['lightgbm_params'])
        
        logger.info("LightGBMModel initialized")
    
    def _check_lightgbm(self) -> bool:
        """Check if LightGBM is available."""
        try:
            import lightgbm as lgb
            return True
        except ImportError:
            logger.warning("LightGBM not installed. Using fallback implementation.")
            return False
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None
    ) -> Dict:
        """
        Train LightGBM model.
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (pd.Series): Training labels
            X_val (pd.DataFrame): Validation features (optional)
            y_val (pd.Series): Validation labels (optional)
            
        Returns:
            Dict: Training metrics
        """
        logger.info(f"Training LightGBM model with {len(X_train)} samples")
        
        if self._check_lightgbm():
            return self._train_lightgbm(X_train, y_train, X_val, y_val)
        else:
            return self._train_fallback(X_train, y_train)
    
    def _train_lightgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None
    ) -> Dict:
        """Train using actual LightGBM."""
        import lightgbm as lgb
        
        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        
        valid_sets = [train_data]
        if X_val is not None and y_val is not None:
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            valid_sets.append(val_data)
        
        # Train model
        callbacks = [
            lgb.early_stopping(self.params.get('early_stopping_rounds', 50)),
            lgb.log_evaluation(period=100)
        ]
        
        self.model = lgb.train(
            params=self.params,
            train_set=train_data,
            valid_sets=valid_sets,
            callbacks=callbacks
        )
        
        # Feature importance
        self.feature_importance = dict(zip(
            X_train.columns,
            self.model.feature_importance(importance_type='gain')
        ))
        
        self.is_trained = True
        
        # Calculate metrics
        train_pred = self.model.predict(X_train)
        train_auc = self._calculate_auc(y_train, train_pred)
        
        metrics = {
            'train_auc': train_auc,
            'best_iteration': self.model.best_iteration,
            'n_features': len(X_train.columns)
        }
        
        if X_val is not None:
            val_pred = self.model.predict(X_val)
            metrics['val_auc'] = self._calculate_auc(y_val, val_pred)
        
        logger.success(f"LightGBM training complete. Train AUC: {train_auc:.4f}")
        
        return metrics
    
    def _train_fallback(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """Fallback training using gradient boosting from scratch."""
        from models.ml_ensemble import GradientBoostingClassifier
        
        self.model = GradientBoostingClassifier(
            n_estimators=self.params.get('n_estimators', 100),
            max_depth=self.params.get('max_depth', 5),
            learning_rate=self.params.get('learning_rate', 0.1)
        )
        
        self.model.fit(X_train.values, y_train.values)
        self.is_trained = True
        
        return {'train_accuracy': 0.0, 'method': 'fallback'}
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions.
        
        Args:
            X (pd.DataFrame): Features
            
        Returns:
            np.ndarray: Prediction probabilities
        """
        if not self.is_trained or self.model is None:
            logger.warning("Model not trained, returning default predictions")
            return np.full(len(X), 0.5)
        
        if self._check_lightgbm():
            return self.model.predict(X)
        else:
            return self.model.predict_proba(X.values)[:, 1]
    
    def predict_class(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Generate class predictions.
        
        Args:
            X (pd.DataFrame): Features
            threshold (float): Classification threshold
            
        Returns:
            np.ndarray: Class predictions (0 or 1)
        """
        probs = self.predict(X)
        return (probs >= threshold).astype(int)
    
    def _calculate_auc(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate AUC score."""
        try:
            from sklearn.metrics import roc_auc_score
            return roc_auc_score(y_true, y_pred)
        except:
            # Simple AUC approximation
            pos_indices = np.where(y_true == 1)[0]
            neg_indices = np.where(y_true == 0)[0]
            
            if len(pos_indices) == 0 or len(neg_indices) == 0:
                return 0.5
            
            n_correct = 0
            for pos_idx in pos_indices:
                for neg_idx in neg_indices:
                    if y_pred[pos_idx] > y_pred[neg_idx]:
                        n_correct += 1
                    elif y_pred[pos_idx] == y_pred[neg_idx]:
                        n_correct += 0.5
            
            return n_correct / (len(pos_indices) * len(neg_indices))
    
    def save_model(self, path: str = None):
        """Save model to disk."""
        save_path = path or self.model_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_importance': self.feature_importance,
                'params': self.params
            }, f)
        
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, path: str = None):
        """Load model from disk."""
        load_path = path or self.model_path
        
        if not os.path.exists(load_path):
            logger.warning(f"Model file not found: {load_path}")
            return False
        
        with open(load_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.feature_importance = data.get('feature_importance')
            self.params = data.get('params', self.params)
        
        self.is_trained = True
        logger.info(f"Model loaded from {load_path}")
        return True
    
    def get_feature_importance(self, top_n: int = 20) -> List[Dict]:
        """
        Get feature importance rankings.
        
        Args:
            top_n (int): Number of top features to return
            
        Returns:
            List[Dict]: Feature importance list
        """
        if self.feature_importance is None:
            return []
        
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'feature': name, 'importance': score}
            for name, score in sorted_features[:top_n]
        ]


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
        n_samples = len(X)
        
        # Initialize with log odds
        pos_ratio = np.mean(y)
        self.initial_pred = np.log(pos_ratio / (1 - pos_ratio + 1e-10))
        
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
        
        # Find best split
        best_feature = 0
        best_threshold = np.median(X[:, 0])
        
        # Random feature selection
        feature_idx = np.random.randint(0, X.shape[1])
        best_feature = feature_idx
        best_threshold = np.median(X[:, feature_idx])
        
        left_mask = X[:, best_feature] <= best_threshold
        right_mask = ~left_mask
        
        if sum(left_mask) == 0 or sum(right_mask) == 0:
            return {'leaf': True, 'value': np.mean(residuals)}
        
        return {
            'leaf': False,
            'feature': best_feature,
            'threshold': best_threshold,
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


def create_lightgbm_model(config: Dict = None) -> LightGBMModel:
    """Factory function for LightGBM model."""
    return LightGBMModel(config)


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
    
    # Split data
    train_size = int(0.8 * n_samples)
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    
    # Train model
    model = LightGBMModel()
    metrics = model.train(X_train, y_train, X_val, y_val)
    
    print("Training Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    
    # Feature importance
    importance = model.get_feature_importance(10)
    print("\nTop 10 Features:")
    for feat in importance:
        print(f"  {feat['feature']}: {feat['importance']:.4f}")
