"""
Gann Time-Price Geometry Module
Implements W.D. Gann's geometric relationships between time and price.
Includes all angle ratios from 1x16 (steepest) to 16x1 (flattest)
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class GannAngle:
    """Represents a Gann angle line."""
    name: str
    ratio: Tuple[int, int]  # (time units, price units)
    slope: float
    significance: str  # 'major', 'minor'


class TimePriceGeometry:
    """
    Implements Gann's Time-Price Geometry.
    
    Gann believed in the natural relationship between time and price, where
    specific angles represent equilibrium and strength/weakness in the market.
    """
    
    # All Gann angles from steepest (1x16) to flattest (16x1)
    GANN_ANGLES = {
        # Steepest angles (price moves faster than time)
        "1x16": (1, 16),   # 1 time unit, 16 price units
        "1x8": (1, 8),     # 1 time unit, 8 price units
        "1x4": (1, 4),     # 1 time unit, 4 price units
        "1x3": (1, 3),     # 1 time unit, 3 price units
        "1x2": (1, 2),     # 1 time unit, 2 price units (63.75°)
        
        # Perfect balance
        "1x1": (1, 1),     # 45° - The most important angle
        
        # Flattest angles (time moves faster than price)
        "2x1": (2, 1),     # 2 time units, 1 price unit (26.25°)
        "3x1": (3, 1),     # 3 time units, 1 price unit
        "4x1": (4, 1),     # 4 time units, 1 price unit
        "8x1": (8, 1),     # 8 time units, 1 price unit
        "16x1": (16, 1),   # 16 time units, 1 price unit
    }
    
    MAJOR_ANGLES = ["1x8", "1x4", "1x2", "1x1", "2x1", "4x1", "8x1"]
    
    def __init__(self, time_unit: float = 1.0, price_unit: float = 1.0):
        """
        Initialize Time-Price Geometry calculator.
        
        Args:
            time_unit (float): Value of one time unit (e.g., 1 day)
            price_unit (float): Value of one price unit (e.g., $1)
        """
        self.time_unit = time_unit
        self.price_unit = price_unit
        self.angles = self._build_angles()
        logger.info(f"TimePriceGeometry initialized with time_unit={time_unit}, price_unit={price_unit}")
    
    def _build_angles(self) -> Dict[str, GannAngle]:
        """Build GannAngle objects for all defined angles."""
        angles = {}
        for name, (t, p) in self.GANN_ANGLES.items():
            slope = (p * self.price_unit) / (t * self.time_unit)
            significance = "major" if name in self.MAJOR_ANGLES else "minor"
            angles[name] = GannAngle(
                name=name,
                ratio=(t, p),
                slope=slope,
                significance=significance
            )
        return angles
    
    def calculate_angle_lines(
        self, 
        pivot_price: float,
        pivot_time: int,
        bars_forward: int = 100,
        direction: str = "both"
    ) -> pd.DataFrame:
        """
        Calculate all Gann angle lines from a pivot point.
        
        Args:
            pivot_price (float): Price at the pivot point
            pivot_time (int): Bar index at the pivot point
            bars_forward (int): Number of bars to project forward
            direction (str): "up", "down", or "both"
            
        Returns:
            pd.DataFrame: DataFrame with angle lines
        """
        results = []
        
        for bar in range(bars_forward + 1):
            time_offset = bar * self.time_unit
            row = {"bar": pivot_time + bar, "time_offset": time_offset}
            
            for name, angle in self.angles.items():
                price_offset = angle.slope * time_offset
                
                if direction in ["up", "both"]:
                    row[f"{name}_up"] = pivot_price + price_offset
                if direction in ["down", "both"]:
                    row[f"{name}_down"] = pivot_price - price_offset
            
            results.append(row)
        
        return pd.DataFrame(results)
    
    def find_support_resistance(
        self,
        current_price: float,
        pivot_price: float,
        pivot_time: int,
        current_time: int
    ) -> Dict[str, List[Dict]]:
        """
        Find support and resistance levels based on Gann angles.
        
        Args:
            current_price (float): Current price
            pivot_price (float): Price at pivot
            pivot_time (int): Time at pivot
            current_time (int): Current time
            
        Returns:
            Dict with support and resistance levels
        """
        time_offset = (current_time - pivot_time) * self.time_unit
        
        support = []
        resistance = []
        
        for name, angle in self.angles.items():
            price_offset = angle.slope * time_offset
            
            # Up angle from low pivot
            up_level = pivot_price + price_offset
            # Down angle from high pivot
            down_level = pivot_price - price_offset
            
            level_info = {
                "angle": name,
                "ratio": angle.ratio,
                "significance": angle.significance,
                "price": up_level,
                "slope": angle.slope
            }
            
            if up_level < current_price:
                support.append({**level_info, "price": up_level, "type": "angle_up"})
            elif up_level > current_price:
                resistance.append({**level_info, "price": up_level, "type": "angle_up"})
            
            if down_level > 0:
                if down_level < current_price:
                    support.append({**level_info, "price": down_level, "type": "angle_down"})
                elif down_level > current_price:
                    resistance.append({**level_info, "price": down_level, "type": "angle_down"})
        
        # Sort by distance from current price
        support = sorted(support, key=lambda x: current_price - x["price"])
        resistance = sorted(resistance, key=lambda x: x["price"] - current_price)
        
        return {"support": support, "resistance": resistance}
    
    def calculate_time_targets(
        self,
        pivot_date: datetime,
        n_cycles: int = 10
    ) -> List[Dict]:
        """
        Calculate time targets based on Gann cycles.
        
        Key Gann time cycles: 7, 30, 45, 60, 90, 120, 144, 180, 270, 360 days
        
        Args:
            pivot_date (datetime): Starting pivot date
            n_cycles (int): Number of cycles to calculate
            
        Returns:
            List[Dict]: Time targets with dates
        """
        # Gann's key time cycles in days
        cycles = [7, 14, 21, 30, 45, 52, 60, 90, 120, 144, 180, 270, 360, 720]
        
        targets = []
        for cycle in cycles[:n_cycles]:
            target_date = pivot_date + timedelta(days=cycle)
            targets.append({
                "days": cycle,
                "date": target_date,
                "date_str": target_date.strftime("%Y-%m-%d"),
                "significance": self._get_cycle_significance(cycle),
                "description": self._get_cycle_description(cycle)
            })
        
        return targets
    
    def _get_cycle_significance(self, days: int) -> str:
        """Get the significance level of a time cycle."""
        major_cycles = [90, 144, 180, 360, 720]
        important_cycles = [7, 30, 45, 60, 120, 270]
        
        if days in major_cycles:
            return "major"
        elif days in important_cycles:
            return "important"
        return "minor"
    
    def _get_cycle_description(self, days: int) -> str:
        """Get description for a time cycle."""
        descriptions = {
            7: "Weekly cycle",
            14: "Bi-weekly cycle",
            21: "Three week cycle",
            30: "Monthly cycle",
            45: "45-day cycle (1/8 year)",
            52: "Annual week cycle",
            60: "60-day cycle (2 months)",
            90: "Quarterly cycle (1/4 year)",
            120: "4-month cycle (1/3 year)",
            144: "Fibonacci/Gann cycle (144 days)",
            180: "Semi-annual cycle (1/2 year)",
            270: "3/4 year cycle",
            360: "Annual cycle (Gann year)",
            720: "Two-year cycle"
        }
        return descriptions.get(days, f"{days} day cycle")
    
    def get_price_squares(
        self,
        base_price: float,
        n_squares: int = 12
    ) -> List[Dict]:
        """
        Calculate price squares based on Gann's theory.
        
        Args:
            base_price (float): Base price for calculations
            n_squares (int): Number of squares to calculate
            
        Returns:
            List[Dict]: Price square levels
        """
        squares = []
        
        for i in range(1, n_squares + 1):
            # Square root method
            sqrt_base = np.sqrt(base_price)
            
            # Add squares
            up_sqrt = sqrt_base + i
            down_sqrt = sqrt_base - i if sqrt_base - i > 0 else 0
            
            squares.append({
                "level": i,
                "up_price": round(up_sqrt ** 2, 4),
                "down_price": round(down_sqrt ** 2, 4) if down_sqrt > 0 else 0,
                "ratio": f"{i}:1"
            })
        
        return squares
    
    def calculate_vibration_levels(
        self,
        high: float,
        low: float
    ) -> Dict[str, List[float]]:
        """
        Calculate Gann vibration levels between high and low.
        
        Args:
            high (float): High price of range
            low (float): Low price of range
            
        Returns:
            Dict with vibration levels
        """
        range_val = high - low
        
        # Gann's natural divisions
        divisions = {
            "1/8": 0.125,
            "1/4": 0.25,
            "1/3": 0.3333,
            "3/8": 0.375,
            "1/2": 0.5,
            "5/8": 0.625,
            "2/3": 0.6667,
            "3/4": 0.75,
            "7/8": 0.875
        }
        
        levels = {}
        
        # Levels from low
        levels["from_low"] = []
        for name, ratio in divisions.items():
            price = low + (range_val * ratio)
            levels["from_low"].append({
                "name": name,
                "price": round(price, 4),
                "percentage": ratio * 100
            })
        
        # Levels from high (retracement)
        levels["from_high"] = []
        for name, ratio in divisions.items():
            price = high - (range_val * ratio)
            levels["from_high"].append({
                "name": name,
                "price": round(price, 4),
                "percentage": ratio * 100
            })
        
        return levels


def calculate_gann_geometry(
    pivot_price: float,
    pivot_time: int,
    bars_forward: int = 100
) -> pd.DataFrame:
    """
    Convenience function to calculate Gann geometry.
    
    Args:
        pivot_price (float): Price at pivot point
        pivot_time (int): Time index at pivot
        bars_forward (int): Bars to project
        
    Returns:
        pd.DataFrame: Gann angle lines
    """
    geometry = TimePriceGeometry()
    return geometry.calculate_angle_lines(pivot_price, pivot_time, bars_forward)


if __name__ == "__main__":
    # Test Time-Price Geometry
    tpg = TimePriceGeometry(time_unit=1.0, price_unit=1.0)
    
    pivot = 42000.0
    current = 45000.0
    
    print("\nGann Time-Price Geometry Analysis")
    print("=" * 50)
    
    # Calculate angle lines
    lines = tpg.calculate_angle_lines(pivot, 0, bars_forward=10)
    print("\nAngle Lines (first 5 bars):")
    print(lines[["bar", "1x1_up", "1x2_up", "2x1_up"]].head())
    
    # Support/Resistance
    sr = tpg.find_support_resistance(current, pivot, 0, 5)
    print(f"\nSupport/Resistance for price ${current:,} (pivot at ${pivot:,}):")
    print("\nClosest Support:")
    for s in sr["support"][:3]:
        print(f"  {s['angle']}: ${s['price']:,.2f}")
    print("\nClosest Resistance:")
    for r in sr["resistance"][:3]:
        print(f"  {r['angle']}: ${r['price']:,.2f}")
    
    # Time targets
    from datetime import datetime
    targets = tpg.calculate_time_targets(datetime.now(), n_cycles=8)
    print("\nTime Targets:")
    for t in targets:
        print(f"  {t['days']} days ({t['significance']}): {t['date_str']}")
    
    # Vibration levels
    vib = tpg.calculate_vibration_levels(50000.0, 40000.0)
    print("\nVibration Levels (from low):")
    for v in vib["from_low"][:5]:
        print(f"  {v['name']}: ${v['price']:,.2f}")
