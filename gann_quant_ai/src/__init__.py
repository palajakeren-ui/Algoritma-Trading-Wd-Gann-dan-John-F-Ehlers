"""
Gann Quant AI - Institutional Trading System
Production-grade quantitative trading platform.

Architecture Layers:
    1. DATA LAYER      - Validation, cleaning, session control
    2. FEATURE ENGINE  - Gann, Ehlers DSP, ML features
    3. SIGNAL ENGINE   - Independent model scoring
    4. FUSION ENGINE   - Adaptive weight allocation
    5. RISK ENGINE     - CVaR, Monte Carlo, circuit breaker
    6. EXECUTION ENGINE- Slippage, retry, duplicate prevention
    7. MONITORING      - Trade journal, metrics, alerts
"""

__version__ = "2.0.0"
__author__ = "Gann Quant AI Institutional Team"
