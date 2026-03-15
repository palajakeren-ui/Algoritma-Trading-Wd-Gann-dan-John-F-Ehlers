"""
Pattern Recognition Module
Candlestick and chart pattern recognition
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger


class PatternRecognition:
    """
    Pattern recognition for candlestick and chart patterns.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize pattern recognition.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.detected_patterns = []
        logger.info("PatternRecognition initialized")
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect candlestick patterns in price data.
        
        Args:
            df: DataFrame with OHLC columns (open, high, low, close)
            
        Returns:
            DataFrame with pattern signals
        """
        result = df.copy()
        
        # Calculate body and shadows
        result['body'] = result['close'] - result['open']
        result['body_abs'] = abs(result['body'])
        result['upper_shadow'] = result['high'] - result[['open', 'close']].max(axis=1)
        result['lower_shadow'] = result[['open', 'close']].min(axis=1) - result['low']
        result['range'] = result['high'] - result['low']
        
        # Detect patterns
        result['doji'] = self._detect_doji(result)
        result['hammer'] = self._detect_hammer(result)
        result['shooting_star'] = self._detect_shooting_star(result)
        result['engulfing_bullish'] = self._detect_engulfing_bullish(result)
        result['engulfing_bearish'] = self._detect_engulfing_bearish(result)
        result['morning_star'] = self._detect_morning_star(result)
        result['evening_star'] = self._detect_evening_star(result)
        
        # Combine into pattern column
        patterns = []
        for i, row in result.iterrows():
            p = []
            if row.get('doji', False): p.append('Doji')
            if row.get('hammer', False): p.append('Hammer')
            if row.get('shooting_star', False): p.append('Shooting Star')
            if row.get('engulfing_bullish', False): p.append('Bullish Engulfing')
            if row.get('engulfing_bearish', False): p.append('Bearish Engulfing')
            if row.get('morning_star', False): p.append('Morning Star')
            if row.get('evening_star', False): p.append('Evening Star')
            patterns.append(', '.join(p) if p else None)
        
        result['patterns'] = patterns
        
        # Log detected patterns
        pattern_count = result['patterns'].notna().sum()
        logger.info(f"Detected {pattern_count} candlestick pattern occurrences")
        
        return result
    
    def _detect_doji(self, df: pd.DataFrame) -> pd.Series:
        """Detect Doji pattern"""
        doji_ratio = 0.1  # Body less than 10% of range
        return df['body_abs'] < (df['range'] * doji_ratio)
    
    def _detect_hammer(self, df: pd.DataFrame) -> pd.Series:
        """Detect Hammer pattern"""
        small_body = df['body_abs'] < (df['range'] * 0.3)
        long_lower = df['lower_shadow'] > (df['body_abs'] * 2)
        small_upper = df['upper_shadow'] < (df['body_abs'] * 0.5)
        downtrend = df['close'].shift(1) > df['close'].shift(5)
        
        return small_body & long_lower & small_upper & downtrend
    
    def _detect_shooting_star(self, df: pd.DataFrame) -> pd.Series:
        """Detect Shooting Star pattern"""
        small_body = df['body_abs'] < (df['range'] * 0.3)
        long_upper = df['upper_shadow'] > (df['body_abs'] * 2)
        small_lower = df['lower_shadow'] < (df['body_abs'] * 0.5)
        uptrend = df['close'].shift(1) < df['close'].shift(5)
        
        return small_body & long_upper & small_lower & uptrend
    
    def _detect_engulfing_bullish(self, df: pd.DataFrame) -> pd.Series:
        """Detect Bullish Engulfing pattern"""
        prev_bearish = df['close'].shift(1) < df['open'].shift(1)
        curr_bullish = df['close'] > df['open']
        engulfs = (df['close'] > df['open'].shift(1)) & (df['open'] < df['close'].shift(1))
        
        return prev_bearish & curr_bullish & engulfs
    
    def _detect_engulfing_bearish(self, df: pd.DataFrame) -> pd.Series:
        """Detect Bearish Engulfing pattern"""
        prev_bullish = df['close'].shift(1) > df['open'].shift(1)
        curr_bearish = df['close'] < df['open']
        engulfs = (df['close'] < df['open'].shift(1)) & (df['open'] > df['close'].shift(1))
        
        return prev_bullish & curr_bearish & engulfs
    
    def _detect_morning_star(self, df: pd.DataFrame) -> pd.Series:
        """Detect Morning Star pattern (3-candle)"""
        first_bearish = df['close'].shift(2) < df['open'].shift(2)
        first_large = df['body_abs'].shift(2) > df['range'].shift(2) * 0.5
        
        second_small = df['body_abs'].shift(1) < df['range'].shift(1) * 0.3
        gap_down = df['high'].shift(1) < df['low'].shift(2)
        
        third_bullish = df['close'] > df['open']
        third_large = df['body_abs'] > df['range'] * 0.5
        closes_above_mid = df['close'] > (df['open'].shift(2) + df['close'].shift(2)) / 2
        
        return first_bearish & first_large & second_small & third_bullish & third_large & closes_above_mid
    
    def _detect_evening_star(self, df: pd.DataFrame) -> pd.Series:
        """Detect Evening Star pattern (3-candle)"""
        first_bullish = df['close'].shift(2) > df['open'].shift(2)
        first_large = df['body_abs'].shift(2) > df['range'].shift(2) * 0.5
        
        second_small = df['body_abs'].shift(1) < df['range'].shift(1) * 0.3
        gap_up = df['low'].shift(1) > df['high'].shift(2)
        
        third_bearish = df['close'] < df['open']
        third_large = df['body_abs'] > df['range'] * 0.5
        closes_below_mid = df['close'] < (df['open'].shift(2) + df['close'].shift(2)) / 2
        
        return first_bullish & first_large & second_small & third_bearish & third_large & closes_below_mid
    
    def detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect chart patterns (head & shoulders, double top/bottom, etc.)
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected patterns with details
        """
        patterns = []
        
        # Find local peaks and troughs
        peaks = self._find_peaks(df['high'], order=5)
        troughs = self._find_troughs(df['low'], order=5)
        
        # Detect Double Top
        double_tops = self._detect_double_top(df, peaks)
        patterns.extend(double_tops)
        
        # Detect Double Bottom  
        double_bottoms = self._detect_double_bottom(df, troughs)
        patterns.extend(double_bottoms)
        
        # Detect Head & Shoulders
        hs_patterns = self._detect_head_shoulders(df, peaks, troughs)
        patterns.extend(hs_patterns)
        
        logger.info(f"Detected {len(patterns)} chart patterns")
        return patterns
    
    def _find_peaks(self, series: pd.Series, order: int = 5) -> List[int]:
        """Find local maxima in series"""
        peaks = []
        for i in range(order, len(series) - order):
            if all(series.iloc[i] > series.iloc[i-j] for j in range(1, order+1)) and \
               all(series.iloc[i] > series.iloc[i+j] for j in range(1, order+1)):
                peaks.append(i)
        return peaks
    
    def _find_troughs(self, series: pd.Series, order: int = 5) -> List[int]:
        """Find local minima in series"""
        troughs = []
        for i in range(order, len(series) - order):
            if all(series.iloc[i] < series.iloc[i-j] for j in range(1, order+1)) and \
               all(series.iloc[i] < series.iloc[i+j] for j in range(1, order+1)):
                troughs.append(i)
        return troughs
    
    def _detect_double_top(self, df: pd.DataFrame, peaks: List[int]) -> List[Dict]:
        """Detect double top patterns"""
        patterns = []
        tolerance = 0.02  # 2% tolerance
        
        for i in range(len(peaks) - 1):
            p1, p2 = peaks[i], peaks[i+1]
            h1, h2 = df['high'].iloc[p1], df['high'].iloc[p2]
            
            if abs(h1 - h2) / h1 < tolerance and (p2 - p1) > 10:
                patterns.append({
                    'type': 'Double Top',
                    'start_idx': p1,
                    'end_idx': p2,
                    'level': (h1 + h2) / 2,
                    'signal': 'bearish'
                })
        
        return patterns
    
    def _detect_double_bottom(self, df: pd.DataFrame, troughs: List[int]) -> List[Dict]:
        """Detect double bottom patterns"""
        patterns = []
        tolerance = 0.02
        
        for i in range(len(troughs) - 1):
            t1, t2 = troughs[i], troughs[i+1]
            l1, l2 = df['low'].iloc[t1], df['low'].iloc[t2]
            
            if abs(l1 - l2) / l1 < tolerance and (t2 - t1) > 10:
                patterns.append({
                    'type': 'Double Bottom',
                    'start_idx': t1,
                    'end_idx': t2,
                    'level': (l1 + l2) / 2,
                    'signal': 'bullish'
                })
        
        return patterns
    
    def _detect_head_shoulders(self, df: pd.DataFrame, peaks: List[int], troughs: List[int]) -> List[Dict]:
        """Detect Head & Shoulders patterns"""
        patterns = []
        
        # Need at least 3 peaks
        if len(peaks) < 3:
            return patterns
        
        for i in range(len(peaks) - 2):
            left = peaks[i]
            head = peaks[i+1]
            right = peaks[i+2]
            
            left_h = df['high'].iloc[left]
            head_h = df['high'].iloc[head]
            right_h = df['high'].iloc[right]
            
            # Head should be higher than shoulders
            if head_h > left_h and head_h > right_h:
                # Shoulders should be roughly equal
                if abs(left_h - right_h) / left_h < 0.05:
                    patterns.append({
                        'type': 'Head and Shoulders',
                        'left_shoulder': left,
                        'head': head,
                        'right_shoulder': right,
                        'neckline': min(df['low'].iloc[left:right+1]),
                        'signal': 'bearish'
                    })
        
        return patterns


# Example usage
if __name__ == '__main__':
    # Test with dummy data
    dates = pd.date_range('2024-01-01', periods=100)
    df = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(100)),
        'high': 102 + np.cumsum(np.random.randn(100)),
        'low': 98 + np.cumsum(np.random.randn(100)),
        'close': 100 + np.cumsum(np.random.randn(100))
    }, index=dates)
    
    # Fix high/low
    df['high'] = df[['open', 'close', 'high']].max(axis=1) + abs(np.random.randn(100))
    df['low'] = df[['open', 'close', 'low']].min(axis=1) - abs(np.random.randn(100))
    
    pr = PatternRecognition()
    result = pr.detect_candlestick_patterns(df)
    print("Patterns detected:", result['patterns'].dropna().tolist()[:10])
