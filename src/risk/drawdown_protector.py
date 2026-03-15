"""
Production Drawdown Protector
Equity curve protection with multiple protection layers.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from loguru import logger
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DrawdownState:
    """Current drawdown tracking state."""
    peak_equity: float = 0.0
    current_equity: float = 0.0
    current_drawdown_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    drawdown_duration_bars: int = 0
    in_drawdown: bool = False
    locked: bool = False
    lock_reason: str = ""


class DrawdownProtector:
    """
    Multi-level equity curve protection.
    
    Levels:
    1. Warning - Log warning, reduce position sizes by 50%
    2. Caution - Reduce position sizes by 75%, notify
    3. Critical - Stop new trades, close when breakeven
    4. Lock - Close ALL positions, halt system
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.warning_dd_pct = config.get("warning_dd_pct", 5.0)
        self.caution_dd_pct = config.get("caution_dd_pct", 10.0)
        self.critical_dd_pct = config.get("critical_dd_pct", 15.0)
        self.lock_dd_pct = config.get("lock_dd_pct", 20.0)
        
        # Equity curve protection: stop if equity curve breaks below X-day MA
        self.equity_ma_period = config.get("equity_ma_period", 20)
        self.use_equity_curve_filter = config.get("use_equity_curve_filter", True)
        
        # Max drawdown duration (in bars/trades)
        self.max_dd_duration = config.get("max_dd_duration", 50)
        
        self._state = DrawdownState()
        self._equity_history: List[float] = []
    
    def update(self, equity: float) -> DrawdownState:
        """Update with current equity and return drawdown state."""
        self._equity_history.append(equity)
        self._state.current_equity = equity
        
        if equity > self._state.peak_equity:
            self._state.peak_equity = equity
            self._state.in_drawdown = False
            self._state.drawdown_duration_bars = 0
        else:
            self._state.in_drawdown = True
            self._state.drawdown_duration_bars += 1
        
        if self._state.peak_equity > 0:
            dd = (self._state.peak_equity - equity) / self._state.peak_equity * 100
            self._state.current_drawdown_pct = dd
            self._state.max_drawdown_pct = max(self._state.max_drawdown_pct, dd)
        
        # Check lock conditions
        if self._state.current_drawdown_pct >= self.lock_dd_pct:
            self._state.locked = True
            self._state.lock_reason = f"Drawdown {self._state.current_drawdown_pct:.2f}% >= lock threshold {self.lock_dd_pct}%"
            logger.critical(f"🔴 DRAWDOWN LOCK: {self._state.lock_reason}")
        
        if self._state.drawdown_duration_bars >= self.max_dd_duration:
            self._state.locked = True
            self._state.lock_reason = f"Drawdown duration {self._state.drawdown_duration_bars} bars >= max {self.max_dd_duration}"
            logger.critical(f"🔴 DRAWDOWN DURATION LOCK: {self._state.lock_reason}")
        
        return self._state
    
    def get_position_size_multiplier(self) -> float:
        """
        Get position size multiplier based on current drawdown level.
        Returns value between 0.0 (no trading) and 1.0 (full size).
        """
        dd = self._state.current_drawdown_pct
        
        if self._state.locked:
            return 0.0
        
        if dd >= self.critical_dd_pct:
            return 0.0  # No new positions
        elif dd >= self.caution_dd_pct:
            return 0.25  # 25% position size
        elif dd >= self.warning_dd_pct:
            return 0.50  # 50% position size
        
        # Equity curve filter
        if self.use_equity_curve_filter and len(self._equity_history) >= self.equity_ma_period:
            equity_ma = np.mean(self._equity_history[-self.equity_ma_period:])
            if self._state.current_equity < equity_ma:
                return 0.50  # Reduce size when equity below MA
        
        return 1.0
    
    def is_trading_allowed(self) -> bool:
        """Check if new trades are allowed."""
        if self._state.locked:
            return False
        if self._state.current_drawdown_pct >= self.critical_dd_pct:
            return False
        return True
    
    def get_level(self) -> str:
        """Get current drawdown protection level."""
        dd = self._state.current_drawdown_pct
        if self._state.locked:
            return "LOCKED"
        if dd >= self.critical_dd_pct:
            return "CRITICAL"
        if dd >= self.caution_dd_pct:
            return "CAUTION"
        if dd >= self.warning_dd_pct:
            return "WARNING"
        return "NORMAL"
    
    def reset(self, new_peak: float = None):
        """Reset drawdown protector (e.g., after admin review)."""
        self._state.locked = False
        self._state.lock_reason = ""
        self._state.drawdown_duration_bars = 0
        if new_peak is not None:
            self._state.peak_equity = new_peak
        logger.info("Drawdown protector reset")
    
    def get_status(self) -> Dict:
        return {
            "level": self.get_level(),
            "current_drawdown_pct": round(self._state.current_drawdown_pct, 2),
            "max_drawdown_pct": round(self._state.max_drawdown_pct, 2),
            "peak_equity": round(self._state.peak_equity, 2),
            "current_equity": round(self._state.current_equity, 2),
            "in_drawdown": self._state.in_drawdown,
            "drawdown_duration": self._state.drawdown_duration_bars,
            "locked": self._state.locked,
            "lock_reason": self._state.lock_reason,
            "position_size_multiplier": self.get_position_size_multiplier(),
        }
