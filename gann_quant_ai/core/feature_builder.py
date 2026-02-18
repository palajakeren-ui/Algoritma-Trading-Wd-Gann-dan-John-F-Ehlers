import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, List, Optional

class FeatureBuilder:
    """
    Constructs a feature set for machine learning models from various data sources.
    """
    def __init__(self, config: Dict):
        self.config = config
        self.ml_config = config.get("ml_config", {}).get("feature_engineering", {})
        logger.info("FeatureBuilder initialized.")

    def build_features(
        self,
        price_data: pd.DataFrame,
        gann_levels: Optional[Dict[str, List[float]]],
        astro_events: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Creates a comprehensive feature DataFrame for the ML model.

        Args:
            price_data (pd.DataFrame): DataFrame with OHLCV and other indicators (like Ehlers).
            gann_levels (Optional[Dict[str, List[float]]]): Gann support/resistance levels.
            astro_events (Optional[pd.DataFrame]): DataFrame of astrological events.

        Returns:
            pd.DataFrame: A DataFrame with features and a target variable.
        """
        logger.info("Building features for ML model...")
        features = price_data.copy()

        # 1. Price-based features
        for n in [5, 10, 20, 60]:
            features[f'return_{n}d'] = features['close'].pct_change(n)
        features['rsi'] = self._calculate_rsi(features['close'])

        # 2. Ehlers features (already in the DataFrame)
        # Ensure they exist to avoid errors
        if 'fisher' not in features.columns:
            features['fisher'] = 0

        # 3. Gann features
        if gann_levels:
            features['dist_to_gann_sup'] = self._dist_to_nearest_level(features['close'], gann_levels['support'])
            features['dist_to_gann_res'] = self._dist_to_nearest_level(features['close'], gann_levels['resistance'])
        else:
            features['dist_to_gann_sup'] = np.nan
            features['dist_to_gann_res'] = np.nan

        # 4. Astro features
        if astro_events is not None and not astro_events.empty:
            features['is_astro_event'] = 0
            features.loc[astro_events.index, 'is_astro_event'] = 1
        else:
            features['is_astro_event'] = 0

        # 5. Target variable
        target_period = self.ml_config.get("target_period", 5)
        features['target'] = (features['close'].shift(-target_period) > features['close']).astype(int)

        # 6. Cleanup
        # Drop original OHLCV and select feature columns
        feature_cols = [
            'return_5d', 'return_10d', 'return_20d', 'return_60d', 'rsi',
            'fisher', 'dist_to_gann_sup', 'dist_to_gann_res', 'is_astro_event', 'target'
        ]
        # Keep only columns that were successfully created
        final_cols = [col for col in feature_cols if col in features.columns]
        features = features[final_cols]
        features.dropna(inplace=True)

        logger.success(f"Feature building complete. Shape: {features.shape}")
        return features

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _dist_to_nearest_level(self, prices: pd.Series, levels: List[float]) -> pd.Series:
        """Calculates normalized distance to the nearest Gann level."""
        if not levels:
            return pd.Series(np.nan, index=prices.index)

        dist_matrix = pd.DataFrame({level: (prices - level) / prices for level in levels})
        return dist_matrix.abs().min(axis=1)
