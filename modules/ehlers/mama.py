"""
Ehlers MESA Adaptive Moving Average (MAMA) and Following Adaptive Moving Average (FAMA)
Implements John Ehlers' adaptive cycle-based moving average system
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from loguru import logger


def mama(data: pd.DataFrame, fast_limit: float = 0.5, slow_limit: float = 0.05) -> pd.DataFrame:
    """
    Calculates the MESA Adaptive Moving Average (MAMA) and its signal line (FAMA).
    
    Uses Hilbert Transform to detect dominant cycle period and adaptively
    adjust the EMA alpha parameter.

    Args:
        data (pd.DataFrame): DataFrame with 'close' prices.
        fast_limit (float): The fastest alpha value for the EMA (default 0.5).
        slow_limit (float): The slowest alpha value for the EMA (default 0.05).

    Returns:
        pd.DataFrame: A DataFrame with 'MAMA' and 'FAMA' columns.
    """
    close = data['close']
    length = len(close)
    
    # Smooth price using weighted average
    smooth = pd.Series(index=close.index, dtype=float)
    smooth.iloc[:4] = close.iloc[:4]
    
    for i in range(4, length):
        smooth.iloc[i] = (4 * close.iloc[i] + 3 * close.iloc[i-1] + 
                          2 * close.iloc[i-2] + close.iloc[i-3]) / 10.0
    
    # Period adjustment coefficient for Hilbert Transform
    # This is the correct Ehlers coefficient for adaptive period
    period_adj = 0.075 * 24 + 0.54  # Standard period of 24 for base calculation
    
    # Detrender using Hilbert Transform coefficients
    detrender = pd.Series(index=close.index, dtype=float)
    detrender.iloc[:7] = 0
    
    for i in range(7, length):
        detrender.iloc[i] = (0.0962 * smooth.iloc[i] + 0.5769 * smooth.iloc[i-2] - 
                             0.5769 * smooth.iloc[i-4] - 0.0962 * smooth.iloc[i-6]) * period_adj
    
    # InPhase and Quadrature components
    q1 = pd.Series(index=close.index, dtype=float)
    i1 = pd.Series(index=close.index, dtype=float)
    q1.iloc[:7] = 0
    i1.iloc[:7] = 0
    
    for i in range(7, length):
        q1.iloc[i] = (0.0962 * detrender.iloc[i] + 0.5769 * detrender.iloc[i-2] - 
                      0.5769 * detrender.iloc[i-4] - 0.0962 * detrender.iloc[i-6]) * period_adj
        i1.iloc[i] = detrender.iloc[i-3] if i >= 10 else 0
    
    # Hilbert Transform - apply to I and Q
    jI = pd.Series(index=close.index, dtype=float)
    jQ = pd.Series(index=close.index, dtype=float)
    jI.iloc[:7] = 0
    jQ.iloc[:7] = 0
    
    for i in range(7, length):
        jI.iloc[i] = (0.0962 * i1.iloc[i] + 0.5769 * i1.iloc[i-2] - 
                      0.5769 * i1.iloc[i-4] - 0.0962 * i1.iloc[i-6]) * period_adj
        jQ.iloc[i] = (0.0962 * q1.iloc[i] + 0.5769 * q1.iloc[i-2] - 
                      0.5769 * q1.iloc[i-4] - 0.0962 * q1.iloc[i-6]) * period_adj
    
    # Phase calculation
    i2 = pd.Series(index=close.index, dtype=float)
    q2 = pd.Series(index=close.index, dtype=float)
    i2.iloc[:1] = 0
    q2.iloc[:1] = 0
    
    for i in range(1, length):
        i2_val = i1.iloc[i] - jQ.iloc[i]
        q2_val = q1.iloc[i] + jI.iloc[i]
        # Smooth I2 and Q2
        i2.iloc[i] = 0.2 * i2_val + 0.8 * i2.iloc[i-1]
        q2.iloc[i] = 0.2 * q2_val + 0.8 * q2.iloc[i-1]
    
    # Calculate Real and Imaginary components for period
    re = pd.Series(index=close.index, dtype=float)
    im = pd.Series(index=close.index, dtype=float)
    re.iloc[:1] = 0
    im.iloc[:1] = 0
    
    for i in range(1, length):
        re_val = i2.iloc[i] * i2.iloc[i-1] + q2.iloc[i] * q2.iloc[i-1]
        im_val = i2.iloc[i] * q2.iloc[i-1] - q2.iloc[i] * i2.iloc[i-1]
        re.iloc[i] = 0.2 * re_val + 0.8 * re.iloc[i-1]
        im.iloc[i] = 0.2 * im_val + 0.8 * im.iloc[i-1]
    
    # Calculate dominant cycle period
    period = pd.Series(index=close.index, dtype=float)
    period.iloc[:1] = 24  # Default period
    
    for i in range(1, length):
        # Safe calculation avoiding division by zero
        denom = np.arctan2(im.iloc[i], re.iloc[i]) if re.iloc[i] != 0 or im.iloc[i] != 0 else 0.001
        if denom != 0:
            period.iloc[i] = 2 * np.pi / abs(denom)
        else:
            period.iloc[i] = period.iloc[i-1] if i > 0 else 24
        
        # Clamp period to reasonable range
        period.iloc[i] = max(6, min(50, period.iloc[i]))
    
    # Adaptive Alpha
    alpha = pd.Series(index=close.index, dtype=float)
    for i in range(length):
        period_val = period.iloc[i] if period.iloc[i] > 0 else 24
        a = fast_limit / (period_val / 10.0)
        a = max(slow_limit, min(fast_limit, a))
        alpha.iloc[i] = a
    
    # MAMA and FAMA calculation using iterative approach
    mama_series = pd.Series(index=close.index, dtype=float)
    fama_series = pd.Series(index=close.index, dtype=float)
    
    mama_series.iloc[0] = close.iloc[0]
    fama_series.iloc[0] = close.iloc[0]
    
    for i in range(1, length):
        a = alpha.iloc[i]
        mama_series.iloc[i] = a * close.iloc[i] + (1 - a) * mama_series.iloc[i-1]
        fama_series.iloc[i] = 0.5 * a * mama_series.iloc[i] + (1 - 0.5 * a) * fama_series.iloc[i-1]
    
    return pd.DataFrame({'MAMA': mama_series, 'FAMA': fama_series}, index=data.index)


class MAMAIndicator:
    """MAMA/FAMA Indicator class wrapper"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.fast_limit = self.config.get('fast_limit', 0.5)
        self.slow_limit = self.config.get('slow_limit', 0.05)
        logger.info(f"MAMAIndicator initialized with fast={self.fast_limit}, slow={self.slow_limit}")
    
    def calculate(self, data: pd.DataFrame, fast_limit: float = None, 
                  slow_limit: float = None) -> Dict[str, pd.Series]:
        """Calculate MAMA and FAMA"""
        fast = fast_limit or self.fast_limit
        slow = slow_limit or self.slow_limit
        result = mama(data, fast, slow)
        return {
            'mama': result['MAMA'],
            'fama': result['FAMA']
        }
    
    def get_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate buy/sell signals based on MAMA/FAMA crossover"""
        result = mama(data, self.fast_limit, self.slow_limit)
        signals = pd.Series(index=data.index, data='')
        
        # Buy when MAMA crosses above FAMA
        signals[(result['MAMA'] > result['FAMA']) & 
                (result['MAMA'].shift(1) <= result['FAMA'].shift(1))] = 'BUY'
        # Sell when MAMA crosses below FAMA
        signals[(result['MAMA'] < result['FAMA']) & 
                (result['MAMA'].shift(1) >= result['FAMA'].shift(1))] = 'SELL'
        
        return signals
    
    def get_trend(self, data: pd.DataFrame) -> pd.Series:
        """Get trend direction"""
        result = mama(data, self.fast_limit, self.slow_limit)
        trend = pd.Series(index=data.index, data='neutral')
        trend[result['MAMA'] > result['FAMA']] = 'bullish'
        trend[result['MAMA'] < result['FAMA']] = 'bearish'
        return trend
