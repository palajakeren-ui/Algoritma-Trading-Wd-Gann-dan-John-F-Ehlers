"""
Production Trading Loop
The main orchestration loop that ties all components together.

Flow per tick/bar:
1. Fetch data → Validate → Clean
2. Check session hours
3. Compute features (Gann, Ehlers, Technical)
4. Generate signals per source
5. Fuse signals with adaptive weights
6. Risk check → Position size
7. Submit through order router
8. Log to trade journal
9. Monitor drift & performance
"""

import asyncio
import time
import traceback
import numpy as np
from typing import Dict, Optional, Any
from loguru import logger
from datetime import datetime

from src.data.validator import DataValidator
from src.data.cleaner import DataCleaner
from src.data.session_controller import SessionController
from src.features.feature_pipeline import FeaturePipeline
from src.signals.signal_generator import SignalGenerator
from src.fusion.adaptive_weighting import AdaptiveWeighting
from src.risk.circuit_breaker import CircuitBreaker
from src.risk.drawdown_protector import DrawdownProtector
from src.risk.position_sizer import PositionSizer
from src.execution.order_router import OrderRouter
from src.monitoring.trade_journal import TradeJournal
from src.ml.drift_detector import DriftDetector
from src.orchestration.mode_controller import ModeController, TradingMode


