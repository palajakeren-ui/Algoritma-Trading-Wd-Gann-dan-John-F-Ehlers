"""
Feature Fusion Engine
Combines Gann, Astrology, and Ehlers DSP features into a unified ML feature set.

This module is the central integration point that fuses multiple analysis
domains into production-ready ML features.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


class FeatureFusionEngine:
    """
    Feature Fusion Engine for ML model input.
    
    Combines:
    - Gann features (Square of 9, angles, time cycles)
    - Astrology features (planetary positions, aspects, synodic cycles)
    - Ehlers DSP features (MAMA, Fisher, bandpass, etc.)
    - Technical features (price-based indicators)
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Feature Fusion Engine.
        
        Args:
            config (Dict): Configuration dictionary
        """
        self.config = config or {}
        self.feature_config = self.config.get('feature_fusion', {})
        self.feature_names = []
        self.feature_stats = {}
        
        # Feature category flags
        self.use_gann = self.feature_config.get('use_gann', True)
        self.use_astro = self.feature_config.get('use_astro', True)
        self.use_ehlers = self.feature_config.get('use_ehlers', True)
        self.use_technical = self.feature_config.get('use_technical', True)
        
        logger.info("FeatureFusionEngine initialized")
    
    def build_features(
        self,
        price_data: pd.DataFrame,
        gann_data: Optional[Dict] = None,
        astro_data: Optional[pd.DataFrame] = None,
        ehlers_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Build comprehensive feature set from multiple data sources.
        
        Args:
            price_data (pd.DataFrame): OHLCV price data
            gann_data (Dict): Gann analysis results
            astro_data (pd.DataFrame): Astrology analysis data
            ehlers_data (pd.DataFrame): Ehlers indicator data
            
        Returns:
            pd.DataFrame: Fused feature DataFrame
        """
        logger.info(f"Building fused features for {len(price_data)} samples")
        
        features = price_data.copy()
        features_added = []
        
        # 1. Technical Features (always calculated)
        if self.use_technical:
            tech_features = self._build_technical_features(price_data)
            features = features.join(tech_features)
            features_added.extend(tech_features.columns.tolist())
        
        # 2. Gann Features
        if self.use_gann and gann_data is not None:
            gann_features = self._build_gann_features(price_data, gann_data)
            features = features.join(gann_features)
            features_added.extend(gann_features.columns.tolist())
        
        # 3. Astrology Features
        if self.use_astro and astro_data is not None:
            astro_features = self._build_astro_features(price_data, astro_data)
            features = features.join(astro_features)
            features_added.extend(astro_features.columns.tolist())
        
        # 4. Ehlers DSP Features
        if self.use_ehlers and ehlers_data is not None:
            ehlers_features = self._build_ehlers_features(ehlers_data)
            features = features.join(ehlers_features)
            features_added.extend(ehlers_features.columns.tolist())
        
        # 5. Interaction Features
        interaction_features = self._build_interaction_features(features)
        features = features.join(interaction_features)
        features_added.extend(interaction_features.columns.tolist())
        
        # 6. Target Variable
        target = self._build_target(price_data)
        features['target'] = target
        
        # Store feature names
        self.feature_names = features_added
        
        # Clean up
        features = self._clean_features(features)
        
        logger.success(f"Built {len(features_added)} features, final shape: {features.shape}")
        
        return features
    
    def _build_technical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Build technical analysis features."""
        result = pd.DataFrame(index=data.index)
        
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data.get('volume', pd.Series(0, index=data.index))
        
        # Returns
        for period in [1, 3, 5, 10, 20, 60]:
            result[f'return_{period}d'] = close.pct_change(period)
        
        # Volatility
        for period in [10, 20, 60]:
            result[f'volatility_{period}d'] = close.pct_change().rolling(period).std()
        
        # Price position
        for period in [20, 50, 100]:
            result[f'price_position_{period}d'] = (close - close.rolling(period).min()) / \
                                                   (close.rolling(period).max() - close.rolling(period).min() + 1e-8)
        
        # Moving averages
        for period in [10, 20, 50, 100]:
            ma = close.rolling(period).mean()
            result[f'dist_from_ma_{period}'] = (close - ma) / ma
        
        # RSI
        result['rsi_14'] = self._calculate_rsi(close, 14)
        result['rsi_7'] = self._calculate_rsi(close, 7)
        
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        result['macd'] = ema12 - ema26
        result['macd_signal'] = result['macd'].ewm(span=9).mean()
        result['macd_histogram'] = result['macd'] - result['macd_signal']
        
        # Bollinger Bands
        bb_ma = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        result['bb_upper_dist'] = (close - (bb_ma + 2 * bb_std)) / close
        result['bb_lower_dist'] = (close - (bb_ma - 2 * bb_std)) / close
        result['bb_width'] = (4 * bb_std) / bb_ma
        
        # ATR
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift()),
            'lc': abs(low - close.shift())
        }).max(axis=1)
        result['atr_14'] = tr.rolling(14).mean() / close
        
        # Volume features
        if volume.sum() > 0:
            result['volume_ma_ratio'] = volume / volume.rolling(20).mean()
            result['volume_trend'] = volume.rolling(5).mean() / volume.rolling(20).mean()
        
        # Price patterns (simple)
        result['higher_high'] = (high > high.shift(1)).astype(int)
        result['lower_low'] = (low < low.shift(1)).astype(int)
        result['inside_bar'] = ((high < high.shift(1)) & (low > low.shift(1))).astype(int)
        
        return result
    
    def _build_gann_features(self, price_data: pd.DataFrame, gann_data: Dict) -> pd.DataFrame:
        """Build Gann-based features."""
        result = pd.DataFrame(index=price_data.index)
        close = price_data['close']
        
        # Distance to Gann levels
        support_levels = gann_data.get('support', [])
        resistance_levels = gann_data.get('resistance', [])
        
        if support_levels:
            result['dist_nearest_gann_support'] = self._distance_to_levels(close, support_levels, 'below')
            result['n_gann_supports_nearby'] = self._count_levels_nearby(close, support_levels, threshold=0.02)
        else:
            result['dist_nearest_gann_support'] = 0
            result['n_gann_supports_nearby'] = 0
        
        if resistance_levels:
            result['dist_nearest_gann_resistance'] = self._distance_to_levels(close, resistance_levels, 'above')
            result['n_gann_resistances_nearby'] = self._count_levels_nearby(close, resistance_levels, threshold=0.02)
        else:
            result['dist_nearest_gann_resistance'] = 0
            result['n_gann_resistances_nearby'] = 0
        
        # Gann angle features
        if 'angles' in gann_data:
            angles = gann_data['angles']
            for angle_name in ['1x1_up', '1x2_up', '2x1_up', '1x1_down']:
                if angle_name in angles:
                    result[f'dist_gann_{angle_name}'] = (close - angles[angle_name]) / close
        
        # Time cycle features
        if 'time_cycles' in gann_data:
            tc = gann_data['time_cycles']
            result['days_to_cycle'] = tc.get('days_to_next', 0)
            result['cycle_significance'] = tc.get('significance', 0.5)
        
        # Square of 9 position
        if 'sq9_position' in gann_data:
            result['sq9_angle'] = gann_data['sq9_position'].get('angle', 0) / 360
            result['sq9_ring'] = gann_data['sq9_position'].get('ring', 0)
        
        return result
    
    def _build_astro_features(self, price_data: pd.DataFrame, astro_data: pd.DataFrame) -> pd.DataFrame:
        """Build astrology-based features."""
        result = pd.DataFrame(index=price_data.index)
        
        # Align astro data with price data
        if astro_data is not None and not astro_data.empty:
            # Presence of aspects
            result['has_major_aspect'] = 0
            result['has_any_aspect'] = 0
            
            for idx in astro_data.index:
                if idx in result.index:
                    result.loc[idx, 'has_any_aspect'] = 1
                    if 'significance' in astro_data.columns:
                        if astro_data.loc[idx, 'significance'] == 'major':
                            result.loc[idx, 'has_major_aspect'] = 1
            
            # Aspect type encoding
            aspect_types = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
            for aspect_type in aspect_types:
                result[f'aspect_{aspect_type}'] = 0
                if 'aspect_type' in astro_data.columns:
                    matching = astro_data[astro_data['aspect_type'] == aspect_type].index
                    for idx in matching:
                        if idx in result.index:
                            result.loc[idx, f'aspect_{aspect_type}'] = 1
            
            # Retrograde features
            for planet in ['mercury', 'venus', 'mars']:
                col = f'{planet}_retrograde'
                if col in astro_data.columns:
                    result[col] = 0
                    for idx in astro_data.index:
                        if idx in result.index:
                            result.loc[idx, col] = astro_data.loc[idx, col] if pd.notna(astro_data.loc[idx, col]) else 0
        else:
            # Default zero features
            result['has_major_aspect'] = 0
            result['has_any_aspect'] = 0
            for aspect_type in ['conjunction', 'opposition', 'trine', 'square', 'sextile']:
                result[f'aspect_{aspect_type}'] = 0
        
        # Moon phase (approximated)
        result['moon_phase'] = self._approximate_moon_phase(price_data.index)
        
        return result
    
    def _build_ehlers_features(self, ehlers_data: pd.DataFrame) -> pd.DataFrame:
        """Build Ehlers DSP features."""
        result = pd.DataFrame(index=ehlers_data.index)
        
        # Select relevant Ehlers columns
        ehlers_cols = [
            'fisher', 'fisher_signal',
            'mama', 'fama',
            'cyber_cycle', 'cyber_cycle_signal',
            'bandpass', 'bp_trigger',
            'smoothed_rsi', 'laguerre_rsi',
            'itrend', 'itrend_trigger',
            'hilbert_period', 'hilbert_phase',
            'decycler', 'decycler_roc'
        ]
        
        for col in ehlers_cols:
            if col in ehlers_data.columns:
                result[f'ehlers_{col}'] = ehlers_data[col]
        
        # Derived Ehlers features
        if 'fisher' in ehlers_data.columns and 'fisher_signal' in ehlers_data.columns:
            result['ehlers_fisher_cross'] = (
                ehlers_data['fisher'] > ehlers_data['fisher_signal']
            ).astype(int)
        
        if 'mama' in ehlers_data.columns and 'fama' in ehlers_data.columns:
            result['ehlers_mama_cross'] = (
                ehlers_data['mama'] > ehlers_data['fama']
            ).astype(int)
            result['ehlers_mama_fama_diff'] = (
                ehlers_data['mama'] - ehlers_data['fama']
            ) / (ehlers_data['mama'].abs() + 1e-8)
        
        if 'itrend' in ehlers_data.columns and 'close' in ehlers_data.columns:
            result['ehlers_itrend_position'] = (
                ehlers_data['close'] - ehlers_data['itrend']
            ) / ehlers_data['close']
        
        return result
    
    def _build_interaction_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Build interaction features between different domains."""
        result = pd.DataFrame(index=features.index)
        
        # Gann + Technical interactions
        if 'dist_nearest_gann_support' in features.columns and 'rsi_14' in features.columns:
            result['gann_support_rsi'] = features['dist_nearest_gann_support'] * (features['rsi_14'] - 50) / 50
        
        if 'dist_nearest_gann_resistance' in features.columns and 'rsi_14' in features.columns:
            result['gann_resistance_rsi'] = features['dist_nearest_gann_resistance'] * (features['rsi_14'] - 50) / 50
        
        # Gann + Ehlers interactions
        if 'dist_nearest_gann_support' in features.columns:
            for ehlers_col in ['ehlers_fisher', 'ehlers_mama']:
                if ehlers_col in features.columns:
                    result[f'gann_support_{ehlers_col}'] = features['dist_nearest_gann_support'] * features[ehlers_col]
        
        # Astro + Technical interactions
        if 'has_major_aspect' in features.columns:
            if 'volatility_20d' in features.columns:
                result['astro_volatility'] = features['has_major_aspect'] * features['volatility_20d']
            if 'return_5d' in features.columns:
                result['astro_momentum'] = features['has_major_aspect'] * features['return_5d']
        
        # Ehlers + Technical interactions
        if 'ehlers_hilbert_period' in features.columns and 'volatility_20d' in features.columns:
            result['cycle_volatility'] = features['ehlers_hilbert_period'] * features['volatility_20d']
        
        # Trend agreement feature
        trend_signals = []
        if 'dist_from_ma_20' in features.columns:
            trend_signals.append((features['dist_from_ma_20'] > 0).astype(int))
        if 'ehlers_itrend_position' in features.columns:
            trend_signals.append((features['ehlers_itrend_position'] > 0).astype(int))
        if 'macd_histogram' in features.columns:
            trend_signals.append((features['macd_histogram'] > 0).astype(int))
        
        if trend_signals:
            result['trend_agreement'] = sum(trend_signals) / len(trend_signals)
        
        return result
    
    def _build_target(self, price_data: pd.DataFrame, periods: int = 5) -> pd.Series:
        """Build target variable."""
        target_type = self.feature_config.get('target_type', 'direction')
        
        if target_type == 'direction':
            # Binary: 1 if price goes up, 0 otherwise
            return (price_data['close'].shift(-periods) > price_data['close']).astype(int)
        elif target_type == 'return':
            # Continuous return
            return price_data['close'].pct_change(periods).shift(-periods)
        else:
            return (price_data['close'].shift(-periods) > price_data['close']).astype(int)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / (loss + 1e-8)
        return 100 - (100 / (1 + rs))
    
    def _distance_to_levels(
        self,
        prices: pd.Series,
        levels: List[float],
        direction: str = 'both'
    ) -> pd.Series:
        """Calculate distance to nearest level."""
        result = pd.Series(np.nan, index=prices.index)
        
        for i, price in enumerate(prices):
            if direction == 'above':
                candidates = [l for l in levels if l > price]
            elif direction == 'below':
                candidates = [l for l in levels if l < price]
            else:
                candidates = levels
            
            if candidates:
                distances = [abs(price - l) / price for l in candidates]
                result.iloc[i] = min(distances)
            else:
                result.iloc[i] = 0.1  # Default distance
        
        return result
    
    def _count_levels_nearby(
        self,
        prices: pd.Series,
        levels: List[float],
        threshold: float = 0.02
    ) -> pd.Series:
        """Count number of levels within threshold distance."""
        result = pd.Series(0, index=prices.index)
        
        for i, price in enumerate(prices):
            count = sum(1 for l in levels if abs(price - l) / price < threshold)
            result.iloc[i] = count
        
        return result
    
    def _approximate_moon_phase(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Approximate moon phase (0-1 cycle)."""
        known_new_moon = datetime(2000, 1, 6)  # Reference new moon
        synodic_month = 29.530588853  # Days
        
        phases = []
        for date in dates:
            if hasattr(date, 'to_pydatetime'):
                date = date.to_pydatetime()
            elif isinstance(date, np.datetime64):
                date = pd.Timestamp(date).to_pydatetime()
            
            try:
                days_since = (date - known_new_moon).days
                phase = (days_since % synodic_month) / synodic_month
                phases.append(phase)
            except:
                phases.append(0.5)
        
        return pd.Series(phases, index=dates)
    
    def _clean_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate features."""
        # Replace infinities
        features = features.replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN with forward/backward fill, then zero
        features = features.ffill().bfill().fillna(0)
        
        # Clip extreme values
        for col in features.columns:
            if col != 'target' and features[col].dtype in ['float64', 'float32']:
                q1, q99 = features[col].quantile([0.01, 0.99])
                features[col] = features[col].clip(q1, q99)
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names."""
        return self.feature_names
    
    def get_feature_importance_proxy(self, features: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """Calculate proxy importance using correlation."""
        importance = {}
        
        for col in features.columns:
            if col != 'target':
                try:
                    corr = features[col].corr(target)
                    importance[col] = abs(corr) if not np.isnan(corr) else 0
                except:
                    importance[col] = 0
        
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


def create_fused_features(
    price_data: pd.DataFrame,
    gann_data: Dict = None,
    astro_data: pd.DataFrame = None,
    ehlers_data: pd.DataFrame = None,
    config: Dict = None
) -> pd.DataFrame:
    """
    Convenience function to create fused features.
    
    Args:
        price_data (pd.DataFrame): OHLCV data
        gann_data (Dict): Gann analysis results
        astro_data (pd.DataFrame): Astrology data
        ehlers_data (pd.DataFrame): Ehlers indicators
        config (Dict): Configuration
        
    Returns:
        pd.DataFrame: Fused features
    """
    engine = FeatureFusionEngine(config)
    return engine.build_features(price_data, gann_data, astro_data, ehlers_data)


if __name__ == "__main__":
    # Test
    np.random.seed(42)
    n = 200
    
    # Create sample price data
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    price_data = pd.DataFrame({
        'open': close - 0.3,
        'high': close + 0.5,
        'low': close - 0.5,
        'close': close,
        'volume': np.random.randint(1000, 10000, n)
    }, index=pd.date_range('2023-01-01', periods=n))
    
    # Sample Gann data
    gann_data = {
        'support': [95.0, 90.0, 85.0],
        'resistance': [105.0, 110.0, 115.0]
    }
    
    # Build features
    engine = FeatureFusionEngine()
    features = engine.build_features(price_data, gann_data)
    
    print(f"Built features shape: {features.shape}")
    print(f"\nFeature columns ({len(features.columns)}):")
    for col in features.columns[:20]:
        print(f"  {col}: {features[col].dtype}")
    
    print(f"\nSample of fused features:")
    print(features.head(5))
