# cython: boundscheck=False, wraparound=False, cdivision=True, nonecheck=False
# ============================================================================
# CENAYANG MARKET — Cython Connector Acceleration Layer
#
# High-performance data processing for broker/exchange connectors
# Optimized for market data parsing and order serialization
#
# Performance: <5μs per data packet processing
# ============================================================================

import numpy as np
cimport numpy as cnp
from libc.math cimport fabs, floor
from libc.string cimport memcpy, strlen
from libc.stdlib cimport malloc, free

ctypedef cnp.float64_t DTYPE_t
ctypedef cnp.int64_t ITYPE_t

# Byte constants for parsing
cdef unsigned char COMMA = 44  # ','
cdef unsigned char DOT = 46    # '.'
cdef unsigned char MINUS = 45  # '-'
cdef unsigned char COLON = 58  # ':'
cdef unsigned char NEWLINE = 10  # '\n'


# ============================================================================
# FAST STRING TO FLOAT CONVERSION
# ============================================================================

cdef inline double fast_atof(char* s) nogil:
    """
    Ultra-fast ASCII to float conversion.
    Handles negative numbers and decimal points.
    """
    cdef double result = 0.0
    cdef double factor = 1.0
    cdef int sign = 1
    cdef int decimal_seen = 0
    cdef char c
    
    # Handle negative sign
    if s[0] == MINUS:
        sign = -1
        s += 1
    
    while s[0] != 0:
        c = s[0]
        if c == DOT:
            decimal_seen = 1
        elif c >= 48 and c <= 57:  # '0' to '9'
            if decimal_seen:
                factor *= 10.0
            result = result * 10.0 + (c - 48)
        s += 1
    
    return sign * result / factor


def parse_price_string_batch(list price_strings):
    """
    Parse batch of price strings to floats.
    """
    cdef int n = len(price_strings)
    cdef cnp.ndarray[DTYPE_t, ndim=1] prices = np.zeros(n, dtype=np.float64)
    cdef bytes price_bytes
    cdef int i
    
    for i in range(n):
        price_bytes = price_strings[i].encode() if isinstance(price_strings[i], str) else price_strings[i]
        prices[i] = fast_atof(<char*>price_bytes)
    
    return prices


# ============================================================================
# FAST OHLCV DATA PARSING
# ============================================================================

def parse_ohlcv_batch(list raw_data):
    """
    Parse batch of OHLCV data from string arrays.
    Input: list of [timestamp, open, high, low, close, volume] strings
    Output: structured numpy array
    """
    cdef int n = len(raw_data)
    cdef cnp.ndarray[DTYPE_t, ndim=2] ohlcv = np.zeros((n, 6), dtype=np.float64)
    cdef list row
    cdef bytes val_bytes
    cdef int i, j
    
    for i in range(n):
        row = raw_data[i]
        for j in range(6):
            if j < len(row):
                val_bytes = str(row[j]).encode() if not isinstance(row[j], bytes) else row[j]
                ohlcv[i, j] = fast_atof(<char*>val_bytes)
    
    return ohlcv


# ============================================================================
# ORDER BOOK PROCESSING
# ============================================================================

def process_order_book(
    cnp.ndarray[DTYPE_t, ndim=1] bid_prices,
    cnp.ndarray[DTYPE_t, ndim=1] bid_quantities,
    cnp.ndarray[DTYPE_t, ndim=1] ask_prices,
    cnp.ndarray[DTYPE_t, ndim=1] ask_quantities,
    int max_levels=20
):
    """
    Process and normalize order book data.
    Returns: (spread, mid_price, bid_depth, ask_depth, imbalance)
    """
    cdef int n_bids = bid_prices.shape[0]
    cdef int n_asks = ask_prices.shape[0]
    cdef double best_bid = 0.0
    cdef double best_ask = 0.0
    cdef double bid_depth = 0.0
    cdef double ask_depth = 0.0
    cdef double spread, mid_price, imbalance
    cdef int i
    
    # Find best bid/ask
    if n_bids > 0:
        best_bid = bid_prices[0]
        for i in range(min(max_levels, n_bids)):
            bid_depth += bid_quantities[i]
    
    if n_asks > 0:
        best_ask = ask_prices[0]
        for i in range(min(max_levels, n_asks)):
            ask_depth += ask_quantities[i]
    
    # Calculate metrics
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


def calculate_vwap(
    cnp.ndarray[DTYPE_t, ndim=1] prices,
    cnp.ndarray[DTYPE_t, ndim=1] volumes
):
    """
    Calculate Volume Weighted Average Price.
    """
    cdef int n = prices.shape[0]
    cdef double sum_pv = 0.0
    cdef double sum_v = 0.0
    cdef int i
    
    for i in range(n):
        sum_pv += prices[i] * volumes[i]
        sum_v += volumes[i]
    
    if sum_v > 0:
        return sum_pv / sum_v
    return 0.0


# ============================================================================
# TRADE DATA AGGREGATION
# ============================================================================

