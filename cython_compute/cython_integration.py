"""
Cython Integration Layer
========================

Provides seamless integration between Python core modules and Cython acceleration.
Automatically falls back to pure Python if Cython modules are not compiled.

Usage in core/ modules:
    from cython_compute.cython_integration import (
        accelerated_validate_order,
        accelerated_calculate_pnl,
        accelerated_var,
        accelerated_sharpe,
        accelerated_signal_fusion,
        accelerated_risk_check,
        CYTHON_AVAILABLE
    )
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Try to import Cython modules
CYTHON_AVAILABLE = False
try:
    import execution_engine_c
    import signal_engine_c
    import risk_engine_c
    import forecast_engine_c
    import connectors_c
    CYTHON_AVAILABLE = True
    logger.info("Cython acceleration modules loaded successfully")
except ImportError as e:
    logger.warning(f"Cython modules not available, using pure Python fallback: {e}")


# ============================================================================
# EXECUTION ENGINE ACCELERATION
# ============================================================================

def accelerated_validate_order_batch(
    quantities: np.ndarray,
    prices: np.ndarray,
    balance: float,
    max_position_pct: float,
    max_open_positions: int,
    current_positions: int,
    daily_pnl: float,
    max_daily_loss_pct: float
) -> np.ndarray:
    """
    Batch validate orders using Cython acceleration.
    Falls back to pure Python if Cython not available.
    """
    if CYTHON_AVAILABLE:
        return execution_engine_c.validate_order_batch(
            quantities, prices, balance, max_position_pct,
            max_open_positions, current_positions, daily_pnl, max_daily_loss_pct
        )
    
    # Pure Python fallback
    valid = np.ones(len(quantities), dtype=bool)
    max_daily_loss = balance * max_daily_loss_pct
    max_value = balance * max_position_pct
    
    for i in range(len(quantities)):
        if quantities[i] <= 0:
            valid[i] = False
        if daily_pnl < -max_daily_loss:
            valid[i] = False
        if current_positions >= max_open_positions:
            valid[i] = False
        if prices[i] > 0 and quantities[i] * prices[i] > max_value:
            valid[i] = False
    
    return valid


def accelerated_calculate_pnl_batch(
    quantities: np.ndarray,
    entry_prices: np.ndarray,
    current_prices: np.ndarray,
    sides: np.ndarray
) -> np.ndarray:
    """Calculate unrealized PnL for multiple positions."""
    if CYTHON_AVAILABLE:
        return execution_engine_c.calculate_position_pnl_batch(
            quantities, entry_prices, current_prices, sides
        )
    
    # Pure Python fallback
    diff = current_prices - entry_prices
    return quantities * diff * sides


def accelerated_max_drawdown(equity_curve: np.ndarray) -> float:
    """Calculate maximum drawdown."""
    if CYTHON_AVAILABLE:
        return execution_engine_c.calculate_max_drawdown(equity_curve)
    
    # Pure Python fallback
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        if peak > 0:
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def accelerated_sharpe_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """Calculate annualized Sharpe ratio."""
    if CYTHON_AVAILABLE:
        return execution_engine_c.calculate_sharpe_ratio(
            returns, risk_free_rate, periods_per_year
        )
    
    # Pure Python fallback
    if len(returns) < 2:
        return 0.0
    mean_ret = np.mean(returns)
    std_ret = np.std(returns)
    if std_ret == 0:
        return 0.0
    return (mean_ret * periods_per_year - risk_free_rate) / (std_ret * np.sqrt(periods_per_year))


# ============================================================================
# SIGNAL ENGINE ACCELERATION
# ============================================================================

def accelerated_signal_fusion(
    signals: np.ndarray,
    weights: np.ndarray
) -> np.ndarray:
    """Fuse multiple signals using weighted average."""
    if CYTHON_AVAILABLE:
        return signal_engine_c.fuse_signals_weighted(signals, weights)
    
    # Pure Python fallback
    weight_sum = np.sum(weights)
    if weight_sum == 0:
        return np.zeros(signals.shape[1])
    return np.average(signals, axis=0, weights=weights)


def accelerated_momentum_signal(close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate momentum-based trading signal."""
    if CYTHON_AVAILABLE:
        return signal_engine_c.momentum_signal(close, period)
    
    # Pure Python fallback
    n = len(close)
    signal = np.zeros(n)
    momentum = np.zeros(n)
    
    for i in range(period, n):
        momentum[i] = close[i] - close[i - period]
    
    for i in range(period * 2, n):
        window = momentum[i-period+1:i+1]
        max_mom = np.max(window)
        min_mom = np.min(window)
        range_mom = max_mom - min_mom
        if range_mom > 0:
            signal[i] = 2.0 * (momentum[i] - min_mom) / range_mom - 1.0
    
    return signal


