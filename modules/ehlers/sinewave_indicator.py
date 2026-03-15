"""
Ehlers Sinewave Indicator Module
Detects cycle mode and generates signals using Hilbert Transform for phase detection
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from loguru import logger


def sinewave_indicator(series: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series]:
    """
    Ehlers Sinewave Indicator.
    
    Uses Hilbert Transform to calculate instantaneous phase and generate
    sine/leadsine lines for cycle mode detection.
    
    Args:
        series: Price series (typically close prices)
        period: Base period for calculations (default 20)
        
    Returns:
        Tuple of (sine, leadsine) series
    """
    length = len(series)
    
    # Smooth price using weighted average - CORRECTED initialization
    smooth = pd.Series(index=series.index, dtype=float)
    
    # Initialize first 6 bars with proper weighted average
    for i in range(min(6, length)):
        if i >= 3:
            smooth.iloc[i] = (series.iloc[i] + 2*series.iloc[i-1] + 2*series.iloc[i-2] + series.iloc[i-3]) / 6
        else:
            smooth.iloc[i] = series.iloc[i]
    
    for i in range(6, length):
        smooth.iloc[i] = (series.iloc[i] + 2*series.iloc[i-1] + 2*series.iloc[i-2] + series.iloc[i-3]) / 6
    
    # Compute cycle using Hilbert Transform approximation
    alpha = 2 / (period + 1)
    cycle = pd.Series(index=series.index, dtype=float)
    cycle.iloc[:6] = 0
    
    for i in range(6, length):
        cycle.iloc[i] = (1 - 0.5*alpha) * (1 - 0.5*alpha) * (smooth.iloc[i] - 2*smooth.iloc[i-1] + smooth.iloc[i-2]) + \
                        2 * (1 - alpha) * cycle.iloc[i-1] - (1 - alpha) * (1 - alpha) * cycle.iloc[i-2]
    
    # Calculate instantaneous phase using Hilbert Transform components
    # This is the CORRECT approach - using actual phase from cycle, not linear progression
    
    # Quadrature component (90° phase shift)
    quad = pd.Series(index=series.index, dtype=float)
    quad.iloc[:3] = 0
    
    for i in range(3, length):
        # Hilbert Transform approximation for quadrature
        quad.iloc[i] = (cycle.iloc[i] - cycle.iloc[i-2]) / 2
    
    # Calculate instantaneous phase from cycle and quadrature
    phase = pd.Series(index=series.index, dtype=float)
    phase.iloc[:3] = 0
    
    for i in range(3, length):
        # arctan2 gives angle in radians from -π to π
        phase.iloc[i] = np.arctan2(quad.iloc[i], cycle.iloc[i]) if (cycle.iloc[i] != 0 or quad.iloc[i] != 0) else 0
    
    # Convert phase to degrees and create sine/leadsine
    sine = pd.Series(index=series.index, dtype=float)
    leadsine = pd.Series(index=series.index, dtype=float)
    
    for i in range(length):
        phase_deg = np.degrees(phase.iloc[i])
        sine.iloc[i] = np.sin(np.radians(phase_deg))
        leadsine.iloc[i] = np.sin(np.radians(phase_deg + 45))
    
    return sine, leadsine


def even_better_sinewave(series: pd.Series, duration: int = 40, period: int = 10) -> pd.Series:
    """
    Ehlers Even Better Sinewave Indicator.
    Improved cycle detection using high-pass filter and super smoother.
    
    Args:
        series: Price series
        duration: High-pass filter duration (default 40)
        period: Super smoother period (default 10)
        
    Returns:
        Normalized sinewave values
    """
    length = len(series)
    
    # High-pass filter
    alpha1 = (1 - np.sin(2 * np.pi / duration)) / np.cos(2 * np.pi / duration)
    hp = pd.Series(index=series.index, dtype=float)
    hp.iloc[0] = 0
    
    for i in range(1, length):
        hp.iloc[i] = 0.5 * (1 + alpha1) * (series.iloc[i] - series.iloc[i-1]) + alpha1 * hp.iloc[i-1]
    
    # Super Smoother
    a1 = np.exp(-1.414 * np.pi / period)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / period)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1 - c2 - c3
    
    filt = pd.Series(index=series.index, dtype=float)
    filt.iloc[:2] = hp.iloc[:2]
    
    for i in range(2, length):
        filt.iloc[i] = c1 * (hp.iloc[i] + hp.iloc[i-1]) / 2 + c2 * filt.iloc[i-1] + c3 * filt.iloc[i-2]
    
    # Wave calculation
    wave = pd.Series(index=series.index, dtype=float)
    pwr = pd.Series(index=series.index, dtype=float)
    wave.iloc[:2] = 0
    pwr.iloc[:2] = 0
    
    for i in range(2, length):
        wave.iloc[i] = (filt.iloc[i] + filt.iloc[i-1] + filt.iloc[i-2]) / 3
        pwr.iloc[i] = (filt.iloc[i]**2 + filt.iloc[i-1]**2 + filt.iloc[i-2]**2) / 3
    
    # Normalize
    ebsw = pd.Series(index=series.index, dtype=float)
    for i in range(length):
        sqrt_pwr = np.sqrt(pwr.iloc[i]) if pwr.iloc[i] > 0 else 1
        ebsw.iloc[i] = wave.iloc[i] / sqrt_pwr if sqrt_pwr != 0 else 0
    
    return ebsw


def dominant_cycle_period(series: pd.Series, max_period: int = 50) -> pd.Series:
    """
    Calculate the dominant cycle period using Ehlers' Homodyne Discriminator.
    
    Args:
        series: Price series
        max_period: Maximum period to detect
        
    Returns:
        Dominant cycle period series
    """
    length = len(series)
    
    # Smooth price
    smooth = pd.Series(index=series.index, dtype=float)
    smooth.iloc[:4] = series.iloc[:4]
    
    for i in range(4, length):
        smooth.iloc[i] = (4*series.iloc[i] + 3*series.iloc[i-1] + 2*series.iloc[i-2] + series.iloc[i-3]) / 10
    
    # Hilbert Transform components
    q = pd.Series(index=series.index, dtype=float)
    i_component = pd.Series(index=series.index, dtype=float)
    q.iloc[:7] = 0
    i_component.iloc[:7] = 0
    
    for i in range(7, length):
        q.iloc[i] = (0.0962*smooth.iloc[i] + 0.5769*smooth.iloc[i-2] - 
                     0.5769*smooth.iloc[i-4] - 0.0962*smooth.iloc[i-6]) * 0.54
        i_component.iloc[i] = smooth.iloc[i-3] if i >= 10 else 0
    
    # Calculate period using arctangent
    period = pd.Series(index=series.index, dtype=float)
    period.iloc[:1] = 20  # Default
    
    for i in range(1, length):
        if i_component.iloc[i] != 0 or q.iloc[i] != 0:
            angle = np.arctan2(q.iloc[i], i_component.iloc[i])
            period.iloc[i] = 2 * np.pi / abs(angle) if angle != 0 else period.iloc[i-1]
            period.iloc[i] = min(max_period, max(6, period.iloc[i]))
        else:
            period.iloc[i] = period.iloc[i-1]
    
    return period


class SinewaveIndicator:
    """Ehlers Sinewave Indicator class wrapper"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.period = self.config.get('period', 20)
        logger.info("SinewaveIndicator initialized")
    
    def calculate(self, series: pd.Series, period: int = None) -> Dict[str, pd.Series]:
        """Calculate sinewave indicator"""
        period = period or self.period
        sine, leadsine = sinewave_indicator(series, period)
        return {'sine': sine, 'leadsine': leadsine}
    
    def calculate_ebsw(self, series: pd.Series, duration: int = 40, period: int = 10) -> pd.Series:
        """Calculate Even Better Sinewave"""
        return even_better_sinewave(series, duration, period)
    
    def get_signals(self, series: pd.Series) -> pd.Series:
        """Get buy/sell signals from sinewave crossovers"""
        sine, leadsine = sinewave_indicator(series, self.period)
        signals = pd.Series(index=series.index, data='')
        
        # Buy when sine crosses above leadsine
        signals[(sine > leadsine) & (sine.shift(1) <= leadsine.shift(1))] = 'BUY'
        # Sell when sine crosses below leadsine
        signals[(sine < leadsine) & (sine.shift(1) >= leadsine.shift(1))] = 'SELL'
        
        return signals
    
    def get_cycle_mode(self, series: pd.Series) -> pd.Series:
        """
        Determine if market is in cycle mode or trend mode.
        
        Cycle mode: sine and leadsine oscillate in regular pattern
        Trend mode: sine and leadsine are mostly aligned
        """
        sine, leadsine = sinewave_indicator(series, self.period)
        
        # Calculate the amplitude of the sine wave
        amplitude = (sine - sine.rolling(window=self.period).min()) / \
                    (sine.rolling(window=self.period).max() - sine.rolling(window=self.period).min() + 0.001)
        
        mode = pd.Series(index=series.index, data='neutral')
        # If amplitude is significant, we're in cycle mode
        mode[amplitude > 0.3] = 'cycle'
        mode[amplitude <= 0.3] = 'trend'
        
        return mode
    
    def get_dominant_period(self, series: pd.Series) -> pd.Series:
        """Get the dominant cycle period"""
        return dominant_cycle_period(series)
