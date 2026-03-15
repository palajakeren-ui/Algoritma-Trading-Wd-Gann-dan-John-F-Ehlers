"""
Ehlers DSP Feature Engine
John Ehlers' Digital Signal Processing indicators as ML features.

Ehlers filters are superior to traditional moving averages because
they have zero-lag and are optimized for cycle analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from loguru import logger


class EhlersFeatureEngine:
    """
    Ehlers DSP indicators for feature extraction:
    
    1. SuperSmoother Filter
    2. Roofing Filter (bandpass)
    3. Instantaneous Trendline
    4. MAMA/FAMA (Mesa Adaptive Moving Average)
    5. Hilbert Transform (dominant cycle)
    6. Autocorrelation Periodogram
    7. Stochastic Cyber Cycle
    8. Even Better Sinewave
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.cycle_period = config.get("cycle_period", 20)
        self.bandpass_period = config.get("bandpass_period", 20)
        self.bandpass_bandwidth = config.get("bandpass_bandwidth", 0.3)
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all Ehlers features."""
        features = pd.DataFrame(index=df.index)
        close = df["close"].values.astype(float)
        
        # 1. SuperSmoother
        for period in [10, 20, 40]:
            features[f"ehlers_ss_{period}"] = self._supersmoother(close, period)
        
        # 2. Roofing Filter
        features["ehlers_roofing"] = self._roofing_filter(close)
        
        # 3. Instantaneous Trendline
        it = self._instantaneous_trendline(close)
        features["ehlers_it"] = it
        features["ehlers_it_signal"] = np.where(close > it, 1.0, -1.0)
        
        # 4. Cyber Cycle
        features["ehlers_cyber_cycle"] = self._cyber_cycle(close)
        
        # 5. Even Better Sinewave
        features["ehlers_ebsw"] = self._even_better_sinewave(close)
        
        # 6. Dominant cycle period
        features["ehlers_dom_cycle"] = self._dominant_cycle(close)
        
        # 7. Relative price to SuperSmoother (momentum-like)
        ss20 = self._supersmoother(close, 20)
        valid = ss20 != 0
        ratio = np.zeros(len(close))
        ratio[valid] = (close[valid] - ss20[valid]) / ss20[valid]
        features["ehlers_momentum"] = np.clip(ratio, -0.1, 0.1) * 10  # Normalize to ~[-1, 1]
        
        # 8. Trend vs Cycle indicator
        features["ehlers_trend_cycle"] = self._trend_vs_cycle(close)
        
        logger.debug(f"Ehlers features computed: {len(features.columns)} features")
        return features
    
    @staticmethod
    def _supersmoother(data: np.ndarray, period: int = 20) -> np.ndarray:
        """Ehlers 2-pole SuperSmoother filter (zero-lag)."""
        n = len(data)
        result = np.zeros(n)
        
        a = np.exp(-np.sqrt(2) * np.pi / period)
        b = 2 * a * np.cos(np.sqrt(2) * np.pi / period)
        c2 = b
        c3 = -a * a
        c1 = 1 - c2 - c3
        
        result[0] = data[0]
        if n > 1:
            result[1] = data[1]
        
        for i in range(2, n):
            result[i] = c1 * (data[i] + data[i-1]) / 2 + c2 * result[i-1] + c3 * result[i-2]
        
        return result
    
    def _roofing_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Ehlers Roofing Filter: highpass + supersmoother.
        Removes both trend (highpass) and noise (lowpass).
        """
        n = len(data)
        
        # Highpass filter
        hp_period = max(self.bandpass_period * 2, 40)
        alpha1 = (np.cos(2 * np.pi / hp_period) + np.sin(2 * np.pi / hp_period) - 1) / np.cos(2 * np.pi / hp_period)
        
        hp = np.zeros(n)
        for i in range(2, n):
            hp[i] = (1 - alpha1/2) * (1 - alpha1/2) * (data[i] - 2*data[i-1] + data[i-2]) + 2*(1-alpha1)*hp[i-1] - (1-alpha1)*(1-alpha1)*hp[i-2]
        
        # Then SuperSmoother
        return self._supersmoother(hp, self.bandpass_period)
    
    def _instantaneous_trendline(self, data: np.ndarray) -> np.ndarray:
        """Ehlers Instantaneous Trendline."""
        n = len(data)
        it = np.zeros(n)
        
        for i in range(min(7, n)):
            it[i] = data[i]
        
        for i in range(7, n):
            it[i] = (data[i] + 2*data[i-1] + data[i-2]) / 4.0
            # Smooth with feedback
            it[i] = (it[i] - 2*it[i-1] + it[i-2]) * 0.0 + 2*it[i-1] - it[i-2]
            # Alternative: direct average
            it[i] = (data[i] + 2*data[i-1] + data[i-2] + 2*data[i-3] + data[i-4]) / 7.0
        
        return it
    
    def _cyber_cycle(self, data: np.ndarray) -> np.ndarray:
        """Ehlers Cyber Cycle oscillator."""
        n = len(data)
        smooth = self._supersmoother(data, 4)
        
        cycle = np.zeros(n)
        
        alpha = 2.0 / (self.cycle_period + 1)
        
        for i in range(4, n):
            cycle[i] = ((1 - 0.5*alpha)**2) * (smooth[i] - 2*smooth[i-1] + smooth[i-2]) + 2*(1-alpha)*cycle[i-1] - (1-alpha)**2 * cycle[i-2]
        
        # Normalize
        max_val = np.max(np.abs(cycle)) if np.max(np.abs(cycle)) > 0 else 1
        return cycle / max_val
    
    def _even_better_sinewave(self, data: np.ndarray) -> np.ndarray:
        """Ehlers Even Better Sinewave indicator."""
        n = len(data)
        
        # Highpass filter
        hp = np.zeros(n)
        period = self.cycle_period * 2
        alpha1 = (1 - np.sin(2*np.pi/period)) / np.cos(2*np.pi/period) if period > 0 else 0.5
        
        for i in range(1, n):
            hp[i] = 0.5 * (1 + alpha1) * (data[i] - data[i-1]) + alpha1 * hp[i-1]
        
        # SuperSmooth the highpass
        filt = self._supersmoother(hp, self.cycle_period)
        
        # Wave calculation
        wave = np.zeros(n)
        for i in range(1, n):
            wave[i] = (filt[i] + filt[i-1]) / 2
        
        # Normalize
        max_val = np.max(np.abs(wave)) if np.max(np.abs(wave)) > 0 else 1
        return wave / max_val
    
    def _dominant_cycle(self, data: np.ndarray) -> np.ndarray:
        """Estimate dominant cycle period using zero-crossing method."""
        n = len(data)
        
        # Use roofing filter to isolate cycle
        cycle = self._roofing_filter(data)
        
        # Count bars between zero crossings
        dom_cycle = np.full(n, float(self.cycle_period))
        
        last_cross = 0
        for i in range(1, n):
            if (cycle[i] > 0 and cycle[i-1] <= 0) or (cycle[i] < 0 and cycle[i-1] >= 0):
                if last_cross > 0:
                    half_period = i - last_cross
                    full_period = half_period * 2
                    # Smooth the estimate
                    dom_cycle[i] = 0.7 * full_period + 0.3 * dom_cycle[i-1]
                last_cross = i
            else:
                dom_cycle[i] = dom_cycle[i-1]
        
        # Normalize to 0-1 range (6-100 bar range)
        return np.clip((dom_cycle - 6) / 94, 0, 1)
    
    def _trend_vs_cycle(self, data: np.ndarray) -> np.ndarray:
        """
        Trend vs Cycle strength indicator.
        +1 = strong trend, -1 = strong cycle, 0 = mixed
        """
        n = len(data)
        
        # Trend component: SuperSmoother difference
        ss_fast = self._supersmoother(data, 10)
        ss_slow = self._supersmoother(data, 40)
        
        trend = np.zeros(n)
        for i in range(n):
            if ss_slow[i] != 0:
                trend[i] = (ss_fast[i] - ss_slow[i]) / ss_slow[i]
        
        # Cycle component: roofing filter power
        cycle = self._roofing_filter(data)
        cycle_power = np.zeros(n)
        window = 20
        for i in range(window, n):
            cycle_power[i] = np.std(cycle[i-window:i])
        
        # Combine: positive = trending, negative = cycling
        max_trend = np.max(np.abs(trend)) if np.max(np.abs(trend)) > 0 else 1
        max_cycle = np.max(cycle_power) if np.max(cycle_power) > 0 else 1
        
        result = (np.abs(trend) / max_trend) - (cycle_power / max_cycle)
        return np.clip(result, -1, 1)
