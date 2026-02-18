"""
Ehlers Hilbert Transform Module
Based on John Ehlers' DSP algorithms from "Rocket Science for Traders"

The Hilbert Transform is a fundamental DSP technique used to compute the
instantaneous phase and period of a cycle. It's the basis for many of
Ehlers' sophisticated indicators.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Tuple, Optional


class HilbertTransform:
    """
    Ehlers Hilbert Transform implementation.
    
    The Hilbert Transform creates a 90-degree phase-shifted version of
    the input signal, enabling calculation of instantaneous phase and
    dominant cycle period.
    """
    
    def __init__(self, smooth_period: int = 4):
        """
        Initialize Hilbert Transform calculator.
        
        Args:
            smooth_period (int): Pre-smoothing period for noise reduction
        """
        self.smooth_period = smooth_period
        logger.info(f"HilbertTransform initialized: smooth_period={smooth_period}")
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Hilbert Transform and derived values.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Column to use as source
            
        Returns:
            pd.DataFrame: Hilbert Transform components
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # Initialize arrays
        smooth = np.zeros(n)
        detrender = np.zeros(n)
        Q1 = np.zeros(n)
        I1 = np.zeros(n)
        jI = np.zeros(n)
        jQ = np.zeros(n)
        I2 = np.zeros(n)
        Q2 = np.zeros(n)
        Re = np.zeros(n)
        Im = np.zeros(n)
        period = np.zeros(n)
        smooth_period = np.zeros(n)
        phase = np.zeros(n)
        
        # Preset initial period
        for i in range(n):
            period[i] = 6
            smooth_period[i] = 6
        
        # Process data
        for i in range(6, n):
            # Weighted moving average
            smooth[i] = (
                4 * prices[i] 
                + 3 * prices[i-1] 
                + 2 * prices[i-2] 
                + prices[i-3]
            ) / 10
            
            # Detrend with Hilbert Transform
            detrender[i] = (
                0.0962 * smooth[i] 
                + 0.5769 * smooth[i-2] 
                - 0.5769 * smooth[i-4] 
                - 0.0962 * smooth[i-6]
            ) * (0.075 * period[i-1] + 0.54)
            
            # Compute InPhase and Quadrature components
            Q1[i] = (
                0.0962 * detrender[i] 
                + 0.5769 * detrender[i-2] 
                - 0.5769 * detrender[i-4] 
                - 0.0962 * detrender[i-6]
            ) * (0.075 * period[i-1] + 0.54)
            
            I1[i] = detrender[i-3]
            
            # Advance phase by 90 degrees
            jI[i] = (
                0.0962 * I1[i] 
                + 0.5769 * I1[i-2] 
                - 0.5769 * I1[i-4] 
                - 0.0962 * I1[i-6]
            ) * (0.075 * period[i-1] + 0.54)
            
            jQ[i] = (
                0.0962 * Q1[i] 
                + 0.5769 * Q1[i-2] 
                - 0.5769 * Q1[i-4] 
                - 0.0962 * Q1[i-6]
            ) * (0.075 * period[i-1] + 0.54)
            
            # Phasor addition for 3-bar averaging
            I2[i] = I1[i] - jQ[i]
            Q2[i] = Q1[i] + jI[i]
            
            # Smooth I and Q components
            I2[i] = 0.2 * I2[i] + 0.8 * I2[i-1]
            Q2[i] = 0.2 * Q2[i] + 0.8 * Q2[i-1]
            
            # Homodyne Discriminator
            Re[i] = I2[i] * I2[i-1] + Q2[i] * Q2[i-1]
            Im[i] = I2[i] * Q2[i-1] - Q2[i] * I2[i-1]
            
            Re[i] = 0.2 * Re[i] + 0.8 * Re[i-1]
            Im[i] = 0.2 * Im[i] + 0.8 * Im[i-1]
            
            # Calculate period
            if Im[i] != 0 and Re[i] != 0:
                period[i] = 2 * np.pi / np.arctan(Im[i] / Re[i])
            
            # Limit period
            if period[i] > 1.5 * period[i-1]:
                period[i] = 1.5 * period[i-1]
            if period[i] < 0.67 * period[i-1]:
                period[i] = 0.67 * period[i-1]
            if period[i] < 6:
                period[i] = 6
            if period[i] > 50:
                period[i] = 50
            
            period[i] = 0.2 * period[i] + 0.8 * period[i-1]
            smooth_period[i] = 0.33 * period[i] + 0.67 * smooth_period[i-1]
            
            # Calculate phase
            if I1[i] != 0:
                phase[i] = np.degrees(np.arctan(Q1[i] / I1[i]))
        
        # Create result DataFrame
        result = pd.DataFrame({
            'hilbert_i': I2,
            'hilbert_q': Q2,
            'hilbert_period': smooth_period,
            'hilbert_phase': phase,
            'hilbert_re': Re,
            'hilbert_im': Im,
            'hilbert_smooth': smooth,
            'hilbert_detrender': detrender
        }, index=data.index)
        
        return result
    
    def get_sine_wave(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Generate Sine Wave indicator from Hilbert Transform.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Source column
            
        Returns:
            pd.DataFrame: Sine wave and lead wave
        """
        ht = self.calculate(data, source_col)
        
        phase = ht['hilbert_phase'].values
        n = len(phase)
        
        sine = np.sin(np.radians(phase))
        lead_sine = np.sin(np.radians(phase + 45))
        
        # Signal generation
        signal = np.zeros(n)
        for i in range(1, n):
            if sine[i] > lead_sine[i] and sine[i-1] <= lead_sine[i-1]:
                signal[i] = 1  # Mode change to trend up
            elif sine[i] < lead_sine[i] and sine[i-1] >= lead_sine[i-1]:
                signal[i] = -1  # Mode change to trend down
        
        result = pd.DataFrame({
            'ht_sine': sine,
            'ht_lead_sine': lead_sine,
            'ht_signal': signal
        }, index=data.index)
        
        return result


