"""
Technical Feature Engine
Standard technical analysis features for ML.
"""

import numpy as np
import pandas as pd
from typing import Dict
from loguru import logger


class TechnicalFeatureEngine:
    """
    Standard technical indicators as ML features.
    All outputs normalized to [-1, 1] or [0, 1].
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.rsi_period = config.get("rsi_period", 14)
        self.atr_period = config.get("atr_period", 14)
        self.bb_period = config.get("bb_period", 20)
        self.macd_fast = config.get("macd_fast", 12)
        self.macd_slow = config.get("macd_slow", 26)
        self.macd_signal = config.get("macd_signal", 9)
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all technical features."""
        features = pd.DataFrame(index=df.index)
        
        close = df["close"].values.astype(float)
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        volume = df["volume"].values.astype(float) if "volume" in df.columns else np.ones(len(close))
        
        # RSI (normalized 0-1)
        features["tech_rsi"] = self._rsi(close, self.rsi_period) / 100.0
        
        # MACD histogram (normalized)
        macd, signal, hist = self._macd(close)
        max_hist = np.max(np.abs(hist)) if np.max(np.abs(hist)) > 0 else 1
        features["tech_macd_hist"] = hist / max_hist
        
        # Bollinger Band position (0 = lower band, 1 = upper band)
        features["tech_bb_position"] = self._bb_position(close, self.bb_period)
        
        # ATR ratio (normalized volatility)
        atr = self._atr(high, low, close, self.atr_period)
        features["tech_atr_ratio"] = np.where(close > 0, atr / close, 0)
        
        # Volume ratio
        vol_ma = self._sma(volume, 20)
        features["tech_vol_ratio"] = np.where(vol_ma > 0, volume / vol_ma, 1.0)
        features["tech_vol_ratio"] = np.clip(features["tech_vol_ratio"], 0, 5) / 5  # 0-1
        
        # Price momentum (ROC)
        for period in [5, 10, 20]:
            roc = np.zeros(len(close))
            for i in range(period, len(close)):
                if close[i - period] > 0:
                    roc[i] = (close[i] - close[i - period]) / close[i - period]
            features[f"tech_roc_{period}"] = np.clip(roc, -0.2, 0.2) * 5  # normalize
        
        # Moving average convergence (multiple timeframes)
        for fast, slow in [(5, 20), (10, 50), (20, 100)]:
            ma_fast = self._ema(close, fast)
            ma_slow = self._ema(close, slow)
            diff = np.where(ma_slow > 0, (ma_fast - ma_slow) / ma_slow, 0)
            features[f"tech_ma_cross_{fast}_{slow}"] = np.clip(diff, -0.1, 0.1) * 10
        
        # OBV direction
        features["tech_obv_slope"] = self._obv_slope(close, volume)
        
        # ADX (trend strength)
        features["tech_adx"] = self._adx(high, low, close) / 100.0
        
        logger.debug(f"Technical features computed: {len(features.columns)} features")
        return features
    
    @staticmethod
    def _rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index."""
        n = len(data)
        rsi = np.full(n, 50.0)
        
        if n < period + 1:
            return rsi
        
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, n - 1):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi[i + 1] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i + 1] = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average."""
        result = np.zeros(len(data))
        multiplier = 2.0 / (period + 1)
        result[0] = data[0]
        for i in range(1, len(data)):
            result[i] = (data[i] - result[i-1]) * multiplier + result[i-1]
        return result
    
    @staticmethod
    def _sma(data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average."""
        result = np.zeros(len(data))
        for i in range(len(data)):
            start = max(0, i - period + 1)
            result[i] = np.mean(data[start:i+1])
        return result
    
    def _macd(self, data: np.ndarray):
        """MACD line, signal, histogram."""
        fast = self._ema(data, self.macd_fast)
        slow = self._ema(data, self.macd_slow)
        macd = fast - slow
        signal = self._ema(macd, self.macd_signal)
        hist = macd - signal
        return macd, signal, hist
    
    def _bb_position(self, data: np.ndarray, period: int) -> np.ndarray:
        """Position within Bollinger Bands (0 = lower, 1 = upper)."""
        n = len(data)
        result = np.full(n, 0.5)
        
        for i in range(period, n):
            window = data[i-period+1:i+1]
            ma = np.mean(window)
            std = np.std(window)
            
            if std > 0:
                upper = ma + 2 * std
                lower = ma - 2 * std
                band_width = upper - lower
                if band_width > 0:
                    result[i] = np.clip((data[i] - lower) / band_width, 0, 1)
        
        return result
    
    @staticmethod
    def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Average True Range."""
        n = len(close)
        tr = np.zeros(n)
        atr = np.zeros(n)
        
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1]),
            )
        
        atr[:period] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
        
        return atr
    
    @staticmethod
    def _obv_slope(close: np.ndarray, volume: np.ndarray, lookback: int = 10) -> np.ndarray:
        """On-Balance Volume slope (normalized)."""
        n = len(close)
        obv = np.zeros(n)
        
        for i in range(1, n):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]
        
        # Slope of OBV
        slope = np.zeros(n)
        for i in range(lookback, n):
            x = np.arange(lookback, dtype=float)
            y = obv[i-lookback:i]
            if np.std(y) > 0:
                coeffs = np.polyfit(x, y, 1)
                slope[i] = coeffs[0]
        
        max_slope = np.max(np.abs(slope)) if np.max(np.abs(slope)) > 0 else 1
        return np.clip(slope / max_slope, -1, 1)
    
    @staticmethod
    def _adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Average Directional Index."""
        n = len(close)
        adx = np.zeros(n)
        
        if n < period * 2:
            return adx
        
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        tr = np.zeros(n)
        
        for i in range(1, n):
            up = high[i] - high[i-1]
            down = low[i-1] - low[i]
            
            plus_dm[i] = up if up > down and up > 0 else 0
            minus_dm[i] = down if down > up and down > 0 else 0
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        
        # Smooth
        atr_s = np.zeros(n)
        pdm_s = np.zeros(n)
        mdm_s = np.zeros(n)
        
        atr_s[period] = np.sum(tr[1:period+1])
        pdm_s[period] = np.sum(plus_dm[1:period+1])
        mdm_s[period] = np.sum(minus_dm[1:period+1])
        
        for i in range(period + 1, n):
            atr_s[i] = atr_s[i-1] - atr_s[i-1]/period + tr[i]
            pdm_s[i] = pdm_s[i-1] - pdm_s[i-1]/period + plus_dm[i]
            mdm_s[i] = mdm_s[i-1] - mdm_s[i-1]/period + minus_dm[i]
        
        # DI
        plus_di = np.where(atr_s > 0, 100 * pdm_s / atr_s, 0)
        minus_di = np.where(atr_s > 0, 100 * mdm_s / atr_s, 0)
        
        # DX
        di_sum = plus_di + minus_di
        dx = np.where(di_sum > 0, 100 * np.abs(plus_di - minus_di) / di_sum, 0)
        
        # ADX (smoothed DX)
        if 2 * period < n:
            adx[2*period] = np.mean(dx[period:2*period+1])
            for i in range(2*period + 1, n):
                adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period
        
        return adx
