"""
Gann Feature Engine
Production-grade Gann analysis feature extraction.

Extracts features from Gann theory for ML consumption:
- Square of 9 price levels
- Gann angles (1x1, 2x1, etc.)
- Time cycles (natural squares, planetary)
- Support/Resistance from Gann grid
- Vibration levels
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger


class GannFeatureEngine:
    """
    Extracts quantifiable features from Gann analysis.
    
    All outputs are normalized [-1, 1] or [0, 1] for ML compatibility.
    No mysticism — pure mathematical relationships.
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.sq9_levels = config.get("sq9_levels", 5)
        self.angle_periods = config.get("angle_periods", [45, 90, 120, 144, 180, 225, 270, 315, 360])
        self.cycle_lengths = config.get("cycle_lengths", [30, 60, 90, 120, 144, 180, 270, 360])
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all Gann features from OHLCV data.
        
        Returns DataFrame with Gann feature columns appended.
        """
        features = pd.DataFrame(index=df.index)
        
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        
        # 1. Square of 9 proximity
        sq9_features = self._square_of_9_features(close)
        for k, v in sq9_features.items():
            features[f"gann_sq9_{k}"] = v
        
        # 2. Gann angle features
        angle_features = self._gann_angle_features(close, high, low)
        for k, v in angle_features.items():
            features[f"gann_angle_{k}"] = v
        
        # 3. Time cycle features
        cycle_features = self._time_cycle_features(len(df))
        for k, v in cycle_features.items():
            features[f"gann_cycle_{k}"] = v[:len(df)]
        
        # 4. Price vibration (distance from natural squares)
        features["gann_vibration"] = self._price_vibration(close)
        
        # 5. Gann hexagon level proximity
        features["gann_hex_proximity"] = self._hexagon_proximity(close)
        
        logger.debug(f"Gann features computed: {len(features.columns)} features")
        return features
    
    def _square_of_9_features(self, close: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Square of 9: Find nearest support/resistance from Gann's spiral.
        Returns distance-to-level features.
        """
        features = {}
        n = len(close)
        
        # Nearest support and resistance from SQ9
        support_dist = np.zeros(n)
        resist_dist = np.zeros(n)
        level_position = np.zeros(n)  # Where in the SQ9 cycle we are
        
        for i in range(n):
            price = close[i]
            if price <= 0:
                continue
            
            sqrt_price = np.sqrt(price)
            
            # Find nearest cardinal and ordinal cross levels
            floor_sq = int(np.floor(sqrt_price))
            
            levels = []
            for offset in range(-self.sq9_levels, self.sq9_levels + 1):
                for angle_frac in [0.0, 0.25, 0.5, 0.75]:
                    level_sqrt = floor_sq + offset + angle_frac
                    if level_sqrt > 0:
                        levels.append(level_sqrt ** 2)
            
            levels = sorted(set(levels))
            
            # Find nearest support (below) and resistance (above)
            below = [l for l in levels if l <= price]
            above = [l for l in levels if l > price]
            
            if below:
                support = max(below)
                support_dist[i] = (price - support) / max(price, 0.001)
            
            if above:
                resist = min(above)
                resist_dist[i] = (resist - price) / max(price, 0.001)
            
            # Position within current SQ9 band
            if below and above:
                band_width = min(above) - max(below)
                if band_width > 0:
                    level_position[i] = (price - max(below)) / band_width
        
        features["support_dist"] = support_dist
        features["resist_dist"] = resist_dist
        features["level_position"] = level_position
        
        return features
    
    def _gann_angle_features(
        self, close: np.ndarray, high: np.ndarray, low: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Gann angle trend features."""
        features = {}
        n = len(close)
        
        # 1x1 angle (45 degrees) from significant lows/highs
        for lookback in [20, 50]:
            angle_bullish = np.zeros(n)
            angle_bearish = np.zeros(n)
            
            for i in range(lookback, n):
                window_low = np.min(low[i-lookback:i])
                window_high = np.max(high[i-lookback:i])
                
                low_idx = i - lookback + np.argmin(low[i-lookback:i])
                high_idx = i - lookback + np.argmax(high[i-lookback:i])
                
                # 1x1 angle from low (bullish support)
                bars_from_low = i - low_idx
                expected_from_low = window_low + bars_from_low * (window_low * 0.01)  # 1% per bar
                angle_bullish[i] = (close[i] - expected_from_low) / max(close[i], 0.001)
                
                # 1x1 angle from high (bearish resistance)
                bars_from_high = i - high_idx
                expected_from_high = window_high - bars_from_high * (window_high * 0.01)
                angle_bearish[i] = (close[i] - expected_from_high) / max(close[i], 0.001)
            
            features[f"bullish_{lookback}"] = np.clip(angle_bullish, -1, 1)
            features[f"bearish_{lookback}"] = np.clip(angle_bearish, -1, 1)
        
        return features
    
    def _time_cycle_features(self, n: int) -> Dict[str, np.ndarray]:
        """Time cycle features using Gann's important numbers."""
        features = {}
        
        for cycle in self.cycle_lengths:
            t = np.arange(n, dtype=float)
            # Sine/cosine representation (captures position in cycle)
            features[f"sin_{cycle}"] = np.sin(2 * np.pi * t / cycle)
            features[f"cos_{cycle}"] = np.cos(2 * np.pi * t / cycle)
        
        return features
    
    def _price_vibration(self, close: np.ndarray) -> np.ndarray:
        """Distance from nearest natural square number (Gann vibration)."""
        result = np.zeros(len(close))
        for i in range(len(close)):
            if close[i] <= 0:
                continue
            sqrt_p = np.sqrt(close[i])
            nearest_sq = round(sqrt_p) ** 2
            result[i] = (close[i] - nearest_sq) / max(close[i], 0.001)
        return np.clip(result, -1, 1)
    
    def _hexagon_proximity(self, close: np.ndarray) -> np.ndarray:
        """Proximity to Gann hexagon chart levels."""
        result = np.zeros(len(close))
        for i in range(len(close)):
            if close[i] <= 0:
                continue
            # Hexagon levels are based on multiples of important numbers
            for base in [7, 12, 49, 144, 360]:
                level = round(close[i] / base) * base
                dist = abs(close[i] - level) / max(close[i], 0.001)
                result[i] = max(result[i], 1.0 - dist)
        return np.clip(result, 0, 1)
