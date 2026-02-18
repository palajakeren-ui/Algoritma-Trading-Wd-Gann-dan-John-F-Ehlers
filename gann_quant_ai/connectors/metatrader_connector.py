"""
MetaTrader Connector Module
Supports MT4 and MT5 integration for Forex trading.
"""
import numpy as np
from loguru import logger
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import socket
import json

from connectors.exchange_connector import (
    Order, Position, Balance, OrderSide, OrderType, 
    OrderStatus, MarginMode, PositionSide
)


class MTVersion(Enum):
    MT4 = "mt4"
    MT5 = "mt5"


@dataclass
class MTCredentials:
    """MetaTrader credentials."""
    login: str
    password: str
    server: str
    version: MTVersion = MTVersion.MT5
    account_type: str = "demo"  # demo or live
    broker: str = ""
    
    @property
    def is_demo(self) -> bool:
        return self.account_type.lower() == "demo"


@dataclass
class MTAccountInfo:
    """MetaTrader account information."""
    login: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    leverage: int
    currency: str
    server: str
    broker: str
    connected: bool = False


class MetaTraderConnector:
    """
    MetaTrader 4/5 connector for Forex trading.
    
    Note: Full MT4/MT5 integration requires:
    - MetaTrader terminal running
    - Expert Advisor (EA) bridge for communication
    - ZMQ or socket-based communication protocol
    
    This implementation provides the interface and fallback behavior.
    """
    
    def __init__(
        self,
        credentials: MTCredentials,
        account_id: str = "default"
    ):
        self.credentials = credentials
        self.account_id = account_id
        self.version = credentials.version
        self.is_connected = False
        self.account_info: Optional[MTAccountInfo] = None
        self._socket = None
        self._running = False
        self._callbacks: Dict[str, List[Callable]] = {
            'on_tick': [],
            'on_order': [],
            'on_position': [],
            'on_error': []
        }
        
        logger.info(f"MetaTraderConnector initialized for {credentials.version.value}")
    
    async def connect(self) -> bool:
        """
        Connect to MetaTrader terminal.
        
        In production, this would connect to an EA bridge running
        in the MT4/MT5 terminal via ZMQ or socket.
        """
        try:
            # Simulate connection for now
            # Real implementation would use ZMQ or socket to connect to EA
            
            logger.info(f"Connecting to {self.credentials.server}...")
            
            # Check MT bridge availability
            if self._check_mt_bridge():
                self.is_connected = True
                
                # Fetch account info
                self.account_info = await self._fetch_account_info()
                
                logger.success(
                    f"Connected to MT{5 if self.version == MTVersion.MT5 else 4} "
                    f"Login: {self.credentials.login}, Server: {self.credentials.server}"
                )
                return True
            else:
                # Fallback: Create mock connection for testing
                logger.warning("MT bridge not available, using simulation mode")
                self.is_connected = True
                self.account_info = MTAccountInfo(
                    login=self.credentials.login,
                    balance=10000.0,
                    equity=10000.0,
                    margin=0.0,
                    free_margin=10000.0,
                    margin_level=0.0,
                    leverage=100,
                    currency="USD",
                    server=self.credentials.server,
                    broker=self.credentials.broker,
                    connected=True
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to MetaTrader: {e}")
            self.is_connected = False
            return False
    
    def _check_mt_bridge(self) -> bool:
        """Check if MT bridge EA is running."""
        # This would check for ZMQ/socket connection to EA
        # For now, return False to use simulation mode
        return False
    
    async def _fetch_account_info(self) -> MTAccountInfo:
        """Fetch account information from MT terminal."""
        # Real implementation would query the EA
        return MTAccountInfo(
            login=self.credentials.login,
            balance=10000.0,
            equity=10000.0,
            margin=0.0,
            free_margin=10000.0,
            margin_level=0.0,
            leverage=100,
            currency="USD",
            server=self.credentials.server,
            broker=self.credentials.broker,
            connected=True
        )
    
    async def disconnect(self) -> bool:
        """Disconnect from MetaTrader."""
        self._running = False
        self.is_connected = False
        if self._socket:
            self._socket.close()
            self._socket = None
        logger.info("Disconnected from MetaTrader")
        return True
    
    async def get_balance(self) -> List[Balance]:
        """Get account balance."""
        if not self.is_connected or not self.account_info:
            return []
        
        return [Balance(
            currency=self.account_info.currency,
            free=self.account_info.free_margin,
            used=self.account_info.margin,
            total=self.account_info.balance,
            exchange=f"mt{5 if self.version == MTVersion.MT5 else 4}",
            account_id=self.account_id
        )]
    
    async def get_positions(self) -> List[Position]:
        """Get open positions."""
        if not self.is_connected:
            return []
        
        # Real implementation would query EA for positions
        # Return empty list for simulation
        return []
    
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: float = None,
        stop_loss: float = None,
        take_profit: float = None,
        comment: str = ""
    ) -> Order:
        """Create a new order."""
        if not self.is_connected:
            return Order(
                id="",
                client_order_id="",
                symbol=symbol,
                side=side,
                type=order_type,
                amount=volume,
                status=OrderStatus.REJECTED
            )
        
        # Real implementation would send order to EA
        order_id = f"MT_{int(time.time() * 1000)}"
        
        logger.info(f"Creating MT order: {side.value} {volume} {symbol} @ {price or 'market'}")
        
        return Order(
            id=order_id,
            client_order_id=order_id,
            symbol=symbol,
            side=side,
            type=order_type,
            amount=volume,
            price=price,
            stop_price=stop_loss,
            status=OrderStatus.OPEN,
            exchange=f"mt{5 if self.version == MTVersion.MT5 else 4}",
            account_id=self.account_id
        )
    
    async def cancel_order(self, ticket: int) -> bool:
        """Cancel/delete an order."""
        if not self.is_connected:
            return False
        
        logger.info(f"Cancelling MT order: {ticket}")
        return True
    
    async def modify_position(
        self,
        ticket: int,
        stop_loss: float = None,
        take_profit: float = None
    ) -> bool:
        """Modify position SL/TP."""
        if not self.is_connected:
            return False
        
        logger.info(f"Modifying MT position: {ticket}, SL={stop_loss}, TP={take_profit}")
        return True
    
    async def close_position(self, ticket: int, volume: float = None) -> bool:
        """Close a position."""
        if not self.is_connected:
            return False
        
        logger.info(f"Closing MT position: {ticket}, volume={volume}")
        return True
    
    async def close_all_positions(self, symbol: str = None) -> int:
        """Close all positions."""
        if not self.is_connected:
            return 0
        
        logger.info(f"Closing all MT positions for {symbol or 'all symbols'}")
        return 0
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current tick data for symbol."""
        if not self.is_connected:
            return {}
        
        # Real implementation would get tick from EA
        return {
            'symbol': symbol,
            'bid': 0.0,
            'ask': 0.0,
            'spread': 0.0,
            'time': datetime.now().isoformat()
        }
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100
    ) -> List[Dict]:
        """Get historical OHLCV data."""
        if not self.is_connected:
            return []
        
        # Real implementation would request data from EA
        return []
    
    def on_tick(self, callback: Callable):
        """Register tick callback."""
        self._callbacks['on_tick'].append(callback)
    
    def on_order(self, callback: Callable):
        """Register order update callback."""
        self._callbacks['on_order'].append(callback)
    
    def normalize_symbol(self, symbol: str) -> str:
        """Convert unified symbol to MT format."""
        # "EUR/USD" -> "EURUSD"
        return symbol.replace("/", "").replace("-", "").upper()
    
    def denormalize_symbol(self, symbol: str) -> str:
        """Convert MT symbol to unified format."""
        # "EURUSD" -> "EUR/USD"
        if len(symbol) == 6:
            return f"{symbol[:3]}/{symbol[3:]}"
        return symbol


class MetaTraderConnectorFactory:
    """Factory for MetaTrader connectors."""
    
    _connectors: Dict[str, MetaTraderConnector] = {}
    
    @classmethod
    def create(
        cls,
        credentials: MTCredentials,
        account_id: str = "default"
    ) -> MetaTraderConnector:
        """Create or get a MetaTrader connector."""
        key = f"{credentials.version.value}_{credentials.login}_{account_id}"
        
        if key not in cls._connectors:
            connector = MetaTraderConnector(credentials, account_id)
            cls._connectors[key] = connector
        
        return cls._connectors[key]
    
    @classmethod
    def get_connector(cls, version: str, login: str, account_id: str = "default") -> Optional[MetaTraderConnector]:
        """Get existing connector."""
        key = f"{version}_{login}_{account_id}"
        return cls._connectors.get(key)
    
    @classmethod
    def get_all_connectors(cls) -> Dict[str, MetaTraderConnector]:
        """Get all active connectors."""
        return cls._connectors.copy()


if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test MT5 connection
        creds = MTCredentials(
            login="12345678",
            password="password",
            server="Demo-Server:443",
            version=MTVersion.MT5,
            account_type="demo",
            broker="ICMarkets"
        )
        
        connector = MetaTraderConnectorFactory.create(creds)
        connected = await connector.connect()
        
        print(f"Connected: {connected}")
        if connector.account_info:
            print(f"Balance: {connector.account_info.balance}")
            print(f"Equity: {connector.account_info.equity}")
    
    asyncio.run(test())
