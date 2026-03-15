"""
Ehlers Cyber Cycle Module
Based on John Ehlers' cycle detection algorithms

The Cyber Cycle is a cycle oscillator that helps identify turning points
in the market by isolating the cyclic component from price data.
"""
import pandas as pd
import numpy as np
from loguru import logger
from typing import Optional


class CyberCycle:
    """
    Ehlers Cyber Cycle Indicator implementation.
    
    Uses a second-order high-pass filter to extract the cyclic component
    from price data, with adjustable alpha parameter for sensitivity.
    """
    
    def __init__(self, alpha: float = 0.07):
        """
        Initialize Cyber Cycle calculator.
        
        Args:
            alpha (float): Smoothing parameter (0-1, default 0.07)
                          Lower values = smoother output, higher values = more responsive
        """
        self.alpha = alpha
        logger.info(f"CyberCycle initialized: alpha={alpha}")
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Cyber Cycle indicator.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Column to use as source
            
        Returns:
            pd.DataFrame: DataFrame with 'cycle' and 'cycle_trigger' columns
        """
        close = data[source_col].values.astype(float)
        n = len(close)
        
        # Initialize arrays
        cycle = np.zeros(n)
        trigger = np.zeros(n)
        
        alpha = self.alpha
        
        # Calculate cyber cycle using iterative approach
        for i in range(n):
            if i < 2:
                cycle[i] = 0.0
            elif i == 2:
                # Initial cycle value
                cycle[i] = (close[i] - 2 * close[i-1] + close[i-2]) / 4.0
            else:
                # Ehlers Cyber Cycle formula
                term1 = (1 - 0.5 * alpha) ** 2 * (close[i] - 2 * close[i-1] + close[i-2])
                term2 = 2 * (1 - alpha) * cycle[i-1]
                term3 = (1 - alpha) ** 2 * cycle[i-2]
                cycle[i] = term1 + term2 - term3
        
        # Create trigger line (2-bar EMA of cycle)
        trigger[0] = cycle[0]
        for i in range(1, n):
            trigger[i] = (2/3) * cycle[i] + (1/3) * trigger[i-1]
        
        # Generate signals
        signal = np.zeros(n)
        for i in range(1, n):
            if cycle[i] > trigger[i] and cycle[i-1] <= trigger[i-1]:
                signal[i] = 1   # Buy signal
            elif cycle[i] < trigger[i] and cycle[i-1] >= trigger[i-1]:
                signal[i] = -1  # Sell signal
        
        result = pd.DataFrame({
            'cycle': cycle,
            'cycle_trigger': trigger,
            'cycle_signal': signal,
            'cycle_overbought': cycle > np.percentile(cycle, 90),
            'cycle_oversold': cycle < np.percentile(cycle, 10)
        }, index=data.index)
        
        return result


def cyber_cycle(
    data: pd.DataFrame, 
    alpha: float = 0.07,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Cyber Cycle calculation.
    
    Args:
        data (pd.DataFrame): OHLCV data
        alpha (float): Smoothing parameter
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Cyber Cycle results
    """
    cc = CyberCycle(alpha)
    return cc.calculate(data, source_col)


if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)
    n = 200
    
    t = np.arange(n)
    cycle_component = 5 * np.sin(2 * np.pi * t / 20)
    trend = t * 0.05
    noise = np.random.randn(n) * 1
    close = 100 + trend + cycle_component + noise
    
    data = pd.DataFrame({
        'open': close - 0.5,
        'high': close + 1,
        'low': close - 1,
        'close': close,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    cc = CyberCycle(alpha=0.07)
    result = cc.calculate(data)
    
    print("Cyber Cycle Results:")
    print(result.tail(10))
