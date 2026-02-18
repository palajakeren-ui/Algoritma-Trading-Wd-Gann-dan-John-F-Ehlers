"""
Adaptive Weighting Engine
Dynamically adjusts signal source weights based on regime and recent performance.
"""

import numpy as np
from typing import Dict, Optional, List
from loguru import logger
from collections import deque

from src.fusion.regime_detector import RegimeDetector, Regime, RegimeState


class AdaptiveWeighting:
    """
    Dynamically adjusts signal weights based on:
    
    1. Current market regime
    2. Rolling signal accuracy per source
    3. Signal agreement (consensus bonus)
    4. Decay of stale signals
    
    This replaces hardcoded weights like {'gann': 0.3, 'ehlers': 0.2, 'ml': 0.25}
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.regime_detector = RegimeDetector(config.get("regime", {}))
        
        # Default sources
        self.sources = config.get("sources", ["gann", "ehlers", "ml", "pattern"])
        
        # Performance tracking window
        self.performance_window = config.get("performance_window", 100)
        
        # How much regime weights vs performance weights
        self.regime_weight_factor = config.get("regime_weight_factor", 0.5)
        self.performance_weight_factor = config.get("performance_weight_factor", 0.5)
        
        # Signal decay (minutes)
        self.signal_max_age_minutes = config.get("signal_max_age_minutes", 60)
        
        # Performance tracking per source
        self._accuracy: Dict[str, deque] = {
            src: deque(maxlen=self.performance_window) for src in self.sources
        }
        
        # Current weights
        self._current_weights: Dict[str, float] = {}
        self._current_regime: Optional[RegimeState] = None
    
    def compute_weights(
        self,
        data=None,
        signal_scores: Dict[str, float] = None,
    ) -> Dict[str, float]:
        """
        Compute adaptive weights for all signal sources.
        
        Args:
            data: OHLCV DataFrame for regime detection
            signal_scores: Optional current signal scores per source
            
        Returns:
            Dict of source -> weight (sums to 1.0)
        """
        # 1. Detect current regime
        if data is not None:
            self._current_regime = self.regime_detector.detect(data)
        
        regime = self._current_regime
        
        # 2. Get regime-based weights
        regime_weights = self._get_regime_weights(regime)
        
        # 3. Get performance-based weights
        perf_weights = self._get_performance_weights()
        
        # 4. Blend
        final_weights = {}
        for src in self.sources:
            rw = regime_weights.get(src, 1.0 / len(self.sources))
            pw = perf_weights.get(src, 1.0 / len(self.sources))
            final_weights[src] = (
                self.regime_weight_factor * rw +
                self.performance_weight_factor * pw
            )
        
        # 5. Normalize to sum to 1.0
        total = sum(final_weights.values())
        if total > 0:
            final_weights = {k: v / total for k, v in final_weights.items()}
        
        self._current_weights = final_weights
        
        logger.debug(
            f"Adaptive weights: {', '.join(f'{k}={v:.3f}' for k, v in final_weights.items())} | "
            f"Regime: {regime.primary_regime.value if regime else 'unknown'}"
        )
        
        return final_weights
    
    def _get_regime_weights(self, regime: Optional[RegimeState]) -> Dict[str, float]:
        """Get weights recommended by current regime."""
        if regime is None:
            return {src: 1.0 / len(self.sources) for src in self.sources}
        
        regime_map = self.regime_detector.get_regime_weights()
        weights = regime_map.get(regime.primary_regime.value, {})
        
        # Fill missing sources
        for src in self.sources:
            if src not in weights:
                weights[src] = 1.0 / len(self.sources)
        
        return weights
    
    def _get_performance_weights(self) -> Dict[str, float]:
        """Get weights based on rolling signal accuracy."""
        weights = {}
        
        for src in self.sources:
            records = list(self._accuracy.get(src, []))
            if len(records) < 5:
                weights[src] = 1.0 / len(self.sources)
            else:
                # Exponentially weighted accuracy
                arr = np.array(records, dtype=float)
                decay = np.exp(-np.arange(len(arr))[::-1] * 0.02)
                weighted_accuracy = np.average(arr, weights=decay)
                weights[src] = max(0.05, weighted_accuracy)  # Floor at 5%
        
        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def record_signal_outcome(self, source: str, was_correct: bool):
        """
        Record whether a signal source was correct.
        
        Args:
            source: Signal source name (e.g., 'gann', 'ehlers')
            was_correct: True if the signal was profitable
        """
        if source in self._accuracy:
            self._accuracy[source].append(1.0 if was_correct else 0.0)
    
    def combine_signals(
        self,
        signal_scores: Dict[str, float],
        data=None,
    ) -> float:
        """
        Combine multiple signal scores into a single fusion score.
        
        Args:
            signal_scores: Dict of source -> score (each -1.0 to 1.0)
            data: OHLCV data for regime detection
            
        Returns:
            Combined score (-1.0 to 1.0)
        """
        weights = self.compute_weights(data=data)
        
        combined = 0.0
        total_weight = 0.0
        
        for src, score in signal_scores.items():
            w = weights.get(src, 0.0)
            combined += score * w
            total_weight += w
        
        if total_weight > 0:
            combined /= total_weight
        
        # Consensus bonus: if all signals agree, boost confidence
        signs = [np.sign(s) for s in signal_scores.values() if s != 0]
        if signs and all(s == signs[0] for s in signs):
            combined *= 1.15  # 15% consensus bonus
        
        return float(np.clip(combined, -1.0, 1.0))
    
    def get_status(self) -> Dict:
        """Get current adaptive weighting status."""
        return {
            "current_weights": {k: round(v, 4) for k, v in self._current_weights.items()},
            "regime": self._current_regime.to_dict() if self._current_regime else None,
            "source_accuracy": {
                src: round(np.mean(list(acc)) if acc else 0.0, 3)
                for src, acc in self._accuracy.items()
            },
            "performance_window": self.performance_window,
        }
