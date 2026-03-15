"""
Smart Order Router
Routes orders through the complete execution pipeline:
Data → Risk Check → Circuit Breaker → Duplicate Guard → Slippage Estimate → 
Retry Engine → Broker Connector → Latency Log → Slippage Record
"""

import uuid
import time
from typing import Dict, Optional, Callable, Any, Tuple
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.risk.pre_trade_check import PreTradeCheck, PreTradeResult
from src.risk.circuit_breaker import CircuitBreaker
from src.risk.drawdown_protector import DrawdownProtector
from src.execution.slippage_model import SlippageModel
from src.execution.retry_engine import RetryEngine, RetryConfig
from src.execution.duplicate_guard import DuplicateGuard
from src.execution.latency_logger import LatencyLogger


class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass
class OrderTicket:
    """Complete order ticket with full lifecycle tracking."""
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    leverage: int = 1
    broker: str = "paper"
    
    # Lifecycle
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Execution details
    fill_price: float = 0.0
    filled_quantity: float = 0.0
    slippage_bps: float = 0.0
    latency_ms: float = 0.0
    retry_count: int = 0
    
    # Risk check
    pre_trade_result: Optional[Dict] = None
    idempotency_key: str = ""
    broker_order_id: str = ""
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "leverage": self.leverage,
            "broker": self.broker,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "fill_price": self.fill_price,
            "filled_quantity": self.filled_quantity,
            "slippage_bps": round(self.slippage_bps, 2),
            "latency_ms": round(self.latency_ms, 1),
            "retry_count": self.retry_count,
            "error_message": self.error_message,
        }


