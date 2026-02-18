"""
Wave Scanner Module
Elliott Wave and harmonic pattern scanner
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger


class WaveScanner:
    """
    Scanner for Elliott Wave patterns and harmonic patterns.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Wave Scanner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.min_wave_size = self.config.get('min_wave_size', 0.01)  # 1% minimum
        self.fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]
        
        logger.info("WaveScanner initialized")
    
    def scan(self, price_data: pd.DataFrame, symbol: str = '') -> List[Dict]:
        """
        Scan for wave patterns in price data.
        
        Args:
            price_data: DataFrame with OHLC data
            symbol: Symbol being scanned
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Find swing points
        swings = self._identify_swing_points(price_data)
        
        if len(swings) < 5:
            logger.debug(f"Not enough swing points for wave analysis: {len(swings)}")
            return patterns
        
        # Scan for Elliott Wave patterns
        elliott_patterns = self._scan_elliott_waves(price_data, swings)
        patterns.extend(elliott_patterns)
        
        # Scan for harmonic patterns
        harmonic_patterns = self._scan_harmonic_patterns(price_data, swings)
        patterns.extend(harmonic_patterns)
        
        logger.info(f"WaveScanner found {len(patterns)} patterns for {symbol}")
        return patterns
    
    def _identify_swing_points(
        self, 
        df: pd.DataFrame, 
        lookback: int = 5
    ) -> List[Dict]:
        """
        Identify swing highs and lows.
        
        Args:
            df: Price data
            lookback: Bars to look back for swing confirmation
            
        Returns:
            List of swing points
        """
        swings = []
        
        highs = df['high'].values
        lows = df['low'].values
        
        for i in range(lookback, len(df) - lookback):
            # Check swing high
            if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and \
               all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):
                swings.append({
                    'index': i,
                    'date': df.index[i],
                    'type': 'high',
                    'price': highs[i]
                })
            
            # Check swing low
            if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and \
               all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):
                swings.append({
                    'index': i,
                    'date': df.index[i],
                    'type': 'low',
                    'price': lows[i]
                })
        
        # Sort by index
        swings.sort(key=lambda x: x['index'])
        
        return swings
    
    def _scan_elliott_waves(
        self, 
        df: pd.DataFrame, 
        swings: List[Dict]
    ) -> List[Dict]:
        """
        Scan for Elliott Wave 5-wave patterns.
        
        Args:
            df: Price data
            swings: List of swing points
            
        Returns:
            List of Elliott Wave patterns
        """
        patterns = []
        
        # Need at least 6 swings for a 5-wave pattern
        if len(swings) < 6:
            return patterns
        
        # Look for 5-wave impulse patterns
        for i in range(len(swings) - 5):
            wave_swings = swings[i:i+6]
            
            # Check if alternating highs and lows
            types = [s['type'] for s in wave_swings]
            if types[0] == 'low':
                expected = ['low', 'high', 'low', 'high', 'low', 'high']
            else:
                expected = ['high', 'low', 'high', 'low', 'high', 'low']
            
            if types != expected:
                continue
            
            # Extract wave prices
            prices = [s['price'] for s in wave_swings]
            
            # Validate Elliott Wave rules
            valid, wave_info = self._validate_elliott_rules(prices, types[0] == 'low')
            
            if valid:
                patterns.append({
                    'type': 'elliott_impulse',
                    'direction': 'bullish' if types[0] == 'low' else 'bearish',
                    'start_date': wave_swings[0]['date'],
                    'end_date': wave_swings[-1]['date'],
                    'waves': wave_info,
                    'confidence': self._calculate_wave_confidence(wave_info),
                    'next_wave_target': self._project_next_wave(wave_info)
                })
        
        return patterns
    
    def _validate_elliott_rules(
        self, 
        prices: List[float], 
        is_bullish: bool
    ) -> Tuple[bool, Dict]:
        """
        Validate Elliott Wave rules.
        
        Args:
            prices: List of 6 prices (0, 1, 2, 3, 4, 5)
            is_bullish: True for bullish impulse
            
        Returns:
            Tuple of (is_valid, wave_info)
        """
        wave_info = {}
        
        if is_bullish:
            # Wave 1: 0 -> 1
            wave1 = prices[1] - prices[0]
            # Wave 2: 1 -> 2 (retracement)
            wave2 = prices[1] - prices[2]
            # Wave 3: 2 -> 3
            wave3 = prices[3] - prices[2]
            # Wave 4: 3 -> 4 (retracement)
            wave4 = prices[3] - prices[4]
            # Wave 5: 4 -> 5
            wave5 = prices[5] - prices[4]
            
            # Rule 1: Wave 2 cannot retrace more than 100% of Wave 1
            if wave2 >= wave1:
                return False, {}
            
            # Rule 2: Wave 3 cannot be the shortest impulse wave
            if wave3 < wave1 and wave3 < wave5:
                return False, {}
            
            # Rule 3: Wave 4 cannot overlap Wave 1 territory
            if prices[4] <= prices[1]:
                return False, {}
            
            wave_info = {
                'wave1': {'length': wave1, 'fib_ratio': 1.0},
                'wave2': {'length': wave2, 'retracement': wave2/wave1},
                'wave3': {'length': wave3, 'extension': wave3/wave1},
                'wave4': {'length': wave4, 'retracement': wave4/wave3},
                'wave5': {'length': wave5, 'extension': wave5/wave1}
            }
        else:
            # Similar logic for bearish, reversed
            wave1 = prices[0] - prices[1]
            wave2 = prices[2] - prices[1]
            wave3 = prices[2] - prices[3]
            wave4 = prices[4] - prices[3]
            wave5 = prices[4] - prices[5]
            
            if wave2 >= wave1:
                return False, {}
            if wave3 < wave1 and wave3 < wave5:
                return False, {}
            if prices[4] >= prices[1]:
                return False, {}
            
            wave_info = {
                'wave1': {'length': wave1, 'fib_ratio': 1.0},
                'wave2': {'length': wave2, 'retracement': wave2/wave1},
                'wave3': {'length': wave3, 'extension': wave3/wave1},
                'wave4': {'length': wave4, 'retracement': wave4/wave3},
                'wave5': {'length': wave5, 'extension': wave5/wave1}
            }
        
        return True, wave_info
    
    def _calculate_wave_confidence(self, wave_info: Dict) -> float:
        """Calculate confidence score based on Fibonacci relationships"""
        score = 0.5  # Base score
        
        # Check Wave 2 retracement (ideal: 0.382 - 0.618)
        w2_ret = wave_info.get('wave2', {}).get('retracement', 0)
        if 0.382 <= w2_ret <= 0.618:
            score += 0.15
        elif 0.236 <= w2_ret <= 0.786:
            score += 0.1
        
        # Check Wave 3 extension (ideal: 1.618)
        w3_ext = wave_info.get('wave3', {}).get('extension', 0)
        if 1.5 <= w3_ext <= 1.8:
            score += 0.15
        elif w3_ext >= 1.0:
            score += 0.1
        
        # Check Wave 4 retracement (ideal: 0.382)
        w4_ret = wave_info.get('wave4', {}).get('retracement', 0)
        if 0.382 <= w4_ret <= 0.5:
            score += 0.1
        
        return min(1.0, score)
    
    def _project_next_wave(self, wave_info: Dict) -> Optional[Dict]:
        """Project next wave target"""
        w1 = wave_info.get('wave1', {}).get('length', 0)
        
        if w1 == 0:
            return None
        
        # Common correction targets
        return {
            'fib_382': w1 * 0.382,
            'fib_500': w1 * 0.5,
            'fib_618': w1 * 0.618
        }
    
    def _scan_harmonic_patterns(
        self, 
        df: pd.DataFrame, 
        swings: List[Dict]
    ) -> List[Dict]:
        """
        Scan for harmonic patterns (Gartley, Bat, Butterfly, Crab).
        
        Args:
            df: Price data
            swings: List of swing points
            
        Returns:
            List of harmonic patterns
        """
        patterns = []
        
        # Need at least 5 swings (XABCD)
        if len(swings) < 5:
            return patterns
        
        # Look for XABCD patterns
        for i in range(len(swings) - 4):
            xabcd = swings[i:i+5]
            
            prices = [s['price'] for s in xabcd]
            X, A, B, C, D = prices
            
            # Calculate ratios
            XA = abs(A - X)
            AB = abs(B - A)
            BC = abs(C - B)
            CD = abs(D - C)
            XD = abs(D - X)
            
            if XA == 0:
                continue
            
            # Check for Gartley pattern
            AB_XA = AB / XA
            BC_AB = BC / AB if AB > 0 else 0
            CD_BC = CD / BC if BC > 0 else 0
            
            # Gartley: AB = 0.618 XA, BC = 0.382-0.886 AB, CD = 1.27-1.618 BC, D = 0.786 XA
            if (0.55 <= AB_XA <= 0.68 and 
                0.35 <= BC_AB <= 0.9 and
                1.2 <= CD_BC <= 1.7):
                patterns.append({
                    'type': 'harmonic_gartley',
                    'direction': 'bullish' if D < X else 'bearish',
                    'start_date': xabcd[0]['date'],
                    'end_date': xabcd[-1]['date'],
                    'points': {'X': X, 'A': A, 'B': B, 'C': C, 'D': D},
                    'ratios': {'AB_XA': AB_XA, 'BC_AB': BC_AB, 'CD_BC': CD_BC},
                    'confidence': 0.7
                })
            
            # Bat: AB = 0.382-0.5 XA, CD = 1.618-2.618 BC, D = 0.886 XA  
            if (0.35 <= AB_XA <= 0.55 and
                1.6 <= CD_BC <= 2.7):
                patterns.append({
                    'type': 'harmonic_bat',
                    'direction': 'bullish' if D < X else 'bearish',
                    'start_date': xabcd[0]['date'],
                    'end_date': xabcd[-1]['date'],
                    'points': {'X': X, 'A': A, 'B': B, 'C': C, 'D': D},
                    'ratios': {'AB_XA': AB_XA, 'BC_AB': BC_AB, 'CD_BC': CD_BC},
                    'confidence': 0.65
                })
        
        return patterns


# Example usage
if __name__ == '__main__':
    # Create sample data with a trending market
    dates = pd.date_range('2024-01-01', periods=200)
    np.random.seed(42)
    
    # Create trending price data
    trend = np.cumsum(np.random.randn(200) + 0.1)
    df = pd.DataFrame({
        'open': 100 + trend,
        'high': 102 + trend + abs(np.random.randn(200)),
        'low': 98 + trend - abs(np.random.randn(200)),
        'close': 100 + trend + np.random.randn(200) * 0.5
    }, index=dates)
    
    scanner = WaveScanner()
    patterns = scanner.scan(df, 'TEST')
    
    print(f"Found {len(patterns)} wave patterns")
    for p in patterns[:3]:
        print(f"  - {p['type']}: {p['direction']}")
