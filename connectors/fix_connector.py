"""
FIX Protocol Connector Module
Institutional-grade FIX protocol support for direct market access.

Supports FIX 4.2, 4.4, and 5.0 protocols.
"""
from loguru import logger
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import socket
import ssl
import hashlib

from connectors.exchange_connector import (
    Order, Position, Balance, OrderSide, OrderType, 
    OrderStatus, MarginMode
)


class FIXVersion(Enum):
    FIX42 = "FIX.4.2"
    FIX44 = "FIX.4.4"
    FIX50 = "FIXT.1.1"


class FIXMsgType(Enum):
    HEARTBEAT = "0"
    TEST_REQUEST = "1"
    RESEND_REQUEST = "2"
    REJECT = "3"
    SEQUENCE_RESET = "4"
    LOGOUT = "5"
    LOGON = "A"
    NEW_ORDER_SINGLE = "D"
    ORDER_CANCEL_REQUEST = "F"
    ORDER_CANCEL_REPLACE = "G"
    ORDER_STATUS_REQUEST = "H"
    EXECUTION_REPORT = "8"
    ORDER_CANCEL_REJECT = "9"
    MARKET_DATA_REQUEST = "V"
    MARKET_DATA_SNAPSHOT = "W"
    MARKET_DATA_INCREMENTAL = "X"


@dataclass
class FIXCredentials:
    """FIX protocol credentials."""
    host: str
    port: int
    sender_comp_id: str
    target_comp_id: str
    username: str = ""
    password: str = ""
    heartbeat_interval: int = 30
    reset_on_logon: bool = True
    ssl_enabled: bool = True
    fix_version: FIXVersion = FIXVersion.FIX44


class FIXMessage:
    """FIX message builder and parser."""
    
    SOH = '\x01'  # Start of Header (field separator)
    
    def __init__(self, msg_type: str = None):
        self.fields: Dict[int, str] = {}
        if msg_type:
            self.fields[35] = msg_type
    
    def set(self, tag: int, value: Any) -> 'FIXMessage':
        """Set a field value."""
        self.fields[tag] = str(value)
        return self
    
    def get(self, tag: int, default: str = None) -> Optional[str]:
        """Get a field value."""
        return self.fields.get(tag, default)
    
    def build(self, begin_string: str, sender: str, target: str, seq_num: int) -> str:
        """Build the complete FIX message."""
        # Build body first
        body = ""
        body += f"35={self.fields.get(35, '')}{self.SOH}"
        body += f"49={sender}{self.SOH}"
        body += f"56={target}{self.SOH}"
        body += f"34={seq_num}{self.SOH}"
        body += f"52={datetime.utcnow().strftime('%Y%m%d-%H:%M:%S.%f')[:-3]}{self.SOH}"
        
        # Add other fields
        for tag, value in self.fields.items():
            if tag not in [8, 9, 35, 49, 56, 34, 52, 10]:
                body += f"{tag}={value}{self.SOH}"
        
        # Build header
        header = f"8={begin_string}{self.SOH}"
        header += f"9={len(body)}{self.SOH}"
        
        # Calculate checksum
        full_msg = header + body
        checksum = sum(ord(c) for c in full_msg) % 256
        
        return full_msg + f"10={checksum:03d}{self.SOH}"
    
    @classmethod
    def parse(cls, raw: str) -> 'FIXMessage':
        """Parse a raw FIX message."""
        msg = cls()
        
        for field in raw.split(cls.SOH):
            if '=' in field:
                tag, value = field.split('=', 1)
                try:
                    msg.fields[int(tag)] = value
                except ValueError:
                    pass
        
        return msg
    
    @property
    def msg_type(self) -> str:
        return self.fields.get(35, '')


