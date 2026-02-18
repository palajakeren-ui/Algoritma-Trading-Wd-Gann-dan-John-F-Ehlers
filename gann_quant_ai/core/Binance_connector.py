"""
Binance Connector v3.0 - Production Ready
Handles Spot, Futures, and WebSocket connections to Binance
"""
import os
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from loguru import logger
import pandas as pd
import requests
from threading import Thread
import json

try:
    from binance.client import Client
    from binance.enums import *
    from binance.um_futures import UMFutures
    from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient
    BINANCE_AVAILABLE = True
except ImportError:
    logger.warning("python-binance not installed. Using fallback REST API.")
    BINANCE_AVAILABLE = False


class BinanceConnector:
    """
    Production-ready Binance connector supporting:
    - Spot Trading
    - USDT-M Futures Trading
    - Real-time WebSocket price feeds
    - Order management (Market, Limit, Stop-Loss, Take-Profit)
    """
    
    # API Endpoints
    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"
    TESTNET_FUTURES_URL = "https://testnet.binancefuture.com"
    
    # Timeframe mappings
    TIMEFRAME_MAP = {
        "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
        "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M",
        "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
        "H1": "1h", "H4": "4h", "D1": "1d", "W1": "1w"
    }
    
    def __init__(self, config: Dict):
        """
        Initialize Binance connector.
        
        Args:
            config: Configuration dictionary with api_key, api_secret, testnet flag
        """
        self.api_key = config.get('api_key') or os.getenv('BINANCE_API_KEY', '')
        self.api_secret = config.get('api_secret') or os.getenv('BINANCE_API_SECRET', '')
        self.testnet = config.get('testnet', True)
        
        self.leverage = config.get('trading', {}).get('leverage', 10)
        self.margin_type = config.get('trading', {}).get('margin_type', 'ISOLATED')
        
        # WebSocket callbacks
        self._price_callbacks: List[Callable] = []
        self._ws_client = None
        self._ws_running = False
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Session for REST API
        self._session = requests.Session()
        self._session.headers.update({
            'X-MBX-APIKEY': self.api_key
        })
        
        # Initialize clients if library available
        self._client = None
        self._futures_client = None
        
        if BINANCE_AVAILABLE and self.api_key and self.api_secret:
            try:
                self._client = Client(self.api_key, self.api_secret, testnet=self.testnet)
                self._futures_client = UMFutures(
                    key=self.api_key,
                    secret=self.api_secret,
                    base_url=self.TESTNET_FUTURES_URL if self.testnet else self.FUTURES_BASE_URL
                )
                logger.success(f"Binance connector initialized ({'TESTNET' if self.testnet else 'LIVE'})")
            except Exception as e:
                logger.error(f"Failed to initialize Binance clients: {e}")
        else:
            logger.info("Binance connector initialized in REST-only mode")
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _sign_request(self, params: Dict) -> Dict:
        """Sign request with HMAC-SHA256"""
        params['timestamp'] = int(time.time() * 1000)
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        params['signature'] = signature
        return params
    
    # ==================== ACCOUNT METHODS ====================
    
    def get_account_balance(self, asset: str = "USDT") -> Dict:
        """
        Get account balance for a specific asset.
        
        Returns:
            Dict with 'free', 'locked', 'total' balances
        """
        try:
            self._rate_limit()
            
            if self._futures_client:
                balances = self._futures_client.balance()
                for b in balances:
                    if b['asset'] == asset:
                        return {
                            'asset': asset,
                            'free': float(b['availableBalance']),
                            'locked': float(b['balance']) - float(b['availableBalance']),
                            'total': float(b['balance'])
                        }
            else:
                # Fallback REST API
                url = f"{self.FUTURES_BASE_URL}/fapi/v2/balance"
                params = self._sign_request({})
                response = self._session.get(url, params=params)
                response.raise_for_status()
                for b in response.json():
                    if b['asset'] == asset:
                        return {
                            'asset': asset,
                            'free': float(b['availableBalance']),
                            'locked': float(b['balance']) - float(b['availableBalance']),
                            'total': float(b['balance'])
                        }
            
            return {'asset': asset, 'free': 0, 'locked': 0, 'total': 0}
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return {'asset': asset, 'free': 0, 'locked': 0, 'total': 0, 'error': str(e)}
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get current position for a symbol.
        
        Returns:
            Dict with position details or None
        """
        try:
            self._rate_limit()
            
            if self._futures_client:
                positions = self._futures_client.get_position_risk(symbol=symbol)
                for pos in positions:
                    if float(pos['positionAmt']) != 0:
                        return {
                            'symbol': symbol,
                            'side': 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT',
                            'size': abs(float(pos['positionAmt'])),
                            'entry_price': float(pos['entryPrice']),
                            'unrealized_pnl': float(pos['unRealizedProfit']),
                            'leverage': int(pos['leverage']),
                            'margin_type': pos['marginType']
                        }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get position for {symbol}: {e}")
            return None
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol"""
        try:
            self._rate_limit()
            
            if self._futures_client:
                self._futures_client.change_leverage(symbol=symbol, leverage=leverage)
                logger.info(f"Set leverage to {leverage}x for {symbol}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return False
    
    def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED") -> bool:
        """Set margin type (ISOLATED or CROSSED)"""
        try:
            self._rate_limit()
            
            if self._futures_client:
                self._futures_client.change_margin_type(symbol=symbol, marginType=margin_type)
                logger.info(f"Set margin type to {margin_type} for {symbol}")
                return True
            return False
            
        except Exception as e:
            # Error 4046 means margin type is already set
            if "4046" in str(e):
                return True
            logger.error(f"Failed to set margin type: {e}")
            return False
    
    # ==================== MARKET DATA ====================
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """Get current ticker price"""
        try:
            self._rate_limit()
            
            if self._futures_client:
                ticker = self._futures_client.ticker_price(symbol=symbol)
                return float(ticker['price'])
            else:
                url = f"{self.FUTURES_BASE_URL}/fapi/v1/ticker/price"
                response = self._session.get(url, params={'symbol': symbol})
                response.raise_for_status()
                return float(response.json()['price'])
                
        except Exception as e:
            logger.error(f"Failed to get ticker price for {symbol}: {e}")
            return None
    
    def get_historical_klines(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> Optional[pd.DataFrame]:
        """
        Get historical kline/candlestick data.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            timeframe: Kline interval
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Max results per request
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            self._rate_limit()
            
            interval = self.TIMEFRAME_MAP.get(timeframe, timeframe)
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000) if end_date else int(time.time() * 1000)
            
            all_klines = []
            current_start = start_ts
            
            while current_start < end_ts:
                if self._futures_client:
                    klines = self._futures_client.klines(
                        symbol=symbol,
                        interval=interval,
                        startTime=current_start,
                        endTime=end_ts,
                        limit=limit
                    )
                else:
                    url = f"{self.FUTURES_BASE_URL}/fapi/v1/klines"
                    params = {
                        'symbol': symbol,
                        'interval': interval,
                        'startTime': current_start,
                        'endTime': end_ts,
                        'limit': limit
                    }
                    response = self._session.get(url, params=params)
                    response.raise_for_status()
                    klines = response.json()
                
                if not klines:
                    break
                    
                all_klines.extend(klines)
                current_start = klines[-1][0] + 1  # Next candle
                
                if len(klines) < limit:
                    break
            
            if not all_klines:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(all_klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.success(f"Fetched {len(df)} klines for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical klines for {symbol}: {e}")
            return None
    
    # ==================== ORDER MANAGEMENT ====================
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False
    ) -> Optional[Dict]:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            reduce_only: Close position only
            
        Returns:
            Order response dict or None
        """
        try:
            self._rate_limit()
            
            # Set leverage and margin type first
            self.set_leverage(symbol, self.leverage)
            self.set_margin_type(symbol, self.margin_type)
            
            if self._futures_client:
                order = self._futures_client.new_order(
                    symbol=symbol,
                    side=side.upper(),
                    type='MARKET',
                    quantity=quantity,
                    reduceOnly=reduce_only
                )
            else:
                url = f"{self.FUTURES_BASE_URL}/fapi/v1/order"
                params = self._sign_request({
                    'symbol': symbol,
                    'side': side.upper(),
                    'type': 'MARKET',
                    'quantity': quantity,
                    'reduceOnly': str(reduce_only).lower()
                })
                response = self._session.post(url, params=params)
                response.raise_for_status()
                order = response.json()
            
            logger.success(f"Market order placed: {side} {quantity} {symbol}")
            return {
                'order_id': order.get('orderId'),
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity,
                'status': order.get('status'),
                'avg_price': float(order.get('avgPrice', 0)),
                'executed_qty': float(order.get('executedQty', 0))
            }
            
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return None
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> Optional[Dict]:
        """Place a limit order"""
        try:
            self._rate_limit()
            
            if self._futures_client:
                order = self._futures_client.new_order(
                    symbol=symbol,
                    side=side.upper(),
                    type='LIMIT',
                    quantity=quantity,
                    price=price,
                    timeInForce=time_in_force,
                    reduceOnly=reduce_only
                )
            else:
                url = f"{self.FUTURES_BASE_URL}/fapi/v1/order"
                params = self._sign_request({
                    'symbol': symbol,
                    'side': side.upper(),
                    'type': 'LIMIT',
                    'quantity': quantity,
                    'price': price,
                    'timeInForce': time_in_force,
                    'reduceOnly': str(reduce_only).lower()
                })
                response = self._session.post(url, params=params)
                response.raise_for_status()
                order = response.json()
            
            logger.success(f"Limit order placed: {side} {quantity} {symbol} @ {price}")
            return {
                'order_id': order.get('orderId'),
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'quantity': quantity,
                'price': price,
                'status': order.get('status')
            }
            
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            return None
    
    def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        close_position: bool = True
    ) -> Optional[Dict]:
        """
        Place a stop-loss order.
        
        Args:
            symbol: Trading pair
            side: 'BUY' to close short, 'SELL' to close long
            quantity: Order quantity
            stop_price: Trigger price
            close_position: Close entire position
        """
        try:
            self._rate_limit()
            
            if self._futures_client:
                order = self._futures_client.new_order(
                    symbol=symbol,
                    side=side.upper(),
                    type='STOP_MARKET',
                    stopPrice=stop_price,
                    closePosition=close_position
                )
            else:
                url = f"{self.FUTURES_BASE_URL}/fapi/v1/order"
                params = self._sign_request({
                    'symbol': symbol,
                    'side': side.upper(),
                    'type': 'STOP_MARKET',
                    'stopPrice': stop_price,
                    'closePosition': str(close_position).lower()
                })
                response = self._session.post(url, params=params)
                response.raise_for_status()
                order = response.json()
            
            logger.success(f"Stop-loss placed: {side} {symbol} @ {stop_price}")
            return {
                'order_id': order.get('orderId'),
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'stop_price': stop_price,
                'status': order.get('status')
            }
            
        except Exception as e:
            logger.error(f"Failed to place stop-loss: {e}")
            return None
    
    def place_take_profit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_price: float,
        close_position: bool = True
    ) -> Optional[Dict]:
        """Place a take-profit order"""
        try:
            self._rate_limit()
            
            if self._futures_client:
                order = self._futures_client.new_order(
                    symbol=symbol,
                    side=side.upper(),
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=take_profit_price,
                    closePosition=close_position
                )
            else:
                url = f"{self.FUTURES_BASE_URL}/fapi/v1/order"
                params = self._sign_request({
                    'symbol': symbol,
                    'side': side.upper(),
                    'type': 'TAKE_PROFIT_MARKET',
                    'stopPrice': take_profit_price,
                    'closePosition': str(close_position).lower()
                })
                response = self._session.post(url, params=params)
                response.raise_for_status()
                order = response.json()
            
            logger.success(f"Take-profit placed: {side} {symbol} @ {take_profit_price}")
            return {
                'order_id': order.get('orderId'),
                'symbol': symbol,
                'side': side,
                'type': 'TAKE_PROFIT_MARKET',
                'take_profit_price': take_profit_price,
                'status': order.get('status')
            }
            
        except Exception as e:
            logger.error(f"Failed to place take-profit: {e}")
            return None
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancel an open order"""
        try:
            self._rate_limit()
            
            if self._futures_client:
                self._futures_client.cancel_order(symbol=symbol, orderId=order_id)
            else:
                url = f"{self.FUTURES_BASE_URL}/fapi/v1/order"
                params = self._sign_request({
                    'symbol': symbol,
                    'orderId': order_id
                })
                response = self._session.delete(url, params=params)
                response.raise_for_status()
            
            logger.info(f"Cancelled order {order_id} for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol"""
        try:
            self._rate_limit()
            
            if self._futures_client:
                self._futures_client.cancel_open_orders(symbol=symbol)
            else:
                url = f"{self.FUTURES_BASE_URL}/fapi/v1/allOpenOrders"
                params = self._sign_request({'symbol': symbol})
                response = self._session.delete(url, params=params)
                response.raise_for_status()
            
            logger.info(f"Cancelled all orders for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def close_position(self, symbol: str) -> Optional[Dict]:
        """Close entire position for a symbol"""
        try:
            position = self.get_position(symbol)
            if not position:
                logger.info(f"No position to close for {symbol}")
                return None
            
            close_side = 'SELL' if position['side'] == 'LONG' else 'BUY'
            return self.place_market_order(
                symbol=symbol,
                side=close_side,
                quantity=position['size'],
                reduce_only=True
            )
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return None
    
    # ==================== WEBSOCKET ====================
    
    def subscribe_price_stream(self, symbol: str, callback: Callable):
        """
        Subscribe to real-time price updates.
        
        Args:
            symbol: Trading pair (lowercase, e.g., 'btcusdt')
            callback: Function to call with price updates
        """
        self._price_callbacks.append(callback)
        
        if not self._ws_running:
            self._start_websocket(symbol.lower())
    
    def _start_websocket(self, symbol: str):
        """Start WebSocket connection for price feeds"""
        def on_message(msg):
            try:
                if 'k' in msg:  # Kline data
                    kline = msg['k']
                    data = {
                        'symbol': msg['s'],
                        'time': datetime.fromtimestamp(kline['t'] / 1000),
                        'open': float(kline['o']),
                        'high': float(kline['h']),
                        'low': float(kline['l']),
                        'close': float(kline['c']),
                        'volume': float(kline['v']),
                        'is_closed': kline['x']
                    }
                    for callback in self._price_callbacks:
                        callback(data)
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
        
        def run_ws():
            try:
                if BINANCE_AVAILABLE:
                    self._ws_client = UMFuturesWebsocketClient(
                        on_message=on_message,
                        is_combined=False
                    )
                    self._ws_client.kline(symbol=symbol, interval='1m')
                    self._ws_running = True
                    logger.info(f"WebSocket started for {symbol}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self._ws_running = False
        
        thread = Thread(target=run_ws, daemon=True)
        thread.start()
    
    def stop_websocket(self):
        """Stop WebSocket connection"""
        if self._ws_client:
            self._ws_client.stop()
            self._ws_running = False
            logger.info("WebSocket stopped")


# Example usage
if __name__ == "__main__":
    config = {
        'api_key': os.getenv('BINANCE_API_KEY'),
        'api_secret': os.getenv('BINANCE_API_SECRET'),
        'testnet': True,
        'trading': {
            'leverage': 10,
            'margin_type': 'ISOLATED'
        }
    }
    
    connector = BinanceConnector(config)
    
    # Test market data
    price = connector.get_ticker_price("BTCUSDT")
    print(f"BTCUSDT Price: {price}")
    
    # Test historical data
    klines = connector.get_historical_klines(
        symbol="BTCUSDT",
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-01-02"
    )
    if klines is not None:
        print(f"Historical klines: {len(klines)} rows")
        print(klines.head())
