"""
Production Risk Management Engine
Live-trading safe risk controls with kill-switch capability.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import json


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskViolationType(Enum):
    MAX_POSITION_SIZE = "max_position_size"
    MAX_DAILY_LOSS = "max_daily_loss"
    MAX_DRAWDOWN = "max_drawdown"
    LEVERAGE_EXCEEDED = "leverage_exceeded"
    MARGIN_INSUFFICIENT = "margin_insufficient"
    LIQUIDITY_CHECK = "liquidity_check"
    SLIPPAGE_CHECK = "slippage_check"
    TIME_RESTRICTION = "time_restriction"
    KILL_SWITCH = "kill_switch"
    CONCURRENT_POSITIONS = "concurrent_positions"


@dataclass
class RiskConfig:
    """Risk management configuration."""
    # Per-trade limits
    max_risk_per_trade: float = 2.0  # Percentage of account
    max_position_size: float = 10.0  # Percentage of account
    max_leverage: int = 10
    
    # Daily limits
    max_daily_loss: float = 5.0  # Percentage
    max_daily_trades: int = 50
    
    # Weekly limits
    max_weekly_loss: float = 15.0  # Percentage
    
    # Drawdown protection
    max_drawdown: float = 20.0  # Percentage
    drawdown_protection_enabled: bool = True
    
    # Position limits
    max_open_positions: int = 5
    max_correlated_positions: int = 3
    
    # Slippage & liquidity
    max_slippage: float = 0.5  # Percentage
    min_liquidity_ratio: float = 10.0  # Order size / daily volume
    
    # Time restrictions
    time_restrictions_enabled: bool = False
    allowed_trading_hours: List[str] = field(default_factory=lambda: ["00:00-23:59"])
    
    # Kill switch
    kill_switch_enabled: bool = True
    kill_switch_loss_threshold: float = 10.0  # Percentage trigger
    
    # Risk reward
    min_risk_reward_ratio: float = 1.5


@dataclass
class RiskCheckResult:
    """Result of a risk check."""
    passed: bool
    risk_level: RiskLevel
    violations: List[RiskViolationType] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    adjusted_position_size: Optional[float] = None
    
    def add_violation(self, violation: RiskViolationType, message: str):
        self.violations.append(violation)
        self.messages.append(message)
        self.passed = False


@dataclass 
class TradeMetrics:
    """Daily/weekly trading metrics."""
    date: datetime
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_volume: float = 0.0
    max_drawdown: float = 0.0
    peak_equity: float = 0.0
    current_equity: float = 0.0


class RiskEngine:
    """
    Production-grade risk management engine.
    
    Features:
    - Pre-trade risk checks
    - Position sizing calculation
    - Drawdown protection
    - Kill switch mechanism
    - Real-time monitoring
    """
    
    def __init__(self, config: RiskConfig = None, account_id: str = "default"):
        self.config = config or RiskConfig()
        self.account_id = account_id
        
        # State
        self.kill_switch_active = False
        self.current_equity = 0.0
        self.peak_equity = 0.0
        self.initial_equity = 0.0
        
        # Metrics
        self.daily_metrics: Dict[str, TradeMetrics] = {}
        self.weekly_metrics: Dict[str, TradeMetrics] = {}
        
        # Position tracking
        self.open_positions: Dict[str, Dict] = {}
        
        # Callbacks
        self._risk_callbacks: List[Callable] = []
        self._kill_switch_callbacks: List[Callable] = []
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        logger.info(f"RiskEngine initialized for account {account_id}")
    
    def initialize_equity(self, equity: float):
        """Initialize equity tracking."""
        with self._lock:
            self.initial_equity = equity
            self.current_equity = equity
            self.peak_equity = equity
            logger.info(f"Equity initialized: ${equity:,.2f}")
    
    def update_equity(self, equity: float):
        """Update current equity and check drawdown."""
        with self._lock:
            self.current_equity = equity
            
            if equity > self.peak_equity:
                self.peak_equity = equity
            
            # Check drawdown
            if self.config.drawdown_protection_enabled:
                drawdown = self._calculate_drawdown()
                
                if drawdown >= self.config.max_drawdown:
                    self._trigger_kill_switch(
                        f"Max drawdown exceeded: {drawdown:.2f}% >= {self.config.max_drawdown}%"
                    )
                
                if drawdown >= self.config.kill_switch_loss_threshold:
                    logger.warning(f"Drawdown warning: {drawdown:.2f}%")
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage."""
        if self.peak_equity <= 0:
            return 0.0
        return ((self.peak_equity - self.current_equity) / self.peak_equity) * 100
    
    def check_trade_risk(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float,
        stop_loss: float = None,
        leverage: int = 1,
        account_balance: float = None
    ) -> RiskCheckResult:
        """
        Comprehensive pre-trade risk check.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            quantity: Position size
            price: Entry price
            stop_loss: Stop loss price
            leverage: Position leverage
            account_balance: Current account balance
            
        Returns:
            RiskCheckResult with pass/fail and any violations
        """
        result = RiskCheckResult(passed=True, risk_level=RiskLevel.LOW)
        
        balance = account_balance or self.current_equity or 10000.0
        position_value = quantity * price
        
        # 1. Kill switch check
        if self.kill_switch_active:
            result.add_violation(
                RiskViolationType.KILL_SWITCH,
                "Kill switch is active. All trading suspended."
            )
            result.risk_level = RiskLevel.CRITICAL
            return result
        
        # 2. Position size check
        position_pct = (position_value / balance) * 100
        if position_pct > self.config.max_position_size:
            result.add_violation(
                RiskViolationType.MAX_POSITION_SIZE,
                f"Position size {position_pct:.1f}% exceeds max {self.config.max_position_size}%"
            )
            result.adjusted_position_size = (self.config.max_position_size / 100) * balance / price
        
        # 3. Leverage check
        if leverage > self.config.max_leverage:
            result.add_violation(
                RiskViolationType.LEVERAGE_EXCEEDED,
                f"Leverage {leverage}x exceeds max {self.config.max_leverage}x"
            )
        
        # 4. Risk per trade check
        if stop_loss:
            risk_per_trade_pct = self._calculate_risk_percentage(
                price, stop_loss, quantity, balance, side
            )
            
            if risk_per_trade_pct > self.config.max_risk_per_trade:
                result.add_violation(
                    RiskViolationType.MAX_POSITION_SIZE,
                    f"Risk per trade {risk_per_trade_pct:.2f}% exceeds max {self.config.max_risk_per_trade}%"
                )
                result.risk_level = RiskLevel.HIGH
        
        # 5. Concurrent positions check
        with self._lock:
            if len(self.open_positions) >= self.config.max_open_positions:
                result.add_violation(
                    RiskViolationType.CONCURRENT_POSITIONS,
                    f"Max open positions ({self.config.max_open_positions}) reached"
                )
        
        # 6. Daily loss check
        daily_metrics = self._get_daily_metrics()
        if daily_metrics:
            daily_loss_pct = abs(min(0, daily_metrics.total_pnl)) / balance * 100
            if daily_loss_pct >= self.config.max_daily_loss:
                result.add_violation(
                    RiskViolationType.MAX_DAILY_LOSS,
                    f"Daily loss {daily_loss_pct:.2f}% exceeds max {self.config.max_daily_loss}%"
                )
                result.risk_level = RiskLevel.HIGH
        
        # 7. Time restriction check
        if self.config.time_restrictions_enabled:
            if not self._check_trading_hours():
                result.add_violation(
                    RiskViolationType.TIME_RESTRICTION,
                    "Trading outside allowed hours"
                )
        
        # 8. Drawdown check
        current_drawdown = self._calculate_drawdown()
        if current_drawdown >= self.config.max_drawdown * 0.8:  # 80% of max
            result.risk_level = RiskLevel.HIGH
            result.messages.append(f"Warning: Near max drawdown ({current_drawdown:.1f}%)")
        
        # Set final risk level
        if len(result.violations) > 0:
            result.passed = False
            if result.risk_level == RiskLevel.LOW:
                result.risk_level = RiskLevel.MEDIUM
        
        return result
    
    def _calculate_risk_percentage(
        self,
        entry_price: float,
        stop_loss: float,
        quantity: float,
        balance: float,
        side: str
    ) -> float:
        """Calculate risk percentage for a trade."""
        if side.lower() == 'buy':
            risk_per_unit = entry_price - stop_loss
        else:
            risk_per_unit = stop_loss - entry_price
        
        total_risk = abs(risk_per_unit * quantity)
        return (total_risk / balance) * 100
    
    def _get_daily_metrics(self) -> Optional[TradeMetrics]:
        """Get today's trading metrics."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_metrics.get(today)
    
    def _check_trading_hours(self) -> bool:
        """Check if current time is within allowed trading hours."""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        for time_range in self.config.allowed_trading_hours:
            try:
                start, end = time_range.split("-")
                if start <= current_time <= end:
                    return True
            except:
                continue
        
        return False
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        risk_percentage: float = None
    ) -> Dict:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_percentage: Risk per trade (default from config)
            
        Returns:
            Dict with position sizing details
        """
        risk_pct = risk_percentage or self.config.max_risk_per_trade
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit <= 0:
            return {
                'position_size': 0,
                'position_value': 0,
                'risk_amount': 0,
                'risk_percentage': 0,
                'error': 'Invalid stop loss'
            }
        
        # Calculate max risk amount
        max_risk_amount = account_balance * (risk_pct / 100)
        
        # Calculate position size
        position_size = max_risk_amount / risk_per_unit
        position_value = position_size * entry_price
        
        # Check against max position size
        max_position_value = account_balance * (self.config.max_position_size / 100)
        if position_value > max_position_value:
            position_size = max_position_value / entry_price
            position_value = max_position_value
        
        return {
            'position_size': round(position_size, 8),
            'position_value': round(position_value, 2),
            'risk_amount': round(position_size * risk_per_unit, 2),
            'risk_percentage': risk_pct,
            'risk_reward_at_2r': round(entry_price + (2 * risk_per_unit), 4)
        }
    
    def record_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        pnl: float
    ):
        """Record a completed trade for metrics."""
        with self._lock:
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today not in self.daily_metrics:
                self.daily_metrics[today] = TradeMetrics(date=datetime.now())
            
            metrics = self.daily_metrics[today]
            metrics.total_trades += 1
            metrics.total_pnl += pnl
            metrics.total_volume += quantity * entry_price
            
            if pnl > 0:
                metrics.winning_trades += 1
            else:
                metrics.losing_trades += 1
            
            # Update equity
            self.current_equity += pnl
            self.update_equity(self.current_equity)
    
    def add_position(self, position_id: str, position_data: Dict):
        """Track an open position."""
        with self._lock:
            self.open_positions[position_id] = position_data
    
    def remove_position(self, position_id: str):
        """Remove a closed position."""
        with self._lock:
            self.open_positions.pop(position_id, None)
    
    def _trigger_kill_switch(self, reason: str):
        """Activate kill switch."""
        with self._lock:
            if not self.kill_switch_active:
                self.kill_switch_active = True
                logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
                
                # Notify callbacks
                for callback in self._kill_switch_callbacks:
                    try:
                        callback(reason)
                    except Exception as e:
                        logger.error(f"Kill switch callback error: {e}")
    
    def deactivate_kill_switch(self, confirmation_code: str = None):
        """Deactivate kill switch (requires confirmation)."""
        # In production, require proper confirmation
        if confirmation_code == "CONFIRM_RESUME_TRADING":
            with self._lock:
                self.kill_switch_active = False
                logger.warning("Kill switch deactivated. Trading resumed.")
                return True
        else:
            logger.warning("Kill switch deactivation requires confirmation code")
            return False
    
    def on_risk_event(self, callback: Callable):
        """Register risk event callback."""
        self._risk_callbacks.append(callback)
    
    def on_kill_switch(self, callback: Callable):
        """Register kill switch callback."""
        self._kill_switch_callbacks.append(callback)
    
    def get_risk_summary(self) -> Dict:
        """Get current risk status summary."""
        daily = self._get_daily_metrics()
        
        return {
            'kill_switch_active': self.kill_switch_active,
            'current_equity': self.current_equity,
            'peak_equity': self.peak_equity,
            'current_drawdown': self._calculate_drawdown(),
            'max_drawdown_threshold': self.config.max_drawdown,
            'open_positions': len(self.open_positions),
            'max_positions': self.config.max_open_positions,
            'daily_pnl': daily.total_pnl if daily else 0,
            'daily_trades': daily.total_trades if daily else 0,
            'max_daily_loss': self.config.max_daily_loss,
            'max_leverage': self.config.max_leverage,
            'risk_level': self._get_overall_risk_level().value
        }
    
    def _get_overall_risk_level(self) -> RiskLevel:
        """Calculate overall risk level."""
        if self.kill_switch_active:
            return RiskLevel.CRITICAL
        
        drawdown = self._calculate_drawdown()
        
        if drawdown >= self.config.max_drawdown * 0.8:
            return RiskLevel.HIGH
        elif drawdown >= self.config.max_drawdown * 0.5:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW


