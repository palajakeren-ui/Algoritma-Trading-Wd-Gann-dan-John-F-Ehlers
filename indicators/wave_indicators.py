"""
Wave Indicators Module
Elliott Wave and market wave analysis indicators
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class WaveType(Enum):
    IMPULSE = "impulse"
    CORRECTIVE = "corrective"
    DIAGONAL = "diagonal"
    TRIANGLE = "triangle"


class WaveDirection(Enum):
    UP = "up"
    DOWN = "down"


@dataclass
class Wave:
    number: int
    wave_type: WaveType
    direction: WaveDirection
    start_index: int
    end_index: int
    start_price: float
    end_price: float
    change_pct: float


def identify_zigzag(data: pd.DataFrame, threshold_pct: float = 3.0) -> List[Dict]:
    """Identify zigzag turning points."""
    zigzag = []
    n = len(data)
    
    if n < 5:
        return zigzag
    
    direction = None
    last_extreme = {'idx': 0, 'price': float(data['close'].iloc[0]), 'type': None}
    
    for i in range(1, n):
        current = float(data['close'].iloc[i])
        change_pct = (current - last_extreme['price']) / last_extreme['price'] * 100
        
        if abs(change_pct) >= threshold_pct:
            if change_pct > 0:
                if direction == 'down' or direction is None:
                    if last_extreme['type'] != 'low':
                        zigzag.append({
                            'idx': last_extreme['idx'],
                            'price': last_extreme['price'],
                            'type': 'low'
                        })
                direction = 'up'
                last_extreme = {'idx': i, 'price': current, 'type': 'high'}
            else:
                if direction == 'up' or direction is None:
                    if last_extreme['type'] != 'high':
                        zigzag.append({
                            'idx': last_extreme['idx'],
                            'price': last_extreme['price'],
                            'type': 'high'
                        })
                direction = 'down'
                last_extreme = {'idx': i, 'price': current, 'type': 'low'}
    
    return zigzag


def wave_momentum(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate wave-based momentum."""
    momentum = pd.Series(index=series.index, dtype=float)
    
    for i in range(period, len(series)):
        window = series.iloc[i-period:i+1]
        
        # Calculate wave strength
        returns = window.pct_change().dropna()
        pos_sum = returns[returns > 0].sum()
        neg_sum = abs(returns[returns < 0].sum())
        
        if neg_sum == 0:
            momentum.iloc[i] = 100
        else:
            momentum.iloc[i] = 100 - (100 / (1 + pos_sum / neg_sum))
    
    return momentum


def wave_ratio_indicator(series: pd.Series, period: int = 20) -> pd.Series:
    """Calculate wave ratio based on swing relationships."""
    ratio = pd.Series(index=series.index, dtype=float)
    ratio[:] = 1.0
    
    for i in range(period * 2, len(series)):
        window = series.iloc[i-period*2:i+1]
        
        # Find swings
        high = window.max()
        low = window.min()
        
        if low != 0:
            current_ratio = high / low
            ratio.iloc[i] = current_ratio
    
    return ratio


def calculate_wave_count(zigzag: List[Dict]) -> Dict:
    """Attempt to count Elliott Waves from zigzag."""
    if len(zigzag) < 5:
        return {'wave_count': 0, 'pattern': 'incomplete'}
    
    # Simple wave counting
    waves = []
    for i in range(len(zigzag) - 1):
        start = zigzag[i]
        end = zigzag[i + 1]
        
        direction = WaveDirection.UP if end['price'] > start['price'] else WaveDirection.DOWN
        change = (end['price'] - start['price']) / start['price'] * 100
        
        waves.append({
            'number': len(waves) + 1,
            'direction': direction.value,
            'change_pct': round(change, 2),
            'start_idx': start['idx'],
            'end_idx': end['idx']
        })
    
    # Check for 5-wave pattern
    if len(waves) >= 5:
        up_waves = [w for w in waves[:5] if w['direction'] == 'up']
        if len(up_waves) == 3:
            pattern = 'impulse_up'
        elif len(up_waves) == 2:
            pattern = 'impulse_down'
        else:
            pattern = 'corrective'
    else:
        pattern = 'developing'
    
    return {
        'wave_count': len(waves),
        'pattern': pattern,
        'waves': waves[:5]
    }


