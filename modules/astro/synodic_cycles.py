"""
Synodic Cycles Module
Implements planetary synodic cycles for financial astrology.

Synodic cycles are the time periods between successive conjunctions of 
two celestial bodies as seen from Earth. These cycles are believed to
correlate with market rhythm and turning points.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class SynodicCycle:
    """Represents a planetary synodic cycle."""
    name: str
    planet1: str
    planet2: str
    period_days: float
    significance: str
    market_correlation: str


class SynodicCycleCalculator:
    """
    Calculates planetary synodic cycles and their influence on markets.
    
    Based on the astrological principle that planetary alignments create
    rhythmic patterns in collective human behavior, affecting markets.
    """
    
    # Mean synodic periods in days (planet to Sun)
    SYNODIC_PERIODS = {
        "Mercury": 115.88,
        "Venus": 583.92,
        "Mars": 779.94,
        "Jupiter": 398.88,
        "Saturn": 378.09,
        "Uranus": 369.66,
        "Neptune": 367.49,
        "Pluto": 366.73
    }
    
    # Key planetary pair cycles
    PAIR_CYCLES = {
        "Jupiter-Saturn": {
            "period_years": 19.86,
            "period_days": 7253.5,
            "significance": "major",
            "market_correlation": "Major economic cycles, generational shifts"
        },
        "Saturn-Uranus": {
            "period_years": 45.4,
            "period_days": 16580.6,
            "significance": "major",
            "market_correlation": "Technology disruption cycles"
        },
        "Jupiter-Uranus": {
            "period_years": 13.81,
            "period_days": 5044.0,
            "significance": "important",
            "market_correlation": "Innovation and breakthrough cycles"
        },
        "Mars-Saturn": {
            "period_years": 2.0,
            "period_days": 730.5,
            "significance": "moderate",
            "market_correlation": "Energy sector cycles, conflict timing"
        },
        "Venus-Mars": {
            "period_days": 340.0,
            "significance": "moderate",
            "market_correlation": "Short-term sentiment cycles"
        },
        "Mercury-Venus": {
            "period_days": 144.5,
            "significance": "minor",
            "market_correlation": "Rapid trading cycles"
        }
    }
    
    # Gann-related time cycles (in calendar days)
    GANN_TIME_CYCLES = [
        7, 14, 21, 28, 30, 45, 49, 52, 60, 63, 72, 84, 90, 
        120, 135, 144, 150, 180, 225, 270, 288, 315, 360, 
        420, 468, 540, 576, 720, 1260, 2160
    ]
    
    def __init__(self):
        """Initialize Synodic Cycle Calculator."""
        logger.info("SynodicCycleCalculator initialized")
    
    def get_cycle_harmonics(
        self,
        base_date: datetime,
        cycle_name: str,
        n_harmonics: int = 8
    ) -> List[Dict]:
        """
        Calculate harmonic dates for a specific synodic cycle.
        
        Args:
            base_date (datetime): Reference starting date
            cycle_name (str): Name of the cycle (e.g., "Jupiter-Saturn")
            n_harmonics (int): Number of harmonic points to calculate
            
        Returns:
            List[Dict]: Harmonic dates and their significance
        """
        if cycle_name not in self.PAIR_CYCLES:
            logger.warning(f"Unknown cycle: {cycle_name}")
            return []
        
        cycle = self.PAIR_CYCLES[cycle_name]
        period = cycle.get("period_days", cycle.get("period_years", 1) * 365.25)
        
        harmonics = []
        divisions = [1, 2, 3, 4, 6, 8, 12]  # Key harmonic divisions
        
        for div in divisions[:n_harmonics]:
            harmonic_period = period / div
            
            # Forward projections
            for mult in range(1, 5):
                target_date = base_date + timedelta(days=harmonic_period * mult)
                harmonics.append({
                    "date": target_date,
                    "date_str": target_date.strftime("%Y-%m-%d"),
                    "cycle": cycle_name,
                    "harmonic": f"1/{div}",
                    "multiple": mult,
                    "days_from_base": int(harmonic_period * mult),
                    "significance": self._get_harmonic_significance(div)
                })
        
        # Sort by date
        harmonics = sorted(harmonics, key=lambda x: x["date"])
        return harmonics
    
    def _get_harmonic_significance(self, division: int) -> str:
        """Get significance level of a harmonic division."""
        if division in [1, 2]:
            return "major"
        elif division in [3, 4]:
            return "important"
        elif division in [6]:
            return "moderate"
        return "minor"
    
    def calculate_time_clusters(
        self,
        base_date: datetime,
        days_forward: int = 365
    ) -> pd.DataFrame:
        """
        Find time clusters where multiple cycles converge.
        
        Args:
            base_date (datetime): Starting date
            days_forward (int): Number of days to analyze
            
        Returns:
            pd.DataFrame: Dates ranked by cycle convergence
        """
        # Create date range
        dates = pd.date_range(start=base_date, periods=days_forward, freq='D')
        convergence_scores = np.zeros(len(dates))
        
        # Check each Gann time cycle
        for cycle_days in self.GANN_TIME_CYCLES:
            for i, date in enumerate(dates):
                days_elapsed = (date - base_date).days
                
                # Check if near a cycle harmonic
                for harmonic in [1, 2, 3, 4, 6, 8]:
                    harmonic_days = cycle_days / harmonic
                    remainder = days_elapsed % harmonic_days if harmonic_days > 0 else 0
                    
                    # If within 2% of cycle
                    tolerance = max(1, harmonic_days * 0.02)
                    if remainder < tolerance or harmonic_days - remainder < tolerance:
                        weight = 1 / harmonic  # Higher harmonics get lower weight
                        convergence_scores[i] += weight
        
        # Check planetary synodic cycles
        for cycle_name, cycle_info in self.PAIR_CYCLES.items():
            period = cycle_info.get("period_days", cycle_info.get("period_years", 1) * 365.25)
            
            for i, date in enumerate(dates):
                days_elapsed = (date - base_date).days
                
                for harmonic in [1, 2, 4]:
                    harmonic_days = period / harmonic
                    remainder = days_elapsed % harmonic_days if harmonic_days > 0 else 0
                    
                    tolerance = max(1, harmonic_days * 0.02)
                    if remainder < tolerance or harmonic_days - remainder < tolerance:
                        weight = 2 / harmonic  # Higher weight for planetary cycles
                        if cycle_info["significance"] == "major":
                            weight *= 2
                        convergence_scores[i] += weight
        
        # Create result DataFrame
        result = pd.DataFrame({
            "date": dates,
            "convergence_score": convergence_scores
        })
        
        # Normalize scores
        max_score = result["convergence_score"].max()
        if max_score > 0:
            result["normalized_score"] = result["convergence_score"] / max_score * 100
        else:
            result["normalized_score"] = 0
        
        result["is_cluster"] = result["normalized_score"] > 70
        
        return result
    
    def get_current_cycle_phases(self, date: datetime = None) -> List[Dict]:
        """
        Get current phase information for all major cycles.
        
        Args:
            date (datetime): Date to analyze (default: now)
            
        Returns:
            List[Dict]: Current phase for each cycle
        """
        if date is None:
            date = datetime.now()
        
        # Reference dates for major cycles (approximate conjunction dates)
        reference_dates = {
            "Jupiter-Saturn": datetime(2020, 12, 21),  # Great conjunction
            "Saturn-Uranus": datetime(2032, 1, 1),     # Approximate
            "Jupiter-Uranus": datetime(2024, 4, 20),   # Conjunction in Taurus
            "Mars-Saturn": datetime(2024, 4, 10),      # Recent conjunction
        }
        
        phases = []
        
        for cycle_name, ref_date in reference_dates.items():
            if cycle_name in self.PAIR_CYCLES:
                cycle_info = self.PAIR_CYCLES[cycle_name]
                period = cycle_info.get("period_days", cycle_info.get("period_years", 1) * 365.25)
                
                days_elapsed = (date - ref_date).days
                phase_fraction = (days_elapsed % period) / period
                phase_degrees = phase_fraction * 360
                
                # Determine phase name
                if phase_degrees < 45:
                    phase_name = "New (Conjunction)"
                elif phase_degrees < 90:
                    phase_name = "Crescent"
                elif phase_degrees < 135:
                    phase_name = "First Quarter (Square)"
                elif phase_degrees < 180:
                    phase_name = "Gibbous"
                elif phase_degrees < 225:
                    phase_name = "Full (Opposition)"
                elif phase_degrees < 270:
                    phase_name = "Disseminating"
                elif phase_degrees < 315:
                    phase_name = "Last Quarter (Square)"
                else:
                    phase_name = "Balsamic"
                
                phases.append({
                    "cycle": cycle_name,
                    "phase_degrees": round(phase_degrees, 1),
                    "phase_name": phase_name,
                    "phase_fraction": round(phase_fraction, 3),
                    "days_in_phase": days_elapsed % period,
                    "days_to_next_conjunction": int(period - (days_elapsed % period)),
                    "market_correlation": cycle_info["market_correlation"]
                })
        
        return phases
    
    def get_time_harmonics(
        self,
        pivot_date: datetime,
        n_projections: int = 20
    ) -> List[Dict]:
        """
        Calculate time harmonics projections from a pivot date.
        Uses Gann time cycles for projection.
        
        Args:
            pivot_date (datetime): Reference pivot date
            n_projections (int): Number of projections to generate
            
        Returns:
            List[Dict]: Projected time targets
        """
        projections = []
        
        # Use key Gann cycles
        key_cycles = [30, 45, 60, 72, 90, 120, 144, 180, 270, 360]
        
        for cycle in key_cycles:
            for mult in range(1, 4):
                days = cycle * mult
                target_date = pivot_date + timedelta(days=days)
                
                projections.append({
                    "date": target_date,
                    "date_str": target_date.strftime("%Y-%m-%d"),
                    "days": days,
                    "cycle": cycle,
                    "multiple": mult,
                    "significance": "major" if cycle in [90, 144, 180, 360] else "moderate"
                })
        
        # Sort by date and limit
        projections = sorted(projections, key=lambda x: x["date"])[:n_projections]
        
        return projections


def calculate_synodic_cycles(base_date: datetime = None) -> Dict:
    """
    Convenience function to get synodic cycle analysis.
    
    Args:
        base_date (datetime): Reference date
        
    Returns:
        Dict: Synodic cycle analysis
    """
    calc = SynodicCycleCalculator()
    
    if base_date is None:
        base_date = datetime.now()
    
    return {
        "current_phases": calc.get_current_cycle_phases(base_date),
        "time_harmonics": calc.get_time_harmonics(base_date),
        "jupiter_saturn_harmonics": calc.get_cycle_harmonics(base_date, "Jupiter-Saturn", 5)
    }


if __name__ == "__main__":
    calc = SynodicCycleCalculator()
    
    print("Synodic Cycle Analysis")
    print("=" * 60)
    
    # Current phases
    phases = calc.get_current_cycle_phases()
    print("\nCurrent Cycle Phases:")
    for p in phases:
        print(f"  {p['cycle']}: {p['phase_name']} ({p['phase_degrees']}°)")
        print(f"    Days to next conjunction: {p['days_to_next_conjunction']}")
    
    # Time clusters
    clusters = calc.calculate_time_clusters(datetime.now(), days_forward=90)
    top_clusters = clusters[clusters["is_cluster"]].head(10)
    
    print("\nUpcoming Time Clusters (next 90 days):")
    for _, row in top_clusters.iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')}: Score {row['normalized_score']:.1f}")
    
    # Time harmonics
    harmonics = calc.get_time_harmonics(datetime.now(), n_projections=10)
    print("\nTime Harmonic Projections:")
    for h in harmonics[:8]:
        print(f"  {h['date_str']}: {h['days']} days ({h['cycle']}x{h['multiple']}) - {h['significance']}")
