"""
Gann Square of 360 Module
Full circle/year cycle analysis based on 360 degrees
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class SquareOf360:
    """
    Gann Square of 360 - The Circle of Time.
    360 degrees representing a complete cycle.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.full_circle = 360
        logger.info("SquareOf360 initialized")
    
    def get_levels(self, base_price: float, n_levels: int = 8) -> Dict[str, List[float]]:
        """Calculate Square of 360 price levels"""
        sqrt_price = np.sqrt(base_price)
        
        support = []
        resistance = []
        
        # Key angles in degrees
        key_angles = [30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330, 360]
        
        increment = sqrt_price / self.full_circle
        
        for angle in key_angles[:n_levels * 2]:
            offset = increment * angle
            
            res_sqrt = sqrt_price + offset
            resistance.append(round(res_sqrt ** 2, 2))
            
            sup_sqrt = sqrt_price - offset
            if sup_sqrt > 0:
                support.append(round(sup_sqrt ** 2, 2))
        
        return {'support': sorted(support)[:n_levels], 'resistance': resistance[:n_levels]}
    
    def get_degree_price(self, base_price: float, degrees: float) -> float:
        """Convert degrees to price level"""
        sqrt_price = np.sqrt(base_price)
        increment = sqrt_price / self.full_circle
        return (sqrt_price + increment * degrees) ** 2
    
    def get_price_degree(self, base_price: float, current_price: float) -> float:
        """Convert current price to degree position"""
        sqrt_base = np.sqrt(base_price)
        sqrt_current = np.sqrt(current_price)
        increment = sqrt_base / self.full_circle
        
        return ((sqrt_current - sqrt_base) / increment) % 360
    
    def get_annual_cycle(self, start_date: datetime) -> List[Dict]:
        """Get annual cycle dates (360-day trading year)"""
        cycles = []
        
        # Key angles and their dates
        key_points = [
            (0, 'Start'), (45, 'Minor'), (90, 'Quarter'),
            (135, 'Minor'), (180, 'Opposition'), (225, 'Minor'),
            (270, '3rd Quarter'), (315, 'Minor'), (360, 'Full Cycle')
        ]
        
        for degrees, label in key_points:
            # Approximate 360 trading days per year
            days = int(degrees * 365 / 360)
            cycle_date = start_date + timedelta(days=days)
            cycles.append({
                'date': cycle_date,
                'degrees': degrees,
                'label': label,
                'days': days,
                'type': 'major' if degrees % 90 == 0 else 'minor'
            })
        
        return cycles
    
    def get_zodiac_division(self, base_price: float) -> Dict[str, float]:
        """Get 12 zodiac sign price divisions (30° each)"""
        signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer',
            'Leo', 'Virgo', 'Libra', 'Scorpio',
            'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        levels = {}
        sqrt_price = np.sqrt(base_price)
        increment = sqrt_price / self.full_circle
        
        for i, sign in enumerate(signs):
            degrees = (i + 1) * 30
            levels[sign] = round((sqrt_price + increment * degrees) ** 2, 2)
        
        return levels
    
    def get_planetary_aspects(self, base_price: float) -> Dict[str, Dict]:
        """Get planetary aspect price levels"""
        sqrt_price = np.sqrt(base_price)
        increment = sqrt_price / self.full_circle
        
        aspects = {
            'conjunction': {'degrees': 0, 'price': base_price},
            'sextile': {'degrees': 60, 'price': (sqrt_price + increment * 60) ** 2},
            'square': {'degrees': 90, 'price': (sqrt_price + increment * 90) ** 2},
            'trine': {'degrees': 120, 'price': (sqrt_price + increment * 120) ** 2},
            'opposition': {'degrees': 180, 'price': (sqrt_price + increment * 180) ** 2}
        }
        
        for key in aspects:
            aspects[key]['price'] = round(aspects[key]['price'], 2)
        
        return aspects
