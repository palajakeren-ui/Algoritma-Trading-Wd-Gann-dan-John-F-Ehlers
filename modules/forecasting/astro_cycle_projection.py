"""
Astro Cycle Projection Module
Projects future price movements based on astrological cycles
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class PlanetaryInfluence(Enum):
    """Types of planetary influences"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"


@dataclass
class AstroProjection:
    """Astrological price projection"""
    date: datetime
    planet: str
    aspect: str
    influence: PlanetaryInfluence
    strength: float  # 0-1
    projected_direction: str
    confidence: float
    description: str


class AstroCycleProjector:
    """
    Projects market movements based on planetary cycles.
    Combines lunar phases, planetary aspects, and zodiac positions.
    """
    
    # Planetary orbital periods in days
    ORBITAL_PERIODS = {
        'Mercury': 87.969,
        'Venus': 224.701,
        'Mars': 686.980,
        'Jupiter': 4332.59,
        'Saturn': 10759.22,
        'Moon': 29.53
    }
    
    # Synodic cycles (relative to Earth)
    SYNODIC_CYCLES = {
        'Mercury': 115.88,
        'Venus': 583.92,
        'Mars': 779.94,
        'Jupiter': 398.88,
        'Saturn': 378.09
    }
    
    # Key aspects and their market implications
    ASPECTS = {
        0: ('conjunction', 0.9, 'volatile'),
        60: ('sextile', 0.6, 'bullish'),
        90: ('square', 0.8, 'bearish'),
        120: ('trine', 0.7, 'bullish'),
        180: ('opposition', 0.85, 'volatile')
    }
    
    def __init__(self, config: Dict = None):
        """Initialize the astro cycle projector."""
        self.config = config or {}
        self.projection_days = self.config.get('projection_days', 90)
        logger.info("AstroCycleProjector initialized")
    
    def calculate_julian_date(self, dt: datetime) -> float:
        """Calculate Julian Date from datetime."""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        jd += (dt.hour - 12) / 24 + dt.minute / 1440 + dt.second / 86400
        
        return jd
    
    def get_planet_longitude(self, planet: str, dt: datetime) -> float:
        """Get approximate heliocentric longitude for a planet."""
        jd = self.calculate_julian_date(dt)
        d = jd - 2451545.0  # Days from J2000.0
        
        period = self.ORBITAL_PERIODS.get(planet, 365.256)
        
        # Mean longitude (simplified)
        mean_longitude = (d / period * 360) % 360
        
        return mean_longitude
    
    def calculate_lunar_phase(self, dt: datetime) -> Dict:
        """Calculate moon phase for given date."""
        reference = datetime(2000, 1, 6, 18, 14)
        days_since = (dt - reference).total_seconds() / 86400
        
        lunation = days_since / 29.53059
        phase = lunation % 1
        
        # Phase name and market influence
        if phase < 0.125:
            name = 'New Moon'
            influence = 'bullish'
        elif phase < 0.25:
            name = 'Waxing Crescent'
            influence = 'neutral'
        elif phase < 0.375:
            name = 'First Quarter'
            influence = 'bullish'
        elif phase < 0.5:
            name = 'Waxing Gibbous'
            influence = 'bullish'
        elif phase < 0.625:
            name = 'Full Moon'
            influence = 'bearish'
        elif phase < 0.75:
            name = 'Waning Gibbous'
            influence = 'neutral'
        elif phase < 0.875:
            name = 'Last Quarter'
            influence = 'bearish'
        else:
            name = 'Waning Crescent'
            influence = 'neutral'
        
        return {
            'phase': round(phase, 4),
            'phase_name': name,
            'illumination': round(abs(np.cos(phase * 2 * np.pi)) * 100, 1),
            'influence': influence,
            'strength': 0.6 + 0.4 * abs(np.sin(phase * 2 * np.pi))
        }
    
    def calculate_aspect(self, planet1: str, planet2: str, dt: datetime) -> Optional[Dict]:
        """Calculate aspect between two planets."""
        lon1 = self.get_planet_longitude(planet1, dt)
        lon2 = self.get_planet_longitude(planet2, dt)
        
        diff = abs(lon1 - lon2)
        if diff > 180:
            diff = 360 - diff
        
        # Check for aspects with orbs
        for exact_angle, (name, strength, influence) in self.ASPECTS.items():
            orb = 8 if exact_angle == 0 else 6
            if abs(diff - exact_angle) <= orb:
                return {
                    'aspect': name,
                    'exact_angle': exact_angle,
                    'actual_angle': round(diff, 2),
                    'orb': round(abs(diff - exact_angle), 2),
                    'strength': strength,
                    'influence': influence,
                    'applying': diff < exact_angle
                }
        
        return None
    
    def project_cycles(
        self,
        start_date: datetime = None,
        days_ahead: int = None
    ) -> List[AstroProjection]:
        """
        Project astrological cycles for the specified period.
        
        Args:
            start_date: Starting date for projections
            days_ahead: Number of days to project
            
        Returns:
            List of AstroProjection objects
        """
        if start_date is None:
            start_date = datetime.now()
        if days_ahead is None:
            days_ahead = self.projection_days
        
        projections = []
        planets = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
        
        for day in range(days_ahead):
            current_date = start_date + timedelta(days=day)
            
            # Lunar phase projections
            lunar = self.calculate_lunar_phase(current_date)
            
            if lunar['phase_name'] in ['New Moon', 'Full Moon', 'First Quarter', 'Last Quarter']:
                influence = PlanetaryInfluence.BULLISH if lunar['influence'] == 'bullish' else \
                           PlanetaryInfluence.BEARISH if lunar['influence'] == 'bearish' else \
                           PlanetaryInfluence.NEUTRAL
                
                projections.append(AstroProjection(
                    date=current_date,
                    planet='Moon',
                    aspect=lunar['phase_name'],
                    influence=influence,
                    strength=lunar['strength'],
                    projected_direction='up' if influence == PlanetaryInfluence.BULLISH else 'down',
                    confidence=0.65,
                    description=f"{lunar['phase_name']} - {lunar['illumination']}% illuminated"
                ))
            
            # Planetary aspects
            for i, planet1 in enumerate(planets):
                for planet2 in planets[i+1:]:
                    aspect = self.calculate_aspect(planet1, planet2, current_date)
                    
                    if aspect:
                        if aspect['influence'] == 'bullish':
                            influence = PlanetaryInfluence.BULLISH
                            direction = 'up'
                        elif aspect['influence'] == 'bearish':
                            influence = PlanetaryInfluence.BEARISH
                            direction = 'down'
                        else:
                            influence = PlanetaryInfluence.VOLATILE
                            direction = 'volatile'
                        
                        projections.append(AstroProjection(
                            date=current_date,
                            planet=f"{planet1}-{planet2}",
                            aspect=aspect['aspect'],
                            influence=influence,
                            strength=aspect['strength'],
                            projected_direction=direction,
                            confidence=aspect['strength'] * 0.8,
                            description=f"{planet1} {aspect['aspect']} {planet2} (orb: {aspect['orb']}°)"
                        ))
        
        # Sort by date
        projections.sort(key=lambda x: x.date)
        
        return projections
    
    def get_daily_influence(
        self,
        dt: datetime = None
    ) -> Dict:
        """
        Get overall astrological influence for a specific day.
        
        Returns:
            Dictionary with aggregated influence metrics
        """
        if dt is None:
            dt = datetime.now()
        
        projections = self.project_cycles(dt, 1)
        
        bullish_count = 0
        bearish_count = 0
        volatile_count = 0
        total_strength = 0
        
        events = []
        
        for proj in projections:
            if proj.influence == PlanetaryInfluence.BULLISH:
                bullish_count += 1
            elif proj.influence == PlanetaryInfluence.BEARISH:
                bearish_count += 1
            elif proj.influence == PlanetaryInfluence.VOLATILE:
                volatile_count += 1
            
            total_strength += proj.strength
            events.append({
                'planet': proj.planet,
                'aspect': proj.aspect,
                'influence': proj.influence.value,
                'strength': proj.strength
            })
        
        # Determine overall bias
        if bullish_count > bearish_count:
            overall_bias = 'bullish'
        elif bearish_count > bullish_count:
            overall_bias = 'bearish'
        else:
            overall_bias = 'neutral'
        
        return {
            'date': dt.isoformat(),
            'overall_bias': overall_bias,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'volatile_signals': volatile_count,
            'average_strength': total_strength / len(projections) if projections else 0,
            'events': events,
            'lunar': self.calculate_lunar_phase(dt)
        }
    
    def find_key_dates(
        self,
        start_date: datetime = None,
        days_ahead: int = 90
    ) -> List[Dict]:
        """
        Find dates with significant astrological activity.
        
        Returns:
            List of key dates with high activity
        """
        if start_date is None:
            start_date = datetime.now()
        
        projections = self.project_cycles(start_date, days_ahead)
        
        # Group by date
        date_events = {}
        for proj in projections:
            date_key = proj.date.strftime('%Y-%m-%d')
            if date_key not in date_events:
                date_events[date_key] = []
            date_events[date_key].append(proj)
        
        # Find key dates (2+ events or high strength events)
        key_dates = []
        for date_str, events in date_events.items():
            if len(events) >= 2 or any(e.strength > 0.7 for e in events):
                bullish = sum(1 for e in events if e.influence == PlanetaryInfluence.BULLISH)
                bearish = sum(1 for e in events if e.influence == PlanetaryInfluence.BEARISH)
                
                key_dates.append({
                    'date': date_str,
                    'event_count': len(events),
                    'bullish_count': bullish,
                    'bearish_count': bearish,
                    'net_bias': 'bullish' if bullish > bearish else 'bearish' if bearish > bullish else 'neutral',
                    'max_strength': max(e.strength for e in events),
                    'events': [
                        {
                            'planet': e.planet,
                            'aspect': e.aspect,
                            'influence': e.influence.value
                        }
                        for e in events
                    ]
                })
        
        # Sort by event count and strength
        key_dates.sort(key=lambda x: (-x['event_count'], -x['max_strength']))
        
        return key_dates


# Example usage
if __name__ == "__main__":
    projector = AstroCycleProjector()
    
    print("\n=== Daily Astrological Influence ===")
    daily = projector.get_daily_influence()
    print(f"Date: {daily['date']}")
    print(f"Overall Bias: {daily['overall_bias']}")
    print(f"Lunar Phase: {daily['lunar']['phase_name']}")
    
    print("\n=== Key Dates (Next 30 Days) ===")
    key_dates = projector.find_key_dates(days_ahead=30)
    for kd in key_dates[:5]:
        print(f"{kd['date']}: {kd['event_count']} events, bias: {kd['net_bias']}")
        for event in kd['events']:
            print(f"  - {event['planet']}: {event['aspect']} ({event['influence']})")
