"""
Astro Ephemeris Module
Handles loading ephemeris data and calculating planetary positions.
Uses the skyfield library for high-precision astronomical calculations.

Note: skyfield is an optional dependency. If not installed, this module
will provide stub implementations that return empty results.
"""
from loguru import logger
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

# Try to import skyfield - this is an optional dependency
SKYFIELD_AVAILABLE = False
try:
    from skyfield.api import load, Topos
    from skyfield.framelib import ecliptic_frame
    SKYFIELD_AVAILABLE = True
except ImportError:
    load = None
    Topos = None
    ecliptic_frame = None
    logger.warning("skyfield not installed. Astro features will be disabled. Install with: pip install skyfield")


class AstroEphemeris:
    """
    Handles loading ephemeris data and calculating planetary positions.
    Uses the skyfield library for high-precision astronomical calculations.
    
    If skyfield is not installed, this class will operate in stub mode
    returning empty results.
    """
    
    def __init__(self, ephemeris_path: str = "data/ephemeris/de440.bsp"):
        """
        Initializes the ephemeris loader.
        Downloads the required JPL ephemeris file if not present.

        Args:
            ephemeris_path (str): The local path to store the ephemeris file.
        """
        self.eph = None
        self.sun = None
        self.moon = None
        self.earth = None
        self.timescale = None
        self.celestial_bodies = {}
        
        if not SKYFIELD_AVAILABLE:
            logger.warning("AstroEphemeris: skyfield not available, operating in stub mode")
            return
            
        try:
            self.planets = load(ephemeris_path)
            self.eph = self.planets
            self.sun = self.eph['sun']
            self.moon = self.eph['moon']
            self.earth = self.eph['earth']
            self.timescale = load.timescale()

            # Define the celestial bodies we'll be working with
            self.celestial_bodies = {
                'sun': self.sun,
                'moon': self.moon,
                'mercury': self.eph['mercury barycenter'],
                'venus': self.eph['venus barycenter'],
                'mars': self.eph['mars barycenter'],
                'jupiter': self.eph['jupiter barycenter'],
                'saturn': self.eph['saturn barycenter'],
                'uranus': self.eph['uranus barycenter'],
                'neptune': self.eph['neptune barycenter'],
            }
            logger.success("AstroEphemeris initialized and ephemeris data loaded.")

        except Exception as e:
            logger.error(f"Failed to load ephemeris data. Error: {e}")
            self.eph = None

    def get_positions_for_dates(self, dates: pd.DatetimeIndex, bodies: List[str]) -> Dict[str, pd.Series]:
        """
        Calculates the ecliptic longitude for multiple celestial bodies over a range of dates.

        Args:
            dates (pd.DatetimeIndex): The dates for which to calculate positions.
            bodies (List[str]): A list of celestial body names (e.g., ['sun', 'jupiter']).

        Returns:
            Dict[str, pd.Series]: A dictionary where keys are body names and values are Series
                                  of their ecliptic longitudes indexed by date.
        """
        if not SKYFIELD_AVAILABLE or self.eph is None:
            logger.warning("Ephemeris data not available, returning empty positions")
            # Return empty series for each requested body
            return {body.lower(): pd.Series(np.nan, index=dates, name=f"{body.lower()}_lon") 
                    for body in bodies}

        t = self.timescale.from_datetime(dates.to_pydatetime())
        positions = {}

        for body_name in bodies:
            body_name = body_name.lower()
            if body_name not in self.celestial_bodies:
                logger.warning(f"Celestial body '{body_name}' not recognized.")
                continue

            # Calculate apparent position from Earth
            astrometric = self.earth.at(t).observe(self.celestial_bodies[body_name])
            ecliptic_pos = astrometric.frame_latlon(ecliptic_frame=ecliptic_frame)

            # The longitude is the first element of the tuple
            longitudes = ecliptic_pos[0].degrees
            positions[body_name] = pd.Series(longitudes, index=dates, name=f"{body_name}_lon")
            logger.debug(f"Calculated positions for {body_name}.")

        return positions
    
    def is_available(self) -> bool:
        """Check if skyfield and ephemeris data are available."""
        return SKYFIELD_AVAILABLE and self.eph is not None


# Example Usage
if __name__ == "__main__":
    # Create a date range for testing
    test_dates = pd.to_datetime(pd.date_range(start="2023-01-01", end="2023-01-10", freq="D"))

    # List of planets we are interested in
    planets_to_track = ["Sun", "Jupiter", "Saturn"]

    # Initialize the ephemeris service
    ephemeris = AstroEphemeris()

    # Get their positions
    planetary_positions = ephemeris.get_positions_for_dates(test_dates, planets_to_track)

    if planetary_positions:
        # Combine into a single DataFrame for display
        positions_df = pd.DataFrame(planetary_positions)

        print("--- Planetary Positions (Ecliptic Longitude) ---")
        print(positions_df)
        print("------------------------------------------------")
