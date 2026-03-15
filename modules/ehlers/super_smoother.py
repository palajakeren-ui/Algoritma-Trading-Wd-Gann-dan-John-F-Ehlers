"""
Ehlers Super Smoother Module
John Ehlers' Super Smoother filter
"""
import numpy as np
import pandas as pd
from typing import Optional
from loguru import logger


def super_smoother(series: pd.Series, period: int = 10) -> pd.Series:
    """
    Ehlers Super Smoother Filter.
    Two-pole Butterworth filter implementation.
    """
    a1 = np.exp(-1.414 * np.pi / period)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / period)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1 - c2 - c3
    
    result = pd.Series(index=series.index, dtype=float)
    result.iloc[0] = series.iloc[0]
    result.iloc[1] = series.iloc[1]
    
    for i in range(2, len(series)):
        result.iloc[i] = c1 * (series.iloc[i] + series.iloc[i-1]) / 2 + \
                         c2 * result.iloc[i-1] + c3 * result.iloc[i-2]
    
    return result


def super_smoother_3pole(series: pd.Series, period: int = 20) -> pd.Series:
    """
    Ehlers 3-Pole Super Smoother.
    Sharper cutoff but more lag.
    """
    a1 = np.exp(-np.pi / period)
    b1 = 2 * a1 * np.cos(1.738 * np.pi / period)
    c1 = a1 * a1
    
    coef2 = b1 + c1
    coef3 = -(c1 + b1 * c1)
    coef4 = c1 * c1
    coef1 = 1 - coef2 - coef3 - coef4
    
    result = pd.Series(index=series.index, dtype=float)
    result.iloc[:3] = series.iloc[:3]
    
    for i in range(3, len(series)):
        result.iloc[i] = coef1 * series.iloc[i] + \
                         coef2 * result.iloc[i-1] + \
                         coef3 * result.iloc[i-2] + \
                         coef4 * result.iloc[i-3]
    
    return result


class SuperSmoother:
    """Ehlers Super Smoother class wrapper"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.default_period = self.config.get('period', 10)
        logger.info("SuperSmoother initialized")
    
    def calculate(self, series: pd.Series, period: int = None) -> pd.Series:
        """Calculate Super Smoother"""
        period = period or self.default_period
        return super_smoother(series, period)
    
    def calculate_3pole(self, series: pd.Series, period: int = None) -> pd.Series:
        """Calculate 3-pole Super Smoother"""
        period = period or self.default_period * 2
        return super_smoother_3pole(series, period)
