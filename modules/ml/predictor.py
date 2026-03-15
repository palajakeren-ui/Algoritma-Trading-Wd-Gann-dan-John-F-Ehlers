"""
ML Predictor Module
High-level prediction interface
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .features import FeatureBuilder
from .models import create_model, EnsembleModel


@dataclass
class PredictionResult:
    direction: str  # 'bullish', 'bearish', 'neutral'
    signal: int  # 1, -1, 0
    confidence: float
    probability: float
    predicted_return: float
    features_used: int


class MLPredictor:
    """High-level ML prediction interface."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.feature_builder = FeatureBuilder(config)
        self.model = create_model('ensemble', config)
        self.threshold = self.config.get('threshold', 0.55)
        logger.info("MLPredictor initialized")
    
    def prepare_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Prepare features from raw data."""
        df = self.feature_builder.build_all_features(data)
        
        # Select features
        feature_cols = [col for col in df.columns 
                       if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        # Drop NaN
        df_clean = df[feature_cols].dropna()
        
        return df_clean.values, feature_cols
    
    def train(self, data: pd.DataFrame, forward_returns: int = 5):
        """Train the model on historical data."""
        # Build features
        df = self.feature_builder.build_all_features(data)
        
        # Create target: future return direction
        df['target'] = (df['close'].shift(-forward_returns) / df['close'] - 1) > 0
        df['target'] = df['target'].astype(float)
        
        # Select features
        feature_cols = [col for col in df.columns 
                       if col not in ['open', 'high', 'low', 'close', 'volume', 'target']]
        
        # Clean data
        df_clean = df.dropna()
        
        if len(df_clean) < 50:
            logger.warning("Insufficient data for training")
            return False
        
        X = df_clean[feature_cols].values
        y = df_clean['target'].values
        
        # Train model
        self.model.train(X, y)
        
        logger.success(f"Model trained on {len(X)} samples with {len(feature_cols)} features")
        return True
    
    def predict(self, data: pd.DataFrame) -> PredictionResult:
        """Make prediction on current data."""
        if not self.model.is_trained:
            return PredictionResult(
                direction='neutral',
                signal=0,
                confidence=0.0,
                probability=0.5,
                predicted_return=0.0,
                features_used=0
            )
        
        # Build features
        df = self.feature_builder.build_all_features(data)
        
        feature_cols = [col for col in df.columns 
                       if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        # Get latest row
        latest = df[feature_cols].iloc[-1:].dropna(axis=1)
        
        if latest.empty:
            return PredictionResult(
                direction='neutral',
                signal=0,
                confidence=0.0,
                probability=0.5,
                predicted_return=0.0,
                features_used=0
            )
        
        X = latest.values
        
        # Predict
        prob = self.model.predict_proba(X)[0]
        bullish_prob = prob[1] if len(prob) > 1 else prob[0]
        
        # Determine direction
        if bullish_prob > self.threshold:
            direction = 'bullish'
            signal = 1
        elif bullish_prob < (1 - self.threshold):
            direction = 'bearish'
            signal = -1
        else:
            direction = 'neutral'
            signal = 0
        
        confidence = abs(bullish_prob - 0.5) * 2  # Scale to 0-1
        
        return PredictionResult(
            direction=direction,
            signal=signal,
            confidence=confidence,
            probability=bullish_prob,
            predicted_return=(bullish_prob - 0.5) * 0.1,
            features_used=len(latest.columns)
        )
    
    def batch_predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Make predictions for multiple periods."""
        results = []
        
        for i in range(50, len(data)):
            subset = data.iloc[:i+1]
            result = self.predict(subset)
            results.append(result)
        
        return results
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance (placeholder)."""
        return {name: np.random.rand() 
                for name in self.feature_builder.get_feature_names()[:10]}




if __name__ == "__main__":
    # Test
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1D')
    np.random.seed(42)
    
    price = 50000
    prices = [price]
    for _ in range(199):
        price = price * (1 + np.random.randn() * 0.015)
        prices.append(price)
    
    data = pd.DataFrame({
        'open': [p * 0.998 for p in prices],
        'high': [p * 1.015 for p in prices],
        'low': [p * 0.985 for p in prices],
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 200)
    }, index=dates)
    
    predictor = MLPredictor()
    predictor.train(data.iloc[:-20])
    
    result = predictor.predict(data)
    print(f"\nPrediction Result:")
    print(f"  Direction: {result.direction}")
    print(f"  Signal: {result.signal}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Probability: {result.probability:.2%}")
