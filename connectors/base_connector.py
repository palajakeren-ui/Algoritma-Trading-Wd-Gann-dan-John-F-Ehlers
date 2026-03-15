"""
Base Connector Classes for Low Latency Trading
Shared functionality to avoid code duplication
"""
import socket
import threading
from typing import Optional, List
from abc import ABC, abstractmethod


class ConnectionPoolBase:
    """Base class for connection pooling with thread safety."""
    
    def __init__(self, lock: threading.Lock = None):
        self._lock = lock or threading.Lock()
        self._connections: List[socket.socket] = []
        self._available: List[socket.socket] = []
    
    def release(self, conn: socket.socket):
        """Release connection back to pool."""
        with self._lock:
            if conn not in self._connections:
                try:
                    conn.close()
                except Exception:
                    pass
                return
            self._available.append(conn)
    
    def close_all(self):
        """Close all connections."""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception:
                    pass
            self._connections.clear()
            self._available.clear()


class SingletonMeta(type):
    """Metaclass for singleton pattern."""
    
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class LowLatencyConnectorBase(ABC):
    """Abstract base class for low latency connectors."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to broker/exchange."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass
    
    @abstractmethod
    def get_positions(self) -> List:
        """Get all open positions."""
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: int, volume: float, **kwargs) -> Optional[int]:
        """Place an order."""
        pass
    
    @abstractmethod
    def close_position(self, ticket: int, volume: float = 0.0) -> bool:
        """Close a position."""
        pass


class ConnectorFactory:
    """Factory for creating connector instances."""
    
    _registry = {}
    
    @classmethod
    def register(cls, connector_type: str, connector_class):
        """Register a connector class."""
        cls._registry[connector_type] = connector_class
    
    @classmethod
    def create(cls, connector_type: str, config) -> LowLatencyConnectorBase:
        """Create a connector instance."""
        if connector_type not in cls._registry:
            raise ValueError(f"Unknown connector type: {connector_type}")
        return cls._registry[connector_type](config)
    
    @classmethod
    def get_available_connectors(cls) -> List[str]:
        """Get list of registered connector types."""
        return list(cls._registry.keys())


def close_all_connectors():
    """Close all singleton connector instances."""
    from connectors.mt4_low_latency import MT4LowLatencyFactory
    from connectors.mt5_low_latency import MT5LowLatencyFactory
    
    MT4LowLatencyFactory.close_all()
    MT5LowLatencyFactory.close_all()
