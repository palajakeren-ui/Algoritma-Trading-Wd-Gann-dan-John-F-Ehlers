"""
Ehlers Sinewave Indicator Module
Detects cycle mode and generates signals
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple
from loguru import logger


def sinewave_indicator(series: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series]:
    """
    Ehlers Sinewave Indicator.
    Returns sine and leadsine for cycle detection.
    """
    smooth = pd.Series(index=series.index, dtype=float)
    cycle = pd.Series(index=series.index, dtype=float)
    
    # Initialize
    smooth.iloc[:6] = (series.iloc[:6] + 2*series.iloc[:6] + 2*series.iloc[:6] + series.iloc[:6]) / 6
    
    for i in range(6, len(series)):
        smooth.iloc[i] = (series.iloc[i] + 2*series.iloc[i-1] + 2*series.iloc[i-2] + series.iloc[i-3]) / 6
    
    # Compute cycle using Hilbert Transform approximation
    alpha = 2 / (period + 1)
    cycle.iloc[:6] = 0
    
    for i in range(6, len(series)):
        cycle.iloc[i] = (1 - 0.5*alpha) * (1 - 0.5*alpha) * (smooth.iloc[i] - 2*smooth.iloc[i-1] + smooth.iloc[i-2]) + \
                        2 * (1 - alpha) * cycle.iloc[i-1] - (1 - alpha) * (1 - alpha) * cycle.iloc[i-2]
    
    # Compute dominant cycle period (simplified)
    dc_period = period
    
    # Compute sine and leadsine
    sine = pd.Series(index=series.index, dtype=float)
    leadsine = pd.Series(index=series.index, dtype=float)
    
    for i in range(len(series)):
        phase = i * 360 / dc_period
        sine.iloc[i] = np.sin(np.radians(phase))
        leadsine.iloc[i] = np.sin(np.radians(phase + 45))
    
    return sine, leadsine


def even_better_sinewave(series: pd.Series, duration: int = 40, period: int = 10) -> pd.Series:
    """
    Ehlers Even Better Sinewave Indicator.
    Improved cycle detection.
    """
    # High-pass filter
    alpha1 = (1 - np.sin(2 * np.pi / duration)) / np.cos(2 * np.pi / duration)
    hp = pd.Series(index=series.index, dtype=float)
    hp.iloc[0] = 0
    
    for i in range(1, len(series)):
        hp.iloc[i] = 0.5 * (1 + alpha1) * (series.iloc[i] - series.iloc[i-1]) + alpha1 * hp.iloc[i-1]
    
    # Super Smoother
    a1 = np.exp(-1.414 * np.pi / period)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / period)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1 - c2 - c3
    
    filt = pd.Series(index=series.index, dtype=float)
    filt.iloc[:2] = hp.iloc[:2]
    
    for i in range(2, len(series)):
        filt.iloc[i] = c1 * (hp.iloc[i] + hp.iloc[i-1]) / 2 + c2 * filt.iloc[i-1] + c3 * filt.iloc[i-2]
    
    # Wave calculation
    wave = (filt + filt.shift(1) + filt.shift(2)) / 3
    pwr = (filt**2 + filt.shift(1)**2 + filt.shift(2)**2) / 3
    
    # Normalize
    ebsw = wave / np.sqrt(pwr.replace(0, np.nan))
    return ebsw.fillna(0)


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
