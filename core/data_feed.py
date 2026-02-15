"""
Data Feed Module - Production Broker-Only Data Feed
Fetches market data exclusively from configured broker connectors:
- MetaTrader 4/5 (Forex, CFD, Commodities)
- Crypto Exchanges via CCXT (Binance, Bybit, OKX, etc.)
- FIX Protocol (Institutional DMA)

No yfinance or public fallback — all data flows through broker connections.
"""
import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from connectors.metatrader_connector import MetaTraderConnectorFactory, MTCredentials, MTVersion
from connectors.exchange_connector import ExchangeConnectorFactory, ExchangeCredentials
from connectors.fix_connector import FIXConnectorFactory, FIXCredentials

# Try importing ccxt for exchange historical data
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("ccxt not installed. Exchange historical data will be unavailable.")


class DataFeed:
    """
    Handles the retrieval of both historical and real-time market data
    exclusively from configured broker connectors (MT4/MT5, Exchanges, FIX).
    """
    def __init__(self, broker_config: Dict):
        """
        Initializes the DataFeed with broker configurations.

        Args:
            broker_config (Dict): A dictionary containing configuration for brokers.
        """
        self.broker_config = broker_config
        self.connectors: Dict[str, Any] = {}
        self._exchange_instances: Dict[str, Any] = {}  # CCXT exchange instances for historical data
        self._initialize_connectors()
        logger.info("DataFeed initialized (broker-only mode).")

    def _initialize_connectors(self):
        """Initializes connector objects based on the broker configuration."""
        logger.debug("Initializing data connectors from config...")
        
        trading_modes = self.broker_config.get('trading_modes', [])
        
        for mode in trading_modes:
            if not mode.get('enabled', False):
                continue
                
            mode_id = mode.get('id', 'default')
            broker_type = mode.get('brokerType')
            
            try:
                if broker_type == "metatrader":
                    creds = MTCredentials(
                        login=mode.get('mtLogin', ''),
                        password=mode.get('mtPassword', ''),
                        server=mode.get('mtServer', ''),
                        version=MTVersion.MT5 if mode.get('mtType') == 'mt5' else MTVersion.MT4,
                        account_type=mode.get('mtAccountType', 'demo'),
                        broker=mode.get('mtBroker', '')
                    )
                    self.connectors[f"mt_{mode_id}"] = MetaTraderConnectorFactory.create(creds, mode_id)
                    logger.info(f"Initialized MetaTrader connector: {mode_id}")
                    
                elif broker_type == "crypto_exchange":
                    exchange_name = mode.get('exchange', 'binance')
                    creds = ExchangeCredentials(
                        api_key=mode.get('apiKey', ''),
                        api_secret=mode.get('apiSecret', ''),
                        passphrase=mode.get('passphrase', ''),
                        testnet=mode.get('testnet', True),
                        endpoint=mode.get('endpoint', '')
                    )
                    connector = ExchangeConnectorFactory.create(
                        exchange_name,
                        creds,
                        mode_id,
                        mode.get('mode', 'spot')
                    )
                    self.connectors[f"exchange_{mode_id}"] = connector
                    logger.info(f"Initialized Exchange connector: {exchange_name} ({mode_id})")
                    
                    # Also create a lightweight CCXT instance for historical data
                    if CCXT_AVAILABLE:
                        try:
                            ccxt_id = exchange_name.lower()
                            exchange_class = getattr(ccxt, ccxt_id, None)
                            if exchange_class:
                                config = {
                                    'apiKey': mode.get('apiKey', ''),
                                    'secret': mode.get('apiSecret', ''),
                                    'enableRateLimit': True,
                                }
                                if mode.get('testnet', True):
                                    config['sandbox'] = True
                                    
                                trade_mode = mode.get('mode', 'spot')
                                if trade_mode == 'futures':
                                    config['options'] = {
                                        'defaultType': 'swap' if ccxt_id in ['binance', 'bybit', 'okx'] else 'future'
                                    }
                                
                                self._exchange_instances[f"exchange_{mode_id}"] = exchange_class(config)
                                logger.info(f"CCXT historical data instance created: {exchange_name}")
                        except Exception as e:
                            logger.warning(f"Failed to create CCXT instance for {exchange_name}: {e}")
                    
                elif broker_type == "fix":
                    creds = FIXCredentials(
                        host=mode.get('fixHost', ''),
                        port=mode.get('fixPort', 443),
                        sender_comp_id=mode.get('fixSenderCompId', ''),
                        target_comp_id=mode.get('fixTargetCompId', ''),
                        username=mode.get('fixUsername', ''),
                        password=mode.get('fixPassword', ''),
                        heartbeat_interval=mode.get('fixHeartbeatInterval', 30),
                        ssl_enabled=mode.get('fixSslEnabled', True)
                    )
                    self.connectors[f"fix_{mode_id}"] = FIXConnectorFactory.create(creds, mode_id)
                    logger.info(f"Initialized FIX connector: {mode_id}")
            except Exception as e:
                logger.error(f"Failed to initialize connector {mode_id}: {e}")

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: Optional[str] = None,
        source: str = "auto",
    ) -> Optional[pd.DataFrame]:
        """
        Fetches historical OHLCV data from broker connectors.

        Data sources (auto-detected by symbol type):
        - MetaTrader: Forex pairs, CFD, commodities (EURUSD, XAUUSD, etc.)
        - Exchange/CCXT: Crypto pairs (BTC/USDT, ETH/USDT, etc.)
        - FIX: Institutional feeds (if available)

        Args:
            symbol (str): The trading symbol (e.g., "BTC/USDT", "EURUSD").
            timeframe (str): The timeframe (e.g., "1d", "4h", "1h", "1m").
            start_date (str): The start date in "YYYY-MM-DD" format.
            end_date (Optional[str]): The end date. Defaults to today.
            source (str): The source to use ("auto", "metatrader", "exchange", "fix").

        Returns:
            Optional[pd.DataFrame]: A DataFrame with OHLCV columns (open, high, low, close, volume),
                                     or None if no connector is available or an error occurs.
        """
        logger.info(f"Fetching historical data for {symbol} ({timeframe}) from {source}...")

        # Auto-detect source based on symbol
        if source == "auto":
            source = self._detect_source(symbol)

        try:
            if source == "metatrader":
                return self._fetch_from_metatrader(symbol, timeframe, start_date, end_date)
            elif source == "exchange":
                return self._fetch_from_exchange(symbol, timeframe, start_date, end_date)
            elif source == "fix":
                return self._fetch_from_fix(symbol, timeframe, start_date, end_date)
            else:
                # Try all sources in order
                for src in ["metatrader", "exchange", "fix"]:
                    data = self._try_fetch(src, symbol, timeframe, start_date, end_date)
                    if data is not None and not data.empty:
                        return data
                
                logger.warning(f"No data available for {symbol} from any connector")
                return None
                
        except Exception as e:
            logger.error(f"An error occurred while fetching historical data for {symbol}: {e}")
            return None

    def _detect_source(self, symbol: str) -> str:
        """Auto-detect the best source for a given symbol."""
        symbol_upper = symbol.upper()
        
        # Forex/CFD/Commodity patterns → MetaTrader
        forex_patterns = ['EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD', 'XAU', 'XAG']
        is_forex = any(p in symbol_upper for p in forex_patterns) and '/' not in symbol or symbol_upper.endswith('=X')
        
        if is_forex:
            mt_connectors = [k for k in self.connectors if k.startswith('mt_')]
            if mt_connectors:
                return "metatrader"
        
        # Crypto patterns → Exchange
        crypto_patterns = ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD', 'USDC']
        is_crypto = any(p in symbol_upper for p in crypto_patterns)
        
        if is_crypto:
            exchange_connectors = [k for k in self.connectors if k.startswith('exchange_')]
            if exchange_connectors:
                return "exchange"
        
        # FIX connector available
        fix_connectors = [k for k in self.connectors if k.startswith('fix_')]
        if fix_connectors:
            return "fix"
        
        # Default to whatever is available
        if self.connectors:
            first_key = list(self.connectors.keys())[0]
            if first_key.startswith('mt_'):
                return "metatrader"
            elif first_key.startswith('exchange_'):
                return "exchange"
            elif first_key.startswith('fix_'):
                return "fix"
        
        return "auto"  # No connectors available

    def _try_fetch(self, source: str, symbol: str, timeframe: str, 
                   start_date: str, end_date: Optional[str]) -> Optional[pd.DataFrame]:
        """Try fetching from a specific source, return None on failure."""
        try:
            if source == "metatrader":
                return self._fetch_from_metatrader(symbol, timeframe, start_date, end_date)
            elif source == "exchange":
                return self._fetch_from_exchange(symbol, timeframe, start_date, end_date)
            elif source == "fix":
                return self._fetch_from_fix(symbol, timeframe, start_date, end_date)
        except Exception as e:
            logger.debug(f"Fetch from {source} failed for {symbol}: {e}")
        return None

    def _fetch_from_metatrader(self, symbol: str, timeframe: str,
                               start_date: str, end_date: Optional[str]) -> Optional[pd.DataFrame]:
        """Fetch historical data from MetaTrader connector."""
        mt_connectors = {k: v for k, v in self.connectors.items() if k.startswith('mt_')}
        
        if not mt_connectors:
            logger.warning("No MetaTrader connector available")
            return None
        
        # Use first available MT connector
        connector = list(mt_connectors.values())[0]
        
        # Normalize symbol for MT (e.g., "EUR/USD" → "EURUSD")
        mt_symbol = connector.normalize_symbol(symbol) if hasattr(connector, 'normalize_symbol') else symbol.replace('/', '').replace('-', '').upper()
        
        try:
            # Calculate approximate bar count from date range
            start_dt = pd.Timestamp(start_date)
            end_dt = pd.Timestamp(end_date) if end_date else pd.Timestamp.now()
            days = (end_dt - start_dt).days
            
            tf_bars_per_day = {
                '1m': 1440, '5m': 288, '15m': 96, '30m': 48,
                '1h': 24, '2h': 12, '4h': 6, '1d': 1, '1w': 0.14
            }
            bars_per_day = tf_bars_per_day.get(timeframe, 24)
            count = max(int(days * bars_per_day), 100)
            
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new event loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        data = pool.submit(
                            lambda: asyncio.run(connector.get_historical_data(mt_symbol, timeframe, count))
                        ).result(timeout=30)
                else:
                    data = loop.run_until_complete(
                        connector.get_historical_data(mt_symbol, timeframe, count)
                    )
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                data = loop.run_until_complete(
                    connector.get_historical_data(mt_symbol, timeframe, count)
                )
                loop.close()
            
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                df = self._normalize_columns(df)
                logger.success(f"Successfully fetched {len(df)} rows for {symbol} from MetaTrader.")
                return df
            else:
                logger.info(f"MetaTrader connector returned empty data for {mt_symbol} (simulation mode)")
                return None
                
        except Exception as e:
            logger.warning(f"MetaTrader fetch error for {symbol}: {e}")
            return None

    def _fetch_from_exchange(self, symbol: str, timeframe: str,
                              start_date: str, end_date: Optional[str]) -> Optional[pd.DataFrame]:
        """Fetch historical data from crypto exchange via CCXT."""
        if not CCXT_AVAILABLE:
            logger.warning("CCXT not available for exchange historical data")
            return None
        
        # Find an exchange instance
        exchange_instance = None
        for key, instance in self._exchange_instances.items():
            exchange_instance = instance
            break
        
        if exchange_instance is None:
            logger.warning("No exchange instance available for historical data")
            return None
        
        # Normalize symbol for exchange (e.g., "BTC-USD" → "BTC/USDT")
        ex_symbol = self._normalize_symbol_exchange(symbol)
        
        # Map timeframe to CCXT format
        tf_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '4h': '4h', '1d': '1d', '1w': '1w',
            'M1': '1m', 'M5': '5m', 'M15': '15m', 'M30': '30m',
            'H1': '1h', 'H2': '2h', 'H4': '4h', 'D1': '1d', 'W1': '1w',
        }
        ccxt_tf = tf_map.get(timeframe, timeframe)
        
        try:
            # Convert start_date to milliseconds
            since = int(pd.Timestamp(start_date).timestamp() * 1000)
            
            # Calculate limit
            start_dt = pd.Timestamp(start_date)
            end_dt = pd.Timestamp(end_date) if end_date else pd.Timestamp.now()
            days = (end_dt - start_dt).days
            tf_bars_per_day = {
                '1m': 1440, '5m': 288, '15m': 96, '30m': 48,
                '1h': 24, '2h': 12, '4h': 6, '1d': 1, '1w': 0.14
            }
            bars_per_day = tf_bars_per_day.get(ccxt_tf, 24)
            limit = min(max(int(days * bars_per_day), 100), 1000)
            
            # Fetch OHLCV via CCXT (synchronous)
            ohlcv = exchange_instance.fetch_ohlcv(ex_symbol, ccxt_tf, since=since, limit=limit)
            
            if ohlcv and len(ohlcv) > 0:
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Filter by end_date if provided
                if end_date:
                    df = df[df.index <= end_date]
                
                logger.success(f"Successfully fetched {len(df)} rows for {symbol} from exchange.")
                return df
            else:
                logger.warning(f"Exchange returned empty data for {ex_symbol}")
                return None
                
        except Exception as e:
            logger.warning(f"Exchange fetch error for {symbol}: {e}")
            return None

    def _fetch_from_fix(self, symbol: str, timeframe: str,
                         start_date: str, end_date: Optional[str]) -> Optional[pd.DataFrame]:
        """Fetch historical data from FIX connector."""
        fix_connectors = {k: v for k, v in self.connectors.items() if k.startswith('fix_')}
        
        if not fix_connectors:
            logger.warning("No FIX connector available")
            return None
        
        # FIX protocol typically doesn't provide historical data
        # It's primarily for real-time market data and order execution
        logger.info("FIX protocol: historical data not available (use for real-time only)")
        return None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame column names to lowercase OHLCV standard."""
        column_map = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
            'Volume': 'volume', 'Adj Close': 'adj_close',
            'time': 'timestamp', 'date': 'timestamp', 'datetime': 'timestamp',
            'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close',
            'v': 'volume', 'vol': 'volume'
        }
        
        rename_needed = {c: column_map[c] for c in df.columns if c in column_map}
        if rename_needed:
            df = df.rename(columns=rename_needed)
        
        # Ensure required columns exist
        for col in ['open', 'high', 'low', 'close']:
            if col not in df.columns:
                logger.warning(f"Missing column '{col}' in data")
        
        return df

    def _normalize_symbol_exchange(self, symbol: str) -> str:
        """Convert symbol to exchange format (CCXT expects 'BTC/USDT')."""
        symbol = symbol.upper()
        
        # Already in CCXT format
        if '/' in symbol:
            return symbol
        
        # "BTCUSDT" → "BTC/USDT"
        stable_coins = ['USDT', 'BUSD', 'USDC', 'USD', 'TUSD', 'DAI']
        for sc in stable_coins:
            if symbol.endswith(sc):
                base = symbol[:-len(sc)]
                return f"{base}/{sc}"
        
        # "BTC-USD" → "BTC/USD"
        if '-' in symbol:
            return symbol.replace('-', '/')
        
        return symbol

    def get_available_connectors(self) -> Dict[str, str]:
        """Get a summary of all available connectors."""
        result = {}
        for key, connector in self.connectors.items():
            conn_type = key.split('_')[0] if '_' in key else key
            status = "initialized"
            if hasattr(connector, 'is_connected'):
                status = "connected" if connector.is_connected else "disconnected"
            result[key] = f"{conn_type} ({status})"
        return result


# Example Usage:
if __name__ == "__main__":
    # Minimal config for testing with broker connectors
    mock_broker_config = {
        "trading_modes": [
            {
                "id": "demo_mt5",
                "enabled": True,
                "brokerType": "metatrader",
                "mtType": "mt5",
                "mtLogin": "12345678",
                "mtPassword": "password",
                "mtServer": "Demo-Server:443",
                "mtAccountType": "demo",
                "mtBroker": "ICMarkets"
            },
            {
                "id": "binance_spot",
                "enabled": True,
                "brokerType": "crypto_exchange",
                "exchange": "binance",
                "apiKey": "",
                "apiSecret": "",
                "testnet": True,
                "mode": "spot"
            }
        ]
    }

    data_feed = DataFeed(broker_config=mock_broker_config)
    
    print("Available connectors:")
    for name, status in data_feed.get_available_connectors().items():
        print(f"  - {name}: {status}")
    
    # Attempt to fetch data (will use broker connectors)
    btc_data = data_feed.get_historical_data(
        symbol="BTC/USDT",
        timeframe="1d",
        start_date="2024-01-01",
        end_date="2024-01-10"
    )
    
    if btc_data is not None:
        print(f"\nBTC/USDT Data ({len(btc_data)} rows):")
        print(btc_data.head())
    else:
        print("\nNo data returned (connectors may be in simulation mode)")
