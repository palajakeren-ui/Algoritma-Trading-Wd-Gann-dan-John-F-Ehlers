import numpy as np
from loguru import logger
from typing import List, Tuple, Dict

class SquareOf9:
    """
    Calculates Gann Square of 9 levels based on a starting price.

    The Square of 9 is a spiral of numbers. The important support and
    resistance levels are found on the "cardinal cross" and "ordinal cross"
    of this spiral. This class calculates those levels mathematically
    without generating the full visual spiral.
    """

    def __init__(self, initial_price: float):
        """
        Initializes the Square of 9 calculator.

        Args:
            initial_price (float): The starting price, typically a major pivot high or low.
        """
        if initial_price <= 0:
            raise ValueError("Initial price must be a positive number.")
        self.initial_price = initial_price
        logger.info(f"SquareOf9 initialized with starting price: {initial_price}")

    def get_levels(self, n_levels: int = 5) -> Dict[str, List[float]]:
        """
        Calculates the major support and resistance levels on the crosses.
        This is a more direct mathematical approach.

        Args:
            n_levels (int): The number of concentric rings/levels to calculate outwards and inwards.

        Returns:
            Dict[str, List[float]]: A dictionary containing lists of "support" and "resistance" levels.
        """
        if n_levels <= 0:
            raise ValueError("Number of levels must be positive.")

        logger.debug(f"Calculating {n_levels} Square of 9 levels...")

        # Find the base square root for the initial price
        sqrt_price = np.sqrt(self.initial_price)

        levels = set()

        # Generate levels by rotating around the center
        for i in range(1, n_levels * 8 + 1):
            # Calculate levels moving outwards (resistance)
            angle_rad = (i * 45) * (np.pi / 180) # 45 degrees per step
            level_sqrt_res = sqrt_price + (i / 4.0) # Move out in 0.25 cycle steps
            resistance_level = level_sqrt_res**2
            levels.add(resistance_level)

            # Calculate levels moving inwards (support)
            level_sqrt_sup = sqrt_price - (i / 4.0)
            if level_sqrt_sup > 0:
                support_level = level_sqrt_sup**2
                levels.add(support_level)

        # Remove duplicates, sort, and filter out non-positive values
        unique_levels = sorted(list(levels))

        # Separate into support and resistance
        resistance = [level for level in unique_levels if level > self.initial_price]
        support = [level for level in unique_levels if level < self.initial_price]

        logger.success(f"Calculated {len(support)} support and {len(resistance)} resistance levels.")

        return {"support": support, "resistance": resistance}


# Example Usage:
if __name__ == "__main__":
    # Let's assume a major pivot low for BTC was at 15500
    btc_pivot = 15500.0

    sq9_calculator = SquareOf9(initial_price=btc_pivot)

    # Get 3 rings of levels around the pivot
    gann_levels = sq9_calculator.get_levels(n_levels=3)

    print(f"Gann Square of 9 Levels around {btc_pivot}")
    print("-" * 40)

    print("\nSupport Levels (descending):")
    # Print support levels from highest to lowest
    for level in reversed(gann_levels["support"]):
        print(f"{level:.2f}")

    print(f"\n--- Initial Price: {btc_pivot:.2f} ---")

    print("\nResistance Levels (ascending):")
    for level in gann_levels["resistance"]:
        print(f"{level:.2f}")

    print("-" * 40)

    # Example for a lower priced stock, e.g., AMD pivot at $55
    amd_pivot = 55.0
    sq9_calculator_amd = SquareOf9(initial_price=amd_pivot)
    gann_levels_amd = sq9_calculator_amd.get_levels(n_levels=5)

    print(f"\nGann Square of 9 Levels around {amd_pivot}")
    print("-" * 40)
    print("Support:", [f"{lvl:.2f}" for lvl in reversed(gann_levels_amd["support"])])
    print("Resistance:", [f"{lvl:.2f}" for lvl in gann_levels_amd["resistance"]])
