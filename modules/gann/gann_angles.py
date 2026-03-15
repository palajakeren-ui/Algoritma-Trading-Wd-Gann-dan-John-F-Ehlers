import pandas as pd
from typing import Dict, List, Optional

def calculate_gann_angles(
    price_data: pd.DataFrame,
    pivot_point: Dict, # e.g., {'date': '2023-01-10', 'price': 150.0, 'type': 'low'}
    time_units_per_price_unit: float = 1.0,
    angles: List[str] = ["1x1", "1x2", "2x1"]
) -> pd.DataFrame:
    """
    Calculates the price levels for Gann Angles originating from a pivot point.

    Args:
        price_data (pd.DataFrame): The price data (used for the index/dates).
        pivot_point (Dict): A dictionary defining the anchor point for the angles.
        time_units_per_price_unit (float): The scaling factor for the 1x1 angle.
        angles (List[str]): A list of angle ratios to calculate (e.g., "1x1", "2x1").

    Returns:
        pd.DataFrame: A DataFrame with columns for each calculated Gann Angle.
    """
    pivot_date = pd.to_datetime(pivot_point['date'])
    pivot_price = pivot_point['price']
    pivot_type = pivot_point['type']

    # Filter data to start from the pivot date
    relevant_data = price_data[price_data.index >= pivot_date]

    # Calculate time delta in days from the pivot
    time_delta = (relevant_data.index - pivot_date).days

    angle_df = pd.DataFrame(index=relevant_data.index)

    angle_map = {
        "1x1": 1.0, "1x2": 2.0, "2x1": 0.5, "1x4": 4.0, "4x1": 0.25,
        "1x8": 8.0, "8x1": 0.125
    }

    for angle_str in angles:
        if angle_str in angle_map:
            ratio = angle_map[angle_str]
            price_change_per_day = ratio / time_units_per_price_unit

            if pivot_type == 'low': # Angles go up from a low
                angle_prices = pivot_price + (time_delta * price_change_per_day)
            else: # 'high', angles go down from a high
                angle_prices = pivot_price - (time_delta * price_change_per_day)

            angle_df[f'angle_{angle_str}'] = angle_prices

    return angle_df
