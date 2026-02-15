"""
Unified Real-Time Market Data Feed
Supports MT4/MT5, FIX Protocol, and Crypto Exchange data sources.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import asyncio
import time
import queue


class DataSource(Enum):
    METATRADER = "metatrader"
    FIX = "fix"
    CRYPTO_EXCHANGE = "crypto_exchange"
    COMBINED = "combined"


class Timeframe(Enum):
    M1 = "1m"
    M2 = "2m"
    M3 = "3m"
    M5 = "5m"
    M10 = "10m"
    M15 = "15m"
    M30 = "30m"
    M45 = "45m"
    H1 = "1h"
    H2 = "2h"
    H3 = "3h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN = "1M"


@dataclass
class Tick:
    """Real-time tick data."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    source: DataSource = DataSource.CRYPTO_EXCHANGE
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


@dataclass
class OHLCV:
    """OHLCV bar data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    symbol: str = ""
    timeframe: str = "1h"
    source: DataSource = DataSource.CRYPTO_EXCHANGE


class RealTimeDataFeed:
    """
    Unified Real-Time Market Data Feed.
    
    Supports:
    - MetaTrader 4/5 (via MT connector)
    - FIX Protocol (via FIX connector)
    - Crypto Exchanges (via CCXT)
    
    Features:
    - Real-time tick streaming
    - OHLCV bar aggregation
    - Multi-symbol support
    - Source priority/failover
    - Data normalization
    """
    
    # Timeframe to seconds mapping
    TF_SECONDS = {
        Timeframe.M1: 60,
        Timeframe.M2: 120,
        Timeframe.M3: 180,
        Timeframe.M5: 300,
        Timeframe.M10: 600,
        Timeframe.M15: 900,
        Timeframe.M30: 1800,
        Timeframe.M45: 2700,
        Timeframe.H1: 3600,
        Timeframe.H2: 7200,
        Timeframe.H3: 10800,
        Timeframe.H4: 14400,
        Timeframe.D1: 86400,
        Timeframe.W1: 604800,
        Timeframe.MN: 2592000,
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Data sources
        self._mt_connector = None
        self._fix_connector = None
        self._exchange_connectors: Dict[str, Any] = {}
        
        # Primary data source
        self.primary_source: DataSource = DataSource(
            self.config.get('primary_source', 'crypto_exchange')
        )
        
        # Streaming state
        self._running = False
        self._tick_queues: Dict[str, queue.Queue] = {}
        self._bar_data: Dict[str, Dict[str, List[OHLCV]]] = {}  # symbol -> timeframe -> bars
        self._current_bars: Dict[str, Dict[str, OHLCV]] = {}  # symbol -> timeframe -> current bar
        
        # Callbacks
        self._tick_callbacks: List[Callable[[Tick], None]] = []
        self._bar_callbacks: List[Callable[[OHLCV], None]] = []
        
        # Threads
        self._stream_threads: Dict[str, threading.Thread] = {}
        self._aggregator_thread: Optional[threading.Thread] = None
        
        logger.info(f"RealTimeDataFeed initialized with primary source: {self.primary_source.value}")
    
    # ========================
    # Connector Configuration
    # ========================
    
    def set_metatrader_connector(self, connector):
        """Set MetaTrader connector for forex data."""
        self._mt_connector = connector
        logger.info("MetaTrader connector configured for data feed")
    
    def set_fix_connector(self, connector):
        """Set FIX protocol connector for institutional data."""
        self._fix_connector = connector
        logger.info("FIX connector configured for data feed")
    
    def add_exchange_connector(self, exchange_id: str, connector):
        """Add crypto exchange connector."""
        self._exchange_connectors[exchange_id] = connector
        logger.info(f"Exchange connector added: {exchange_id}")
    
    def set_primary_source(self, source: DataSource):
        """Set primary data source."""
        self.primary_source = source
        logger.info(f"Primary data source set to: {source.value}")
    
    # ========================
    # Real-Time Tick Data
    # ========================
    
    async def subscribe_ticks(self, symbols: List[str]):
        """Subscribe to real-time tick data for symbols."""
        for symbol in symbols:
            if symbol not in self._tick_queues:
                self._tick_queues[symbol] = queue.Queue(maxsize=10000)
            
            # Start streaming based on primary source
            if self.primary_source == DataSource.METATRADER:
                self._start_mt_stream(symbol)
            elif self.primary_source == DataSource.FIX:
                self._start_fix_stream(symbol)
            elif self.primary_source == DataSource.CRYPTO_EXCHANGE:
                await self._start_exchange_stream(symbol)
        
        logger.info(f"Subscribed to ticks for: {symbols}")
    
    def _start_mt_stream(self, symbol: str):
        """Start MetaTrader tick stream."""
        if not self._mt_connector:
            logger.warning("MetaTrader connector not configured")
            return
        
        def stream_worker():
            mt_symbol = self._normalize_symbol_mt(symbol)
            
            while self._running:
                try:
                    # Get tick from MT connector
                    if hasattr(self._mt_connector, 'get_ticker'):
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        ticker = loop.run_until_complete(
                            self._mt_connector.get_ticker(mt_symbol)
                        )
                        loop.close()
                        
                        if ticker:
                            tick = Tick(
                                symbol=symbol,
                                bid=ticker.get('bid', 0),
                                ask=ticker.get('ask', 0),
                                last=ticker.get('last', ticker.get('bid', 0)),
                                volume=ticker.get('volume', 0),
                                source=DataSource.METATRADER
                            )
                            self._process_tick(tick)
                    
                    time.sleep(0.1)  # 100ms polling
                    
                except Exception as e:
                    logger.warning(f"MT stream error for {symbol}: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()
        self._stream_threads[f"mt_{symbol}"] = thread
    
    def _start_fix_stream(self, symbol: str):
        """Start FIX protocol market data stream."""
        if not self._fix_connector:
            logger.warning("FIX connector not configured")
            return
        
        def on_market_data(data: Dict):
            try:
                tick = Tick(
                    symbol=symbol,
                    bid=float(data.get('bid', 0)),
                    ask=float(data.get('ask', 0)),
                    last=float(data.get('last', 0)),
                    volume=float(data.get('volume', 0)),
                    source=DataSource.FIX
                )
                self._process_tick(tick)
            except Exception as e:
                logger.warning(f"FIX tick processing error: {e}")
        
        # Register callback with FIX connector
        if hasattr(self._fix_connector, 'on_market_data'):
            self._fix_connector._callbacks.setdefault('on_market_data', []).append(on_market_data)
        
        # Request market data subscription
        if hasattr(self._fix_connector, 'subscribe_market_data'):
            asyncio.create_task(self._fix_connector.subscribe_market_data(symbol))
    
    async def _start_exchange_stream(self, symbol: str):
        """Start crypto exchange tick stream."""
        if not self._exchange_connectors:
            logger.warning("No exchange connectors configured")
            return
        
        # Use first available connector
        exchange_id = list(self._exchange_connectors.keys())[0]
        connector = self._exchange_connectors[exchange_id]
        
        def stream_worker():
            while self._running:
                try:
                    # Get ticker from exchange
                    if hasattr(connector, 'get_ticker'):
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        ticker = loop.run_until_complete(connector.get_ticker(symbol))
                        loop.close()
                        
                        if ticker:
                            tick = Tick(
                                symbol=symbol,
                                bid=ticker.get('bid', 0),
                                ask=ticker.get('ask', 0),
                                last=ticker.get('last', 0),
                                volume=ticker.get('volume', 0),
                                source=DataSource.CRYPTO_EXCHANGE
                            )
                            self._process_tick(tick)
                    
                    time.sleep(0.5)  # 500ms polling for exchanges
                    
                except Exception as e:
                    logger.warning(f"Exchange stream error for {symbol}: {e}")
                    time.sleep(2)
        
        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()
        self._stream_threads[f"ex_{symbol}"] = thread
    
    def _process_tick(self, tick: Tick):
        """Process incoming tick data."""
        # Add to queue
        if tick.symbol in self._tick_queues:
            try:
                self._tick_queues[tick.symbol].put_nowait(tick)
            except queue.Full:
                # Remove oldest tick if queue is full
                try:
                    self._tick_queues[tick.symbol].get_nowait()
                    self._tick_queues[tick.symbol].put_nowait(tick)
                except:
                    pass
        
        # Update current bars
        self._update_bars(tick)
        
        # Notify callbacks
        for callback in self._tick_callbacks:
            try:
                callback(tick)
            except Exception as e:
                logger.warning(f"Tick callback error: {e}")
    
    def get_latest_tick(self, symbol: str) -> Optional[Tick]:
        """Get latest tick for a symbol."""
        if symbol in self._tick_queues and not self._tick_queues[symbol].empty():
            try:
                # Get without removing
                tick = None
                temp_list = []
                while not self._tick_queues[symbol].empty():
                    tick = self._tick_queues[symbol].get_nowait()
                    temp_list.append(tick)
                
                # Put back
                for t in temp_list:
                    try:
                        self._tick_queues[symbol].put_nowait(t)
                    except:
                        break
                
                return tick
            except:
                pass
        return None
    
    # ========================
    # OHLCV Bar Data
    # ========================
    
    def _update_bars(self, tick: Tick):
        """Update OHLCV bars from tick data."""
        symbol = tick.symbol
        
        if symbol not in self._current_bars:
            self._current_bars[symbol] = {}
            self._bar_data[symbol] = {}
        
        for tf in [Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1]:
            tf_key = tf.value
            bar_seconds = self.TF_SECONDS[tf]
            
            # Calculate bar timestamp
            ts = tick.timestamp.timestamp()
            bar_ts = datetime.fromtimestamp((ts // bar_seconds) * bar_seconds)
            
            if tf_key not in self._current_bars[symbol]:
                # Create new bar
                self._current_bars[symbol][tf_key] = OHLCV(
                    timestamp=bar_ts,
                    open=tick.last,
                    high=tick.last,
                    low=tick.last,
                    close=tick.last,
                    volume=tick.volume,
                    symbol=symbol,
                    timeframe=tf_key,
                    source=tick.source
                )
                self._bar_data[symbol].setdefault(tf_key, [])
            else:
                current = self._current_bars[symbol][tf_key]
                
                if bar_ts > current.timestamp:
                    # Complete current bar
                    self._bar_data[symbol][tf_key].append(current)
                    
                    # Keep only last 1000 bars
                    if len(self._bar_data[symbol][tf_key]) > 1000:
                        self._bar_data[symbol][tf_key] = self._bar_data[symbol][tf_key][-500:]
                    
                    # Notify bar callbacks
                    for callback in self._bar_callbacks:
                        try:
                            callback(current)
                        except Exception as e:
                            logger.warning(f"Bar callback error: {e}")
                    
                    # Create new bar
                    self._current_bars[symbol][tf_key] = OHLCV(
                        timestamp=bar_ts,
                        open=tick.last,
                        high=tick.last,
                        low=tick.last,
                        close=tick.last,
                        volume=tick.volume,
                        symbol=symbol,
                        timeframe=tf_key,
                        source=tick.source
                    )
                else:
                    # Update current bar
                    current.high = max(current.high, tick.last)
                    current.low = min(current.low, tick.last)
                    current.close = tick.last
                    current.volume += tick.volume
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        source: DataSource = None
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 1h, etc.)
            limit: Number of bars
            source: Data source (uses primary if None)
            
        Returns:
            DataFrame with OHLCV data
        """
        source = source or self.primary_source
        
        try:
            if source == DataSource.METATRADER:
                return await self._get_mt_historical(symbol, timeframe, limit)
            elif source == DataSource.FIX:
                return await self._get_fix_historical(symbol, timeframe, limit)
            elif source == DataSource.CRYPTO_EXCHANGE:
                return await self._get_exchange_historical(symbol, timeframe, limit)
            else:
                # Combined: try each source until one works
                for s in [DataSource.METATRADER, DataSource.FIX, DataSource.CRYPTO_EXCHANGE]:
                    try:
                        data = await self.get_historical_data(symbol, timeframe, limit, s)
                        if data is not None and len(data) > 0:
                            return data
                    except:
                        continue
                
                # Fallback: use cached bar data
                return self._get_cached_bars(symbol, timeframe, limit)
                
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return self._get_cached_bars(symbol, timeframe, limit)
    
    async def _get_mt_historical(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get historical data from MetaTrader."""
        if not self._mt_connector:
            return pd.DataFrame()
        
        try:
            mt_symbol = self._normalize_symbol_mt(symbol)
            data = await self._mt_connector.get_historical_data(mt_symbol, timeframe, limit)
            
            if data:
                df = pd.DataFrame(data)
                df['source'] = 'metatrader'
                return self._normalize_dataframe(df)
        except Exception as e:
            logger.warning(f"MT historical data error: {e}")
        
        return pd.DataFrame()
    
    async def _get_fix_historical(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get historical data from FIX (typically not available)."""
        # FIX protocol typically doesn't provide historical data
        return pd.DataFrame()
    
    async def _get_exchange_historical(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get historical data from crypto exchange."""
        if not self._exchange_connectors:
            return pd.DataFrame()
        
        try:
            # Use first available connector
            exchange_id = list(self._exchange_connectors.keys())[0]
            connector = self._exchange_connectors[exchange_id]
            
            if hasattr(connector, 'exchange') and connector.exchange:
                # Use CCXT fetch_ohlcv
                ohlcv = await connector.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                if ohlcv:
                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    df['source'] = exchange_id
                    return df
                    
        except Exception as e:
            logger.warning(f"Exchange historical data error: {e}")
        
        return pd.DataFrame()
    
    def _get_cached_bars(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get bars from local cache."""
        if symbol in self._bar_data and timeframe in self._bar_data[symbol]:
            bars = self._bar_data[symbol][timeframe][-limit:]
            
            if bars:
                data = [
                    {
                        'timestamp': b.timestamp,
                        'open': b.open,
                        'high': b.high,
                        'low': b.low,
                        'close': b.close,
                        'volume': b.volume
                    }
                    for b in bars
                ]
                df = pd.DataFrame(data)
                df.set_index('timestamp', inplace=True)
                return df
        
        return pd.DataFrame()
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame column names."""
        column_map = {
            'time': 'timestamp',
            'date': 'timestamp',
            'datetime': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume',
            'vol': 'volume'
        }
        
        df.columns = [column_map.get(c.lower(), c.lower()) for c in df.columns]
        
        if 'timestamp' in df.columns and df.index.name != 'timestamp':
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        return df
    
    def _normalize_symbol_mt(self, symbol: str) -> str:
        """Convert symbol to MetaTrader format."""
        # BTC/USDT -> BTCUSDT, EUR/USD -> EURUSD
        return symbol.replace("/", "").replace("-", "")
    
    # ========================
    # Stream Control
    # ========================
    
    def start(self):
        """Start data feed streaming."""
        self._running = True
        logger.info("Real-time data feed started")
    
    def stop(self):
        """Stop data feed streaming."""
        self._running = False
        
        # Wait for threads to stop
        for thread in self._stream_threads.values():
            if thread.is_alive():
                thread.join(timeout=2)
        
        self._stream_threads.clear()
        logger.info("Real-time data feed stopped")
    
    def on_tick(self, callback: Callable[[Tick], None]):
        """Register tick callback."""
        self._tick_callbacks.append(callback)
    
    def on_bar(self, callback: Callable[[OHLCV], None]):
        """Register bar callback."""
        self._bar_callbacks.append(callback)
    
    # ========================
    # Convenience Methods
    # ========================
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        tick = self.get_latest_tick(symbol)
        if tick:
            return tick.last
        
        # Fallback: fetch from exchange
        if self._exchange_connectors:
            exchange_id = list(self._exchange_connectors.keys())[0]
            connector = self._exchange_connectors[exchange_id]
            
            try:
                ticker = await connector.get_ticker(symbol)
                return ticker.get('last', 0)
            except:
                pass
        
        return None
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book for symbol."""
        if self._exchange_connectors:
            exchange_id = list(self._exchange_connectors.keys())[0]
            connector = self._exchange_connectors[exchange_id]
            
            try:
                return await connector.get_orderbook(symbol, limit)
            except:
                pass
        
        return {'bids': [], 'asks': []}
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols."""
        return list(self._tick_queues.keys())
    
    def get_data_sources(self) -> Dict[str, bool]:
        """Get available data sources."""
        return {
            'metatrader': self._mt_connector is not None,
            'fix': self._fix_connector is not None,
            'crypto_exchange': len(self._exchange_connectors) > 0
        }


# Global data feed instance
_data_feed: Optional[RealTimeDataFeed] = None


def get_data_feed(config: Dict = None) -> RealTimeDataFeed:
    """Get or create real-time data feed."""
    global _data_feed
    if _data_feed is None:
        _data_feed = RealTimeDataFeed(config)
    return _data_feed


async def create_data_feed_with_connectors(
    mt_connector=None,
    fix_connector=None,
    exchange_connectors: Dict = None,
    primary_source: str = "crypto_exchange"
) -> RealTimeDataFeed:
    """Create data feed with pre-configured connectors."""
    feed = RealTimeDataFeed({'primary_source': primary_source})
    
    if mt_connector:
        feed.set_metatrader_connector(mt_connector)
    
    if fix_connector:
        feed.set_fix_connector(fix_connector)
    
    if exchange_connectors:
        for ex_id, connector in exchange_connectors.items():
            feed.add_exchange_connector(ex_id, connector)
    
    return feed


if __name__ == "__main__":
    import asyncio
    
    async def test_feed():
        # Create feed
        feed = RealTimeDataFeed({
            'primary_source': 'crypto_exchange'
        })
        
        # Add tick callback
        def on_tick(tick: Tick):
            print(f"Tick: {tick.symbol} @ {tick.last:.2f} (bid: {tick.bid:.2f}, ask: {tick.ask:.2f})")
        
        feed.on_tick(on_tick)
        
        print("Data Feed Sources:", feed.get_data_sources())
    
    asyncio.run(test_feed())
