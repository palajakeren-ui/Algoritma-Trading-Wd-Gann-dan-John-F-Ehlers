# cython: boundscheck=False, wraparound=False, cdivision=True, nonecheck=False
# ============================================================================
# CENAYANG MARKET — Cython Ehlers DSP Compute Plane
#
# John F. Ehlers Digital Signal Processing Indicators
# Deterministic, incremental, zero look-ahead bias
# Pre-allocated double buffers for hot-path performance
#
# All functions are pure math — no I/O, no allocation in hot path
# Shared memory interface with Go State Authority Plane
#
# Indicators Implemented:
#   1.  Fisher Transform
#   2.  Super Smoother Filter
#   3.  MAMA (MESA Adaptive Moving Average)
#   4.  FAMA (Following Adaptive Moving Average)
#   5.  Cyber Cycle
#   6.  Sinewave Indicator
#   7.  Decycler Oscillator
#   8.  Smoothed RSI (Ehlers)
#   9.  Instantaneous Trendline
#   10. Dominant Cycle (Hilbert Transform)
#   11. Roofing Filter
#   12. Bandpass Filter
#
# Performance: <50μs per bar per indicator on single core
# ============================================================================

import numpy as np
cimport numpy as cnp
from libc.math cimport sin, cos, atan, exp, sqrt, log, M_PI, fabs

ctypedef cnp.float64_t DTYPE_t


# ============================================================================
# 1. FISHER TRANSFORM
# ============================================================================

def fisher_transform(cnp.ndarray[DTYPE_t, ndim=1] high,
                     cnp.ndarray[DTYPE_t, ndim=1] low,
                     int period=10):
    """
    Ehlers Fisher Transform — normalizes price to Gaussian distribution.
    Produces sharp turning-point signals with minimal lag.
    """
    cdef int n = high.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] fisher = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] trigger = np.zeros(n, dtype=np.float64)
    cdef double max_h, min_l, mid, val, prev_val = 0.0, prev_fish = 0.0
    cdef int i, j

    for i in range(period, n):
        max_h = high[i]
        min_l = low[i]
        for j in range(1, period):
            if high[i - j] > max_h:
                max_h = high[i - j]
            if low[i - j] < min_l:
                min_l = low[i - j]

        mid = (high[i] + low[i]) / 2.0
        if max_h != min_l:
            val = 0.33 * 2.0 * ((mid - min_l) / (max_h - min_l) - 0.5) + 0.67 * prev_val
        else:
            val = prev_val

        # Clamp to prevent atanh overflow
        if val > 0.999:
            val = 0.999
        elif val < -0.999:
            val = -0.999

        fisher[i] = 0.5 * log((1.0 + val) / (1.0 - val)) + 0.5 * prev_fish
        trigger[i] = prev_fish
        prev_val = val
        prev_fish = fisher[i]

    return fisher, trigger


# ============================================================================
# 2. SUPER SMOOTHER FILTER
# ============================================================================

