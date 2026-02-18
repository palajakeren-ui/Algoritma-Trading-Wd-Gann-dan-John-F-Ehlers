"""
Execution Gate Module
Trading mode-aware execution with AI signal integration and risk checks.
"""
import numpy as np
from loguru import logger
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import time
import json

from core.signal_engine import AISignal, SignalType, get_signal_engine
from core.risk_engine import RiskEngine, RiskCheckResult, get_risk_engine
from connectors.exchange_connector import (
    Order, OrderSide, OrderType, OrderStatus, 
    ExchangeConnectorFactory, ExchangeCredentials
)


class TradingMode(Enum):
    MANUAL = "manual"
    AI_ASSISTED = "ai_assisted"
    AI_FULL_AUTO = "ai_full_auto"
    PAPER_TRADING = "paper_trading"


class ExecutionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionRequest:
    """Execution request from AI signal."""
    id: str
    signal: AISignal
    trading_mode: TradingMode
    account_id: str
    exchange: str
    position_size: float
    leverage: int = 1
    status: ExecutionStatus = ExecutionStatus.PENDING
    risk_check_result: Optional[RiskCheckResult] = None
    order: Optional[Order] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class ExecutionGate:
    """
    AI Execution Gate - Controls signal-to-execution flow.
    
    Features:
    - Trading mode awareness (manual/AI-assisted/AI full-auto)
    - AI signal → risk check → execution pipeline
    - Hard safety lock when risk violated
    - Paper trading mode support
    - Multi-account execution
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.trading_mode = TradingMode(self.config.get('trading_mode', 'manual'))
        self.paper_trading = self.config.get('paper_trading', True)
        
        # Engines
        self.signal_engine = get_signal_engine()
        self.risk_engines: Dict[str, RiskEngine] = {}
        
        # Execution tracking
        self.pending_requests: Dict[str, ExecutionRequest] = {}
        self.execution_history: List[ExecutionRequest] = []
        
        # Safety
        self.global_kill_switch = False
        self.max_concurrent_orders = self.config.get('max_concurrent_orders', 5)
        
        # Callbacks
        self._execution_callbacks: List[Callable] = []
        self._approval_callbacks: List[Callable] = []
        
        logger.info(f"ExecutionGate initialized in {self.trading_mode.value} mode")
    
    def set_trading_mode(self, mode: TradingMode):
        """Set trading mode."""
        self.trading_mode = mode
        logger.info(f"Trading mode set to: {mode.value}")
    
    def get_risk_engine(self, account_id: str) -> RiskEngine:
        """Get or create risk engine for account."""
        if account_id not in self.risk_engines:
            self.risk_engines[account_id] = get_risk_engine(account_id)
        return self.risk_engines[account_id]
    
    async def process_signal(
        self,
        signal: AISignal,
        account_id: str,
        exchange: str,
        position_size: float = None,
        leverage: int = 1
    ) -> ExecutionRequest:
        """
        Process AI signal through execution gate.
        
        Args:
            signal: AI trading signal
            account_id: Account to trade on
            exchange: Exchange to execute on
            position_size: Position size (auto-calculated if None)
            leverage: Leverage to use
            
        Returns:
            ExecutionRequest with status
        """
        request_id = f"EXE_{int(time.time() * 1000)}"
        
        request = ExecutionRequest(
            id=request_id,
            signal=signal,
            trading_mode=self.trading_mode,
            account_id=account_id,
            exchange=exchange,
            position_size=position_size or 0,
            leverage=leverage
        )
        
        # 1. Check global kill switch
        if self.global_kill_switch:
            request.status = ExecutionStatus.REJECTED
            request.metadata['rejection_reason'] = "Global kill switch active"
            logger.warning(f"Execution rejected: Kill switch active")
            return request
        
        # 2. Check signal validity
        if signal.signal == SignalType.HOLD:
            request.status = ExecutionStatus.REJECTED
            request.metadata['rejection_reason'] = "HOLD signal - no action"
            return request
        
        # 3. Risk check
        risk_engine = self.get_risk_engine(account_id)
        
        # Calculate position size if not provided
        if position_size is None or position_size <= 0:
            sizing = risk_engine.calculate_position_size(
                account_balance=risk_engine.current_equity or 10000,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss
            )
            request.position_size = sizing.get('position_size', 0.01)
        
        # Run risk check
        risk_result = risk_engine.check_trade_risk(
            symbol=signal.symbol,
            side='buy' if signal.signal in [SignalType.BUY, SignalType.STRONG_BUY] else 'sell',
            order_type='market',
            quantity=request.position_size,
            price=signal.entry_price,
            stop_loss=signal.stop_loss,
            leverage=leverage
        )
        
        request.risk_check_result = risk_result
        
        if not risk_result.passed:
            request.status = ExecutionStatus.REJECTED
            request.metadata['rejection_reason'] = "Risk check failed"
            request.metadata['violations'] = [v.value for v in risk_result.violations]
            logger.warning(f"Execution rejected: Risk violations {risk_result.violations}")
            return request
        
        # Adjust position size if recommended
        if risk_result.adjusted_position_size:
            request.position_size = risk_result.adjusted_position_size
            logger.info(f"Position size adjusted to {request.position_size}")
        
        # 4. Mode-specific handling
        if self.trading_mode == TradingMode.MANUAL:
            # Store for manual approval
            request.status = ExecutionStatus.PENDING
            self.pending_requests[request_id] = request
            logger.info(f"Execution pending manual approval: {request_id}")
            
            # Notify approval callbacks
            for callback in self._approval_callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Approval callback error: {e}")
        
        elif self.trading_mode == TradingMode.AI_ASSISTED:
            # Require approval but highlight recommendation
            request.status = ExecutionStatus.PENDING
            request.metadata['ai_recommendation'] = 'EXECUTE'
            self.pending_requests[request_id] = request
            logger.info(f"AI-assisted execution pending approval: {request_id}")
        
        elif self.trading_mode == TradingMode.AI_FULL_AUTO:
            # Execute automatically
            request.status = ExecutionStatus.APPROVED
            await self._execute_order(request)
        
        elif self.trading_mode == TradingMode.PAPER_TRADING:
            # Simulate execution
            request.status = ExecutionStatus.APPROVED
            await self._simulate_execution(request)
        
        # Store in history
        self.execution_history.append(request)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]
        
        return request
    
    async def approve_execution(self, request_id: str) -> Optional[ExecutionRequest]:
        """Manually approve a pending execution."""
        if request_id not in self.pending_requests:
            logger.warning(f"Execution request not found: {request_id}")
            return None
        
        request = self.pending_requests.pop(request_id)
        request.status = ExecutionStatus.APPROVED
        
        if self.paper_trading:
            await self._simulate_execution(request)
        else:
            await self._execute_order(request)
        
        return request
    
    async def reject_execution(self, request_id: str, reason: str = None) -> Optional[ExecutionRequest]:
        """Manually reject a pending execution."""
        if request_id not in self.pending_requests:
            return None
        
        request = self.pending_requests.pop(request_id)
        request.status = ExecutionStatus.REJECTED
        request.metadata['rejection_reason'] = reason or "Manual rejection"
        
        logger.info(f"Execution rejected: {request_id}")
        return request
    
    async def _execute_order(self, request: ExecutionRequest) -> bool:
        """Execute order on exchange."""
        try:
            # Get connector
            connector = ExchangeConnectorFactory.get_connector(
                request.exchange,
                request.account_id
            )
            
            if not connector or not connector.is_connected:
                request.status = ExecutionStatus.FAILED
                request.metadata['error'] = "Exchange not connected"
                return False
            
            # Determine order side
            side = OrderSide.BUY if request.signal.signal in [
                SignalType.BUY, SignalType.STRONG_BUY
            ] else OrderSide.SELL
            
            # Create order
            order = Order(
                id="",
                client_order_id=f"AI_{request.id}",
                symbol=request.signal.symbol,
                side=side,
                type=OrderType.MARKET,
                amount=request.position_size,
                price=request.signal.entry_price,
                leverage=request.leverage
            )
            
            # Execute
            executed_order = await connector.create_order(order)
            request.order = executed_order
            
            if executed_order.status == OrderStatus.OPEN or executed_order.status == OrderStatus.FILLED:
                request.status = ExecutionStatus.EXECUTED
                logger.success(f"Order executed: {executed_order.id}")
                
                # Notify callbacks
                for callback in self._execution_callbacks:
                    try:
                        callback(request)
                    except Exception as e:
                        logger.error(f"Execution callback error: {e}")
                
                return True
            else:
                request.status = ExecutionStatus.FAILED
                request.metadata['error'] = "Order rejected by exchange"
                return False
                
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            request.status = ExecutionStatus.FAILED
            request.metadata['error'] = str(e)
            return False
    
    async def _simulate_execution(self, request: ExecutionRequest) -> bool:
        """Simulate order execution for paper trading."""
        try:
            side = OrderSide.BUY if request.signal.signal in [
                SignalType.BUY, SignalType.STRONG_BUY
            ] else OrderSide.SELL
            
            # Create simulated order
            order = Order(
                id=f"PAPER_{int(time.time() * 1000)}",
                client_order_id=f"PAPER_AI_{request.id}",
                symbol=request.signal.symbol,
                side=side,
                type=OrderType.MARKET,
                amount=request.position_size,
                price=request.signal.entry_price,
                status=OrderStatus.FILLED,
                filled=request.position_size,
                average_price=request.signal.entry_price,
                exchange="paper",
                account_id=request.account_id
            )
            
            request.order = order
            request.status = ExecutionStatus.EXECUTED
            request.metadata['paper_trade'] = True
            
            logger.success(f"Paper trade executed: {order.id}")
            
            # Notify callbacks
            for callback in self._execution_callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Execution callback error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Paper trade simulation failed: {e}")
            request.status = ExecutionStatus.FAILED
            return False
    
    def activate_kill_switch(self, reason: str = None):
        """Activate global kill switch."""
        self.global_kill_switch = True
        logger.critical(f"KILL SWITCH ACTIVATED: {reason or 'Manual activation'}")
        
        # Cancel all pending requests
        for req_id, request in list(self.pending_requests.items()):
            request.status = ExecutionStatus.CANCELLED
            request.metadata['cancellation_reason'] = "Kill switch activated"
        
        self.pending_requests.clear()
    
    def deactivate_kill_switch(self, confirmation: str = None):
        """Deactivate global kill switch."""
        if confirmation == "CONFIRM_RESUME":
            self.global_kill_switch = False
            logger.warning("Kill switch deactivated. Trading resumed.")
            return True
        else:
            logger.warning("Kill switch deactivation requires confirmation")
            return False
    
    def on_execution(self, callback: Callable):
        """Register execution callback."""
        self._execution_callbacks.append(callback)
    
    def on_approval_required(self, callback: Callable):
        """Register approval callback."""
        self._approval_callbacks.append(callback)
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending execution requests."""
        return [
            {
                'id': req.id,
                'symbol': req.signal.symbol,
                'signal': req.signal.signal.value,
                'confidence': req.signal.confidence,
                'position_size': req.position_size,
                'account_id': req.account_id,
                'exchange': req.exchange,
                'timestamp': req.timestamp.isoformat()
            }
            for req in self.pending_requests.values()
        ]
    
    def get_execution_history(self, limit: int = 50) -> List[Dict]:
        """Get execution history."""
        return [
            {
                'id': req.id,
                'symbol': req.signal.symbol,
                'signal': req.signal.signal.value,
                'status': req.status.value,
                'position_size': req.position_size,
                'order_id': req.order.id if req.order else None,
                'timestamp': req.timestamp.isoformat()
            }
            for req in self.execution_history[-limit:]
        ]
    
    def get_status(self) -> Dict:
        """Get execution gate status."""
        return {
            'trading_mode': self.trading_mode.value,
            'paper_trading': self.paper_trading,
            'kill_switch_active': self.global_kill_switch,
            'pending_requests': len(self.pending_requests),
            'total_executions': len(self.execution_history),
            'accounts_active': len(self.risk_engines)
        }


