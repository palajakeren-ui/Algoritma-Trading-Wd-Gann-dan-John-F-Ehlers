from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame
from loguru import logger
from typing import Dict, List
import pandas as pd

class AstroEphemeris:
    """
    Handles loading ephemeris data and calculating planetary positions.
    Uses the skyfield library for high-precision astronomical calculations.
    """
    def __init__(self, ephemeris_path: str = "data/ephemeris/de440.bsp"):
        """
        Initializes the ephemeris loader.
        Downloads the required JPL ephemeris file if not present.

        Args:
            ephemeris_path (str): The local path to store the ephemeris file.
        """
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
            logger.error(f"Failed to load ephemeris data. Please ensure '{ephemeris_path}' is accessible. Error: {e}")
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
        if self.eph is None:
            logger.error("Ephemeris data not loaded, cannot calculate positions.")
            return {}

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
