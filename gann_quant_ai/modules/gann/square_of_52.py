"""
Gann Square of 52 Module
Weekly time cycle analysis based on 52 weeks per year
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger


class SquareOf52:
    """
    Gann Square of 52 for weekly cycle analysis.
    Based on 52 weeks in a year for time-price relationships.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.weeks_per_year = 52
        logger.info("SquareOf52 initialized")
    
    def get_levels(self, base_price: float, n_levels: int = 8) -> Dict[str, List[float]]:
        """Calculate Square of 52 price levels"""
        sqrt_price = np.sqrt(base_price)
        
        support = []
        resistance = []
        
        # Each level represents 1 week of the 52-week cycle
        increment = sqrt_price / self.weeks_per_year
        
        for i in range(1, n_levels + 1):
            # Resistance levels (price moving up)
            res_sqrt = sqrt_price + (increment * i * 4)  # 4-week intervals
            resistance.append(res_sqrt ** 2)
            
            # Support levels (price moving down)
            sup_sqrt = sqrt_price - (increment * i * 4)
            if sup_sqrt > 0:
                support.append(sup_sqrt ** 2)
        
        return {'support': support, 'resistance': resistance}
    
    def get_time_cycles(self, start_date: datetime, n_cycles: int = 4) -> List[Dict]:
        """Get weekly time cycle dates"""
        cycles = []
        
        # Key weekly intervals: 13, 26, 39, 52 weeks
        key_weeks = [13, 26, 39, 52]
        
        for multiplier in range(n_cycles):
            for weeks in key_weeks:
                cycle_date = start_date + timedelta(weeks=weeks + (52 * multiplier))
                cycles.append({
                    'date': cycle_date,
                    'weeks': weeks + (52 * multiplier),
                    'type': 'major' if weeks == 52 else 'minor',
                    'description': f'{weeks + (52 * multiplier)} week cycle'
                })
        
        return sorted(cycles, key=lambda x: x['date'])
    
    def analyze_weekly_position(self, date: datetime, reference_date: datetime) -> Dict:
        """Analyze position within 52-week cycle"""
        days_diff = (date - reference_date).days
        weeks_diff = days_diff / 7
        position_in_cycle = weeks_diff % 52
        
        # Determine phase
        if position_in_cycle < 13:
            phase = 'Q1 - Accumulation'
        elif position_in_cycle < 26:
            phase = 'Q2 - Markup'
        elif position_in_cycle < 39:
            phase = 'Q3 - Distribution'
        else:
            phase = 'Q4 - Markdown'
        
        return {
            'weeks_from_reference': int(weeks_diff),
            'position_in_cycle': round(position_in_cycle, 2),
            'phase': phase,
            'cycle_completion': round((position_in_cycle / 52) * 100, 2)
        }
