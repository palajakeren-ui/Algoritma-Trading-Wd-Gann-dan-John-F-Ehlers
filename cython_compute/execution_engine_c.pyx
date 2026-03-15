# cython: boundscheck=False, wraparound=False, cdivision=True, nonecheck=False
# ============================================================================
# CENAYANG MARKET — Cython Execution Engine Acceleration Layer
#
# High-performance order execution and position management
# Optimized for ultra-low-latency trading operations
#
# Performance: <10μs per order operation
# ============================================================================

import numpy as np
cimport numpy as cnp
from libc.math cimport fabs, floor, ceil
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

ctypedef cnp.float64_t DTYPE_t
ctypedef cnp.int64_t ITYPE_t

# Order status constants
cdef int STATUS_PENDING = 0
cdef int STATUS_SUBMITTED = 1
cdef int STATUS_PARTIALLY_FILLED = 2
cdef int STATUS_FILLED = 3
cdef int STATUS_CANCELLED = 4
cdef int STATUS_REJECTED = 5

# Order side constants
cdef int SIDE_BUY = 1
cdef int SIDE_SELL = -1

# Order type constants
cdef int TYPE_MARKET = 0
cdef int TYPE_LIMIT = 1
cdef int TYPE_STOP = 2
cdef int TYPE_STOP_LIMIT = 3


# ============================================================================
# ORDER VALIDATION (Ultra-fast)
# ============================================================================

cdef inline bint validate_order_fast(
    double quantity,
    double price,
    double balance,
    double max_position_pct,
    int max_open_positions,
    int current_positions,
    double daily_pnl,
    double max_daily_loss_pct
) nogil:
    """
    Ultra-fast order validation with no Python object overhead.
    Returns 1 if valid, 0 if invalid.
    """
    cdef double trade_value
    cdef double max_value
    cdef double max_daily_loss
    
    # Check quantity
    if quantity <= 0:
        return 0
    
    # Check daily loss limit
    max_daily_loss = balance * max_daily_loss_pct
    if daily_pnl < -max_daily_loss:
        return 0
    
    # Check max open positions
    if current_positions >= max_open_positions:
        return 0
    
    # Check position size (for market orders price=0, use minimal check)
    if price > 0:
        trade_value = quantity * price
        max_value = balance * max_position_pct
        if trade_value > max_value:
            return 0
    
    return 1


def validate_order_batch(
    cnp.ndarray[DTYPE_t, ndim=1] quantities,
    cnp.ndarray[DTYPE_t, ndim=1] prices,
    double balance,
    double max_position_pct,
    int max_open_positions,
    int current_positions,
    double daily_pnl,
    double max_daily_loss_pct
):
    """
    Batch validate multiple orders at once.
    Returns array of booleans indicating validity.
    """
    cdef int n = quantities.shape[0]
    cdef cnp.ndarray[cnp.uint8_t, ndim=1] valid = np.zeros(n, dtype=np.uint8)
    cdef int i
    
    for i in range(n):
        valid[i] = validate_order_fast(
            quantities[i],
            prices[i],
            balance,
            max_position_pct,
            max_open_positions,
            current_positions,
            daily_pnl,
            max_daily_loss_pct
        )
    
    return valid.astype(bool)


# ============================================================================
# POSITION TRACKING (Optimized)
# ============================================================================

cdef struct PositionData:
    double quantity
    double entry_price
    double unrealized_pnl
    double stop_loss
    double take_profit
    int side
    int is_open


def calculate_position_pnl_batch(
    cnp.ndarray[DTYPE_t, ndim=1] quantities,
    cnp.ndarray[DTYPE_t, ndim=1] entry_prices,
    cnp.ndarray[DTYPE_t, ndim=1] current_prices,
    cnp.ndarray[ITYPE_t, ndim=1] sides  # 1=BUY, -1=SELL
):
    """
    Calculate unrealized PnL for multiple positions in batch.
    """
    cdef int n = quantities.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] pnl = np.zeros(n, dtype=np.float64)
    cdef int i
    cdef double diff
    
    for i in range(n):
        diff = current_prices[i] - entry_prices[i]
        pnl[i] = quantities[i] * diff * sides[i]
    
    return pnl


