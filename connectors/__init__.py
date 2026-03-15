"""
Connectors Package - Ultra Low Latency Trading Infrastructure
=============================================================
Unified exchange and broker connectivity layer with HFT optimization.

Available Connectors:
├── Standard Connectors (Production Ready)
│   ├── CCXTExchangeConnector - Multi-exchange via CCXT
│   ├── MetaTraderConnector - MT4/MT5 via ZMQ bridge
│   ├── FIXConnector - FIX protocol for institutional
│   └── DEXConnector - Decentralized exchange connectivity
│
├── Ultra Low Latency Connectors (HFT Optimized)
│   ├── MT4UltraLowLatency - MT4 direct TCP (<100μs)
│   ├── MT5UltraLowLatency - MT5 native API + TCP (<100μs)
│   ├── CryptoLowLatency - Crypto exchanges WebSocket (<10ms)
│   └── FIXLowLatency - FIX protocol optimized (<1ms)
│
└── Bridge Connectors
    ├── MT4ZMQBridge - MT4 ZMQ bridge
    └── MT4ZMQBridgeAsync - Async MT4 bridge

Performance Comparison:
┌─────────────────────┬───────────────┬───────────────┐
│ Connector           │ Latency       │ Throughput    │
├─────────────────────┼───────────────┼───────────────┤
│ MT4UltraLowLatency  │ <100μs        │ 100k orders/s │
│ MT5UltraLowLatency  │ <100μs        │ 100k orders/s │
│ CryptoLowLatency    │ <10ms         │ 10k orders/s  │
│ FIXLowLatency       │ <1ms          │ 50k msg/s     │
│ Standard MT4/MT5    │ <500ms        │ 1k orders/s   │
│ CCXT Connector      │ <1s           │ 100 orders/s  │
└─────────────────────┴───────────────┴───────────────┘

Slippage Synchronization:
All connectors support dynamic slippage synchronized from frontend:
- auto_slippage: bool
- max_slippage: int
- min_slippage: int
- Slippage profiles by symbol type (forex, crypto, metals, indices)
"""

# Standard Connectors
from connectors.exchange_connector import (
    Order,
    Position,
    Balance,
    OrderSide,
    OrderType,
    OrderStatus,
    MarginMode,
    PositionSide,
    ExchangeCredentials,
    BaseExchangeConnector,
    CCXTExchangeConnector,
    ExchangeConnectorFactory
)

from connectors.metatrader_connector import (
    MTVersion,
    MTCredentials,
    MTAccountInfo,
    MetaTraderConnector,
    MetaTraderConnectorFactory
)

from connectors.fix_connector import (
    FIXVersion,
    FIXCredentials,
    FIXMessage,
    FIXMsgType,
    FIXConnector,
    FIXConnectorFactory
)

from connectors.dex_connector import (
    DEXConnector,
    Chain,
    TokenInfo,
    LiquidityPool,
    SwapQuote,
)

# MT4 Bridge Connectors
from connectors.mt4_zmq_bridge import (
    MT4Config,
    MT4Tick,
    MT4Position,
    MT4ZMQBridge,
    MT4ZMQBridgeAsync,
    ZMQCommand
)

# Ultra Low Latency Connectors
from connectors.mt4_low_latency import (
    UltraLowLatencyConfig as MT4UltraLowLatencyConfig,
    TickData as MT4TickData,
    OrderData as MT4OrderData,
    CommandType,
    ResponseStatus,
    OrderSide as HFTOrderSide,
    OrderType as HFTOrderType,
    MT4UltraLowLatency,
    MT4UltraLowLatencyAsync,
    MT4LowLatencyFactory,
    SharedMemoryTickStream,
    ConnectionPool,
    PreallocatedBuffer
)

from connectors.mt5_low_latency import (
    MT5LowLatencyConfig,
    MT5TickData,
    MT5OrderData,
    MT5CommandType,
    MT5ResponseStatus,
    MT5OrderSide,
    MT5OrderType,
    MT5OrderFilling,
    MT5UltraLowLatency,
    MT5UltraLowLatencyAsync,
    MT5LowLatencyFactory
)

from connectors.crypto_low_latency import (
    ExchangeType,
    CryptoLowLatencyConfig,
    CryptoOrderSide,
    CryptoOrderType,
    CryptoTimeInForce,
    CryptoPositionSide,
    CryptoTick,
    CryptoOrderBook,
    CryptoOrder,
    CryptoPosition,
    CryptoLowLatencyConnector,
    CryptoLowLatencyFactory
)