def hilbert_transform(
    data: pd.DataFrame,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Hilbert Transform.
    
    Args:
        data (pd.DataFrame): OHLCV data
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Hilbert Transform results
    """
    ht = HilbertTransform()
    return ht.calculate(data, source_col)


class DominantCyclePeriod:
    """
    Dominant Cycle Period indicator using Hilbert Transform.
    
    Identifies the dominant market cycle period at any point in time.
    """
    
    def __init__(self, smooth_factor: float = 0.2):
        """
        Initialize Dominant Cycle Period calculator.
        
        Args:
            smooth_factor (float): Smoothing factor for period estimation
        """
        self.smooth_factor = smooth_factor
        self.ht = HilbertTransform()
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Dominant Cycle Period.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Source column
            
        Returns:
            pd.DataFrame: Dominant cycle period values
        """
        ht_result = self.ht.calculate(data, source_col)
        
        period = ht_result['hilbert_period'].values
        n = len(period)
        
        # Calculate cycle mode
        cycle_mode = np.zeros(n)
        for i in range(1, n):
            # Low period = trending, high period = cycling
            if period[i] > 20:
                cycle_mode[i] = 1  # Cycle mode
            elif period[i] < 10:
                cycle_mode[i] = -1  # Trend mode
            else:
                cycle_mode[i] = 0  # Mixed mode
        
        result = pd.DataFrame({
            'dominant_period': period,
            'cycle_mode': cycle_mode,
            'is_cycling': period > 15,
            'is_trending': period < 12
        }, index=data.index)
        
        return result


def dominant_cycle_period(
    data: pd.DataFrame,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Dominant Cycle Period.
    
    Args:
        data (pd.DataFrame): OHLCV data
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Dominant cycle period results
    """
    dcp = DominantCyclePeriod()
    return dcp.calculate(data, source_col)


if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)
    n = 250
    
    t = np.arange(n)
    # Create data with varying cycle period
    cycle1 = 5 * np.sin(2 * np.pi * t[:100] / 10)
    cycle2 = 5 * np.sin(2 * np.pi * t[100:] / 25)
    cycle = np.concatenate([cycle1, cycle2])
    
    trend = t * 0.05
    noise = np.random.randn(n) * 0.5
    close = 100 + trend + cycle + noise
    
    data = pd.DataFrame({
        'open': close - 0.5,
        'high': close + 1,
        'low': close - 1,
        'close': close,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    # Test Hilbert Transform
    ht = HilbertTransform()
    result = ht.calculate(data)
    
    print("Hilbert Transform Results:")
    print(result.tail(10))
    
    # Test Sine Wave
    sw = ht.get_sine_wave(data)
    
    print("\nSine Wave Results:")
    print(sw.tail(10))
    
    # Test Dominant Cycle Period
    dcp = DominantCyclePeriod()
    period_result = dcp.calculate(data)
    
    print("\nDominant Cycle Period Results:")
    print(period_result.tail(10))
