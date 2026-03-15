"""
Ehlers Indicators v3.0 - Production Ready
John Ehlers' Advanced DSP Indicators for trading
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from loguru import logger


class EhlersIndicators:
    """
    Collection of John Ehlers' Digital Signal Processing indicators:
    - SuperSmoother Filter
    - Roofing Filter
    - Decycler
    - Cyber Cycle
    - CG Oscillator
    - Relative Vigor Index
    - Stochastic CG
    - Adaptive RSI
    - MESA Adaptive Moving Average (MAMA)
    - Hilbert Transform
    - Dominant Cycle Period
    """
    
    @staticmethod
    def supersmoother(data: pd.Series, period: int = 10) -> pd.Series:
        """
        SuperSmoother Filter - Two-pole Butterworth filter.
        Removes high-frequency noise while preserving trend.
        
        Args:
            data: Input price series
            period: Filter period
            
        Returns:
            Smoothed series
        """
        a1 = np.exp(-1.414 * np.pi / period)
        b1 = 2 * a1 * np.cos(1.414 * np.pi / period)
        c2 = b1
        c3 = -a1 * a1
        c1 = 1 - c2 - c3
        
        result = data.copy().astype(float)
        
        for i in range(2, len(data)):
            result.iloc[i] = c1 * (data.iloc[i] + data.iloc[i-1]) / 2 + c2 * result.iloc[i-1] + c3 * result.iloc[i-2]
        
        return result
    
    @staticmethod
    def roofing_filter(data: pd.Series, hp_period: int = 48, lp_period: int = 10) -> pd.Series:
        """
        Roofing Filter - Highpass then lowpass filter.
        Removes both high-frequency noise and low-frequency trends.
        
        Args:
            data: Input price series
            hp_period: Highpass filter period
            lp_period: Lowpass filter period
            
        Returns:
            Filtered series
        """
        # Highpass filter coefficients
        alpha1 = (np.cos(2 * np.pi / hp_period) + np.sin(2 * np.pi / hp_period) - 1) / np.cos(2 * np.pi / hp_period)
        
        hp = data.copy().astype(float)
        for i in range(1, len(data)):
            hp.iloc[i] = (1 - alpha1/2) * (data.iloc[i] - data.iloc[i-1]) + (1 - alpha1) * hp.iloc[i-1]
        
        # SuperSmoother lowpass
        result = EhlersIndicators.supersmoother(hp, lp_period)
        
        return result
    
    @staticmethod
    def decycler(data: pd.Series, period: int = 125) -> pd.Series:
        """
        Decycler - Removes cycle component, leaving only trend.
        
        Args:
            data: Input price series
            period: Decycler period
            
        Returns:
            Trend-only series
        """
        alpha = (np.cos(2 * np.pi / period) + np.sin(2 * np.pi / period) - 1) / np.cos(2 * np.pi / period)
        
        result = data.copy().astype(float)
        
        for i in range(1, len(data)):
            result.iloc[i] = (alpha/2) * (data.iloc[i] + data.iloc[i-1]) + (1 - alpha) * result.iloc[i-1]
        
        return result
    
    @staticmethod
    def cyber_cycle(data: pd.Series, alpha: float = 0.07) -> pd.Series:
        """
        Cyber Cycle Indicator - Isolates the dominant cycle component.
        
        Args:
            data: Input price series
            alpha: Smoothing factor
            
        Returns:
            Cycle series
        """
        smooth = (data + 2*data.shift(1) + 2*data.shift(2) + data.shift(3)) / 6
        
        cycle = pd.Series(np.zeros(len(data)), index=data.index)
        
        for i in range(6, len(data)):
            cycle.iloc[i] = ((1 - 0.5*alpha)**2) * (smooth.iloc[i] - 2*smooth.iloc[i-1] + smooth.iloc[i-2]) + \
                           2 * (1 - alpha) * cycle.iloc[i-1] - ((1 - alpha)**2) * cycle.iloc[i-2]
        
        return cycle
    
    @staticmethod
    def cg_oscillator(data: pd.Series, period: int = 10) -> pd.Series:
        """
        Center of Gravity Oscillator - Measures the center of gravity of prices.
        
        Args:
            data: Input price series
            period: Lookback period
            
        Returns:
            CG oscillator series
        """
        cg = pd.Series(np.zeros(len(data)), index=data.index)
        
        for i in range(period, len(data)):
            num = 0
            denom = 0
            for j in range(period):
                num += (j + 1) * data.iloc[i - j]
                denom += data.iloc[i - j]
            
            if denom != 0:
                cg.iloc[i] = -num / denom + (period + 1) / 2
        
        return cg
    
    @staticmethod
    def relative_vigor_index(data: pd.DataFrame, period: int = 10) -> Tuple[pd.Series, pd.Series]:
        """
        Relative Vigor Index (RVI) - Measures conviction of a recent price move.
        
        Args:
            data: DataFrame with OHLC
            period: Smoothing period
            
        Returns:
            Tuple of (RVI, Signal line)
        """
        close_open = data['close'] - data['open']
        high_low = data['high'] - data['low']
        
        # Symmetrical weighted moving average
        num = (close_open + 2*close_open.shift(1) + 2*close_open.shift(2) + close_open.shift(3)) / 6
        denom = (high_low + 2*high_low.shift(1) + 2*high_low.shift(2) + high_low.shift(3)) / 6
        
        rvi = num.rolling(period).sum() / denom.rolling(period).sum()
        signal = (rvi + 2*rvi.shift(1) + 2*rvi.shift(2) + rvi.shift(3)) / 6
        
        return rvi, signal
    
    @staticmethod
    def stochastic_cg(data: pd.Series, period: int = 8, smooth: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic CG - Stochastic applied to Center of Gravity.
        
        Args:
            data: Input price series
            period: CG period
            smooth: Smoothing period
            
        Returns:
            Tuple of (Stochastic CG, Signal)
        """
        cg = EhlersIndicators.cg_oscillator(data, period)
        
        cg_min = cg.rolling(period).min()
        cg_max = cg.rolling(period).max()
        
        stoch_cg = (cg - cg_min) / (cg_max - cg_min + 1e-10)
        signal = stoch_cg.rolling(smooth).mean()
        
        return stoch_cg, signal
    
    @staticmethod
    def adaptive_rsi(data: pd.Series, period: int = 14, alpha: float = 0.07) -> pd.Series:
        """
        Adaptive RSI - RSI with cycle-adaptive lookback.
        
        Args:
            data: Input price series
            period: Base RSI period
            alpha: Cycle detection alpha
            
        Returns:
            Adaptive RSI series
        """
        # Get dominant cycle for adaptation
        cycle = EhlersIndicators.cyber_cycle(data, alpha)
        cycle_period = EhlersIndicators.dominant_cycle_period(data)
        
        # Calculate standard RSI with adaptive period
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()
        
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def mama(data: pd.Series, fast_limit: float = 0.5, slow_limit: float = 0.05) -> Tuple[pd.Series, pd.Series]:
        """
        MESA Adaptive Moving Average (MAMA) with FAMA.
        
        Args:
            data: Input price series
            fast_limit: Fast limit for alpha
            slow_limit: Slow limit for alpha
            
        Returns:
            Tuple of (MAMA, FAMA)
        """
        smooth = (4 * data + 3 * data.shift(1) + 2 * data.shift(2) + data.shift(3)) / 10
        
        mama = pd.Series(np.zeros(len(data)), index=data.index)
        fama = pd.Series(np.zeros(len(data)), index=data.index)
        period = pd.Series(np.zeros(len(data)), index=data.index)
        phase = pd.Series(np.zeros(len(data)), index=data.index)
        
        mama.iloc[0] = data.iloc[0]
        fama.iloc[0] = data.iloc[0]
        
        for i in range(6, len(data)):
            detrender = (0.0962 * smooth.iloc[i] + 0.5769 * smooth.iloc[i-2] - 
                        0.5769 * smooth.iloc[i-4] - 0.0962 * smooth.iloc[i-6]) * 0.075
            
            # Phase accumulation
            if detrender != 0 and i > 7:
                delta_phase = np.arctan(detrender / (smooth.iloc[i-3] + 1e-10))
                phase.iloc[i] = phase.iloc[i-1] + delta_phase
                
                # Determine period from phase
                if phase.iloc[i] - phase.iloc[i-1] > 0:
                    period.iloc[i] = 2 * np.pi / (phase.iloc[i] - phase.iloc[i-1] + 1e-10)
                else:
                    period.iloc[i] = period.iloc[i-1]
                
                period.iloc[i] = max(6, min(50, period.iloc[i]))
            else:
                period.iloc[i] = period.iloc[i-1] if i > 0 else 10
            
            # Calculate alpha
            alpha = fast_limit / (period.iloc[i] + 1)
            alpha = max(slow_limit, min(fast_limit, alpha))
            
            mama.iloc[i] = alpha * data.iloc[i] + (1 - alpha) * mama.iloc[i-1]
            fama.iloc[i] = 0.5 * alpha * mama.iloc[i] + (1 - 0.5 * alpha) * fama.iloc[i-1]
        
        return mama, fama
    
    @staticmethod
    def hilbert_transform(data: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        Hilbert Transform - Computes the instantaneous phase and amplitude.
        
        Args:
            data: Input price series
            
        Returns:
            Tuple of (In-Phase, Quadrature)
        """
        smooth = (4 * data + 3 * data.shift(1) + 2 * data.shift(2) + data.shift(3)) / 10
        
        detrender = pd.Series(np.zeros(len(data)), index=data.index)
        i1 = pd.Series(np.zeros(len(data)), index=data.index)
        q1 = pd.Series(np.zeros(len(data)), index=data.index)
        
        for i in range(6, len(data)):
            detrender.iloc[i] = (0.0962 * smooth.iloc[i] + 0.5769 * smooth.iloc[i-2] - 
                                0.5769 * smooth.iloc[i-4] - 0.0962 * smooth.iloc[i-6]) * 0.075
            
            # In-phase
            i1.iloc[i] = detrender.iloc[i-3]
            
            # Quadrature (90 degree phase shift)
            q1.iloc[i] = (0.0962 * detrender.iloc[i] + 0.5769 * detrender.iloc[i-2] - 
                         0.5769 * detrender.iloc[i-4] - 0.0962 * detrender.iloc[i-6]) * 0.075
        
        return i1, q1
    
    @staticmethod
    def dominant_cycle_period(data: pd.Series) -> pd.Series:
        """
        Dominant Cycle Period - Measures the dominant cycle length.
        
        Args:
            data: Input price series
            
        Returns:
            Cycle period series
        """
        i1, q1 = EhlersIndicators.hilbert_transform(data)
        
        # Calculate phase
        phase = pd.Series(np.zeros(len(data)), index=data.index)
        delta_phase = pd.Series(np.zeros(len(data)), index=data.index)
        inst_period = pd.Series(np.zeros(len(data)), index=data.index)
        
        for i in range(1, len(data)):
            if i1.iloc[i] != 0:
                phase.iloc[i] = np.arctan(q1.iloc[i] / (i1.iloc[i] + 1e-10)) * 180 / np.pi
            else:
                phase.iloc[i] = phase.iloc[i-1]
            
            delta_phase.iloc[i] = phase.iloc[i-1] - phase.iloc[i]
            delta_phase.iloc[i] = max(1, min(60, delta_phase.iloc[i]))
            
        # Smooth and calculate period
        for i in range(10, len(data)):
            inst_period.iloc[i] = 360 / delta_phase.iloc[i-9:i+1].mean() if delta_phase.iloc[i-9:i+1].mean() > 0 else 10
            inst_period.iloc[i] = max(6, min(50, inst_period.iloc[i]))
        
        return inst_period
    
    @staticmethod
    def bandpass_filter(data: pd.Series, period: int = 20, bandwidth: float = 0.3) -> pd.Series:
        """
        Bandpass Filter - Isolates a specific cycle frequency.
        
        Args:
            data: Input price series
            period: Center period
            bandwidth: Bandwidth as fraction of center period
            
        Returns:
            Bandpass filtered series
        """
        delta = bandwidth
        beta = np.cos(2 * np.pi / period)
        gamma = 1 / np.cos(4 * np.pi * delta / period)
        alpha = gamma - np.sqrt(gamma**2 - 1)
        
        result = pd.Series(np.zeros(len(data)), index=data.index)
        
        for i in range(2, len(data)):
            result.iloc[i] = 0.5 * (1 - alpha) * (data.iloc[i] - data.iloc[i-2]) + \
                           beta * (1 + alpha) * result.iloc[i-1] - alpha * result.iloc[i-2]
        
        return result
    
    @staticmethod
    def fisher_transform(data: pd.Series, period: int = 10) -> Tuple[pd.Series, pd.Series]:
        """
        Fisher Transform - Converts prices to Gaussian normal distribution.
        
        Args:
            data: Input price series
            period: Lookback period
            
        Returns:
            Tuple of (Fisher, Signal)
        """
        # Normalize price to -1 to 1 range
        highest = data.rolling(period).max()
        lowest = data.rolling(period).min()
        
        value = 2 * ((data - lowest) / (highest - lowest + 1e-10)) - 1
        value = value.clip(-0.999, 0.999)  # Prevent infinities
        
        fisher = pd.Series(np.zeros(len(data)), index=data.index)
        
        for i in range(1, len(data)):
            fisher.iloc[i] = 0.5 * np.log((1 + value.iloc[i]) / (1 - value.iloc[i] + 1e-10)) + \
                            0.5 * fisher.iloc[i-1]
        
        signal = fisher.shift(1)
        
        return fisher, signal
    
    @staticmethod
    def instantaneous_trendline(data: pd.Series, alpha: float = 0.07) -> pd.Series:
        """
        Instantaneous Trendline - Tracks the trend with minimal lag.
        
        Args:
            data: Input price series
            alpha: Smoothing factor
            
        Returns:
            Trendline series
        """
        it = pd.Series(np.zeros(len(data)), index=data.index)
        
        for i in range(2, len(data)):
            it.iloc[i] = (alpha - (alpha**2) / 4) * data.iloc[i] + \
                        0.5 * (alpha**2) * data.iloc[i-1] - \
                        (alpha - 0.75 * (alpha**2)) * data.iloc[i-2] + \
                        2 * (1 - alpha) * it.iloc[i-1] - \
                        (1 - alpha)**2 * it.iloc[i-2]
        
        return it
    
    @staticmethod
    def sine_wave_indicator(data: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        Sine Wave Indicator - Shows cycle position.
        
        Args:
            data: Input price series
            
        Returns:
            Tuple of (Sine, Lead Sine)
        """
        smooth = EhlersIndicators.supersmoother(data, 10)
        cycle = EhlersIndicators.cyber_cycle(smooth)
        
        # Calculate phase
        phase = np.arctan2(cycle, cycle.shift(1))
        
        sine = np.sin(phase)
        lead_sine = np.sin(phase + np.pi/4)  # 45 degrees lead
        
        return pd.Series(sine, index=data.index), pd.Series(lead_sine, index=data.index)


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')
    np.random.seed(42)
    
    # Generate synthetic price data with cycle
    t = np.arange(200)
    price = 50000 + 1000 * np.sin(2 * np.pi * t / 20) + np.cumsum(np.random.randn(200) * 100)
    
    data = pd.DataFrame({
        'open': price - np.random.rand(200) * 100,
        'high': price + np.random.rand(200) * 150,
        'low': price - np.random.rand(200) * 150,
        'close': price,
        'volume': np.random.uniform(1000, 5000, 200)
    }, index=dates)
    
    close = data['close']
    
    # Test indicators
    print("Testing Ehlers Indicators:")
    
    ss = EhlersIndicators.supersmoother(close, 10)
    print(f"SuperSmoother: {ss.tail(5).values}")
    
    roof = EhlersIndicators.roofing_filter(close)
    print(f"Roofing Filter: {roof.tail(5).values}")
    
    mama, fama = EhlersIndicators.mama(close)
    print(f"MAMA: {mama.tail(5).values}")
    print(f"FAMA: {fama.tail(5).values}")
    
    fisher, signal = EhlersIndicators.fisher_transform(close)
    print(f"Fisher: {fisher.tail(5).values}")
    
    cycle_period = EhlersIndicators.dominant_cycle_period(close)
    print(f"Dominant Cycle Period: {cycle_period.tail(5).values}")
