"""
ML Trainer Module
Model training and validation utilities
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .features import FeatureBuilder
from .models import create_model


@dataclass
class TrainingResult:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    samples_trained: int
    features_used: int


class ModelTrainer:
    """Handles model training and validation."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.feature_builder = FeatureBuilder(config)
        self.train_split = self.config.get('train_split', 0.8)
        logger.info("ModelTrainer initialized")
    
    def prepare_data(
        self,
        data: pd.DataFrame,
        forward_periods: int = 5
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare data for training."""
        # Build features
        df = self.feature_builder.build_all_features(data)
        
        # Create target
        df['target'] = (df['close'].shift(-forward_periods) / df['close'] - 1) > 0
        df['target'] = df['target'].astype(float)
        
        # Select feature columns
        feature_cols = [col for col in df.columns 
                       if col not in ['open', 'high', 'low', 'close', 'volume', 'target']]
        
        # Clean data
        df_clean = df.dropna()
        
        X = df_clean[feature_cols].values
        y = df_clean['target'].values
        
        return X, y, feature_cols
    
    def train_test_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        train_ratio: float = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into train and test sets."""
        if train_ratio is None:
            train_ratio = self.train_split
        
        split_idx = int(len(X) * train_ratio)
        
        X_train = X[:split_idx]
        X_test = X[split_idx:]
        y_train = y[:split_idx]
        y_test = y[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Calculate classification metrics."""
        y_pred_binary = (y_pred > 0.5).astype(float)
        
        tp = np.sum((y_true == 1) & (y_pred_binary == 1))
        tn = np.sum((y_true == 0) & (y_pred_binary == 0))
        fp = np.sum((y_true == 0) & (y_pred_binary == 1))
        fn = np.sum((y_true == 1) & (y_pred_binary == 0))
        
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    def train_and_evaluate(
        self,
        data: pd.DataFrame,
        model_type: str = 'ensemble',
        forward_periods: int = 5
    ) -> Tuple[TrainingResult, any]:
        """Train model and evaluate performance."""
        # Prepare data
        X, y, feature_cols = self.prepare_data(data, forward_periods)
        
        if len(X) < 100:
            logger.warning("Insufficient data for training")
            return None, None
        
        # Split data
        X_train, X_test, y_train, y_test = self.train_test_split(X, y)
        
        # Create and train model
        model = create_model(model_type, self.config)
        model.train(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        metrics = self.calculate_metrics(y_test, y_pred)
        
        result = TrainingResult(
            accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            samples_trained=len(X_train),
            features_used=len(feature_cols)
        )
        
        logger.success(f"Training complete: Accuracy={result.accuracy:.2%}")
        
        return result, model
    
    def cross_validate(
        self,
        data: pd.DataFrame,
        n_folds: int = 5,
        model_type: str = 'ensemble'
    ) -> Dict[str, float]:
        """Perform time-series cross-validation."""
        X, y, _ = self.prepare_data(data)
        
        if len(X) < n_folds * 20:
            return {'error': 'Insufficient data for cross-validation'}
        
        fold_size = len(X) // n_folds
        accuracies = []
        
        for i in range(1, n_folds):
            train_end = i * fold_size
            test_end = (i + 1) * fold_size
            
            X_train = X[:train_end]
            y_train = y[:train_end]
            X_test = X[train_end:test_end]
            y_test = y[train_end:test_end]
            
            model = create_model(model_type, self.config)
            model.train(X_train, y_train)
            
            y_pred = model.predict(X_test)
            metrics = self.calculate_metrics(y_test, y_pred)
            accuracies.append(metrics['accuracy'])
        
        return {
            'mean_accuracy': np.mean(accuracies),
            'std_accuracy': np.std(accuracies),
            'fold_accuracies': accuracies
        }


if __name__ == "__main__":
    # Test
    dates = pd.date_range(start='2024-01-01', periods=300, freq='1D')
    np.random.seed(42)
    
    price = 50000
    prices = [price]
    for _ in range(299):
        price = price * (1 + np.random.randn() * 0.015)
        prices.append(price)
    
    data = pd.DataFrame({
        'open': [p * 0.998 for p in prices],
        'high': [p * 1.015 for p in prices],
        'low': [p * 0.985 for p in prices],
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 300)
    }, index=dates)
    
    trainer = ModelTrainer()
    result, model = trainer.train_and_evaluate(data)
    
    if result:
        print(f"\nTraining Result:")
        print(f"  Accuracy: {result.accuracy:.2%}")
        print(f"  Precision: {result.precision:.2%}")
        print(f"  Recall: {result.recall:.2%}")
        print(f"  F1 Score: {result.f1_score:.2%}")
