"""
Enhanced Ehlers Scanner Module
Advanced scanning for Ehlers DSP indicators.
"""
import pandas as pd
from typing import Tuple

def scan_ehlers_fisher_state(
    last_candle: pd.Series,
    extreme_threshold: float = 2.0
) -> Tuple[bool, str]:
    """Scans for Fisher Transform extremes."""
    if 'fisher' not in last_candle or pd.isna(last_candle['fisher']):
        return False, "Fisher Transform not available"

    fisher_value = last_candle['fisher']

    if fisher_value > extreme_threshold:
        return True, f"Fisher Overbought ({fisher_value:.2f})"

    if fisher_value < -extreme_threshold:
        return True, f"Fisher Oversold ({fisher_value:.2f})"

    return False, ""

def scan_mama_fama_crossover(
    last_candle: pd.Series,
    prev_candle: pd.Series
) -> Tuple[bool, str]:
    """Scans for MAMA/FAMA crossovers."""
    required = ['mama', 'fama']
    if not all(col in last_candle for col in required) or not all(col in prev_candle for col in required):
        return False, "MAMA/FAMA data missing"
        
    # Bullish Cross: MAMA crosses above FAMA
    if prev_candle['mama'] <= prev_candle['fama'] and last_candle['mama'] > last_candle['fama']:
        return True, "Bullish MAMA/FAMA Cross"
        
    # Bearish Cross: MAMA crosses below FAMA
    if prev_candle['mama'] >= prev_candle['fama'] and last_candle['mama'] < last_candle['fama']:
        return True, "Bearish MAMA/FAMA Cross"
        
    return False, ""

def scan_trend_mode(
    last_candle: pd.Series
) -> Tuple[bool, str]:
    """Scans for Trend vs Cycle mode using Sinewave."""
    # If sine and leadsine are criss-crossing, it's Cycle mode
    # If they run parallel/wide spread, it's Trend mode
    # Here we simplify: strict Trend if distance > threshold
    
    if 'sine' not in last_candle or 'leadsine' not in last_candle:
        return False, "Sinewave data missing"
        
    spread = abs(last_candle['leadsine'] - last_candle['sine'])
    
    if spread > 0.8: # Arbitrary threshold for trend
        return True, "Trend Mode (Wide Spread)"
        
    return False, "Cycle Mode"
