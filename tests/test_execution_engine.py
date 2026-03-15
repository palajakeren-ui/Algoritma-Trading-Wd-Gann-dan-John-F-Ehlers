"""
Tests for Execution Engine Module
Comprehensive unit tests for order execution and trade management
"""
import unittest
import sys
import os
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.execution_engine import ExecutionEngine


class TestExecutionEngine(unittest.TestCase):
    """Test cases for Execution Engine"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = {
            'max_slippage': 0.001,
            'max_latency_ms': 100,
            'retry_attempts': 3,
            'paper_trading': True,
            'paper_balance': 100000,
            'execution_mode': 'paper'
        }
        cls.execution_engine = ExecutionEngine(cls.config)
    
    def setUp(self):
        """Reset engine state before each test"""
        self.execution_engine.reset_paper_trading()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsNotNone(self.execution_engine)
        self.assertTrue(self.execution_engine.config.get('paper_trading'))
    
    def test_paper_order_execution_buy(self):
        """Test paper trading buy order execution"""
        result = self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=0.1,
            price=45000
        )
        
        self.assertIsNotNone(result)
        self.assertIn('order_id', result)
        self.assertEqual(result['status'], 'FILLED')
        self.assertEqual(result['side'], 'BUY')
    
    def test_paper_order_execution_sell(self):
        """Test paper trading sell order execution"""
        # First buy
        self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=0.1,
            price=45000
        )
        
        # Then sell
        result = self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='SELL',
            order_type='MARKET',
            quantity=0.1,
            price=46000
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'FILLED')
        self.assertEqual(result['side'], 'SELL')
    
    def test_limit_order_creation(self):
        """Test limit order creation"""
        result = self.execution_engine.execute_order(
            symbol='ETH/USDT',
            side='BUY',
            order_type='LIMIT',
            quantity=1.0,
            price=2500
        )
        
        self.assertIsNotNone(result)
        self.assertIn('order_id', result)
        self.assertIn(result['status'], ['PENDING', 'FILLED', 'NEW'])
    
    def test_stop_loss_order(self):
        """Test stop loss order creation"""
        result = self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='SELL',
            order_type='STOP_LOSS',
            quantity=0.1,
            price=44000,
            stop_price=44000
        )
        
        self.assertIsNotNone(result)
        self.assertIn('order_id', result)
    
    def test_take_profit_order(self):
        """Test take profit order creation"""
        result = self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='SELL',
            order_type='TAKE_PROFIT',
            quantity=0.1,
            price=48000,
            stop_price=48000
        )
        
        self.assertIsNotNone(result)
        self.assertIn('order_id', result)
    
    def test_latency_check(self):
        """Test execution latency measurement"""
        start_time = datetime.now()
        
        result = self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=0.01,
            price=45000
        )
        
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Paper trading should be fast
        self.assertLess(latency_ms, 1000)  # Should complete within 1 second
    
    def test_slippage_calculation(self):
        """Test slippage calculation"""
        expected_price = 45000
        actual_price = 45050
        
        slippage = self.execution_engine.calculate_slippage(expected_price, actual_price)
        
        self.assertIsNotNone(slippage)
        self.assertAlmostEqual(slippage, 0.00111, places=4)
    
    def test_order_validation(self):
        """Test order validation"""
        # Valid order
        is_valid = self.execution_engine.validate_order(
            symbol='BTC/USDT',
            side='BUY',
            quantity=0.1,
            price=45000
        )
        self.assertTrue(is_valid)
        
        # Invalid quantity
        is_valid = self.execution_engine.validate_order(
            symbol='BTC/USDT',
            side='BUY',
            quantity=-0.1,
            price=45000
        )
        self.assertFalse(is_valid)
    
    def test_position_tracking(self):
        """Test position tracking after order execution"""
        # Execute buy order
        self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=0.1,
            price=45000
        )
        
        positions = self.execution_engine.get_positions()
        
        self.assertIsNotNone(positions)
        self.assertIn('BTC/USDT', positions)
    
    def test_balance_tracking(self):
        """Test balance tracking after trades"""
        initial_balance = self.execution_engine.get_balance()
        
        # Execute trade
        self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=0.1,
            price=45000
        )
        
        new_balance = self.execution_engine.get_balance()
        
        # Balance should decrease after buy
        self.assertLess(new_balance, initial_balance)
    
    def test_order_cancellation(self):
        """Test order cancellation"""
        # Create limit order
        order = self.execution_engine.execute_order(
            symbol='ETH/USDT',
            side='BUY',
            order_type='LIMIT',
            quantity=1.0,
            price=2000  # Low price to stay pending
        )
        
        # Cancel order
        result = self.execution_engine.cancel_order(order['order_id'])
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('status'), 'CANCELLED')
    
    def test_get_open_orders(self):
        """Test retrieving open orders"""
        # Create limit order
        self.execution_engine.execute_order(
            symbol='ETH/USDT',
            side='BUY',
            order_type='LIMIT',
            quantity=1.0,
            price=2000
        )
        
        open_orders = self.execution_engine.get_open_orders()
        
        self.assertIsNotNone(open_orders)
        self.assertIsInstance(open_orders, list)
    
    def test_execution_with_insufficient_balance(self):
        """Test order rejection due to insufficient balance"""
        # Try to buy more than available balance
        result = self.execution_engine.execute_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=10000,  # Very large quantity
            price=45000
        )
        
        # Should be rejected
        self.assertIn(result.get('status'), ['REJECTED', 'INSUFFICIENT_BALANCE', 'ERROR'])


class TestExecutionEngineIntegration(unittest.TestCase):
    """Integration tests for Execution Engine"""
    
    def test_full_trade_lifecycle(self):
        """Test complete trade lifecycle: open, monitor, close"""
        config = {'paper_trading': True, 'paper_balance': 100000}
        engine = ExecutionEngine(config)
        
        # 1. Open position
        entry = engine.execute_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=0.1,
            price=45000
        )
        self.assertEqual(entry['status'], 'FILLED')
        
        # 2. Check position
        positions = engine.get_positions()
        self.assertIn('BTC/USDT', positions)
        
        # 3. Close position
        exit_order = engine.execute_order(
            symbol='BTC/USDT',
            side='SELL',
            order_type='MARKET',
            quantity=0.1,
            price=46000
        )
        self.assertEqual(exit_order['status'], 'FILLED')
        
        # 4. Verify P&L
        pnl = engine.get_realized_pnl()
        self.assertIsNotNone(pnl)


if __name__ == '__main__':
    unittest.main()
