import pytest
import numpy as np
from modules.gann.square_of_9 import SquareOf9

def test_sq9_initialization():
    """Tests that the SquareOf9 class initializes correctly."""
    sq9 = SquareOf9(initial_price=100)
    assert sq9.initial_price == 100

    with pytest.raises(ValueError):
        SquareOf9(initial_price=0)
    with pytest.raises(ValueError):
        SquareOf9(initial_price=-50)

def test_sq9_level_calculation():
    """
    Tests the SQ9 level calculation against a known, simple case.
    The square root of 100 is 10. A 360-degree rotation (one full circle)
    outwards should result in a sqrt of 12, so the price should be 144.
    A 180-degree rotation (half circle) should be a sqrt of 11, so price is 121.
    """
    sq9 = SquareOf9(initial_price=100)
    levels = sq9.get_levels(n_levels=2) # n_levels needs to be large enough to contain expected values

    assert len(levels['support']) > 0
    assert len(levels['resistance']) > 0

    # Check if key resistance levels are present (180 and 360-degree rotations)
    # Note: The exact levels depend on the simplified formula.
    # We are checking for the presence of values close to the expected ones.
    resistance_levels = levels['resistance']
    assert any(np.isclose(level, 121) for level in resistance_levels)
    assert any(np.isclose(level, 144) for level in resistance_levels)

    # Check if key support levels are present
    support_levels = levels['support']
    assert any(np.isclose(level, 81) for level in support_levels)
    assert any(np.isclose(level, 64) for level in support_levels)

def test_sq9_edge_cases():
    """Tests with a very low initial price."""
    sq9 = SquareOf9(initial_price=1.5)
    levels = sq9.get_levels(n_levels=3)
    assert len(levels['resistance']) > 0
    # There might be very few or no support levels for a very low price
    assert all(level > 0 for level in levels['support'])
