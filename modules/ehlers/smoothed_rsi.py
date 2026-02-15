"""
Ehlers Smoothed RSI Module
Based on John Ehlers' DSP approach to improving the traditional RSI

The Smoothed RSI applies Ehlers' SuperSmoother filter to remove high-frequency
noise before calculating RSI, resulting in smoother and less whipsaw-prone signals.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Optional


class SmoothedRSI:
    """
    Ehlers Smoothed RSI implementation.
    
    Uses SuperSmoother filter to pre-smooth prices before RSI calculation,
    and also smooths the final RSI output for cleaner signals.
    """
    
    def __init__(self, rsi_period: int = 14, smooth_period: int = 10):
        """
        Initialize Smoothed RSI calculator.
        
        Args:
            rsi_period (int): RSI lookback period (default 14)
            smooth_period (int): Smoothing filter period (default 10)
        """
        self.rsi_period = rsi_period
        self.smooth_period = smooth_period
        logger.info(f"SmoothedRSI initialized: rsi_period={rsi_period}, smooth_period={smooth_period}")
    
    def _super_smoother(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Apply Ehlers SuperSmoother filter.
        
        Args:
            data (np.ndarray): Input data
            period (int): Smoothing period
            
        Returns:
            np.ndarray: Smoothed data
        """
        n = len(data)
        result = np.zeros(n)
        
        # Calculate coefficients
        a = np.exp(-np.sqrt(2) * np.pi / period)
        b = 2 * a * np.cos(np.sqrt(2) * np.pi / period)
        
        c2 = b
        c3 = -a * a
        c1 = 1 - c2 - c3
        
        # Apply filter
        for i in range(2, n):
            result[i] = c1 * (data[i] + data[i-1]) / 2 + c2 * result[i-1] + c3 * result[i-2]
        
        return result
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Ehlers Smoothed RSI.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Column to use as source
            
        Returns:
            pd.DataFrame: DataFrame with smoothed RSI values
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # Step 1: Apply SuperSmoother to prices
        smoothed_prices = self._super_smoother(prices, self.smooth_period)
        
        # Step 2: Calculate momentum (change)
        momentum = np.zeros(n)
        for i in range(1, n):
            momentum[i] = smoothed_prices[i] - smoothed_prices[i-1]
        
        # Step 3: Calculate RSI
        gains = np.where(momentum > 0, momentum, 0)
        losses = np.where(momentum < 0, -momentum, 0)
        
        # EMA of gains and losses
        avg_gain = np.zeros(n)
        avg_loss = np.zeros(n)
        
        # Simple average for first period
        if n >= self.rsi_period:
            avg_gain[self.rsi_period] = np.mean(gains[1:self.rsi_period+1])
            avg_loss[self.rsi_period] = np.mean(losses[1:self.rsi_period+1])
        
        # EMA calculation
        alpha = 1 / self.rsi_period
        for i in range(self.rsi_period + 1, n):
            avg_gain[i] = alpha * gains[i] + (1 - alpha) * avg_gain[i-1]
            avg_loss[i] = alpha * losses[i] + (1 - alpha) * avg_loss[i-1]
        
        # Calculate RSI
        rsi = np.zeros(n)
        for i in range(self.rsi_period, n):
            if avg_loss[i] == 0:
                rsi[i] = 100
            else:
                rs = avg_gain[i] / avg_loss[i]
                rsi[i] = 100 - (100 / (1 + rs))
        
        # Step 4: Smooth the RSI output
        smoothed_rsi = self._super_smoother(rsi, self.smooth_period)
        
        # Create result DataFrame
        result = pd.DataFrame({
            'smoothed_rsi': smoothed_rsi,
            'rsi_raw': rsi,
            'rsi_overbought': smoothed_rsi > 70,
            'rsi_oversold': smoothed_rsi < 30,
            'rsi_signal': np.where(smoothed_rsi > 50, 1, np.where(smoothed_rsi < 50, -1, 0))
        }, index=data.index)
        
        return result


