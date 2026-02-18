"""
Training Pipeline Module
Complete ML training, validation, and prediction pipeline.

This module orchestrates the entire ML workflow from data preparation
through model training, validation, and deployment.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import pickle
import os
import json
from pathlib import Path


class TrainingPipeline:
    """
    Complete ML training pipeline.
    
    Handles:
    - Data preparation and feature engineering
    - Model training with cross-validation
    - Hyperparameter tuning
    - Model evaluation and selection
    - Model persistence and versioning
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Training Pipeline.
        
        Args:
            config (Dict): Pipeline configuration
        """
        self.config = config or {}
        self.training_config = self.config.get('training', {})
        
        # Paths
        self.model_dir = Path(self.config.get('model_dir', 'outputs/models'))
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Model registry
        self.models = {}
        self.trained_models = {}
        self.model_metrics = {}
        self.best_model_name = None
        
        # Training state
        self.is_fitted = False
        self.feature_names = []
        self.scaler = None
        
        logger.info("TrainingPipeline initialized")
    
    def _init_models(self):
        """Initialize available models."""
        model_configs = self.training_config.get('models', {})
        
        # LightGBM
        try:
            from models.ml_lightgbm import LightGBMModel
            self.models['lightgbm'] = LightGBMModel(model_configs.get('lightgbm', {}))
            logger.info("LightGBM model initialized")
        except Exception as e:
            logger.warning(f"LightGBM not available: {e}")
        
        # XGBoost
        try:
            from models.ml_xgboost import XGBoostModel
            self.models['xgboost'] = XGBoostModel(model_configs.get('xgboost', {}))
            logger.info("XGBoost model initialized")
        except Exception as e:
            logger.warning(f"XGBoost not available: {e}")
        
        # MLP
        try:
            from models.ml_mlp import MLPModel
            self.models['mlp'] = MLPModel(model_configs.get('mlp', {'hidden_layers': [128, 64], 'epochs': 100}))
            logger.info("MLP model initialized")
        except Exception as e:
            logger.warning(f"MLP not available: {e}")
        
        # LSTM
        try:
            from models.ml_lstm import LSTMModel
            self.models['lstm'] = LSTMModel(model_configs.get('lstm', {}))
            logger.info("LSTM model initialized")
        except Exception as e:
            logger.warning(f"LSTM not available: {e}")
        
        # Transformer
        try:
            from models.ml_transformer import TransformerModel
            self.models['transformer'] = TransformerModel(model_configs.get('transformer', {}))
            logger.info("Transformer model initialized")
        except Exception as e:
            logger.warning(f"Transformer not available: {e}")
        
        # Neural ODE
        try:
            from models.ml_neural_ode import NeuralODEModel
            self.models['neural_ode'] = NeuralODEModel(model_configs.get('neural_ode', {}))
            logger.info("Neural ODE model initialized")
        except Exception as e:
            logger.warning(f"Neural ODE not available: {e}")
        
        # Hybrid Meta Model
        try:
            from models.ml_hybrid_meta import HybridMetaModel
            self.models['hybrid_meta'] = HybridMetaModel(model_configs.get('hybrid_meta', {}))
            logger.info("Hybrid Meta Model initialized")
        except Exception as e:
            logger.warning(f"Hybrid Meta not available: {e}")
        
        # Random Forest (fallback)
        try:
            from models.ml_randomforest import RandomForestModel
            self.models['random_forest'] = RandomForestModel()
            logger.info("Random Forest model initialized")
        except Exception as e:
            logger.warning(f"Random Forest not available: {e}")
        
        if not self.models:
            logger.error("No models available!")
    
    def prepare_data(
        self,
        features: pd.DataFrame,
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Dict[str, Tuple[pd.DataFrame, pd.Series]]:
        """
        Prepare data for training.
        
        Args:
            features (pd.DataFrame): Feature DataFrame with target column
            test_size (float): Test set proportion
            val_size (float): Validation set proportion
            
        Returns:
            Dict: Train, validation, test data splits
        """
        logger.info(f"Preparing data with shape {features.shape}")
        
        # Separate features and target
        if 'target' not in features.columns:
            raise ValueError("Target column not found in features")
        
        X = features.drop('target', axis=1)
        y = features['target']
        
        self.feature_names = X.columns.tolist()
        
        # Time-based split (for time series data)
        n = len(X)
        test_idx = int(n * (1 - test_size))
        val_idx = int(test_idx * (1 - val_size))
        
        X_train = X.iloc[:val_idx]
        y_train = y.iloc[:val_idx]
        
        X_val = X.iloc[val_idx:test_idx]
        y_val = y.iloc[val_idx:test_idx]
        
        X_test = X.iloc[test_idx:]
        y_test = y.iloc[test_idx:]
        
        # Fit scaler on training data
        self._fit_scaler(X_train)
        
        logger.info(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return {
            'train': (X_train, y_train),
            'val': (X_val, y_val),
            'test': (X_test, y_test)
        }
    
    def _fit_scaler(self, X: pd.DataFrame):
        """Fit feature scaler."""
        self.scaler = {
            'mean': X.mean(),
            'std': X.std() + 1e-8
        }
    
    def _transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features using fitted scaler."""
        if self.scaler is None:
            return X
        return (X - self.scaler['mean']) / self.scaler['std']
    
    def train_all_models(
        self,
        data: Dict[str, Tuple[pd.DataFrame, pd.Series]],
        models_to_train: List[str] = None
    ) -> Dict[str, Dict]:
        """
        Train all available models.
        
        Args:
            data (Dict): Data splits from prepare_data
            models_to_train (List[str]): List of model names to train (None = all)
            
        Returns:
            Dict: Training metrics for each model
        """
        # Initialize models if not done
        if not self.models:
            self._init_models()
        
        X_train, y_train = data['train']
        X_val, y_val = data['val']
        X_test, y_test = data['test']
        
        if models_to_train is None:
            models_to_train = list(self.models.keys())
        
        results = {}
        
        for model_name in models_to_train:
            if model_name not in self.models:
                logger.warning(f"Model {model_name} not found, skipping")
                continue
            
            logger.info(f"Training {model_name}...")
            
            try:
                model = self.models[model_name]
                
                # Train
                train_metrics = model.train(X_train, y_train, X_val, y_val)
                
                # Evaluate on test set
                test_pred = model.predict(X_test)
                test_metrics = self._evaluate_predictions(y_test, test_pred)
                
                # Store results
                results[model_name] = {
                    'train_metrics': train_metrics,
                    'test_metrics': test_metrics,
                    'status': 'success'
                }
                
                self.trained_models[model_name] = model
                self.model_metrics[model_name] = test_metrics
                
                logger.success(f"{model_name} training complete. Test AUC: {test_metrics.get('auc', 'N/A')}")
                
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
                results[model_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        # Select best model
        self._select_best_model()
        
        self.is_fitted = True
        
        return results
    
    def _evaluate_predictions(
        self,
        y_true: pd.Series,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Evaluate predictions."""
        y_true = y_true.values
        y_pred_binary = (y_pred >= 0.5).astype(int)
        
        # Accuracy
        accuracy = np.mean(y_pred_binary == y_true)
        
        # Precision, Recall, F1
        tp = np.sum((y_pred_binary == 1) & (y_true == 1))
        fp = np.sum((y_pred_binary == 1) & (y_true == 0))
        fn = np.sum((y_pred_binary == 0) & (y_true == 1))
        
        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)
        
        # AUC approximation
        auc = self._calculate_auc(y_true, y_pred)
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'auc': float(auc)
        }
    
    def _calculate_auc(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate AUC score."""
        try:
            from sklearn.metrics import roc_auc_score
            return roc_auc_score(y_true, y_pred)
        except:
            # Manual calculation
            pos_idx = np.where(y_true == 1)[0]
            neg_idx = np.where(y_true == 0)[0]
            
            if len(pos_idx) == 0 or len(neg_idx) == 0:
                return 0.5
            
            correct = 0
            for pi in pos_idx:
                for ni in neg_idx:
                    if y_pred[pi] > y_pred[ni]:
                        correct += 1
                    elif y_pred[pi] == y_pred[ni]:
                        correct += 0.5
            
            return correct / (len(pos_idx) * len(neg_idx))
    
    def _select_best_model(self):
        """Select best model based on test metrics."""
        if not self.model_metrics:
            return
        
        # Sort by AUC
        best_name = max(
            self.model_metrics.keys(),
            key=lambda x: self.model_metrics[x].get('auc', 0)
        )
        
        self.best_model_name = best_name
        logger.info(f"Best model selected: {best_name} (AUC: {self.model_metrics[best_name].get('auc', 0):.4f})")
    
    def predict(
        self,
        X: pd.DataFrame,
        model_name: str = None,
        return_all: bool = False
    ) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        """
        Generate predictions.
        
        Args:
            X (pd.DataFrame): Features
            model_name (str): Specific model to use (None = best model)
            return_all (bool): Return predictions from all models
            
        Returns:
            Predictions
        """
        if not self.is_fitted:
            logger.warning("Pipeline not fitted, returning default predictions")
            return np.full(len(X), 0.5)
        
        if return_all:
            predictions = {}
            for name, model in self.trained_models.items():
                try:
                    predictions[name] = model.predict(X)
                except:
                    predictions[name] = np.full(len(X), 0.5)
            return predictions
        
        # Use specific model or best model
        if model_name is None:
            model_name = self.best_model_name
        
        if model_name not in self.trained_models:
            logger.warning(f"Model {model_name} not found")
            return np.full(len(X), 0.5)
        
        return self.trained_models[model_name].predict(X)
    
    def predict_with_ensemble(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict using ensemble of all trained models.
        
        Args:
            X (pd.DataFrame): Features
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Mean predictions and confidence
        """
        all_predictions = self.predict(X, return_all=True)
        
        if not all_predictions:
            return np.full(len(X), 0.5), np.zeros(len(X))
        
        preds_array = np.array(list(all_predictions.values()))
        
        mean_pred = np.mean(preds_array, axis=0)
        std_pred = np.std(preds_array, axis=0)
        confidence = 1 - np.clip(std_pred / 0.5, 0, 1)
        
        return mean_pred, confidence
    
    def save_pipeline(self, path: str = None):
        """
        Save entire pipeline to disk.
        
        Args:
            path (str): Save path
        """
        save_path = path or str(self.model_dir / 'training_pipeline.pkl')
        
        pipeline_data = {
            'trained_models': self.trained_models,
            'model_metrics': self.model_metrics,
            'best_model_name': self.best_model_name,
            'feature_names': self.feature_names,
            'scaler': self.scaler,
            'config': self.config,
            'is_fitted': self.is_fitted,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(save_path, 'wb') as f:
            pickle.dump(pipeline_data, f)
        
        # Also save metadata as JSON
        metadata = {
            'model_metrics': self.model_metrics,
            'best_model_name': self.best_model_name,
            'feature_names': self.feature_names,
            'n_features': len(self.feature_names),
            'n_models': len(self.trained_models),
            'saved_at': datetime.now().isoformat()
        }
        
        metadata_path = save_path.replace('.pkl', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Pipeline saved to {save_path}")
    
    def load_pipeline(self, path: str = None):
        """
        Load pipeline from disk.
        
        Args:
            path (str): Load path
        """
        load_path = path or str(self.model_dir / 'training_pipeline.pkl')
        
        if not os.path.exists(load_path):
            logger.warning(f"Pipeline file not found: {load_path}")
            return False
        
        with open(load_path, 'rb') as f:
            pipeline_data = pickle.load(f)
        
        self.trained_models = pipeline_data.get('trained_models', {})
        self.model_metrics = pipeline_data.get('model_metrics', {})
        self.best_model_name = pipeline_data.get('best_model_name')
        self.feature_names = pipeline_data.get('feature_names', [])
        self.scaler = pipeline_data.get('scaler')
        self.config = pipeline_data.get('config', {})
        self.is_fitted = pipeline_data.get('is_fitted', False)
        
        logger.info(f"Pipeline loaded from {load_path}")
        return True
    
    def get_pipeline_summary(self) -> Dict:
        """Get pipeline summary."""
        return {
            'is_fitted': self.is_fitted,
            'n_trained_models': len(self.trained_models),
            'trained_models': list(self.trained_models.keys()),
            'best_model': self.best_model_name,
            'n_features': len(self.feature_names),
            'model_metrics': self.model_metrics
        }


class PredictionService:
    """
    Production prediction service.
    
    Handles real-time predictions with caching and error handling.
    """
    
    def __init__(self, pipeline: TrainingPipeline = None):
        """
        Initialize Prediction Service.
        
        Args:
            pipeline (TrainingPipeline): Trained pipeline
        """
        self.pipeline = pipeline
        self.cache = {}
        self.prediction_history = []
        
        logger.info("PredictionService initialized")
    
    def load_pipeline(self, path: str):
        """Load pipeline from disk."""
        self.pipeline = TrainingPipeline()
        return self.pipeline.load_pipeline(path)
    
    def predict(
        self,
        features: pd.DataFrame,
        use_ensemble: bool = True
    ) -> Dict[str, Any]:
        """
        Generate predictions with full result package.
        
        Args:
            features (pd.DataFrame): Input features
            use_ensemble (bool): Use ensemble prediction
            
        Returns:
            Dict: Prediction results
        """
        if self.pipeline is None or not self.pipeline.is_fitted:
            return {
                'status': 'error',
                'message': 'Pipeline not loaded or not fitted'
            }
        
        try:
            timestamp = datetime.now()
            
            if use_ensemble:
                predictions, confidence = self.pipeline.predict_with_ensemble(features)
            else:
                predictions = self.pipeline.predict(features)
                confidence = np.ones(len(predictions))
            
            # Generate signals
            signals = self._generate_signals(predictions, confidence)
            
            result = {
                'status': 'success',
                'timestamp': timestamp.isoformat(),
                'n_samples': len(predictions),
                'predictions': predictions.tolist(),
                'confidence': confidence.tolist(),
                'signals': signals,
                'model_used': self.pipeline.best_model_name if not use_ensemble else 'ensemble'
            }
            
            # Store in history
            self.prediction_history.append({
                'timestamp': timestamp,
                'n_samples': len(predictions)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _generate_signals(
        self,
        predictions: np.ndarray,
        confidence: np.ndarray
    ) -> List[Dict]:
        """Generate trading signals from predictions."""
        signals = []
        
        for i, (pred, conf) in enumerate(zip(predictions, confidence)):
            if pred >= 0.65 and conf >= 0.6:
                signal_type = 'strong_buy'
            elif pred >= 0.55:
                signal_type = 'buy'
            elif pred <= 0.35 and conf >= 0.6:
                signal_type = 'strong_sell'
            elif pred <= 0.45:
                signal_type = 'sell'
            else:
                signal_type = 'neutral'
            
            signals.append({
                'index': i,
                'signal': signal_type,
                'probability': float(pred),
                'confidence': float(conf)
            })
        
        return signals


def create_training_pipeline(config: Dict = None) -> TrainingPipeline:
    """Factory function for training pipeline."""
    return TrainingPipeline(config)


if __name__ == "__main__":
    # Test pipeline
    np.random.seed(42)
    n_samples = 1000
    n_features = 20
    
    # Create sample features
    X = np.random.randn(n_samples, n_features)
    y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1 > 0).astype(int)
    
    features = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
    features['target'] = y
    
    # Initialize and run pipeline
    pipeline = TrainingPipeline()
    
    # Prepare data
    data = pipeline.prepare_data(features)
    
    print("Data prepared:")
    for key, (X, y) in data.items():
        print(f"  {key}: X={X.shape}, y={len(y)}")
    
    # Train models
    results = pipeline.train_all_models(data)
    
    print("\nTraining Results:")
    for model, result in results.items():
        if result['status'] == 'success':
            print(f"  {model}: AUC={result['test_metrics'].get('auc', 'N/A'):.4f}")
        else:
            print(f"  {model}: {result['status']}")
    
    # Get summary
    summary = pipeline.get_pipeline_summary()
    print(f"\nPipeline Summary:")
    print(f"  Best model: {summary['best_model']}")
    print(f"  Trained models: {summary['trained_models']}")
