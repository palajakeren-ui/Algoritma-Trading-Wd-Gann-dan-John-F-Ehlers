"""
Gann Square of 24 Module
Based on W.D. Gann's concept of dividing the circle into 24 segments (15 degrees each)
This represents the 24-hour time cycle and market harmonics.
"""
import numpy as np
from loguru import logger
from typing import List, Dict, Optional


class SquareOf24:
    """
    Calculates Gann Square of 24 levels based on a starting price.
    
    The Square of 24 divides the circle into 24 equal parts (15° each).
    This corresponds to Gann's 24-hour cycle and the 15-degree price/time
    movements that Gann considered significant.
    """

    def __init__(self, initial_price: float):
        """
        Initializes the Square of 24 calculator.
        
        Args:
            initial_price (float): The starting price, typically a major pivot high or low.
        """
        if initial_price <= 0:
            raise ValueError("Initial price must be a positive number.")
        self.initial_price = initial_price
        self.segments = 24  # 24 divisions of the circle
        self.degrees_per_segment = 360 / self.segments  # 15 degrees
        logger.info(f"SquareOf24 initialized with starting price: {initial_price}")

    def get_levels(self, n_levels: int = 5) -> Dict[str, List[float]]:
        """
        Calculates support and resistance levels based on Square of 24.
        
        The formula adds/subtracts increments based on 15-degree movements
        in the price-time continuum.
        
        Args:
            n_levels (int): Number of levels to calculate in each direction.
            
        Returns:
            Dict[str, List[float]]: Support and resistance levels.
        """
        if n_levels <= 0:
            raise ValueError("Number of levels must be positive.")
            
        logger.debug(f"Calculating {n_levels} Square of 24 levels...")
        
        sqrt_price = np.sqrt(self.initial_price)
        
        resistance = []
        support = []
        
        # 24 segments means 15 degrees each
        # Full cycle = 24 segments
        for i in range(1, n_levels * self.segments + 1):
            # Calculate the angle in degrees
            angle = i * self.degrees_per_segment
            angle_rad = np.radians(angle)
            
            # Level increment based on 24-segment spiral
            increment = (i / self.segments) * 0.25  # 1/4 cycle per full rotation
            
            # Resistance levels (moving outward)
            res_sqrt = sqrt_price + increment
            res_level = res_sqrt ** 2
            resistance.append(round(res_level, 4))
            
            # Support levels (moving inward)
            sup_sqrt = sqrt_price - increment
            if sup_sqrt > 0:
                sup_level = sup_sqrt ** 2
                support.append(round(sup_level, 4))
        
        # Remove duplicates and sort
        resistance = sorted(list(set(resistance)))
        support = sorted(list(set(support)), reverse=True)
        
        # Filter relevant levels
        resistance = [l for l in resistance if l > self.initial_price]
        support = [l for l in support if l < self.initial_price]
        support = sorted(support)  # Ascending order
        
        logger.success(f"Calculated {len(support)} support and {len(resistance)} resistance levels.")
        
        return {"support": support, "resistance": resistance}
    
    def get_time_harmonics(self, base_time: int = 24) -> List[Dict]:
        """
        Calculate time harmonics based on 24-hour cycle.
        
        Args:
            base_time (int): Base time unit (default 24 hours)
            
        Returns:
            List[Dict]: Time harmonic points
        """
        harmonics = []
        
        # Key harmonic multiples
        multiples = [1, 2, 3, 4, 6, 8, 12, 24, 48, 72, 144, 360]
        
        for mult in multiples:
            time_value = base_time * mult
            harmonics.append({
                "time_value": time_value,
                "multiple": mult,
                "significance": "major" if mult in [1, 6, 12, 24, 144, 360] else "minor",
                "description": f"{mult}x base cycle ({time_value} hours)"
            })
        
        return harmonics
    
    def get_price_angles(self) -> List[Dict]:
        """
        Calculate key price levels at each 15-degree increment.
        
        Returns:
            List[Dict]: Price levels with corresponding angles.
        """
        sqrt_price = np.sqrt(self.initial_price)
        angles = []
        
        for i in range(self.segments + 1):  # 0 to 360 degrees in 15-degree steps
            angle = i * self.degrees_per_segment
            
            # Calculate price at this angle
            if i == 0:
                price = self.initial_price
            else:
                increment = (i / self.segments) * 0.25
                price_sqrt = sqrt_price + increment
                price = price_sqrt ** 2
            
            angles.append({
                "angle": angle,
                "price": round(price, 4),
                "segment": i,
                "cardinal": angle in [0, 90, 180, 270, 360],
                "major": angle % 45 == 0
            })
        
        return angles


def calculate_sq24_levels(initial_price: float, n_levels: int = 5) -> Dict[str, List[float]]:
    """
    Convenience function to calculate Square of 24 levels.
    
    Args:
        initial_price (float): Starting price point.
        n_levels (int): Number of levels to calculate.
        
    Returns:
        Dict[str, List[float]]: Support and resistance levels.
    """
    calculator = SquareOf24(initial_price)
    return calculator.get_levels(n_levels)


if __name__ == "__main__":
    # Test with BTC price
    btc_pivot = 42000.0
    
    sq24 = SquareOf24(initial_price=btc_pivot)
    levels = sq24.get_levels(n_levels=3)
    
    print(f"\nGann Square of 24 Levels around {btc_pivot}")
    print("-" * 50)
    
    print("\nSupport Levels:")
    for level in reversed(levels["support"]):
        print(f"  ${level:,.2f}")
    
    print(f"\n--- Initial Price: ${btc_pivot:,.2f} ---")
    
    print("\nResistance Levels:")
    for level in levels["resistance"]:
        print(f"  ${level:,.2f}")
    
    print("\nPrice Angles (first 10):")
    angles = sq24.get_price_angles()[:10]
    for a in angles:
        cardinal = " [CARDINAL]" if a["cardinal"] else ""
        print(f"  {a['angle']:>3}° = ${a['price']:,.2f}{cardinal}")
    
    print("\nTime Harmonics:")
    harmonics = sq24.get_time_harmonics()
    for h in harmonics[:8]:
        print(f"  {h['description']} ({h['significance']})")
