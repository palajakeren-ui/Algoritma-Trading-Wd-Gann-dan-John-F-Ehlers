"""
Connectors Package
Unified exchange and broker connectivity layer.
"""
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
    DexConnector,
    create_dex_connector,
    CHAIN_CONFIG,
    DEX_PROTOCOLS,
)

__all__ = [
    # Exchange
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
    
    # MetaTrader
    'MTVersion',
    'MTCredentials',
    'MTAccountInfo',
    'MetaTraderConnector',
    'MetaTraderConnectorFactory',
    
    # FIX
    'FIXVersion',
    'FIXCredentials',
    'FIXMessage',
    'FIXMsgType',
    'FIXConnector',
    'FIXConnectorFactory',

    # DEX
    'DexConnector',
    'create_dex_connector',
    'CHAIN_CONFIG',
    'DEX_PROTOCOLS',
]
