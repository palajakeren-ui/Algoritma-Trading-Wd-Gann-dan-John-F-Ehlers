"""
Gann Square of 90 Module
Quarter-year cycle analysis based on 90 days/degrees
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class SquareOf90:
    """
    Gann Square of 90 for quarterly cycle analysis.
    Based on 90 degrees (quarter of 360) for time-price relationships.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.degrees = 90
        logger.info("SquareOf90 initialized")
    
    def get_levels(self, base_price: float, n_levels: int = 8) -> Dict[str, List[float]]:
        """Calculate Square of 90 price levels"""
        sqrt_price = np.sqrt(base_price)
        
        support = []
        resistance = []
        
        # 90-degree increments
        increment = sqrt_price / self.degrees
        
        for i in range(1, n_levels + 1):
            # Key angles: 22.5, 45, 67.5, 90 degrees
            for angle in [22.5, 45, 67.5, 90]:
                offset = increment * angle * i / 90
                
                res_sqrt = sqrt_price + offset
                resistance.append(round(res_sqrt ** 2, 2))
                
                sup_sqrt = sqrt_price - offset
                if sup_sqrt > 0:
                    support.append(round(sup_sqrt ** 2, 2))
        
        # Remove duplicates and sort
        support = sorted(list(set(support)), reverse=True)
        resistance = sorted(list(set(resistance)))
        
        return {'support': support[:n_levels], 'resistance': resistance[:n_levels]}
    
    def get_quarterly_dates(self, start_date: datetime, n_quarters: int = 8) -> List[Dict]:
        """Get quarterly cycle dates (90-day intervals)"""
        dates = []
        
        for i in range(1, n_quarters + 1):
            cycle_date = start_date + timedelta(days=90 * i)
            dates.append({
                'date': cycle_date,
                'days': 90 * i,
                'quarter': i,
                'angle': (90 * i) % 360,
                'type': 'major' if (90 * i) % 360 == 0 else 'minor'
            })
        
        return dates
    
    def get_cardinal_levels(self, base_price: float) -> Dict[str, float]:
        """Get cardinal cross levels (0, 90, 180, 270, 360 degrees)"""
        sqrt_price = np.sqrt(base_price)
        unit = sqrt_price / 360
        
        return {
            '0': base_price,
            '90': (sqrt_price + unit * 90) ** 2,
            '180': (sqrt_price + unit * 180) ** 2,
            '270': (sqrt_price + unit * 270) ** 2,
            '360': (sqrt_price + unit * 360) ** 2
        }
