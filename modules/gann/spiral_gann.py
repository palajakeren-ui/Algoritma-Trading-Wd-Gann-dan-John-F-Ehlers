"""
Gann Spiral Module
Spiral calculations for time-price analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger


class SpiralGann:
    """
    Gann Spiral for logarithmic price-time relationships.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.golden_ratio = 1.618033988749895
        logger.info("SpiralGann initialized")
    
    def calculate_spiral(self, center_price: float, n_turns: int = 4) -> List[Dict]:
        """Calculate spiral price levels"""
        spiral_points = []
        
        for turn in range(n_turns * 360):
            angle = turn  # degrees
            radius = (self.golden_ratio ** (angle / 90)) * np.sqrt(center_price) / 100
            
            price = center_price + (radius * np.sqrt(center_price))
            
            if angle % 45 == 0:  # Key angles
                spiral_points.append({
                    'angle': angle % 360,
                    'turn': angle // 360,
                    'price': round(price, 2),
                    'type': 'major' if angle % 90 == 0 else 'minor'
                })
        
        return spiral_points
    
    def find_spiral_position(self, center_price: float, current_price: float) -> Dict:
        """Find position on spiral"""
        ratio = current_price / center_price
        log_ratio = np.log(ratio) / np.log(self.golden_ratio)
        
        angle = (log_ratio * 90) % 360
        turn = int(log_ratio * 90) // 360
        
        return {
            'angle': round(angle, 2),
            'turn': turn,
            'distance_from_center': round(ratio, 4),
            'quadrant': int(angle // 90) + 1
        }
    
    def get_fibonacci_spiral_levels(self, base_price: float) -> Dict[str, float]:
        """Get Fibonacci spiral price levels"""
        fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        
        levels = {}
        for fib in fib_sequence:
            levels[f'fib_{fib}'] = round(base_price * (self.golden_ratio ** (fib/10)), 2)
        
        return levels
    
    def project_spiral_target(self, start: float, end: float, projection_degrees: float = 180) -> Dict:
        """Project spiral price target"""
        move = abs(end - start)
        direction = 1 if end > start else -1
        
        # Spiral expansion
        expansion = self.golden_ratio ** (projection_degrees / 360)
        target = end + (move * expansion * direction)
        
        return {
            'projected_price': round(target, 2),
            'expansion_ratio': round(expansion, 4),
            'projection_degrees': projection_degrees,
            'direction': 'up' if direction > 0 else 'down'
        }
