"""
Hybrid Scanner v3.0 - Production Ready
Combines multiple analysis methods for comprehensive market scanning
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable
from loguru import logger
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class ScannerType(Enum):
    GANN = "gann"
    CANDLESTICK = "candlestick"
    EHLERS = "ehlers"
    ASTRO = "astro"
    VOLUME = "volume"
    MOMENTUM = "momentum"
    PATTERN = "pattern"


class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class ScanResult:
    """Individual scanner result"""
    scanner_type: ScannerType
    symbol: str
    signal: str  # 'BUY', 'SELL', 'NEUTRAL'
    strength: SignalStrength
    score: float  # 0-100
    price: float
    timestamp: datetime
    details: Dict = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)


@dataclass
class HybridSignal:
    """Combined signal from multiple scanners"""
    symbol: str
    direction: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    confidence: float  # 0-100
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    contributing_signals: List[ScanResult]
    confluence_count: int
    timestamp: datetime
    description: str


class HybridScanner:
    """
    Production-ready hybrid market scanner combining:
    - Gann Analysis (Square of 9, Time Cycles)
    - Candlestick Patterns
    - Ehlers DSP Indicators
    - Astro Cycles (optional)
    - Volume Analysis
    - Momentum Indicators
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize hybrid scanner.
        
        Args:
            config: Scanner configuration
        """
        self.config = config or {}
        
        # Scanner weights for combining signals
        self.weights = self.config.get('weights', {
            ScannerType.GANN: 0.20,
            ScannerType.CANDLESTICK: 0.20,
            ScannerType.EHLERS: 0.15,
            ScannerType.ASTRO: 0.10,
            ScannerType.VOLUME: 0.15,
            ScannerType.MOMENTUM: 0.20
        })
        
        # Minimum confluence for signal
        self.min_confluence = self.config.get('min_confluence', 3)
        self.min_confidence = self.config.get('min_confidence', 60.0)
        
        # Initialize sub-scanners
        self._init_scanners()
        
        logger.info("Hybrid Scanner initialized")
    
    def _init_scanners(self):
        """Initialize individual scanners"""
        # Lazy imports to avoid circular dependencies
        self._scanners = {}
        
        try:
            from scanner.gann_scanner import GannScanner
            self._scanners[ScannerType.GANN] = GannScanner()
        except ImportError:
            logger.warning("Gann Scanner not available")
        
        try:
            from scanner.Candlestick_Pattern_Scanner import CandlestickPatternScanner
            self._scanners[ScannerType.CANDLESTICK] = CandlestickPatternScanner()
        except ImportError:
            logger.warning("Candlestick Scanner not available")
        
        try:
            from scanner.ehlers_scanner import EhlersScanner
            self._scanners[ScannerType.EHLERS] = EhlersScanner()
        except ImportError:
            logger.warning("Ehlers Scanner not available")
    
    # ==================== INDIVIDUAL SCANNERS ====================
    
    def _scan_gann(self, data: pd.DataFrame, symbol: str) -> Optional[ScanResult]:
        """Run Gann analysis"""
        try:
            current_price = data['close'].iloc[-1]
            sqrt_price = np.sqrt(current_price)
            
            # Calculate Gann levels
            sq9_up = (sqrt_price + 0.25) ** 2
            sq9_down = (sqrt_price - 0.25) ** 2
            
            # Determine signal based on price position
            distance_to_up = (sq9_up - current_price) / current_price
            distance_to_down = (current_price - sq9_down) / current_price
            
            if distance_to_up < 0.01:  # Near resistance
                signal = 'SELL'
                strength = SignalStrength.MODERATE
                score = 60
            elif distance_to_down < 0.01:  # Near support
                signal = 'BUY'
                strength = SignalStrength.MODERATE
                score = 60
            else:
                signal = 'NEUTRAL'
                strength = SignalStrength.WEAK
                score = 40
            
            return ScanResult(
                scanner_type=ScannerType.GANN,
                symbol=symbol,
                signal=signal,
                strength=strength,
                score=score,
                price=current_price,
                timestamp=datetime.now(),
                details={
                    'sq9_resistance': sq9_up,
                    'sq9_support': sq9_down,
                    'distance_to_resistance': distance_to_up,
                    'distance_to_support': distance_to_down
                }
            )
        except Exception as e:
            logger.error(f"Gann scan error: {e}")
            return None
    
    def _scan_candlestick(self, data: pd.DataFrame, symbol: str) -> Optional[ScanResult]:
        """Run candlestick pattern analysis"""
        try:
            if ScannerType.CANDLESTICK in self._scanners:
                scanner = self._scanners[ScannerType.CANDLESTICK]
                patterns = scanner.scan(data, min_reliability="medium")
                
                if patterns:
                    best = patterns[0]
                    signal = 'BUY' if 'bullish' in best.type.value else 'SELL' if 'bearish' in best.type.value else 'NEUTRAL'
                    
                    strength_map = {
                        'low': SignalStrength.WEAK,
                        'medium': SignalStrength.MODERATE,
                        'high': SignalStrength.STRONG,
                        'very_high': SignalStrength.VERY_STRONG
                    }
                    
                    return ScanResult(
                        scanner_type=ScannerType.CANDLESTICK,
                        symbol=symbol,
                        signal=signal,
                        strength=strength_map.get(best.reliability.value, SignalStrength.MODERATE),
                        score=best.signal_strength * 100,
                        price=data['close'].iloc[-1],
                        timestamp=datetime.now(),
                        patterns=[p.name for p in patterns[:5]],
                        details={'pattern': best.name, 'reliability': best.reliability.value}
                    )
            
            # Fallback basic pattern detection
            c1 = data.iloc[-2]
            c2 = data.iloc[-1]
            
            # Simple engulfing check
            if c2['close'] > c2['open'] and c1['close'] < c1['open']:
                if c2['close'] > c1['open'] and c2['open'] < c1['close']:
                    return ScanResult(
                        scanner_type=ScannerType.CANDLESTICK,
                        symbol=symbol,
                        signal='BUY',
                        strength=SignalStrength.STRONG,
                        score=75,
                        price=c2['close'],
                        timestamp=datetime.now(),
                        patterns=['Bullish Engulfing']
                    )
            
            return ScanResult(
                scanner_type=ScannerType.CANDLESTICK,
                symbol=symbol,
                signal='NEUTRAL',
                strength=SignalStrength.WEAK,
                score=40,
                price=data['close'].iloc[-1],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Candlestick scan error: {e}")
            return None
    
    def _scan_ehlers(self, data: pd.DataFrame, symbol: str) -> Optional[ScanResult]:
        """Run Ehlers DSP analysis"""
        try:
            from core.ehlers_indicators import EhlersIndicators
            
            close = data['close']
            
            # Calculate indicators
            mama, fama = EhlersIndicators.mama(close)
            fisher, fisher_signal = EhlersIndicators.fisher_transform(close)
            
            # Generate signal
            mama_cross = mama.iloc[-1] > fama.iloc[-1] and mama.iloc[-2] <= fama.iloc[-2]
            mama_cross_down = mama.iloc[-1] < fama.iloc[-1] and mama.iloc[-2] >= fama.iloc[-2]
            
            fisher_bullish = fisher.iloc[-1] > fisher_signal.iloc[-1]
            fisher_extreme = abs(fisher.iloc[-1]) > 1.5
            
            if mama_cross or (fisher_bullish and fisher_extreme):
                signal = 'BUY'
                strength = SignalStrength.STRONG if mama_cross and fisher_bullish else SignalStrength.MODERATE
                score = 80 if mama_cross and fisher_bullish else 65
            elif mama_cross_down or (not fisher_bullish and fisher_extreme):
                signal = 'SELL'
                strength = SignalStrength.STRONG if mama_cross_down and not fisher_bullish else SignalStrength.MODERATE
                score = 80 if mama_cross_down and not fisher_bullish else 65
            else:
                signal = 'NEUTRAL'
                strength = SignalStrength.WEAK
                score = 45
            
            return ScanResult(
                scanner_type=ScannerType.EHLERS,
                symbol=symbol,
                signal=signal,
                strength=strength,
                score=score,
                price=close.iloc[-1],
                timestamp=datetime.now(),
                details={
                    'mama': mama.iloc[-1],
                    'fama': fama.iloc[-1],
                    'fisher': fisher.iloc[-1],
                    'fisher_signal': fisher_signal.iloc[-1]
                }
            )
            
        except Exception as e:
            logger.error(f"Ehlers scan error: {e}")
            return None
    
    def _scan_volume(self, data: pd.DataFrame, symbol: str) -> Optional[ScanResult]:
        """Run volume analysis"""
        try:
            # Volume indicators
            avg_volume = data['volume'].rolling(20).mean()
            volume_ratio = data['volume'].iloc[-1] / avg_volume.iloc[-1]
            
            # Price-volume analysis
            price_change = (data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2]
            
            # Volume-price divergence
            if volume_ratio > 2.0:  # High volume
                if price_change > 0:
                    signal = 'BUY'
                    strength = SignalStrength.STRONG
                    score = 75
                else:
                    signal = 'SELL'
                    strength = SignalStrength.STRONG
                    score = 75
            elif volume_ratio > 1.5:
                if price_change > 0:
                    signal = 'BUY'
                    strength = SignalStrength.MODERATE
                    score = 60
                else:
                    signal = 'SELL'
                    strength = SignalStrength.MODERATE
                    score = 60
            else:
                signal = 'NEUTRAL'
                strength = SignalStrength.WEAK
                score = 40
            
            return ScanResult(
                scanner_type=ScannerType.VOLUME,
                symbol=symbol,
                signal=signal,
                strength=strength,
                score=score,
                price=data['close'].iloc[-1],
                timestamp=datetime.now(),
                details={
                    'volume_ratio': volume_ratio,
                    'avg_volume': avg_volume.iloc[-1],
                    'current_volume': data['volume'].iloc[-1]
                }
            )
            
        except Exception as e:
            logger.error(f"Volume scan error: {e}")
            return None
    
    def _scan_momentum(self, data: pd.DataFrame, symbol: str) -> Optional[ScanResult]:
        """Run momentum analysis (RSI, MACD, etc.)"""
        try:
            close = data['close']
            
            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).ewm(span=14, adjust=False).mean()
            loss = (-delta).where(delta < 0, 0).ewm(span=14, adjust=False).mean()
            rs = gain / (loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            
            # MACD
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal_line = macd.ewm(span=9, adjust=False).mean()
            macd_histogram = macd - signal_line
            
            # Generate signal
            rsi_bullish = rsi.iloc[-1] < 30
            rsi_bearish = rsi.iloc[-1] > 70
            macd_bullish = macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]
            macd_bearish = macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]
            
            if (rsi_bullish and macd_bullish) or rsi.iloc[-1] < 25:
                signal = 'BUY'
                strength = SignalStrength.STRONG
                score = 80
            elif (rsi_bearish and macd_bearish) or rsi.iloc[-1] > 75:
                signal = 'SELL'
                strength = SignalStrength.STRONG
                score = 80
            elif macd_bullish:
                signal = 'BUY'
                strength = SignalStrength.MODERATE
                score = 65
            elif macd_bearish:
                signal = 'SELL'
                strength = SignalStrength.MODERATE
                score = 65
            else:
                signal = 'NEUTRAL'
                strength = SignalStrength.WEAK
                score = 45
            
            return ScanResult(
                scanner_type=ScannerType.MOMENTUM,
                symbol=symbol,
                signal=signal,
                strength=strength,
                score=score,
                price=close.iloc[-1],
                timestamp=datetime.now(),
                details={
                    'rsi': rsi.iloc[-1],
                    'macd': macd.iloc[-1],
                    'macd_signal': signal_line.iloc[-1],
                    'macd_histogram': macd_histogram.iloc[-1]
                }
            )
            
        except Exception as e:
            logger.error(f"Momentum scan error: {e}")
            return None
    
    # ==================== MAIN SCAN ====================
    
    def scan(
        self,
        data: pd.DataFrame,
        symbol: str,
        scanners: List[ScannerType] = None
    ) -> Optional[HybridSignal]:
        """
        Run hybrid scan on data.
        
        Args:
            data: OHLCV DataFrame
            symbol: Symbol being scanned
            scanners: List of scanners to use (default: all)
            
        Returns:
            HybridSignal if signal found, None otherwise
        """
        if len(data) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        if scanners is None:
            scanners = [
                ScannerType.GANN,
                ScannerType.CANDLESTICK,
                ScannerType.EHLERS,
                ScannerType.VOLUME,
                ScannerType.MOMENTUM
            ]
        
        # Run individual scanners
        results: List[ScanResult] = []
        
        scanner_methods = {
            ScannerType.GANN: self._scan_gann,
            ScannerType.CANDLESTICK: self._scan_candlestick,
            ScannerType.EHLERS: self._scan_ehlers,
            ScannerType.VOLUME: self._scan_volume,
            ScannerType.MOMENTUM: self._scan_momentum
        }
        
        for scanner_type in scanners:
            if scanner_type in scanner_methods:
                result = scanner_methods[scanner_type](data, symbol)
                if result:
                    results.append(result)
        
        if not results:
            return None
        
        # Combine signals
        return self._combine_signals(results, symbol, data)
    
    def _combine_signals(
        self,
        results: List[ScanResult],
        symbol: str,
        data: pd.DataFrame
    ) -> Optional[HybridSignal]:
        """Combine individual scan results into hybrid signal"""
        
        # Count directional signals
        buy_signals = [r for r in results if r.signal == 'BUY']
        sell_signals = [r for r in results if r.signal == 'SELL']
        
        # Calculate weighted scores
        buy_score = sum(
            r.score * self.weights.get(r.scanner_type, 0.1) * r.strength.value
            for r in buy_signals
        )
        sell_score = sum(
            r.score * self.weights.get(r.scanner_type, 0.1) * r.strength.value
            for r in sell_signals
        )
        
        # Determine direction
        confluence_count = max(len(buy_signals), len(sell_signals))
        
        if confluence_count < self.min_confluence:
            return None
        
        if buy_score > sell_score * 1.2:  # 20% margin for confirmation
            direction = 'BULLISH'
            confidence = min(100, buy_score / 4)  # Normalize
            contributing = buy_signals
        elif sell_score > buy_score * 1.2:
            direction = 'BEARISH'
            confidence = min(100, sell_score / 4)
            contributing = sell_signals
        else:
            return None
        
        if confidence < self.min_confidence:
            return None
        
        # Calculate entry, SL, TP
        current_price = data['close'].iloc[-1]
        atr = self._calculate_atr(data)
        
        if direction == 'BULLISH':
            entry = current_price
            stop_loss = current_price - (atr * 1.5)
            take_profit = current_price + (atr * 3.0)
        else:
            entry = current_price
            stop_loss = current_price + (atr * 1.5)
            take_profit = current_price - (atr * 3.0)
        
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        risk_reward = reward / risk if risk > 0 else 0
        
        return HybridSignal(
            symbol=symbol,
            direction=direction,
            confidence=round(confidence, 2),
            entry_price=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            risk_reward=round(risk_reward, 2),
            contributing_signals=contributing,
            confluence_count=confluence_count,
            timestamp=datetime.now(),
            description=f"{direction} signal with {confluence_count} confirming indicators"
        )
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR"""
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        return atr if not pd.isna(atr) else high_low.mean()
    
    def scan_multiple(
        self,
        data_dict: Dict[str, pd.DataFrame],
        scanners: List[ScannerType] = None,
        max_workers: int = 4
    ) -> List[HybridSignal]:
        """
        Scan multiple symbols in parallel.
        
        Args:
            data_dict: Dictionary of {symbol: DataFrame}
            scanners: Scanners to use
            max_workers: Max parallel workers
            
        Returns:
            List of signals found
        """
        signals = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scan, data, symbol, scanners): symbol
                for symbol, data in data_dict.items()
            }
            
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        signals.append(result)
                except Exception as e:
                    logger.error(f"Scan failed for {symbol}: {e}")
        
        # Sort by confidence
        return sorted(signals, key=lambda x: -x.confidence)


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    np.random.seed(42)
    
    price = 50000 + np.cumsum(np.random.randn(100) * 100)
    
    data = pd.DataFrame({
        'open': price - np.random.rand(100) * 50,
        'high': price + np.random.rand(100) * 100,
        'low': price - np.random.rand(100) * 100,
        'close': price,
        'volume': np.random.uniform(1e6, 5e6, 100)
    }, index=dates)
    
    # Run scanner
    scanner = HybridScanner(config={'min_confluence': 2, 'min_confidence': 50})
    signal = scanner.scan(data, 'BTCUSDT')
    
    if signal:
        print(f"\n=== Hybrid Signal ===")
        print(f"Symbol: {signal.symbol}")
        print(f"Direction: {signal.direction}")
        print(f"Confidence: {signal.confidence}%")
        print(f"Entry: ${signal.entry_price:,.2f}")
        print(f"Stop Loss: ${signal.stop_loss:,.2f}")
        print(f"Take Profit: ${signal.take_profit:,.2f}")
        print(f"Risk/Reward: {signal.risk_reward}")
        print(f"Confluence: {signal.confluence_count} signals")
        print(f"\nContributing signals:")
        for s in signal.contributing_signals:
            print(f"  - {s.scanner_type.value}: {s.signal} (Score: {s.score})")
    else:
        print("No signal found")