def accelerated_atr(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> np.ndarray:
    """Calculate Average True Range."""
    if CYTHON_AVAILABLE:
        return signal_engine_c.calculate_atr(high, low, close, period)
    
    # Pure Python fallback
    n = len(high)
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]
    
    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
    
    atr = np.zeros(n)
    atr[period-1] = np.mean(tr[:period])
    for i in range(period, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    
    return atr


def accelerated_sl_tp_levels(
    current_price: float,
    atr_value: float,
    direction: int,
    sl_multiplier: float = 1.5,
    tp_multiplier: float = 3.0
) -> Tuple[float, float, float]:
    """Calculate Stop Loss and Take Profit levels."""
    if CYTHON_AVAILABLE:
        return signal_engine_c.calculate_sl_tp_levels(
            current_price, atr_value, direction, sl_multiplier, tp_multiplier
        )
    
    # Pure Python fallback
    entry = current_price
    if direction == 1:  # BUY
        stop_loss = current_price - (atr_value * sl_multiplier)
        take_profit = current_price + (atr_value * tp_multiplier)
    elif direction == -1:  # SELL
        stop_loss = current_price + (atr_value * sl_multiplier)
        take_profit = current_price - (atr_value * tp_multiplier)
    else:
        stop_loss = current_price
        take_profit = current_price
    
    return entry, stop_loss, take_profit


# ============================================================================
# RISK ENGINE ACCELERATION
# ============================================================================

def accelerated_var_historical(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Calculate Value at Risk using historical simulation."""
    if CYTHON_AVAILABLE:
        return risk_engine_c.calculate_var_historical(returns, confidence)
    
    # Pure Python fallback
    sorted_returns = np.sort(returns)
    var_index = int((1.0 - confidence) * len(returns))
    return -sorted_returns[var_index]


def accelerated_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Calculate Conditional VaR (Expected Shortfall)."""
    if CYTHON_AVAILABLE:
        return risk_engine_c.calculate_cvar(returns, confidence)
    
    # Pure Python fallback
    sorted_returns = np.sort(returns)
    cutoff_index = int((1.0 - confidence) * len(returns))
    if cutoff_index < 1:
        cutoff_index = 1
    return -np.mean(sorted_returns[:cutoff_index])


def accelerated_kelly_criterion(
    win_rate: float,
    avg_win: float,
    avg_loss: float
) -> float:
    """Calculate optimal position size using Kelly Criterion."""
    if CYTHON_AVAILABLE:
        return risk_engine_c.kelly_criterion(win_rate, avg_win, avg_loss)
    
    # Pure Python fallback
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0
    r_ratio = avg_win / avg_loss
    kelly = win_rate - (1.0 - win_rate) / r_ratio
    return max(0.0, min(kelly, 0.25))


def accelerated_trade_risk_batch(
    quantities: np.ndarray,
    prices: np.ndarray,
    account_balance: float,
    max_position_size_pct: float,
    max_risk_per_trade_pct: float,
    stop_losses: np.ndarray,
    sides: np.ndarray,
    max_open_positions: int,
    current_open_positions: int,
    current_drawdown_pct: float,
    max_drawdown_pct: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Batch trade risk check."""
    if CYTHON_AVAILABLE:
        return risk_engine_c.check_trade_risk_batch(
            quantities, prices, account_balance, max_position_size_pct,
            max_risk_per_trade_pct, stop_losses, sides, max_open_positions,
            current_open_positions, current_drawdown_pct, max_drawdown_pct
        )
    
    # Pure Python fallback
    n = len(quantities)
    passed = np.ones(n, dtype=bool)
    risk_level = np.zeros(n, dtype=np.int8)
    adjusted_size = quantities.copy()
    
    max_position_value = account_balance * (max_position_size_pct / 100.0)
    
    for i in range(n):
        position_value = quantities[i] * prices[i]
        position_pct = (position_value / account_balance) * 100.0
        
        if current_open_positions >= max_open_positions:
            passed[i] = False
            risk_level[i] = 2
            continue
        
        if position_pct > max_position_size_pct:
            adjusted_size[i] = max_position_value / prices[i] if prices[i] > 0 else 0.0
            passed[i] = False
            risk_level[i] = 1
        
        if stop_losses[i] > 0:
            if sides[i] == 1:
                risk_per_unit = prices[i] - stop_losses[i]
            else:
                risk_per_unit = stop_losses[i] - prices[i]
            
            total_risk = abs(risk_per_unit * quantities[i])
            risk_pct = (total_risk / account_balance) * 100.0
            
            if risk_pct > max_risk_per_trade_pct:
                max_risk_amount = account_balance * (max_risk_per_trade_pct / 100.0)
                if risk_per_unit > 0:
                    adjusted_size[i] = max_risk_amount / risk_per_unit
                passed[i] = False
                risk_level[i] = 2
    
    return passed, risk_level, adjusted_size


# ============================================================================
# FORECAST ENGINE ACCELERATION
# ============================================================================

def accelerated_gann_price_levels(
    current_price: float,
    num_levels: int = 8
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Gann Square of 9 price levels."""
    if CYTHON_AVAILABLE:
        return forecast_engine_c.gann_price_levels(current_price, num_levels)
    
    # Pure Python fallback
    sqrt_price = np.sqrt(current_price)
    resistances = np.zeros(num_levels)
    supports = np.zeros(num_levels)
    
    for i in range(num_levels):
        angle = 45.0 * (i + 1)
        increment = angle / 180.0
        
        resistances[i] = (sqrt_price + increment) ** 2
        support_price = (sqrt_price - increment) ** 2
        supports[i] = support_price if support_price > 0 else 0.0
    
    return resistances, supports


def accelerated_ensemble_forecast(
    close: np.ndarray,
    days_ahead: int = 7,
    gann_weight: float = 0.35,
    stat_weight: float = 0.35,
    cycle_weight: float = 0.30
) -> Tuple[float, float, float]:
    """Ensemble forecast combining multiple methods."""
    if CYTHON_AVAILABLE:
        return forecast_engine_c.ensemble_forecast_combined(
            close, days_ahead, gann_weight, stat_weight, cycle_weight
        )
    
    # Pure Python fallback
    current_price = close[-1]
    sqrt_price = np.sqrt(current_price)
    
    # Gann target
    gann_target = (sqrt_price + 0.25) ** 2
    
    # Statistical forecast
    returns = np.diff(close) / close[:-1]
    mean_return = np.mean(returns)
    expected_return = mean_return * days_ahead
    stat_predicted = current_price * (1.0 + expected_return)
    
    # Trend detection
    ema20 = np.mean(close[-20:]) if len(close) >= 20 else current_price
    ema50 = np.mean(close[-50:]) if len(close) >= 50 else current_price
    
    if current_price > ema20 > ema50:
        trend_direction = 1.0
    elif current_price < ema20 < ema50:
        trend_direction = -1.0
    else:
        trend_direction = 0.0
    
    # Ensemble
    ensemble_price = (
        gann_target * gann_weight +
        stat_predicted * stat_weight +
        current_price * (1.0 + trend_direction * 0.02) * cycle_weight
    )
    
    confidence = 0.6 + abs(trend_direction) * 0.1
    
    return ensemble_price, confidence, trend_direction


# ============================================================================
# CONNECTOR ACCELERATION
# ============================================================================

def accelerated_process_order_book(
    bid_prices: np.ndarray,
    bid_quantities: np.ndarray,
    ask_prices: np.ndarray,
    ask_quantities: np.ndarray,
    max_levels: int = 20
) -> Tuple[float, float, float, float, float]:
    """Process and normalize order book data."""
    if CYTHON_AVAILABLE:
        return connectors_c.process_order_book(
            bid_prices, bid_quantities, ask_prices, ask_quantities, max_levels
        )
    
    # Pure Python fallback
    best_bid = bid_prices[0] if len(bid_prices) > 0 else 0.0
    best_ask = ask_prices[0] if len(ask_prices) > 0 else 0.0
    
    bid_depth = np.sum(bid_quantities[:max_levels])
    ask_depth = np.sum(ask_quantities[:max_levels])
    
    if best_bid > 0 and best_ask > 0:
        spread = best_ask - best_bid
        mid_price = (best_bid + best_ask) / 2.0
    else:
        spread = 0.0
        mid_price = 0.0
    
    if bid_depth + ask_depth > 0:
        imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
    else:
        imbalance = 0.0
    
    return spread, mid_price, bid_depth, ask_depth, imbalance


def accelerated_vwap(prices: np.ndarray, volumes: np.ndarray) -> float:
    """Calculate Volume Weighted Average Price."""
    if CYTHON_AVAILABLE:
        return connectors_c.calculate_vwap(prices, volumes)
    
    # Pure Python fallback
    sum_pv = np.sum(prices * volumes)
    sum_v = np.sum(volumes)
    return sum_pv / sum_v if sum_v > 0 else 0.0


# ============================================================================
# MODULE STATUS
# ============================================================================

def get_cython_status() -> Dict[str, Any]:
    """Get status of Cython acceleration modules."""
    status = {
        'cython_available': CYTHON_AVAILABLE,
        'modules': {}
    }
    
    if CYTHON_AVAILABLE:
        modules = ['execution_engine_c', 'signal_engine_c', 'risk_engine_c', 
                   'forecast_engine_c', 'connectors_c']
        for mod in modules:
            try:
                __import__(f'cython_compute.{mod}', fromlist=[''])
                status['modules'][mod] = 'loaded'
            except ImportError:
                status['modules'][mod] = 'not_available'
    else:
        status['modules'] = {'all': 'pure_python_fallback'}
    
    return status


if __name__ == "__main__":
    # Quick test
    print(f"Cython Available: {CYTHON_AVAILABLE}")
    print(f"Status: {get_cython_status()}")
    
    # Test signal fusion
    signals = np.array([[0.5, 0.6, 0.4], [0.3, 0.4, 0.5]])
    weights = np.array([0.6, 0.4])
    fused = accelerated_signal_fusion(signals, weights)
    print(f"Fused Signal: {fused}")
    
    # Test VaR
    returns = np.random.randn(100) * 0.02
    var = accelerated_var_historical(returns)
    print(f"VaR (95%): {var:.4f}")
    
    # Test Gann levels
    resistances, supports = accelerated_gann_price_levels(50000.0)
    print(f"Gann R1: {resistances[0]:.2f}, S1: {supports[0]:.2f}")