class OrderRouter:
    """
    Production order router that enforces the complete execution pipeline.
    
    Every order goes through:
    1. Pre-trade risk check
    2. Circuit breaker check
    3. Duplicate detection
    4. Position size adjustment (drawdown protector)
    5. Slippage estimation
    6. Submission with retry
    7. Latency logging
    8. Actual slippage recording
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        # Initialize all sub-components
        self.pre_trade = PreTradeCheck(config.get("risk", {}))
        self.circuit_breaker = CircuitBreaker(config.get("circuit_breaker", {}))
        self.drawdown_protector = DrawdownProtector(config.get("drawdown", {}))
        self.slippage_model = SlippageModel(config.get("slippage", {}))
        self.retry_engine = RetryEngine(RetryConfig(
            max_retries=config.get("max_retries", 3),
            initial_delay_ms=config.get("retry_delay_ms", 200),
        ))
        self.duplicate_guard = DuplicateGuard(config.get("dedup", {}))
        self.latency_logger = LatencyLogger(config.get("latency", {}))
        
        # Broker connectors (injected)
        self._connectors: Dict[str, Any] = {}
        
        # Order book
        self._orders: Dict[str, OrderTicket] = {}
        self._positions: Dict[str, Dict] = {}
        
        # Callbacks
        self._on_fill: Optional[Callable] = None
        self._on_reject: Optional[Callable] = None
    
    def register_connector(self, broker_name: str, connector: Any):
        """Register a broker connector."""
        self._connectors[broker_name] = connector
        logger.info(f"Registered broker connector: {broker_name}")
    
    def register_callbacks(
        self,
        on_fill: Callable = None,
        on_reject: Callable = None,
    ):
        """Register event callbacks."""
        self._on_fill = on_fill
        self._on_reject = on_reject
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_type: str = "MARKET",
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        leverage: int = 1,
        broker: str = "paper",
        account_balance: float = 0.0,
        signal_source: str = "",
    ) -> OrderTicket:
        """
        Submit an order through the complete execution pipeline.
        
        This is the ONLY way to submit orders. Direct broker access is blocked.
        """
        # Create order ticket
        order = OrderTicket(
            id=f"ORD-{uuid.uuid4().hex[:12].upper()}",
            symbol=symbol,
            side=side.upper(),
            order_type=order_type.upper(),
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=leverage,
            broker=broker,
        )
        
        logger.info(f"Order pipeline START: {order.id} | {symbol} {side} {quantity:.6f} @ {price}")
        
        # STEP 1: Circuit breaker check
        if not self.circuit_breaker.check_order():
            order.status = OrderStatus.REJECTED
            order.error_message = "Circuit breaker is tripped"
            self._orders[order.id] = order
            self._notify_reject(order)
            return order
        
        # STEP 2: Duplicate check
        idem_key = self.duplicate_guard.generate_idempotency_key(symbol, side, quantity, price, order_type)
        order.idempotency_key = idem_key
        
        if self.duplicate_guard.check_duplicate(symbol, side, quantity, price, order_type, idem_key):
            order.status = OrderStatus.REJECTED
            order.error_message = "Duplicate order detected"
            self._orders[order.id] = order
            self._notify_reject(order)
            return order
        
        # STEP 3: Drawdown position size adjustment
        dd_multiplier = self.drawdown_protector.get_position_size_multiplier()
        if dd_multiplier < 1.0:
            original_qty = quantity
            quantity = quantity * dd_multiplier
            order.quantity = quantity
            logger.info(f"Drawdown adjusted: {original_qty:.6f} → {quantity:.6f} ({dd_multiplier:.0%})")
        
        if dd_multiplier == 0:
            order.status = OrderStatus.REJECTED
            order.error_message = "Drawdown protector has locked trading"
            self._orders[order.id] = order
            self._notify_reject(order)
            return order
        
        # STEP 4: Pre-trade risk check
        pre_trade_result = self.pre_trade.check(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=leverage,
            account_balance=account_balance,
            current_positions=self._positions,
            circuit_breaker_ok=True,  # Already checked
            drawdown_multiplier=dd_multiplier,
        )
        order.pre_trade_result = pre_trade_result.to_dict()
        
        if not pre_trade_result.approved:
            order.status = OrderStatus.REJECTED
            order.error_message = f"Pre-trade check failed: {pre_trade_result.rejections}"
            self._orders[order.id] = order
            self._notify_reject(order)
            return order
        
        # Apply adjusted size if any
        if pre_trade_result.adjusted_size is not None:
            order.quantity = pre_trade_result.adjusted_size
        
        # STEP 5: Slippage estimation
        estimated_slippage = self.slippage_model.estimate_slippage(
            price=price,
            side=side,
            quantity=order.quantity,
        )
        
        # STEP 6: Submit with retry
        timer_start = self.latency_logger.start_timer()
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.utcnow()
        
        connector = self._connectors.get(broker)
        if connector is None and broker != "paper":
            order.status = OrderStatus.FAILED
            order.error_message = f"No connector registered for broker: {broker}"
            self._orders[order.id] = order
            return order
        
        if broker == "paper":
            # Paper trading simulation
            order = self._execute_paper(order, estimated_slippage)
        else:
            # Live execution with retry
            retry_result = self.retry_engine.execute_with_retry(
                operation=lambda **kw: self._execute_live(order, connector),
                operation_name="submit_order",
                order_id=order.id,
                circuit_breaker_check=lambda: self.circuit_breaker.check_order(),
            )
            
            order.retry_count = retry_result.attempts
            
            if not retry_result.success:
                order.status = OrderStatus.FAILED
                order.error_message = retry_result.last_error
                self.circuit_breaker.record_execution_failure(retry_result.last_error)
            else:
                self.circuit_breaker.record_execution_success()
        
        # STEP 7: Record latency
        self.latency_logger.record(
            order_id=order.id,
            symbol=symbol,
            broker=broker,
            operation="submit",
            start_time=timer_start,
            success=order.status == OrderStatus.FILLED,
        )
        
        # STEP 8: Record actual slippage
        if order.status == OrderStatus.FILLED and order.fill_price > 0:
            self.slippage_model.record_actual_slippage(
                order_id=order.id,
                symbol=symbol,
                side=side,
                expected_price=price,
                actual_price=order.fill_price,
            )
        
        # Record in duplicate guard
        self.duplicate_guard.record_order_sent(symbol, idem_key)
        
        # Store order
        self._orders[order.id] = order
        
        # Notify callbacks
        if order.status == OrderStatus.FILLED and self._on_fill:
            try:
                self._on_fill(order)
            except Exception as e:
                logger.error(f"Error in on_fill callback: {e}")
        
        logger.info(
            f"Order pipeline END: {order.id} | Status={order.status.value} | "
            f"Fill={order.fill_price:.4f} | Slippage={order.slippage_bps:.1f}bps | "
            f"Latency={order.latency_ms:.0f}ms | Retries={order.retry_count}"
        )
        
        return order
    
    def _execute_paper(self, order: OrderTicket, estimated_slippage: float) -> OrderTicket:
        """Execute order in paper trading mode with realistic simulation."""
        # Simulate latency (50-200ms)
        import random
        sim_latency = random.uniform(50, 200)
        time.sleep(sim_latency / 1000)
        
        # Simulate fill with slippage
        fill_price = order.price + estimated_slippage
        
        # Simulate partial fills occasionally (10% chance)
        if random.random() < 0.1:
            order.filled_quantity = order.quantity * random.uniform(0.5, 0.95)
            order.status = OrderStatus.PARTIALLY_FILLED
        else:
            order.filled_quantity = order.quantity
            order.status = OrderStatus.FILLED
        
        order.fill_price = fill_price
        order.filled_at = datetime.utcnow()
        order.latency_ms = sim_latency
        
        if order.price > 0:
            order.slippage_bps = ((fill_price - order.price) / order.price) * 10000
        
        return order
    
    def _execute_live(self, order: OrderTicket, connector: Any) -> Dict:
        """Execute order on live broker."""
        # This calls the actual broker connector
        result = connector.create_order(
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
        )
        
        order.broker_order_id = str(result.get("id", ""))
        order.fill_price = float(result.get("price", order.price))
        order.filled_quantity = float(result.get("filled", order.quantity))
        order.status = OrderStatus.FILLED
        order.filled_at = datetime.utcnow()
        
        if order.price > 0:
            order.slippage_bps = ((order.fill_price - order.price) / order.price) * 10000
        
        return result
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if order_id not in self._orders:
            logger.warning(f"Order {order_id} not found for cancellation")
            return False
        
        order = self._orders[order_id]
        if order.status not in (OrderStatus.PENDING, OrderStatus.SUBMITTED):
            logger.warning(f"Cannot cancel order {order_id} in state {order.status.value}")
            return False
        
        order.status = OrderStatus.CANCELLED
        logger.info(f"Order {order_id} cancelled")
        return True
    
    def get_order(self, order_id: str) -> Optional[OrderTicket]:
        """Get order by ID."""
        return self._orders.get(order_id)
    
    def get_all_orders(self) -> Dict[str, OrderTicket]:
        """Get all orders."""
        return self._orders
    
    def update_position(self, symbol: str, position_data: Dict):
        """Update position tracking."""
        self._positions[symbol] = position_data
    
    def remove_position(self, symbol: str):
        """Remove closed position."""
        self._positions.pop(symbol, None)
    
    def _notify_reject(self, order: OrderTicket):
        """Notify rejection callbacks."""
        if self._on_reject:
            try:
                self._on_reject(order)
            except Exception as e:
                logger.error(f"Error in on_reject callback: {e}")
    
    def get_execution_stats(self) -> Dict:
        """Get comprehensive execution statistics."""
        orders = list(self._orders.values())
        filled = [o for o in orders if o.status == OrderStatus.FILLED]
        rejected = [o for o in orders if o.status == OrderStatus.REJECTED]
        failed = [o for o in orders if o.status == OrderStatus.FAILED]
        
        return {
            "total_orders": len(orders),
            "filled": len(filled),
            "rejected": len(rejected),
            "failed": len(failed),
            "fill_rate": round(len(filled) / max(len(orders), 1) * 100, 1),
            "avg_slippage_bps": round(
                sum(o.slippage_bps for o in filled) / max(len(filled), 1), 2
            ),
            "avg_latency_ms": round(
                sum(o.latency_ms for o in filled) / max(len(filled), 1), 1
            ),
            "slippage_stats": self.slippage_model.get_stats(),
            "latency_stats": self.latency_logger.get_stats(),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "drawdown": self.drawdown_protector.get_status(),
        }
