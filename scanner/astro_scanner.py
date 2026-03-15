"""
Astro Scanner Module
Scans for astrological trading signals
"""
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime, timedelta

try:
    from modules.astro.astro_ephemeris import AstroEphemeris
    from modules.astro.planetary_aspects import PlanetaryAspects
except ImportError:
    AstroEphemeris = None
    PlanetaryAspects = None


class AstroScanner:
    """
    Scanner for astrological signals affecting financial markets.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Astro Scanner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        
        if AstroEphemeris:
            self.ephemeris = AstroEphemeris()
        else:
            self.ephemeris = None
            
        if PlanetaryAspects:
            self.aspects = PlanetaryAspects()
        else:
            self.aspects = None
            
        logger.info("AstroScanner initialized")
    
    def scan_upcoming_events(
        self, 
        days_ahead: int = 30
    ) -> List[Dict]:
        """
        Scan for upcoming astrological events.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming events
        """
        events = []
        today = datetime.now()
        
        for i in range(days_ahead):
            scan_date = today + timedelta(days=i)
            
            # Check planetary aspects
            if self.aspects:
                daily_aspects = self.aspects.get_aspects_for_date(scan_date)
                for aspect in daily_aspects:
                    events.append({
                        'date': scan_date.strftime('%Y-%m-%d'),
                        'type': 'planetary_aspect',
                        'description': aspect.get('description', 'Unknown aspect'),
                        'planets': aspect.get('planets', []),
                        'aspect_type': aspect.get('aspect_type', 'unknown'),
                        'strength': aspect.get('strength', 0.5),
                        'market_impact': self._estimate_market_impact(aspect)
                    })
            
            # Check retrogrades
            retrogrades = self._check_retrogrades(scan_date)
            events.extend(retrogrades)
            
            # Check moon phases
            moon_event = self._check_moon_phase(scan_date)
            if moon_event:
                events.append(moon_event)
        
        logger.info(f"Found {len(events)} upcoming astrological events")
        return events
    
    def analyze_date(self, date: datetime) -> Dict:
        """
        Analyze astrological influences for a specific date.
        
        Args:
            date: Date to analyze
            
        Returns:
            Analysis results
        """
        analysis = {
            'date': date.strftime('%Y-%m-%d'),
            'aspects': [],
            'retrogrades': [],
            'moon_phase': None,
            'overall_score': 0.5,
            'market_bias': 'neutral'
        }
        
        # Get aspects
        if self.aspects:
            aspects = self.aspects.get_aspects_for_date(date)
            analysis['aspects'] = aspects
        
        # Check retrogrades
        analysis['retrogrades'] = self._get_active_retrogrades(date)
        
        # Moon phase
        analysis['moon_phase'] = self._get_moon_phase(date)
        
        # Calculate overall score
        analysis['overall_score'] = self._calculate_astro_score(analysis)
        
        # Determine market bias
        if analysis['overall_score'] > 0.6:
            analysis['market_bias'] = 'bullish'
        elif analysis['overall_score'] < 0.4:
            analysis['market_bias'] = 'bearish'
        else:
            analysis['market_bias'] = 'neutral'
        
        return analysis
    
    def _estimate_market_impact(self, aspect: Dict) -> str:
        """Estimate market impact of an aspect"""
        strength = aspect.get('strength', 0.5)
        aspect_type = aspect.get('aspect_type', '')
        
        # Major aspects have more impact
        major_aspects = ['conjunction', 'opposition', 'square', 'trine', 'sextile']
        
        if strength > 0.8 and aspect_type in major_aspects:
            return 'high'
        elif strength > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _check_retrogrades(self, date: datetime) -> List[Dict]:
        """Check for retrograde events on date"""
        retrogrades = []
        
        # Simplified retrograde schedule (would normally use ephemeris)
        mercury_retrogrades_2024 = [
            ('2024-04-01', '2024-04-25'),
            ('2024-08-04', '2024-08-28'),
            ('2024-11-25', '2024-12-15')
        ]
        
        for start, end in mercury_retrogrades_2024:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
            
            if date.date() == start_date.date():
                retrogrades.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'type': 'retrograde_start',
                    'planet': 'Mercury',
                    'description': 'Mercury retrograde begins',
                    'market_impact': 'high'
                })
            elif date.date() == end_date.date():
                retrogrades.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'type': 'retrograde_end',
                    'planet': 'Mercury',
                    'description': 'Mercury retrograde ends',
                    'market_impact': 'medium'
                })
        
        return retrogrades
    
    def _check_moon_phase(self, date: datetime) -> Optional[Dict]:
        """Check moon phase for date"""
        # Simplified moon phase calculation
        # Would normally use proper astronomical calculation
        day_of_year = date.timetuple().tm_yday
        moon_cycle = (day_of_year % 29.5) / 29.5
        
        if 0 <= moon_cycle < 0.03 or moon_cycle >= 0.97:
            return {
                'date': date.strftime('%Y-%m-%d'),
                'type': 'moon_phase',
                'phase': 'new_moon',
                'description': 'New Moon',
                'market_impact': 'medium'
            }
        elif 0.47 <= moon_cycle < 0.53:
            return {
                'date': date.strftime('%Y-%m-%d'),
                'type': 'moon_phase',
                'phase': 'full_moon',
                'description': 'Full Moon',
                'market_impact': 'medium'
            }
        
        return None
    
    def _get_active_retrogrades(self, date: datetime) -> List[str]:
        """Get list of planets currently in retrograde"""
        retrogrades = []
        # Simplified - would normally check ephemeris
        return retrogrades
    
    def _get_moon_phase(self, date: datetime) -> str:
        """Get moon phase name"""
        day_of_year = date.timetuple().tm_yday
        moon_cycle = (day_of_year % 29.5) / 29.5
        
        if 0 <= moon_cycle < 0.125:
            return 'new_moon'
        elif 0.125 <= moon_cycle < 0.25:
            return 'waxing_crescent'
        elif 0.25 <= moon_cycle < 0.375:
            return 'first_quarter'
        elif 0.375 <= moon_cycle < 0.5:
            return 'waxing_gibbous'
        elif 0.5 <= moon_cycle < 0.625:
            return 'full_moon'
        elif 0.625 <= moon_cycle < 0.75:
            return 'waning_gibbous'
        elif 0.75 <= moon_cycle < 0.875:
            return 'last_quarter'
        else:
            return 'waning_crescent'
    
    def _calculate_astro_score(self, analysis: Dict) -> float:
        """Calculate overall astrological score (0-1)"""
        score = 0.5  # Neutral baseline
        
        # Adjust for retrogrades (negative)
        score -= len(analysis.get('retrogrades', [])) * 0.1
        
        # Adjust for moon phase
        moon = analysis.get('moon_phase', '')
        if moon == 'new_moon':
            score += 0.05
        elif moon == 'full_moon':
            score += 0.1
        
        # Clamp to 0-1
        return max(0, min(1, score))


# Example usage
if __name__ == '__main__':
    scanner = AstroScanner()
    
    # Scan upcoming events
    events = scanner.scan_upcoming_events(days_ahead=14)
    print(f"Found {len(events)} events")
    for event in events[:5]:
        print(event)
    
    # Analyze today
    analysis = scanner.analyze_date(datetime.now())
    print(f"\nToday's analysis: {analysis}")
