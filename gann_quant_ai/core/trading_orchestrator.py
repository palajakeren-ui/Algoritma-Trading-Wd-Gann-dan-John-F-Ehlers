"""
Trading Orchestrator
Unified orchestration layer connecting all trading components.

Integrated with:
- Mode Controller (centralized mode switching)
- Strategy Router (mode-aware signal routing)
- Agent Orchestrator (AI agent lifecycle management)
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import threading
import time


class OrchestratorState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class TradingSession:
    """Trading session info."""
    id: str
    started_at: datetime
    ended_at: datetime = None
    state: OrchestratorState = OrchestratorState.STOPPED
    total_signals: int = 0
    total_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0


class TradingOrchestrator:
    """
    Unified Trading Orchestrator.
    
    Connects all components:
    - Real-time data feed → Signal engine
    - Signal engine → Execution gate
    - Execution gate → Risk engine
    - Risk engine → Execution engine
    - Execution engine → Connectors
    
    Features:
    - Automated trading loop
    - Multi-symbol monitoring
    - Session management
    - Performance tracking
    - Event-driven architecture
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.state = OrchestratorState.STOPPED
        
        # Core Components (lazy initialization)
        self._data_feed = None
        self._signal_engine = None
        self._execution_gate = None
        self._risk_engine = None
        self._execution_engine = None
        self._account_manager = None
        
        # AI Agent Components
        self._mode_controller = None
        self._strategy_router = None
        self._agent_orchestrator = None
        
        # Trading configuration
        self.symbols: List[str] = self.config.get('symbols', [])
        self.timeframes: List[str] = self.config.get('timeframes', ['1h'])
        self.scan_interval_seconds: int = self.config.get('scan_interval', 60)
        
        # Session tracking
        self._current_session: Optional[TradingSession] = None
        self._session_history: List[TradingSession] = []
        
        # Trading loop
        self._running = False
        self._trading_thread: Optional[threading.Thread] = None
        
        # Event callbacks
        self._on_signal_callbacks: List[Callable] = []
        self._on_trade_callbacks: List[Callable] = []
        self._on_error_callbacks: List[Callable] = []
        
        logger.info("TradingOrchestrator initialized")
    
    # ========================
    # Component Initialization
    # ========================
    
    def _init_components(self):
        """Initialize all components including AI agent layer."""
        try:
            # Data Feed
            from core.realtime_data_feed import get_data_feed
            self._data_feed = get_data_feed()
            
            # Signal Engine
            from core.signal_engine import get_signal_engine
            self._signal_engine = get_signal_engine()
            
            # Execution Gate
            from core.execution_gate import get_execution_gate
            self._execution_gate = get_execution_gate()
            
            # Risk Engine
            from core.risk_engine import get_risk_engine
            self._risk_engine = get_risk_engine()
            
            # Execution Engine
            from core.live_execution_engine import get_execution_engine
            self._execution_engine = get_execution_engine()
            
            # Account Manager
            from core.multi_account_manager import get_multi_account_manager
            self._account_manager = get_multi_account_manager()
            
            logger.success("All core trading components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}")
            return False
        
        # Initialize AI Agent Layer (non-fatal if fails)
        try:
            # Mode Controller
            from core.mode_controller import get_mode_controller
            self._mode_controller = get_mode_controller()
            
            # Strategy Router
            from router.strategy_router import StrategyRouter
            self._strategy_router = StrategyRouter()
            
            # Agent Orchestrator
            from agent.agent_orchestrator import get_agent_orchestrator
            self._agent_orchestrator = get_agent_orchestrator(
                risk_engine=self._risk_engine
            )
            
            # Register mode change callback
            self._mode_controller.on_mode_change(self._on_mode_changed)
            self._mode_controller.on_emergency_revert(self._on_emergency)
            
            # Start agent monitoring
            self._agent_orchestrator.start_monitoring()
            
            logger.success("AI Agent layer initialized")
            
        except Exception as e:
            logger.warning(f"AI Agent layer not available (non-fatal): {e}")
            self._mode_controller = None
            self._strategy_router = None
            self._agent_orchestrator = None
        
        return True
    
    # ========================
    # Orchestration
    # ========================
    
    async def start(self) -> bool:
        """Start trading orchestrator."""
        if self.state == OrchestratorState.RUNNING:
            logger.warning("Orchestrator already running")
            return False
        
        self.state = OrchestratorState.STARTING
        
        # Initialize components
        if not self._init_components():
            self.state = OrchestratorState.ERROR
            return False
        
        # Start data feed
        self._data_feed.start()
        
        # Subscribe to symbols
        if self.symbols:
            await self._data_feed.subscribe_ticks(self.symbols)
        
        # Initialize risk engine with account balance
        default_account = self._account_manager.get_default_account()
        if default_account and default_account.balance:
            self._risk_engine.initialize_equity(default_account.balance.total)
        else:
            self._risk_engine.initialize_equity(10000)  # Default
        
        # Create session
        self._current_session = TradingSession(
            id=f"SESSION_{int(datetime.now().timestamp())}",
            started_at=datetime.now(),
            state=OrchestratorState.RUNNING
        )
        
        # Start trading loop
        self._running = True
        self._trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self._trading_thread.start()
        
        self.state = OrchestratorState.RUNNING
        logger.success(f"Trading orchestrator started - Session: {self._current_session.id}")
        
        return True
    
    async def stop(self) -> bool:
        """Stop trading orchestrator."""
        self._running = False
        
        # Wait for trading thread
        if self._trading_thread and self._trading_thread.is_alive():
            self._trading_thread.join(timeout=5)
        
        # Stop data feed
        if self._data_feed:
            self._data_feed.stop()
        
        # End session
        if self._current_session:
            self._current_session.ended_at = datetime.now()
            self._current_session.state = OrchestratorState.STOPPED
            self._session_history.append(self._current_session)
            self._current_session = None
        
        self.state = OrchestratorState.STOPPED
        logger.info("Trading orchestrator stopped")
        
        return True
    
    def pause(self):
        """Pause trading (no new signals processed)."""
        self.state = OrchestratorState.PAUSED
        logger.info("Trading paused")
    
    def resume(self):
        """Resume trading."""
        if self.state == OrchestratorState.PAUSED:
            self.state = OrchestratorState.RUNNING
            logger.info("Trading resumed")
    
    def _trading_loop(self):
        """Main trading loop."""
        logger.info("Trading loop started")
        
        while self._running:
            try:
                if self.state != OrchestratorState.RUNNING:
                    time.sleep(1)
                    continue
                
                # Process each symbol
                for symbol in self.symbols:
                    self._process_symbol(symbol)
                
                # Wait for next scan
                time.sleep(self.scan_interval_seconds)
                
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                for callback in self._on_error_callbacks:
                    try:
                        callback(e)
                    except:
                        pass
                time.sleep(5)
        
        logger.info("Trading loop stopped")
    
    def _process_symbol(self, symbol: str):
        """Process a single symbol through the full pipeline (mode-aware)."""
        try:
            # Get historical data for analysis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for timeframe in self.timeframes:
                df = loop.run_until_complete(
                    self._data_feed.get_historical_data(symbol, timeframe, 100)
                )
                
                if df is None or len(df) < 50:
                    continue
                
                # Generate signal
                signal = self._signal_engine.generate_signal(symbol, df, timeframe)
                
                if signal and self._current_session:
                    self._current_session.total_signals += 1
                
                # Route through Strategy Router (mode-aware)
                routed_signal = signal
                if self._strategy_router and self._mode_controller:
                    try:
                        # Extract rule/ML components from the generated signal
                        rule_output = {}
                        ml_output = {}
                        if signal and hasattr(signal, 'signal'):
                            rule_output = {
                                "direction": str(signal.signal.value) if hasattr(signal.signal, 'value') else str(signal.signal),
                                "confidence": getattr(signal, 'confidence', 0.0) / 100.0 if getattr(signal, 'confidence', 0) > 1 else getattr(signal, 'confidence', 0.0),
                            }
                        if signal and hasattr(signal, 'components'):
                            for comp in getattr(signal, 'components', []):
                                if hasattr(comp, 'source') and 'ml' in str(comp.source).lower():
                                    ml_output = {
                                        "probability": getattr(comp, 'confidence', 0.5) / 100.0 if getattr(comp, 'confidence', 0) > 1 else getattr(comp, 'confidence', 0.5),
                                    }
                        
                        routed = self._strategy_router.route_signal(
                            symbol=symbol,
                            rule_output=rule_output,
                            ml_output=ml_output,
                            price_data=df,
                        )
                        if routed:
                            routed_signal = routed
                    except Exception as e:
                        logger.warning(f"Strategy routing error for {symbol}: {e}")
                
                # Feed to Agent Orchestrator for regime detection (Mode 3+)
                if self._agent_orchestrator and self._mode_controller:
                    try:
                        if self._mode_controller.is_ai_active:
                            self._agent_orchestrator.detect_regime(
                                price_data=df,
                            )
                    except Exception as e:
                        logger.debug(f"Agent regime detection skip: {e}")
                
                # Notify signal callbacks
                for callback in self._on_signal_callbacks:
                    try:
                        callback(routed_signal)
                    except Exception as e:
                        logger.warning(f"Signal callback error: {e}")
                
                # Check if actionable signal
                from core.signal_engine import SignalType
                is_actionable = False
                if hasattr(routed_signal, 'signal'):
                    is_actionable = routed_signal.signal not in [SignalType.HOLD]
                elif isinstance(routed_signal, dict):
                    is_actionable = routed_signal.get('action') not in ['hold', 'HOLD', None]
                
                if is_actionable:
                    
                    # Mode 4: Create trade proposal instead of executing
                    if (self._mode_controller and self._mode_controller.is_autonomous 
                            and self._agent_orchestrator):
                        try:
                            signal_dict = routed_signal if isinstance(routed_signal, dict) else {
                                'symbol': symbol,
                                'action': str(routed_signal.signal.value) if hasattr(routed_signal, 'signal') else 'unknown',
                                'confidence': getattr(routed_signal, 'confidence', 0),
                            }
                            self._agent_orchestrator.propose_trade(
                                symbol=symbol,
                                rule_signal=signal_dict,
                                ml_prediction={},
                            )
                            logger.info(f"Trade proposal created for {symbol} (Mode 4)")
                        except Exception as e:
                            logger.warning(f"Trade proposal error for {symbol}: {e}")
                        continue  # Don't auto-execute in Mode 4
                    
                    # Get default account
                    account = self._account_manager.get_default_account()
                    exchange = account.exchange if account else "binance"
                    account_id = account.id if account else "default"
                    
                    # Process through execution gate
                    result = loop.run_until_complete(
                        self._execution_gate.process_signal(
                            signal=routed_signal,
                            account_id=account_id,
                            exchange=exchange,
                            leverage=min(5, account.max_leverage if account else 1)
                        )
                    )
                    
                    # Track trade
                    if result.status.value == 'executed':
                        if self._current_session:
                            self._current_session.total_trades += 1
                        
                        # Notify trade callbacks
                        for callback in self._on_trade_callbacks:
                            try:
                                callback(result)
                            except Exception as e:
                                logger.warning(f"Trade callback error: {e}")
            
            loop.close()
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    # ========================
    # Configuration
    # ========================
    
    def add_symbol(self, symbol: str):
        """Add symbol to watch list."""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            
            # Subscribe if running
            if self._data_feed and self._running:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._data_feed.subscribe_ticks([symbol]))
                loop.close()
            
            logger.info(f"Added symbol: {symbol}")
    
    def remove_symbol(self, symbol: str):
        """Remove symbol from watch list."""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            logger.info(f"Removed symbol: {symbol}")
    
    def set_scan_interval(self, seconds: int):
        """Set scan interval."""
        self.scan_interval_seconds = max(10, seconds)
        logger.info(f"Scan interval set to {self.scan_interval_seconds}s")
    
    # ========================
    # Event Handlers
    # ========================
    
    def on_signal(self, callback: Callable):
        """Register signal callback."""
        self._on_signal_callbacks.append(callback)
    
    def on_trade(self, callback: Callable):
        """Register trade callback."""
        self._on_trade_callbacks.append(callback)
    
    def on_error(self, callback: Callable):
        """Register error callback."""
        self._on_error_callbacks.append(callback)
    
    # ========================
    # Mode Change Handlers
    # ========================
    
    def _on_mode_changed(self, old_mode: int, new_mode: int, reason: str):
        """Handle mode change events from Mode Controller."""
        logger.info(f"TradingOrchestrator notified: M{old_mode}→M{new_mode} ({reason})")
        
        # Update strategy router if available
        if self._strategy_router:
            try:
                self._strategy_router.set_mode(new_mode)
            except Exception as e:
                logger.warning(f"Failed to update strategy router mode: {e}")
        
        # Update agent orchestrator if available
        if self._agent_orchestrator:
            try:
                self._agent_orchestrator.switch_mode(new_mode, reason)
            except Exception as e:
                logger.warning(f"Failed to update agent orchestrator mode: {e}")
    
    def _on_emergency(self, old_mode: int, reason: str):
        """Handle emergency revert from Mode Controller."""
        logger.warning(f"⚠️ TradingOrchestrator: Emergency revert from M{old_mode}: {reason}")
        
        # Pause trading briefly
        if self.state == OrchestratorState.RUNNING:
            self.pause()
            # Auto-resume after 5 seconds in safe mode
            threading.Timer(5.0, self.resume).start()
    
    # ========================
    # Status & Reporting
    # ========================
    
    def get_status(self) -> Dict:
        """Get orchestrator status (includes AI agent info)."""
        status = {
            'state': self.state.value,
            'symbols': self.symbols,
            'timeframes': self.timeframes,
            'scan_interval': self.scan_interval_seconds,
            'session': {
                'id': self._current_session.id if self._current_session else None,
                'started_at': self._current_session.started_at.isoformat() if self._current_session else None,
                'total_signals': self._current_session.total_signals if self._current_session else 0,
                'total_trades': self._current_session.total_trades if self._current_session else 0
            } if self._current_session else None,
            'components': {
                'data_feed': self._data_feed is not None,
                'signal_engine': self._signal_engine is not None,
                'execution_gate': self._execution_gate is not None,
                'risk_engine': self._risk_engine is not None,
                'execution_engine': self._execution_engine is not None,
                'mode_controller': self._mode_controller is not None,
                'strategy_router': self._strategy_router is not None,
                'agent_orchestrator': self._agent_orchestrator is not None,
            }
        }
        
        # Add mode info if available
        if self._mode_controller:
            status['mode'] = self._mode_controller.get_status()
        
        return status
    
    def get_session_history(self) -> List[Dict]:
        """Get session history."""
        return [
            {
                'id': s.id,
                'started_at': s.started_at.isoformat(),
                'ended_at': s.ended_at.isoformat() if s.ended_at else None,
                'duration_minutes': (
                    (s.ended_at - s.started_at).total_seconds() / 60
                ) if s.ended_at else None,
                'total_signals': s.total_signals,
                'total_trades': s.total_trades,
                'total_pnl': s.total_pnl,
                'win_rate': s.win_rate
            }
            for s in self._session_history
        ]


# Global instance
_orchestrator: Optional[TradingOrchestrator] = None


def get_orchestrator(config: Dict = None) -> TradingOrchestrator:
    """Get or create trading orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TradingOrchestrator(config)
    return _orchestrator


if __name__ == "__main__":
    import asyncio
    
    async def main():
        orchestrator = TradingOrchestrator({
            'symbols': ['BTC/USDT', 'ETH/USDT'],
            'timeframes': ['1h'],
            'scan_interval': 60
        })
        
        # Register callbacks
        def on_signal(signal):
            print(f"Signal: {signal.symbol} - {signal.signal.value} ({signal.confidence:.1f}%)")
        
        def on_trade(result):
            print(f"Trade executed: {result.order.id if result.order else 'N/A'}")
        
        orchestrator.on_signal(on_signal)
        orchestrator.on_trade(on_trade)
        
        # Start
        await orchestrator.start()
        
        print(f"\nOrchestrator Status: {orchestrator.get_status()}")
        
        # Run for 10 seconds
        await asyncio.sleep(10)
        
        # Stop
        await orchestrator.stop()
    
    asyncio.run(main())
