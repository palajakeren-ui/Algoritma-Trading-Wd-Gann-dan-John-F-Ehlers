"""
Ehlers Roofing Filter Module
Band-pass filter for cycle isolation
"""
import numpy as np
import pandas as pd
from typing import Tuple
from loguru import logger


def roofing_filter(series: pd.Series, hp_period: int = 48, lp_period: int = 10) -> pd.Series:
    """
    Ehlers Roofing Filter.
    Combines high-pass and low-pass filters.
    """
    # High-pass filter
    alpha1 = (np.cos(2 * np.pi / hp_period) + np.sin(2 * np.pi / hp_period) - 1) / \
             np.cos(2 * np.pi / hp_period)
    
    hp = pd.Series(index=series.index, dtype=float)
    hp.iloc[:2] = 0
    
    for i in range(2, len(series)):
        hp.iloc[i] = (1 - alpha1/2) * (1 - alpha1/2) * (series.iloc[i] - 2*series.iloc[i-1] + series.iloc[i-2]) + \
                     2 * (1 - alpha1) * hp.iloc[i-1] - (1 - alpha1) * (1 - alpha1) * hp.iloc[i-2]
    
    # Super Smoother (low-pass)
    a1 = np.exp(-1.414 * np.pi / lp_period)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / lp_period)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1 - c2 - c3
    
    filt = pd.Series(index=series.index, dtype=float)
    filt.iloc[:2] = hp.iloc[:2]
    
    for i in range(2, len(series)):
        filt.iloc[i] = c1 * (hp.iloc[i] + hp.iloc[i-1]) / 2 + c2 * filt.iloc[i-1] + c3 * filt.iloc[i-2]
    
    return filt


def band_pass_filter(series: pd.Series, period: int = 20, bandwidth: float = 0.3) -> pd.Series:
    """
    Ehlers Band-Pass Filter.
    Isolates a specific frequency band.
    """
    beta = np.cos(2 * np.pi / period)
    gamma = 1 / np.cos(4 * np.pi * bandwidth / period)
    alpha = gamma - np.sqrt(gamma * gamma - 1)
    
    bp = pd.Series(index=series.index, dtype=float)
    bp.iloc[:2] = 0
    
    for i in range(2, len(series)):
        bp.iloc[i] = 0.5 * (1 - alpha) * (series.iloc[i] - series.iloc[i-2]) + \
                     beta * (1 + alpha) * bp.iloc[i-1] - alpha * bp.iloc[i-2]
    
    return bp


class RoofingFilter:
    """Ehlers Roofing Filter class wrapper"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.hp_period = self.config.get('hp_period', 48)
        self.lp_period = self.config.get('lp_period', 10)
        logger.info("RoofingFilter initialized")
    
    def calculate(self, series: pd.Series, hp_period: int = None, lp_period: int = None) -> pd.Series:
        """Calculate roofing filter"""
        hp = hp_period or self.hp_period
        lp = lp_period or self.lp_period
        return roofing_filter(series, hp, lp)
    
    def calculate_bandpass(self, series: pd.Series, period: int = 20, bandwidth: float = 0.3) -> pd.Series:
        """Calculate band-pass filter"""
        return band_pass_filter(series, period, bandwidth)
