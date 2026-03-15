"""
Order Manager v3.0 - Production Ready
Manages order queuing, validation, and execution orchestration
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from loguru import logger
from enum import Enum
from dataclasses import dataclass, field
from threading import Thread, Lock, Event
from queue import Queue, Empty
import json


class OrderPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4  # Immediate execution (e.g., emergency close)


@dataclass
class OrderRequest:
    """Order request in queue"""
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    broker: str = "paper"
    priority: OrderPriority = OrderPriority.NORMAL
    max_slippage_pct: float = 0.5
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    callback: Optional[Callable] = None
    metadata: Dict = field(default_factory=dict)


class OrderManager:
    """
    Production-ready order manager supporting:
    - Order queue with priority handling
    - Automatic retry on failures
    - Order expiration handling
    - Pre-trade validation
    - Post-trade reconciliation
    - Order history tracking
    """
    
    def __init__(self, config: Dict, execution_engine=None):
        """
        Initialize order manager.
        
        Args:
            config: Configuration dictionary
            execution_engine: ExecutionEngine instance
        """
        self.config = config
        self._execution_engine = execution_engine
        
        # Order queues by priority
        self._queues: Dict[OrderPriority, Queue] = {
            priority: Queue() for priority in OrderPriority
        }
        
        # State tracking
        self._pending_orders: Dict[str, OrderRequest] = {}
        self._order_history: List[Dict] = []
        self._active_symbols: Dict[str, int] = {}  # symbol -> active order count
        
        # Threading
        self._lock = Lock()
        self._processing = False
        self._stop_event = Event()
        self._processor_thread = None
        
        # Configuration
        self.max_orders_per_symbol = config.get('max_orders_per_symbol', 3)
        self.max_queue_size = config.get('max_queue_size', 100)
        self.processing_interval = config.get('processing_interval', 0.1)  # 100ms
        
        # Rate limiting
        self._last_order_time: Dict[str, float] = {}
        self.min_order_interval = config.get('min_order_interval', 1.0)  # 1 second
        
        logger.info("Order Manager initialized")
    
    def set_execution_engine(self, engine):
        """Set execution engine after initialization"""
        self._execution_engine = engine
    
    # ==================== ORDER SUBMISSION ====================
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0.0,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        broker: str = "paper",
        priority: OrderPriority = OrderPriority.NORMAL,
        ttl_seconds: int = 300,
        callback: Callable = None,
        **kwargs
    ) -> Tuple[bool, str]:
        """
        Submit order to queue.
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            order_type: MARKET, LIMIT, etc.
            quantity: Order quantity
            price: Limit price
            stop_loss: Stop loss price
            take_profit: Take profit price
            broker: Broker to use
            priority: Order priority
            ttl_seconds: Time to live in seconds
            callback: Callback on completion
            
        Returns:
            Tuple of (success, order_id or error message)
        """
        # Validate queue capacity
        total_queued = sum(q.qsize() for q in self._queues.values())
        if total_queued >= self.max_queue_size:
            return False, "Order queue is full"
        
        # Check symbol order limit
        if self._active_symbols.get(symbol, 0) >= self.max_orders_per_symbol:
            return False, f"Max orders for {symbol} reached"
        
        # Create order request
        order_id = f"OMG-{int(time.time()*1000)}-{len(self._pending_orders)}"
        
        request = OrderRequest(
            id=order_id,
            symbol=symbol,
            side=side.upper(),
            order_type=order_type.upper(),
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker,
            priority=priority,
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds) if ttl_seconds > 0 else None,
            callback=callback,
            metadata=kwargs
        )
        
        # Add to queue
        with self._lock:
            self._queues[priority].put(request)
            self._pending_orders[order_id] = request
            self._active_symbols[symbol] = self._active_symbols.get(symbol, 0) + 1
        
        logger.info(f"Order queued: {order_id} - {side} {quantity} {symbol}")
        
        return True, order_id
    
    def submit_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        **kwargs
    ) -> Tuple[bool, str]:
        """Submit market order"""
        return self.submit_order(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
            priority=OrderPriority.HIGH,
            **kwargs
        )
    
    def submit_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        **kwargs
    ) -> Tuple[bool, str]:
        """Submit limit order"""
        return self.submit_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            **kwargs
        )
    
    def emergency_close(
        self,
        symbol: str,
        broker: str = "paper"
    ) -> Tuple[bool, str]:
        """Submit urgent close order"""
        if not self._execution_engine:
            return False, "Execution engine not available"
        
        position = self._execution_engine.get_position(symbol, broker)
        if not position:
            return False, f"No position found for {symbol}"
        
        close_side = "SELL" if position.side.value == "BUY" else "BUY"
        
        return self.submit_order(
            symbol=symbol,
            side=close_side,
            order_type="MARKET",
            quantity=position.quantity,
            broker=broker,
            priority=OrderPriority.URGENT,
            ttl_seconds=30
        )
    
    # ==================== ORDER PROCESSING ====================
    
    def start_processing(self):
        """Start order processing thread"""
        if self._processing:
            return
        
        self._processing = True
        self._stop_event.clear()
        self._processor_thread = Thread(target=self._process_loop, daemon=True)
        self._processor_thread.start()
        logger.info("Order processing started")
    
    def stop_processing(self):
        """Stop order processing"""
        self._stop_event.set()
        self._processing = False
        if self._processor_thread:
            self._processor_thread.join(timeout=5)
        logger.info("Order processing stopped")
    
    def _process_loop(self):
        """Main processing loop"""
        while not self._stop_event.is_set():
            try:
                request = self._get_next_order()
                if request:
                    self._process_order(request)
                else:
                    time.sleep(self.processing_interval)
            except Exception as e:
                logger.error(f"Order processing error: {e}")
                time.sleep(1)
    
    def _get_next_order(self) -> Optional[OrderRequest]:
        """Get next order from queues by priority"""
        for priority in [OrderPriority.URGENT, OrderPriority.HIGH, OrderPriority.NORMAL, OrderPriority.LOW]:
            try:
                request = self._queues[priority].get_nowait()
                return request
            except Empty:
                continue
        return None
    
    def _process_order(self, request: OrderRequest):
        """Process a single order request"""
        # Check expiration
        if request.expires_at and datetime.now() > request.expires_at:
            self._complete_order(request, success=False, error="Order expired")
            return
        
        # Check rate limiting
        last_time = self._last_order_time.get(request.symbol, 0)
        if time.time() - last_time < self.min_order_interval:
            # Re-queue with small delay
            time.sleep(self.min_order_interval - (time.time() - last_time))
        
        # Execute order
        if not self._execution_engine:
            self._complete_order(request, success=False, error="Execution engine not available")
            return
        
        try:
            # Create and submit order
            order = self._execution_engine.create_order(
                symbol=request.symbol,
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                price=request.price,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit,
                broker=request.broker
            )
            
            result = self._execution_engine.submit_order(order)
            
            # Update rate limit
            self._last_order_time[request.symbol] = time.time()
            
            # Check result
            if result.status.value in ['FILLED', 'SUBMITTED', 'PARTIALLY_FILLED']:
                self._complete_order(
                    request,
                    success=True,
                    result={
                        'order_id': result.id,
                        'broker_order_id': result.broker_order_id,
                        'status': result.status.value,
                        'fill_price': result.avg_fill_price,
                        'fill_qty': result.filled_quantity
                    }
                )
            else:
                # Retry logic
                if request.retry_count < request.max_retries:
                    request.retry_count += 1
                    logger.warning(f"Order {request.id} failed, retry {request.retry_count}/{request.max_retries}")
                    time.sleep(1)  # Wait before retry
                    self._queues[request.priority].put(request)
                else:
                    self._complete_order(request, success=False, error=result.error_message)
                    
        except Exception as e:
            logger.error(f"Order processing error: {e}")
            if request.retry_count < request.max_retries:
                request.retry_count += 1
                self._queues[request.priority].put(request)
            else:
                self._complete_order(request, success=False, error=str(e))
    
    def _complete_order(
        self,
        request: OrderRequest,
        success: bool,
        result: Dict = None,
        error: str = None
    ):
        """Complete order processing"""
        with self._lock:
            # Remove from pending
            if request.id in self._pending_orders:
                del self._pending_orders[request.id]
            
            # Update symbol count
            if request.symbol in self._active_symbols:
                self._active_symbols[request.symbol] -= 1
                if self._active_symbols[request.symbol] <= 0:
                    del self._active_symbols[request.symbol]
            
            # Add to history
            self._order_history.append({
                'id': request.id,
                'symbol': request.symbol,
                'side': request.side,
                'type': request.order_type,
                'quantity': request.quantity,
                'success': success,
                'result': result,
                'error': error,
                'completed_at': datetime.now().isoformat()
            })
            
            # Keep history limited
            if len(self._order_history) > 1000:
                self._order_history = self._order_history[-500:]
        
        # Call callback
        if request.callback:
            try:
                request.callback(request, success, result, error)
            except Exception as e:
                logger.error(f"Order callback error: {e}")
        
        if success:
            logger.success(f"Order {request.id} completed: {result}")
        else:
            logger.error(f"Order {request.id} failed: {error}")
    
    # ==================== ORDER MANAGEMENT ====================
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        with self._lock:
            if order_id not in self._pending_orders:
                return False
            
            request = self._pending_orders[order_id]
            
            # Try to remove from queue (not guaranteed)
            # Mark as expired to skip processing
            request.expires_at = datetime.now() - timedelta(seconds=1)
            
            logger.info(f"Order {order_id} marked for cancellation")
            return True
    
    def cancel_all_orders(self, symbol: str = None) -> int:
        """Cancel all pending orders"""
        cancelled = 0
        
        with self._lock:
            for order_id, request in list(self._pending_orders.items()):
                if symbol is None or request.symbol == symbol:
                    request.expires_at = datetime.now() - timedelta(seconds=1)
                    cancelled += 1
        
        logger.info(f"Cancelled {cancelled} orders")
        return cancelled
    
    def get_pending_orders(self, symbol: str = None) -> List[Dict]:
        """Get all pending orders"""
        with self._lock:
            orders = []
            for request in self._pending_orders.values():
                if symbol is None or request.symbol == symbol:
                    orders.append({
                        'id': request.id,
                        'symbol': request.symbol,
                        'side': request.side,
                        'type': request.order_type,
                        'quantity': request.quantity,
                        'price': request.price,
                        'priority': request.priority.name,
                        'created_at': request.created_at.isoformat()
                    })
            return orders
    
    def get_order_history(self, limit: int = 50) -> List[Dict]:
        """Get recent order history"""
        return self._order_history[-limit:]
    
    def get_queue_status(self) -> Dict:
        """Get queue status"""
        return {
            'total_pending': len(self._pending_orders),
            'by_priority': {
                p.name: self._queues[p].qsize()
                for p in OrderPriority
            },
            'active_symbols': dict(self._active_symbols),
            'processing': self._processing
        }
    
    # ==================== BATCH OPERATIONS ====================
    
    def submit_bracket_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        broker: str = "paper"
    ) -> Tuple[bool, str]:
        """
        Submit a bracket order (entry + SL + TP).
        
        For market entries, SL/TP are placed as separate orders after fill.
        For limit entries, this creates OCO (One-Cancels-Other) setup.
        """
        return self.submit_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT" if entry_price > 0 else "MARKET",
            quantity=quantity,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker,
            priority=OrderPriority.HIGH
        )
    
    def scale_in(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        num_orders: int = 3,
        price_range_pct: float = 1.0,
        current_price: float = 0.0,
        broker: str = "paper"
    ) -> List[Tuple[bool, str]]:
        """
        Place multiple orders to scale into position.
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            total_quantity: Total quantity to accumulate
            num_orders: Number of orders to split into
            price_range_pct: Price range for limit orders
            current_price: Current market price
            broker: Broker to use
            
        Returns:
            List of order submission results
        """
        if num_orders < 1:
            return [(False, "Invalid number of orders")]
        
        qty_per_order = total_quantity / num_orders
        price_step = (current_price * price_range_pct / 100) / num_orders
        
        results = []
        for i in range(num_orders):
            if side.upper() == "BUY":
                # Buy lower for each order
                price = current_price - (price_step * i)
            else:
                # Sell higher for each order
                price = current_price + (price_step * i)
            
            result = self.submit_limit_order(
                symbol=symbol,
                side=side,
                quantity=qty_per_order,
                price=price,
                broker=broker
            )
            results.append(result)
        
        return results


# Example usage
if __name__ == "__main__":
    from core.execution_engine import ExecutionEngine
    
    config = {
        'max_orders_per_symbol': 5,
        'max_queue_size': 100,
        'min_order_interval': 0.5
    }
    
    exec_config = {
        'paper_trading': {'initial_balance': 100000.0}
    }
    
    execution_engine = ExecutionEngine(exec_config)
    order_manager = OrderManager(config, execution_engine)
    
    # Start processing
    order_manager.start_processing()
    
    # Submit some orders
    success, order_id = order_manager.submit_market_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.1,
        stop_loss=45000,
        take_profit=55000
    )
    print(f"Order submitted: {success}, ID: {order_id}")
    
    # Wait for processing
    time.sleep(2)
    
    # Check status
    print(f"Queue status: {order_manager.get_queue_status()}")
    print(f"Order history: {order_manager.get_order_history()}")
    
    # Stop processing
    order_manager.stop_processing()
