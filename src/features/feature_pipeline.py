"""
Feature Pipeline
Orchestrates all feature engines into a single pipeline.
Handles feature selection, normalization, and NaN management.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from loguru import logger

from src.features.gann_features import GannFeatureEngine
from src.features.ehlers_features import EhlersFeatureEngine
from src.features.technical_features import TechnicalFeatureEngine


class FeaturePipeline:
    """
    Unified feature computation pipeline.
    
    Data → Gann Features + Ehlers Features + Technical Features
    → Normalization → NaN handling → Feature Selection → Output
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.gann_engine = GannFeatureEngine(config.get("gann", {}))
        self.ehlers_engine = EhlersFeatureEngine(config.get("ehlers", {}))
        self.technical_engine = TechnicalFeatureEngine(config.get("technical", {}))
        
        self.enable_gann = config.get("enable_gann", True)
        self.enable_ehlers = config.get("enable_ehlers", True)
        self.enable_technical = config.get("enable_technical", True)
        
        self.max_nan_pct = config.get("max_nan_pct", 20.0)
        self.warmup_bars = config.get("warmup_bars", 100)
        
        self._feature_names: List[str] = []
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all features from OHLCV data.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with all computed features
        """
        if df is None or len(df) < self.warmup_bars:
            logger.warning(f"Insufficient data for feature computation: {len(df) if df is not None else 0} bars")
            return pd.DataFrame()
        
        all_features = pd.DataFrame(index=df.index)
        
        # Compute features from each engine
        if self.enable_gann:
            try:
                gann_feats = self.gann_engine.compute(df)
                all_features = pd.concat([all_features, gann_feats], axis=1)
                logger.debug(f"Gann: {len(gann_feats.columns)} features")
            except Exception as e:
                logger.error(f"Gann feature computation failed: {e}")
        
        if self.enable_ehlers:
            try:
                ehlers_feats = self.ehlers_engine.compute(df)
                all_features = pd.concat([all_features, ehlers_feats], axis=1)
                logger.debug(f"Ehlers: {len(ehlers_feats.columns)} features")
            except Exception as e:
                logger.error(f"Ehlers feature computation failed: {e}")
        
        if self.enable_technical:
            try:
                tech_feats = self.technical_engine.compute(df)
                all_features = pd.concat([all_features, tech_feats], axis=1)
                logger.debug(f"Technical: {len(tech_feats.columns)} features")
            except Exception as e:
                logger.error(f"Technical feature computation failed: {e}")
        
        if all_features.empty:
            return all_features
        
        # Drop warmup period
        all_features = all_features.iloc[self.warmup_bars:]
        
        # Handle NaN columns
        nan_pcts = all_features.isnull().mean() * 100
        bad_cols = nan_pcts[nan_pcts > self.max_nan_pct].index.tolist()
        if bad_cols:
            logger.warning(f"Dropping {len(bad_cols)} features with >{self.max_nan_pct}% NaN")
            all_features = all_features.drop(columns=bad_cols)
        
        # Forward fill remaining NaNs, then zero fill
        all_features = all_features.ffill().fillna(0)
        
        # Replace infinities
        all_features = all_features.replace([np.inf, -np.inf], 0)
        
        self._feature_names = all_features.columns.tolist()
        
        logger.info(f"Feature pipeline: {len(self._feature_names)} features × {len(all_features)} bars")
        
        return all_features
    
    @property
    def feature_names(self) -> List[str]:
        return self._feature_names
    
    def get_feature_groups(self) -> Dict[str, List[str]]:
        """Get features grouped by source."""
        groups = {"gann": [], "ehlers": [], "technical": [], "other": []}
        for name in self._feature_names:
            if name.startswith("gann_"):
                groups["gann"].append(name)
            elif name.startswith("ehlers_"):
                groups["ehlers"].append(name)
            elif name.startswith("tech_"):
                groups["technical"].append(name)
            else:
                groups["other"].append(name)
        return groups
