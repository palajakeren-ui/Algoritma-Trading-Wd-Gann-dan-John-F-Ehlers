"""
Strategies Module
Collection of trading strategies
"""
from .base_strategy import BaseStrategy
from .trend_strategy import TrendFollowingStrategy
from .gann_strategy import GannStrategy

__all__ = [
    'BaseStrategy',
    'TrendFollowingStrategy',
    'GannStrategy'
]
