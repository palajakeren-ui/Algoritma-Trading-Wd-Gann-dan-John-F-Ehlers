"""
Astro View Module
Interface for Astrological charts and cycles
"""
from loguru import logger

class AstroView:
    """View for Astro Cycles."""
    def __init__(self):
        logger.info("GUI: AstroView initialized")
        
    def plot_aspects(self, aspects):
        print("Plotting planetary aspects...")
