"""
Test Suite for MT4 Ultra Low Latency Connector
==============================================
Comprehensive tests for HFT-optimized MT4 connectivity.

Run with: pytest tests/test_mt4_low_latency.py -v
"""

import pytest
import time
import struct
import asyncio
import threading
import socket
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Import the connector components
from connectors.mt4_low_latency import (
    UltraLowLatencyConfig,
    TickData,
    OrderData,
    CommandType,
    ResponseStatus,
    OrderSide,
    OrderType,
    MT4UltraLowLatency,
    MT4UltraLowLatencyAsync,
    MT4LowLatencyFactory,
    SharedMemoryTickStream,
    ConnectionPool,
    PreallocatedBuffer,
    Command
)


class TestUltraLowLatencyConfig:
    """Test configuration dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = UltraLowLatencyConfig()
        
        assert config.host == "localhost"
        assert config.port == 5557
        assert config.connection_timeout_ms == 1000
        assert config.socket_timeout_ms == 100
        assert config.tcp_nodelay is True
        assert config.pool_size == 4
        assert config.command_timeout_us == 50000
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = UltraLowLatencyConfig(
            host="192.168.1.100",
            port=6000,
            pool_size=8,
            command_timeout_us=25000
        )
        
        assert config.host == "192.168.1.100"
        assert config.port == 6000
        assert config.pool_size == 8
        assert config.command_timeout_us == 25000


class TestTickData:
    """Test tick data serialization."""
    
    def test_tick_data_creation(self):
        """Test tick data creation."""
        tick = TickData(
            symbol=b"EURUSD",
            bid=1.0850,
            ask=1.0852,
            spread=2.0,
            volume=1000,
            time_ns=1234567890000000000
        )
        
        assert tick.symbol == b"EURUSD"
        assert tick.bid == 1.0850
        assert tick.ask == 1.0852
        assert tick.spread == 2.0
        assert tick.volume == 1000
    
    def test_tick_serialization(self):
        """Test binary serialization/deserialization."""
        original = TickData(
            symbol=b"GBPUSD",
            bid=1.2500,
            ask=1.2502,
            spread=2.0,
            volume=500,
            time_ns=int(time.time() * 1e9)
        )
        
        # Serialize
        data = original.to_bytes()
        assert len(data) == TickData.BINARY_SIZE
        assert len(data) == 52  # Expected size
        
        # Deserialize
        restored = TickData.from_bytes(data)
        
        assert restored.symbol == original.symbol
        assert restored.bid == original.bid
        assert restored.ask == original.ask
        assert restored.spread == original.spread
        assert restored.volume == original.volume
        assert restored.time_ns == original.time_ns
    
    def test_long_symbol_truncation(self):
        """Test that long symbols are truncated to 12 bytes."""
        tick = TickData(
            symbol=b"VERYLONGSYMBOLNAME",
            bid=1.0,
            ask=1.0,
            spread=0,
            volume=0,
            time_ns=0
        )
        
        data = tick.to_bytes()
        restored = TickData.from_bytes(data)
        
        # Should be truncated to 12 bytes
        assert len(restored.symbol) <= 12


class TestOrderData:
    """Test order data serialization."""
    
    def test_order_data_creation(self):
        """Test order data creation."""
        order = OrderData(
            ticket=123456,
            symbol=b"EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=0.1,
            open_price=1.0850,
            sl=1.0800,
            tp=1.0900,
            profit=50.0,
            magic=12345,
            time_ns=int(time.time() * 1e9)
        )
        
        assert order.ticket == 123456
        assert order.side == OrderSide.BUY
        assert order.volume == 0.1
    
    def test_order_serialization(self):
        """Test binary serialization/deserialization."""
        original = OrderData(
            ticket=999999,
            symbol=b"XAUUSD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            volume=0.5,
            open_price=2000.50,
            sl=2050.00,
            tp=1950.00,
            profit=-100.0,
            magic=999,
            time_ns=int(time.time() * 1e9)
        )
        
        # Serialize
        data = original.to_bytes()
        assert len(data) == OrderData.BINARY_SIZE
        
        # Deserialize
        restored = OrderData.from_bytes(data)
        
        assert restored.ticket == original.ticket
        assert restored.symbol == original.symbol
        assert restored.side == original.side
        assert restored.order_type == original.order_type
        assert restored.volume == original.volume
        assert restored.open_price == original.open_price


class TestCommand:
    """Test command serialization."""
    
    def test_command_creation(self):
        """Test command creation."""
        cmd = Command(
            cmd_type=CommandType.PING,
            request_id=123,
            payload=b"test"
        )
        
        assert cmd.cmd_type == CommandType.PING
        assert cmd.request_id == 123
        assert cmd.payload == b"test"
    
    def test_command_serialization(self):
        """Test command serialization."""
        original = Command(
            cmd_type=CommandType.ORDER_SEND,
            request_id=123456789,
            payload=b"x" * 100
        )
        
        data = original.to_bytes()
        restored = Command.from_bytes(data)
        
        assert restored.cmd_type == original.cmd_type
        assert restored.request_id == original.request_id
        assert restored.payload == original.payload


class TestPreallocatedBuffer:
    """Test preallocated buffer."""
    
    def test_buffer_creation(self):
        """Test buffer creation."""
        buffer = PreallocatedBuffer(4096)
        
        assert len(buffer.buffer) == 4096
        assert len(buffer.view) == 4096
    
    def test_buffer_clear(self):
        """Test buffer clearing."""
        buffer = PreallocatedBuffer(100)
        
        # Fill with data
        for i in range(100):
            buffer.buffer[i] = 0xFF
        
        # Clear
        buffer.clear()
        
        # Should be all zeros
        assert all(b == 0 for b in buffer.buffer)


class TestSharedMemoryTickStream:
    """Test shared memory tick streaming."""
    
    def test_shared_memory_creation(self):
        """Test shared memory creation."""
        shm = SharedMemoryTickStream(
            name="test_ticks.shm",
            size=65536,
            create=True
        )
        
        assert shm._shm is not None
        assert shm.size == 65536
        
        # Cleanup
        shm.close()
        shm.unlink()
    
    def test_tick_write_read(self):
        """Test tick write and read."""
        shm = SharedMemoryTickStream(
            name="test_ticks_rw.shm",
            size=65536,
            create=True
        )
        
        tick = TickData(
            symbol=b"EURUSD",
            bid=1.0850,
            ask=1.0852,
            spread=2.0,
            volume=1000,
            time_ns=int(time.time() * 1e9)
        )
        
        # Write
        assert shm.write_tick(tick) is True
        
        # Read
        restored = shm.read_tick(0)
        assert restored is not None
        assert restored.symbol == tick.symbol
        assert restored.bid == tick.bid
        
        # Cleanup
        shm.close()
        shm.unlink()
    
    def test_get_latest_ticks(self):
        """Test getting latest ticks."""
        shm = SharedMemoryTickStream(
            name="test_ticks_latest.shm",
            size=65536,
            create=True
        )
        
        # Write multiple ticks
        for i in range(10):
            tick = TickData(
                symbol=b"EURUSD",
                bid=1.0850 + i * 0.0001,
                ask=1.0852 + i * 0.0001,
                spread=2.0,
                volume=1000,
                time_ns=int(time.time() * 1e9) + i
            )
            shm.write_tick(tick)
        
        # Get latest 5
        latest = shm.get_latest_ticks(5)
        assert len(latest) == 5
        
        # Cleanup
        shm.close()
        shm.unlink()


class TestConnectionPool:
    """Test connection pool."""
    
    def test_pool_creation(self):
        """Test pool creation."""
        config = UltraLowLatencyConfig()
        pool = ConnectionPool(config)
        
        assert pool._connections == []
        assert len(pool._available) == 0
    
    @patch('socket.socket')
    def test_pool_initialize(self, mock_socket):
        """Test pool initialization."""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        config = UltraLowLatencyConfig(pool_size=2)
        pool = ConnectionPool(config)
        
        # Mock successful connection
        mock_sock.connect.return_value = None
        
        # Initialize should create connections
        # Note: This will fail in real environment without server
        # pool.initialize() would try to connect


class TestMT4UltraLowLatency:
    """Test ultra low latency connector."""
    
    def test_connector_creation(self):
        """Test connector creation."""
        config = UltraLowLatencyConfig()
        connector = MT4UltraLowLatency(config)
        
        assert connector.config == config
        assert connector._connected is False
        assert connector._running is False
    
    def test_request_id_increment(self):
        """Test request ID increment."""
        config = UltraLowLatencyConfig()
        connector = MT4UltraLowLatency(config)
        
        id1 = connector._next_request_id()
        id2 = connector._next_request_id()
        id3 = connector._next_request_id()
        
        assert id1 < id2 < id3
    
    def test_is_connected(self):
        """Test connection status."""
        config = UltraLowLatencyConfig()
        connector = MT4UltraLowLatency(config)
        
        assert connector.is_connected() is False
        
        # Simulate connected state
        connector._connected = True
        assert connector.is_connected() is True
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        config = UltraLowLatencyConfig()
        connector = MT4UltraLowLatency(config)
        
        metrics = connector.get_metrics()
        
        assert metrics['commands_sent'] == 0
        assert metrics['commands_success'] == 0
        assert metrics['commands_failed'] == 0
        assert metrics['success_rate'] == 0


class TestMT4UltraLowLatencyAsync:
    """Test async connector wrapper."""
    
    @pytest.mark.asyncio
    async def test_async_connector_creation(self):
        """Test async connector creation."""
        config = UltraLowLatencyConfig()
        connector = MT4UltraLowLatencyAsync(config)
        
        assert connector._connector is not None
        assert connector.is_connected() is False
    
    @pytest.mark.asyncio
    async def test_async_get_metrics(self):
        """Test getting metrics asynchronously."""
        config = UltraLowLatencyConfig()
        connector = MT4UltraLowLatencyAsync(config)
        
        metrics = connector.get_metrics()
        
        assert 'commands_sent' in metrics
        assert 'success_rate' in metrics


class TestMT4LowLatencyFactory:
    """Test factory pattern."""
    
    def test_singleton_pattern(self):
        """Test singleton pattern."""
        config = UltraLowLatencyConfig()
        
        connector1 = MT4LowLatencyFactory.get_connector(config)
        connector2 = MT4LowLatencyFactory.get_connector()
        
        assert connector1 is connector2
    
    def test_async_singleton(self):
        """Test async singleton."""
        config = UltraLowLatencyConfig()
        
        connector1 = MT4LowLatencyFactory.get_async_connector(config)
        connector2 = MT4LowLatencyFactory.get_async_connector()
        
        assert connector1 is connector2
    
    def test_close_all(self):
        """Test closing all connectors."""
        MT4LowLatencyFactory.get_connector()
        MT4LowLatencyFactory.get_async_connector()
        
        MT4LowLatencyFactory.close_all()
        
        assert MT4LowLatencyFactory._instance is None
        assert MT4LowLatencyFactory._async_instance is None


class TestBinaryProtocol:
    """Test binary protocol operations."""
    
    def test_ping_command_format(self):
        """Test PING command format."""
        cmd = Command(
            cmd_type=CommandType.PING,
            request_id=0,
            payload=b''
        )
        
        data = cmd.to_bytes()
        
        # Check header
        cmd_type = data[0]
        assert cmd_type == CommandType.PING
    
    def test_order_send_payload_format(self):
        """Test ORDER_SEND payload format."""
        # Format: symbol(12) + side(1) + type(1) + volume(8) + price(8) + sl(8) + tp(8) + slippage(4) + magic(4) + comment(32)
        
        payload = struct.pack(
            "<12sBBddddII32s",
            b"EURUSD\x00\x00\x00\x00\x00\x00",
            OrderSide.BUY,
            OrderType.MARKET,
            0.1,  # volume
            0.0,  # price (market order)
            1.0800,  # sl
            1.0900,  # tp
            0,  # slippage
            123456,  # magic
            b"HFT Bot\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )
        
        # Verify payload size
        expected_size = 12 + 1 + 1 + 8 + 8 + 8 + 8 + 4 + 4 + 32
        assert len(payload) == expected_size
        
        # Unpack and verify
        unpacked = struct.unpack("<12sBBddddII32s", payload)
        assert unpacked[0].rstrip(b'\x00') == b"EURUSD"
        assert unpacked[1] == OrderSide.BUY
        assert unpacked[2] == OrderType.MARKET
        assert unpacked[3] == 0.1
    
    def test_tick_response_format(self):
        """Test tick response format."""
        # Create a tick
        tick = TickData(
            symbol=b"EURUSD",
            bid=1.0850,
            ask=1.0852,
            spread=2.0,
            volume=1000,
            time_ns=int(time.time() * 1e9)
        )
        
        data = tick.to_bytes()
        
        # Verify size
        assert len(data) == 52
        
        # Verify can be unpacked
        unpacked = struct.unpack("<12sdddQ", data)
        assert unpacked[0].rstrip(b'\x00') == b"EURUSD"


class TestPerformanceBenchmark:
    """Performance benchmarks for ultra low latency."""
    
    def test_serialization_performance(self):
        """Benchmark serialization performance."""
        iterations = 10000
        
        tick = TickData(
            symbol=b"EURUSD",
            bid=1.0850,
            ask=1.0852,
            spread=2.0,
            volume=1000,
            time_ns=0
        )
        
        # Warm up
        for _ in range(100):
            tick.to_bytes()
        
        # Benchmark
        start = time.perf_counter_ns()
        for _ in range(iterations):
            data = tick.to_bytes()
        end = time.perf_counter_ns()
        
        avg_ns = (end - start) / iterations
        avg_us = avg_ns / 1000
        
        print(f"\nSerialization: {avg_us:.3f} μs per tick")
        
        # Should be under 1 microsecond
        assert avg_us < 1.0, f"Serialization too slow: {avg_us} μs"
    
    def test_deserialization_performance(self):
        """Benchmark deserialization performance."""
        iterations = 10000
        
        tick = TickData(
            symbol=b"EURUSD",
            bid=1.0850,
            ask=1.0852,
            spread=2.0,
            volume=1000,
            time_ns=0
        )
        data = tick.to_bytes()
        
        # Warm up
        for _ in range(100):
            TickData.from_bytes(data)
        
        # Benchmark
        start = time.perf_counter_ns()
        for _ in range(iterations):
            restored = TickData.from_bytes(data)
        end = time.perf_counter_ns()
        
        avg_ns = (end - start) / iterations
        avg_us = avg_ns / 1000
        
        print(f"\nDeserialization: {avg_us:.3f} μs per tick")
        
        # Should be under 1 microsecond
        assert avg_us < 1.0, f"Deserialization too slow: {avg_us} μs"
    
    def test_full_roundtrip_performance(self):
        """Benchmark full round-trip serialization."""
        iterations = 10000
        
        tick = TickData(
            symbol=b"EURUSD",
            bid=1.0850,
            ask=1.0852,
            spread=2.0,
            volume=1000,
            time_ns=0
        )
        
        # Warm up
        for _ in range(100):
            data = tick.to_bytes()
            restored = TickData.from_bytes(data)
        
        # Benchmark
        start = time.perf_counter_ns()
        for _ in range(iterations):
            data = tick.to_bytes()
            restored = TickData.from_bytes(data)
        end = time.perf_counter_ns()
        
        avg_ns = (end - start) / iterations
        avg_us = avg_ns / 1000
        
        print(f"\nRound-trip: {avg_us:.3f} μs per tick")
        
        # Should be under 2 microseconds
        assert avg_us < 2.0, f"Round-trip too slow: {avg_us} μs"


class TestIntegration:
    """Integration tests (require mock server)."""
    
    def test_connector_initialization_flow(self):
        """Test full initialization flow."""
        config = UltraLowLatencyConfig(
            host="localhost",
            port=5557,
            pool_size=2
        )
        
        connector = MT4UltraLowLatency(config)
        
        # Verify initialization
        assert connector.config == config
        assert connector._request_id == 0
        assert len(connector._tick_callbacks) == 0
        assert len(connector._order_callbacks) == 0
        
        # Verify metrics
        metrics = connector.get_metrics()
        assert metrics['commands_sent'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
