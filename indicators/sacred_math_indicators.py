"""
Sacred Math Indicators Module
Fibonacci, Golden Ratio, and Sacred Geometry indicators
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger


# Golden Ratio and Fibonacci constants
PHI = 1.6180339887498949  # Golden Ratio
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
FIB_RATIOS = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618]


def calculate_fibonacci_levels(high: float, low: float, direction: str = 'up') -> Dict:
    """Calculate Fibonacci retracement levels."""
    diff = high - low
    
    if direction == 'up':
        levels = {
            '0.0%': high,
            '23.6%': high - diff * 0.236,
            '38.2%': high - diff * 0.382,
            '50.0%': high - diff * 0.5,
            '61.8%': high - diff * 0.618,
            '78.6%': high - diff * 0.786,
            '100.0%': low
        }
    else:
        levels = {
            '0.0%': low,
            '23.6%': low + diff * 0.236,
            '38.2%': low + diff * 0.382,
            '50.0%': low + diff * 0.5,
            '61.8%': low + diff * 0.618,
            '78.6%': low + diff * 0.786,
            '100.0%': high
        }
    
    return levels


def calculate_fibonacci_extensions(
    swing_low: float,
    swing_high: float,
    retracement_low: float
) -> Dict:
    """Calculate Fibonacci extension levels."""
    diff = swing_high - swing_low
    
    return {
        '100.0%': retracement_low + diff,
        '127.2%': retracement_low + diff * 1.272,
        '161.8%': retracement_low + diff * 1.618,
        '200.0%': retracement_low + diff * 2.0,
        '261.8%': retracement_low + diff * 2.618
    }


def golden_ratio_oscillator(series: pd.Series, period: int = 21) -> pd.Series:
    """Oscillator based on golden ratio relationships."""
    high_period = series.rolling(period).max()
    low_period = series.rolling(period).min()
    
    # Position relative to golden ratio points
    range_size = high_period - low_period
    golden_upper = low_period + range_size * (1 / PHI)
    golden_lower = low_period + range_size * (1 - 1 / PHI)
    
    osc = (series - golden_lower) / (golden_upper - golden_lower)
    return osc.fillna(0.5)


def fibonacci_time_zones(start_index: int, total_length: int) -> List[int]:
    """Calculate Fibonacci time zones from a starting point."""
    zones = []
    for fib in FIBONACCI:
        zone = start_index + fib
        if zone < total_length:
            zones.append(zone)
    return zones


def sacred_geometry_levels(price: float) -> Dict:
    """Calculate price levels based on sacred geometry."""
    sqrt_price = np.sqrt(price)
    
    return {
        'phi_up_1': price * PHI,
        'phi_up_2': price * PHI * PHI,
        'phi_down_1': price / PHI,
        'phi_down_2': price / (PHI * PHI),
        'sqrt_up': (sqrt_price + 1) ** 2,
        'sqrt_down': max(0, (sqrt_price - 1) ** 2),
        'octave_up': price * 2,
        'octave_down': price / 2,
        'fifth_up': price * 1.5,
        'fifth_down': price / 1.5
    }


def calculate_vesica_piscis_levels(high: float, low: float) -> Dict:
    """Calculate Vesica Piscis ratio levels (related to √3)."""
    sqrt3 = np.sqrt(3)
    center = (high + low) / 2
    diff = high - low
    
    return {
        'upper_vesica': center + diff * sqrt3 / 2,
        'lower_vesica': center - diff * sqrt3 / 2,
        'center': center,
        'inner_upper': center + diff / (2 * sqrt3),
        'inner_lower': center - diff / (2 * sqrt3)
    }


class SacredMathIndicators:
    """Collection of sacred math based indicators."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("SacredMathIndicators initialized")
    
    def fibonacci_analysis(self, data: pd.DataFrame) -> Dict:
        """Complete Fibonacci analysis."""
        high = float(data['high'].max())
        low = float(data['low'].min())
        current = float(data['close'].iloc[-1])
        
        retracement = calculate_fibonacci_levels(high, low)
        
        # Find nearest levels
        levels_list = list(retracement.values())
        nearest_support = max([l for l in levels_list if l < current], default=low)
        nearest_resistance = min([l for l in levels_list if l > current], default=high)
        
        return {
            'levels': retracement,
            'current_price': current,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'position_pct': (current - low) / (high - low) * 100 if high != low else 50
        }
    
    def golden_ratio_analysis(self, data: pd.DataFrame) -> Dict:
        """Golden ratio based analysis."""
        current = float(data['close'].iloc[-1])
        
        osc = golden_ratio_oscillator(data['close'])
        current_osc = float(osc.iloc[-1])
        
        sacred_levels = sacred_geometry_levels(current)
        
        return {
            'oscillator': current_osc,
            'osc_signal': 'overbought' if current_osc > 1 else 'oversold' if current_osc < 0 else 'neutral',
            'sacred_levels': sacred_levels,
            'phi_ratio': PHI
        }
    
    def time_analysis(self, data: pd.DataFrame) -> Dict:
        """Time-based sacred math analysis."""
        n = len(data)
        
        # Find major pivot points
        pivots = []
        for i in range(2, min(50, n - 2)):
            if (data['high'].iloc[i] >= data['high'].iloc[i-1] and
                data['high'].iloc[i] >= data['high'].iloc[i+1]):
                pivots.append({'index': i, 'type': 'high'})
        
        if pivots:
            last_pivot = pivots[-1]['index']
            fib_zones = fibonacci_time_zones(last_pivot, n + 50)
            upcoming = [z for z in fib_zones if z >= n]
        else:
            upcoming = []
        
        return {
            'pivot_count': len(pivots),
            'last_pivot_bars_ago': n - pivots[-1]['index'] if pivots else None,
            'upcoming_fib_bars': upcoming[:5]
        }


if __name__ == "__main__":
    # Test
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1D')
    prices = np.linspace(45000, 55000, 100) + np.random.randn(100) * 500
    
    data = pd.DataFrame({
        'open': prices * 0.998,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 100)
    }, index=dates)
    
    indicators = SacredMathIndicators()
    
    print("\n=== Fibonacci Analysis ===")
    fib = indicators.fibonacci_analysis(data)
    print(f"Position: {fib['position_pct']:.1f}%")
    print(f"Nearest Support: {fib['nearest_support']:.0f}")
    print(f"Nearest Resistance: {fib['nearest_resistance']:.0f}")
    
    print("\n=== Golden Ratio ===")
    golden = indicators.golden_ratio_analysis(data)
    print(f"Oscillator: {golden['oscillator']:.2f} ({golden['osc_signal']})")
