"""
Core Enums Module - Single Source of Truth for All Trading Enums
===============================================================
This module consolidates all duplicate enum definitions across the codebase.
All modules should import enums from this file to ensure consistency.

Usage:
    from core.enums import OrderType, OrderSide, OrderStatus, PositionSide, MarginMode, BrokerType
"""
from enum import Enum


class OrderType(Enum):
    """Order type enumeration - unified across all connectors and engines."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    CANCEL = "CANCEL"


class OrderSide(Enum):
    """Order side enumeration - unified across all connectors and engines."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status enumeration - unified across all connectors and engines."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PositionSide(Enum):
    """Position side enumeration - unified across all connectors and engines."""
    LONG = "LONG"
    SHORT = "SHORT"
    BOTH = "BOTH"


class MarginMode(Enum):
    """Margin mode enumeration - for futures trading."""
    CROSS = "CROSS"
    ISOLATED = "ISOLATED"


class BrokerType(Enum):
    """Broker type enumeration - for multi-broker support."""
    BINANCE = "binance"
    MT4 = "metatrader4"
    MT5 = "metatrader5"
    BYBIT = "bybit"
    OKX = "okx"
    PAPER = "paper"
    FIX = "fix"
    OANDA = "oanda"


class TradingMode(Enum):
    """Trading mode enumeration."""
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"


class RiskMode(Enum):
    """Risk management mode enumeration."""
    DYNAMIC = "dynamic"
    FIXED = "fixed"


class ExitMode(Enum):
    """Exit strategy mode enumeration."""
    TICKS = "ticks"
    RISK_REWARD = "rr"


class SignalSource(Enum):
    """Signal source enumeration for tracking signal origin."""
    GANN_SQ9 = "gann_sq9"
    GANN_ANGLES = "gann_angles"
    GANN_WAVE = "gann_wave"
    GANN_FIBO = "gann_fibo"
    EHLERS_MAMA_FAMA = "ehlers_mama_fama"
    EHLERS_FISHER = "ehlers_fisher"
    EHLERS_BANDPASS = "ehlers_bandpass"
    EHLERS_CYBER_CYCLE = "ehlers_cyber_cycle"
    MARKET_MAKING = "market_making"
    MOMENTUM_SCALPING = "momentum_scalping"
    MEAN_REVERSION = "mean_reversion"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    ML_MODEL = "ml_model"
    ASTRO = "astro"
    FUSION = "fusion"


class ConnectionState(Enum):
    """Connection state enumeration for broker connectors."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class EngineState(Enum):
    """Engine state enumeration for trading engines."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class TimeFrame(Enum):
    """Timeframe enumeration for charts and data."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN = "1M"


# Helper functions for enum conversion
def str_to_order_side(value: str) -> OrderSide:
    """Convert string to OrderSide enum."""
    value = value.upper().strip()
    if value in ("BUY", "LONG"):
        return OrderSide.BUY
    elif value in ("SELL", "SHORT"):
        return OrderSide.SELL
    raise ValueError(f"Invalid order side: {value}")


def str_to_order_type(value: str) -> OrderType:
    """Convert string to OrderType enum."""
    value = value.upper().strip().replace("-", "_")
    mapping = {
        "MARKET": OrderType.MARKET,
        "LIMIT": OrderType.LIMIT,
        "STOP": OrderType.STOP,
        "STOP_LIMIT": OrderType.STOP_LIMIT,
        "STOP_LOSS": OrderType.STOP_LOSS,
        "TAKE_PROFIT": OrderType.TAKE_PROFIT,
        "TRAILING_STOP": OrderType.TRAILING_STOP,
    }
    if value in mapping:
        return mapping[value]
    raise ValueError(f"Invalid order type: {value}")


def str_to_order_status(value: str) -> OrderStatus:
    """Convert string to OrderStatus enum."""
    value = value.upper().strip()
    mapping = {
        "PENDING": OrderStatus.PENDING,
        "SUBMITTED": OrderStatus.SUBMITTED,
        "OPEN": OrderStatus.OPEN,
        "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
        "FILLED": OrderStatus.FILLED,
        "CANCELLED": OrderStatus.CANCELLED,
        "REJECTED": OrderStatus.REJECTED,
        "EXPIRED": OrderStatus.EXPIRED,
        "CANCELED": OrderStatus.CANCELLED,  # Alternative spelling
    }
    if value in mapping:
        return mapping[value]
    raise ValueError(f"Invalid order status: {value}")


# Export all enums
__all__ = [
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'PositionSide',
    'MarginMode',
    'BrokerType',
    'TradingMode',
    'RiskMode',
    'ExitMode',
    'SignalSource',
    'ConnectionState',
    'EngineState',
    'TimeFrame',
    'str_to_order_side',
    'str_to_order_type',
    'str_to_order_status',
]
