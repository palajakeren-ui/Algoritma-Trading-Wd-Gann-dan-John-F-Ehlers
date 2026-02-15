"""
Time Harmonics Module
Advanced time cycle analysis combining Gann, Fibonacci, and planetary time harmonics.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class TimeHarmonic:
    """Represents a time harmonic point."""
    date: datetime
    days_from_pivot: int
    cycle_type: str
    significance: str
    description: str


class TimeHarmonicsCalculator:
    """
    Advanced time harmonics analysis combining multiple methodologies.
    
    Integrates:
    - Gann natural time cycles
    - Fibonacci time sequences
    - Square of 9 time projections
    - Planetary cycle harmonics
    """
    
    # Gann key numbers
    GANN_NUMBERS = [7, 9, 12, 18, 24, 30, 36, 45, 49, 52, 60, 72, 84, 90, 
                   120, 144, 168, 180, 225, 252, 270, 288, 315, 360, 
                   432, 450, 468, 504, 540, 576, 630, 720, 756, 900,
                   1008, 1080, 1260, 2160, 2520]
    
    # Fibonacci time sequence (in days)
    FIBONACCI_DAYS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
    
    # Square root time cycles
    SQRT_CYCLES = [i**2 for i in range(1, 20)]  # 1, 4, 9, 16, 25, ...
    
    def __init__(self):
        """Initialize TimeHarmonicsCalculator."""
        logger.info("TimeHarmonicsCalculator initialized")
    
    def calculate_gann_time_targets(
        self,
        pivot_date: datetime,
        n_targets: int = 20
    ) -> List[TimeHarmonic]:
        """
        Calculate Gann natural time cycle targets.
        
        Args:
            pivot_date (datetime): Reference pivot date
            n_targets (int): Number of targets to return
            
        Returns:
            List[TimeHarmonic]: Time harmonic targets
        """
        targets = []
        
        for days in self.GANN_NUMBERS:
            if days <= 365 * 3:  # Limit to 3 years
                target_date = pivot_date + timedelta(days=days)
                
                # Determine significance
                if days in [90, 144, 180, 270, 360, 720]:
                    significance = "major"
                    desc = f"Major Gann cycle ({days} days)"
                elif days in [30, 45, 60, 252]:
                    significance = "important"
                    desc = f"Important Gann cycle ({days} days)"
                else:
                    significance = "minor"
                    desc = f"Gann cycle ({days} days)"
                
                targets.append(TimeHarmonic(
                    date=target_date,
                    days_from_pivot=days,
                    cycle_type="gann",
                    significance=significance,
                    description=desc
                ))
        
        targets = sorted(targets, key=lambda x: x.date)[:n_targets]
        return targets
    
    def calculate_fibonacci_time(
        self,
        pivot_date: datetime,
        unit: str = "days"
    ) -> List[TimeHarmonic]:
        """
        Calculate Fibonacci time sequence targets.
        
        Args:
            pivot_date (datetime): Reference pivot date
            unit (str): Time unit ("days" or "weeks")
            
        Returns:
            List[TimeHarmonic]: Fibonacci time targets
        """
        targets = []
        multiplier = 7 if unit == "weeks" else 1
        
        for fib_num in self.FIBONACCI_DAYS:
            days = fib_num * multiplier
            target_date = pivot_date + timedelta(days=days)
            
            # Key Fibonacci numbers are more significant
            if fib_num in [8, 13, 21, 55, 89, 144, 233]:
                significance = "major"
            elif fib_num in [34, 377]:
                significance = "important"
            else:
                significance = "minor"
            
            targets.append(TimeHarmonic(
                date=target_date,
                days_from_pivot=days,
                cycle_type="fibonacci",
                significance=significance,
                description=f"Fibonacci {fib_num} {unit}"
            ))
        
        return targets
    
    def calculate_square_of_9_time(
        self,
        pivot_date: datetime,
        base_value: float
    ) -> List[TimeHarmonic]:
        """
        Calculate Square of 9 time projections.
        Uses square root time cycles.
        
        Args:
            pivot_date (datetime): Reference pivot date
            base_value (float): Base value for calculations
            
        Returns:
            List[TimeHarmonic]: Square of 9 time targets
        """
        targets = []
        
        sqrt_base = np.sqrt(base_value)
        
        # Calculate time targets using cardinal and ordinal cross
        angles = [45, 90, 135, 180, 225, 270, 315, 360]
        
        for n in range(1, 6):  # 5 levels
            for angle in angles:
                # Time value from square of 9
                sqrt_time = sqrt_base + (n * angle / 360)
                days = int(sqrt_time ** 2)
                
                target_date = pivot_date + timedelta(days=days)
                
                significance = "major" if angle in [90, 180, 270, 360] else "minor"
                
                targets.append(TimeHarmonic(
                    date=target_date,
                    days_from_pivot=days,
                    cycle_type="sq9_time",
                    significance=significance,
                    description=f"SQ9 {angle}° Level {n} ({days} days)"
                ))
        
        # Remove duplicates and sort
        seen = set()
        unique_targets = []
        for t in targets:
            key = t.days_from_pivot
            if key not in seen and key > 0:
                seen.add(key)
                unique_targets.append(t)
        
        return sorted(unique_targets, key=lambda x: x.date)
    
    def find_time_convergence(
        self,
        pivot_date: datetime,
        days_forward: int = 365,
        tolerance_days: int = 3
    ) -> pd.DataFrame:
        """
        Find dates where multiple time cycles converge.
        
        Args:
            pivot_date (datetime): Reference pivot date
            days_forward (int): Days to analyze
            tolerance_days (int): Days tolerance for convergence
            
        Returns:
            pd.DataFrame: Convergence analysis
        """
        # Collect all cycle targets
        gann_targets = [t.days_from_pivot for t in self.calculate_gann_time_targets(pivot_date, 50)]
        fib_targets = [t.days_from_pivot for t in self.calculate_fibonacci_time(pivot_date)]
        
        # Create date range
        dates = pd.date_range(start=pivot_date, periods=days_forward, freq='D')
        convergence_scores = np.zeros(len(dates))
        convergence_details = [""] * len(dates)
        
        for i, date in enumerate(dates):
            days_elapsed = (date - pivot_date).days
            details = []
            
            # Check Gann cycles
            for g_days in gann_targets:
                if abs(days_elapsed - g_days) <= tolerance_days:
                    convergence_scores[i] += 2 if g_days in [90, 144, 180, 360, 720] else 1
                    details.append(f"Gann-{g_days}")
            
            # Check Fibonacci
            for f_days in fib_targets:
                if abs(days_elapsed - f_days) <= tolerance_days:
                    convergence_scores[i] += 2 if f_days in [55, 89, 144, 233] else 1
                    details.append(f"Fib-{f_days}")
            
            # Check square cycles
            for sq in self.SQRT_CYCLES:
                if abs(days_elapsed - sq) <= tolerance_days:
                    convergence_scores[i] += 1
                    details.append(f"Sq-{sq}")
            
            convergence_details[i] = ", ".join(details)
        
        result = pd.DataFrame({
            "date": dates,
            "days_from_pivot": range(days_forward),
            "convergence_score": convergence_scores,
            "details": convergence_details
        })
        
        # Normalize
        max_score = result["convergence_score"].max()
        if max_score > 0:
            result["normalized_score"] = result["convergence_score"] / max_score * 100
        else:
            result["normalized_score"] = 0
        
        result["is_cluster"] = result["normalized_score"] >= 50
        
        return result
    
    def calculate_anniversary_cycles(
        self,
        historical_pivots: List[datetime],
        analysis_date: datetime = None
    ) -> List[Dict]:
        """
        Calculate anniversary cycles from historical pivots.
        
        Args:
            historical_pivots (List[datetime]): List of historical pivot dates
            analysis_date (datetime): Date to analyze from
            
        Returns:
            List[Dict]: Anniversary cycle information
        """
        if analysis_date is None:
            analysis_date = datetime.now()
        
        results = []
        
        for pivot in historical_pivots:
            days_since = (analysis_date - pivot).days
            years_since = days_since / 365.25
            
            # Check for anniversary cycles
            anniversary_cycles = []
            
            # Annual cycles
            for year in range(1, 11):
                year_days = int(year * 365.25)
                if abs(days_since - year_days) <= 7:
                    anniversary_cycles.append(f"{year}-year anniversary")
            
            # Quarter cycles
            for quarter in range(1, 41):
                quarter_days = int(quarter * 91.3)
                if abs(days_since - quarter_days) <= 5:
                    anniversary_cycles.append(f"{quarter}-quarter cycle")
            
            if anniversary_cycles:
                results.append({
                    "pivot_date": pivot.strftime("%Y-%m-%d"),
                    "days_since": days_since,
                    "years_since": round(years_since, 2),
                    "cycles_active": anniversary_cycles,
                    "significance": "major" if len(anniversary_cycles) > 1 else "moderate"
                })
        
        return results
    
    def get_composite_time_analysis(
        self,
        pivot_date: datetime,
        days_forward: int = 90
    ) -> Dict:
        """
        Get comprehensive time analysis combining all methods.
        
        Args:
            pivot_date (datetime): Reference pivot date
            days_forward (int): Days to analyze
            
        Returns:
            Dict: Complete time analysis
        """
        # Calculate all targets
        gann = self.calculate_gann_time_targets(pivot_date, 20)
        fib = self.calculate_fibonacci_time(pivot_date)
        convergence = self.find_time_convergence(pivot_date, days_forward)
        
        # Get top clusters
        top_clusters = convergence[
            convergence["is_cluster"]
        ].nlargest(10, "convergence_score")
        
        return {
            "pivot_date": pivot_date.strftime("%Y-%m-%d"),
            "gann_targets": [
                {
                    "date": t.date.strftime("%Y-%m-%d"),
                    "days": t.days_from_pivot,
                    "significance": t.significance,
                    "description": t.description
                }
                for t in gann[:10]
            ],
            "fibonacci_targets": [
                {
                    "date": t.date.strftime("%Y-%m-%d"),
                    "days": t.days_from_pivot,
                    "significance": t.significance,
                    "description": t.description
                }
                for t in fib
            ],
            "time_clusters": [
                {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "days": int(row["days_from_pivot"]),
                    "score": round(row["normalized_score"], 1),
                    "cycles": row["details"]
                }
                for _, row in top_clusters.iterrows()
            ]
        }


def calculate_time_harmonics(pivot_date: datetime = None) -> Dict:
    """
    Convenience function for time harmonics analysis.
    
    Args:
        pivot_date (datetime): Reference date
        
    Returns:
        Dict: Time harmonics analysis
    """
    if pivot_date is None:
        pivot_date = datetime.now()
    
    calc = TimeHarmonicsCalculator()
    return calc.get_composite_time_analysis(pivot_date)


if __name__ == "__main__":
    calc = TimeHarmonicsCalculator()
    
    print("Time Harmonics Analysis")
    print("=" * 60)
    
    pivot = datetime.now() - timedelta(days=30)  # Use 30 days ago as pivot
    
    # Gann targets
    gann = calc.calculate_gann_time_targets(pivot, 10)
    print(f"\nGann Time Targets from {pivot.strftime('%Y-%m-%d')}:")
    for t in gann[:8]:
        print(f"  {t.date.strftime('%Y-%m-%d')}: {t.description} ({t.significance})")
    
    # Fibonacci targets
    fib = calc.calculate_fibonacci_time(pivot)
    print(f"\nFibonacci Time Targets:")
    for t in fib[:8]:
        print(f"  {t.date.strftime('%Y-%m-%d')}: {t.description} ({t.significance})")
    
    # Time convergence
    convergence = calc.find_time_convergence(pivot, days_forward=90)
    clusters = convergence[convergence["is_cluster"]].head(10)
    
    print(f"\nTime Clusters (next 90 days):")
    for _, row in clusters.iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')}: Score {row['normalized_score']:.1f} | {row['details']}")
