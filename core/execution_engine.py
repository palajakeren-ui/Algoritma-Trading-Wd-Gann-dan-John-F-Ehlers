"""
Execution Engine v3.0 - Production Ready
Unified order execution layer for live trading across multiple brokers
"""
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Tuple
from loguru import logger
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
import uuid


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class BrokerType(Enum):
    BINANCE = "binance"
    MT5 = "metatrader5"
    PAPER = "paper"


@dataclass
class Order:
    """Order data class"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: float = 0.0
    stop_price: float = 0.0
    take_profit: float = 0.0
    stop_loss: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    broker_order_id: Optional[str] = None
    broker: BrokerType = BrokerType.PAPER
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: str = ""


@dataclass
class Position:
    """Position data class"""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    broker: BrokerType = BrokerType.PAPER
    opened_at: datetime = field(default_factory=datetime.now)


class ExecutionEngine:
    """
    Production-ready execution engine supporting:
    - Multi-broker order routing
    - Order lifecycle management
    - Position tracking
    - Paper trading mode
    - Order validation and risk checks
    """
    
    def __init__(self, config: Dict):
        """
        Initialize execution engine.
        
        Args:
            config: Configuration dict with broker configs
        """
        self.config = config
        self._connectors: Dict[BrokerType, object] = {}
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Position] = {}  # Key: broker_symbol
        self._order_callbacks: List[Callable] = []
        self._position_callbacks: List[Callable] = []
        self._lock = Lock()
        
        # Paper trading state
        self._paper_balance = config.get('paper_trading', {}).get('initial_balance', 100000.0)
        self._paper_positions: Dict[str, Position] = {}
        
        # Risk settings
        self.max_position_size = config.get('risk', {}).get('max_position_size', 0.1)  # 10% of portfolio
        self.max_daily_loss = config.get('risk', {}).get('max_daily_loss', 0.05)  # 5%
        self.max_open_positions = config.get('risk', {}).get('max_open_positions', 5)
        
        self._daily_pnl = 0.0
        self._daily_pnl_reset_date = datetime.now().date()
        
        self._initialize_connectors()
        logger.info("Execution Engine initialized")
    
    def _initialize_connectors(self):
        """Initialize broker connectors"""
        broker_config = self.config.get('broker_config', {})
        
        # Initialize Binance
        if broker_config.get('binance_futures', {}).get('enabled'):
            try:
                from core.Binance_connector import BinanceConnector
                self._connectors[BrokerType.BINANCE] = BinanceConnector(
                    broker_config['binance_futures']
                )
                logger.success("Binance connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Binance: {e}")
        
        # Initialize MT5
        if broker_config.get('metatrader5', {}).get('enabled'):
            try:
                from core.Metatrader5_bridge import MetaTrader5Bridge
                self._connectors[BrokerType.MT5] = MetaTrader5Bridge(
                    broker_config['metatrader5']
                )
                logger.success("MT5 connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize MT5: {e}")
    
    def get_connector(self, broker: BrokerType):
        """Get broker connector"""
        return self._connectors.get(broker)
    
    # ==================== ORDER METHODS ====================
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    def _validate_order(self, order: Order) -> Tuple[bool, str]:
        """
        Validate order against risk rules.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Reset daily PnL if new day
        today = datetime.now().date()
        if today > self._daily_pnl_reset_date:
            self._daily_pnl = 0.0
            self._daily_pnl_reset_date = today
        
        # Check daily loss limit
        if self._daily_pnl < -self.max_daily_loss * self._paper_balance:
            return False, "Daily loss limit exceeded"
        
        # Check max open positions
        open_positions = len([p for p in self._positions.values() if p.quantity > 0])
        if open_positions >= self.max_open_positions:
            return False, f"Max open positions ({self.max_open_positions}) reached"
        
        # Check position size
        total_value = order.quantity * (order.price if order.price > 0 else 1)
        max_value = self._paper_balance * self.max_position_size
        if total_value > max_value:
            return False, f"Position size exceeds limit ({self.max_position_size*100}% of portfolio)"
        
        # Valid
        return True, ""
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0.0,
        stop_price: float = 0.0,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        broker: str = "paper"
    ) -> Order:
        """
        Create a new order.
        
        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            order_type: 'MARKET', 'LIMIT', 'STOP', etc.
            quantity: Order quantity
            price: Limit price (for limit orders)
            stop_price: Stop trigger price
            stop_loss: Stop loss price
            take_profit: Take profit price
            broker: Broker to use
            
        Returns:
            Order object
        """
        order = Order(
            id=self._generate_order_id(),
            symbol=symbol,
            side=OrderSide[side.upper()],
            type=OrderType[order_type.upper()],
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=BrokerType(broker)
        )
        
        with self._lock:
            self._orders[order.id] = order
        
        logger.info(f"Order created: {order.id} - {side} {quantity} {symbol}")
        return order
    
    def submit_order(self, order: Order) -> Order:
        """
        Submit order to broker.
        
        Args:
            order: Order to submit
            
        Returns:
            Updated order with broker response
        """
        # Validate
        is_valid, error = self._validate_order(order)
        if not is_valid:
            order.status = OrderStatus.REJECTED
            order.error_message = error
            logger.error(f"Order rejected: {error}")
            return order
        
        # Submit to broker
        try:
            if order.broker == BrokerType.PAPER:
                return self._execute_paper_order(order)
            
            connector = self._connectors.get(order.broker)
            if not connector:
                order.status = OrderStatus.REJECTED
                order.error_message = f"Broker {order.broker.value} not available"
                return order
            
            # Execute based on order type
            if order.type == OrderType.MARKET:
                result = self._execute_market_order(order, connector)
            elif order.type == OrderType.LIMIT:
                result = self._execute_limit_order(order, connector)
            else:
                result = self._execute_stop_order(order, connector)
            
            return result
            
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.error_message = str(e)
            logger.error(f"Order execution failed: {e}")
            return order
    
    def _execute_market_order(self, order: Order, connector) -> Order:
        """Execute market order on broker"""
        if order.broker == BrokerType.BINANCE:
            result = connector.place_market_order(
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity
            )
        elif order.broker == BrokerType.MT5:
            result = connector.place_market_order(
                symbol=order.symbol,
                side=order.side.value,
                lot=order.quantity,
                stop_loss=order.stop_loss,
                take_profit=order.take_profit
            )
        else:
            result = None
        
        if result:
            order.status = OrderStatus.FILLED
            order.broker_order_id = str(result.get('order_id', ''))
            order.filled_quantity = result.get('executed_qty', order.quantity)
            order.avg_fill_price = result.get('avg_price', result.get('price', 0))
            order.updated_at = datetime.now()
            
            # Update position
            self._update_position_from_order(order)
            
            # Place SL/TP orders
            self._place_bracket_orders(order, connector)
        else:
            order.status = OrderStatus.REJECTED
            order.error_message = "Broker returned no result"
        
        return order
    
    def _execute_limit_order(self, order: Order, connector) -> Order:
        """Execute limit order on broker"""
        if order.broker == BrokerType.BINANCE:
            result = connector.place_limit_order(
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity,
                price=order.price
            )
        elif order.broker == BrokerType.MT5:
            result = connector.place_limit_order(
                symbol=order.symbol,
                side=order.side.value,
                lot=order.quantity,
                price=order.price,
                stop_loss=order.stop_loss,
                take_profit=order.take_profit
            )
        else:
            result = None
        
        if result:
            order.status = OrderStatus.SUBMITTED
            order.broker_order_id = str(result.get('order_id', ''))
            order.updated_at = datetime.now()
        else:
            order.status = OrderStatus.REJECTED
            order.error_message = "Broker returned no result"
        
        return order
    
    def _execute_stop_order(self, order: Order, connector) -> Order:
        """Execute stop order on broker"""
        if order.broker == BrokerType.BINANCE:
            if order.type == OrderType.STOP_LOSS:
                close_side = 'SELL' if order.side == OrderSide.BUY else 'BUY'
                result = connector.place_stop_loss(
                    symbol=order.symbol,
                    side=close_side,
                    quantity=order.quantity,
                    stop_price=order.stop_price
                )
            else:
                result = None
        else:
            result = None
        
        if result:
            order.status = OrderStatus.SUBMITTED
            order.broker_order_id = str(result.get('order_id', ''))
            order.updated_at = datetime.now()
        else:
            order.status = OrderStatus.REJECTED
            order.error_message = "Stop order failed"
        
        return order
    
    def _place_bracket_orders(self, order: Order, connector):
        """Place SL/TP orders after main order fills"""
        if order.stop_loss > 0:
            close_side = 'SELL' if order.side == OrderSide.BUY else 'BUY'
            if order.broker == BrokerType.BINANCE:
                connector.place_stop_loss(
                    symbol=order.symbol,
                    side=close_side,
                    quantity=order.filled_quantity,
                    stop_price=order.stop_loss
                )
        
        if order.take_profit > 0:
            close_side = 'SELL' if order.side == OrderSide.BUY else 'BUY'
            if order.broker == BrokerType.BINANCE:
                connector.place_take_profit(
                    symbol=order.symbol,
                    side=close_side,
                    quantity=order.filled_quantity,
                    take_profit_price=order.take_profit
                )
    
    def _execute_paper_order(self, order: Order) -> Order:
        """Execute order in paper trading mode"""
        # Get current price (simulated)
        fill_price = order.price if order.price > 0 else 50000.0  # Default price
        
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.avg_fill_price = fill_price
        order.broker_order_id = f"PAPER-{order.id}"
        order.updated_at = datetime.now()
        
        # Update paper position
        self._update_position_from_order(order)
        
        logger.info(f"Paper order filled: {order.side.value} {order.quantity} {order.symbol} @ {fill_price}")
        
        return order
    
    def _update_position_from_order(self, order: Order):
        """Update position based on filled order"""
        key = f"{order.broker.value}_{order.symbol}"
        
        with self._lock:
            if key in self._positions:
                pos = self._positions[key]
                
                if order.side == pos.side:
                    # Adding to position
                    total_qty = pos.quantity + order.filled_quantity
                    pos.entry_price = (
                        (pos.entry_price * pos.quantity + order.avg_fill_price * order.filled_quantity)
                        / total_qty
                    )
                    pos.quantity = total_qty
                else:
                    # Reducing or closing position
                    if order.filled_quantity >= pos.quantity:
                        # Close position
                        realized_pnl = (order.avg_fill_price - pos.entry_price) * pos.quantity
                        if pos.side == OrderSide.SELL:
                            realized_pnl = -realized_pnl
                        self._daily_pnl += realized_pnl
                        del self._positions[key]
                    else:
                        # Partial close
                        pos.quantity -= order.filled_quantity
            else:
                # New position
                self._positions[key] = Position(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.filled_quantity,
                    entry_price=order.avg_fill_price,
                    stop_loss=order.stop_loss,
                    take_profit=order.take_profit,
                    broker=order.broker
                )
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        
        if order.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
            return False
        
        if order.broker == BrokerType.PAPER:
            order.status = OrderStatus.CANCELLED
            return True
        
        connector = self._connectors.get(order.broker)
        if not connector or not order.broker_order_id:
            return False
        
        try:
            if order.broker == BrokerType.BINANCE:
                success = connector.cancel_order(order.symbol, int(order.broker_order_id))
            elif order.broker == BrokerType.MT5:
                success = connector.cancel_order(int(order.broker_order_id))
            else:
                success = False
            
            if success:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    # ==================== POSITION METHODS ====================
    
    def get_position(self, symbol: str, broker: str = "paper") -> Optional[Position]:
        """Get position for a symbol"""
        key = f"{broker}_{symbol}"
        return self._positions.get(key)
    
    def get_all_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self._positions.values())
    
    def close_position(self, symbol: str, broker: str = "paper") -> Optional[Order]:
        """Close entire position for a symbol"""
        pos = self.get_position(symbol, broker)
        if not pos:
            return None
        
        close_side = 'SELL' if pos.side == OrderSide.BUY else 'BUY'
        
        order = self.create_order(
            symbol=symbol,
            side=close_side,
            order_type='MARKET',
            quantity=pos.quantity,
            broker=broker
        )
        
        return self.submit_order(order)
    
    def close_all_positions(self, broker: str = None) -> int:
        """Close all open positions"""
        closed = 0
        for pos in list(self._positions.values()):
            if broker and pos.broker.value != broker:
                continue
            result = self.close_position(pos.symbol, pos.broker.value)
            if result and result.status == OrderStatus.FILLED:
                closed += 1
        return closed
    
    # ==================== QUERIES ====================
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self._orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """Get all open/pending orders"""
        return [
            o for o in self._orders.values()
            if o.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
        ]
    
    def get_daily_pnl(self) -> float:
        """Get daily realized PnL"""
        return self._daily_pnl
    
    def get_paper_balance(self) -> float:
        """Get paper trading balance"""
        return self._paper_balance + self._daily_pnl
    
    # ==================== CALLBACKS ====================
    
    def on_order_update(self, callback: Callable):
        """Register order update callback"""
        self._order_callbacks.append(callback)
    
    def on_position_update(self, callback: Callable):
        """Register position update callback"""
        self._position_callbacks.append(callback)
    
    # ==================== CONVENIENCE METHODS ====================
    
    def buy_market(
        self,
        symbol: str,
        quantity: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        broker: str = "paper"
    ) -> Order:
        """Place a market buy order"""
        order = self.create_order(
            symbol=symbol,
            side='BUY',
            order_type='MARKET',
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker
        )
        return self.submit_order(order)
    
    def sell_market(
        self,
        symbol: str,
        quantity: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        broker: str = "paper"
    ) -> Order:
        """Place a market sell order"""
        order = self.create_order(
            symbol=symbol,
            side='SELL',
            order_type='MARKET',
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker
        )
        return self.submit_order(order)
    
    def buy_limit(
        self,
        symbol: str,
        quantity: float,
        price: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        broker: str = "paper"
    ) -> Order:
        """Place a limit buy order"""
        order = self.create_order(
            symbol=symbol,
            side='BUY',
            order_type='LIMIT',
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker
        )
        return self.submit_order(order)
    
    def sell_limit(
        self,
        symbol: str,
        quantity: float,
        price: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        broker: str = "paper"
    ) -> Order:
        """Place a limit sell order"""
        order = self.create_order(
            symbol=symbol,
            side='SELL',
            order_type='LIMIT',
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker
        )
        return self.submit_order(order)


# Example usage
if __name__ == "__main__":
    config = {
        'paper_trading': {
            'initial_balance': 100000.0
        },
        'risk': {
            'max_position_size': 0.1,
            'max_daily_loss': 0.05,
            'max_open_positions': 5
        }
    }
    
    engine = ExecutionEngine(config)
    
    # Paper trade example
    order = engine.buy_market(
        symbol="BTCUSDT",
        quantity=0.1,
        stop_loss=45000,
        take_profit=55000,
        broker="paper"
    )
    
    print(f"Order: {order}")
    print(f"Positions: {engine.get_all_positions()}")
    print(f"Paper Balance: ${engine.get_paper_balance():,.2f}")
