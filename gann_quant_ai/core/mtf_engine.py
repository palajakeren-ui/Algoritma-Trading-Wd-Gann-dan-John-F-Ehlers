"""
Multi-Timeframe (MTF) Engine v3.0 - Production Ready
Analyzes multiple timeframes for confluence and signal confirmation
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed


class Timeframe(Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN = "1M"


class TrendDirection(Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class TimeframeAnalysis:
    """Analysis result for a single timeframe"""
    timeframe: Timeframe
    trend: TrendDirection
    trend_strength: float  # 0-100
    momentum: float  # -100 to 100
    volatility: float
    support_levels: List[float]
    resistance_levels: List[float]
    key_level_proximity: str  # 'near_support', 'near_resistance', 'mid_range'
    signal: str  # 'BUY', 'SELL', 'NEUTRAL'
    signal_strength: float  # 0-100


@dataclass
class MTFConfluence:
    """Multi-timeframe confluence result"""
    symbol: str
    timestamp: datetime
    overall_trend: TrendDirection
    overall_signal: str
    confidence: float  # 0-100
    timeframe_alignment: float  # 0-100
    analyses: Dict[str, TimeframeAnalysis]
    higher_tf_bias: str
    lower_tf_trigger: str
    entry_zone: Tuple[float, float]
    invalidation_level: float
    notes: List[str]


class MTFEngine:
    """
    Production-ready multi-timeframe analysis engine supporting:
    - Trend analysis across timeframes
    - Confluence scoring
    - Higher timeframe bias detection
    - Lower timeframe entry triggers
    - Support/Resistance alignment
    """
    
    # Timeframe hierarchy (higher = more weight)
    TF_WEIGHTS = {
        Timeframe.M1: 0.05,
        Timeframe.M5: 0.10,
        Timeframe.M15: 0.15,
        Timeframe.M30: 0.20,
        Timeframe.H1: 0.30,
        Timeframe.H4: 0.50,
        Timeframe.D1: 0.80,
        Timeframe.W1: 1.00,
        Timeframe.MN: 1.00
    }
    
    # Timeframe periods in minutes
    TF_MINUTES = {
        Timeframe.M1: 1,
        Timeframe.M5: 5,
        Timeframe.M15: 15,
        Timeframe.M30: 30,
        Timeframe.H1: 60,
        Timeframe.H4: 240,
        Timeframe.D1: 1440,
        Timeframe.W1: 10080,
        Timeframe.MN: 43200
    }
    
    def __init__(self, config: Dict = None):
        """
        Initialize MTF engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Analysis settings
        self.default_timeframes = self.config.get('timeframes', [
            Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1
        ])
        self.lookback_bars = self.config.get('lookback_bars', 100)
        self.min_confluence = self.config.get('min_confluence', 0.6)  # 60%
        
        logger.info("MTF Engine initialized")
    
    # ==================== SINGLE TIMEFRAME ANALYSIS ====================
    
    def analyze_timeframe(
        self,
        data: pd.DataFrame,
        timeframe: Timeframe
    ) -> TimeframeAnalysis:
        """
        Analyze a single timeframe.
        
        Args:
            data: OHLCV DataFrame
            timeframe: Timeframe being analyzed
            
        Returns:
            TimeframeAnalysis object
        """
        if len(data) < 20:
            return self._empty_analysis(timeframe)
        
        close = data['close']
        high = data['high']
        low = data['low']
        current_price = close.iloc[-1]
        
        # Calculate indicators
        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()
        ema200 = close.ewm(span=200).mean() if len(close) >= 200 else close.ewm(span=len(close)).mean()
        
        # Trend analysis
        trend, trend_strength = self._analyze_trend(close, ema20, ema50, ema200)
        
        # Momentum (RSI-based)
        momentum = self._calculate_momentum(close)
        
        # Volatility (ATR-based)
        volatility = self._calculate_volatility(data)
        
        # Support and Resistance
        supports, resistances = self._find_sr_levels(data)
        
        # Key level proximity
        proximity = self._check_level_proximity(current_price, supports, resistances)
        
        # Generate signal
        signal, signal_strength = self._generate_tf_signal(
            trend, trend_strength, momentum, proximity
        )
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            trend_strength=trend_strength,
            momentum=momentum,
            volatility=volatility,
            support_levels=supports[:3],
            resistance_levels=resistances[:3],
            key_level_proximity=proximity,
            signal=signal,
            signal_strength=signal_strength
        )
    
    def _empty_analysis(self, timeframe: Timeframe) -> TimeframeAnalysis:
        """Return empty analysis for insufficient data"""
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=TrendDirection.NEUTRAL,
            trend_strength=0,
            momentum=0,
            volatility=0,
            support_levels=[],
            resistance_levels=[],
            key_level_proximity='mid_range',
            signal='NEUTRAL',
            signal_strength=0
        )
    
    def _analyze_trend(
        self,
        close: pd.Series,
        ema20: pd.Series,
        ema50: pd.Series,
        ema200: pd.Series
    ) -> Tuple[TrendDirection, float]:
        """Analyze trend direction and strength"""
        current = close.iloc[-1]
        
        # EMA alignment
        bullish_emas = ema20.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]
        bearish_emas = ema20.iloc[-1] < ema50.iloc[-1] < ema200.iloc[-1]
        
        # Price position
        above_20 = current > ema20.iloc[-1]
        above_50 = current > ema50.iloc[-1]
        above_200 = current > ema200.iloc[-1]
        
        # Slope analysis
        ema20_slope = (ema20.iloc[-1] - ema20.iloc[-10]) / ema20.iloc[-10] if len(ema20) >= 10 else 0
        
        # Determine trend
        bullish_score = sum([above_20, above_50, above_200, bullish_emas, ema20_slope > 0])
        bearish_score = sum([not above_20, not above_50, not above_200, bearish_emas, ema20_slope < 0])
        
        if bullish_score >= 4:
            trend = TrendDirection.STRONG_BULLISH
            strength = min(100, bullish_score * 20)
        elif bullish_score >= 3:
            trend = TrendDirection.BULLISH
            strength = bullish_score * 15
        elif bearish_score >= 4:
            trend = TrendDirection.STRONG_BEARISH
            strength = min(100, bearish_score * 20)
        elif bearish_score >= 3:
            trend = TrendDirection.BEARISH
            strength = bearish_score * 15
        else:
            trend = TrendDirection.NEUTRAL
            strength = 30
        
        return trend, strength
    
    def _calculate_momentum(self, close: pd.Series, period: int = 14) -> float:
        """Calculate momentum using RSI"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta).where(delta < 0, 0).rolling(period).mean()
        
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Convert RSI to momentum (-100 to 100)
        momentum = (rsi.iloc[-1] - 50) * 2
        
        return round(momentum, 2)
    
    def _calculate_volatility(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate volatility using ATR percentage"""
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        
        # ATR as percentage of price
        atr_pct = (atr / data['close'].iloc[-1]) * 100
        
        return round(atr_pct, 4)
    
    def _find_sr_levels(
        self,
        data: pd.DataFrame,
        num_levels: int = 5
    ) -> Tuple[List[float], List[float]]:
        """Find support and resistance levels"""
        current_price = data['close'].iloc[-1]
        supports = []
        resistances = []
        
        # Use swing highs/lows
        for i in range(2, min(50, len(data) - 2)):
            idx = len(data) - i - 1
            
            # Swing high (resistance)
            if (data['high'].iloc[idx] > data['high'].iloc[idx-1] and
                data['high'].iloc[idx] > data['high'].iloc[idx+1]):
                level = data['high'].iloc[idx]
                if level > current_price:
                    resistances.append(level)
                else:
                    supports.append(level)
            
            # Swing low (support)
            if (data['low'].iloc[idx] < data['low'].iloc[idx-1] and
                data['low'].iloc[idx] < data['low'].iloc[idx+1]):
                level = data['low'].iloc[idx]
                if level < current_price:
                    supports.append(level)
                else:
                    resistances.append(level)
        
        # Sort and deduplicate
        supports = sorted(set(supports), reverse=True)[:num_levels]
        resistances = sorted(set(resistances))[:num_levels]
        
        return supports, resistances
    
    def _check_level_proximity(
        self,
        price: float,
        supports: List[float],
        resistances: List[float],
        threshold_pct: float = 1.0
    ) -> str:
        """Check proximity to key levels"""
        if supports:
            nearest_support = supports[0]
            support_distance = (price - nearest_support) / price * 100
            if support_distance < threshold_pct:
                return 'near_support'
        
        if resistances:
            nearest_resistance = resistances[0]
            resistance_distance = (nearest_resistance - price) / price * 100
            if resistance_distance < threshold_pct:
                return 'near_resistance'
        
        return 'mid_range'
    
    def _generate_tf_signal(
        self,
        trend: TrendDirection,
        trend_strength: float,
        momentum: float,
        proximity: str
    ) -> Tuple[str, float]:
        """Generate signal for timeframe"""
        # Score components
        trend_score = 0
        if trend in [TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH]:
            trend_score = trend_strength
        elif trend in [TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH]:
            trend_score = -trend_strength
        
        momentum_score = momentum
        
        # Proximity bonus
        proximity_bonus = 0
        if proximity == 'near_support' and trend_score >= 0:
            proximity_bonus = 20
        elif proximity == 'near_resistance' and trend_score <= 0:
            proximity_bonus = -20
        
        # Combined score
        combined = trend_score + momentum_score / 2 + proximity_bonus
        
        if combined > 30:
            return 'BUY', min(100, combined)
        elif combined < -30:
            return 'SELL', min(100, abs(combined))
        else:
            return 'NEUTRAL', 50 - abs(combined) / 2
    
    # ==================== MULTI-TIMEFRAME ANALYSIS ====================
    
    def analyze_multiple(
        self,
        data_dict: Dict[Timeframe, pd.DataFrame],
        symbol: str = 'UNKNOWN'
    ) -> MTFConfluence:
        """
        Analyze multiple timeframes and find confluence.
        
        Args:
            data_dict: Dictionary of {Timeframe: DataFrame}
            symbol: Trading symbol
            
        Returns:
            MTFConfluence object
        """
        analyses = {}
        
        # Analyze each timeframe
        for tf, data in data_dict.items():
            if data is not None and len(data) >= 20:
                analyses[tf.value] = self.analyze_timeframe(data, tf)
        
        if not analyses:
            return self._empty_confluence(symbol)
        
        # Calculate confluence
        confluence = self._calculate_confluence(analyses)
        
        # Determine overall trend
        overall_trend = self._determine_overall_trend(analyses)
        
        # Determine overall signal
        overall_signal, confidence = self._determine_overall_signal(analyses)
        
        # Get higher TF bias
        higher_tf_bias = self._get_higher_tf_bias(analyses)
        
        # Get lower TF trigger
        lower_tf_trigger = self._get_lower_tf_trigger(analyses)
        
        # Calculate entry zone
        entry_zone, invalidation = self._calculate_entry_zone(analyses, data_dict)
        
        # Generate notes
        notes = self._generate_notes(analyses, confluence, overall_signal)
        
        return MTFConfluence(
            symbol=symbol,
            timestamp=datetime.now(),
            overall_trend=overall_trend,
            overall_signal=overall_signal,
            confidence=confidence,
            timeframe_alignment=confluence,
            analyses=analyses,
            higher_tf_bias=higher_tf_bias,
            lower_tf_trigger=lower_tf_trigger,
            entry_zone=entry_zone,
            invalidation_level=invalidation,
            notes=notes
        )
    
    def _empty_confluence(self, symbol: str) -> MTFConfluence:
        """Return empty confluence"""
        return MTFConfluence(
            symbol=symbol,
            timestamp=datetime.now(),
            overall_trend=TrendDirection.NEUTRAL,
            overall_signal='NEUTRAL',
            confidence=0,
            timeframe_alignment=0,
            analyses={},
            higher_tf_bias='NEUTRAL',
            lower_tf_trigger='NONE',
            entry_zone=(0, 0),
            invalidation_level=0,
            notes=['Insufficient data']
        )
    
    def _calculate_confluence(self, analyses: Dict[str, TimeframeAnalysis]) -> float:
        """Calculate timeframe alignment/confluence score"""
        if not analyses:
            return 0
        
        signals = [a.signal for a in analyses.values()]
        
        # Count signal agreement
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        total = len(signals)
        
        # Confluence is max agreement percentage
        max_agreement = max(buy_count, sell_count) / total * 100
        
        return round(max_agreement, 1)
    
    def _determine_overall_trend(
        self,
        analyses: Dict[str, TimeframeAnalysis]
    ) -> TrendDirection:
        """Determine overall trend from multiple timeframes"""
        if not analyses:
            return TrendDirection.NEUTRAL
        
        # Weight trends by timeframe importance
        bullish_weight = 0
        bearish_weight = 0
        total_weight = 0
        
        for tf_str, analysis in analyses.items():
            try:
                tf = Timeframe(tf_str)
                weight = self.TF_WEIGHTS.get(tf, 0.5)
            except:
                weight = 0.5
            
            total_weight += weight
            
            if analysis.trend in [TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH]:
                bullish_weight += weight * (1.5 if 'STRONG' in analysis.trend.value else 1.0)
            elif analysis.trend in [TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH]:
                bearish_weight += weight * (1.5 if 'STRONG' in analysis.trend.value else 1.0)
        
        ratio = bullish_weight / (bullish_weight + bearish_weight + 1e-10)
        
        if ratio > 0.7:
            return TrendDirection.STRONG_BULLISH
        elif ratio > 0.55:
            return TrendDirection.BULLISH
        elif ratio < 0.3:
            return TrendDirection.STRONG_BEARISH
        elif ratio < 0.45:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.NEUTRAL
    
    def _determine_overall_signal(
        self,
        analyses: Dict[str, TimeframeAnalysis]
    ) -> Tuple[str, float]:
        """Determine overall signal and confidence"""
        if not analyses:
            return 'NEUTRAL', 0
        
        buy_strength = 0
        sell_strength = 0
        total_weight = 0
        
        for tf_str, analysis in analyses.items():
            try:
                tf = Timeframe(tf_str)
                weight = self.TF_WEIGHTS.get(tf, 0.5)
            except:
                weight = 0.5
            
            total_weight += weight
            
            if analysis.signal == 'BUY':
                buy_strength += weight * analysis.signal_strength
            elif analysis.signal == 'SELL':
                sell_strength += weight * analysis.signal_strength
        
        if buy_strength > sell_strength * 1.2:
            signal = 'BUY'
            confidence = min(100, buy_strength / total_weight)
        elif sell_strength > buy_strength * 1.2:
            signal = 'SELL'
            confidence = min(100, sell_strength / total_weight)
        else:
            signal = 'NEUTRAL'
            confidence = 50
        
        return signal, round(confidence, 1)
    
    def _get_higher_tf_bias(self, analyses: Dict[str, TimeframeAnalysis]) -> str:
        """Get bias from higher timeframes"""
        higher_tfs = ['1d', '4h', '1h']
        
        for tf in higher_tfs:
            if tf in analyses:
                analysis = analyses[tf]
                if analysis.trend in [TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH]:
                    return 'BULLISH'
                elif analysis.trend in [TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH]:
                    return 'BEARISH'
        
        return 'NEUTRAL'
    
    def _get_lower_tf_trigger(self, analyses: Dict[str, TimeframeAnalysis]) -> str:
        """Get entry trigger from lower timeframes"""
        lower_tfs = ['5m', '15m', '30m']
        
        for tf in lower_tfs:
            if tf in analyses:
                analysis = analyses[tf]
                if analysis.signal in ['BUY', 'SELL']:
                    return analysis.signal
        
        return 'NONE'
    
    def _calculate_entry_zone(
        self,
        analyses: Dict[str, TimeframeAnalysis],
        data_dict: Dict[Timeframe, pd.DataFrame]
    ) -> Tuple[Tuple[float, float], float]:
        """Calculate entry zone and invalidation level"""
        # Get current price from available data
        current_price = 0
        for tf, data in data_dict.items():
            if data is not None and len(data) > 0:
                current_price = data['close'].iloc[-1]
                break
        
        if current_price == 0:
            return (0, 0), 0
        
        # Find nearest support/resistance for entry zone
        all_supports = []
        all_resistances = []
        
        for analysis in analyses.values():
            all_supports.extend(analysis.support_levels)
            all_resistances.extend(analysis.resistance_levels)
        
        # Determine signal direction
        overall_signal = self._determine_overall_signal(analyses)[0]
        
        if overall_signal == 'BUY':
            # Entry zone near support
            if all_supports:
                nearest_support = max([s for s in all_supports if s < current_price], default=current_price * 0.98)
                entry_zone = (nearest_support, current_price)
                invalidation = nearest_support * 0.98
            else:
                entry_zone = (current_price * 0.98, current_price)
                invalidation = current_price * 0.95
        elif overall_signal == 'SELL':
            # Entry zone near resistance
            if all_resistances:
                nearest_resistance = min([r for r in all_resistances if r > current_price], default=current_price * 1.02)
                entry_zone = (current_price, nearest_resistance)
                invalidation = nearest_resistance * 1.02
            else:
                entry_zone = (current_price, current_price * 1.02)
                invalidation = current_price * 1.05
        else:
            entry_zone = (current_price * 0.99, current_price * 1.01)
            invalidation = current_price * 0.95
        
        return entry_zone, invalidation
    
    def _generate_notes(
        self,
        analyses: Dict[str, TimeframeAnalysis],
        confluence: float,
        overall_signal: str
    ) -> List[str]:
        """Generate analysis notes"""
        notes = []
        
        # Confluence note
        if confluence >= 80:
            notes.append(f"Strong confluence ({confluence:.0f}%) across timeframes")
        elif confluence >= 60:
            notes.append(f"Good confluence ({confluence:.0f}%) across timeframes")
        else:
            notes.append(f"Weak confluence ({confluence:.0f}%) - wait for alignment")
        
        # Signal consistency
        signals = [a.signal for a in analyses.values()]
        if all(s == overall_signal for s in signals if s != 'NEUTRAL'):
            notes.append("All timeframes aligned")
        
        # Higher TF trend
        for tf in ['1d', '4h']:
            if tf in analyses:
                trend = analyses[tf].trend.value
                notes.append(f"{tf.upper()} trend: {trend.replace('_', ' ').title()}")
        
        # Proximity warnings
        for tf_str, analysis in analyses.items():
            if analysis.key_level_proximity != 'mid_range':
                notes.append(f"{tf_str.upper()}: {analysis.key_level_proximity.replace('_', ' ')}")
        
        return notes


