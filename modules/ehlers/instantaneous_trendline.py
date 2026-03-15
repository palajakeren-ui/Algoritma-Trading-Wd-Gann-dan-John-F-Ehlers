"""
Ehlers Instantaneous Trendline Module
Based on John Ehlers' DSP algorithms

The Instantaneous Trendline (ITrend) is designed to track price with minimal lag
while filtering out cycle components. It acts as a superior moving average
for identifying the underlying trend.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Optional, Tuple


class InstantaneousTrendline:
    """
    Ehlers Instantaneous Trendline (ITrend) implementation.
    
    The ITrend uses Hilbert Transform principles to create a trendline
    that has minimal lag compared to traditional moving averages.
    """
    
    def __init__(self, alpha: float = 0.07):
        """
        Initialize Instantaneous Trendline.
        
        Args:
            alpha (float): Smoothing factor (default 0.07, range 0.05-0.2)
        """
        self.alpha = alpha
        logger.info(f"InstantaneousTrendline initialized: alpha={alpha}")
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Instantaneous Trendline.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Column to use as source
            
        Returns:
            pd.DataFrame: DataFrame with ITrend and trigger values
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # Initialize arrays
        itrend = np.zeros(n)
        trigger = np.zeros(n)
        
        alpha = self.alpha
        
        # Initialize first values
        for i in range(min(7, n)):
            itrend[i] = prices[i]
        
        # Calculate ITrend
        for i in range(7, n):
            itrend[i] = (
                (alpha - alpha**2 / 4) * prices[i]
                + 0.5 * alpha**2 * prices[i-1]
                - (alpha - 0.75 * alpha**2) * prices[i-2]
                + 2 * (1 - alpha) * itrend[i-1]
                - (1 - alpha)**2 * itrend[i-2]
            )
        
        # Trigger is 2-bar lag
        trigger[2:] = itrend[:-2]
        
        # Signal generation
        signal = np.zeros(n)
        for i in range(1, n):
            if itrend[i] > trigger[i] and itrend[i-1] <= trigger[i-1]:
                signal[i] = 1  # Bullish crossover
            elif itrend[i] < trigger[i] and itrend[i-1] >= trigger[i-1]:
                signal[i] = -1  # Bearish crossover
        
        result = pd.DataFrame({
            'itrend': itrend,
            'itrend_trigger': trigger,
            'itrend_signal': signal,
            'itrend_bullish': itrend > trigger,
            'itrend_bearish': itrend < trigger
        }, index=data.index)
        
        return result


def instantaneous_trendline(
    data: pd.DataFrame,
    alpha: float = 0.07,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Instantaneous Trendline.
    
    Args:
        data (pd.DataFrame): OHLCV data
        alpha (float): Smoothing factor
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: ITrend results
    """
    it = InstantaneousTrendline(alpha)
    return it.calculate(data, source_col)


class TrendVigor:
    """
    Trend Vigor indicator based on ITrend.
    
    Measures the strength and quality of the current trend by comparing
    the cycle component to the trend component.
    """
    
    def __init__(self, period: int = 20):
        """
        Initialize Trend Vigor calculator.
        
        Args:
            period (int): Lookback period for calculations
        """
        self.period = period
        logger.info(f"TrendVigor initialized: period={period}")
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Trend Vigor.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Source column
            
        Returns:
            pd.DataFrame: Trend Vigor values
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # Get ITrend
        itrend_calc = InstantaneousTrendline()
        itrend_result = itrend_calc.calculate(data, source_col)
        itrend = itrend_result['itrend'].values
        
        # Calculate cycle component (price - itrend)
        cycle = prices - itrend
        
        # Calculate Trend Vigor as RMS ratio
        trend_vigor = np.zeros(n)
        
        for i in range(self.period, n):
            cycle_rms = np.sqrt(np.mean(cycle[i-self.period:i]**2))
            itrend_change = abs(itrend[i] - itrend[i-self.period])
            
            if itrend_change > 0:
                trend_vigor[i] = itrend_change / (itrend_change + cycle_rms)
            else:
                trend_vigor[i] = 0
        
        result = pd.DataFrame({
            'trend_vigor': trend_vigor,
            'itrend': itrend,
            'cycle_component': cycle,
            'trend_strong': trend_vigor > 0.6,
            'trend_weak': trend_vigor < 0.3
        }, index=data.index)
        
        return result


