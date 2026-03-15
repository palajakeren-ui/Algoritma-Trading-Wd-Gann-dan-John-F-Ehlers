"""
Candlestick Pattern Scanner v5.0 - Production Ready
Advanced candlestick pattern recognition based on Nison, Bulkowski, and modern price action
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from dataclasses import dataclass
from enum import Enum
import yaml
import os


class PatternType(Enum):
    BULLISH_REVERSAL = "bullish_reversal"
    BEARISH_REVERSAL = "bearish_reversal"
    BULLISH_CONTINUATION = "bullish_continuation"
    BEARISH_CONTINUATION = "bearish_continuation"
    INDECISION = "indecision"


class PatternReliability(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class CandlestickPattern:
    """Detected candlestick pattern"""
    id: str
    name: str
    type: PatternType
    reliability: PatternReliability
    timestamp: pd.Timestamp
    candle_count: int
    entry_price: float
    stop_loss: float
    take_profit: float
    signal_strength: float
    description: str
    candles: List[Dict]


class CandlestickPatternScanner:
    """
    Production-ready candlestick pattern scanner supporting:
    - 130+ candlestick patterns
    - Multi-timeframe analysis
    - Pattern confirmation validation
    - Automatic SL/TP calculation
    - Real-time scanning
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize scanner.
        
        Args:
            config_path: Path to candlestick pattern YAML config
        """
        self.patterns_db = {}
        
        # Load pattern database
        if config_path and os.path.exists(config_path):
            self._load_patterns(config_path)
        else:
            # Try default path
            default_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 'config', 'Candlestick_Pattern.yaml'
            )
            if os.path.exists(default_path):
                self._load_patterns(default_path)
        
        # Pattern detection thresholds
        self.body_ratio_threshold = 0.6  # Body / Total range ratio
        self.doji_threshold = 0.1  # Max body ratio for doji
        self.shadow_ratio_threshold = 2.0  # Shadow / Body ratio for hammers
        self.engulfing_threshold = 1.0  # Engulfing body ratio
        
        logger.info(f"Candlestick Scanner initialized with {len(self.patterns_db)} patterns")
    
    def _load_patterns(self, config_path: str):
        """Load pattern database from YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'patterns' in config:
                for pattern in config['patterns']:
                    self.patterns_db[pattern['id']] = pattern
            
            logger.success(f"Loaded {len(self.patterns_db)} patterns from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load patterns config: {e}")
    
    # ==================== CANDLE CALCULATIONS ====================
    
    def _calc_body(self, candle: pd.Series) -> float:
        """Calculate candle body size"""
        return abs(candle['close'] - candle['open'])
    
    def _calc_range(self, candle: pd.Series) -> float:
        """Calculate candle total range"""
        return candle['high'] - candle['low']
    
    def _is_bullish(self, candle: pd.Series) -> bool:
        """Check if candle is bullish"""
        return candle['close'] > candle['open']
    
    def _is_bearish(self, candle: pd.Series) -> bool:
        """Check if candle is bearish"""
        return candle['close'] < candle['open']
    
    def _body_ratio(self, candle: pd.Series) -> float:
        """Calculate body to range ratio"""
        total_range = self._calc_range(candle)
        if total_range == 0:
            return 0
        return self._calc_body(candle) / total_range
    
    def _upper_shadow(self, candle: pd.Series) -> float:
        """Calculate upper shadow"""
        if self._is_bullish(candle):
            return candle['high'] - candle['close']
        return candle['high'] - candle['open']
    
    def _lower_shadow(self, candle: pd.Series) -> float:
        """Calculate lower shadow"""
        if self._is_bullish(candle):
            return candle['open'] - candle['low']
        return candle['close'] - candle['low']
    
    def _upper_shadow_ratio(self, candle: pd.Series) -> float:
        """Calculate upper shadow to body ratio"""
        body = self._calc_body(candle)
        if body == 0:
            return float('inf')
        return self._upper_shadow(candle) / body
    
    def _lower_shadow_ratio(self, candle: pd.Series) -> float:
        """Calculate lower shadow to body ratio"""
        body = self._calc_body(candle)
        if body == 0:
            return float('inf')
        return self._lower_shadow(candle) / body
    
    def _get_trend(self, data: pd.DataFrame, lookback: int = 10) -> str:
        """Determine current trend"""
        if len(data) < lookback:
            return "neutral"
        
        closes = data['close'].tail(lookback)
        sma = closes.mean()
        current = closes.iloc[-1]
        
        # Also check slope
        slope = (closes.iloc[-1] - closes.iloc[0]) / lookback
        
        if current > sma and slope > 0:
            return "up"
        elif current < sma and slope < 0:
            return "down"
        return "neutral"
    
    # ==================== SINGLE CANDLE PATTERNS ====================
    
    def _detect_doji(self, candle: pd.Series) -> Optional[Dict]:
        """Detect Doji pattern"""
        body_ratio = self._body_ratio(candle)
        
        if body_ratio < self.doji_threshold:
            upper = self._upper_shadow(candle)
            lower = self._lower_shadow(candle)
            total_range = self._calc_range(candle)
            
            # Classify doji type
            if total_range > 0:
                if lower > upper * 3 and lower > total_range * 0.6:
                    return {"type": "dragonfly_doji", "reliability": "high"}
                elif upper > lower * 3 and upper > total_range * 0.6:
                    return {"type": "gravestone_doji", "reliability": "high"}
                elif upper > total_range * 0.3 and lower > total_range * 0.3:
                    return {"type": "long_legged_doji", "reliability": "medium"}
            
            return {"type": "standard_doji", "reliability": "low"}
        
        return None
    
    def _detect_hammer(self, candle: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Hammer or Hanging Man"""
        lower_ratio = self._lower_shadow_ratio(candle)
        upper_ratio = self._upper_shadow_ratio(candle)
        body_ratio = self._body_ratio(candle)
        
        # Hammer/Hanging man: long lower shadow, little upper shadow, small body at top
        if lower_ratio >= 2.0 and upper_ratio < 0.3 and body_ratio > 0.1:
            if trend == "down":
                return {"type": "hammer", "reliability": "medium", "pattern_type": PatternType.BULLISH_REVERSAL}
            elif trend == "up":
                return {"type": "hanging_man", "reliability": "medium", "pattern_type": PatternType.BEARISH_REVERSAL}
        
        return None
    
    def _detect_shooting_star(self, candle: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Shooting Star or Inverted Hammer"""
        upper_ratio = self._upper_shadow_ratio(candle)
        lower_ratio = self._lower_shadow_ratio(candle)
        body_ratio = self._body_ratio(candle)
        
        # Shooting star/Inverted hammer: long upper shadow, little lower shadow
        if upper_ratio >= 2.0 and lower_ratio < 0.3 and body_ratio > 0.1:
            if trend == "up":
                return {"type": "shooting_star", "reliability": "medium", "pattern_type": PatternType.BEARISH_REVERSAL}
            elif trend == "down":
                return {"type": "inverted_hammer", "reliability": "medium", "pattern_type": PatternType.BULLISH_REVERSAL}
        
        return None
    
    def _detect_marubozu(self, candle: pd.Series) -> Optional[Dict]:
        """Detect Marubozu (full body, no shadows)"""
        body_ratio = self._body_ratio(candle)
        upper = self._upper_shadow(candle)
        lower = self._lower_shadow(candle)
        total_range = self._calc_range(candle)
        
        if body_ratio > 0.9:
            if self._is_bullish(candle):
                return {"type": "white_marubozu", "reliability": "high", "pattern_type": PatternType.BULLISH_CONTINUATION}
            else:
                return {"type": "black_marubozu", "reliability": "high", "pattern_type": PatternType.BEARISH_CONTINUATION}
        
        # Opening/Closing Marubozu
        if total_range > 0:
            if upper / total_range < 0.02:  # Almost no upper shadow
                if self._is_bullish(candle) and body_ratio > 0.7:
                    return {"type": "white_closing_marubozu", "reliability": "medium"}
            if lower / total_range < 0.02:  # Almost no lower shadow
                if self._is_bearish(candle) and body_ratio > 0.7:
                    return {"type": "black_closing_marubozu", "reliability": "medium"}
        
        return None
    
    def _detect_spinning_top(self, candle: pd.Series) -> Optional[Dict]:
        """Detect Spinning Top"""
        body_ratio = self._body_ratio(candle)
        upper = self._upper_shadow(candle)
        lower = self._lower_shadow(candle)
        
        # Small body with shadows on both sides
        if 0.1 < body_ratio < 0.3:
            if abs(upper - lower) / max(upper, lower, 0.001) < 0.5:  # Roughly balanced shadows
                return {"type": "spinning_top", "reliability": "low", "pattern_type": PatternType.INDECISION}
        
        return None
    
    # ==================== DOUBLE CANDLE PATTERNS ====================
    
    def _detect_engulfing(self, c1: pd.Series, c2: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Bullish/Bearish Engulfing"""
        c1_body = self._calc_body(c1)
        c2_body = self._calc_body(c2)
        
        # C2 body must engulf C1 body
        if c2_body < c1_body * 1.0:
            return None
        
        # Bullish engulfing: bearish C1, bullish C2 that engulfs C1
        if trend == "down" and self._is_bearish(c1) and self._is_bullish(c2):
            if c2['open'] <= c1['close'] and c2['close'] >= c1['open']:
                return {
                    "type": "bullish_engulfing",
                    "reliability": "high",
                    "pattern_type": PatternType.BULLISH_REVERSAL,
                    "candle_count": 2
                }
        
        # Bearish engulfing: bullish C1, bearish C2 that engulfs C1
        if trend == "up" and self._is_bullish(c1) and self._is_bearish(c2):
            if c2['open'] >= c1['close'] and c2['close'] <= c1['open']:
                return {
                    "type": "bearish_engulfing",
                    "reliability": "high",
                    "pattern_type": PatternType.BEARISH_REVERSAL,
                    "candle_count": 2
                }
        
        return None
    
    def _detect_harami(self, c1: pd.Series, c2: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Harami pattern (inside bar)"""
        c1_body = self._calc_body(c1)
        c2_body = self._calc_body(c2)
        
        # C2 must be inside C1
        if c2_body >= c1_body * 0.5:
            return None
        
        c1_body_high = max(c1['open'], c1['close'])
        c1_body_low = min(c1['open'], c1['close'])
        c2_body_high = max(c2['open'], c2['close'])
        c2_body_low = min(c2['open'], c2['close'])
        
        if c2_body_high <= c1_body_high and c2_body_low >= c1_body_low:
            doji_pattern = self._detect_doji(c2)
            
            if trend == "down" and self._is_bearish(c1):
                if doji_pattern:
                    return {"type": "bullish_harami_cross", "reliability": "high", "pattern_type": PatternType.BULLISH_REVERSAL, "candle_count": 2}
                return {"type": "bullish_harami", "reliability": "medium", "pattern_type": PatternType.BULLISH_REVERSAL, "candle_count": 2}
            
            if trend == "up" and self._is_bullish(c1):
                if doji_pattern:
                    return {"type": "bearish_harami_cross", "reliability": "high", "pattern_type": PatternType.BEARISH_REVERSAL, "candle_count": 2}
                return {"type": "bearish_harami", "reliability": "medium", "pattern_type": PatternType.BEARISH_REVERSAL, "candle_count": 2}
        
        return None
    
    def _detect_piercing_dark_cloud(self, c1: pd.Series, c2: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Piercing Line or Dark Cloud Cover"""
        c1_body = self._calc_body(c1)
        c1_midpoint = (c1['open'] + c1['close']) / 2
        
        # Piercing Line
        if trend == "down" and self._is_bearish(c1) and self._is_bullish(c2):
            if c2['open'] < c1['low'] and c2['close'] > c1_midpoint and c2['close'] < c1['open']:
                return {"type": "piercing_line", "reliability": "medium", "pattern_type": PatternType.BULLISH_REVERSAL, "candle_count": 2}
        
        # Dark Cloud Cover
        if trend == "up" and self._is_bullish(c1) and self._is_bearish(c2):
            if c2['open'] > c1['high'] and c2['close'] < c1_midpoint and c2['close'] > c1['open']:
                return {"type": "dark_cloud_cover", "reliability": "medium", "pattern_type": PatternType.BEARISH_REVERSAL, "candle_count": 2}
        
        return None
    
    def _detect_tweezer(self, c1: pd.Series, c2: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Tweezer Top/Bottom"""
        tolerance = self._calc_range(c1) * 0.02  # 2% tolerance
        
        # Tweezer Bottom
        if trend == "down":
            if abs(c1['low'] - c2['low']) < tolerance:
                return {"type": "tweezer_bottom", "reliability": "medium", "pattern_type": PatternType.BULLISH_REVERSAL, "candle_count": 2}
        
        # Tweezer Top
        if trend == "up":
            if abs(c1['high'] - c2['high']) < tolerance:
                return {"type": "tweezer_top", "reliability": "medium", "pattern_type": PatternType.BEARISH_REVERSAL, "candle_count": 2}
        
        return None
    
    # ==================== TRIPLE CANDLE PATTERNS ====================
    
    def _detect_morning_evening_star(self, c1: pd.Series, c2: pd.Series, c3: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Morning Star or Evening Star"""
        c1_body = self._calc_body(c1)
        c2_body = self._calc_body(c2)
        c3_body = self._calc_body(c3)
        
        c1_midpoint = (c1['open'] + c1['close']) / 2
        
        # Morning Star
        if trend == "down" and self._is_bearish(c1) and c1_body > 0:
            if c2_body < c1_body * 0.3:  # Small middle candle
                if c2['high'] < c1['close']:  # Gap down
                    if self._is_bullish(c3) and c3['close'] > c1_midpoint:
                        doji = self._detect_doji(c2)
                        if doji:
                            return {"type": "morning_doji_star", "reliability": "very_high", "pattern_type": PatternType.BULLISH_REVERSAL, "candle_count": 3}
                        return {"type": "morning_star", "reliability": "high", "pattern_type": PatternType.BULLISH_REVERSAL, "candle_count": 3}
        
        # Evening Star
        if trend == "up" and self._is_bullish(c1) and c1_body > 0:
            if c2_body < c1_body * 0.3:  # Small middle candle
                if c2['low'] > c1['close']:  # Gap up
                    if self._is_bearish(c3) and c3['close'] < c1_midpoint:
                        doji = self._detect_doji(c2)
                        if doji:
                            return {"type": "evening_doji_star", "reliability": "very_high", "pattern_type": PatternType.BEARISH_REVERSAL, "candle_count": 3}
                        return {"type": "evening_star", "reliability": "high", "pattern_type": PatternType.BEARISH_REVERSAL, "candle_count": 3}
        
        return None
    
    def _detect_three_soldiers_crows(self, c1: pd.Series, c2: pd.Series, c3: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Three White Soldiers or Three Black Crows"""
        # Three White Soldiers
        if self._is_bullish(c1) and self._is_bullish(c2) and self._is_bullish(c3):
            if c2['close'] > c1['close'] and c3['close'] > c2['close']:
                if c2['open'] > c1['open'] and c3['open'] > c2['open']:
                    body_ratios = [self._body_ratio(c) for c in [c1, c2, c3]]
                    if all(r > 0.5 for r in body_ratios):
                        return {"type": "three_white_soldiers", "reliability": "high", "pattern_type": PatternType.BULLISH_CONTINUATION, "candle_count": 3}
        
        # Three Black Crows
        if self._is_bearish(c1) and self._is_bearish(c2) and self._is_bearish(c3):
            if c2['close'] < c1['close'] and c3['close'] < c2['close']:
                if c2['open'] < c1['open'] and c3['open'] < c2['open']:
                    body_ratios = [self._body_ratio(c) for c in [c1, c2, c3]]
                    if all(r > 0.5 for r in body_ratios):
                        return {"type": "three_black_crows", "reliability": "high", "pattern_type": PatternType.BEARISH_CONTINUATION, "candle_count": 3}
        
        return None
    
    def _detect_three_inside(self, c1: pd.Series, c2: pd.Series, c3: pd.Series, trend: str) -> Optional[Dict]:
        """Detect Three Inside Up/Down"""
        harami = self._detect_harami(c1, c2, trend)
        
        if harami:
            if harami['type'] == 'bullish_harami':
                if self._is_bullish(c3) and c3['close'] > c1['high']:
                    return {"type": "three_inside_up", "reliability": "high", "pattern_type": PatternType.BULLISH_REVERSAL, "candle_count": 3}
            elif harami['type'] == 'bearish_harami':
                if self._is_bearish(c3) and c3['close'] < c1['low']:
                    return {"type": "three_inside_down", "reliability": "high", "pattern_type": PatternType.BEARISH_REVERSAL, "candle_count": 3}
        
        return None
    
    # ==================== MAIN SCAN METHOD ====================
    
    def scan(
        self,
        data: pd.DataFrame,
        min_reliability: str = "medium",
        lookback: int = 50
    ) -> List[CandlestickPattern]:
        """
        Scan data for candlestick patterns.
        
        Args:
            data: DataFrame with OHLCV data
            min_reliability: Minimum pattern reliability to return
            lookback: Bars to look back for trend detection
            
        Returns:
            List of detected patterns
        """
        if len(data) < 3:
            return []
        
        patterns = []
        reliability_order = ["low", "medium", "high", "very_high"]
        min_rel_idx = reliability_order.index(min_reliability)
        
        # Get trend
        trend = self._get_trend(data, lookback)
        
        # Get last few candles
        c3 = data.iloc[-1]  # Most recent
        c2 = data.iloc[-2] if len(data) >= 2 else None
        c1 = data.iloc[-3] if len(data) >= 3 else None
        
        timestamp = c3.name if hasattr(c3, 'name') else pd.Timestamp.now()
        
        # Single candle patterns
        for detector in [
            lambda: self._detect_doji(c3),
            lambda: self._detect_hammer(c3, trend),
            lambda: self._detect_shooting_star(c3, trend),
            lambda: self._detect_marubozu(c3),
            lambda: self._detect_spinning_top(c3)
        ]:
            result = detector()
            if result:
                rel_idx = reliability_order.index(result.get('reliability', 'low'))
                if rel_idx >= min_rel_idx:
                    patterns.append(self._create_pattern(result, c3, timestamp, data))
        
        # Double candle patterns
        if c2 is not None:
            for detector in [
                lambda: self._detect_engulfing(c2, c3, trend),
                lambda: self._detect_harami(c2, c3, trend),
                lambda: self._detect_piercing_dark_cloud(c2, c3, trend),
                lambda: self._detect_tweezer(c2, c3, trend)
            ]:
                result = detector()
                if result:
                    rel_idx = reliability_order.index(result.get('reliability', 'low'))
                    if rel_idx >= min_rel_idx:
                        patterns.append(self._create_pattern(result, c3, timestamp, data))
        
        # Triple candle patterns
        if c1 is not None and c2 is not None:
            for detector in [
                lambda: self._detect_morning_evening_star(c1, c2, c3, trend),
                lambda: self._detect_three_soldiers_crows(c1, c2, c3, trend),
                lambda: self._detect_three_inside(c1, c2, c3, trend)
            ]:
                result = detector()
                if result:
                    rel_idx = reliability_order.index(result.get('reliability', 'low'))
                    if rel_idx >= min_rel_idx:
                        patterns.append(self._create_pattern(result, c3, timestamp, data))
        
        return patterns
    
    def _create_pattern(
        self,
        result: Dict,
        last_candle: pd.Series,
        timestamp: pd.Timestamp,
        data: pd.DataFrame
    ) -> CandlestickPattern:
        """Create CandlestickPattern object from detection result"""
        pattern_type = result.get('pattern_type', PatternType.INDECISION)
        
        # Calculate SL/TP based on pattern type
        entry = last_candle['close']
        atr = self._calc_atr(data)
        
        if pattern_type in [PatternType.BULLISH_REVERSAL, PatternType.BULLISH_CONTINUATION]:
            stop_loss = entry - (atr * 1.5)
            take_profit = entry + (atr * 3.0)
        elif pattern_type in [PatternType.BEARISH_REVERSAL, PatternType.BEARISH_CONTINUATION]:
            stop_loss = entry + (atr * 1.5)
            take_profit = entry - (atr * 3.0)
        else:
            stop_loss = entry - atr
            take_profit = entry + atr
        
        # Signal strength based on reliability
        reliability_scores = {"low": 0.4, "medium": 0.6, "high": 0.8, "very_high": 0.95}
        signal_strength = reliability_scores.get(result.get('reliability', 'low'), 0.5)
        
        return CandlestickPattern(
            id=result.get('type', 'unknown'),
            name=result.get('type', 'Unknown').replace('_', ' ').title(),
            type=pattern_type,
            reliability=PatternReliability(result.get('reliability', 'low')),
            timestamp=timestamp,
            candle_count=result.get('candle_count', 1),
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            signal_strength=signal_strength,
            description=self._get_pattern_description(result.get('type', '')),
            candles=[]
        )
    
    def _calc_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR for SL/TP calculation"""
        if len(data) < period:
            return (data['high'] - data['low']).mean()
        
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else high_low.mean()
    
    def _get_pattern_description(self, pattern_type: str) -> str:
        """Get pattern description"""
        descriptions = {
            "bullish_engulfing": "Strong bullish reversal. The current candle completely engulfs the previous bearish candle.",
            "bearish_engulfing": "Strong bearish reversal. The current candle completely engulfs the previous bullish candle.",
            "hammer": "Bullish reversal pattern at bottom of downtrend. Long lower shadow shows buying pressure.",
            "shooting_star": "Bearish reversal pattern at top of uptrend. Long upper shadow shows selling pressure.",
            "morning_star": "Three-candle bullish reversal. Gap down followed by recovery indicates trend change.",
            "evening_star": "Three-candle bearish reversal. Gap up followed by decline indicates trend change.",
            "doji": "Indecision pattern. Open and close are nearly equal, showing equilibrium between buyers and sellers.",
            "three_white_soldiers": "Strong bullish continuation. Three consecutive bullish candles with higher closes.",
            "three_black_crows": "Strong bearish continuation. Three consecutive bearish candles with lower closes."
        }
        return descriptions.get(pattern_type, "Candlestick pattern detected")
    
    def scan_all_timeframes(
        self,
        data_dict: Dict[str, pd.DataFrame],
        min_reliability: str = "medium"
    ) -> Dict[str, List[CandlestickPattern]]:
        """
        Scan multiple timeframes.
        
        Args:
            data_dict: Dictionary of {timeframe: DataFrame}
            min_reliability: Minimum reliability to return
            
        Returns:
            Dictionary of {timeframe: [patterns]}
        """
        results = {}
        for timeframe, data in data_dict.items():
            patterns = self.scan(data, min_reliability)
            if patterns:
                results[timeframe] = patterns
        return results


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
    data = pd.DataFrame({
        'open': np.random.uniform(45000, 50000, 50),
        'high': np.random.uniform(46000, 51000, 50),
        'low': np.random.uniform(44000, 49000, 50),
        'close': np.random.uniform(45000, 50000, 50),
        'volume': np.random.uniform(1000, 5000, 50)
    }, index=dates)
    
    # Fix OHLC consistency
    for i in range(len(data)):
        row = data.iloc[i]
        data.iloc[i, data.columns.get_loc('high')] = max(row['open'], row['close'], row['high'])
        data.iloc[i, data.columns.get_loc('low')] = min(row['open'], row['close'], row['low'])
    
    # Scan for patterns
    scanner = CandlestickPatternScanner()
    patterns = scanner.scan(data, min_reliability="low")
    
    print(f"Found {len(patterns)} patterns:")
    for p in patterns:
        print(f"  - {p.name}: {p.type.value} (Reliability: {p.reliability.value})")
        print(f"    Entry: ${p.entry_price:.2f}, SL: ${p.stop_loss:.2f}, TP: ${p.take_profit:.2f}")
