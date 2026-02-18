"""
Production Data Cleaner
Handles gap filling, OHLCV repair, and normalization.
"""

import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, Optional


class DataCleaner:
    """
    Cleans and normalizes OHLCV data for feature engineering.
    
    Operations:
    - Forward fill small gaps (configurable limit)
    - Interpolate medium gaps
    - Flag large gaps for manual review
    - Normalize column names
    - Handle timezone alignment
    - Resample to target timeframe
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.max_ffill_bars = config.get("max_ffill_bars", 3)
        self.interpolation_method = config.get("interpolation_method", "linear")
        self.max_interpolate_bars = config.get("max_interpolate_bars", 5)
    
    def clean(self, df: pd.DataFrame, timeframe: str = "1h") -> pd.DataFrame:
        """
        Clean OHLCV DataFrame.
        
        Args:
            df: Validated OHLCV DataFrame with DatetimeIndex
            timeframe: Target timeframe
            
        Returns:
            Cleaned DataFrame
        """
        if df is None or df.empty:
            return df
        
        df = df.copy()
        
        # Normalize columns
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Sort by time
        df = df.sort_index()
        
        # Handle missing values
        df = self._fill_gaps(df)
        
        # Ensure numeric types
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Remove any remaining NaN in critical columns
        critical = [c for c in ["close"] if c in df.columns]
        if critical:
            df = df.dropna(subset=critical)
        
        # Ensure volume is non-negative
        if "volume" in df.columns:
            df["volume"] = df["volume"].clip(lower=0)
        
        logger.debug(f"Data cleaned: {len(df)} rows, {df.columns.tolist()}")
        return df
    
    def _fill_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill gaps using forward fill then interpolation."""
        price_cols = [c for c in ["open", "high", "low", "close"] if c in df.columns]
        
        # Forward fill (limit to max_ffill_bars)
        df[price_cols] = df[price_cols].ffill(limit=self.max_ffill_bars)
        
        # Linear interpolation for remaining (limit to max_interpolate_bars)
        df[price_cols] = df[price_cols].interpolate(
            method=self.interpolation_method,
            limit=self.max_interpolate_bars
        )
        
        # Volume: fill with 0 (no volume = no activity)
        if "volume" in df.columns:
            df["volume"] = df["volume"].fillna(0)
        
        return df
    
    def resample(self, df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
        """
        Resample OHLCV data to a different timeframe.
        
        Args:
            df: Source OHLCV DataFrame
            target_tf: Target timeframe (e.g., '4h', '1d')
            
        Returns:
            Resampled DataFrame
        """
        rule = self._tf_to_rule(target_tf)
        if rule is None:
            logger.warning(f"Unknown timeframe {target_tf}, returning original data")
            return df
        
        agg = {}
        if "open" in df.columns:
            agg["open"] = "first"
        if "high" in df.columns:
            agg["high"] = "max"
        if "low" in df.columns:
            agg["low"] = "min"
        if "close" in df.columns:
            agg["close"] = "last"
        if "volume" in df.columns:
            agg["volume"] = "sum"
        
        resampled = df.resample(rule).agg(agg).dropna()
        logger.debug(f"Resampled from {len(df)} to {len(resampled)} bars ({target_tf})")
        return resampled
    
    @staticmethod
    def _tf_to_rule(tf: str) -> Optional[str]:
        """Convert timeframe to pandas resample rule."""
        tf = tf.lower().strip()
        mapping = {
            "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
            "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
            "1d": "1D", "1w": "1W",
            "m1": "1min", "m5": "5min", "m15": "15min", "m30": "30min",
            "h1": "1h", "h4": "4h", "d1": "1D", "w1": "1W",
        }
        return mapping.get(tf)
    
    def add_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add return columns for downstream analysis."""
        if "close" in df.columns:
            df = df.copy()
            df["returns"] = df["close"].pct_change()
            df["log_returns"] = np.log(df["close"] / df["close"].shift(1))
        return df
