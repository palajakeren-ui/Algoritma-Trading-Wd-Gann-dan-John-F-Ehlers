"""
Gann Time Analysis Module
Time cycle and vibration calculations
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger


class GannTime:
    """
    Gann Time Analysis for cycle timing.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        # Key Gann time intervals
        self.key_intervals = [7, 14, 21, 28, 30, 45, 49, 60, 90, 120, 144, 180, 270, 360]
        logger.info("GannTime initialized")
    
    def get_time_cycles(self, pivot_date: datetime, look_ahead: int = 365) -> List[Dict]:
        """Get upcoming time cycles from pivot"""
        cycles = []
        
        for days in self.key_intervals:
            # Forward cycle
            future_date = pivot_date + timedelta(days=days)
            if (future_date - datetime.now()).days <= look_ahead:
                cycles.append({
                    'date': future_date,
                    'days_from_pivot': days,
                    'direction': 'forward',
                    'strength': self._get_cycle_strength(days),
                    'type': self._get_cycle_type(days)
                })
        
        return sorted(cycles, key=lambda x: x['date'])
    
    def _get_cycle_strength(self, days: int) -> float:
        """Determine cycle strength based on days"""
        major_cycles = [90, 180, 270, 360, 144]
        minor_cycles = [30, 45, 60, 120]
        
        if days in major_cycles:
            return 1.0
        elif days in minor_cycles:
            return 0.7
        else:
            return 0.5
    
    def _get_cycle_type(self, days: int) -> str:
        """Categorize cycle type"""
        if days in [7, 14, 21, 28]:
            return 'weekly'
        elif days in [30, 60, 90]:
            return 'monthly'
        elif days in [180, 360]:
            return 'semi-annual'
        elif days == 144:
            return 'master'
        else:
            return 'geometric'
    
    def calculate_vibration(self, date1: datetime, date2: datetime) -> Dict:
        """Calculate time vibration between two dates"""
        days_diff = abs((date2 - date1).days)
        
        # Find nearest Gann cycle
        nearest_cycle = min(self.key_intervals, key=lambda x: abs(x - days_diff))
        deviation = days_diff - nearest_cycle
        
        return {
            'days': days_diff,
            'nearest_cycle': nearest_cycle,
            'deviation_days': deviation,
            'harmony': 1 - abs(deviation) / nearest_cycle if nearest_cycle > 0 else 0,
            'vibration_number': days_diff % 9  # Gann numerology
        }
    
    def get_seasonal_dates(self, year: int) -> Dict[str, datetime]:
        """Get Gann seasonal change dates"""
        return {
            'spring_equinox': datetime(year, 3, 21),
            'summer_solstice': datetime(year, 6, 21),
            'autumn_equinox': datetime(year, 9, 23),
            'winter_solstice': datetime(year, 12, 21),
            'mid_spring': datetime(year, 5, 5),
            'mid_summer': datetime(year, 8, 8),
            'mid_autumn': datetime(year, 11, 8),
            'mid_winter': datetime(year, 2, 4)
        }
    
    def time_price_square(self, price: float, start_date: datetime) -> List[Dict]:
        """Calculate when time equals price"""
        sqrt_price = np.sqrt(price)
        days_equivalent = int(sqrt_price)
        
        projections = []
        for mult in range(1, 5):
            target_days = int(days_equivalent * mult)
            target_date = start_date + timedelta(days=target_days)
            projections.append({
                'date': target_date,
                'days': target_days,
                'multiplier': mult,
                'type': 'time_equals_price'
            })
        
        return projections
