"""
ML Features Module
Feature engineering for machine learning models
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger


class FeatureBuilder:
    """Builds features for ML models."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("FeatureBuilder initialized")
    
    def build_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Build price-based features."""
        df = data.copy()
        
        # Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50, 100, 200]:
            if len(df) >= period:
                df[f'sma_{period}'] = df['close'].rolling(period).mean()
                df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # Price relative to MAs
        for period in [20, 50, 200]:
            if f'sma_{period}' in df:
                df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
        
        return df
    
    def build_volatility_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Build volatility-based features."""
        df = data.copy()
        
        if 'returns' not in df:
            df['returns'] = df['close'].pct_change()
        
        # Rolling volatility
        for period in [5, 10, 20]:
            df[f'volatility_{period}'] = df['returns'].rolling(period).std()
        
        # ATR
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr_14'] = df['tr'].rolling(14).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        df['bb_std'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def build_momentum_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Build momentum-based features."""
        df = data.copy()
        
        # Momentum
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] - df['close'].shift(period)
            df[f'roc_{period}'] = df['close'].pct_change(period) * 100
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Stochastic
        low_14 = df['low'].rolling(14).min()
        high_14 = df['high'].rolling(14).max()
        df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        
        return df
    
    def build_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Build volume-based features."""
        df = data.copy()
        
        if 'volume' not in df:
            return df
        
        # Volume averages
        for period in [5, 10, 20]:
            df[f'vol_sma_{period}'] = df['volume'].rolling(period).mean()
        
        # Volume ratio
        df['vol_ratio'] = df['volume'] / df['vol_sma_20']
        
        # OBV
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        
        # Money Flow
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['money_flow'] = df['typical_price'] * df['volume']
        
        return df
    
    def build_trend_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Build trend-based features."""
        df = data.copy()
        
        # ADX
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = np.maximum(df['high'] - df['low'],
                       np.maximum(abs(df['high'] - df['close'].shift(1)),
                                 abs(df['low'] - df['close'].shift(1))))
        
        atr = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(14).mean()
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        
        # Trend direction
        df['trend'] = np.where(df.get('sma_20', df['close']) > df.get('sma_50', df['close']), 1, -1)
        
        return df
    
    def build_all_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Build all features."""
        df = data.copy()
        
        df = self.build_price_features(df)
        df = self.build_volatility_features(df)
        df = self.build_momentum_features(df)
        df = self.build_volume_features(df)
        df = self.build_trend_features(df)
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names."""
        return [
            'returns', 'log_returns',
            'sma_5', 'sma_10', 'sma_20', 'sma_50',
            'ema_5', 'ema_10', 'ema_20',
            'volatility_5', 'volatility_10', 'volatility_20',
            'atr_14', 'bb_position',
            'momentum_5', 'momentum_10', 'momentum_20',
            'roc_5', 'roc_10', 'roc_20',
            'rsi_14', 'macd', 'macd_signal', 'macd_hist',
            'stoch_k', 'stoch_d',
            'vol_ratio', 'adx', 'trend'
        ]


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
    
    builder = FeatureBuilder()
    features = builder.build_all_features(data)
    print(f"Built {len(features.columns)} features")
    print(f"Sample features: {features.columns[:10].tolist()}")
