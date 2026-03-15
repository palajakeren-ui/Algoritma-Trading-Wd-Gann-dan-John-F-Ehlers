"""
Signal Generator
Converts features into tradeable signals with confidence scoring.

Each signal source produces an independent score [-1.0, +1.0]:
- -1.0 = Strong sell
-  0.0 = Neutral
- +1.0 = Strong buy
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SignalDirection(Enum):
    STRONG_SELL = -2
    SELL = -1
    NEUTRAL = 0
    BUY = 1
    STRONG_BUY = 2


@dataclass
class Signal:
    """A tradeable signal from a single source."""
    source: str
    symbol: str
    direction: SignalDirection
    score: float           # -1.0 to 1.0
    confidence: float      # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    features_used: int = 0
    expiry_minutes: int = 60
    metadata: Dict = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        age = (datetime.utcnow() - self.timestamp).total_seconds() / 60
        return age > self.expiry_minutes
    
    @property
    def strength(self) -> float:
        """Signal strength = |score| × confidence."""
        return abs(self.score) * self.confidence
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "symbol": self.symbol,
            "direction": self.direction.name,
            "score": round(self.score, 4),
            "confidence": round(self.confidence, 4),
            "strength": round(self.strength, 4),
            "timestamp": self.timestamp.isoformat(),
            "expired": self.is_expired,
        }


class SignalGenerator:
    """
    Converts feature engine outputs into tradeable signals.
    
    Process:
    1. Receive features from FeaturePipeline
    2. Score each source independently (Gann, Ehlers, Technical)
    3. Apply confidence calibration
    4. Apply signal decay (older signals lose strength)
    5. Output Signal objects
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.min_confidence = config.get("min_confidence", 0.3)
        self.signal_expiry_minutes = config.get("signal_expiry_minutes", 60)
        self.decay_rate = config.get("decay_rate", 0.02)  # Per minute
        
        # Active signals
        self._active_signals: Dict[str, Signal] = {}
    
    def generate(
        self,
        features: pd.DataFrame,
        symbol: str = "BTCUSDT",
    ) -> Dict[str, Signal]:
        """
        Generate signals from computed features.
        
        Args:
            features: DataFrame from FeaturePipeline
            symbol: Trading symbol
            
        Returns:
            Dict of source_name → Signal
        """
        if features.empty:
            return {}
        
        signals = {}
        
        # Get latest feature values
        latest = features.iloc[-1]
        
        # 1. Gann signal
        gann_cols = [c for c in features.columns if c.startswith("gann_")]
        if gann_cols:
            gann_signal = self._score_gann(latest, gann_cols)
            if abs(gann_signal.score) > 0.1:
                signals["gann"] = gann_signal
        
        # 2. Ehlers signal
        ehlers_cols = [c for c in features.columns if c.startswith("ehlers_")]
        if ehlers_cols:
            ehlers_signal = self._score_ehlers(latest, ehlers_cols)
            if abs(ehlers_signal.score) > 0.1:
                signals["ehlers"] = ehlers_signal
        
        # 3. Technical signal
        tech_cols = [c for c in features.columns if c.startswith("tech_")]
        if tech_cols:
            tech_signal = self._score_technical(latest, tech_cols)
            if abs(tech_signal.score) > 0.1:
                signals["technical"] = tech_signal
        
        # Update active signals
        for name, sig in signals.items():
            sig.symbol = symbol
            self._active_signals[f"{symbol}_{name}"] = sig
        
        # Clean expired signals
        self._clean_expired()
        
        logger.debug(
            f"Signals for {symbol}: " +
            ", ".join(f"{k}={v.score:+.3f}(conf={v.confidence:.2f})" for k, v in signals.items())
        )
        
        return signals
    
    def _score_gann(self, row: pd.Series, cols: List[str]) -> Signal:
        """Score Gann features into a signal."""
        score = 0.0
        n = 0
        
        # SQ9 support/resist proximity
        if "gann_sq9_support_dist" in cols:
            support_dist = row.get("gann_sq9_support_dist", 0)
            resist_dist = row.get("gann_sq9_resist_dist", 0)
            
            # Near support = bullish, near resistance = bearish
            if resist_dist > 0 and support_dist > 0:
                sr_score = (resist_dist - support_dist) / max(resist_dist + support_dist, 0.001)
                score += sr_score
                n += 1
        
        # SQ9 level position (0.0-0.3 = near support, 0.7-1.0 = near resistance)
        if "gann_sq9_level_position" in cols:
            pos = row.get("gann_sq9_level_position", 0.5)
            score += (0.5 - pos)  # Below 0.5 = bullish, above = bearish
            n += 1
        
        # Angle features
        for col in cols:
            if "angle_bullish" in col:
                score += float(row.get(col, 0)) * 0.3
                n += 1
            elif "angle_bearish" in col:
                score -= float(row.get(col, 0)) * 0.3
                n += 1
        
        # Vibration
        if "gann_vibration" in cols:
            score += float(row.get("gann_vibration", 0)) * 0.2
            n += 1
        
        if n > 0:
            score /= n
        
        confidence = min(0.9, 0.3 + 0.1 * n)  # More features = higher confidence
        
        direction = self._score_to_direction(score)
        
        return Signal(
            source="gann",
            symbol="",
            direction=direction,
            score=float(np.clip(score, -1, 1)),
            confidence=confidence,
            features_used=n,
            expiry_minutes=self.signal_expiry_minutes,
        )
    
    def _score_ehlers(self, row: pd.Series, cols: List[str]) -> Signal:
        """Score Ehlers DSP features into a signal."""
        score = 0.0
        n = 0
        
        # Cyber cycle (oscillator)
        if "ehlers_cyber_cycle" in cols:
            cc = float(row.get("ehlers_cyber_cycle", 0))
            score += cc * 0.8
            n += 1
        
        # Even Better Sinewave
        if "ehlers_ebsw" in cols:
            ebsw = float(row.get("ehlers_ebsw", 0))
            score += ebsw * 0.8
            n += 1
        
        # Instantaneous Trendline signal
        if "ehlers_it_signal" in cols:
            it_sig = float(row.get("ehlers_it_signal", 0))
            score += it_sig * 0.6
            n += 1
        
        # Momentum (price vs SuperSmoother)
        if "ehlers_momentum" in cols:
            mom = float(row.get("ehlers_momentum", 0))
            score += mom * 0.5
            n += 1
        
        # Trend vs cycle indicator
        if "ehlers_trend_cycle" in cols:
            tc = float(row.get("ehlers_trend_cycle", 0))
            # If trending, trust momentum; if cycling, trust oscillators
            if tc > 0.3:
                score *= 1.2  # Boost trending signals
            elif tc < -0.3:
                score *= 0.8  # Reduce in cycle mode
            n += 1
        
        if n > 0:
            score /= n
        
        confidence = min(0.9, 0.35 + 0.1 * n)
        direction = self._score_to_direction(score)
        
        return Signal(
            source="ehlers",
            symbol="",
            direction=direction,
            score=float(np.clip(score, -1, 1)),
            confidence=confidence,
            features_used=n,
            expiry_minutes=self.signal_expiry_minutes,
        )
    
    def _score_technical(self, row: pd.Series, cols: List[str]) -> Signal:
        """Score technical features into a signal."""
        score = 0.0
        n = 0
        
        # RSI (overbought/oversold)
        if "tech_rsi" in cols:
            rsi = float(row.get("tech_rsi", 0.5))
            if rsi > 0.7:
                score -= (rsi - 0.5) * 2  # Overbought = bearish
            elif rsi < 0.3:
                score += (0.5 - rsi) * 2  # Oversold = bullish
            n += 1
        
        # MACD histogram
        if "tech_macd_hist" in cols:
            macd_h = float(row.get("tech_macd_hist", 0))
            score += macd_h * 0.6
            n += 1
        
        # BB position
        if "tech_bb_position" in cols:
            bb = float(row.get("tech_bb_position", 0.5))
            score += (0.5 - bb) * 0.8  # Near lower band = bullish
            n += 1
        
        # MA crossovers
        for col in cols:
            if "tech_ma_cross" in col:
                score += float(row.get(col, 0)) * 0.4
                n += 1
        
        # Volume confirmation
        if "tech_vol_ratio" in cols:
            vol = float(row.get("tech_vol_ratio", 0.5))
            if vol > 0.7:  # High volume confirms direction
                score *= 1.2
            n += 1
        
        # ADX (trend strength) - doesn't change direction but affects confidence
        adx_val = float(row.get("tech_adx", 0.25)) if "tech_adx" in cols else 0.25
        
        if n > 0:
            score /= n
        
        confidence = min(0.9, 0.3 + 0.1 * n + adx_val * 0.3)
        direction = self._score_to_direction(score)
        
        return Signal(
            source="technical",
            symbol="",
            direction=direction,
            score=float(np.clip(score, -1, 1)),
            confidence=confidence,
            features_used=n,
            expiry_minutes=self.signal_expiry_minutes,
        )
    
    @staticmethod
    def _score_to_direction(score: float) -> SignalDirection:
        """Convert raw score to direction enum."""
        if score > 0.6:
            return SignalDirection.STRONG_BUY
        elif score > 0.2:
            return SignalDirection.BUY
        elif score < -0.6:
            return SignalDirection.STRONG_SELL
        elif score < -0.2:
            return SignalDirection.SELL
        else:
            return SignalDirection.NEUTRAL
    
    def _clean_expired(self):
        """Remove expired signals."""
        expired = [k for k, v in self._active_signals.items() if v.is_expired]
        for k in expired:
            del self._active_signals[k]
    
    def get_active_signals(self, symbol: str = None) -> Dict[str, Signal]:
        """Get active (non-expired) signals."""
        self._clean_expired()
        if symbol:
            return {k: v for k, v in self._active_signals.items() if v.symbol == symbol}
        return dict(self._active_signals)
