"""
Volatility Regime Detector
Classifies current market regime for adaptive signal weighting.

Regimes:
- LOW_VOL:    Calm market, mean-reversion strategies work
- NORMAL_VOL: Standard conditions
- HIGH_VOL:   Elevated vol, trend-following better
- CRISIS:     Extreme vol, defensive posture
- TRENDING:   Strong directional move
- RANGING:    Sideways/choppy market
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from loguru import logger
from dataclasses import dataclass
from enum import Enum


class Regime(Enum):
    LOW_VOL = "low_vol"
    NORMAL_VOL = "normal_vol"
    HIGH_VOL = "high_vol"
    CRISIS = "crisis"
    TRENDING = "trending"
    RANGING = "ranging"


@dataclass
class RegimeState:
    """Current regime classification."""
    primary_regime: Regime
    secondary_regime: Optional[Regime]
    confidence: float
    volatility_percentile: float
    trend_strength: float
    mean_reversion_score: float
    
    def to_dict(self) -> Dict:
        return {
            "primary": self.primary_regime.value,
            "secondary": self.secondary_regime.value if self.secondary_regime else None,
            "confidence": round(self.confidence, 3),
            "volatility_percentile": round(self.volatility_percentile, 3),
            "trend_strength": round(self.trend_strength, 3),
            "mean_reversion_score": round(self.mean_reversion_score, 3),
        }


class RegimeDetector:
    """
    Multi-factor regime detection using:
    
    1. Realized volatility percentile ranking
    2. Trend strength (ADX-like)
    3. Mean reversion scoring (Hurst exponent approximation)
    4. Volume regime (volume relative to historical)
    
    Uses lookback windows to avoid whipsaw on regime transitions.
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.vol_lookback = config.get("vol_lookback", 252)    # 1 year
        self.trend_lookback = config.get("trend_lookback", 20)  # ADX-like period
        self.smoothing = config.get("smoothing", 5)             # Regime smoothing
        
        # Percentile thresholds
        self.low_vol_pct = config.get("low_vol_pct", 25)
        self.high_vol_pct = config.get("high_vol_pct", 75)
        self.crisis_vol_pct = config.get("crisis_vol_pct", 95)
        
        # Trend thresholds
        self.trending_threshold = config.get("trending_threshold", 0.5)
        self.ranging_threshold = config.get("ranging_threshold", 0.2)
        
        self._history: list = []
    
    def detect(self, df: pd.DataFrame) -> RegimeState:
        """
        Detect current market regime from OHLCV data.
        
        Args:
            df: OHLCV DataFrame with at least `close` column
            
        Returns:
            RegimeState with classification
        """
        if df is None or len(df) < 50:
            return RegimeState(
                primary_regime=Regime.NORMAL_VOL,
                secondary_regime=None,
                confidence=0.0,
                volatility_percentile=50.0,
                trend_strength=0.0,
                mean_reversion_score=0.5,
            )
        
        close = df["close"].values if "close" in df.columns else df.iloc[:, 0].values
        
        # 1. Volatility regime
        vol_pct = self._volatility_percentile(close)
        
        # 2. Trend strength
        trend = self._trend_strength(close)
        
        # 3. Mean reversion score (Hurst exponent approximation)
        mr_score = self._hurst_exponent(close)
        
        # Classify
        primary, secondary, confidence = self._classify(vol_pct, trend, mr_score)
        
        state = RegimeState(
            primary_regime=primary,
            secondary_regime=secondary,
            confidence=confidence,
            volatility_percentile=vol_pct,
            trend_strength=trend,
            mean_reversion_score=mr_score,
        )
        
        self._history.append(state)
        
        logger.debug(
            f"Regime: {primary.value} (conf={confidence:.2f}) | "
            f"VolPct={vol_pct:.0f} | Trend={trend:.2f} | MR={mr_score:.2f}"
        )
        
        return state
    
    def _volatility_percentile(self, close: np.ndarray) -> float:
        """Calculate current volatility as percentile of historical."""
        returns = np.diff(np.log(close))
        
        if len(returns) < 20:
            return 50.0
        
        # Current vol (20-bar rolling)
        current_vol = np.std(returns[-20:])
        
        # Historical vol distribution
        lookback = min(len(returns), self.vol_lookback)
        rolling_vols = []
        for i in range(20, lookback):
            rolling_vols.append(np.std(returns[i-20:i]))
        
        if not rolling_vols:
            return 50.0
        
        # Percentile rank
        pct = (np.searchsorted(sorted(rolling_vols), current_vol) / len(rolling_vols)) * 100
        return float(pct)
    
    def _trend_strength(self, close: np.ndarray) -> float:
        """
        Measure trend strength (0 = no trend, 1 = strong trend).
        Uses efficiency ratio: net movement / total movement.
        """
        n = min(self.trend_lookback, len(close) - 1)
        if n < 5:
            return 0.0
        
        recent = close[-n:]
        
        # Net movement
        net_move = abs(recent[-1] - recent[0])
        
        # Total path length
        total_move = np.sum(np.abs(np.diff(recent)))
        
        if total_move == 0:
            return 0.0
        
        efficiency = net_move / total_move
        return float(efficiency)
    
    def _hurst_exponent(self, close: np.ndarray, max_lag: int = 20) -> float:
        """
        Approximate Hurst exponent.
        H < 0.5 = mean reverting
        H = 0.5 = random walk
        H > 0.5 = trending
        """
        returns = np.diff(np.log(close))
        
        if len(returns) < max_lag * 2:
            return 0.5
        
        lags = range(2, max_lag)
        tau = []
        
        for lag in lags:
            # Standard deviation of lagged differences
            diff = returns[lag:] - returns[:-lag]
            tau.append(np.std(diff))
        
        tau = np.array(tau)
        lags_arr = np.array(list(lags), dtype=float)
        
        # Avoid log of zero
        valid = tau > 0
        if not valid.any():
            return 0.5
        
        # Linear regression of log(tau) vs log(lag)
        log_lags = np.log(lags_arr[valid])
        log_tau = np.log(tau[valid])
        
        if len(log_lags) < 3:
            return 0.5
        
        coeffs = np.polyfit(log_lags, log_tau, 1)
        hurst = coeffs[0]
        
        return float(np.clip(hurst, 0.0, 1.0))
    
    def _classify(
        self, vol_pct: float, trend: float, mr_score: float
    ) -> Tuple[Regime, Optional[Regime], float]:
        """Classify into regime with confidence."""
        
        # Volatility regime
        if vol_pct >= self.crisis_vol_pct:
            vol_regime = Regime.CRISIS
            vol_confidence = (vol_pct - self.crisis_vol_pct) / (100 - self.crisis_vol_pct)
        elif vol_pct >= self.high_vol_pct:
            vol_regime = Regime.HIGH_VOL
            vol_confidence = (vol_pct - self.high_vol_pct) / (self.crisis_vol_pct - self.high_vol_pct)
        elif vol_pct <= self.low_vol_pct:
            vol_regime = Regime.LOW_VOL
            vol_confidence = 1 - (vol_pct / self.low_vol_pct)
        else:
            vol_regime = Regime.NORMAL_VOL
            vol_confidence = 0.5
        
        # Trend regime
        if trend >= self.trending_threshold:
            trend_regime = Regime.TRENDING
        elif trend <= self.ranging_threshold:
            trend_regime = Regime.RANGING
        else:
            trend_regime = None
        
        # Primary = crisis always wins, otherwise volatility regime
        if vol_regime == Regime.CRISIS:
            primary = Regime.CRISIS
            secondary = trend_regime
            confidence = max(0.7, vol_confidence)
        elif trend >= 0.6:
            primary = Regime.TRENDING
            secondary = vol_regime
            confidence = trend
        elif trend <= 0.15:
            primary = Regime.RANGING
            secondary = vol_regime
            confidence = 1 - trend
        else:
            primary = vol_regime
            secondary = trend_regime
            confidence = vol_confidence
        
        return primary, secondary, float(np.clip(confidence, 0.0, 1.0))
    
    def get_regime_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Get recommended signal weights for each regime.
        These are the defaults; actual weights should be learned from data.
        """
        return {
            Regime.LOW_VOL.value: {
                "gann": 0.25, "ehlers": 0.35, "ml": 0.30, "pattern": 0.10,
            },
            Regime.NORMAL_VOL.value: {
                "gann": 0.30, "ehlers": 0.25, "ml": 0.30, "pattern": 0.15,
            },
            Regime.HIGH_VOL.value: {
                "gann": 0.35, "ehlers": 0.15, "ml": 0.35, "pattern": 0.15,
            },
            Regime.CRISIS.value: {
                "gann": 0.10, "ehlers": 0.10, "ml": 0.70, "pattern": 0.10,
            },
            Regime.TRENDING.value: {
                "gann": 0.30, "ehlers": 0.20, "ml": 0.35, "pattern": 0.15,
            },
            Regime.RANGING.value: {
                "gann": 0.20, "ehlers": 0.40, "ml": 0.25, "pattern": 0.15,
            },
        }
