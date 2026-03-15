"""
Helper Functions Module
Common utility functions
"""
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safe division avoiding zero division"""
    try:
        if b == 0:
            return default
        return a / b
    except:
        return default


def round_to_tick(price: float, tick_size: float) -> float:
    """Round price to nearest tick size"""
    return round(price / tick_size) * tick_size


def calculate_pct_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def normalize_series(series: pd.Series) -> pd.Series:
    """Normalize series to 0-1 range"""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(0.5, index=series.index)
    return (series - min_val) / (max_val - min_val)


def standardize_series(series: pd.Series) -> pd.Series:
    """Standardize series (z-score)"""
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(0, index=series.index)
    return (series - mean) / std


def resample_ohlc(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample OHLC data to different timeframe"""
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    return resampled


def calculate_returns(prices: pd.Series, method: str = 'simple') -> pd.Series:
    """Calculate returns from price series"""
    if method == 'log':
        return np.log(prices / prices.shift(1))
    else:
        return prices.pct_change()


def calculate_rolling_stats(series: pd.Series, window: int) -> Dict[str, pd.Series]:
    """Calculate rolling statistics"""
    return {
        'mean': series.rolling(window).mean(),
        'std': series.rolling(window).std(),
        'min': series.rolling(window).min(),
        'max': series.rolling(window).max(),
        'median': series.rolling(window).median()
    }


def find_peaks(series: pd.Series, order: int = 5) -> List[int]:
    """Find local maxima in series"""
    peaks = []
    for i in range(order, len(series) - order):
        if all(series.iloc[i] > series.iloc[i-j] for j in range(1, order+1)) and \
           all(series.iloc[i] > series.iloc[i+j] for j in range(1, order+1)):
            peaks.append(i)
    return peaks


def find_troughs(series: pd.Series, order: int = 5) -> List[int]:
    """Find local minima in series"""
    troughs = []
    for i in range(order, len(series) - order):
        if all(series.iloc[i] < series.iloc[i-j] for j in range(1, order+1)) and \
           all(series.iloc[i] < series.iloc[i+j] for j in range(1, order+1)):
            troughs.append(i)
    return troughs


def timestamp_to_str(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Convert datetime to string"""
    return dt.strftime(fmt) if dt else ''


def str_to_timestamp(s: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """Convert string to datetime"""
    try:
        return datetime.strptime(s, fmt)
    except:
        return None


def trading_days_between(start: datetime, end: datetime) -> int:
    """Calculate trading days between two dates"""
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Monday=0, Friday=4
            days += 1
        current += timedelta(days=1)
    return days


def format_number(value: float, decimals: int = 2, prefix: str = '') -> str:
    """Format number with thousand separators"""
    return f"{prefix}{value:,.{decimals}f}"


def format_pct(value: float, decimals: int = 2) -> str:
    """Format as percentage"""
    return f"{value:.{decimals}f}%"


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def moving_average(series: pd.Series, window: int, ma_type: str = 'sma') -> pd.Series:
    """Calculate moving average"""
    if ma_type == 'ema':
        return series.ewm(span=window, adjust=False).mean()
    elif ma_type == 'wma':
        weights = np.arange(1, window + 1)
        return series.rolling(window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    else:  # sma
        return series.rolling(window).mean()
