import pytest
import pandas as pd
from scanner.gann_scanner import scan_gann_sq9_proximity
from scanner.ehlers_scanner import scan_ehlers_fisher_state

# --- Gann Scanner Tests ---

def test_gann_scanner_near_support():
    """Tests Gann scanner when price is near a support level."""
    last_candle = pd.Series({'close': 100.5})
    gann_levels = {'support': [100.0, 95.0], 'resistance': [110.0]}
    is_near, reason = scan_gann_sq9_proximity(last_candle, gann_levels, tolerance_pct=1.0)
    assert is_near
    assert "Near Gann Support" in reason
    assert "100.00" in reason

def test_gann_scanner_not_near_any_level():
    """Tests Gann scanner when price is not near any level."""
    last_candle = pd.Series({'close': 105.0})
    gann_levels = {'support': [100.0], 'resistance': [110.0]}
    is_near, _ = scan_gann_sq9_proximity(last_candle, gann_levels, tolerance_pct=2.0)
    assert not is_near

def test_gann_scanner_no_levels():
    """Tests Gann scanner when Gann levels are not provided."""
    last_candle = pd.Series({'close': 100.0})
    is_near, reason = scan_gann_sq9_proximity(last_candle, None)
    assert not is_near
    assert "not available" in reason

# --- Ehlers Scanner Tests ---

def test_ehlers_scanner_overbought():
    """Tests Ehlers scanner for an overbought Fisher Transform state."""
    last_candle = pd.Series({'fisher': 2.5})
    is_extreme, reason = scan_ehlers_fisher_state(last_candle, extreme_threshold=2.0)
    assert is_extreme
    assert "Fisher Overbought" in reason
    assert "2.50" in reason

def test_ehlers_scanner_oversold():
    """Tests Ehlers scanner for an oversold Fisher Transform state."""
    last_candle = pd.Series({'fisher': -3.1})
    is_extreme, reason = scan_ehlers_fisher_state(last_candle, extreme_threshold=2.5)
    assert is_extreme
    assert "Fisher Oversold" in reason
    assert "-3.10" in reason

def test_ehlers_scanner_not_extreme():
    """Tests Ehlers scanner when Fisher is not in an extreme state."""
    last_candle = pd.Series({'fisher': 0.5})
    is_extreme, _ = scan_ehlers_fisher_state(last_candle, extreme_threshold=1.5)
    assert not is_extreme

def test_ehlers_scanner_missing_data():
    """Tests Ehlers scanner when the 'fisher' column is missing."""
    last_candle = pd.Series({'close': 100.0})
    is_extreme, reason = scan_ehlers_fisher_state(last_candle)
    assert not is_extreme
    assert "not available" in reason