def calculate_portfolio_value(
    cnp.ndarray[DTYPE_t, ndim=1] quantities,
    cnp.ndarray[DTYPE_t, ndim=1] current_prices,
    double cash_balance
):
    """
    Calculate total portfolio value.
    """
    cdef int n = quantities.shape[0]
    cdef double total = cash_balance
    cdef int i
    
    for i in range(n):
        total += quantities[i] * current_prices[i]
    
    return total


# ============================================================================
# SLIPPAGE CALCULATION
# ============================================================================

def calculate_slippage_batch(
    cnp.ndarray[DTYPE_t, ndim=1] expected_prices,
    cnp.ndarray[DTYPE_t, ndim=1] actual_prices
):
    """
    Calculate slippage percentage for multiple fills.
    """
    cdef int n = expected_prices.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] slippage = np.zeros(n, dtype=np.float64)
    cdef int i
    
    for i in range(n):
        if expected_prices[i] > 0:
            slippage[i] = fabs(actual_prices[i] - expected_prices[i]) / expected_prices[i]
    
    return slippage


# ============================================================================
# ORDER MATCHING ENGINE (Simplified)
# ============================================================================

def match_orders(
    cnp.ndarray[DTYPE_t, ndim=1] bid_prices,
    cnp.ndarray[DTYPE_t, ndim=1] ask_prices,
    cnp.ndarray[DTYPE_t, ndim=1] bid_quantities,
    cnp.ndarray[DTYPE_t, ndim=1] ask_quantities
):
    """
    Match bid/ask orders and return matched trades.
    Returns: (matched_prices, matched_quantities, bid_indices, ask_indices)
    """
    cdef int n_bids = bid_prices.shape[0]
    cdef int n_asks = ask_prices.shape[0]
    
    # Pre-allocate max possible matches
    cdef int max_matches = n_bids if n_bids < n_asks else n_asks
    cdef cnp.ndarray[DTYPE_t, ndim=1] matched_prices = np.zeros(max_matches, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] matched_quantities = np.zeros(max_matches, dtype=np.float64)
    cdef cnp.ndarray[ITYPE_t, ndim=1] bid_indices = np.zeros(max_matches, dtype=np.int64)
    cdef cnp.ndarray[ITYPE_t, ndim=1] ask_indices = np.zeros(max_matches, dtype=np.int64)
    
    cdef int match_count = 0
    cdef int i = 0, j = 0
    cdef double match_qty, match_price
    
    # Simple matching: highest bid with lowest ask
    while i < n_bids and j < n_asks:
        if bid_prices[i] >= ask_prices[j]:
            # Match found
            match_qty = bid_quantities[i] if bid_quantities[i] < ask_quantities[j] else ask_quantities[j]
            match_price = (bid_prices[i] + ask_prices[j]) / 2.0
            
            matched_prices[match_count] = match_price
            matched_quantities[match_count] = match_qty
            bid_indices[match_count] = i
            ask_indices[match_count] = j
            match_count += 1
            
            # Update remaining quantities
            bid_quantities[i] -= match_qty
            ask_quantities[j] -= match_qty
            
            if bid_quantities[i] <= 0:
                i += 1
            if ask_quantities[j] <= 0:
                j += 1
        else:
            break
    
    return (matched_prices[:match_count], matched_quantities[:match_count],
            bid_indices[:match_count], ask_indices[:match_count])


# ============================================================================
# RISK METRICS CALCULATION
# ============================================================================

def calculate_var_batch(
    cnp.ndarray[DTYPE_t, ndim=2] returns_matrix,  # shape: (n_assets, n_periods)
    double confidence=0.95
):
    """
    Calculate Value at Risk for portfolio.
    Uses historical simulation method.
    """
    cdef int n_assets = returns_matrix.shape[0]
    cdef int n_periods = returns_matrix.shape[1]
    cdef cnp.ndarray[DTYPE_t, ndim=1] portfolio_returns = np.zeros(n_periods, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] sorted_returns
    cdef int i, j
    cdef int var_index
    cdef double var_value
    
    # Calculate equal-weighted portfolio returns
    for j in range(n_periods):
        for i in range(n_assets):
            portfolio_returns[j] += returns_matrix[i, j]
        portfolio_returns[j] /= n_assets
    
    # Sort returns
    sorted_returns = np.sort(portfolio_returns)
    
    # Find VaR index
    var_index = <int>floor(n_periods * (1.0 - confidence))
    if var_index < 0:
        var_index = 0
    if var_index >= n_periods:
        var_index = n_periods - 1
    
    var_value = sorted_returns[var_index]
    
    return var_value