class WaveIndicators:
    """Collection of wave-based indicators."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.zigzag_threshold = self.config.get('zigzag_threshold', 3.0)
        logger.info("WaveIndicators initialized")
    
    def analyze_waves(self, data: pd.DataFrame) -> Dict:
        """Complete wave analysis."""
        # Identify zigzag points
        zigzag = identify_zigzag(data, self.zigzag_threshold)
        
        # Count waves
        wave_count = calculate_wave_count(zigzag)
        
        # Calculate momentum
        momentum = wave_momentum(data['close'])
        current_momentum = float(momentum.iloc[-1]) if not momentum.empty else 50
        
        # Wave ratio
        ratio = wave_ratio_indicator(data['close'])
        current_ratio = float(ratio.iloc[-1]) if not ratio.empty else 1.0
        
        return {
            'zigzag_points': len(zigzag),
            'wave_analysis': wave_count,
            'momentum': round(current_momentum, 2),
            'wave_ratio': round(current_ratio, 3),
            'trend': 'bullish' if current_momentum > 60 else 'bearish' if current_momentum < 40 else 'neutral'
        }
    
    def get_current_wave(self, data: pd.DataFrame) -> Dict:
        """Determine current wave position."""
        zigzag = identify_zigzag(data, self.zigzag_threshold)
        
        if len(zigzag) < 2:
            return {'wave_number': 0, 'in_progress': True}
        
        last = zigzag[-1]
        current_price = float(data['close'].iloc[-1])
        
        if last['type'] == 'low':
            wave_dir = 'up'
            progress = (current_price - last['price']) / last['price'] * 100
        else:
            wave_dir = 'down'
            progress = (last['price'] - current_price) / last['price'] * 100
        
        return {
            'wave_number': len(zigzag),
            'direction': wave_dir,
            'progress_pct': round(progress, 2),
            'since_last_pivot': len(data) - last['idx']
        }
    
    def fibonacci_wave_targets(self, data: pd.DataFrame) -> Dict:
        """Calculate wave-based Fibonacci targets."""
        zigzag = identify_zigzag(data, self.zigzag_threshold)
        
        if len(zigzag) < 3:
            return {'targets': []}
        
        # Use last complete wave
        wave_start = zigzag[-2]
        wave_end = zigzag[-1]
        
        wave_size = abs(wave_end['price'] - wave_start['price'])
        current = float(data['close'].iloc[-1])
        
        if wave_end['type'] == 'low':
            # Expecting up wave
            targets = {
                '38.2%': wave_end['price'] + wave_size * 0.382,
                '50.0%': wave_end['price'] + wave_size * 0.5,
                '61.8%': wave_end['price'] + wave_size * 0.618,
                '100%': wave_end['price'] + wave_size,
                '161.8%': wave_end['price'] + wave_size * 1.618
            }
        else:
            # Expecting down wave
            targets = {
                '38.2%': wave_end['price'] - wave_size * 0.382,
                '50.0%': wave_end['price'] - wave_size * 0.5,
                '61.8%': wave_end['price'] - wave_size * 0.618,
                '100%': wave_end['price'] - wave_size,
                '161.8%': wave_end['price'] - wave_size * 1.618
            }
        
        return {
            'targets': {k: round(v, 2) for k, v in targets.items()},
            'wave_size': round(wave_size, 2),
            'last_pivot_type': wave_end['type']
        }


if __name__ == "__main__":
    # Test
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1D')
    np.random.seed(42)
    
    # Create wave-like price action
    t = np.arange(100)
    wave = 2000 * np.sin(2 * np.pi * t / 20)
    trend = 50000 + t * 20
    noise = np.cumsum(np.random.randn(100) * 100)
    prices = trend + wave + noise
    
    data = pd.DataFrame({
        'open': prices * 0.998,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 100)
    }, index=dates)
    
    indicators = WaveIndicators({'zigzag_threshold': 2.0})
    
    print("\n=== Wave Analysis ===")
    analysis = indicators.analyze_waves(data)
    print(f"Zigzag Points: {analysis['zigzag_points']}")
    print(f"Pattern: {analysis['wave_analysis']['pattern']}")
    print(f"Momentum: {analysis['momentum']}")
    print(f"Trend: {analysis['trend']}")
    
    print("\n=== Current Wave ===")
    current = indicators.get_current_wave(data)
    print(f"Wave: {current['wave_number']} ({current.get('direction', 'N/A')})")
    print(f"Progress: {current.get('progress_pct', 0):.1f}%")