def smoothed_rsi(
    data: pd.DataFrame,
    rsi_period: int = 14,
    smooth_period: int = 10,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Ehlers Smoothed RSI.
    
    Args:
        data (pd.DataFrame): OHLCV data
        rsi_period (int): RSI lookback period
        smooth_period (int): Smoothing filter period
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Smoothed RSI results
    """
    srsi = SmoothedRSI(rsi_period, smooth_period)
    return srsi.calculate(data, source_col)


class LaguerreRSI:
    """
    Laguerre RSI - Ehlers' alternative RSI implementation.
    
    Uses Laguerre polynomials for smooth filtering with minimal lag.
    """
    
    def __init__(self, gamma: float = 0.5):
        """
        Initialize Laguerre RSI.
        
        Args:
            gamma (float): Damping factor (0-1, default 0.5)
        """
        self.gamma = gamma
        logger.info(f"LaguerreRSI initialized: gamma={gamma}")
    
    def calculate(self, data: pd.DataFrame, source_col: str = 'close') -> pd.DataFrame:
        """
        Calculate Laguerre RSI.
        
        Args:
            data (pd.DataFrame): OHLCV data
            source_col (str): Source column
            
        Returns:
            pd.DataFrame: Laguerre RSI values
        """
        prices = data[source_col].values.astype(float)
        n = len(prices)
        
        # Laguerre filter variables
        L0 = np.zeros(n)
        L1 = np.zeros(n)
        L2 = np.zeros(n)
        L3 = np.zeros(n)
        
        cu = np.zeros(n)
        cd = np.zeros(n)
        rsi = np.zeros(n)
        
        gamma = self.gamma
        
        for i in range(1, n):
            # Calculate Laguerre filter stages
            L0[i] = (1 - gamma) * prices[i] + gamma * L0[i-1]
            L1[i] = -gamma * L0[i] + L0[i-1] + gamma * L1[i-1]
            L2[i] = -gamma * L1[i] + L1[i-1] + gamma * L2[i-1]
            L3[i] = -gamma * L2[i] + L2[i-1] + gamma * L3[i-1]
            
            # Calculate fractional change accumulation
            cu[i] = 0
            cd[i] = 0
            
            if L0[i] >= L1[i]:
                cu[i] += L0[i] - L1[i]
            else:
                cd[i] += L1[i] - L0[i]
            
            if L1[i] >= L2[i]:
                cu[i] += L1[i] - L2[i]
            else:
                cd[i] += L2[i] - L1[i]
            
            if L2[i] >= L3[i]:
                cu[i] += L2[i] - L3[i]
            else:
                cd[i] += L3[i] - L2[i]
            
            # Calculate RSI
            if cu[i] + cd[i] != 0:
                rsi[i] = cu[i] / (cu[i] + cd[i]) * 100
        
        result = pd.DataFrame({
            'laguerre_rsi': rsi,
            'lrsi_overbought': rsi > 80,
            'lrsi_oversold': rsi < 20,
            'lrsi_signal': np.where(rsi > 50, 1, np.where(rsi < 50, -1, 0))
        }, index=data.index)
        
        return result


def laguerre_rsi(
    data: pd.DataFrame,
    gamma: float = 0.5,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Convenience function for Laguerre RSI.
    
    Args:
        data (pd.DataFrame): OHLCV data
        gamma (float): Damping factor
        source_col (str): Source column
        
    Returns:
        pd.DataFrame: Laguerre RSI results
    """
    lrsi = LaguerreRSI(gamma)
    return lrsi.calculate(data, source_col)


if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)
    n = 200
    
    t = np.arange(n)
    trend = t * 0.1
    noise = np.random.randn(n) * 2
    close = 100 + trend + noise
    
    data = pd.DataFrame({
        'open': close - 0.5,
        'high': close + 1,
        'low': close - 1,
        'close': close,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    # Test Smoothed RSI
    srsi = SmoothedRSI(rsi_period=14, smooth_period=10)
    result = srsi.calculate(data)
    
    print("Smoothed RSI Results:")
    print(result.tail(10))
    
    # Test Laguerre RSI
    lrsi = LaguerreRSI(gamma=0.5)
    lrsi_result = lrsi.calculate(data)
    
    print("\nLaguerre RSI Results:")
    print(lrsi_result.tail(10))
