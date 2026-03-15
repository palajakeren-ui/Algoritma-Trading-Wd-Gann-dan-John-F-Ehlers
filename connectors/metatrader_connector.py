"""
MetaTrader 5 Connector with ZMQ Bridge
Enables real-time connection to MT5 terminal through Expert Advisor bridge.

Architecture:
- MT5 Terminal runs an EA that publishes data via ZMQ
- This connector subscribes to the ZMQ feed and sends commands
- Supports both PUSH/PULL and PUB/SUB patterns
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
import json
import queue
from datetime import datetime, timedelta

# ZMQ imports with fallback
try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
    logger.warning("zmq not installed. MT5 connector will use simulation mode. Install with: pip install pyzmq")


class MTVersion(Enum):
    MT4 = 4
    MT5 = 5


@dataclass
class MTCredentials:
    """MetaTrader account credentials."""
    login: int
    password: str
    server: str
    broker: str = ""


@dataclass
class MTAccountInfo:
    """MetaTrader account information."""
    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    profit: float
    currency: str = "USD"


@dataclass
class MTOrder:
    """MetaTrader order structure."""
    ticket: int
    symbol: str
    type: str  # BUY, SELL
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    open_time: datetime
    comment: str = ""


class MetaTraderConnector:
    """
    MetaTrader 5/4 connector using ZMQ bridge.
    
    The connector communicates with an Expert Advisor running in MT5
    that acts as a ZMQ bridge for order execution and data streaming.
    
    Required EA Configuration (MT5 side):
    - EA runs ZMQ PUSH socket on configured port for sending commands
    - EA runs ZMQ PULL socket for receiving responses
    - EA runs ZMQ PUB socket for streaming price data
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize MetaTrader connector.
        
        Args:
            config: Configuration dict with:
                - host: ZMQ host (default 'localhost')
                - command_port: Command port (default 32768)
                - data_port: Data streaming port (default 32769)
                - timeout_ms: Socket timeout in ms (default 5000)
        """
        self.config = config or {}
        self.host = self.config.get('host', 'localhost')
        self.command_port = self.config.get('command_port', 32768)
        self.data_port = self.config.get('data_port', 32769)
        self.timeout_ms = self.config.get('timeout_ms', 5000)
        
        self._connected = False
        self._context = None
        self._command_socket = None
        self._data_socket = None
        self._receive_thread = None
        self._running = False
        self._response_queue = queue.Queue()
        self._price_callbacks: Dict[str, List[Callable]] = {}
        self._account_info: Optional[MTAccountInfo] = None
        self._positions: Dict[int, MTOrder] = {}
        self._lock = threading.Lock()
        
        logger.info(f"MetaTraderConnector initialized: {self.host}:{self.command_port}")
    
    def connect(self) -> bool:
        """
        Establish connection to MT5 EA bridge.
        
        Returns:
            bool: True if connection successful
        """
        if not ZMQ_AVAILABLE:
            logger.warning("ZMQ not available, using simulation mode")
            return self._init_simulation_mode()
        
        try:
            # Create ZMQ context
            self._context = zmq.Context()
            
            # Command socket (REQ/REP pattern for commands)
            self._command_socket = self._context.socket(zmq.REQ)
            self._command_socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
            self._command_socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
            self._command_socket.connect(f"tcp://{self.host}:{self.command_port}")
            
            # Data socket (SUB pattern for streaming)
            self._data_socket = self._context.socket(zmq.SUB)
            self._data_socket.setsockopt(zmq.RCVTIMEO, 1000)  # Shorter timeout for streaming
            self._data_socket.connect(f"tcp://{self.host}:{self.data_port}")
            self._data_socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all topics
            
            # Start receive thread
            self._running = True
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            # Test connection
            response = self._send_command({"action": "PING"})
            if response and response.get("status") == "OK":
                self._connected = True
                logger.success("Connected to MT5 EA bridge")
                
                # Get initial account info
                self._sync_account_info()
                return True
            else:
                logger.error("Failed to connect: Invalid response from EA")
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from MT5 EA bridge."""
        self._running = False
        
        if self._receive_thread:
            self._receive_thread.join(timeout=2)
        
        if self._command_socket:
            self._command_socket.close()
        
        if self._data_socket:
            self._data_socket.close()
        
        if self._context:
            self._context.term()
        
        self._connected = False
        logger.info("Disconnected from MT5")
        return True
    
    def _init_simulation_mode(self) -> bool:
        """Initialize simulation mode for testing without ZMQ."""
        self._connected = True
        self._simulation_mode = True
        logger.warning("MetaTrader running in SIMULATION mode")
        return True
    
    def _send_command(self, command: Dict, timeout_ms: int = None) -> Optional[Dict]:
        """
        Send command to MT5 EA and wait for response.
        
        Args:
            command: Command dictionary
            timeout_ms: Optional timeout override
            
        Returns:
            Response dictionary or None on failure
        """
        if hasattr(self, '_simulation_mode') and self._simulation_mode:
            return self._simulate_command(command)
        
        if not self._command_socket:
            logger.error("Not connected to MT5")
            return None
        
        try:
            # Send command
            message = json.dumps(command).encode('utf-8')
            self._command_socket.send(message)
            
            # Receive response
            response = self._command_socket.recv_json()
            return response
            
        except zmq.error.Again:
            logger.error("Command timeout")
            return None
        except Exception as e:
            logger.error(f"Command error: {e}")
            return None
    
    def _receive_loop(self):
        """Background thread for receiving streaming data."""
        while self._running:
            try:
                if self._data_socket:
                    message = self._data_socket.recv_json(flags=zmq.NOBLOCK)
                    self._process_streaming_data(message)
            except zmq.error.Again:
                # No data available, continue
                time.sleep(0.01)
            except Exception as e:
                if self._running:
                    logger.error(f"Receive error: {e}")
                    time.sleep(0.1)
    
    def _process_streaming_data(self, data: Dict):
        """Process incoming streaming data."""
        data_type = data.get("type", "")
        
        if data_type == "TICK":
            symbol = data.get("symbol")
            if symbol and symbol in self._price_callbacks:
                for callback in self._price_callbacks[symbol]:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Price callback error: {e}")
        
        elif data_type == "POSITION_UPDATE":
            self._update_position(data)
        
        elif data_type == "ACCOUNT_UPDATE":
            self._update_account_info(data)
    
    def _sync_account_info(self) -> bool:
        """Synchronize account information."""
        response = self._send_command({"action": "ACCOUNT_INFO"})
        if response and response.get("status") == "OK":
            data = response.get("data", {})
            self._account_info = MTAccountInfo(
                login=data.get("login", 0),
                balance=data.get("balance", 0.0),
                equity=data.get("equity", 0.0),
                margin=data.get("margin", 0.0),
                free_margin=data.get("free_margin", 0.0),
                margin_level=data.get("margin_level", 0.0),
                profit=data.get("profit", 0.0),
                currency=data.get("currency", "USD")
            )
            return True
        return False
    
    def _update_account_info(self, data: Dict):
        """Update account info from streaming data."""
        if self._account_info:
            self._account_info.equity = data.get("equity", self._account_info.equity)
            self._account_info.margin = data.get("margin", self._account_info.margin)
            self._account_info.free_margin = data.get("free_margin", self._account_info.free_margin)
            self._account_info.profit = data.get("profit", self._account_info.profit)
    
    def _update_position(self, data: Dict):
        """Update position from streaming data."""
        ticket = data.get("ticket")
        if ticket:
            if data.get("closed"):
                self._positions.pop(ticket, None)
            else:
                self._positions[ticket] = MTOrder(
                    ticket=ticket,
                    symbol=data.get("symbol", ""),
                    type=data.get("type", ""),
                    volume=data.get("volume", 0.0),
                    open_price=data.get("open_price", 0.0),
                    current_price=data.get("current_price", 0.0),
                    sl=data.get("sl", 0.0),
                    tp=data.get("tp", 0.0),
                    profit=data.get("profit", 0.0),
                    open_time=datetime.fromtimestamp(data.get("open_time", 0))
                )
    
    def _simulate_command(self, command: Dict) -> Dict:
        """Simulate command response for testing."""
        action = command.get("action", "")
        
        if action == "PING":
            return {"status": "OK", "message": "PONG"}
        elif action == "ACCOUNT_INFO":
            return {
                "status": "OK",
                "data": {
                    "login": 12345678,
                    "balance": 10000.0,
                    "equity": 10250.0,
                    "margin": 500.0,
                    "free_margin": 9750.0,
                    "margin_level": 2050.0,
                    "profit": 250.0,
                    "currency": "USD"
                }
            }
        elif action == "ORDER_SEND":
            return {
                "status": "OK",
                "ticket": int(time.time() * 1000) % 1000000,
                "message": f"Order executed (SIMULATION)"
            }
        else:
            return {"status": "OK", "message": f"Simulated {action}"}
    
    # ==================== Trading Operations ====================
    
    def get_account_info(self) -> Optional[MTAccountInfo]:
        """Get current account information."""
        self._sync_account_info()
        return self._account_info
    
    def get_positions(self, symbol: str = None) -> List[MTOrder]:
        """
        Get open positions.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of MTOrder objects
        """
        if symbol:
            return [p for p in self._positions.values() if p.symbol == symbol]
        return list(self._positions.values())
    
    def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: float = None,
        sl: float = None,
        tp: float = None,
        comment: str = ""
    ) -> Optional[int]:
        """
        Place a new order.
        
        Args:
            symbol: Trading symbol
            order_type: 'BUY' or 'SELL'
            volume: Position size in lots
            price: Entry price (for pending orders)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            Order ticket on success, None on failure
        """
        command = {
            "action": "ORDER_SEND",
            "symbol": symbol,
            "type": order_type.upper(),
            "volume": volume,
            "sl": sl or 0.0,
            "tp": tp or 0.0,
            "comment": comment
        }
        
        if price:
            command["price"] = price
        
        response = self._send_command(command)
        
        if response and response.get("status") == "OK":
            ticket = response.get("ticket")
            logger.success(f"Order placed: {symbol} {order_type} {volume} lots (ticket: {ticket})")
            return ticket
        
        logger.error(f"Order failed: {response}")
        return None
    
    def close_position(self, ticket: int, volume: float = None) -> bool:
        """
        Close a position.
        
        Args:
            ticket: Position ticket
            volume: Volume to close (partial close), None for full close
            
        Returns:
            True on success
        """
        command = {
            "action": "ORDER_CLOSE",
            "ticket": ticket,
            "volume": volume if volume else 0.0  # 0 means full close
        }
        
        response = self._send_command(command)
        
        if response and response.get("status") == "OK":
            logger.success(f"Position closed: {ticket}")
            return True
        
        return False
    
    def modify_position(
        self,
        ticket: int,
        sl: float = None,
        tp: float = None
    ) -> bool:
        """
        Modify position SL/TP.
        
        Args:
            ticket: Position ticket
            sl: New stop loss
            tp: New take profit
            
        Returns:
            True on success
        """
        command = {
            "action": "ORDER_MODIFY",
            "ticket": ticket,
            "sl": sl if sl is not None else 0.0,
            "tp": tp if tp is not None else 0.0
        }
        
        response = self._send_command(command)
        return response and response.get("status") == "OK"
    
    def get_price(self, symbol: str) -> Optional[Dict]:
        """
        Get current bid/ask prices.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with bid, ask, spread
        """
        response = self._send_command({
            "action": "GET_PRICE",
            "symbol": symbol
        })
        
        if response and response.get("status") == "OK":
            return response.get("data")
        
        return None
    
    def get_history(
        self,
        symbol: str,
        timeframe: str = "H1",
        bars: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN)
            bars: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        response = self._send_command({
            "action": "GET_HISTORY",
            "symbol": symbol,
            "timeframe": timeframe,
            "bars": bars
        })
        
        if response and response.get("status") == "OK":
            data = response.get("data", [])
            if data:
                df = pd.DataFrame(data)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                return df
        
        return None
    
    def subscribe_price(self, symbol: str, callback: Callable) -> bool:
        """
        Subscribe to real-time price updates.
        
        Args:
            symbol: Symbol to subscribe
            callback: Function to call on price update
            
        Returns:
            True on success
        """
        if symbol not in self._price_callbacks:
            self._price_callbacks[symbol] = []
        
        self._price_callbacks[symbol].append(callback)
        
        # Send subscription command
        response = self._send_command({
            "action": "SUBSCRIBE_PRICE",
            "symbol": symbol
        })
        
        return response and response.get("status") == "OK"


class MetaTraderConnectorFactory:
    """Factory for creating MetaTrader connectors."""
    
    _instances: Dict[str, MetaTraderConnector] = {}
    
    @classmethod
    def get_connector(cls, name: str = "default", config: Dict = None) -> MetaTraderConnector:
        """Get or create a connector instance."""
        if name not in cls._instances:
            cls._instances[name] = MetaTraderConnector(config)
        return cls._instances[name]
    
    @classmethod
    def close_all(cls):
        """Close all connector instances."""
        for connector in cls._instances.values():
            connector.disconnect()
        cls._instances.clear()