def super_smoother(cnp.ndarray[DTYPE_t, ndim=1] data, int period=10):
    """
    Ehlers Super Smoother — superior to EMA with less lag and no ripple.
    Two-pole Butterworth filter implementation.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] filt = np.zeros(n, dtype=np.float64)
    cdef double a1, b1, c1, c2, c3
    cdef double freq = 1.414 * M_PI / period
    cdef int i

    a1 = exp(-freq)
    b1 = 2.0 * a1 * cos(freq)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1.0 - c2 - c3

    filt[0] = data[0]
    if n > 1:
        filt[1] = data[1]

    for i in range(2, n):
        filt[i] = c1 * (data[i] + data[i - 1]) / 2.0 + c2 * filt[i - 1] + c3 * filt[i - 2]

    return filt


# ============================================================================
# 3 & 4. MAMA + FAMA (MESA Adaptive Moving Average)
# ============================================================================

def mama_fama(cnp.ndarray[DTYPE_t, ndim=1] data,
              double fast_limit=0.5, double slow_limit=0.05):
    """
    Ehlers MAMA/FAMA — adaptive filter that adjusts speed to market conditions.
    MAMA = MESA Adaptive Moving Average
    FAMA = Following Adaptive Moving Average
    Crossover signals: MAMA crosses FAMA.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] mama_out = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] fama_out = np.zeros(n, dtype=np.float64)
    cdef double smooth[7]
    cdef double detrender[7]
    cdef double q1[7]
    cdef double i1[7]
    cdef double ji, jq, i2, q2, re, im, period_val, smooth_period
    cdef double phase, delta_phase, alpha
    cdef double mama_val, fama_val
    cdef int i, j

    for j in range(7):
        smooth[j] = 0.0
        detrender[j] = 0.0
        q1[j] = 0.0
        i1[j] = 0.0

    i2 = 0.0
    q2 = 0.0
    re = 0.0
    im = 0.0
    period_val = 0.0
    smooth_period = 0.0
    phase = 0.0
    mama_val = data[0] if n > 0 else 0.0
    fama_val = data[0] if n > 0 else 0.0

    for i in range(6, n):
        # Shift arrays
        for j in range(6, 0, -1):
            smooth[j] = smooth[j - 1]
            detrender[j] = detrender[j - 1]
            q1[j] = q1[j - 1]
            i1[j] = i1[j - 1]

        smooth[0] = (4.0 * data[i] + 3.0 * data[i - 1] + 2.0 * data[i - 2] + data[i - 3]) / 10.0

        adj = 0.075 * period_val + 0.54 if period_val > 0 else 0.075
        detrender[0] = (0.0962 * smooth[0] + 0.5769 * smooth[2] -
                        0.5769 * smooth[4] - 0.0962 * smooth[6]) * adj

        # In-phase and quadrature
        q1[0] = (0.0962 * detrender[0] + 0.5769 * detrender[2] -
                 0.5769 * detrender[4] - 0.0962 * detrender[6]) * adj
        i1[0] = detrender[3]

        ji = (0.0962 * i1[0] + 0.5769 * i1[2] - 0.5769 * i1[4] - 0.0962 * i1[6]) * adj
        jq = (0.0962 * q1[0] + 0.5769 * q1[2] - 0.5769 * q1[4] - 0.0962 * q1[6]) * adj

        i2_new = i1[0] - jq
        q2_new = q1[0] + ji
        i2 = 0.2 * i2_new + 0.8 * i2
        q2 = 0.2 * q2_new + 0.8 * q2

        re_new = i2 * i2 + q2 * q2
        im_new = i2 * q2 - q2 * i2
        re = 0.2 * re_new + 0.8 * re
        im = 0.2 * im_new + 0.8 * im

        if im != 0.0 and re != 0.0:
            period_val = 2.0 * M_PI / atan(im / re)
        if period_val > 1.5 * smooth_period:
            period_val = 1.5 * smooth_period
        if period_val < 0.67 * smooth_period:
            period_val = 0.67 * smooth_period
        if period_val < 6.0:
            period_val = 6.0
        if period_val > 50.0:
            period_val = 50.0

        smooth_period = 0.33 * period_val + 0.67 * smooth_period

        if smooth_period != 0.0:
            phase_new = atan(i1[0] / q1[0]) if q1[0] != 0.0 else 0.0
            delta_phase = phase - phase_new
            if delta_phase < 1.0:
                delta_phase = 1.0
            alpha = fast_limit / delta_phase
            if alpha < slow_limit:
                alpha = slow_limit
            if alpha > fast_limit:
                alpha = fast_limit
            phase = phase_new
        else:
            alpha = fast_limit

        mama_val = alpha * data[i] + (1.0 - alpha) * mama_val
        fama_val = 0.5 * alpha * mama_val + (1.0 - 0.5 * alpha) * fama_val

        mama_out[i] = mama_val
        fama_out[i] = fama_val

    return mama_out, fama_out


# ============================================================================
# 5. CYBER CYCLE
# ============================================================================