def calculate_max_drawdown(cnp.ndarray[DTYPE_t, ndim=1] equity_curve):
    """
    Calculate maximum drawdown from equity curve.
    """
    cdef int n = equity_curve.shape[0]
    cdef double peak = equity_curve[0]
    cdef double max_dd = 0.0
    cdef double current_dd
    cdef int i
    
    for i in range(n):
        if equity_curve[i] > peak:
            peak = equity_curve[i]
        
        if peak > 0:
            current_dd = (peak - equity_curve[i]) / peak
            if current_dd > max_dd:
                max_dd = current_dd
    
    return max_dd


def calculate_sharpe_ratio(
    cnp.ndarray[DTYPE_t, ndim=1] returns,
    double risk_free_rate=0.0,
    int periods_per_year=252
):
    """
    Calculate annualized Sharpe ratio.
    """
    cdef int n = returns.shape[0]
    cdef double sum_ret = 0.0
    cdef double sum_sq = 0.0
    cdef double mean_ret, std_ret, excess_ret
    cdef int i
    
    if n < 2:
        return 0.0
    
    for i in range(n):
        sum_ret += returns[i]
        sum_sq += returns[i] * returns[i]
    
    mean_ret = sum_ret / n
    std_ret = (sum_sq / n - mean_ret * mean_ret) ** 0.5
    
    if std_ret == 0:
        return 0.0
    
    excess_ret = mean_ret - risk_free_rate / periods_per_year
    
    return excess_ret / std_ret * (periods_per_year ** 0.5)


# ============================================================================
# ORDER ID GENERATION (Fast)
# ============================================================================

cdef unsigned long _order_counter = 0

def generate_order_id_fast():
    """
    Generate fast sequential order ID.
    Format: ORD-XXXXXXXX
    """
    global _order_counter
    _order_counter += 1
    return f"ORD-{_order_counter:08X}"


# ============================================================================
# PRICE IMPACT MODEL
# ============================================================================

def calculate_price_impact(
    double order_quantity,
    double market_depth,
    double avg_spread,
    double volatility,
    double impact_coefficient=0.1
):
    """
    Calculate expected price impact using square-root model.
    impact = spread/2 + volatility * sqrt(quantity/depth) * coefficient
    """
    cdef double spread_impact = avg_spread / 2.0
    cdef double quantity_impact = 0.0
    
    if market_depth > 0:
        quantity_impact = volatility * (order_quantity / market_depth) ** 0.5 * impact_coefficient
    
    return spread_impact + quantity_impact


# ============================================================================
# BATCH ORDER CREATION
# ============================================================================

def create_orders_batch(
    cnp.ndarray[ITYPE_t, ndim=1] sides,        # 1=BUY, -1=SELL
    cnp.ndarray[ITYPE_t, ndim=1] order_types,  # 0=MARKET, 1=LIMIT, etc.
    cnp.ndarray[DTYPE_t, ndim=1] quantities,
    cnp.ndarray[DTYPE_t, ndim=1] prices,
    cnp.ndarray[DTYPE_t, ndim=1] stop_losses,
    cnp.ndarray[DTYPE_t, ndim=1] take_profits
):
    """
    Create multiple orders in batch for improved performance.
    Returns structured array with order data.
    """
    cdef int n = sides.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=2] orders = np.zeros((n, 7), dtype=np.float64)
    cdef int i
    
    for i in range(n):
        orders[i, 0] = <double>sides[i]
        orders[i, 1] = <double>order_types[i]
        orders[i, 2] = quantities[i]
        orders[i, 3] = prices[i]
        orders[i, 4] = stop_losses[i]
        orders[i, 5] = take_profits[i]
        orders[i, 6] = <double>STATUS_PENDING  # Initial status
    
    return orders
