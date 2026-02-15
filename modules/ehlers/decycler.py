"""
Ehlers Decycler Module
Removes cycle components to reveal trend
"""
import numpy as np
import pandas as pd
from typing import Optional
from loguru import logger


def decycler(series: pd.Series, period: int = 125) -> pd.Series:
    """
    Ehlers Decycler - High-pass filter to remove cycles.
    Reveals underlying trend by removing cycle components.
    """
    alpha = (np.cos(2 * np.pi / period) + np.sin(2 * np.pi / period) - 1) / \
            np.cos(2 * np.pi / period)
    
    result = pd.Series(index=series.index, dtype=float)
    result.iloc[0] = series.iloc[0]
    
    for i in range(1, len(series)):
        result.iloc[i] = (1 - alpha / 2) * (series.iloc[i] - series.iloc[i-1]) + \
                         (1 - alpha) * result.iloc[i-1]
    
    # Decycler = Price - HighPass
    decycled = series - result
    return decycled


def decycler_oscillator(series: pd.Series, short_period: int = 100, long_period: int = 125) -> pd.Series:
    """
    Ehlers Decycler Oscillator.
    Difference between two decyclers.
    """
    short_dec = decycler(series, short_period)
    long_dec = decycler(series, long_period)
    
    return short_dec - long_dec


class Decycler:
    """Ehlers Decycler class wrapper"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.default_period = self.config.get('period', 125)
        logger.info("Decycler initialized")
    
    def calculate(self, series: pd.Series, period: int = None) -> pd.Series:
        """Calculate decycler"""
        period = period or self.default_period
        return decycler(series, period)
    
    def calculate_oscillator(self, series: pd.Series, short: int = 100, long: int = 125) -> pd.Series:
        """Calculate decycler oscillator"""
        return decycler_oscillator(series, short, long)
    
    def get_trend(self, series: pd.Series, period: int = None) -> pd.Series:
        """Get trend direction from decycler"""
        dec = self.calculate(series, period)
        return np.sign(dec.diff())
