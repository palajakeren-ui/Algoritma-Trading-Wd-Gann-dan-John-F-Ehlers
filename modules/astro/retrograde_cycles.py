"""
Retrograde Cycles Module
Planetary retrograde analysis for trading
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class RetrogradeCycles:
    """
    Planetary retrograde cycle analysis.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        # Average retrograde periods (approximate)
        self.retrograde_info = {
            'Mercury': {'frequency': 3, 'duration': 21, 'year_days': 88},
            'Venus': {'frequency': 1, 'duration': 42, 'year_days': 225},
            'Mars': {'frequency': 1, 'duration': 72, 'year_days': 687},
            'Jupiter': {'frequency': 1, 'duration': 120, 'year_days': 4333},
            'Saturn': {'frequency': 1, 'duration': 140, 'year_days': 10759}
        }
        logger.info("RetrogradeCycles initialized")
    
    def get_retrograde_schedule(self, year: int) -> List[Dict]:
        """Get retrograde schedule for a year (approximation)"""
        schedule = []
        
        # Mercury retrogrades 2024 (example - would normally use ephemeris)
        mercury_retros = [
            (f'{year}-01-01', f'{year}-01-21'),
            (f'{year}-04-01', f'{year}-04-25'),
            (f'{year}-08-04', f'{year}-08-28'),
            (f'{year}-11-25', f'{year}-12-15')
        ]
        
        for start, end in mercury_retros:
            schedule.append({
                'planet': 'Mercury',
                'start': datetime.strptime(start, '%Y-%m-%d'),
                'end': datetime.strptime(end, '%Y-%m-%d'),
                'type': 'retrograde',
                'market_effect': 'communication_issues'
            })
        
        # Venus retrograde
        schedule.append({
            'planet': 'Venus',
            'start': datetime(year, 7, 22),
            'end': datetime(year, 9, 3),
            'type': 'retrograde',
            'market_effect': 'value_reassessment'
        })
        
        # Mars retrograde
        schedule.append({
            'planet': 'Mars',
            'start': datetime(year, 12, 6),
            'end': datetime(year + 1, 2, 23),
            'type': 'retrograde',
            'market_effect': 'action_delayed'
        })
        
        return sorted(schedule, key=lambda x: x['start'])
    
    def is_retrograde(self, planet: str, date: datetime) -> bool:
        """Check if planet is in retrograde on date"""
        schedule = self.get_retrograde_schedule(date.year)
        
        for retro in schedule:
            if retro['planet'] == planet:
                if retro['start'] <= date <= retro['end']:
                    return True
        
        return False
    
    def get_active_retrogrades(self, date: datetime) -> List[str]:
        """Get list of planets currently in retrograde"""
        active = []
        
        for planet in self.retrograde_info.keys():
            if self.is_retrograde(planet, date):
                active.append(planet)
        
        return active
    
    def analyze_retrograde_impact(self, date: datetime) -> Dict:
        """Analyze retrograde impact on date"""
        active = self.get_active_retrogrades(date)
        
        impact_score = 0
        effects = []
        
        if 'Mercury' in active:
            impact_score += 0.3
            effects.append('Communication delays, tech issues')
        if 'Venus' in active:
            impact_score += 0.2
            effects.append('Value reassessment, relationship issues')
        if 'Mars' in active:
            impact_score += 0.3
            effects.append('Action delays, conflict potential')
        if 'Jupiter' in active:
            impact_score += 0.1
            effects.append('Growth review period')
        if 'Saturn' in active:
            impact_score += 0.1
            effects.append('Structure reassessment')
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'active_retrogrades': active,
            'impact_score': round(impact_score, 2),
            'effects': effects,
            'trading_caution': impact_score > 0.3
        }
    
    def get_shadow_periods(self, planet: str, year: int) -> List[Dict]:
        """Get pre and post retrograde shadow periods"""
        schedule = self.get_retrograde_schedule(year)
        shadows = []
        
        shadow_days = {'Mercury': 14, 'Venus': 21, 'Mars': 30}
        
        for retro in schedule:
            if retro['planet'] == planet:
                shadow_len = shadow_days.get(planet, 14)
                shadows.append({
                    'planet': planet,
                    'pre_shadow_start': retro['start'] - timedelta(days=shadow_len),
                    'retrograde_start': retro['start'],
                    'retrograde_end': retro['end'],
                    'post_shadow_end': retro['end'] + timedelta(days=shadow_len)
                })
        
        return shadows