# Global execution gate instance
_execution_gate: Optional[ExecutionGate] = None


def get_execution_gate(config: Dict = None) -> ExecutionGate:
    """Get or create execution gate."""
    global _execution_gate
    if _execution_gate is None:
        _execution_gate = ExecutionGate(config)
    return _execution_gate


if __name__ == "__main__":
    import asyncio
    
    async def test():
        gate = ExecutionGate({'trading_mode': 'paper_trading', 'paper_trading': True})
        
        # Create test signal
        from core.signal_engine import AISignal, SignalStrength
        
        signal = AISignal(
            symbol="BTC/USDT",
            timeframe="H1",
            signal=SignalType.BUY,
            confidence=75.0,
            strength=SignalStrength.STRONG,
            entry_price=45000.0,
            stop_loss=44000.0,
            take_profit=47000.0,
            risk_reward=2.0
        )
        
        # Initialize risk engine with equity
        risk_engine = gate.get_risk_engine("test_account")
        risk_engine.initialize_equity(10000)
        
        # Process signal
        result = await gate.process_signal(
            signal=signal,
            account_id="test_account",
            exchange="binance",
            leverage=5
        )
        
        print(f"\nExecution Result:")
        print(f"  Status: {result.status.value}")
        print(f"  Position Size: {result.position_size}")
        if result.order:
            print(f"  Order ID: {result.order.id}")
    
    asyncio.run(test())