def aggregate_trades_to_bars(
    cnp.ndarray[DTYPE_t, ndim=1] trade_prices,
    cnp.ndarray[DTYPE_t, ndim=1] trade_volumes,
    cnp.ndarray[ITYPE_t, ndim=1] trade_times,
    int bar_interval_ms=60000  # 1 minute default
):
    """
    Aggregate trade data into OHLCV bars.
    """
    cdef int n_trades = trade_prices.shape[0]
    cdef int est_bars = n_trades // 10 + 1  # Estimate number of bars
    cdef cnp.ndarray[DTYPE_t, ndim=2] bars = np.zeros((est_bars, 6), dtype=np.float64)
    cdef int bar_count = 0
    cdef int current_bar_start = -1
    cdef double bar_open, bar_high, bar_low, bar_close, bar_volume
    cdef int i
    
    if n_trades == 0:
        return bars[:0]
    
    # Initialize first bar
    current_bar_start = <int>(trade_times[0] / bar_interval_ms)
    bar_open = trade_prices[0]
    bar_high = trade_prices[0]
    bar_low = trade_prices[0]
    bar_close = trade_prices[0]
    bar_volume = 0.0
    
    for i in range(n_trades):
        # Check if we need to start a new bar
        if <int>(trade_times[i] / bar_interval_ms) != current_bar_start:
            # Save current bar
            bars[bar_count, 0] = <double>current_bar_start * bar_interval_ms
            bars[bar_count, 1] = bar_open
            bars[bar_count, 2] = bar_high
            bars[bar_count, 3] = bar_low
            bars[bar_count, 4] = bar_close
            bars[bar_count, 5] = bar_volume
            bar_count += 1
            
            # Start new bar
            current_bar_start = <int>(trade_times[i] / bar_interval_ms)
            bar_open = trade_prices[i]
            bar_high = trade_prices[i]
            bar_low = trade_prices[i]
            bar_close = trade_prices[i]
            bar_volume = trade_volumes[i]
        else:
            # Update current bar
            if trade_prices[i] > bar_high:
                bar_high = trade_prices[i]
            if trade_prices[i] < bar_low:
                bar_low = trade_prices[i]
            bar_close = trade_prices[i]
            bar_volume += trade_volumes[i]
    
    # Save last bar
    if bar_volume > 0:
        bars[bar_count, 0] = <double>current_bar_start * bar_interval_ms
        bars[bar_count, 1] = bar_open
        bars[bar_count, 2] = bar_high
        bars[bar_count, 3] = bar_low
        bars[bar_count, 4] = bar_close
        bars[bar_count, 5] = bar_volume
        bar_count += 1
    
    return bars[:bar_count]


# ============================================================================
# TICK DATA PROCESSING
# ============================================================================

def calculate_tick_statistics(
    cnp.ndarray[DTYPE_t, ndim=1] tick_prices,
    cnp.ndarray[DTYPE_t, ndim=1] tick_volumes,
    int window=100
):
    """
    Calculate rolling tick statistics.
    Returns: (tick_speed, avg_tick_size, volume_rate)
    """
    cdef int n = tick_prices.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] tick_speed = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] avg_tick_size = np.zeros(n, dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] volume_rate = np.zeros(n, dtype=np.float64)
    cdef double sum_tick_size, sum_volume
    cdef int i, j, count
    
    for i in range(window, n):
        sum_tick_size = 0.0
        sum_volume = 0.0
        count = 0
        
        for j in range(window):
            if i - j > 0:
                sum_tick_size += fabs(tick_prices[i - j] - tick_prices[i - j - 1])
                sum_volume += tick_volumes[i - j]
                count += 1
        
        if count > 0:
            tick_speed[i] = <double>count
            avg_tick_size[i] = sum_tick_size / count
            volume_rate[i] = sum_volume / count
    
    return tick_speed, avg_tick_size, volume_rate


# ============================================================================
# MARKET DATA NORMALIZATION
# ============================================================================

def normalize_price_data(
    cnp.ndarray[DTYPE_t, ndim=1] prices,
    double reference_price=0.0
):
    """
    Normalize prices relative to reference.
    """
    cdef int n = prices.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] normalized = np.zeros(n, dtype=np.float64)
    cdef double ref = reference_price if reference_price > 0 else prices[0]
    cdef int i
    
    if ref == 0:
        return normalized
    
    for i in range(n):
        normalized[i] = (prices[i] - ref) / ref
    
    return normalized


