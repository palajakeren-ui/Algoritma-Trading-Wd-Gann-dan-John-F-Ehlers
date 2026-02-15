"""
Exchange Connector Module - Multi-Exchange Trading Backend
Unified interface for all supported cryptocurrency exchanges.

Supports: Binance, Bybit, OKX, KuCoin, Gate.io, Bitget, MEXC,
          Kraken, Coinbase, HTX, Crypto.com, BingX, Deribit, Phemex
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import hmac
import time
import json

# Try importing ccxt for exchange connectivity
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("ccxt not installed. Exchange connectivity will be limited.")


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MarginMode(Enum):
    CROSS = "cross"
    ISOLATED = "isolated"


class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"
    BOTH = "both"


@dataclass
class Order:
    """Universal order structure."""
    id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled: float = 0.0
    average_price: float = 0.0
    fee: float = 0.0
    fee_currency: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    exchange: str = ""
    account_id: str = ""
    leverage: int = 1
    margin_mode: MarginMode = MarginMode.CROSS
    reduce_only: bool = False
    post_only: bool = False
    time_in_force: str = "GTC"  # GTC, IOC, FOK
    raw_response: Dict = field(default_factory=dict)


@dataclass
class Position:
    """Universal position structure."""
    symbol: str
    side: PositionSide
    amount: float
    entry_price: float
    mark_price: float = 0.0
    liquidation_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    margin: float = 0.0
    leverage: int = 1
    margin_mode: MarginMode = MarginMode.CROSS
    exchange: str = ""
    account_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Balance:
    """Universal balance structure."""
    currency: str
    free: float
    used: float
    total: float
    exchange: str = ""
    account_id: str = ""


@dataclass
class ExchangeCredentials:
    """Secure credential storage."""
    api_key: str
    api_secret: str
    passphrase: str = ""
    testnet: bool = False
    endpoint: str = ""
    
    def __post_init__(self):
        # Validate credentials
        if not self.api_key or not self.api_secret:
            logger.warning("Empty API credentials provided")


class BaseExchangeConnector(ABC):
    """Abstract base class for exchange connectors."""
    
    EXCHANGE_NAME = "base"
    SUPPORTED_MODES = ["spot", "futures"]
    
    def __init__(
        self,
        credentials: ExchangeCredentials,
        account_id: str = "default",
        mode: str = "spot"
    ):
        self.credentials = credentials
        self.account_id = account_id
        self.mode = mode
        self.is_connected = False
        self._last_request_time = 0
        self._rate_limit_delay = 0.1  # 100ms between requests
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to exchange."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to exchange."""
        pass
    
    @abstractmethod
    async def get_balance(self) -> List[Balance]:
        """Get account balances."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get open positions."""
        pass
    
    @abstractmethod
    async def create_order(self, order: Order) -> Order:
        """Create a new order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get order details."""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Get all open orders."""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data for symbol."""
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book for symbol."""
        pass
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol (futures)."""
        pass
    
    @abstractmethod
    async def set_margin_mode(self, symbol: str, mode: MarginMode) -> bool:
        """Set margin mode for a symbol (futures)."""
        pass
    
    def _rate_limit(self):
        """Apply rate limiting."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to exchange format."""
        # Default: "BTC/USDT" format
        return symbol.upper().replace("_", "/").replace("-", "/")
    
    def denormalize_symbol(self, symbol: str) -> str:
        """Convert exchange symbol to unified format."""
        return symbol


