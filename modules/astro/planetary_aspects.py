import pandas as pd
from loguru import logger
from typing import Dict, List, Tuple

def find_planetary_aspects(
    planetary_positions: Dict[str, pd.Series],
    aspects_to_check: List[Dict]
) -> pd.DataFrame:
    """
    Identifies dates where specific planetary aspects occur.

    Args:
        planetary_positions (Dict[str, pd.Series]): A dictionary of planetary longitudes.
        aspects_to_check (List[Dict]): A list of dictionaries from the astro_config,
                                       specifying the planets, aspect angle, and tolerance.

    Returns:
        pd.DataFrame: A DataFrame listing the dates and details of any detected aspects.
    """
    if not planetary_positions:
        logger.warning("Planetary positions are empty. Cannot check for aspects.")
        return pd.DataFrame()

    all_aspect_events = []

    # Combine positions into a single DataFrame for easier calculations
    positions_df = pd.DataFrame(planetary_positions)

    for aspect_info in aspects_to_check:
        planets = aspect_info.get("planets", [])
        target_aspect = aspect_info.get("aspect", 0)
        tolerance = aspect_info.get("tolerance_degrees", 1.0)

        if len(planets) != 2:
            logger.warning(f"Aspect check requires exactly 2 planets, but got {planets}. Skipping.")
            continue

        p1_name, p2_name = planets[0].lower(), planets[1].lower()

        if f"{p1_name}_lon" not in positions_df.columns or f"{p2_name}_lon" not in positions_df.columns:
            logger.warning(f"Missing position data for {p1_name} or {p2_name}. Skipping aspect check.")
            continue

        # Calculate the angular separation between the two planets
        angle_diff = abs(positions_df[f"{p1_name}_lon"] - positions_df[f"{p2_name}_lon"])
        # Handle the 360-degree wrap-around
        angle_diff = angle_diff.apply(lambda x: x if x <= 180 else 360 - x)

        # Find dates where the angle is within the tolerance of the target aspect
        aspect_dates = positions_df[abs(angle_diff - target_aspect) <= tolerance]

        for date, row in aspect_dates.iterrows():
            actual_diff = angle_diff.loc[date]
            all_aspect_events.append({
                "date": date,
                "aspect_type": f"{target_aspect}° ({_get_aspect_name(target_aspect)})",
                "planets": f"{p1_name.capitalize()} - {p2_name.capitalize()}",
                "angle_degrees": actual_diff
            })
            logger.info(f"Detected {p1_name}-{p2_name} aspect on {date.date()}.")

    if not all_aspect_events:
        logger.info("No significant planetary aspects found in the given date range.")
        return pd.DataFrame()

    return pd.DataFrame(all_aspect_events).sort_values(by="date").reset_index(drop=True)

def _get_aspect_name(angle: int) -> str:
    """Returns the common name for a given aspect angle."""
    names = {
        0: "Conjunction",
        60: "Sextile",
        90: "Square",
        120: "Trine",
        180: "Opposition",
    }
    return names.get(angle, f"Aspect {angle}")

# Example Usage
if __name__ == "__main__":
    from modules.astro.astro_ephemeris import AstroEphemeris

    # 1. Define aspects we want to look for (similar to astro_config.yaml)
    mock_aspect_config = [
        {"planets": ["Jupiter", "Saturn"], "aspect": 0, "tolerance_degrees": 5.0},
        {"planets": ["Mars", "Venus"], "aspect": 120, "tolerance_degrees": 3.0},
        {"planets": ["Sun", "Moon"], "aspect": 180, "tolerance_degrees": 8.0} # This one is very frequent
    ]

    # 2. Get ephemeris data for a longer period to find aspects
    ephemeris = AstroEphemeris()
    date_range = pd.to_datetime(pd.date_range(start="2020-01-01", end="2021-01-01", freq="D"))
    planets_needed = ["Sun", "Moon", "Mars", "Venus", "Jupiter", "Saturn"]

    positions = ephemeris.get_positions_for_dates(date_range, planets_needed)

    # 3. Find the aspects
    if positions:
        aspect_events = find_planetary_aspects(positions, mock_aspect_config)

        print("\n--- Detected Planetary Aspects ---")
        print(aspect_events)
        print("----------------------------------")

        # Example: The Great Conjunction of Jupiter and Saturn in late 2020
        great_conjunction = aspect_events[
            (aspect_events['planets'] == 'Jupiter - Saturn') &
            (aspect_events['aspect_type'] == "0° (Conjunction)")
        ]
        print("\nHighlight: The Great Conjunction")
        print(great_conjunction)
