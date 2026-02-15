import pandas as pd
import numpy as np

def cyber_cycle(data: pd.DataFrame, alpha: float = 0.07) -> pd.DataFrame:
    """
    Calculates the Ehlers Cyber Cycle Indicator.

    This is a cycle oscillator that can help identify turning points in the market.
    It is often smoothed with a 2-bar EMA to create a trigger line.

    Args:
        data (pd.DataFrame): DataFrame with 'close' prices.
        alpha (float): The alpha smoothing parameter for the cycle calculation.

    Returns:
        pd.DataFrame: A DataFrame with 'cycle' and 'cycle_trigger' columns.
    """
    close = data['close']

    # Using an iterative approach to correctly calculate the cycle
    cycle_series = pd.Series(index=close.index, dtype=float)

    cycle_val = 0.0
    for i in range(len(close)):
        if i < 2:
            cycle_val = (close[i] - 2 * close[i-1] + close[i-2]) / 4.0 if i > 1 else 0.0
        else:
            prev1_cycle = cycle_series.iloc[i-1] if pd.notna(cycle_series.iloc[i-1]) else 0.0
            prev2_cycle = cycle_series.iloc[i-2] if pd.notna(cycle_series.iloc[i-2]) else 0.0

            term1 = (1 - 0.5 * alpha)**2 * (close[i] - 2 * close[i-1] + close[i-2])
            term2 = 2 * (1 - alpha) * prev1_cycle
            term3 = (1 - alpha)**2 * prev2_cycle
            cycle_val = term1 + term2 - term3

        cycle_series.iloc[i] = cycle_val

    # Create a 2-bar EMA trigger line
    cycle_trigger = cycle_series.ewm(span=2, adjust=False).mean()

    return pd.DataFrame({'cycle': cycle_series, 'cycle_trigger': cycle_trigger}, index=data.index)