# Example usage
if __name__ == "__main__":
    # Create sample data for multiple timeframes
    np.random.seed(42)
    
    def create_sample_data(periods: int, freq: str) -> pd.DataFrame:
        dates = pd.date_range(start='2024-01-01', periods=periods, freq=freq)
        t = np.arange(periods)
        trend = 50000 + t * 10
        noise = np.cumsum(np.random.randn(periods) * 100)
        price = trend + noise
        
        return pd.DataFrame({
            'open': price - np.abs(np.random.randn(periods) * 200),
            'high': price + np.abs(np.random.randn(periods) * 300),
            'low': price - np.abs(np.random.randn(periods) * 300),
            'close': price,
            'volume': np.random.uniform(1e9, 5e9, periods)
        }, index=dates)
    
    data_dict = {
        Timeframe.M15: create_sample_data(500, '15min'),
        Timeframe.H1: create_sample_data(200, '1H'),
        Timeframe.H4: create_sample_data(100, '4H'),
        Timeframe.D1: create_sample_data(100, '1D')
    }
    
    # Run MTF analysis
    engine = MTFEngine()
    result = engine.analyze_multiple(data_dict, 'BTCUSD')
    
    print("\n=== Multi-Timeframe Analysis ===")
    print(f"Symbol: {result.symbol}")
    print(f"Overall Trend: {result.overall_trend.value}")
    print(f"Overall Signal: {result.overall_signal}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"Timeframe Alignment: {result.timeframe_alignment:.1f}%")
    print(f"Higher TF Bias: {result.higher_tf_bias}")
    print(f"Lower TF Trigger: {result.lower_tf_trigger}")
    print(f"Entry Zone: ${result.entry_zone[0]:,.2f} - ${result.entry_zone[1]:,.2f}")
    print(f"Invalidation: ${result.invalidation_level:,.2f}")
    
    print("\n--- Timeframe Details ---")
    for tf_str, analysis in result.analyses.items():
        print(f"{tf_str}: {analysis.trend.value} | Signal: {analysis.signal} ({analysis.signal_strength:.0f}%)")
    
    print("\n--- Notes ---")
    for note in result.notes:
        print(f"• {note}")
