from loguru import logger
import pandas as pd
from typing import Dict, List, Optional

from modules.astro.astro_ephemeris import AstroEphemeris
from modules.astro.planetary_aspects import find_planetary_aspects

class AstroEngine:
    """
    The main engine for performing all astro-based analysis.
    It identifies key astrological events like aspects and retrogrades
    that may correlate with market turning points.
    """
    def __init__(self, astro_config: Dict):
        """
        Initializes the AstroEngine.

        Args:
            astro_config (Dict): A dictionary containing astro-related settings.
        """
        self.config = astro_config
        # Use de440.bsp as it's a more modern and available ephemeris file
        ephemeris_path = self.config.get("ephemeris", {}).get("data_path", "data/ephemeris/") + "de440.bsp"
        self.ephemeris = AstroEphemeris(ephemeris_path=ephemeris_path)
        logger.info("AstroEngine initialized.")

    def analyze_dates(self, dates: pd.DatetimeIndex) -> Optional[pd.DataFrame]:
        """
        Analyzes a range of dates to find all configured astrological events.

        Args:
            dates (pd.DatetimeIndex): The dates to analyze.

        Returns:
            Optional[pd.DataFrame]: A DataFrame of astro events, indexed by date,
                                     or None if analysis fails.
        """
        if self.ephemeris.eph is None:
            logger.error("Cannot perform astro analysis because ephemeris data is not loaded.")
            return None

        logger.info(f"Performing astro analysis for date range: {dates.min().date()} to {dates.max().date()}")

        # --- 1. Identify Planetary Aspects ---
        aspects_to_check = self.config.get("planetary_aspects", [])

        # Determine the unique set of planets we need to calculate positions for
        planets_needed = set()
        for aspect in aspects_to_check:
            for planet in aspect.get("planets", []):
                planets_needed.add(planet)

        if not planets_needed:
            logger.warning("No planets configured for aspect analysis.")
            return pd.DataFrame()

        # Get positions for the required planets
        positions = self.ephemeris.get_positions_for_dates(dates, list(planets_needed))

        if not positions:
            logger.warning("Could not retrieve planetary positions.")
            return pd.DataFrame()

        # Find the aspect events
        aspect_events_df = find_planetary_aspects(positions, aspects_to_check)

        if aspect_events_df.empty:
            return pd.DataFrame()

        # Set the date as the index for easy merging/lookup later
        aspect_events_df.set_index('date', inplace=True)

        # --- 2. Retrograde Analysis ---
        retrograde_planets = self.config.get("retrograde_monitoring", {}).get("planets", [])
        if retrograde_planets and positions:
            try:
                retro_records = []
                for date_i in range(1, len(dates)):
                    d_now = dates[date_i]
                    d_prev = dates[date_i - 1]
                    for planet in retrograde_planets:
                        if planet in positions and d_now in positions[planet] and d_prev in positions[planet]:
                            # A negative change in ecliptic longitude = retrograde
                            lon_now = positions[planet][d_now]
                            lon_prev = positions[planet][d_prev]
                            delta = lon_now - lon_prev
                            # Handle wrap-around (360 -> 0)
                            if delta > 180:
                                delta -= 360
                            elif delta < -180:
                                delta += 360
                            if delta < 0:
                                retro_records.append({'date': d_now, 'planet': planet, 'type': 'retrograde'})
                if retro_records:
                    retro_df = pd.DataFrame(retro_records)
                    retro_df.set_index('date', inplace=True)
                    if aspect_events_df.empty:
                        aspect_events_df = retro_df
                    else:
                        aspect_events_df = pd.concat([aspect_events_df, retro_df])
                    logger.info(f"Retrograde analysis found {len(retro_records)} retrograde-day events.")
            except Exception as e:
                logger.warning(f"Retrograde analysis encountered an error: {e}")

        return aspect_events_df

# Example Usage
if __name__ == '__main__':
    # 1. Load mock configuration
    mock_astro_config = {
        "ephemeris": {
            "data_path": "data/ephemeris/"
        },
        "planetary_aspects": [
            {"planets": ["Jupiter", "Saturn"], "aspect": 0, "tolerance_degrees": 5.0},
            {"planets": ["Mars", "Venus"], "aspect": 120, "tolerance_degrees": 3.0},
        ]
    }

    # 2. Create a date range from a mock price DataFrame
    dates_to_analyze = pd.to_datetime(pd.date_range("2020-12-15", "2020-12-25", freq="D"))

    # 3. Initialize and run the engine
    astro_engine = AstroEngine(astro_config=mock_astro_config)
    astro_events = astro_engine.analyze_dates(dates_to_analyze)

    if astro_events is not None:
        print("\n--- Astro Engine Analysis Results ---")
        if astro_events.empty:
            print("No significant astro events found in the specified date range.")
        else:
            print(astro_events)
        print("-----------------------------------")