# Global risk engine instance
_risk_engines: Dict[str, RiskEngine] = {}


def get_risk_engine(account_id: str = "default", config: RiskConfig = None) -> RiskEngine:
    """Get or create risk engine for account."""
    if account_id not in _risk_engines:
        _risk_engines[account_id] = RiskEngine(config, account_id)
    return _risk_engines[account_id]


if __name__ == "__main__":
    # Test risk engine
    config = RiskConfig(
        max_risk_per_trade=2.0,
        max_position_size=10.0,
        max_daily_loss=5.0,
        max_drawdown=20.0
    )
    
    engine = RiskEngine(config)
    engine.initialize_equity(10000)
    
    # Test position sizing
    sizing = engine.calculate_position_size(
        account_balance=10000,
        entry_price=100,
        stop_loss=95
    )
    print("Position Sizing:", json.dumps(sizing, indent=2))
    
    # Test risk check
    result = engine.check_trade_risk(
        symbol="BTC/USDT",
        side="buy",
        order_type="market",
        quantity=0.1,
        price=45000,
        stop_loss=43000,
        leverage=5.
    )
    print(f"\nRisk Check: {'PASSED' if result.passed else 'FAILED'}")
    print(f"Risk Level: {result.risk_level.value}")
    if result.violations:
        print("Violations:", [v.value for v in result.violations])
