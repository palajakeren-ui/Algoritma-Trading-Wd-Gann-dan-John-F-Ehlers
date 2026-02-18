"""
Ehlers Bandpass Filter Module
Based on John Ehlers' original DSP algorithms from "Cycle Analytics for Traders"

The Bandpass Filter isolates the dominant cycle component from price data,
filtering out both low-frequency trend and high-frequency noise.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Tuple, Optional


class BandpassFilter:
    """
    Ehlers Bandpass Filter implementation.
    
    The bandpass filter passes only the frequencies within a specified band
    (between low and high cutoff frequencies), rejecting all others.
    """
    
    def __init__(self, period: int = 20, bandwidth: float = 0.3):
        """
        Initialize Bandpass Filter.
        
        Args:
            period (int): Center period of the bandpass filter (default 20)
            bandwidth (float): Bandwidth as fraction of period (default 0.3)
        """
        self.period = period
        self.bandwidth = bandwidth
        logger.info(f"BandpassFilter initialized: period={period}, bandwidth={bandwidth}")
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate bandpass filter on price data.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Column to use as source
            
        Returns:
            pd.DataFrame: DataFrame with bandpass and trigger columns
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # Initialize arrays
        bp = np.zeros(n)
        trigger = np.zeros(n)
        
        # Calculate filter coefficients
        L1 = np.cos(2 * np.pi / self.period)
        G1 = np.cos(self.bandwidth * 2 * np.pi / self.period)
        S1 = 1 / G1 - np.sqrt(1 / (G1 ** 2) - 1)
        
        # Coefficient calculations
        beta = (1 - S1) / 2
        gamma = (1 + S1) * L1
        alpha = 1 - gamma - (beta * 2)
        
        # Apply bandpass filter
        for i in range(2, n):
            bp[i] = (
                0.5 * (1 - alpha) * (prices[i] - prices[i-2])
                + gamma * bp[i-1]
                - beta * bp[i-2]
            )
        
        # Trigger is a 1-bar lag
        trigger[1:] = bp[:-1]
        
        # Create result DataFrame
        result = pd.DataFrame({
            'bandpass': bp,
            'bp_trigger': trigger,
            'bp_signal': np.where(bp > trigger, 1, np.where(bp < trigger, -1, 0))
        }, index=data.index)
        
        return result
    
    def get_cycle_period(self, data: pd.DataFrame, source_col: str = 'close') -> pd.Series:
        """
        Estimate the dominant cycle period using bandpass approach.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Source column
            
        Returns:
            pd.Series: Estimated cycle period
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # Instantaneous period estimation
        inst_period = np.full(n, float(self.period))
        dc = np.zeros(n)
        
        # Smooth prices first
        smooth = np.zeros(n)
        for i in range(4, n):
            smooth[i] = (
                4 * prices[i]
                + 3 * prices[i-1]
                + 2 * prices[i-2]
                + prices[i-3]
            ) / 10
        
        # Zero crossing count for period estimation
        zero_cross_count = 0
        last_cross = 0
        
        for i in range(1, n):
            if smooth[i] * smooth[i-1] < 0:  # Zero crossing
                if last_cross > 0:
                    period_estimate = 4 * (i - last_cross)
                    inst_period[i] = min(max(period_estimate, 6), 50)
                last_cross = i
                zero_cross_count += 1
            else:
                inst_period[i] = inst_period[i-1]
        
        return pd.Series(inst_period, index=data.index, name='cycle_period')


def bandpass_filter(
    data: pd.DataFrame,
    period: int = 20,
    bandwidth: float = 0.3,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for bandpass filtering.
    
    Args:
        data (pd.DataFrame): OHLCV data
        period (int): Center period
        bandwidth (float): Bandwidth fraction
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Bandpass results
    """
    bp_filter = BandpassFilter(period, bandwidth)
    return bp_filter.calculate(data, source_col)


class AGCBandpass:
    """
    Automatic Gain Control Bandpass Filter.
    
    AGC normalizes the bandpass output to maintain consistent amplitude,
    making it easier to identify overbought/oversold conditions.
    """
    
    def __init__(self, period: int = 20, bandwidth: float = 0.3):
        """
        Initialize AGC Bandpass Filter.
        
        Args:
            period (int): Center period
            bandwidth (float): Bandwidth fraction
        """
        self.period = period
        self.bandwidth = bandwidth
        self.bp_filter = BandpassFilter(period, bandwidth)
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate AGC normalized bandpass filter.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Source column
            
        Returns:
            pd.DataFrame: Normalized bandpass results
        """
        # Get regular bandpass
        bp_result = self.bp_filter.calculate(data, source_col)
        bp = bp_result['bandpass'].values
        
        n = len(bp)
        peak = np.zeros(n)
        agc_bp = np.zeros(n)
        
        # Track peaks for normalization
        decay = 0.991  # Decay factor for peak tracking
        
        for i in range(n):
            peak[i] = max(abs(bp[i]), peak[i-1] * decay if i > 0 else abs(bp[i]))
            
            if peak[i] != 0:
                agc_bp[i] = bp[i] / peak[i]
        
        result = bp_result.copy()
        result['agc_bandpass'] = agc_bp
        result['bp_overbought'] = result['agc_bandpass'] > 0.8
        result['bp_oversold'] = result['agc_bandpass'] < -0.8
        
        return result


def agc_bandpass(
    data: pd.DataFrame,
    period: int = 20,
    bandwidth: float = 0.3,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for AGC bandpass filtering.
    
    Args:
        data (pd.DataFrame): OHLCV data
        period (int): Center period
        bandwidth (float): Bandwidth fraction
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: AGC normalized bandpass results
    """
    agc = AGCBandpass(period, bandwidth)
    return agc.calculate(data, source_col)


if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)
    n = 200
    
    # Generate synthetic price data with embedded cycle
    t = np.arange(n)
    cycle = 10 * np.sin(2 * np.pi * t / 20)  # 20-period cycle
    trend = t * 0.1
    noise = np.random.randn(n) * 2
    close = 100 + trend + cycle + noise
    
    data = pd.DataFrame({
        'open': close - 0.5,
        'high': close + 1,
        'low': close - 1,
        'close': close,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    # Test bandpass filter
    bp = BandpassFilter(period=20, bandwidth=0.3)
    result = bp.calculate(data)
    
    print("Bandpass Filter Results:")
    print(result.tail(10))
    
    # Test AGC bandpass
    agc = AGCBandpass(period=20, bandwidth=0.3)
    agc_result = agc.calculate(data)
    
    print("\nAGC Bandpass Results:")
    print(agc_result.tail(10))