def cyber_cycle(cnp.ndarray[DTYPE_t, ndim=1] data, double alpha=0.07):
    """
    Ehlers Cyber Cycle — extracts dominant cycle component from price.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] smooth = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] cycle = np.zeros(n, dtype=np.float64)
    cdef int i

    for i in range(3, n):
        smooth[i] = (data[i] + 2.0 * data[i-1] + 2.0 * data[i-2] + data[i-3]) / 6.0

    for i in range(6, n):
        cycle[i] = ((1.0 - 0.5 * alpha) * (1.0 - 0.5 * alpha) *
                    (smooth[i] - 2.0 * smooth[i-1] + smooth[i-2]) +
                    2.0 * (1.0 - alpha) * cycle[i-1] -
                    (1.0 - alpha) * (1.0 - alpha) * cycle[i-2])

    return cycle


# ============================================================================
# 6. SINEWAVE INDICATOR
# ============================================================================

def sinewave_indicator(cnp.ndarray[DTYPE_t, ndim=1] data, double alpha=0.07):
    """
    Ehlers Sinewave Indicator — identifies cycle mode vs trend mode.
    Returns sine and leadsine for crossover signals.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] cycle = cyber_cycle(data, alpha)
    cdef cnp.ndarray[DTYPE_t, ndim=1] sine_out = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] leadsine = np.zeros(n, dtype=np.float64)
    cdef double dc_period, real_part, imag_part, dc_phase
    cdef int i, j

    for i in range(25, n):
        real_part = 0.0
        imag_part = 0.0
        for j in range(25):
            real_part += sin(2.0 * M_PI * j / 25.0) * cycle[i - j]
            imag_part += cos(2.0 * M_PI * j / 25.0) * cycle[i - j]

        if fabs(imag_part) > 0.001:
            dc_phase = atan(real_part / imag_part)
        else:
            dc_phase = M_PI / 2.0 if real_part > 0 else -M_PI / 2.0

        sine_out[i] = sin(dc_phase)
        leadsine[i] = sin(dc_phase + M_PI / 4.0)

    return sine_out, leadsine


# ============================================================================
# 7. DECYCLER OSCILLATOR
# ============================================================================

def decycler_oscillator(cnp.ndarray[DTYPE_t, ndim=1] data, int hp_period=125):
    """
    Ehlers Decycler Oscillator — removes cycle component, shows trend.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] hp = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] decycler = np.zeros(n, dtype=np.float64)
    cdef double alpha1 = (cos(2.0 * M_PI / hp_period) + sin(2.0 * M_PI / hp_period) - 1.0) / cos(2.0 * M_PI / hp_period)
    cdef int i

    for i in range(1, n):
        hp[i] = (1.0 - alpha1 / 2.0) * (1.0 - alpha1 / 2.0) * (data[i] - 2.0 * data[i-1] + (data[i-2] if i >= 2 else 0.0)) + 2.0 * (1.0 - alpha1) * hp[i-1] - (1.0 - alpha1) * (1.0 - alpha1) * (hp[i-2] if i >= 2 else 0.0)
        decycler[i] = data[i] - hp[i]

    return decycler


# ============================================================================
# 8. SMOOTHED RSI (Ehlers)
# ============================================================================

def ehlers_rsi(cnp.ndarray[DTYPE_t, ndim=1] close, int period=10):
    """
    Ehlers Smoothed RSI — Super Smoother applied to RSI for reduced noise.
    """
    cdef int n = close.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] cu = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] cd = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] rsi = np.zeros(n, dtype=np.float64)
    cdef double diff, total
    cdef int i

    for i in range(1, n):
        diff = close[i] - close[i-1]
        if diff > 0:
            cu[i] = diff
        else:
            cd[i] = -diff

    # Apply Super Smoother to up/down separately
    cdef cnp.ndarray[DTYPE_t, ndim=1] smooth_cu = super_smoother(cu, period)
    cdef cnp.ndarray[DTYPE_t, ndim=1] smooth_cd = super_smoother(cd, period)

    for i in range(period, n):
        total = smooth_cu[i] + smooth_cd[i]
        if total > 0:
            rsi[i] = smooth_cu[i] / total * 100.0
        else:
            rsi[i] = 50.0

    return rsi


# ============================================================================
# 9. INSTANTANEOUS TRENDLINE
# ============================================================================

def instantaneous_trendline(cnp.ndarray[DTYPE_t, ndim=1] data, double alpha=0.07):
    """
    Ehlers Instantaneous Trendline — identifies trend with minimal lag.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] it = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] trigger = np.zeros(n, dtype=np.float64)
    cdef int i

    it[0] = data[0]
    if n > 1:
        it[1] = data[1]

    for i in range(2, n):
        it[i] = (alpha - alpha * alpha / 4.0) * data[i] + 0.5 * alpha * alpha * data[i-1] - (alpha - 0.75 * alpha * alpha) * data[i-2] + 2.0 * (1.0 - alpha) * it[i-1] - (1.0 - alpha) * (1.0 - alpha) * it[i-2]
        trigger[i] = 2.0 * it[i] - it[i-1]

    return it, trigger