def trend_vigor(
    data: pd.DataFrame,
    period: int = 20,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Trend Vigor.
    
    Args:
        data (pd.DataFrame): OHLCV data
        period (int): Lookback period
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Trend Vigor results
    """
    tv = TrendVigor(period)
    return tv.calculate(data, source_col)


class EhlersDecycler:
    """
    Ehlers Decycler indicator.
    
    Removes cycle components from price to reveal pure trend.
    Opposite of the bandpass filter - it passes low frequencies (trend)
    and rejects high frequencies (cycles/noise).
    """
    
    def __init__(self, hp_period: int = 125):
        """
        Initialize Decycler.
        
        Args:
            hp_period (int): High-pass filter period (determines minimum cycle to remove)
        """
        self.hp_period = hp_period
        logger.info(f"EhlersDecycler initialized: hp_period={hp_period}")
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Decycler values.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Source column
            
        Returns:
            pd.DataFrame: Decycler trendline values
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # High-pass filter to remove cycle
        alpha1 = (np.cos(2 * np.pi / self.hp_period) + np.sin(2 * np.pi / self.hp_period) - 1) / \
                 np.cos(2 * np.pi / self.hp_period)
        
        hp = np.zeros(n)
        decycler = np.zeros(n)
        
        for i in range(2, n):
            # High-pass filter
            hp[i] = ((1 - alpha1/2)**2) * (prices[i] - 2*prices[i-1] + prices[i-2]) + \
                    2 * (1 - alpha1) * hp[i-1] - (1 - alpha1)**2 * hp[i-2]
        
        # Decycler is price minus high-pass (i.e., low-pass filtered)
        decycler = prices - hp
        
        # Rate of change of decycler for signal
        decycler_roc = np.zeros(n)
        for i in range(1, n):
            decycler_roc[i] = (decycler[i] - decycler[i-1]) / max(decycler[i-1], 0.001) * 100
        
        result = pd.DataFrame({
            'decycler': decycler,
            'decycler_hp': hp,
            'decycler_roc': decycler_roc,
            'trend_up': decycler_roc > 0,
            'trend_down': decycler_roc < 0
        }, index=data.index)
        
        return result


def ehlers_decycler(
    data: pd.DataFrame,
    hp_period: int = 125,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Ehlers Decycler.
    
    Args:
        data (pd.DataFrame): OHLCV data
        hp_period (int): High-pass filter period
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Decycler results
    """
    dec = EhlersDecycler(hp_period)
    return dec.calculate(data, source_col)


if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)
    n = 200
    
    t = np.arange(n)
    cycle = 5 * np.sin(2 * np.pi * t / 20)  # 20-period cycle
    trend = t * 0.1
    noise = np.random.randn(n) * 1
    close = 100 + trend + cycle + noise
    
    data = pd.DataFrame({
        'open': close - 0.5,
        'high': close + 1,
        'low': close - 1,
        'close': close,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    # Test ITrend
    itrend = InstantaneousTrendline(alpha=0.07)
    result = itrend.calculate(data)
    
    print("Instantaneous Trendline Results:")
    print(result.tail(10))
    
    # Test Trend Vigor
    tv = TrendVigor(period=20)
    tv_result = tv.calculate(data)
    
    print("\nTrend Vigor Results:")
    print(tv_result[['trend_vigor', 'itrend', 'trend_strong']].tail(10))
    
    # Test Decycler
    dec = EhlersDecycler(hp_period=50)
    dec_result = dec.calculate(data)
    
    print("\nDecycler Results:")
    print(dec_result.tail(10))
