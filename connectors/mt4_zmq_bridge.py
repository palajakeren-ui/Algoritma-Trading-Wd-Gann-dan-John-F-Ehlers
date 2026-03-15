"""
MetaTrader 4 ZMQ Bridge Connector
==================================
Real-time ZMQ-based communication with MetaTrader 4 terminal.

Requirements:
- pyzmq: pip install pyzmq
- MT4 Terminal with ZMQ EA running
- ZeroMQ Expert Advisor installed on MT4

Architecture:
┌──────────────────┐      ZMQ       ┌──────────────────┐
│   Python API     │◄──────────────►│   MT4 Terminal   │
│  (This Module)   │    REQ/REP     │   (ZMQ EA)       │
└──────────────────┘    PUB/SUB     └──────────────────┘
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import asyncio

# ZMQ imports with fallback
try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
    logger.warning("pyzmq not installed. Install with: pip install pyzmq")

from connectors.exchange_connector import (
    Order, Position, Balance, OrderSide, OrderType,
    OrderStatus, MarginMode, PositionSide
)


class ZMQCommand(Enum):
    """ZMQ command types for MT4 communication."""
    # Account
    ACCOUNT_INFO = "ACCOUNT_INFO"
    BALANCE = "BALANCE"
    EQUITY = "EQUITY"
    
    # Market Data
    SYMBOL_INFO = "SYMBOL_INFO"
    TICK = "TICK"
    BARS = "BARS"
    
    # Orders
    ORDER_SEND = "ORDER_SEND"
    ORDER_MODIFY = "ORDER_MODIFY"
    ORDER_DELETE = "ORDER_DELETE"
    ORDER_CLOSE = "ORDER_CLOSE"
    ORDERS_TOTAL = "ORDERS_TOTAL"
    ORDERS_SELECT = "ORDERS_SELECT"
    
    # Positions
    POSITIONS = "POSITIONS"
    POSITION_CLOSE = "POSITION_CLOSE"
    POSITION_MODIFY = "POSITION_MODIFY"
    
    # History
    HISTORY_ORDERS = "HISTORY_ORDERS"
    HISTORY_DEALS = "HISTORY_DEALS"
    
    # System
    PING = "PING"
    PONG = "PONG"
    STATUS = "STATUS"


@dataclass
class MT4Config:
    """MT4 ZMQ Bridge configuration."""
    req_host: str = "localhost"
    req_port: int = 5555  # REQ/REP for commands
    sub_host: str = "localhost"
    sub_port: int = 5556  # PUB/SUB for streaming
    
    login: str = ""
    password: str = ""
    server: str = ""
    broker: str = ""
    
    timeout_ms: int = 5000
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    
    # Order settings - synced with frontend
    default_slippage: int = 3
    default_magic: int = 123456
    default_comment: str = "GQ_BOT"
    
    # Dynamic slippage settings (synced via broker_config.yaml)
    auto_slippage: bool = True
    max_slippage: int = 10
    min_slippage: int = 0
    
    # Slippage profile by symbol type
    forex_slippage: int = 3
    crypto_slippage: int = 10
    metals_slippage: int = 5
    indices_slippage: int = 2


@dataclass
class MT4Tick:
    """Real-time tick data from MT4."""
    symbol: str
    bid: float
    ask: float
    spread: float
    time: datetime
    volume: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MT4Tick':
        return cls(
            symbol=data.get('symbol', ''),
            bid=float(data.get('bid', 0)),
            ask=float(data.get('ask', 0)),
            spread=float(data.get('spread', 0)),
            time=datetime.fromtimestamp(data.get('time', 0)),
            volume=int(data.get('volume', 0))
        )


@dataclass
class MT4Position:
    """MT4 position data."""
    ticket: int
    symbol: str
    type: int  # 0=BUY, 1=SELL
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    swap: float
    commission: float
    comment: str
    magic: int
    open_time: datetime
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MT4Position':
        return cls(
            ticket=int(data.get('ticket', 0)),
            symbol=data.get('symbol', ''),
            type=int(data.get('type', 0)),
            volume=float(data.get('volume', 0)),
            open_price=float(data.get('open_price', 0)),
            current_price=float(data.get('current_price', 0)),
            sl=float(data.get('sl', 0)),
            tp=float(data.get('tp', 0)),
            profit=float(data.get('profit', 0)),
            swap=float(data.get('swap', 0)),
            commission=float(data.get('commission', 0)),
            comment=data.get('comment', ''),
            magic=int(data.get('magic', 0)),
            open_time=datetime.fromtimestamp(data.get('open_time', 0))
        )


class MT4ZMQBridge:
    """
    MetaTrader 4 ZMQ Bridge for live trading.
    
    Communication Pattern:
    - REQ/REP socket: Synchronous command-response
    - PUB/SUB socket: Asynchronous data streaming
    """
    
    def __init__(self, config: MT4Config):
        self.config = config
        self._connected = False
        self._context = None
        self._req_socket = None
        self._sub_socket = None
        self._running = False
        self._lock = threading.Lock()
        
        self._ticks: Dict[str, MT4Tick] = {}
        self._positions: Dict[int, MT4Position] = {}
        self._account_info: Dict = {}
        
        self._tick_callbacks: List[Callable] = []
        self._order_callbacks: List[Callable] = []
        self._position_callbacks: List[Callable] = []
        
        self._stream_thread: Optional[threading.Thread] = None
        
        if not ZMQ_AVAILABLE:
            logger.error("ZeroMQ not available. Install with: pip install pyzmq")
        else:
            logger.info(f"MT4ZMQBridge initialized (REQ: {config.req_host}:{config.req_port})")
    
    def is_available(self) -> bool:
        return ZMQ_AVAILABLE
    
    def connect(self) -> bool:
        if not ZMQ_AVAILABLE:
            logger.error("Cannot connect: ZeroMQ not installed")
            return False
        
        try:
            self._context = zmq.Context()
            
            self._req_socket = self._context.socket(zmq.REQ)
            self._req_socket.setsockopt(zmq.RCVTIMEO, self.config.timeout_ms)
            self._req_socket.setsockopt(zmq.SNDTIMEO, self.config.timeout_ms)
            self._req_socket.setsockopt(zmq.LINGER, 0)
            
            req_addr = f"tcp://{self.config.req_host}:{self.config.req_port}"
            self._req_socket.connect(req_addr)
            logger.info(f"Connected REQ socket to {req_addr}")
            
            self._sub_socket = self._context.socket(zmq.SUB)
            self._sub_socket.setsockopt(zmq.RCVTIMEO, 1000)
            self._sub_socket.setsockopt(zmq.SUBSCRIBE, b"")
            self._sub_socket.setsockopt(zmq.LINGER, 0)
            
            sub_addr = f"tcp://{self.config.sub_host}:{self.config.sub_port}"
            self._sub_socket.connect(sub_addr)
            logger.info(f"Connected SUB socket to {sub_addr}")
            
            if self._ping():
                self._connected = True
                self._running = True
                self._start_streaming()
                self._account_info = self._send_command(ZMQCommand.ACCOUNT_INFO.value, {})
                self._sync_positions()
                logger.success("MT4 ZMQ Bridge connected successfully")
                return True
            else:
                logger.error("MT4 ZMQ Bridge ping failed")
                self._cleanup_sockets()
                return False
                
        except Exception as e:
            logger.error(f"MT4 ZMQ Bridge connection failed: {e}")
            self._cleanup_sockets()
            return False
    
    def disconnect(self) -> bool:
        self._running = False
        self._connected = False
        
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=2)
        
        self._cleanup_sockets()
        logger.info("MT4 ZMQ Bridge disconnected")
        return True
    
    def _cleanup_sockets(self):
        try:
            if self._req_socket:
                self._req_socket.close()
                self._req_socket = None
            if self._sub_socket:
                self._sub_socket.close()
                self._sub_socket = None
            if self._context:
                self._context.term()
                self._context = None
        except Exception as e:
            logger.error(f"Socket cleanup error: {e}")
    
    def _ping(self) -> bool:
        try:
            response = self._send_command(ZMQCommand.PING.value, {"timestamp": time.time()})
            return response.get("status") == "ok" or response.get("command") == "PONG"
        except Exception:
            return False
    
    def _send_command(self, command: str, params: Dict) -> Dict:
        if not self._req_socket:
            return {"status": "error", "message": "Not connected"}
        
        with self._lock:
            try:
                message = json.dumps({
                    "command": command,
                    "params": params,
                    "timestamp": time.time()
                })
                
                self._req_socket.send_string(message)
                response_str = self._req_socket.recv_string()
                response = json.loads(response_str)
                
                return response
                
            except zmq.error.Again:
                logger.error(f"Timeout waiting for response to {command}")
                return {"status": "error", "message": "Timeout"}
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return {"status": "error", "message": "Invalid JSON"}
            except Exception as e:
                logger.error(f"Command error ({command}): {e}")
                return {"status": "error", "message": str(e)}
    
    def _start_streaming(self):
        def stream_loop():
            logger.info("MT4 streaming thread started")
            
            while self._running and self._sub_socket:
                try:
                    if self._sub_socket.poll(100):
                        message = self._sub_socket.recv_string()
                        data = json.loads(message)
                        
                        msg_type = data.get("type", "")
                        
                        if msg_type == "TICK":
                            self._handle_tick(data)
                        elif msg_type == "ORDER_UPDATE":
                            self._handle_order_update(data)
                        elif msg_type == "POSITION_UPDATE":
                            self._handle_position_update(data)
                            
                except json.JSONDecodeError:
                    pass
                except zmq.error.ZMQError:
                    break
                except Exception as e:
                    if self._running:
                        logger.error(f"Streaming error: {e}")
            
            logger.info("MT4 streaming thread stopped")
        
        self._stream_thread = threading.Thread(target=stream_loop, daemon=True)
        self._stream_thread.start()
    
    def _handle_tick(self, data: Dict):
        try:
            tick = MT4Tick.from_dict(data)
            self._ticks[tick.symbol] = tick
            
            for callback in self._tick_callbacks:
                try:
                    callback(tick)
                except Exception as e:
                    logger.error(f"Tick callback error: {e}")
        except Exception as e:
            logger.error(f"Tick handling error: {e}")
    
    def _handle_order_update(self, data: Dict):
        for callback in self._order_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Order callback error: {e}")
    
    def _handle_position_update(self, data: Dict):
        try:
            position = MT4Position.from_dict(data)
            self._positions[position.ticket] = position
            
            for callback in self._position_callbacks:
                try:
                    callback(position)
                except Exception as e:
                    logger.error(f"Position callback error: {e}")
        except Exception as e:
            logger.error(f"Position update error: {e}")
    
    def _sync_positions(self):
        response = self._send_command(ZMQCommand.POSITIONS.value, {})
        if response.get("status") == "ok":
            positions = response.get("positions", [])
            self._positions.clear()
            for pos_data in positions:
                try:
                    pos = MT4Position.from_dict(pos_data)
                    self._positions[pos.ticket] = pos
                except Exception:
                    pass
    
    def is_connected(self) -> bool:
        return self._connected
    
    def get_account_info(self) -> Dict:
        if not self._connected:
            return {}
        
        response = self._send_command(ZMQCommand.ACCOUNT_INFO.value, {})
        if response.get("status") == "ok":
            self._account_info = response.get("account", {})
        return self._account_info
    
    def get_balance(self) -> float:
        info = self.get_account_info()
        return float(info.get("balance", 0))
    
    def get_equity(self) -> float:
        info = self.get_account_info()
        return float(info.get("equity", 0))
    
    def get_tick(self, symbol: str) -> Optional[MT4Tick]:
        if symbol in self._ticks:
            return self._ticks[symbol]
        
        if not self._connected:
            return None
        
        response = self._send_command(ZMQCommand.TICK.value, {"symbol": symbol})
        if response.get("status") == "ok":
            return MT4Tick.from_dict(response.get("tick", {}))
        return None
    
    def get_positions(self, symbol: str = None) -> List[MT4Position]:
        if not self._connected:
            return []
        
        self._sync_positions()
        positions = list(self._positions.values())
        
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        
        return positions
    
    def calculate_slippage(
        self,
        symbol: str,
        spread: float = None,
        volatility: float = None,
        frontend_slippage: int = None
    ) -> int:
        """
        Calculate dynamic slippage based on frontend settings and market conditions.
        
        Args:
            symbol: Trading symbol
            spread: Current spread in points
            volatility: Current volatility
            frontend_slippage: Slippage from frontend config
            
        Returns:
            Calculated slippage in points
        """
        # If frontend provides slippage, use it with limits
        if frontend_slippage is not None:
            return max(self.config.min_slippage,
                      min(frontend_slippage, self.config.max_slippage))
        
        # If auto_slippage is disabled, use default
        if not self.config.auto_slippage:
            return self.config.default_slippage
        
        # Determine symbol type for base slippage
        symbol_upper = symbol.upper()
        
        if any(s in symbol_upper for s in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']):
            # Forex pair
            base_slippage = self.config.forex_slippage
        elif any(s in symbol_upper for s in ['BTC', 'ETH', 'SOL', 'BNB', 'XRP']):
            # Crypto CFD
            base_slippage = self.config.crypto_slippage
        elif any(s in symbol_upper for s in ['XAU', 'XAG', 'GOLD', 'SILVER']):
            # Metals
            base_slippage = self.config.metals_slippage
        elif any(s in symbol_upper for s in ['US30', 'US500', 'NAS100', 'SPX', 'NDX', 'DJI']):
            # Indices
            base_slippage = self.config.indices_slippage
        else:
            # Default
            base_slippage = self.config.default_slippage
        
        # Adjust based on spread if provided
        if spread is not None:
            spread_adjustment = int(spread * 0.5)
            base_slippage += spread_adjustment
        
        # Adjust based on volatility if provided
        if volatility is not None:
            if volatility > 2.0:
                base_slippage = int(base_slippage * 1.5)
            elif volatility > 1.0:
                base_slippage = int(base_slippage * 1.2)
        
        # Clamp to configured limits
        return max(self.config.min_slippage,
                  min(base_slippage, self.config.max_slippage))
    
    def update_slippage_from_frontend(self, frontend_config: Dict):
        """
        Update slippage settings from frontend configuration.
        
        Args:
            frontend_config: Dict with slippage settings from frontend
        """
        if 'auto_slippage' in frontend_config:
            self.config.auto_slippage = frontend_config['auto_slippage']
        if 'max_slippage' in frontend_config:
            self.config.max_slippage = frontend_config['max_slippage']
        if 'min_slippage' in frontend_config:
            self.config.min_slippage = frontend_config['min_slippage']
        if 'default_slippage' in frontend_config:
            self.config.default_slippage = frontend_config['default_slippage']
        if 'forex_slippage' in frontend_config:
            self.config.forex_slippage = frontend_config['forex_slippage']
        if 'crypto_slippage' in frontend_config:
            self.config.crypto_slippage = frontend_config['crypto_slippage']
        if 'metals_slippage' in frontend_config:
            self.config.metals_slippage = frontend_config['metals_slippage']
        if 'indices_slippage' in frontend_config:
            self.config.indices_slippage = frontend_config['indices_slippage']
        
        logger.info(f"Slippage settings updated from frontend: auto={self.config.auto_slippage}, "
                   f"range=[{self.config.min_slippage}, {self.config.max_slippage}]")
    
    def place_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        order_type: str = "MARKET",
        price: float = 0,
        sl: float = 0,
        tp: float = 0,
        slippage: int = None,
        magic: int = None,
        comment: str = None,
        expiration: int = 0,
        spread: float = None,
        volatility: float = None,
        use_auto_slippage: bool = True
    ) -> Dict:
        """
        Place order with dynamic slippage from frontend settings.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            volume: Position volume
            order_type: Order type (MARKET/LIMIT/STOP)
            price: Entry price for pending orders
            sl: Stop loss
            tp: Take profit
            slippage: Manual slippage (overrides auto calculation)
            magic: Magic number
            comment: Order comment
            expiration: Order expiration time
            spread: Current spread for auto slippage calculation
            volatility: Current volatility for auto slippage calculation
            use_auto_slippage: Whether to use auto slippage
            
        Returns:
            Response dict with status and ticket
        """
        if not self._connected:
            return {"status": "error", "message": "Not connected"}
        
        # Calculate dynamic slippage
        if use_auto_slippage and slippage is None:
            calculated_slippage = self.calculate_slippage(
                symbol=symbol,
                spread=spread,
                volatility=volatility
            )
        else:
            calculated_slippage = slippage if slippage is not None else self.config.default_slippage
        
        # Clamp to configured limits
        final_slippage = max(self.config.min_slippage,
                            min(calculated_slippage, self.config.max_slippage))
        
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "volume": volume,
            "type": order_type.upper(),
            "price": price,
            "sl": sl,
            "tp": tp,
            "slippage": final_slippage,
            "magic": magic or self.config.default_magic,
            "comment": comment or self.config.default_comment,
            "expiration": expiration
        }
        
        response = self._send_command(ZMQCommand.ORDER_SEND.value, params)
        
        if response.get("status") == "ok":
            ticket = response.get("ticket", 0)
            logger.success(f"Order placed: {side} {volume} {symbol} @ {price or 'market'}, "
                         f"slippage={final_slippage}, ticket={ticket}")
        else:
            logger.error(f"Order failed: {response.get('message', 'Unknown error')}")
        
        return response
    
    def close_position(self, ticket: int, volume: float = None) -> Dict:
        if not self._connected:
            return {"status": "error", "message": "Not connected"}
        
        params = {
            "ticket": ticket,
            "volume": volume or 0
        }
        
        response = self._send_command(ZMQCommand.POSITION_CLOSE.value, params)
        
        if response.get("status") == "ok":
            logger.info(f"Position {ticket} closed")
            self._positions.pop(ticket, None)
        
        return response
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        count: int = 1000,
        start_time: int = 0
    ) -> List[Dict]:
        if not self._connected:
            return []
        
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": count,
            "start_time": start_time
        }
        
        response = self._send_command(ZMQCommand.BARS.value, params)
        
        if response.get("status") == "ok":
            return response.get("bars", [])
        return []
    
    def on_tick(self, callback: Callable[[MT4Tick], None]):
        self._tick_callbacks.append(callback)
    
    def on_order_update(self, callback: Callable[[Dict], None]):
        self._order_callbacks.append(callback)
    
    def on_position_update(self, callback: Callable[[MT4Position], None]):
        self._position_callbacks.append(callback)


class MT4ZMQBridgeAsync:
    """Async wrapper for MT4ZMQBridge."""
    
    def __init__(self, config: MT4Config):
        self._bridge = MT4ZMQBridge(config)
    
    async def connect(self) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._bridge.connect)
    
    async def disconnect(self) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._bridge.disconnect)
    
    def is_connected(self) -> bool:
        return self._bridge.is_connected()
    
    async def get_account_info(self) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._bridge.get_account_info)
    
    async def get_positions(self, symbol: str = None) -> List[MT4Position]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._bridge.get_positions(symbol))
    
    async def place_order(self, symbol: str, side: str, volume: float, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self._bridge.place_order(symbol, side, volume, **kwargs)
        )