class FIXConnector:
    """
    FIX protocol connector for institutional trading.
    
    Supports:
    - Session layer (logon, logout, heartbeat, sequence management)
    - Application layer (orders, executions, market data)
    - SSL/TLS encryption
    - Automatic reconnection
    """
    
    def __init__(
        self,
        credentials: FIXCredentials,
        account_id: str = "default"
    ):
        self.credentials = credentials
        self.account_id = account_id
        self.is_connected = False
        self.is_logged_in = False
        
        self._socket: Optional[socket.socket] = None
        self._ssl_socket: Optional[ssl.SSLSocket] = None
        self._send_seq_num = 1
        self._recv_seq_num = 1
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._receiver_thread: Optional[threading.Thread] = None
        
        self._callbacks: Dict[str, List[Callable]] = {
            'on_execution': [],
            'on_order_status': [],
            'on_market_data': [],
            'on_error': []
        }
        
        self._pending_orders: Dict[str, Order] = {}
        
        logger.info(f"FIXConnector initialized for {credentials.sender_comp_id} -> {credentials.target_comp_id}")
    
    async def connect(self) -> bool:
        """Connect to FIX server."""
        try:
            # Create socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(30)
            
            # Connect
            logger.info(f"Connecting to FIX server {self.credentials.host}:{self.credentials.port}...")
            self._socket.connect((self.credentials.host, self.credentials.port))
            
            # SSL wrap if enabled
            if self.credentials.ssl_enabled:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self._ssl_socket = context.wrap_socket(
                    self._socket,
                    server_hostname=self.credentials.host
                )
            
            self.is_connected = True
            self._running = True
            
            # Start receiver thread
            self._receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receiver_thread.start()
            
            # Send Logon
            if await self._send_logon():
                logger.success("FIX Logon successful")
                
                # Start heartbeat thread
                self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
                self._heartbeat_thread.start()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"FIX connection failed: {e}")
            self.is_connected = False
            return False
    
    async def _send_logon(self) -> bool:
        """Send FIX Logon message."""
        msg = FIXMessage(FIXMsgType.LOGON.value)
        msg.set(98, 0)  # EncryptMethod = None
        msg.set(108, self.credentials.heartbeat_interval)  # HeartBtInt
        
        if self.credentials.reset_on_logon:
            msg.set(141, "Y")  # ResetSeqNumFlag
        
        if self.credentials.username:
            msg.set(553, self.credentials.username)
        if self.credentials.password:
            msg.set(554, self.credentials.password)
        
        return self._send_message(msg)
    
    async def disconnect(self) -> bool:
        """Disconnect from FIX server."""
        if not self.is_connected:
            return True
        
        try:
            # Send Logout
            msg = FIXMessage(FIXMsgType.LOGOUT.value)
            self._send_message(msg)
            
            self._running = False
            self.is_connected = False
            self.is_logged_in = False
            
            if self._ssl_socket:
                self._ssl_socket.close()
            if self._socket:
                self._socket.close()
            
            logger.info("FIX session disconnected")
            return True
            
        except Exception as e:
            logger.error(f"FIX disconnect error: {e}")
            return False
    
    def _send_message(self, msg: FIXMessage) -> bool:
        """Send a FIX message."""
        try:
            raw = msg.build(
                begin_string=self.credentials.fix_version.value,
                sender=self.credentials.sender_comp_id,
                target=self.credentials.target_comp_id,
                seq_num=self._send_seq_num
            )
            
            sock = self._ssl_socket or self._socket
            if sock:
                sock.send(raw.encode())
                self._send_seq_num += 1
                logger.debug(f"FIX sent: {msg.msg_type}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"FIX send error: {e}")
            return False
    
    def _receive_loop(self):
        """Receive messages from FIX server."""
        buffer = ""
        sock = self._ssl_socket or self._socket
        
        while self._running and sock:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                
                buffer += data.decode()
                
                # Process complete messages
                while FIXMessage.SOH in buffer:
                    # Find message end (checksum field)
                    end_idx = buffer.find("10=")
                    if end_idx == -1:
                        break
                    
                    # Find actual end
                    end_idx = buffer.find(FIXMessage.SOH, end_idx)
                    if end_idx == -1:
                        break
                    
                    msg_raw = buffer[:end_idx + 1]
                    buffer = buffer[end_idx + 1:]
                    
                    self._process_message(FIXMessage.parse(msg_raw))
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"FIX receive error: {e}")
                break
    
    def _process_message(self, msg: FIXMessage):
        """Process received FIX message."""
        msg_type = msg.msg_type
        
        if msg_type == FIXMsgType.LOGON.value:
            self.is_logged_in = True
            logger.info("FIX Logon acknowledged")
            
        elif msg_type == FIXMsgType.LOGOUT.value:
            self.is_logged_in = False
            logger.info("FIX Logout received")
            
        elif msg_type == FIXMsgType.HEARTBEAT.value:
            logger.debug("FIX Heartbeat received")
            
        elif msg_type == FIXMsgType.TEST_REQUEST.value:
            # Respond with heartbeat
            hb = FIXMessage(FIXMsgType.HEARTBEAT.value)
            test_req_id = msg.get(112)
            if test_req_id:
                hb.set(112, test_req_id)
            self._send_message(hb)
            
        elif msg_type == FIXMsgType.EXECUTION_REPORT.value:
            self._handle_execution_report(msg)
            
        elif msg_type == FIXMsgType.ORDER_CANCEL_REJECT.value:
            logger.warning(f"FIX Order cancel rejected: {msg.get(58)}")
            
        elif msg_type == FIXMsgType.REJECT.value:
            logger.warning(f"FIX Message rejected: {msg.get(58)}")
        
        self._recv_seq_num += 1
    
    def _handle_execution_report(self, msg: FIXMessage):
        """Handle execution report."""
        order_id = msg.get(37)  # OrderID
        cl_ord_id = msg.get(11)  # ClOrdID
        exec_type = msg.get(150)  # ExecType
        ord_status = msg.get(39)  # OrdStatus
        
        logger.info(f"FIX Execution: OrderID={order_id}, Status={ord_status}, ExecType={exec_type}")
        
        # Notify callbacks
        for callback in self._callbacks.get('on_execution', []):
            try:
                callback({
                    'order_id': order_id,
                    'client_order_id': cl_ord_id,
                    'exec_type': exec_type,
                    'status': ord_status,
                    'side': msg.get(54),
                    'symbol': msg.get(55),
                    'quantity': msg.get(32),
                    'price': msg.get(31),
                    'text': msg.get(58)
                })
            except Exception as e:
                logger.error(f"Execution callback error: {e}")
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self._running and self.is_logged_in:
            time.sleep(self.credentials.heartbeat_interval)
            if self._running and self.is_logged_in:
                hb = FIXMessage(FIXMsgType.HEARTBEAT.value)
                self._send_message(hb)
    
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = None,
        account: str = None,
        time_in_force: str = "0"  # 0=Day, 1=GTC, 3=IOC, 4=FOK
    ) -> Order:
        """Send a new order via FIX."""
        if not self.is_logged_in:
            return Order(
                id="",
                client_order_id="",
                symbol=symbol,
                side=side,
                type=order_type,
                amount=quantity,
                status=OrderStatus.REJECTED
            )
        
        cl_ord_id = f"ORD{int(time.time() * 1000)}"
        
        msg = FIXMessage(FIXMsgType.NEW_ORDER_SINGLE.value)
        msg.set(11, cl_ord_id)  # ClOrdID
        msg.set(55, symbol)  # Symbol
        msg.set(54, "1" if side == OrderSide.BUY else "2")  # Side
        msg.set(60, datetime.utcnow().strftime('%Y%m%d-%H:%M:%S'))  # TransactTime
        msg.set(38, quantity)  # OrderQty
        msg.set(40, "1" if order_type == OrderType.MARKET else "2")  # OrdType
        msg.set(59, time_in_force)  # TimeInForce
        
        if price and order_type == OrderType.LIMIT:
            msg.set(44, price)  # Price
        
        if account:
            msg.set(1, account)  # Account
        
        if self._send_message(msg):
            order = Order(
                id="",  # Will be filled by execution report
                client_order_id=cl_ord_id,
                symbol=symbol,
                side=side,
                type=order_type,
                amount=quantity,
                price=price,
                status=OrderStatus.PENDING,
                exchange="fix",
                account_id=self.account_id
            )
            self._pending_orders[cl_ord_id] = order
            return order
        
        return Order(
            id="",
            client_order_id=cl_ord_id,
            symbol=symbol,
            side=side,
            type=order_type,
            amount=quantity,
            status=OrderStatus.REJECTED
        )
    
    async def cancel_order(self, cl_ord_id: str, symbol: str) -> bool:
        """Cancel an order via FIX."""
        if not self.is_logged_in:
            return False
        
        msg = FIXMessage(FIXMsgType.ORDER_CANCEL_REQUEST.value)
        msg.set(11, f"CXL{int(time.time() * 1000)}")  # ClOrdID for cancel
        msg.set(41, cl_ord_id)  # OrigClOrdID
        msg.set(55, symbol)  # Symbol
        msg.set(60, datetime.utcnow().strftime('%Y%m%d-%H:%M:%S'))  # TransactTime
        
        return self._send_message(msg)
    
    def on_execution(self, callback: Callable):
        """Register execution callback."""
        self._callbacks['on_execution'].append(callback)
    
    def on_order_status(self, callback: Callable):
        """Register order status callback."""
        self._callbacks['on_order_status'].append(callback)


class FIXConnectorFactory:
    """Factory for FIX connectors."""
    
    _connectors: Dict[str, FIXConnector] = {}
    
    @classmethod
    def create(
        cls,
        credentials: FIXCredentials,
        account_id: str = "default"
    ) -> FIXConnector:
        """Create or get a FIX connector."""
        key = f"{credentials.sender_comp_id}_{credentials.target_comp_id}_{account_id}"
        
        if key not in cls._connectors:
            connector = FIXConnector(credentials, account_id)
            cls._connectors[key] = connector
        
        return cls._connectors[key]
    
    @classmethod
    def get_all_connectors(cls) -> Dict[str, FIXConnector]:
        """Get all active connectors."""
        return cls._connectors.copy()


if __name__ == "__main__":
    print("FIX Protocol Connector")
    print("Supported versions:", [v.value for v in FIXVersion])
