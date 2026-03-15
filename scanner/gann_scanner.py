"""
Enhanced Gann Scanner Module
Advanced scanning for Gann patterns, angles, and cycles.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
from loguru import logger

def scan_gann_sq9_proximity(
    last_candle: pd.Series,
    gann_levels: Optional[Dict[str, List[float]]],
    tolerance_pct: float = 1.0
) -> Tuple[bool, str]:
    """Scans if price is near Gann SQ9 levels."""
    if gann_levels is None or not gann_levels.get('support') or not gann_levels.get('resistance'):
        return False, "Gann levels not available"

    last_close = float(last_candle['close'])
    tolerance_multiplier = tolerance_pct / 100.0

    # Support
    for level in gann_levels['support']:
        if abs(last_close - level) / level < tolerance_multiplier:
            return True, f"Near Gann Support {level:.2f}"

    # Resistance
    for level in gann_levels['resistance']:
        if abs(last_close - level) / level < tolerance_multiplier:
            return True, f"Near Gann Resistance {level:.2f}"

    return False, ""

def scan_gann_vibration(
    last_candle: pd.Series,
    prev_candle: pd.Series
) -> Tuple[bool, str]:
    """Scans for significant price vibration (Gann Swing)."""
    # Simple calculation: High > Prev High AND Low > Prev Low (Up Swing)
    # or High < Prev High AND Low < Prev Low (Down Swing)
    
    if last_candle['high'] > prev_candle['high'] and last_candle['low'] > prev_candle['low']:
        return True, "Gann Up Swing"
    
    if last_candle['high'] < prev_candle['high'] and last_candle['low'] < prev_candle['low']:
        return True, "Gann Down Swing"
        
    return False, ""

def scan_time_cycle_turn(
    current_date: datetime,
    pivot_dates: List[datetime],
    cycle_days: List[int] = [30, 60, 90, 144, 360],
    tolerance_days: int = 2
) -> Tuple[bool, str]:
    """Scans if current date is a potential time cycle turn."""
    for pivot in pivot_dates:
        days_diff = (current_date - pivot).days
        
        for cycle in cycle_days:
            if abs(days_diff - cycle) <= tolerance_days:
                return True, f"Time Turn: {cycle} days from pivot {pivot.date()}"
                
            # Check harmonic parts (0.5, 0.25)
            if abs(days_diff - cycle * 0.5) <= tolerance_days:
                 return True, f"Time Turn: {cycle*0.5:.0f} days (50% of {cycle}) from pivot"

    return False, ""
