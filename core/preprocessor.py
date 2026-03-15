"""
Data Preprocessor Module
Data cleaning, normalization, and feature engineering
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler


class Preprocessor:
    """
    Data preprocessing utilities for price and feature data.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize preprocessor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.scalers: Dict[str, StandardScaler] = {}
        logger.info("Preprocessor initialized")
    
    def clean_ohlc_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate OHLC data.
        
        Args:
            df: DataFrame with OHLC columns
            
        Returns:
            Cleaned DataFrame
        """
        result = df.copy()
        
        # Standardize column names
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume',
            'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low',
            'CLOSE': 'close', 'VOLUME': 'volume'
        }
        result = result.rename(columns=column_mapping)
        
        # Remove duplicates
        result = result[~result.index.duplicated(keep='first')]
        
        # Handle missing values
        result = result.ffill().bfill()
        
        # Fix OHLC logic (high >= max(open, close), low <= min(open, close))
        result['high'] = result[['open', 'high', 'close']].max(axis=1)
        result['low'] = result[['open', 'low', 'close']].min(axis=1)
        
        # Remove zero/negative prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in result.columns:
                result = result[result[col] > 0]
        
        # Sort by index
        result = result.sort_index()
        
        logger.info(f"Cleaned data: {len(result)} rows, columns: {list(result.columns)}")
        return result
    
    def add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add common technical features.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with added features
        """
        result = df.copy()
        
        # Returns
        result['returns'] = result['close'].pct_change()
        result['log_returns'] = np.log(result['close'] / result['close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50, 200]:
            result[f'sma_{period}'] = result['close'].rolling(window=period).mean()
            result[f'ema_{period}'] = result['close'].ewm(span=period, adjust=False).mean()
        
        # Volatility
        result['volatility_20'] = result['returns'].rolling(window=20).std() * np.sqrt(252)
        result['atr_14'] = self._calculate_atr(result, period=14)
        
        # Momentum
        result['momentum_10'] = result['close'] / result['close'].shift(10) - 1
        result['rsi_14'] = self._calculate_rsi(result['close'], period=14)
        
        # Volume features
        if 'volume' in result.columns:
            result['volume_sma_20'] = result['volume'].rolling(window=20).mean()
            result['volume_ratio'] = result['volume'] / result['volume_sma_20']
        
        # Price position
        result['price_position'] = (result['close'] - result['low']) / (result['high'] - result['low'])
        
        # Range
        result['range'] = result['high'] - result['low']
        result['range_pct'] = result['range'] / result['close'] * 100
        
        # Gap
        result['gap'] = result['open'] - result['close'].shift(1)
        result['gap_pct'] = result['gap'] / result['close'].shift(1) * 100
        
        logger.info(f"Added technical features. Total columns: {len(result.columns)}")
        return result
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def normalize_features(
        self, 
        df: pd.DataFrame, 
        columns: List[str] = None,
        method: str = 'standard'
    ) -> pd.DataFrame:
        """
        Normalize features.
        
        Args:
            df: DataFrame
            columns: Columns to normalize (default: all numeric)
            method: 'standard', 'minmax', or 'robust'
            
        Returns:
            DataFrame with normalized features
        """
        result = df.copy()
        
        if columns is None:
            columns = result.select_dtypes(include=[np.number]).columns.tolist()
        
        # Select scaler
        if method == 'standard':
            scaler_class = StandardScaler
        elif method == 'minmax':
            scaler_class = MinMaxScaler
        elif method == 'robust':
            scaler_class = RobustScaler
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        for col in columns:
            if col in result.columns and not result[col].isna().all():
                scaler = scaler_class()
                values = result[col].values.reshape(-1, 1)
                result[col] = scaler.fit_transform(values).flatten()
                self.scalers[col] = scaler
        
        logger.info(f"Normalized {len(columns)} columns using {method} method")
        return result
    
    def create_lag_features(
        self, 
        df: pd.DataFrame, 
        columns: List[str], 
        lags: List[int]
    ) -> pd.DataFrame:
        """
        Create lagged features.
        
        Args:
            df: DataFrame
            columns: Columns to create lags for
            lags: List of lag periods
            
        Returns:
            DataFrame with lag features
        """
        result = df.copy()
        
        for col in columns:
            if col in result.columns:
                for lag in lags:
                    result[f'{col}_lag_{lag}'] = result[col].shift(lag)
        
        logger.info(f"Created {len(columns) * len(lags)} lag features")
        return result
    
    def create_rolling_features(
        self, 
        df: pd.DataFrame, 
        columns: List[str], 
        windows: List[int],
        functions: List[str] = ['mean', 'std', 'min', 'max']
    ) -> pd.DataFrame:
        """
        Create rolling window features.
        
        Args:
            df: DataFrame
            columns: Columns to process
            windows: Rolling window sizes
            functions: Aggregation functions
            
        Returns:
            DataFrame with rolling features
        """
        result = df.copy()
        
        for col in columns:
            if col in result.columns:
                for window in windows:
                    for func in functions:
                        result[f'{col}_roll_{window}_{func}'] = getattr(
                            result[col].rolling(window=window), func
                        )()
        
        logger.info(f"Created rolling features for {len(columns)} columns")
        return result
    
    def remove_outliers(
        self, 
        df: pd.DataFrame, 
        columns: List[str] = None,
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Remove or clip outliers.
        
        Args:
            df: DataFrame
            columns: Columns to check (default: all numeric)
            method: 'zscore' or 'iqr'
            threshold: Threshold for outlier detection
            
        Returns:
            DataFrame with outliers handled
        """
        result = df.copy()
        
        if columns is None:
            columns = result.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in columns:
            if col not in result.columns:
                continue
                
            if method == 'zscore':
                mean = result[col].mean()
                std = result[col].std()
                lower = mean - threshold * std
                upper = mean + threshold * std
            elif method == 'iqr':
                q1 = result[col].quantile(0.25)
                q3 = result[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
            else:
                continue
            
            result[col] = result[col].clip(lower=lower, upper=upper)
        
        logger.info(f"Handled outliers in {len(columns)} columns using {method} method")
        return result


# Example usage
if __name__ == '__main__':
    # Create dummy data
    dates = pd.date_range('2024-01-01', periods=100)
    df = pd.DataFrame({
        'Open': 100 + np.cumsum(np.random.randn(100)),
        'High': 102 + np.cumsum(np.random.randn(100)),
        'Low': 98 + np.cumsum(np.random.randn(100)),
        'Close': 100 + np.cumsum(np.random.randn(100)),
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    prep = Preprocessor()
    
    # Clean
    df = prep.clean_ohlc_data(df)
    
    # Add features
    df = prep.add_technical_features(df)
    
    print(f"Processed data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