def resample_data(
    cnp.ndarray[DTYPE_t, ndim=2] ohlcv,  # [timestamp, O, H, L, C, V]
    int factor=5
):
    """
    Resample OHLCV data to lower timeframe.
    """
    cdef int n = ohlcv.shape[0]
    cdef int new_n = n // factor
    cdef cnp.ndarray[DTYPE_t, ndim=2] resampled = np.zeros((new_n, 6), dtype=np.float64)
    cdef int i, j, start_idx
    cdef double high_val, low_val, vol_sum
    
    for i in range(new_n):
        start_idx = i * factor
        resampled[i, 0] = ohlcv[start_idx, 0]  # Timestamp
        resampled[i, 1] = ohlcv[start_idx, 1]  # Open = first open
        
        high_val = ohlcv[start_idx, 2]
        low_val = ohlcv[start_idx, 3]
        vol_sum = 0.0
        
        for j in range(factor):
            if ohlcv[start_idx + j, 2] > high_val:
                high_val = ohlcv[start_idx + j, 2]
            if ohlcv[start_idx + j, 3] < low_val:
                low_val = ohlcv[start_idx + j, 3]
            vol_sum += ohlcv[start_idx + j, 5]
        
        resampled[i, 2] = high_val
        resampled[i, 3] = low_val
        resampled[i, 4] = ohlcv[start_idx + factor - 1, 4]  # Close = last close
        resampled[i, 5] = vol_sum
    
    return resampled


# ============================================================================
# ORDER SERIALIZATION
# ============================================================================

def serialize_order(
    str symbol,
    str side,
    str order_type,
    double quantity,
    double price=0.0,
    double stop_price=0.0
):
    """
    Serialize order to JSON-compatible dict (optimized).
    """
    return {
        'symbol': symbol,
        'side': side,
        'type': order_type,
        'quantity': quantity,
        'price': price,
        'stop_price': stop_price,
        'timestamp': np.datetime64('now').astype(np.int64)
    }


def serialize_order_batch(list orders):
    """
    Serialize batch of orders.
    """
    cdef int n = len(orders)
    cdef list serialized = []
    cdef int i
    
    for i in range(n):
        serialized.append(serialize_order(
            orders[i].get('symbol', ''),
            orders[i].get('side', 'BUY'),
            orders[i].get('type', 'MARKET'),
            orders[i].get('quantity', 0.0),
            orders[i].get('price', 0.0),
            orders[i].get('stop_price', 0.0)
        ))
    
    return serialized


# ============================================================================
# WEBSOCKET MESSAGE PARSING
# ============================================================================

def parse_websocket_ticker(dict data):
    """
    Parse ticker data from WebSocket message.
    """
    cdef str symbol
    cdef double bid, ask, last, volume
    
    symbol = data.get('s', data.get('symbol', ''))
    bid = float(data.get('b', data.get('bid', 0)))
    ask = float(data.get('a', data.get('ask', 0)))
    last = float(data.get('c', data.get('last', 0)))
    volume = float(data.get('v', data.get('volume', 0)))
    
    return {
        'symbol': symbol,
        'bid': bid,
        'ask': ask,
        'last': last,
        'volume': volume,
        'spread': ask - bid if ask > 0 and bid > 0 else 0,
        'mid': (ask + bid) / 2 if ask > 0 and bid > 0 else last
    }


def parse_websocket_depth(dict data):
    """
    Parse order book depth from WebSocket message.
    """
    cdef list bids = data.get('b', data.get('bids', []))
    cdef list asks = data.get('a', data.get('asks', []))
    
    cdef cnp.ndarray[DTYPE_t, ndim=1] bid_prices = np.zeros(len(bids), dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] bid_quantities = np.zeros(len(bids), dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] ask_prices = np.zeros(len(asks), dtype=np.float64)
    cdef cnp.ndarray[DTYPE_t, ndim=1] ask_quantities = np.zeros(len(asks), dtype=np.float64)
    cdef int i
    
    for i in range(len(bids)):
        bid_prices[i] = float(bids[i][0])
        bid_quantities[i] = float(bids[i][1])
    
    for i in range(len(asks)):
        ask_prices[i] = float(asks[i][0])
        ask_quantities[i] = float(asks[i][1])
    
    return bid_prices, bid_quantities, ask_prices, ask_quantities


# ============================================================================
# LATENCY TRACKING
# ============================================================================

cdef double _last_timestamp = 0.0

def track_latency(double current_timestamp):
    """
    Track processing latency between calls.
    """
    global _last_timestamp
    cdef double latency = 0.0
    
    if _last_timestamp > 0:
        latency = current_timestamp - _last_timestamp
    
    _last_timestamp = current_timestamp
    return latency


def calculate_latency_statistics(
    cnp.ndarray[DTYPE_t, ndim=1] send_times,
    cnp.ndarray[DTYPE_t, ndim=1] receive_times
):
    """
    Calculate latency statistics from send/receive timestamps.
    """
    cdef int n = send_times.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=1] latencies = np.zeros(n, dtype=np.float64)
    cdef double sum_lat = 0.0
    cdef double min_lat = 1e10
    cdef double max_lat = 0.0
    cdef double lat
    cdef int i
    
    for i in range(n):
        lat = receive_times[i] - send_times[i]
        latencies[i] = lat
        sum_lat += lat
        if lat < min_lat:
            min_lat = lat
        if lat > max_lat:
            max_lat = lat
    
    return {
        'mean': sum_lat / n if n > 0 else 0,
        'min': min_lat if min_lat < 1e10 else 0,
        'max': max_lat,
        'std': np.std(latencies)
    }
