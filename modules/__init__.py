"""
Modules Package - Gann Quant AI
Contains specialized analysis modules for trading
"""
from . import gann
from . import ehlers
from . import forecasting
from . import ml
from . import options
from . import smith

# Astro module is optional (requires skyfield)
try:
    from . import astro
    ASTRO_AVAILABLE = True
except ImportError:
    astro = None
    ASTRO_AVAILABLE = False

__all__ = [
    'gann',
    'astro',
    'ehlers',
    'forecasting',
    'ml',
    'options',
    'smith',
    'ASTRO_AVAILABLE',
]

__version__ = '2.0.0'
