"""
Astro Module
Astrological analysis tools for financial markets

Note: skyfield is an optional dependency for astronomical calculations.
If not installed, astro features will be disabled but core trading still works.
"""

# Check if skyfield is available first
SKYFIELD_AVAILABLE = False
try:
    import skyfield
    SKYFIELD_AVAILABLE = True
except ImportError:
    pass

# Only import astro modules if skyfield is available
if SKYFIELD_AVAILABLE:
    try:
        from .astro_ephemeris import AstroEphemeris
        from .planetary_aspects import find_planetary_aspects
        from .retrograde_cycles import RetrogradeCycles
        from .zodiac_degrees import ZodiacDegrees
        from .synodic_cycles import SynodicCycleCalculator, calculate_synodic_cycles
        from .time_harmonics import TimeHarmonicsCalculator, calculate_time_harmonics
        
        __all__ = [
            'AstroEphemeris',
            'find_planetary_aspects',
            'RetrogradeCycles',
            'ZodiacDegrees',
            'SynodicCycleCalculator',
            'calculate_synodic_cycles',
            'TimeHarmonicsCalculator',
            'calculate_time_harmonics',
            'SKYFIELD_AVAILABLE',
        ]
    except ImportError as e:
        SKYFIELD_AVAILABLE = False

# Always define these, even if skyfield is not available
if not SKYFIELD_AVAILABLE:
    # Provide None stubs for when skyfield is not available
    AstroEphemeris = None
    find_planetary_aspects = None
    RetrogradeCycles = None
    ZodiacDegrees = None
    SynodicCycleCalculator = None
    calculate_synodic_cycles = None
    TimeHarmonicsCalculator = None
    calculate_time_harmonics = None
    
    __all__ = [
        'AstroEphemeris',
        'find_planetary_aspects', 
        'RetrogradeCycles',
        'ZodiacDegrees',
        'SynodicCycleCalculator',
        'calculate_synodic_cycles',
        'TimeHarmonicsCalculator',
        'calculate_time_harmonics',
        'SKYFIELD_AVAILABLE',
    ]