class CCXTExchangeConnector(BaseExchangeConnector):
    """CCXT-based exchange connector for all supported exchanges."""
    
    EXCHANGE_MAP = {
        "binance": "binance",
        "bybit": "bybit",
        "okx": "okx",
        "kucoin": "kucoin",
        "gateio": "gateio",
        "bitget": "bitget",
        "mexc": "mexc",
        "kraken": "kraken",
        "coinbase": "coinbase",
        "htx": "huobi",
        "crypto_com": "cryptocom",
        "bingx": "bingx",
        "deribit": "deribit",
        "phemex": "phemex",
    }
    
    def __init__(
        self,
        exchange_id: str,
        credentials: ExchangeCredentials,
        account_id: str = "default",
        mode: str = "spot"
    ):
        super().__init__(credentials, account_id, mode)
        self.exchange_id = exchange_id
        self.exchange = None
        self.EXCHANGE_NAME = exchange_id
        
    async def connect(self) -> bool:
        """Connect to exchange via CCXT."""
        if not CCXT_AVAILABLE:
            logger.error("CCXT not available")
            return False
        
        try:
            ccxt_id = self.EXCHANGE_MAP.get(self.exchange_id, self.exchange_id)
            exchange_class = getattr(ccxt, ccxt_id)
            
            config = {
                'apiKey': self.credentials.api_key,
                'secret': self.credentials.api_secret,
                'enableRateLimit': True,
            }
            
            if self.credentials.passphrase:
                config['password'] = self.credentials.passphrase
            
            if self.credentials.testnet:
                config['sandbox'] = True
            
            if self.credentials.endpoint:
                config['urls'] = {'api': self.credentials.endpoint}
            
            # Set futures mode if needed
            if self.mode == "futures":
                config['options'] = {
                    'defaultType': 'swap' if ccxt_id in ['binance', 'bybit', 'okx'] else 'future'
                }
            
            self.exchange = exchange_class(config)
            
            # Test connection by fetching balance
            await self.exchange.load_markets()
            
            self.is_connected = True
            logger.success(f"Connected to {self.exchange_id} ({self.mode} mode)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_id}: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from exchange."""
        self.is_connected = False
        self.exchange = None
        logger.info(f"Disconnected from {self.exchange_id}")
        return True
    
    async def get_balance(self) -> List[Balance]:
        """Get account balances."""
        if not self.is_connected or not self.exchange:
            return []
        
        try:
            self._rate_limit()
            balance_data = await self.exchange.fetch_balance()
            
            balances = []
            for currency, data in balance_data.get('total', {}).items():
                if data and data > 0:
                    balances.append(Balance(
                        currency=currency,
                        free=balance_data['free'].get(currency, 0),
                        used=balance_data['used'].get(currency, 0),
                        total=data,
                        exchange=self.exchange_id,
                        account_id=self.account_id
                    ))
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to fetch balance from {self.exchange_id}: {e}")
            return []
    
    async def get_positions(self) -> List[Position]:
        """Get open positions (futures mode)."""
        if not self.is_connected or not self.exchange:
            return []
        
        if self.mode != "futures":
            return []
        
        try:
            self._rate_limit()
            positions_data = await self.exchange.fetch_positions()
            
            positions = []
            for pos in positions_data:
                if pos.get('contracts', 0) > 0 or pos.get('notional', 0) != 0:
                    positions.append(Position(
                        symbol=pos.get('symbol', ''),
                        side=PositionSide.LONG if pos.get('side') == 'long' else PositionSide.SHORT,
                        amount=abs(pos.get('contracts', 0)),
                        entry_price=pos.get('entryPrice', 0),
                        mark_price=pos.get('markPrice', 0),
                        liquidation_price=pos.get('liquidationPrice', 0),
                        unrealized_pnl=pos.get('unrealizedPnl', 0),
                        realized_pnl=pos.get('realizedPnl', 0),
                        margin=pos.get('initialMargin', 0),
                        leverage=int(pos.get('leverage', 1)),
                        margin_mode=MarginMode.ISOLATED if pos.get('marginMode') == 'isolated' else MarginMode.CROSS,
                        exchange=self.exchange_id,
                        account_id=self.account_id
                    ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to fetch positions from {self.exchange_id}: {e}")
            return []
    
    async def create_order(self, order: Order) -> Order:
        """Create a new order."""
        if not self.is_connected or not self.exchange:
            order.status = OrderStatus.REJECTED
            return order
        
        try:
            self._rate_limit()
            
            params = {}
            if order.reduce_only:
                params['reduceOnly'] = True
            if order.post_only:
                params['postOnly'] = True
            
            ccxt_order = await self.exchange.create_order(
                symbol=order.symbol,
                type=order.type.value,
                side=order.side.value,
                amount=order.amount,
                price=order.price if order.type == OrderType.LIMIT else None,
                params=params
            )
            
            order.id = ccxt_order.get('id', '')
            order.status = OrderStatus.OPEN
            order.exchange = self.exchange_id
            order.account_id = self.account_id
            order.raw_response = ccxt_order
            
            logger.info(f"Order created: {order.id} on {self.exchange_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create order on {self.exchange_id}: {e}")
            order.status = OrderStatus.REJECTED
            return order
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        if not self.is_connected or not self.exchange:
            return False
        
        try:
            self._rate_limit()
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order {order_id} cancelled on {self.exchange_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id} on {self.exchange_id}: {e}")
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get order details."""
        if not self.is_connected or not self.exchange:
            return None
        
        try:
            self._rate_limit()
            ccxt_order = await self.exchange.fetch_order(order_id, symbol)
            
            return Order(
                id=ccxt_order.get('id', ''),
                client_order_id=ccxt_order.get('clientOrderId', ''),
                symbol=ccxt_order.get('symbol', ''),
                side=OrderSide.BUY if ccxt_order.get('side') == 'buy' else OrderSide.SELL,
                type=OrderType(ccxt_order.get('type', 'market')),
                amount=ccxt_order.get('amount', 0),
                price=ccxt_order.get('price'),
                status=OrderStatus(ccxt_order.get('status', 'open')),
                filled=ccxt_order.get('filled', 0),
                average_price=ccxt_order.get('average', 0),
                fee=ccxt_order.get('fee', {}).get('cost', 0),
                exchange=self.exchange_id,
                account_id=self.account_id
            )
        except Exception as e:
            logger.error(f"Failed to get order {order_id} from {self.exchange_id}: {e}")
            return None
    
    async def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Get all open orders."""
        if not self.is_connected or not self.exchange:
            return []
        
        try:
            self._rate_limit()
            ccxt_orders = await self.exchange.fetch_open_orders(symbol)
            
            orders = []
            for co in ccxt_orders:
                orders.append(Order(
                    id=co.get('id', ''),
                    client_order_id=co.get('clientOrderId', ''),
                    symbol=co.get('symbol', ''),
                    side=OrderSide.BUY if co.get('side') == 'buy' else OrderSide.SELL,
                    type=OrderType(co.get('type', 'market')),
                    amount=co.get('amount', 0),
                    price=co.get('price'),
                    status=OrderStatus.OPEN,
                    filled=co.get('filled', 0),
                    exchange=self.exchange_id,
                    account_id=self.account_id
                ))
            
            return orders
        except Exception as e:
            logger.error(f"Failed to get open orders from {self.exchange_id}: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data for symbol."""
        if not self.is_connected or not self.exchange:
            return {}
        
        try:
            self._rate_limit()
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker.get('last', 0),
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'high': ticker.get('high', 0),
                'low': ticker.get('low', 0),
                'volume': ticker.get('quoteVolume', 0),
                'change_pct': ticker.get('percentage', 0),
                'timestamp': ticker.get('timestamp', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol} from {self.exchange_id}: {e}")
            return {}
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book for symbol."""
        if not self.is_connected or not self.exchange:
            return {}
        
        try:
            self._rate_limit()
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            return {
                'symbol': symbol,
                'bids': orderbook.get('bids', [])[:limit],
                'asks': orderbook.get('asks', [])[:limit],
                'timestamp': orderbook.get('timestamp', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol} from {self.exchange_id}: {e}")
            return {}
    
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol (futures)."""
        if not self.is_connected or not self.exchange:
            return False
        
        if self.mode != "futures":
            return False
        
        try:
            self._rate_limit()
            await self.exchange.set_leverage(leverage, symbol)
            logger.info(f"Set leverage to {leverage}x for {symbol} on {self.exchange_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage on {self.exchange_id}: {e}")
            return False
    
    async def set_margin_mode(self, symbol: str, mode: MarginMode) -> bool:
        """Set margin mode for a symbol (futures)."""
        if not self.is_connected or not self.exchange:
            return False
        
        if self.mode != "futures":
            return False
        
        try:
            self._rate_limit()
            await self.exchange.set_margin_mode(mode.value, symbol)
            logger.info(f"Set margin mode to {mode.value} for {symbol} on {self.exchange_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set margin mode on {self.exchange_id}: {e}")
            return False


class ExchangeConnectorFactory:
    """Factory for creating exchange connectors."""
    
    _connectors: Dict[str, BaseExchangeConnector] = {}
    
    @classmethod
    def create(
        cls,
        exchange_id: str,
        credentials: ExchangeCredentials,
        account_id: str = "default",
        mode: str = "spot"
    ) -> BaseExchangeConnector:
        """Create or get an exchange connector."""
        key = f"{exchange_id}_{account_id}_{mode}"
        
        if key not in cls._connectors:
            connector = CCXTExchangeConnector(
                exchange_id=exchange_id,
                credentials=credentials,
                account_id=account_id,
                mode=mode
            )
            cls._connectors[key] = connector
        
        return cls._connectors[key]
    
    @classmethod
    def get_connector(cls, exchange_id: str, account_id: str = "default", mode: str = "spot") -> Optional[BaseExchangeConnector]:
        """Get existing connector."""
        key = f"{exchange_id}_{account_id}_{mode}"
        return cls._connectors.get(key)
    
    @classmethod
    def remove_connector(cls, exchange_id: str, account_id: str = "default", mode: str = "spot"):
        """Remove a connector."""
        key = f"{exchange_id}_{account_id}_{mode}"
        if key in cls._connectors:
            del cls._connectors[key]
    
    @classmethod
    def get_all_connectors(cls) -> Dict[str, BaseExchangeConnector]:
        """Get all active connectors."""
        return cls._connectors.copy()
    
    @classmethod
    def get_supported_exchanges(cls) -> List[Dict]:
        """Get list of supported exchanges."""
        return [
            {"id": "binance", "name": "Binance", "type": "both", "hasPassphrase": False},
            {"id": "bybit", "name": "Bybit", "type": "both", "hasPassphrase": False},
            {"id": "okx", "name": "OKX", "type": "both", "hasPassphrase": True},
            {"id": "kucoin", "name": "KuCoin", "type": "both", "hasPassphrase": True},
            {"id": "gateio", "name": "Gate.io", "type": "both", "hasPassphrase": False},
            {"id": "bitget", "name": "Bitget", "type": "both", "hasPassphrase": True},
            {"id": "mexc", "name": "MEXC", "type": "both", "hasPassphrase": False},
            {"id": "kraken", "name": "Kraken", "type": "both", "hasPassphrase": False},
            {"id": "coinbase", "name": "Coinbase", "type": "spot", "hasPassphrase": False},
            {"id": "htx", "name": "HTX", "type": "both", "hasPassphrase": False},
            {"id": "crypto_com", "name": "Crypto.com", "type": "both", "hasPassphrase": False},
            {"id": "bingx", "name": "BingX", "type": "both", "hasPassphrase": False},
            {"id": "deribit", "name": "Deribit", "type": "futures", "hasPassphrase": False},
            {"id": "phemex", "name": "Phemex", "type": "both", "hasPassphrase": False},
        ]


if __name__ == "__main__":
    # Test
    print("Supported Exchanges:")
    for ex in ExchangeConnectorFactory.get_supported_exchanges():
        print(f"  - {ex['name']} ({ex['id']}): {ex['type']}")