class TradingLoop:
    """
    Main orchestration loop.
    
    Coordinates all layers:
    Data → Features → Signals → Fusion → Risk → Execution → Monitoring
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        # Initialize all layers
        self.mode_controller = ModeController(config.get("mode", {}))
        self.validator = DataValidator(config.get("validator", {}))
        self.cleaner = DataCleaner(config.get("cleaner", {}))
        self.session = SessionController(config.get("session", {}))
        self.feature_pipeline = FeaturePipeline(config.get("features", {}))
        self.signal_generator = SignalGenerator(config.get("signals", {}))
        self.fusion = AdaptiveWeighting(config.get("fusion", {}))
        self.circuit_breaker = CircuitBreaker(config.get("circuit_breaker", {}))
        self.drawdown_protector = DrawdownProtector(config.get("drawdown", {}))
        self.position_sizer = PositionSizer(config.get("position_sizer", {}))
        self.order_router = OrderRouter(config.get("execution", {}))
        self.trade_journal = TradeJournal(config.get("journal_dir", "data/journal"))
        self.drift_detector = DriftDetector(config.get("drift", {}))
        
        # State
        self._running = False
        self._tick_count = 0
        self._error_count = 0
        self._max_errors = config.get("max_errors", 10)
        self._data_fetch_fn = None
        self._account_balance = config.get("initial_capital", 100000.0)
        
        # Trading parameters
        self.symbol = config.get("symbol", "BTCUSDT")
        self.timeframe = config.get("timeframe", "1h")
        self.min_signal_strength = config.get("min_signal_strength", 0.3)
        self.tick_interval_seconds = config.get("tick_interval_seconds", 60)
        
        # Mark circuit breaker as the order router's CB
        self.mode_controller.mark_circuit_breaker_ready()
        
        logger.info(f"Trading loop initialized: {self.symbol} {self.timeframe}")
    
    def register_data_source(self, fetch_fn):
        """Register data fetch function: fn(symbol, timeframe) -> DataFrame."""
        self._data_fetch_fn = fetch_fn
    
    def start(self):
        """Start the trading loop."""
        self._running = True
        logger.info(f"🚀 Trading loop STARTED | Mode: {self.mode_controller.mode.value}")
        
        while self._running:
            try:
                self._tick()
                self._tick_count += 1
                self._error_count = 0  # Reset error count on success
                
                time.sleep(self.tick_interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Trading loop stopped by user")
                self._running = False
            except Exception as e:
                self._error_count += 1
                logger.error(f"Trading loop error #{self._error_count}: {e}\n{traceback.format_exc()}")
                
                if self._error_count >= self._max_errors:
                    logger.critical(f"Max errors reached ({self._max_errors}), stopping")
                    self.circuit_breaker.record_execution_failure(str(e))
                    self._running = False
                
                time.sleep(5)  # Back off on error
        
        logger.info(f"Trading loop STOPPED after {self._tick_count} ticks")
    
    def stop(self):
        """Stop the trading loop."""
        self._running = False
    
    def _tick(self):
        """Single iteration of the trading loop."""
        tick_start = time.perf_counter()
        
        # 1. Session check
        if not self.session.is_trading_allowed():
            logger.debug("Outside trading session, skipping tick")
            return
        
        # 2. Circuit breaker check
        if self.circuit_breaker.is_tripped:
            logger.warning("Circuit breaker tripped, skipping tick")
            return
        
        # 3. Fetch data
        if not self._data_fetch_fn:
            logger.warning("No data source registered")
            return
        
        try:
            raw_data = self._data_fetch_fn(self.symbol, self.timeframe)
        except Exception as e:
            logger.error(f"Data fetch failed: {e}")
            self.circuit_breaker.record_data_feed_failure(str(e))
            return
        
        if raw_data is None or raw_data.empty:
            logger.warning("No data received")
            return
        
        # 4. Validate
        clean_data, validation = self.validator.validate(raw_data, self.timeframe)
        if not validation.is_valid:
            logger.warning(f"Data validation failed: {validation.errors}")
            return
        
        # 5. Clean
        clean_data = self.cleaner.clean(clean_data, self.timeframe)
        
        # 6. Compute features
        features = self.feature_pipeline.compute(clean_data)
        if features.empty:
            return
        
        # 7. Generate signals
        signals = self.signal_generator.generate(features, self.symbol)
        if not signals:
            return
        
        # 8. Fuse signals
        signal_scores = {name: sig.score for name, sig in signals.items()}
        fused_score = self.fusion.combine_signals(signal_scores, data=clean_data)
        
        logger.info(
            f"Tick #{self._tick_count} | {self.symbol} | "
            f"Fused={fused_score:+.3f} | "
            f"Sources: {', '.join(f'{k}={v:+.3f}' for k, v in signal_scores.items())}"
        )
        
        # 9. Check if signal meets threshold
        if abs(fused_score) < self.min_signal_strength:
            return
        
        # 10. Determine trade direction
        side = "BUY" if fused_score > 0 else "SELL"
        current_price = float(clean_data["close"].iloc[-1])
        
        # 11. Position sizing
        dd_mult = self.drawdown_protector.get_position_size_multiplier()
        atr_value = self._calculate_atr(clean_data)
        
        size_result = self.position_sizer.calculate(
            method="volatility",
            account_balance=self._account_balance,
            entry_price=current_price,
            stop_loss=current_price - (2 * atr_value) if side == "BUY" else current_price + (2 * atr_value),
            atr=atr_value,
            drawdown_multiplier=dd_mult,
        )
        
        quantity = size_result["position_size"]
        if quantity <= 0:
            return
        
        # 12. Calculate SL/TP
        if side == "BUY":
            stop_loss = current_price - 2 * atr_value
            take_profit = current_price + 3 * atr_value
        else:
            stop_loss = current_price + 2 * atr_value
            take_profit = current_price - 3 * atr_value
        
        # 13. Submit order through router
        broker = "paper" if self.mode_controller.is_paper else "live"
        
        order = self.order_router.submit_order(
            symbol=self.symbol,
            side=side,
            quantity=quantity,
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker,
            account_balance=self._account_balance,
            signal_source=max(signal_scores, key=lambda k: abs(signal_scores[k])),
        )
        
        # 14. Log to journal
        if order.status.value in ("FILLED", "PARTIALLY_FILLED"):
            regime = "unknown"
            if self.fusion._current_regime:
                regime = self.fusion._current_regime.primary_regime.value
            
            self.trade_journal.log_open(
                trade_id=order.id,
                symbol=self.symbol,
                side=side,
                quantity=order.filled_quantity,
                entry_price=order.fill_price,
                signal_source=max(signal_scores, key=lambda k: abs(signal_scores[k])),
                signal_score=fused_score,
                regime=regime,
                stop_loss=stop_loss,
                take_profit=take_profit,
                broker=broker,
                execution_latency_ms=order.latency_ms,
                slippage_bps=order.slippage_bps,
            )
        
        # 15. Update drawdown protector
        self.drawdown_protector.update(self._account_balance)
        
        tick_elapsed = (time.perf_counter() - tick_start) * 1000
        logger.debug(f"Tick completed in {tick_elapsed:.1f}ms")
    
    @staticmethod
    def _calculate_atr(df, period: int = 14) -> float:
        """Calculate current ATR from OHLCV data."""
        if len(df) < period + 1:
            close = df["close"].values
            return float(np.std(np.diff(close))) if len(close) > 1 else 0.0
        
        high = df["high"].values[-period-1:]
        low = df["low"].values[-period-1:]
        close = df["close"].values[-period-1:]
        
        tr = np.zeros(len(high))
        tr[0] = high[0] - low[0]
        for i in range(1, len(high)):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        
        return float(np.mean(tr))
    
    def get_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            "running": self._running,
            "tick_count": self._tick_count,
            "error_count": self._error_count,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "mode": self.mode_controller.get_status(),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "drawdown": self.drawdown_protector.get_status(),
            "execution": self.order_router.get_execution_stats(),
            "journal": self.trade_journal.get_performance_summary(),
            "fusion": self.fusion.get_status(),
        }
