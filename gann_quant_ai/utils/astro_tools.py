"""
Astro Tools Module
Astronomical calculation utilities
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger


# Planetary orbital periods in days
ORBITAL_PERIODS = {
    'Mercury': 87.969,
    'Venus': 224.701,
    'Earth': 365.256,
    'Mars': 686.980,
    'Jupiter': 4332.59,
    'Saturn': 10759.22,
    'Uranus': 30688.5,
    'Neptune': 60182,
    'Pluto': 90560,
    'Moon': 27.322  # Sidereal month
}

# Synodic periods (relative to Earth)
SYNODIC_PERIODS = {
    'Mercury': 115.88,
    'Venus': 583.92,
    'Mars': 779.94,
    'Jupiter': 398.88,
    'Saturn': 378.09
}


def calculate_julian_date(dt: datetime) -> float:
    """Calculate Julian Date from datetime"""
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    
    jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd += (dt.hour - 12) / 24 + dt.minute / 1440 + dt.second / 86400
    
    return jd


def julian_to_datetime(jd: float) -> datetime:
    """Convert Julian Date to datetime"""
    z = int(jd + 0.5)
    f = jd + 0.5 - z
    
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    
    day = b - d - int(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    
    hours = (day % 1) * 24
    minutes = (hours % 1) * 60
    seconds = (minutes % 1) * 60
    
    return datetime(int(year), int(month), int(day), int(hours), int(minutes), int(seconds))


def calculate_moon_phase(dt: datetime) -> Dict:
    """Calculate moon phase for date"""
    # Simplified calculation
    # Reference new moon: January 6, 2000
    reference = datetime(2000, 1, 6, 18, 14)
    days_since = (dt - reference).total_seconds() / 86400
    
    lunation = days_since / 29.53059
    phase = lunation % 1
    
    # Determine phase name
    if phase < 0.0625:
        name = 'New Moon'
    elif phase < 0.1875:
        name = 'Waxing Crescent'
    elif phase < 0.3125:
        name = 'First Quarter'
    elif phase < 0.4375:
        name = 'Waxing Gibbous'
    elif phase < 0.5625:
        name = 'Full Moon'
    elif phase < 0.6875:
        name = 'Waning Gibbous'
    elif phase < 0.8125:
        name = 'Last Quarter'
    elif phase < 0.9375:
        name = 'Waning Crescent'
    else:
        name = 'New Moon'
    
    return {
        'phase': round(phase, 4),
        'phase_name': name,
        'illumination': round(abs(np.cos(phase * 2 * np.pi)) * 100, 1),
        'lunation_number': int(lunation)
    }


def get_planet_longitude(planet: str, dt: datetime) -> float:
    """Get approximate heliocentric longitude for planet"""
    # Simplified mean anomaly calculation
    jd = calculate_julian_date(dt)
    d = jd - 2451545.0  # Days from J2000.0
    
    period = ORBITAL_PERIODS.get(planet, 365.256)
    
    # Mean longitude (very approximate)
    mean_longitude = (d / period * 360) % 360
    
    return mean_longitude


def calculate_aspect(lon1: float, lon2: float) -> Dict:
    """Calculate aspect between two longitudes"""
    diff = abs(lon1 - lon2)
    if diff > 180:
        diff = 360 - diff
    
    aspects = [
        (0, 'conjunction', 10),
        (60, 'sextile', 6),
        (90, 'square', 8),
        (120, 'trine', 8),
        (180, 'opposition', 10)
    ]
    
    for exact, name, orb in aspects:
        if abs(diff - exact) <= orb:
            return {
                'aspect': name,
                'exact_angle': exact,
                'actual_angle': round(diff, 2),
                'orb': round(abs(diff - exact), 2),
                'applying': diff < exact
            }
    
    return {'aspect': None, 'actual_angle': round(diff, 2)}


def get_planetary_hours(dt: datetime, latitude: float = 0) -> Dict:
    """Calculate planetary hour for time"""
    # Simplified - actual calculation needs sunrise/sunset
    day_of_week = dt.weekday()
    hour = dt.hour
    
    # Chaldean order
    planets = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
    day_rulers = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
    
    day_ruler = day_rulers[day_of_week]
    ruler_idx = planets.index(day_ruler)
    
    # Each planetary hour ruler
    hour_ruler_idx = (ruler_idx + hour) % 7
    hour_ruler = planets[hour_ruler_idx]
    
    return {
        'day_ruler': day_ruler,
        'hour_ruler': hour_ruler,
        'planetary_hour': hour % 12 + 1,
        'is_day_hour': 6 <= hour < 18
    }


def next_lunar_event(dt: datetime, event: str = 'new_moon') -> datetime:
    """Find next lunar event after date"""
    current = dt
    synodic_month = 29.53059
    
    # Get current phase
    phase_info = calculate_moon_phase(current)
    current_phase = phase_info['phase']
    
    # Target phases
    targets = {
        'new_moon': 0,
        'first_quarter': 0.25,
        'full_moon': 0.5,
        'last_quarter': 0.75
    }
    
    target = targets.get(event, 0)
    
    # Calculate days to target
    if current_phase < target:
        days = (target - current_phase) * synodic_month
    else:
        days = (1 - current_phase + target) * synodic_month
    
    return current + timedelta(days=days)


def get_zodiac_sign(longitude: float) -> Dict:
    """Get zodiac sign from ecliptic longitude"""
    signs = [
        'Aries', 'Taurus', 'Gemini', 'Cancer',
        'Leo', 'Virgo', 'Libra', 'Scorpio',
        'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]
    
    sign_num = int(longitude // 30)
    degree_in_sign = longitude % 30
    
    return {
        'sign': signs[sign_num],
        'degree': round(degree_in_sign, 2),
        'longitude': round(longitude, 2)
    }
