"""
ML Time Forecast Module
Machine learning based time series forecasting
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass 
class TimeForecast:
    target_date: datetime
    predicted_price: float
    predicted_high: float
    predicted_low: float
    confidence: float
    direction: str
    features_used: List[str]


class MLTimeForecaster:
    """ML-based time series forecaster using statistical methods."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.lookback = self.config.get('lookback', 20)
        self.forecast_horizon = self.config.get('horizon', 5)
        logger.info("MLTimeForecaster initialized")
    
    def calculate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical features for forecasting."""
        df = data.copy()
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # Volatility
        df['volatility_10'] = df['returns'].rolling(10).std()
        df['volatility_20'] = df['returns'].rolling(20).std()
        
        # Range features
        df['daily_range'] = df['high'] - df['low']
        df['avg_range'] = df['daily_range'].rolling(20).mean()
        
        # Momentum
        df['momentum_5'] = df['close'] - df['close'].shift(5)
        df['momentum_10'] = df['close'] - df['close'].shift(10)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Trend
        df['trend'] = np.where(df['sma_10'] > df['sma_20'], 1, -1)
        
        return df.dropna()
    
    def predict_arima_simple(self, series: pd.Series, steps: int = 5) -> np.ndarray:
        """Simple AR prediction."""
        n = len(series)
        if n < 20:
            return np.full(steps, series.iloc[-1])
        
        # Fit AR(5) model using OLS
        y = series.values[5:]
        X = np.column_stack([series.values[5-i:-i] for i in range(1, 6)])
        
        try:
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
        except:
            return np.full(steps, series.iloc[-1])
        
        # Predict
        predictions = []
        last_values = list(series.values[-5:])
        
        for _ in range(steps):
            pred = np.dot(coeffs, last_values[::-1])
            predictions.append(pred)
            last_values.pop(0)
            last_values.append(pred)
        
        return np.array(predictions)
    
    def predict_exponential_smoothing(self, series: pd.Series, steps: int = 5) -> np.ndarray:
        """Holt-Winters exponential smoothing."""
        alpha = 0.3  # Level smoothing
        beta = 0.1   # Trend smoothing
        
        n = len(series)
        level = series.iloc[0]
        trend = (series.iloc[-1] - series.iloc[0]) / n
        
        for val in series.values[1:]:
            prev_level = level
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
        
        predictions = []
        for i in range(steps):
            predictions.append(level + (i + 1) * trend)
        
        return np.array(predictions)
    
    def ensemble_predict(self, data: pd.DataFrame, steps: int = 5) -> np.ndarray:
        """Ensemble prediction combining multiple methods."""
        close = data['close']
        
        # Get predictions from each method
        ar_pred = self.predict_arima_simple(close, steps)
        es_pred = self.predict_exponential_smoothing(close, steps)
        
        # Simple average ensemble
        ensemble = (ar_pred + es_pred) / 2
        
        return ensemble
    
    def calculate_confidence(self, data: pd.DataFrame, predictions: np.ndarray) -> float:
        """Calculate prediction confidence."""
        # Base confidence on volatility and trend consistency
        volatility = data['close'].pct_change().std()
        
        # Lower volatility = higher confidence
        vol_score = max(0.3, 1 - volatility * 10)
        
        # Check trend consistency
        sma_10 = data['close'].rolling(10).mean().iloc[-1]
        sma_20 = data['close'].rolling(20).mean().iloc[-1]
        trend_consistent = (sma_10 > sma_20 and predictions.mean() > data['close'].iloc[-1]) or \
                          (sma_10 < sma_20 and predictions.mean() < data['close'].iloc[-1])
        
        trend_score = 0.7 if trend_consistent else 0.5
        
        return min(0.9, (vol_score + trend_score) / 2)
    
    def forecast(
        self,
        data: pd.DataFrame,
        steps: int = None
    ) -> List[TimeForecast]:
        """
        Generate time series forecast.
        
        Args:
            data: OHLCV DataFrame
            steps: Number of periods to forecast
            
        Returns:
            List of TimeForecast objects
        """
        if steps is None:
            steps = self.forecast_horizon
        
        # Calculate features
        df = self.calculate_features(data)
        
        # Get predictions
        predictions = self.ensemble_predict(df, steps)
        
        # Calculate uncertainty ranges
        volatility = df['volatility_20'].iloc[-1] if 'volatility_20' in df else 0.02
        
        # Calculate confidence
        confidence = self.calculate_confidence(df, predictions)
        
        # Determine direction
        current_price = df['close'].iloc[-1]
        direction = 'bullish' if predictions.mean() > current_price else 'bearish'
        
        # Generate forecasts
        forecasts = []
        last_date = df.index[-1]
        
        for i, pred in enumerate(predictions):
            target_date = last_date + timedelta(days=i + 1)
            
            # Calculate high/low based on volatility
            range_pct = volatility * 2
            pred_high = pred * (1 + range_pct)
            pred_low = pred * (1 - range_pct)
            
            forecasts.append(TimeForecast(
                target_date=target_date if isinstance(target_date, datetime) else target_date.to_pydatetime(),
                predicted_price=round(pred, 2),
                predicted_high=round(pred_high, 2),
                predicted_low=round(pred_low, 2),
                confidence=round(confidence - i * 0.05, 2),  # Confidence decreases
                direction=direction,
                features_used=['sma', 'ema', 'rsi', 'macd', 'momentum']
            ))
        
        return forecasts
    
    def forecast_summary(self, data: pd.DataFrame, steps: int = 5) -> Dict:
        """Get forecast summary as dictionary."""
        forecasts = self.forecast(data, steps)
        
        if not forecasts:
            return {'status': 'error', 'message': 'No forecasts generated'}
        
        return {
            'status': 'success',
            'current_price': float(data['close'].iloc[-1]),
            'forecast_direction': forecasts[0].direction,
            'avg_confidence': np.mean([f.confidence for f in forecasts]),
            'forecasts': [
                {
                    'date': f.target_date.strftime('%Y-%m-%d'),
                    'price': f.predicted_price,
                    'high': f.predicted_high,
                    'low': f.predicted_low,
                    'confidence': f.confidence
                }
                for f in forecasts
            ]
        }


if __name__ == "__main__":
    # Test with sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1D')
    np.random.seed(42)
    
    price = 50000
    prices = [price]
    for _ in range(99):
        price = price * (1 + np.random.randn() * 0.015)
        prices.append(price)
    
    data = pd.DataFrame({
        'open': [p * 0.998 for p in prices],
        'high': [p * 1.015 for p in prices],
        'low': [p * 0.985 for p in prices],
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 100)
    }, index=dates)
    
    forecaster = MLTimeForecaster()
    result = forecaster.forecast_summary(data)
    
    print(f"\n=== ML Time Forecast ===")
    print(f"Current: {result['current_price']:.0f}")
    print(f"Direction: {result['forecast_direction']}")
    for f in result['forecasts']:
        print(f"  {f['date']}: {f['price']:.0f} ({f['confidence']:.0%})")
