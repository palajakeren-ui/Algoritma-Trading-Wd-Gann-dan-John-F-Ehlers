"""
Gann Square of 144 Module
Master time cycle analysis based on 144 (12x12)
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class SquareOf144:
    """
    Gann Square of 144 - The Master Square.
    144 = 12² representing mastery of time and price.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.master_number = 144
        logger.info("SquareOf144 initialized")
    
    def get_levels(self, base_price: float, n_levels: int = 12) -> Dict[str, List[float]]:
        """Calculate Square of 144 price levels"""
        sqrt_price = np.sqrt(base_price)
        
        support = []
        resistance = []
        
        # 144 divisions
        increment = sqrt_price / self.master_number
        
        # Key divisions: 12, 24, 36, 48, 72, 96, 120, 144
        key_points = [12, 24, 36, 48, 60, 72, 84, 96, 108, 120, 132, 144]
        
        for point in key_points[:n_levels]:
            offset = increment * point
            
            res_sqrt = sqrt_price + offset
            resistance.append(round(res_sqrt ** 2, 2))
            
            sup_sqrt = sqrt_price - offset
            if sup_sqrt > 0:
                support.append(round(sup_sqrt ** 2, 2))
        
        return {'support': support, 'resistance': resistance}
    
    def get_time_cycles(self, start_date: datetime, n_cycles: int = 4) -> List[Dict]:
        """Get 144-based time cycles"""
        cycles = []
        
        # Key time intervals in days
        intervals = [12, 36, 72, 144, 288, 432]
        
        for mult in range(n_cycles):
            for days in intervals:
                total_days = days + (144 * mult)
                cycle_date = start_date + timedelta(days=total_days)
                cycles.append({
                    'date': cycle_date,
                    'days': total_days,
                    'type': 'master' if total_days % 144 == 0 else 'minor',
                    'harmonic': total_days / 12
                })
        
        return sorted(cycles, key=lambda x: x['date'])
    
    def get_grid(self, base_price: float, grid_size: int = 12) -> np.ndarray:
        """Generate 12x12 price grid"""
        sqrt_base = np.sqrt(base_price)
        increment = sqrt_base / self.master_number * 12
        
        grid = np.zeros((grid_size, grid_size))
        
        for i in range(grid_size):
            for j in range(grid_size):
                cell_offset = (i * grid_size + j + 1) * increment / 12
                grid[i, j] = (sqrt_base + cell_offset) ** 2
        
        return grid
    
    def find_harmonic_price(self, current_price: float, target_harmonic: int = 12) -> Dict:
        """Find next harmonic price level"""
        sqrt_price = np.sqrt(current_price)
        increment = sqrt_price / self.master_number
        
        # Find current position
        remainder = int(sqrt_price / increment) % target_harmonic
        
        # Next harmonic
        to_next = target_harmonic - remainder
        next_price = (sqrt_price + increment * to_next) ** 2
        
        return {
            'current_position': int(sqrt_price / increment),
            'next_harmonic_price': round(next_price, 2),
            'distance': round(next_price - current_price, 2),
            'harmonic': target_harmonic
        }