from connectors.fix_low_latency import (
    FIXVersion as FIXLLVersion,
    FIXLowLatencyConfig,
    FIXMsgTypeValue,
    FIXSide,
    FIXOrdType,
    FIXTimeInForce,
    FIXExecType,
    FIXOrdStatus,
    FIXOrder,
    FIXPosition,
    FIXMessage as FIXLLMessage,
    FIXLowLatencyConnector,
    FIXLowLatencyAsync,
    FIXLowLatencyFactory
)

__all__ = [
    # Standard Exchange
    'Order',
    'Position',
    'Balance',
    'OrderSide',
    'OrderType',
    'OrderStatus',
    'MarginMode',
    'PositionSide',
    'ExchangeCredentials',
    'BaseExchangeConnector',
    'CCXTExchangeConnector',
    'ExchangeConnectorFactory',
    
    # Standard MetaTrader
    'MTVersion',
    'MTCredentials',
    'MTAccountInfo',
    'MetaTraderConnector',
    'MetaTraderConnectorFactory',
    
    # Standard FIX
    'FIXVersion',
    'FIXCredentials',
    'FIXMessage',
    'FIXMsgType',
    'FIXConnector',
    'FIXConnectorFactory',
    
    # DEX
    'DEXConnector',
    'Chain',
    'TokenInfo',
    'LiquidityPool',
    'SwapQuote',
    
    # MT4 ZMQ Bridge
    'MT4Config',
    'MT4Tick',
    'MT4Position',
    'MT4ZMQBridge',
    'MT4ZMQBridgeAsync',
    'ZMQCommand',
    
    # MT4 Ultra Low Latency (HFT)
    'MT4UltraLowLatencyConfig',
    'MT4TickData',
    'MT4OrderData',
    'CommandType',
    'ResponseStatus',
    'HFTOrderSide',
    'HFTOrderType',
    'MT4UltraLowLatency',
    'MT4UltraLowLatencyAsync',
    'MT4LowLatencyFactory',
    'SharedMemoryTickStream',
    'ConnectionPool',
    'PreallocatedBuffer',
    
    # MT5 Ultra Low Latency (HFT)
    'MT5LowLatencyConfig',
    'MT5TickData',
    'MT5OrderData',
    'MT5CommandType',
    'MT5ResponseStatus',
    'MT5OrderSide',
    'MT5OrderType',
    'MT5OrderFilling',
    'MT5UltraLowLatency',
    'MT5UltraLowLatencyAsync',
    'MT5LowLatencyFactory',
    
    # Crypto Low Latency
    'ExchangeType',
    'CryptoLowLatencyConfig',
    'CryptoOrderSide',
    'CryptoOrderType',
    'CryptoTimeInForce',
    'CryptoPositionSide',
    'CryptoTick',
    'CryptoOrderBook',
    'CryptoOrder',
    'CryptoPosition',
    'CryptoLowLatencyConnector',
    'CryptoLowLatencyFactory',
    
    # FIX Low Latency
    'FIXLLVersion',
    'FIXLowLatencyConfig',
    'FIXMsgTypeValue',
    'FIXSide',
    'FIXOrdType',
    'FIXTimeInForce',
    'FIXExecType',
    'FIXOrdStatus',
    'FIXOrder',
    'FIXPosition',
    'FIXLLMessage',
    'FIXLowLatencyConnector',
    'FIXLowLatencyAsync',
    'FIXLowLatencyFactory',
]


# Connector Registry
CONNECTOR_REGISTRY = {
    'standard': {
        'exchange': CCXTExchangeConnector,
        'metatrader': MetaTraderConnector,
        'fix': FIXConnector,
        'dex': DEXConnector,
    },
    'low_latency': {
        'mt4': MT4UltraLowLatency,
        'mt5': MT5UltraLowLatency,
        'crypto': CryptoLowLatencyConnector,
        'fix': FIXLowLatencyConnector,
    },
    'bridge': {
        'mt4_zmq': MT4ZMQBridge,
    }
}


def get_connector(connector_type: str, latency_mode: str = 'standard', **kwargs):
    """
    Get a connector instance by type.
    
    Args:
        connector_type: 'exchange', 'metatrader', 'mt4', 'mt5', 'crypto', 'fix', 'dex'
        latency_mode: 'standard', 'low_latency', 'bridge'
        **kwargs: Connector configuration
        
    Returns:
        Connector instance
    """
    mode_connectors = CONNECTOR_REGISTRY.get(latency_mode, {})
    connector_class = mode_connectors.get(connector_type)
    
    if connector_class:
        return connector_class(**kwargs)
    
    raise ValueError(f"Unknown connector: {connector_type} ({latency_mode})")
