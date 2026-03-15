"""
Ehlers Module
John Ehlers' Cycle and DSP indicators
"""
from .cyber_cycle import cyber_cycle
from .decycler import Decycler, decycler, decycler_oscillator
from .fisher_transform import fisher_transform
from .mama import mama
from .roofing_filter import RoofingFilter, roofing_filter, band_pass_filter
from .sinewave_indicator import SinewaveIndicator, sinewave_indicator, even_better_sinewave
from .super_smoother import SuperSmoother, super_smoother, super_smoother_3pole
from .bandpass_filter import BandpassFilter, bandpass_filter, AGCBandpass, agc_bandpass
from .smoothed_rsi import SmoothedRSI, smoothed_rsi, LaguerreRSI, laguerre_rsi
from .instantaneous_trendline import InstantaneousTrendline, instantaneous_trendline, TrendVigor, trend_vigor, EhlersDecycler, ehlers_decycler
from .hilbert_transform import HilbertTransform, hilbert_transform, DominantCyclePeriod, dominant_cycle_period

__all__ = [
    'cyber_cycle',
    'Decycler',
    'decycler',
    'decycler_oscillator',
    'fisher_transform',
    'mama',
    'RoofingFilter',
    'roofing_filter',
    'band_pass_filter',
    'SinewaveIndicator',
    'sinewave_indicator',
    'even_better_sinewave',
    'SuperSmoother',
    'super_smoother',
    'super_smoother_3pole',
    # New DSP modules
    'BandpassFilter',
    'bandpass_filter',
    'AGCBandpass',
    'agc_bandpass',
    'SmoothedRSI',
    'smoothed_rsi',
    'LaguerreRSI',
    'laguerre_rsi',
    'InstantaneousTrendline',
    'instantaneous_trendline',
    'TrendVigor',
    'trend_vigor',
    'EhlersDecycler',
    'ehlers_decycler',
    'HilbertTransform',
    'hilbert_transform',
    'DominantCyclePeriod',
    'dominant_cycle_period',
]
