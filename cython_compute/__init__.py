"""
Cenayang Market — Cython Compute Plane
=======================================

High-performance accelerated computing modules for trading operations.

Modules:
--------
ehlers_dsp : John F. Ehlers DSP Indicators
    - fisher_transform: Fisher Transform oscillator
    - super_smoother: Super Smoother filter
    - mama_fama: MESA Adaptive Moving Average
    - cyber_cycle: Cyber Cycle indicator
    - sinewave_indicator: Sinewave cycle indicator
    - decycler_oscillator: Decycler Oscillator
    - ehlers_rsi: Smoothed RSI
    - instantaneous_trendline: Instantaneous Trendline
    - dominant_cycle: Hilbert Transform cycle detector
    - roofing_filter: Roofing Filter (bandpass)
    - bandpass_filter: Bandpass Filter

gann_math : W.D. Gann Mathematical Analysis
    - gann_wave_levels: Gann wave projections
    - gann_fan_angles: Gann fan calculations
    - elliott_wave_targets: Elliott Wave Fibonacci
    - gann_square_of_9: Square of 9 calculator
    - gann_square_of_24: Square of 24 calculator
    - gann_square_of_52: Square of 52 calculator
    - gann_square_of_144: Square of 144 calculator
    - gann_square_of_90: Square of 90 calculator
    - gann_square_of_360: Square of 360 calculator
    - gann_box: Gann Box projections
    - gann_hexagon: Gann Hexagon geometry
    - gann_supply_demand: Supply/Demand zones
    - time_price_square: Time-Price relationships
    - planetary_harmonics: Planetary cycle harmonics

execution_engine_c : Execution Engine Acceleration
    - validate_order_batch: Batch order validation
    - calculate_position_pnl_batch: Position PnL calculation
    - calculate_portfolio_value: Portfolio value calculation
    - calculate_slippage_batch: Slippage calculation
    - match_orders: Order matching engine
    - calculate_var_batch: VaR calculation
    - calculate_max_drawdown: Maximum drawdown
    - calculate_sharpe_ratio: Sharpe ratio
    - generate_order_id_fast: Fast order ID generation
    - calculate_price_impact: Price impact model
    - create_orders_batch: Batch order creation

signal_engine_c : Signal Engine Acceleration
    - fuse_signals_weighted: Weighted signal fusion
    - apply_signal_threshold: Signal thresholding
    - momentum_signal: Momentum-based signal
    - mean_reversion_signal: Mean reversion signal
    - crossover_signal: Crossover detection
    - aggregate_mtf_signals: Multi-timeframe aggregation
    - calculate_signal_confidence: Signal confidence
    - filter_signal_noise: Noise filtering
    - regime_adaptive_signal: Regime-adaptive signals
    - calculate_signal_stats: Signal statistics

risk_engine_c : Risk Engine Acceleration
    - calculate_var_historical: Historical VaR
    - calculate_var_parametric: Parametric VaR
    - calculate_cvar: Conditional VaR (Expected Shortfall)
    - calculate_portfolio_volatility: Portfolio volatility
    - kelly_criterion: Kelly criterion position sizing
    - optimal_position_size: Optimal position size
    - calculate_drawdowns: Drawdown calculations
    - calculate_underwater_time: Underwater time
    - calculate_sharpe_ratio: Sharpe ratio
    - calculate_sortino_ratio: Sortino ratio
    - calculate_calmar_ratio: Calmar ratio
    - calculate_correlation_matrix: Correlation matrix
    - risk_parity_weights: Risk parity allocation
    - monte_carlo_var: Monte Carlo VaR
    - calculate_gross_exposure: Gross exposure
    - calculate_net_exposure: Net exposure
    - calculate_leverage: Effective leverage

connectors_c : Connector Acceleration
    - parse_price_string_batch: Batch price parsing
    - parse_ohlcv_batch: OHLCV data parsing
    - process_order_book: Order book processing
    - calculate_vwap: VWAP calculation
    - aggregate_trades_to_bars: Trade aggregation
    - calculate_tick_statistics: Tick statistics
    - normalize_price_data: Price normalization
    - resample_data: Data resampling
    - serialize_order: Order serialization
    - serialize_order_batch: Batch order serialization
    - parse_websocket_ticker: WebSocket ticker parsing
    - parse_websocket_depth: WebSocket depth parsing
    - track_latency: Latency tracking
    - calculate_latency_statistics: Latency statistics

forecast_engine_c : Forecast Engine Acceleration
    - exponential_smoothing_forecast: Simple exponential smoothing
    - double_exponential_smoothing: Holt's method
    - moving_average_forecast: Moving average forecast
    - weighted_ma_forecast: Weighted MA forecast
    - linear_regression_forecast: Linear regression
    - cycle_forecast: Cycle-based forecast
    - ensemble_forecast: Ensemble combination
    - calculate_forecast_intervals: Confidence intervals
    - predict_support_resistance: Support/Resistance levels
    - forecast_trend_strength: Trend strength
    - calculate_price_targets: Price targets
    - forecast_volatility: Volatility forecast

Performance:
------------
All functions are optimized for minimal latency:
- DSP operations: <50μs per bar
- Gann calculations: <20μs per operation
- Order operations: <10μs per order
- Signal calculations: <5μs per signal
- Risk metrics: <15μs per calculation
- Data parsing: <5μs per packet
- Forecasts: <20μs per prediction

Usage:
------
from cython_compute import ehlers_dsp, gann_math
from cython_compute import execution_engine_c, signal_engine_c, risk_engine_c
from cython_compute import connectors_c, forecast_engine_c

# Example: Fisher Transform
fisher, trigger = ehlers_dsp.fisher_transform(high, low, period=10)

# Example: Gann Square of 9
upper, lower = gann_math.gann_square_of_9(price=50000, num_levels=8)

# Example: Validate orders
valid = execution_engine_c.validate_order_batch(quantities, prices, balance, 0.1, 5, 2, 0, 0.05)

# Example: Calculate VaR
var = risk_engine_c.calculate_var_historical(returns, confidence=0.95)

# Example: Process order book
spread, mid, bid_depth, ask_depth, imbalance = connectors_c.process_order_book(
    bid_prices, bid_quantities, ask_prices, ask_quantities
)
"""

__version__ = "2.0.0"
__author__ = "Trading System"

# Try to import compiled modules
try:
    from . import ehlers_dsp
    from . import gann_math
except ImportError:
    pass

try:
    from . import execution_engine_c
except ImportError:
    pass

try:
    from . import signal_engine_c
except ImportError:
    pass

try:
    from . import risk_engine_c
except ImportError:
    pass

try:
    from . import connectors_c
except ImportError:
    pass

try:
    from . import forecast_engine_c
except ImportError:
    pass

__all__ = [
    'ehlers_dsp',
    'gann_math',
    'execution_engine_c',
    'signal_engine_c',
    'risk_engine_c',
    'connectors_c',
    'forecast_engine_c',
]
