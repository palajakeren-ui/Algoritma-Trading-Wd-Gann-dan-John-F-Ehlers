"""
MetaTrader 5 Bridge v3.0 - Production Ready
Handles connection, trading, and data retrieval from MetaTrader 5
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from loguru import logger
import pandas as pd
from threading import Thread, Event
import time

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    logger.warning("MetaTrader5 package not installed. Install with: pip install MetaTrader5")
    MT5_AVAILABLE = False


class MetaTrader5Bridge:
    """
    Production-ready MetaTrader 5 bridge supporting:
    - Account connection and authentication
    - Real-time price feeds
    - Order execution (Market, Limit, Stop)
    - Position management
    - Historical data retrieval
    """
    
    # Timeframe mapping
    TIMEFRAME_MAP = {
        "M1": "TIMEFRAME_M1", "M2": "TIMEFRAME_M2", "M3": "TIMEFRAME_M3",
        "M4": "TIMEFRAME_M4", "M5": "TIMEFRAME_M5", "M6": "TIMEFRAME_M6",
        "M10": "TIMEFRAME_M10", "M12": "TIMEFRAME_M12", "M15": "TIMEFRAME_M15",
        "M20": "TIMEFRAME_M20", "M30": "TIMEFRAME_M30",
        "H1": "TIMEFRAME_H1", "H2": "TIMEFRAME_H2", "H3": "TIMEFRAME_H3",
        "H4": "TIMEFRAME_H4", "H6": "TIMEFRAME_H6", "H8": "TIMEFRAME_H8",
        "H12": "TIMEFRAME_H12", "D1": "TIMEFRAME_D1", "W1": "TIMEFRAME_W1",
        "MN1": "TIMEFRAME_MN1",
        "1m": "TIMEFRAME_M1", "5m": "TIMEFRAME_M5", "15m": "TIMEFRAME_M15",
        "30m": "TIMEFRAME_M30", "1h": "TIMEFRAME_H1", "4h": "TIMEFRAME_H4",
        "1d": "TIMEFRAME_D1", "1w": "TIMEFRAME_W1"
    }
    
    def __init__(self, config: Dict):
        """
        Initialize MT5 bridge.
        
        Args:
            config: Configuration dictionary with login, password, server, path
        """
        self.login = config.get('login') or os.getenv('MT5_LOGIN')
        self.password = config.get('password') or os.getenv('MT5_PASSWORD')
        self.server = config.get('server', 'MetaQuotes-Demo')
        self.path = config.get('path', r"C:\Program Files\MetaTrader 5\terminal64.exe")
        
        self.timeout = config.get('timeout', {})
        self.connection_timeout = self.timeout.get('connection', 60000)
        self.order_timeout = self.timeout.get('order', 30000)
        
        self.execution = config.get('execution', {})
        self.slippage = self.execution.get('slippage', 3)
        self.magic_number = self.execution.get('magic_number', 123456)
        self.comment = self.execution.get('comment', 'GQ_AI_v3')
        
        self.symbol_mapping = config.get('symbol_mapping', {})
        
        # Price streaming
        self._price_callbacks: List[Callable] = []
        self._streaming = False
        self._stream_stop_event = Event()
        
        self._connected = False
        
        if MT5_AVAILABLE:
            self._initialize()
        else:
            logger.error("MetaTrader5 package not available")
    
    def _initialize(self) -> bool:
        """Initialize MT5 terminal"""
        try:
            # Initialize MT5
            if not mt5.initialize(path=self.path, timeout=self.connection_timeout):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            # Login if credentials provided
            if self.login and self.password:
                login_int = int(self.login) if isinstance(self.login, str) else self.login
                authorized = mt5.login(
                    login=login_int,
                    password=self.password,
                    server=self.server
                )
                if not authorized:
                    error = mt5.last_error()
                    logger.error(f"MT5 login failed: {error}")
                    return False
            
            self._connected = True
            account_info = mt5.account_info()
            logger.success(f"MT5 connected: {account_info.name} (Balance: {account_info.balance})")
            return True
            
        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if MT5 is connected"""
        if not MT5_AVAILABLE:
            return False
        return self._connected and mt5.terminal_info() is not None
    
    def _map_symbol(self, symbol: str) -> str:
        """Map internal symbol to broker symbol"""
        return self.symbol_mapping.get(symbol, symbol)
    
    def _get_timeframe(self, timeframe: str):
        """Get MT5 timeframe constant"""
        tf_name = self.TIMEFRAME_MAP.get(timeframe, "TIMEFRAME_H1")
        return getattr(mt5, tf_name, mt5.TIMEFRAME_H1)
    
    # ==================== ACCOUNT METHODS ====================
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        if not self.is_connected():
            return None
        
        try:
            info = mt5.account_info()
            if info is None:
                return None
            
            return {
                'login': info.login,
                'name': info.name,
                'server': info.server,
                'currency': info.currency,
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'free_margin': info.margin_free,
                'margin_level': info.margin_level,
                'leverage': info.leverage,
                'profit': info.profit
            }
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
    
    def get_balance(self) -> float:
        """Get account balance"""
        info = self.get_account_info()
        return info['balance'] if info else 0.0
    
    def get_equity(self) -> float:
        """Get account equity"""
        info = self.get_account_info()
        return info['equity'] if info else 0.0
    
    # ==================== MARKET DATA ====================
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information"""
        if not self.is_connected():
            return None
        
        try:
            mapped_symbol = self._map_symbol(symbol)
            info = mt5.symbol_info(mapped_symbol)
            
            if info is None:
                logger.warning(f"Symbol {mapped_symbol} not found")
                return None
            
            return {
                'symbol': info.name,
                'bid': info.bid,
                'ask': info.ask,
                'spread': info.spread,
                'digits': info.digits,
                'point': info.point,
                'lot_min': info.volume_min,
                'lot_max': info.volume_max,
                'lot_step': info.volume_step,
                'trade_mode': info.trade_mode,
                'swap_long': info.swap_long,
                'swap_short': info.swap_short
            }
            
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    def get_ticker_price(self, symbol: str) -> Optional[Tuple[float, float]]:
        """Get current bid/ask prices"""
        if not self.is_connected():
            return None
        
        try:
            mapped_symbol = self._map_symbol(symbol)
            tick = mt5.symbol_info_tick(mapped_symbol)
            
            if tick is None:
                return None
            
            return (tick.bid, tick.ask)
            
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            return None
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: Optional[str] = None,
        count: int = 1000
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            count: Number of bars to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.is_connected():
            return None
        
        try:
            mapped_symbol = self._map_symbol(symbol)
            tf = self._get_timeframe(timeframe)
            
            # Enable symbol
            if not mt5.symbol_select(mapped_symbol, True):
                logger.warning(f"Failed to select symbol {mapped_symbol}")
                return None
            
            # Parse dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
            
            # Fetch rates
            rates = mt5.copy_rates_range(mapped_symbol, tf, start_dt, end_dt)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No data returned for {mapped_symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.rename(columns={
                'tick_volume': 'volume',
                'real_volume': 'real_volume',
                'spread': 'spread'
            }, inplace=True)
            
            logger.success(f"Fetched {len(df)} bars for {mapped_symbol}")
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None
    
    # ==================== ORDER MANAGEMENT ====================
    
    def _normalize_lot(self, symbol: str, lot: float) -> float:
        """Normalize lot size to symbol requirements"""
        info = self.get_symbol_info(symbol)
        if not info:
            return lot
        
        lot_min = info['lot_min']
        lot_max = info['lot_max']
        lot_step = info['lot_step']
        
        # Round to step
        normalized = round(lot / lot_step) * lot_step
        
        # Clamp to range
        normalized = max(lot_min, min(lot_max, normalized))
        
        return normalized
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        lot: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        comment: str = None
    ) -> Optional[Dict]:
        """
        Place a market order.
        
        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            lot: Lot size
            stop_loss: Stop loss price (0 for none)
            take_profit: Take profit price (0 for none)
            comment: Order comment
            
        Returns:
            Order result dictionary
        """
        if not self.is_connected():
            return None
        
        try:
            mapped_symbol = self._map_symbol(symbol)
            lot = self._normalize_lot(symbol, lot)
            
            # Enable symbol
            if not mt5.symbol_select(mapped_symbol, True):
                return None
            
            info = mt5.symbol_info(mapped_symbol)
            if not info.visible:
                logger.error(f"Symbol {mapped_symbol} is not visible")
                return None
            
            # Get current prices
            tick = mt5.symbol_info_tick(mapped_symbol)
            price = tick.ask if side.upper() == 'BUY' else tick.bid
            
            # Prepare request
            order_type = mt5.ORDER_TYPE_BUY if side.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": mapped_symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": comment or self.comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return None
            
            logger.success(f"Market order executed: {side} {lot} {mapped_symbol} @ {result.price}")
            
            return {
                'order_id': result.order,
                'deal_id': result.deal,
                'symbol': mapped_symbol,
                'side': side,
                'type': 'MARKET',
                'lot': lot,
                'price': result.price,
                'sl': stop_loss,
                'tp': take_profit,
                'comment': comment or self.comment
            }
            
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return None
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        lot: float,
        price: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        expiration: datetime = None,
        comment: str = None
    ) -> Optional[Dict]:
        """Place a pending limit order"""
        if not self.is_connected():
            return None
        
        try:
            mapped_symbol = self._map_symbol(symbol)
            lot = self._normalize_lot(symbol, lot)
            
            if not mt5.symbol_select(mapped_symbol, True):
                return None
            
            tick = mt5.symbol_info_tick(mapped_symbol)
            current_price = tick.ask if side.upper() == 'BUY' else tick.bid
            
            # Determine order type
            if side.upper() == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY_LIMIT if price < current_price else mt5.ORDER_TYPE_BUY_STOP
            else:
                order_type = mt5.ORDER_TYPE_SELL_LIMIT if price > current_price else mt5.ORDER_TYPE_SELL_STOP
            
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": mapped_symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": comment or self.comment,
                "type_time": mt5.ORDER_TIME_GTC if expiration is None else mt5.ORDER_TIME_SPECIFIED,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            
            if expiration:
                request["expiration"] = int(expiration.timestamp())
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Limit order failed: {result.retcode} - {result.comment}")
                return None
            
            logger.success(f"Limit order placed: {side} {lot} {mapped_symbol} @ {price}")
            
            return {
                'order_id': result.order,
                'symbol': mapped_symbol,
                'side': side,
                'type': 'LIMIT',
                'lot': lot,
                'price': price,
                'sl': stop_loss,
                'tp': take_profit
            }
            
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            return None
    
    def modify_position(
        self,
        ticket: int,
        stop_loss: float = None,
        take_profit: float = None
    ) -> bool:
        """Modify an existing position's SL/TP"""
        if not self.is_connected():
            return False
        
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                logger.error(f"Position {ticket} not found")
                return False
            
            pos = position[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": stop_loss if stop_loss is not None else pos.sl,
                "tp": take_profit if take_profit is not None else pos.tp,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Position modify failed: {result.retcode}")
                return False
            
            logger.success(f"Position {ticket} modified: SL={stop_loss}, TP={take_profit}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to modify position: {e}")
            return False
    
    def close_position(self, ticket: int) -> Optional[Dict]:
        """Close a position by ticket"""
        if not self.is_connected():
            return None
        
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                logger.error(f"Position {ticket} not found")
                return None
            
            pos = position[0]
            
            # Determine close direction
            order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(pos.symbol)
            price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": "Close by script",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close position failed: {result.retcode}")
                return None
            
            logger.success(f"Position {ticket} closed at {result.price}")
            
            return {
                'ticket': ticket,
                'symbol': pos.symbol,
                'close_price': result.price,
                'profit': pos.profit
            }
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return None
    
    def close_all_positions(self, symbol: str = None) -> int:
        """Close all positions, optionally filtered by symbol"""
        if not self.is_connected():
            return 0
        
        try:
            if symbol:
                mapped_symbol = self._map_symbol(symbol)
                positions = mt5.positions_get(symbol=mapped_symbol)
            else:
                positions = mt5.positions_get()
            
            if not positions:
                return 0
            
            closed_count = 0
            for pos in positions:
                result = self.close_position(pos.ticket)
                if result:
                    closed_count += 1
            
            logger.info(f"Closed {closed_count} positions")
            return closed_count
            
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            return 0
    
    def cancel_order(self, ticket: int) -> bool:
        """Cancel a pending order"""
        if not self.is_connected():
            return False
        
        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Cancel order failed: {result.retcode}")
                return False
            
            logger.info(f"Order {ticket} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    # ==================== POSITION QUERIES ====================
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get all open positions"""
        if not self.is_connected():
            return []
        
        try:
            if symbol:
                mapped_symbol = self._map_symbol(symbol)
                positions = mt5.positions_get(symbol=mapped_symbol)
            else:
                positions = mt5.positions_get()
            
            if not positions:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'magic': pos.magic,
                    'comment': pos.comment,
                    'open_time': datetime.fromtimestamp(pos.time)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_pending_orders(self, symbol: str = None) -> List[Dict]:
        """Get all pending orders"""
        if not self.is_connected():
            return []
        
        try:
            if symbol:
                mapped_symbol = self._map_symbol(symbol)
                orders = mt5.orders_get(symbol=mapped_symbol)
            else:
                orders = mt5.orders_get()
            
            if not orders:
                return []
            
            result = []
            for order in orders:
                result.append({
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': order.type,
                    'volume': order.volume_current,
                    'price': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'magic': order.magic,
                    'comment': order.comment
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get pending orders: {e}")
            return []
    
    # ==================== STREAMING ====================
    
    def subscribe_price_stream(self, symbol: str, callback: Callable):
        """Subscribe to real-time price updates"""
        self._price_callbacks.append(callback)
        
        if not self._streaming:
            self._start_price_stream(symbol)
    
    def _start_price_stream(self, symbol: str):
        """Start price streaming thread"""
        def stream_loop():
            mapped_symbol = self._map_symbol(symbol)
            
            while not self._stream_stop_event.is_set():
                if not self.is_connected():
                    time.sleep(1)
                    continue
                
                try:
                    tick = mt5.symbol_info_tick(mapped_symbol)
                    if tick:
                        data = {
                            'symbol': symbol,
                            'bid': tick.bid,
                            'ask': tick.ask,
                            'time': datetime.fromtimestamp(tick.time),
                            'volume': tick.volume
                        }
                        for callback in self._price_callbacks:
                            callback(data)
                except Exception as e:
                    logger.error(f"Price stream error: {e}")
                
                time.sleep(0.1)  # 100ms polling
        
        self._streaming = True
        thread = Thread(target=stream_loop, daemon=True)
        thread.start()
        logger.info(f"Price stream started for {symbol}")
    
    def stop_price_stream(self):
        """Stop price streaming"""
        self._stream_stop_event.set()
        self._streaming = False
        logger.info("Price stream stopped")
    
    # ==================== CLEANUP ====================
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        self.stop_price_stream()
        if MT5_AVAILABLE:
            mt5.shutdown()
        self._connected = False
        logger.info("MT5 connection closed")
    
    def __del__(self):
        """Destructor"""
        self.shutdown()


# Example usage
if __name__ == "__main__":
    config = {
        'login': os.getenv('MT5_LOGIN'),
        'password': os.getenv('MT5_PASSWORD'),
        'server': 'MetaQuotes-Demo',
        'execution': {
            'slippage': 3,
            'magic_number': 123456
        }
    }
    
    bridge = MetaTrader5Bridge(config)
    
    if bridge.is_connected():
        # Get account info
        account = bridge.get_account_info()
        print(f"Account: {account}")
        
        # Get symbol info
        symbol_info = bridge.get_symbol_info("EURUSD")
        print(f"Symbol info: {symbol_info}")
        
        # Get historical data
        data = bridge.get_historical_data(
            symbol="EURUSD",
            timeframe="H1",
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
        if data is not None:
            print(f"Historical data: {len(data)} bars")
            print(data.head())
        
        bridge.shutdown()