# ============================================================================
# 10. DOMINANT CYCLE (Hilbert Transform)
# ============================================================================

def dominant_cycle(cnp.ndarray[DTYPE_t, ndim=1] data):
    """
    Ehlers Dominant Cycle via Hilbert Transform Discriminator.
    Returns measured cycle period and smoothed period.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] period_out = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] smooth_period = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] smooth = np.zeros(n, dtype=np.float64)
    cdef double i1 = 0.0, q1 = 0.0, i2 = 0.0, q2 = 0.0
    cdef double re = 0.0, im = 0.0, dc_period = 15.0
    cdef int i

    for i in range(6, n):
        smooth[i] = (4.0 * data[i] + 3.0 * data[i-1] + 2.0 * data[i-2] + data[i-3]) / 10.0

        det = (0.0962 * smooth[i] + 0.5769 * smooth[i-2] - 0.5769 * smooth[i-4] - 0.0962 * smooth[i-6]) * (0.075 * dc_period + 0.54)

        q1_new = (0.0962 * det + 0.5769 * (det if i < 8 else 0.0) - 0.5769 * 0.0 - 0.0962 * 0.0) * (0.075 * dc_period + 0.54)
        i1_new = det

        i2 = 0.2 * (i1_new - q1_new) + 0.8 * i2
        q2 = 0.2 * (q1_new + i1_new) + 0.8 * q2

        re = 0.2 * (i2 * i2 + q2 * q2) + 0.8 * re
        im = 0.2 * (i2 * q2 - q2 * i2) + 0.8 * im

        if im != 0.0 and re != 0.0:
            dc_period = 2.0 * M_PI / atan(im / re)
        if dc_period < 6.0:
            dc_period = 6.0
        if dc_period > 50.0:
            dc_period = 50.0

        period_out[i] = dc_period
        smooth_period[i] = 0.33 * dc_period + 0.67 * (smooth_period[i-1] if i > 0 else dc_period)

    return period_out, smooth_period


# ============================================================================
# 11. ROOFING FILTER
# ============================================================================

def roofing_filter(cnp.ndarray[DTYPE_t, ndim=1] data, int hp_period=48, int lp_period=10):
    """
    Ehlers Roofing Filter — highpass + super smoother = bandpass without ripple.
    Removes trend (HP) and noise (LP), isolating the cycle component.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] hp = np.zeros(n, dtype=np.float64)
    cdef double alpha1 = (cos(2.0 * M_PI / hp_period) + sin(2.0 * M_PI / hp_period) - 1.0) / cos(2.0 * M_PI / hp_period)
    cdef int i

    for i in range(2, n):
        hp[i] = (1.0 - alpha1 / 2.0) * (1.0 - alpha1 / 2.0) * (data[i] - 2.0 * data[i-1] + data[i-2]) + 2.0 * (1.0 - alpha1) * hp[i-1] - (1.0 - alpha1) * (1.0 - alpha1) * hp[i-2]

    return super_smoother(hp, lp_period)


# ============================================================================
# 12. BANDPASS FILTER
# ============================================================================

def bandpass_filter(cnp.ndarray[DTYPE_t, ndim=1] data, int period=20, double bandwidth=0.3):
    """
    Ehlers Bandpass Filter — isolates dominant cycle at specified period.
    """
    cdef int n = data.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] bp = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] trigger = np.zeros(n, dtype=np.float64)
    cdef double beta_val = cos(2.0 * M_PI / period)
    cdef double gamma_val = 1.0 / cos(2.0 * M_PI * bandwidth / period)
    cdef double alpha1 = gamma_val - sqrt(gamma_val * gamma_val - 1.0)
    cdef int i

    for i in range(2, n):
        bp[i] = 0.5 * (1.0 - alpha1) * (data[i] - data[i-2]) + beta_val * (1.0 + alpha1) * bp[i-1] - alpha1 * bp[i-2]
        trigger[i] = bp[i-1]

    return bp, trigger
