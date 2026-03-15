"""
Math Tools Module
Mathematical utilities for trading calculations
"""
import numpy as np
from typing import List, Tuple, Optional
from loguru import logger


# Sacred geometry constants
PHI = 1.618033988749895  # Golden ratio
SQRT_PHI = np.sqrt(PHI)
PI = np.pi
SQRT_2 = np.sqrt(2)
SQRT_3 = np.sqrt(3)
SQRT_5 = np.sqrt(5)


def fibonacci_sequence(n: int) -> List[int]:
    """Generate Fibonacci sequence"""
    if n <= 0:
        return []
    if n == 1:
        return [1]
    
    fib = [1, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib


def fibonacci_retracements(high: float, low: float) -> dict:
    """Calculate Fibonacci retracement levels"""
    diff = high - low
    return {
        '0.0': high,
        '0.236': high - diff * 0.236,
        '0.382': high - diff * 0.382,
        '0.5': high - diff * 0.5,
        '0.618': high - diff * 0.618,
        '0.786': high - diff * 0.786,
        '1.0': low
    }


def fibonacci_extensions(high: float, low: float, retracement: float) -> dict:
    """Calculate Fibonacci extension levels"""
    diff = high - low
    return {
        '1.0': retracement + diff * 1.0,
        '1.272': retracement + diff * 1.272,
        '1.414': retracement + diff * 1.414,
        '1.618': retracement + diff * 1.618,
        '2.0': retracement + diff * 2.0,
        '2.618': retracement + diff * 2.618
    }


def gann_square_root(price: float) -> float:
    """Calculate Gann square root"""
    return np.sqrt(price)


def gann_natural_squares(base: int, n: int = 10) -> List[int]:
    """Generate natural square numbers"""
    return [(base + i) ** 2 for i in range(n)]


def calculate_pivot_points(high: float, low: float, close: float) -> dict:
    """Calculate pivot points"""
    pivot = (high + low + close) / 3
    
    return {
        'pivot': pivot,
        's1': 2 * pivot - high,
        's2': pivot - (high - low),
        's3': low - 2 * (high - pivot),
        'r1': 2 * pivot - low,
        'r2': pivot + (high - low),
        'r3': high + 2 * (pivot - low)
    }


def calculate_camarilla_pivots(high: float, low: float, close: float) -> dict:
    """Calculate Camarilla pivot levels"""
    diff = high - low
    
    return {
        'h4': close + diff * 1.1 / 2,
        'h3': close + diff * 1.1 / 4,
        'h2': close + diff * 1.1 / 6,
        'h1': close + diff * 1.1 / 12,
        'l1': close - diff * 1.1 / 12,
        'l2': close - diff * 1.1 / 6,
        'l3': close - diff * 1.1 / 4,
        'l4': close - diff * 1.1 / 2
    }


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians"""
    return degrees * PI / 180


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees"""
    return radians * 180 / PI


def polar_to_cartesian(r: float, theta: float) -> Tuple[float, float]:
    """Convert polar to cartesian coordinates"""
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return (x, y)


def cartesian_to_polar(x: float, y: float) -> Tuple[float, float]:
    """Convert cartesian to polar coordinates"""
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return (r, theta)


def calculate_volatility(returns: np.ndarray, annualize: bool = True) -> float:
    """Calculate volatility from returns"""
    vol = np.std(returns)
    if annualize:
        vol *= np.sqrt(252)  # Trading days per year
    return vol


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio"""
    excess_returns = returns - risk_free_rate / 252
    if np.std(excess_returns) == 0:
        return 0
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)


def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate Sortino ratio (downside deviation)"""
    excess_returns = returns - risk_free_rate / 252
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0 or np.std(downside_returns) == 0:
        return 0
    
    return np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)


def calculate_max_drawdown(equity_curve: np.ndarray) -> Tuple[float, int, int]:
    """Calculate maximum drawdown"""
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (peak - equity_curve) / peak
    
    max_dd = np.max(drawdown)
    end_idx = np.argmax(drawdown)
    start_idx = np.argmax(equity_curve[:end_idx]) if end_idx > 0 else 0
    
    return (max_dd, start_idx, end_idx)


def linear_regression(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Simple linear regression"""
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_xx = np.sum(x * x)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n
    
    return (slope, intercept)


def exponential_smoothing(series: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Exponential smoothing"""
    result = np.zeros_like(series)
    result[0] = series[0]
    
    for i in range(1, len(series)):
        result[i] = alpha * series[i] + (1 - alpha) * result[i-1]
    
    return result
