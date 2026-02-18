"""
Live Trading Runner v3.0 - Production Ready
Main entry point for live trading with Gann Quant AI
"""
import os
import sys
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Import core components
from utils.config_loader import load_all_configs
from core.data_feed import DataFeed
from core.gann_engine import GannEngine
from core.ehlers_engine import EhlersEngine
from core.astro_engine import AstroEngine
from core.ml_engine import MLEngine
from core.signal_engine import AISignalEngine
from core.execution_engine import ExecutionEngine
from core.order_manager import OrderManager, OrderPriority
from core.risk_manager import RiskManager
from core.portfolio_manager import PortfolioManager
from scanner.hybrid_scanner import HybridScanner


class LiveTradingBot:
    """
    Production-ready live trading bot integrating:
    - Real-time data feeds
    - Multi-engine signal generation
    - Risk management
    - Order execution
    - Position tracking
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize trading bot.
        
        Args:
            config_path: Path to config directory
        """
        self.running = False
        self.paused = False
        
        # Load configuration
        logger.info("Loading configurations...")
        self.config = load_all_configs(config_path)
        if not self.config:
            raise RuntimeError("Failed to load configuration")
        
        # Trading settings
        self.symbols = self.config.get('trading', {}).get('symbols', ['BTC-USD'])
        self.timeframes = self.config.get('trading', {}).get('timeframes', ['1h', '4h', '1d'])
        self.scan_interval = self.config.get('trading', {}).get('scan_interval', 60)  # seconds
        
        # Initialize engines
        self._init_engines()
        
        # State tracking
        self._last_signals: Dict[str, Dict] = {}
        self._active_trades: Dict[str, Dict] = {}
        self._daily_stats = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'pnl': 0.0,
            'max_drawdown': 0.0
        }
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        logger.success("Live Trading Bot initialized")
    
    def _init_engines(self):
        """Initialize all trading engines"""
        logger.info("Initializing trading engines...")
        
        # Data feed
        self.data_feed = DataFeed(self.config.get('broker_config', {}))
        
        # Analysis engines
        self.gann_engine = GannEngine(self.config.get('gann_config', {}))
        self.ehlers_engine = EhlersEngine(self.config.get('ehlers_config', {}))
        self.astro_engine = AstroEngine(self.config.get('astro_config', {}))
        self.ml_engine = MLEngine(self.config)
        self.signal_engine = AISignalEngine(self.config.get('strategy_config', {}))
        
        # Execution
        self.execution_engine = ExecutionEngine({
            'broker_config': self.config.get('broker_config', {}),
            'paper_trading': self.config.get('paper_trading', {'initial_balance': 100000}),
            'risk': self.config.get('risk_config', {})
        })
        
        self.order_manager = OrderManager(
            self.config.get('order_manager', {}),
            self.execution_engine
        )
        
        # Scanner
        self.hybrid_scanner = HybridScanner(self.config.get('scanner_config', {}))
        
        logger.success("All engines initialized")
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal"""
        logger.warning("Shutdown signal received...")
        self.stop()
    
    # ==================== DATA METHODS ====================
    
    def fetch_data(self, symbol: str, timeframe: str = '1d', days: int = 100) -> Optional[pd.DataFrame]:
        """Fetch historical data for a symbol"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            data = self.data_feed.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None
    
    # ==================== ANALYSIS METHODS ====================
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Run full analysis on symbol.
        
        Returns:
            Analysis dictionary with signals and levels
        """
        try:
            # Gann analysis
            gann_levels = self.gann_engine.calculate_sq9_levels(data)
            
            # Ehlers indicators
            data_with_indicators = self.ehlers_engine.calculate_all_indicators(data)
            
            # Astro analysis
            astro_events = self.astro_engine.analyze_dates(data.index)
            
            # ML predictions
            ml_predictions = self.ml_engine.get_predictions(
                data_with_indicators, gann_levels, astro_events
            )
            if ml_predictions is not None:
                data_with_indicators = data_with_indicators.join(ml_predictions)
            
            # Generate signals
            signals = self.signal_engine.generate_signals(
                data_with_indicators, gann_levels, astro_events
            )
            
            # Hybrid scanner
            hybrid_signal = self.hybrid_scanner.scan(data, symbol)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'current_price': data['close'].iloc[-1],
                'gann_levels': gann_levels,
                'signals': signals,
                'hybrid_signal': hybrid_signal,
                'indicators': {
                    'mama': data_with_indicators.get('mama', pd.Series()).iloc[-1] if 'mama' in data_with_indicators.columns else None,
                    'fama': data_with_indicators.get('fama', pd.Series()).iloc[-1] if 'fama' in data_with_indicators.columns else None
                },
                'astro_events': astro_events
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    # ==================== TRADING METHODS ====================
    
    def should_trade(self, analysis: Dict) -> Optional[Dict]:
        """
        Determine if we should enter a trade based on analysis.
        
        Returns:
            Trade parameters if should trade, None otherwise
        """
        hybrid_signal = analysis.get('hybrid_signal')
        
        if hybrid_signal and hybrid_signal.confidence >= 70:
            symbol = analysis['symbol']
            current_price = analysis['current_price']
            
            # Check if already in position
            position = self.execution_engine.get_position(symbol)
            if position:
                logger.info(f"Already have position in {symbol}")
                return None
            
            # Check daily limits
            if self._daily_stats['trades'] >= self.config.get('risk_config', {}).get('max_daily_trades', 5):
                logger.warning("Daily trade limit reached")
                return None
            
            return {
                'symbol': symbol,
                'direction': hybrid_signal.direction,
                'entry': hybrid_signal.entry_price,
                'stop_loss': hybrid_signal.stop_loss,
                'take_profit': hybrid_signal.take_profit,
                'confidence': hybrid_signal.confidence,
                'risk_reward': hybrid_signal.risk_reward
            }
        
        return None
    
    def execute_trade(self, trade_params: Dict) -> bool:
        """Execute a trade based on parameters"""
        try:
            symbol = trade_params['symbol']
            direction = trade_params['direction']
            
            # Calculate position size
            risk_pct = self.config.get('risk_config', {}).get('risk_percentage', 1.5)
            
            # Use fixed position for simplicity (can be enhanced)
            position_size = 0.01  # 0.01 BTC or equivalent
            
            # Submit order
            side = 'BUY' if direction == 'BULLISH' else 'SELL'
            
            success, order_id = self.order_manager.submit_market_order(
                symbol=symbol,
                side=side,
                quantity=position_size,
                stop_loss=trade_params['stop_loss'],
                take_profit=trade_params['take_profit'],
                broker='paper'  # Use paper trading by default
            )
            
            if success:
                logger.success(f"Trade executed: {side} {position_size} {symbol}")
                self._daily_stats['trades'] += 1
                self._active_trades[symbol] = {
                    'order_id': order_id,
                    'side': side,
                    'entry_time': datetime.now(),
                    'params': trade_params
                }
                return True
            else:
                logger.error(f"Trade failed: {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return False
    
    # ==================== MAIN LOOP ====================
    
    def run_cycle(self):
        """Run one analysis and trading cycle"""
        logger.info("Starting trading cycle...")
        
        for symbol in self.symbols:
            try:
                if self.paused:
                    continue
                
                # Fetch data
                data = self.fetch_data(symbol, '1h', 100)
                if data is None or len(data) < 50:
                    logger.warning(f"Insufficient data for {symbol}")
                    continue
                
                # Analyze
                analysis = self.analyze(symbol, data)
                if 'error' in analysis:
                    continue
                
                # Store signal
                self._last_signals[symbol] = analysis
                
                # Check for trade
                trade_params = self.should_trade(analysis)
                if trade_params:
                    logger.info(f"Trade signal for {symbol}: {trade_params['direction']} (Confidence: {trade_params['confidence']:.1f}%)")
                    self.execute_trade(trade_params)
                
            except Exception as e:
                logger.error(f"Cycle error for {symbol}: {e}")
        
        logger.info("Trading cycle complete")
    
    def start(self):
        """Start the trading bot"""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        self.running = True
        logger.info("=" * 50)
        logger.info("🚀 CENAYANG MARKET - Advanced Quant & Astro-Trading Analytics")
        logger.info("=" * 50)
        logger.info("📢 Social Hub")
        logger.info("• Twitter / X : @CenayangMarket")
        logger.info("• Instagram   : @cenayang.market")
        logger.info("• TikTok      : @cenayang.market")
        logger.info("• Facebook    : Cenayang.Market")
        logger.info("• Telegram    : @cenayangmarket")
        logger.info("-" * 50)
        logger.info("☕ Support & Donations")
        logger.info("• Saweria     : saweria.co/CenayangMarket")
        logger.info("• Trakteer    : trakteer.id/Cenayang.Market/tip")
        logger.info("• Patreon     : patreon.com/Cenayangmarket")
        logger.info("=" * 50)
        logger.info(f"📊 Symbols: {', '.join(self.symbols)}")
        logger.info(f"⏱️  Scan Interval: {self.scan_interval}s")
        logger.info("=" * 50)
        
        # Start order manager
        self.order_manager.start_processing()
        
        # Main loop
        while self.running:
            try:
                cycle_start = time.time()
                
                self.run_cycle()
                
                # Wait for next cycle
                elapsed = time.time() - cycle_start
                sleep_time = max(0, self.scan_interval - elapsed)
                
                if sleep_time > 0 and self.running:
                    logger.info(f"Next cycle in {sleep_time:.0f}s...")
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(10)
    
    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.running = False
        
        # Close all positions (optional)
        if self.config.get('trading', {}).get('close_on_stop', False):
            logger.info("Closing all positions...")
            self.execution_engine.close_all_positions()
        
        # Stop order manager
        self.order_manager.stop_processing()
        
        # Print daily stats
        self._print_stats()
        
        logger.success("Trading bot stopped")
    
    def pause(self):
        """Pause trading (keep monitoring)"""
        self.paused = True
        logger.info("Trading paused")
    
    def resume(self):
        """Resume trading"""
        self.paused = False
        logger.info("Trading resumed")
    
    def _print_stats(self):
        """Print daily statistics"""
        logger.info("=" * 50)
        logger.info("📈 Daily Statistics")
        logger.info("=" * 50)
        logger.info(f"Total Trades: {self._daily_stats['trades']}")
        logger.info(f"Wins: {self._daily_stats['wins']}")
        logger.info(f"Losses: {self._daily_stats['losses']}")
        logger.info(f"PnL: ${self._daily_stats['pnl']:,.2f}")
        logger.info(f"Paper Balance: ${self.execution_engine.get_paper_balance():,.2f}")
        logger.info("=" * 50)
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        return {
            'running': self.running,
            'paused': self.paused,
            'symbols': self.symbols,
            'active_trades': len(self._active_trades),
            'daily_stats': self._daily_stats,
            'paper_balance': self.execution_engine.get_paper_balance(),
            'positions': [
                {
                    'symbol': p.symbol,
                    'side': p.side.value,
                    'quantity': p.quantity,
                    'entry_price': p.entry_price,
                    'unrealized_pnl': p.unrealized_pnl
                }
                for p in self.execution_engine.get_all_positions()
            ],
            'last_signals': {
                sym: {
                    'direction': s.get('hybrid_signal').direction if s.get('hybrid_signal') else None,
                    'confidence': s.get('hybrid_signal').confidence if s.get('hybrid_signal') else None
                }
                for sym, s in self._last_signals.items()
                if s.get('hybrid_signal')
            }
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gann Quant AI Live Trading Bot')
    parser.add_argument('--config', type=str, help='Path to config directory')
    parser.add_argument('--paper', action='store_true', help='Run in paper trading mode')
    parser.add_argument('--symbols', type=str, nargs='+', help='Symbols to trade')
    parser.add_argument('--interval', type=int, default=60, help='Scan interval in seconds')
    args = parser.parse_args()
    
    # Setup logging
    logger.add(
        "logs/trading_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    try:
        bot = LiveTradingBot(args.config)
        
        if args.symbols:
            bot.symbols = args.symbols
        if args.interval:
            bot.scan_interval = args.interval
        
        bot.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
