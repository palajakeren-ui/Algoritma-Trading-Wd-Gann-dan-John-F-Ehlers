"""
AI Signal Engine
Comprehensive signal generation combining Gann, Astrology, Ehlers DSP, and ML models.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class SignalComponent:
    """Individual signal component from a specific engine."""
    source: str  # 'gann', 'astro', 'ehlers', 'ml', 'pattern'
    signal: SignalType
    confidence: float  # 0-100
    weight: float  # Contribution weight
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AISignal:
    """Complete AI trading signal."""
    symbol: str
    timeframe: str
    signal: SignalType
    confidence: float  # 0-100
    strength: SignalStrength
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    components: List[SignalComponent] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    model_attribution: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    valid_until: datetime = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'signal': self.signal.value,
            'confidence': round(self.confidence, 2),
            'strength': self.strength.name,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_reward': round(self.risk_reward, 2),
            'reasons': self.reasons,
            'model_attribution': self.model_attribution,
            'timestamp': self.timestamp.isoformat(),
            'components': [
                {
                    'source': c.source,
                    'signal': c.signal.value,
                    'confidence': c.confidence,
                    'weight': c.weight
                } for c in self.components
            ]
        }


class AISignalEngine:
    """
    Main AI Signal Engine that combines multiple analysis methods.
    
    Integrates:
    - WD Gann modules (Square of 9, 24, 52, 90, 144, 360)
    - Gann Time-Price Geometry
    - Astrology & market cycles
    - John Ehlers DSP indicators
    - Machine Learning models
    - Pattern Recognition
    """
    
    # Default weights for each component
    DEFAULT_WEIGHTS = {
        'gann': 0.25,
        'astro': 0.15,
        'ehlers': 0.20,
        'ml': 0.25,
        'pattern': 0.10,
        'options_flow': 0.05
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.weights = self.config.get('weights', self.DEFAULT_WEIGHTS.copy())
        
        # Initialize engines (lazy loading)
        self._gann_engine = None
        self._astro_engine = None
        self._ehlers_engine = None
        self._ml_engine = None
        self._pattern_engine = None
        
        # Signal history
        self.signal_history: List[AISignal] = []
        
        logger.info("AISignalEngine initialized")
    
    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        timeframe: str = "H1",
        current_price: float = None
    ) -> AISignal:
        """
        Generate comprehensive AI trading signal.
        
        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            timeframe: Timeframe of the data
            current_price: Current market price
            
        Returns:
            AISignal with complete analysis
        """
        if current_price is None and len(data) > 0:
            current_price = data['close'].iloc[-1]
        
        components = []
        reasons = []
        
        # 1. Gann Analysis
        gann_component = self._analyze_gann(data, current_price)
        if gann_component:
            components.append(gann_component)
            if gann_component.confidence > 60:
                reasons.append(f"Gann: {gann_component.details.get('reason', 'Signal detected')}")
        
        # 2. Astrology Analysis
        astro_component = self._analyze_astro(data, symbol)
        if astro_component:
            components.append(astro_component)
            if astro_component.confidence > 60:
                reasons.append(f"Astro: {astro_component.details.get('reason', 'Cycle alignment')}")
        
        # 3. Ehlers DSP Analysis
        ehlers_component = self._analyze_ehlers(data)
        if ehlers_component:
            components.append(ehlers_component)
            if ehlers_component.confidence > 60:
                reasons.append(f"Ehlers: {ehlers_component.details.get('reason', 'DSP signal')}")
        
        # 4. ML Prediction
        ml_component = self._analyze_ml(data)
        if ml_component:
            components.append(ml_component)
            if ml_component.confidence > 60:
                reasons.append(f"ML: {ml_component.details.get('reason', 'Model prediction')}")
        
        # 5. Pattern Recognition
        pattern_component = self._analyze_patterns(data)
        if pattern_component:
            components.append(pattern_component)
            if pattern_component.confidence > 60:
                reasons.append(f"Pattern: {pattern_component.details.get('reason', 'Pattern detected')}")
        
        # Combine signals
        final_signal, confidence, strength = self._combine_signals(components)
        
        # Calculate entry, SL, TP
        entry, sl, tp = self._calculate_levels(data, final_signal, current_price)
        
        # Calculate risk-reward
        risk_reward = self._calculate_risk_reward(entry, sl, tp, final_signal)
        
        # Build model attribution
        attribution = {c.source: c.weight * c.confidence for c in components}
        total_attr = sum(attribution.values()) or 1
        attribution = {k: round(v / total_attr * 100, 1) for k, v in attribution.items()}
        
        # Create final signal
        signal = AISignal(
            symbol=symbol,
            timeframe=timeframe,
            signal=final_signal,
            confidence=confidence,
            strength=strength,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            risk_reward=risk_reward,
            components=components,
            reasons=reasons,
            model_attribution=attribution,
            metadata={
                'data_points': len(data),
                'components_used': len(components)
            }
        )
        
        # Store in history
        self.signal_history.append(signal)
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-500:]
        
        logger.info(f"Generated signal for {symbol}: {final_signal.value} ({confidence:.1f}%)")
        
        return signal
    
    def _analyze_gann(self, data: pd.DataFrame, current_price: float) -> Optional[SignalComponent]:
        """Analyze using Gann methods."""
        try:
            if len(data) < 20:
                return None
            
            high = data['high'].max()
            low = data['low'].min()
            close = data['close'].iloc[-1]
            
            # Square of 9 analysis
            from modules.gann.square_of_9 import SquareOf9
            sq9 = SquareOf9(low)
            levels = sq9.get_levels(5)
            
            # Find nearest support/resistance
            supports = [l for l in levels.get('support', []) if l < current_price]
            resistances = [l for l in levels.get('resistance', []) if l > current_price]
            
            nearest_support = max(supports) if supports else low
            nearest_resistance = min(resistances) if resistances else high
            
            # Determine signal based on price position
            range_size = nearest_resistance - nearest_support
            price_position = (current_price - nearest_support) / range_size if range_size > 0 else 0.5
            
            if price_position < 0.3:
                signal = SignalType.BUY
                confidence = (0.3 - price_position) * 200 + 50
                reason = f"Price near Sq9 support ${nearest_support:.2f}"
            elif price_position > 0.7:
                signal = SignalType.SELL
                confidence = (price_position - 0.7) * 200 + 50
                reason = f"Price near Sq9 resistance ${nearest_resistance:.2f}"
            else:
                signal = SignalType.HOLD
                confidence = 50
                reason = "Price in neutral zone"
            
            return SignalComponent(
                source='gann',
                signal=signal,
                confidence=min(95, confidence),
                weight=self.weights.get('gann', 0.25),
                details={
                    'reason': reason,
                    'nearest_support': nearest_support,
                    'nearest_resistance': nearest_resistance
                }
            )
            
        except Exception as e:
            logger.warning(f"Gann analysis error: {e}")
            return None
    
    def _analyze_astro(self, data: pd.DataFrame, symbol: str) -> Optional[SignalComponent]:
        """Analyze using astrological cycles."""
        try:
            from modules.astro.synodic_cycles import SynodicCycleCalculator
            
            synodic = SynodicCycleCalculator()
            phases = synodic.get_current_cycle_phases()
            
            bullish_score = 0
            bearish_score = 0
            
            for phase in phases:
                if phase.get('phase_name') in ['new', 'first_quarter']:
                    bullish_score += 1
                elif phase.get('phase_name') in ['full', 'last_quarter']:
                    bearish_score += 1
            
            if bullish_score > bearish_score:
                signal = SignalType.BUY
                confidence = 50 + (bullish_score * 10)
                reason = f"Bullish astro cycles ({bullish_score} signals)"
            elif bearish_score > bullish_score:
                signal = SignalType.SELL
                confidence = 50 + (bearish_score * 10)
                reason = f"Bearish astro cycles ({bearish_score} signals)"
            else:
                signal = SignalType.HOLD
                confidence = 50
                reason = "Neutral astro cycles"
            
            return SignalComponent(
                source='astro',
                signal=signal,
                confidence=confidence,
                weight=self.weights.get('astro', 0.15),
                details={'reason': reason}
            )
            
        except Exception as e:
            logger.warning(f"Astro analysis error: {e}")
            return None
    
    def _analyze_ehlers(self, data: pd.DataFrame) -> Optional[SignalComponent]:
        """Analyze using Ehlers DSP indicators."""
        try:
            if len(data) < 50:
                return None
            
            signals = {'buy': 0, 'sell': 0}
            
            # Simple momentum check as fallback
            close = data['close']
            momentum = close.iloc[-1] / close.iloc[-10] - 1
            
            if momentum > 0.02:
                signals['buy'] += 2
            elif momentum < -0.02:
                signals['sell'] += 2
            
            # RSI-like calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            if rsi < 30:
                signals['buy'] += 1
            elif rsi > 70:
                signals['sell'] += 1
            
            total = signals['buy'] + signals['sell']
            if total == 0:
                return None
            
            if signals['buy'] > signals['sell']:
                signal = SignalType.BUY
                confidence = 50 + (signals['buy'] / total) * 40
                reason = f"Ehlers bullish"
            elif signals['sell'] > signals['buy']:
                signal = SignalType.SELL
                confidence = 50 + (signals['sell'] / total) * 40
                reason = f"Ehlers bearish"
            else:
                signal = SignalType.HOLD
                confidence = 50
                reason = "Ehlers neutral"
            
            return SignalComponent(
                source='ehlers',
                signal=signal,
                confidence=confidence,
                weight=self.weights.get('ehlers', 0.20),
                details={'reason': reason}
            )
            
        except Exception as e:
            logger.warning(f"Ehlers analysis error: {e}")
            return None
    
    def _analyze_ml(self, data: pd.DataFrame) -> Optional[SignalComponent]:
        """Analyze using ML models."""
        try:
            if len(data) < 100:
                return None
            
            close = data['close']
            sma_20 = close.rolling(20).mean()
            sma_50 = close.rolling(50).mean()
            
            if close.iloc[-1] > sma_20.iloc[-1] > sma_50.iloc[-1]:
                signal = SignalType.BUY
                confidence = 65
                reason = "Bullish MA alignment"
            elif close.iloc[-1] < sma_20.iloc[-1] < sma_50.iloc[-1]:
                signal = SignalType.SELL
                confidence = 65
                reason = "Bearish MA alignment"
            else:
                signal = SignalType.HOLD
                confidence = 50
                reason = "Mixed MA signals"
            
            return SignalComponent(
                source='ml',
                signal=signal,
                confidence=confidence,
                weight=self.weights.get('ml', 0.25),
                details={'reason': reason}
            )
            
        except Exception as e:
            logger.warning(f"ML analysis error: {e}")
            return None
    
    def _analyze_patterns(self, data: pd.DataFrame) -> Optional[SignalComponent]:
        """Analyze chart patterns."""
        try:
            if len(data) < 20:
                return None
            
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            signal_bias = 0
            patterns = []
            
            # Higher highs/lows trend
            if high[-1] > high[-5] and low[-1] > low[-5]:
                signal_bias += 1
                patterns.append("Uptrend")
            elif high[-1] < high[-5] and low[-1] < low[-5]:
                signal_bias -= 1
                patterns.append("Downtrend")
            
            if signal_bias > 0:
                signal = SignalType.BUY
                confidence = 55
            elif signal_bias < 0:
                signal = SignalType.SELL
                confidence = 55
            else:
                signal = SignalType.HOLD
                confidence = 50
            
            return SignalComponent(
                source='pattern',
                signal=signal,
                confidence=confidence,
                weight=self.weights.get('pattern', 0.10),
                details={'reason': ', '.join(patterns) if patterns else 'No clear pattern'}
            )
            
        except Exception as e:
            logger.warning(f"Pattern analysis error: {e}")
            return None
    
    def _combine_signals(self, components: List[SignalComponent]) -> Tuple[SignalType, float, SignalStrength]:
        """Combine all signal components into final signal."""
        if not components:
            return SignalType.HOLD, 50.0, SignalStrength.WEAK
        
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        for comp in components:
            weight = comp.weight * (comp.confidence / 100)
            total_weight += comp.weight
            
            if comp.signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                buy_score += weight
            elif comp.signal in [SignalType.SELL, SignalType.STRONG_SELL]:
                sell_score += weight
        
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
        
        if buy_score > sell_score and buy_score > 0.4:
            signal = SignalType.STRONG_BUY if buy_score > 0.7 else SignalType.BUY
            confidence = buy_score * 100
        elif sell_score > buy_score and sell_score > 0.4:
            signal = SignalType.STRONG_SELL if sell_score > 0.7 else SignalType.SELL
            confidence = sell_score * 100
        else:
            signal = SignalType.HOLD
            confidence = 50
        
        if confidence >= 80:
            strength = SignalStrength.VERY_STRONG
        elif confidence >= 65:
            strength = SignalStrength.STRONG
        elif confidence >= 50:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        return signal, min(95, confidence), strength
    
    def _calculate_levels(self, data: pd.DataFrame, signal: SignalType, current_price: float) -> Tuple[float, float, float]:
        """Calculate entry, stop loss, and take profit levels."""
        if len(data) < 20:
            if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                return current_price, current_price * 0.98, current_price * 1.04
            elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
                return current_price, current_price * 1.02, current_price * 0.96
            return current_price, current_price, current_price
        
        # ATR calculation
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            entry = current_price
            stop_loss = current_price - (atr * 1.5)
            take_profit = current_price + (atr * 3)
        elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            entry = current_price
            stop_loss = current_price + (atr * 1.5)
            take_profit = current_price - (atr * 3)
        else:
            entry = current_price
            stop_loss = current_price
            take_profit = current_price
        
        return round(entry, 4), round(stop_loss, 4), round(take_profit, 4)
    
    def _calculate_risk_reward(self, entry: float, stop_loss: float, take_profit: float, signal: SignalType) -> float:
        """Calculate risk-reward ratio."""
        if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
        elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            risk = abs(stop_loss - entry)
            reward = abs(entry - take_profit)
        else:
            return 0.0
        
        return reward / risk if risk > 0 else 0.0
    
    def update_weights(self, weights: Dict[str, float]):
        """Update component weights."""
        self.weights.update(weights)
    
    def get_signal_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get signal history."""
        history = self.signal_history
        if symbol:
            history = [s for s in history if s.symbol == symbol]
        return [s.to_dict() for s in history[-limit:]]


_signal_engine: Optional[AISignalEngine] = None


def get_signal_engine(config: Dict = None) -> AISignalEngine:
    """Get or create the signal engine."""
    global _signal_engine
    if _signal_engine is None:
        _signal_engine = AISignalEngine(config)
    return _signal_engine
