"""
MetaTrader 4 Connector Virtual Test Suite
==========================================
Comprehensive tests for MT4 ZMQ Bridge and connector functionality.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock

import sys
sys.path.insert(0, '/home/z/my-project')

from connectors.mt4_zmq_bridge import (
    MT4ZMQBridge, MT4ZMQBridgeAsync, MT4Config,
    MT4Tick, MT4Position, ZMQCommand, ZMQ_AVAILABLE
)


class TestMT4Config:
    """Test MT4Config dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MT4Config()
        
        assert config.req_host == "localhost"
        assert config.req_port == 5555
        assert config.sub_host == "localhost"
        assert config.sub_port == 5556
        assert config.timeout_ms == 5000
        assert config.default_slippage == 3
        assert config.default_magic == 123456
        assert config.default_comment == "GQ_BOT"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = MT4Config(
            req_host="192.168.1.100",
            req_port=5557,
            sub_host="192.168.1.100",
            sub_port=5558,
            login="12345678",
            password="testpass",
            server="Demo-Server",
            broker="ICMarkets",
            timeout_ms=10000,
            default_magic=999999,
            default_comment="CUSTOM_BOT"
        )
        
        assert config.req_host == "192.168.1.100"
        assert config.req_port == 5557
        assert config.login == "12345678"
        assert config.default_magic == 999999


class TestMT4Tick:
    """Test MT4Tick dataclass."""
    
    def test_tick_creation(self):
        """Test tick data creation."""
        tick = MT4Tick(
            symbol="EURUSD",
            bid=1.1000,
            ask=1.1002,
            spread=2.0,
            time=datetime.now(),
            volume=1000
        )
        
        assert tick.symbol == "EURUSD"
        assert tick.bid == 1.1000
        assert tick.ask == 1.1002
        assert tick.spread == 2.0
        assert tick.volume == 1000
    
    def test_tick_from_dict(self):
        """Test tick creation from dictionary."""
        data = {
            'symbol': 'GBPUSD',
            'bid': 1.2500,
            'ask': 1.2503,
            'spread': 3.0,
            'time': 1704067200,
            'volume': 500
        }
        
        tick = MT4Tick.from_dict(data)
        
        assert tick.symbol == 'GBPUSD'
        assert tick.bid == 1.2500
        assert tick.ask == 1.2503
        assert tick.spread == 3.0
        assert tick.volume == 500


class TestMT4Position:
    """Test MT4Position dataclass."""
    
    def test_position_creation(self):
        """Test position data creation."""
        position = MT4Position(
            ticket=12345,
            symbol="XAUUSD",
            type=0,
            volume=0.1,
            open_price=2000.00,
            current_price=2010.00,
            sl=1980.00,
            tp=2050.00,
            profit=100.00,
            swap=-2.50,
            commission=0.0,
            comment="GQ_BOT",
            magic=123456,
            open_time=datetime.now()
        )
        
        assert position.ticket == 12345
        assert position.symbol == "XAUUSD"
        assert position.type == 0
        assert position.volume == 0.1
        assert position.profit == 100.00
    
    def test_position_from_dict(self):
        """Test position creation from dictionary."""
        data = {
            'ticket': 54321,
            'symbol': 'USDJPY',
            'type': 1,
            'volume': 0.5,
            'open_price': 145.00,
            'current_price': 144.50,
            'sl': 146.00,
            'tp': 143.00,
            'profit': 250.00,
            'swap': 0.0,
            'commission': -5.00,
            'comment': 'TEST',
            'magic': 654321,
            'open_time': 1704067200
        }
        
        position = MT4Position.from_dict(data)
        
        assert position.ticket == 54321
        assert position.symbol == 'USDJPY'
        assert position.type == 1
        assert position.volume == 0.5


class TestMT4ZMQBridge:
    """Test MT4 ZMQ Bridge functionality."""
    
    def test_bridge_initialization(self):
        """Test bridge initialization."""
        config = MT4Config()
        bridge = MT4ZMQBridge(config)
        
        assert bridge.config == config
        assert bridge.is_connected() == False
    
    def test_is_available(self):
        """Test ZMQ availability check."""
        config = MT4Config()
        bridge = MT4ZMQBridge(config)
        assert bridge.is_available() == ZMQ_AVAILABLE
    
    def test_command_enum_values(self):
        """Test ZMQ command enum values."""
        assert ZMQCommand.PING.value == "PING"
        assert ZMQCommand.ACCOUNT_INFO.value == "ACCOUNT_INFO"
        assert ZMQCommand.ORDER_SEND.value == "ORDER_SEND"
        assert ZMQCommand.POSITIONS.value == "POSITIONS"
        assert ZMQCommand.TICK.value == "TICK"
        assert ZMQCommand.BARS.value == "BARS"
    
    def test_callback_registration(self):
        """Test callback registration."""
        config = MT4Config()
        bridge = MT4ZMQBridge(config)
        
        tick_callback = Mock()
        order_callback = Mock()
        position_callback = Mock()
        
        bridge.on_tick(tick_callback)
        bridge.on_order_update(order_callback)
        bridge.on_position_update(position_callback)
        
        assert tick_callback in bridge._tick_callbacks
        assert order_callback in bridge._order_callbacks
        assert position_callback in bridge._position_callbacks


class TestMT4ZMQBridgeAsync:
    """Test async wrapper for MT4 ZMQ Bridge."""
    
    def test_async_wrapper_creation(self):
        """Test async wrapper initialization."""
        config = MT4Config()
        bridge = MT4ZMQBridgeAsync(config)
        assert bridge._bridge is not None
        assert isinstance(bridge._bridge, MT4ZMQBridge)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
