import pytest
import pandas as pd
from modules.astro.astro_ephemeris import AstroEphemeris
from modules.astro.planetary_aspects import find_planetary_aspects

@pytest.fixture(scope="module")
def ephemeris():
    """Fixture to load the ephemeris data once for all tests in this module."""
    eph = AstroEphemeris()
    return eph

# Conditional skip marker
# We skip all tests in this file if the ephemeris data (`eph.eph`) could not be loaded.
# This prevents test failures due to network issues outside of our code's control.
ephemeris_not_loaded = AstroEphemeris().eph is None
skip_if_no_ephemeris = pytest.mark.skipif(
    ephemeris_not_loaded,
    reason="Could not download ephemeris file from JPL. Skipping astro tests."
)

@skip_if_no_ephemeris
def test_ephemeris_initialization(ephemeris):
    """Tests that ephemeris data loads correctly."""
    assert ephemeris.eph is not None
    assert 'jupiter barycenter' in ephemeris.celestial_bodies

@skip_if_no_ephemeris
def test_get_positions(ephemeris):
    """Tests the calculation of planetary positions."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=5))
    positions = ephemeris.get_positions_for_dates(dates, ["Mars", "Venus"])

    assert isinstance(positions, dict)
    assert "mars" in positions
    assert "venus" in positions
    assert len(positions["mars"]) == 5
    assert isinstance(positions["venus"], pd.Series)

@skip_if_no_ephemeris
def test_find_aspects(ephemeris):
    """Tests the aspect detection logic with a known major aspect."""
    # Test for the Jupiter-Saturn conjunction in December 2020
    dates = pd.to_datetime(pd.date_range(start="2020-12-15", end="2020-12-30"))

    aspect_config = [{
        "planets": ["Jupiter", "Saturn"],
        "aspect": 0,
        "tolerance_degrees": 2.0
    }]

    positions = ephemeris.get_positions_for_dates(dates, ["Jupiter", "Saturn"])
    aspects = find_planetary_aspects(positions, aspect_config)

    assert not aspects.empty
    assert "Jupiter - Saturn" in aspects.iloc[0]['planets']
    assert "Conjunction" in aspects.iloc[0]['aspect_type']
    # The conjunction was exact around the 21st
    assert any(d.day in [20, 21, 22] for d in aspects['date'])

@skip_if_no_ephemeris
def test_empty_aspect_config(ephemeris):
    """Tests that no error occurs with empty aspect config."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=5))
    positions = ephemeris.get_positions_for_dates(dates, ["Mars"])
    aspects = find_planetary_aspects(positions, [])
    assert aspects.empty
