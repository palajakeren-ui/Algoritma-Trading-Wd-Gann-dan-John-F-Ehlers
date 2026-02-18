"""
Volatility-Based Position Sizer
Institutional position sizing using multiple methodologies.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from loguru import logger


class PositionSizer:
    """
    Calculates position size using institutional methodologies:
    
    1. Fixed Fractional - Risk X% per trade
    2. Kelly Criterion - Optimal geometric growth
    3. Volatility-Adjusted - ATR-based sizing
    4. CVaR-Based - Size based on tail risk
    5. Equal Risk Contribution - Equal vol per position
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.default_method = config.get("method", "fixed_fractional")
        self.max_position_pct = config.get("max_position_pct", 10.0)
        self.default_risk_pct = config.get("default_risk_pct", 1.0)
        self.kelly_fraction = config.get("kelly_fraction", 0.25)  # Quarter Kelly
    
    def calculate(
        self,
        method: str = None,
        account_balance: float = 100000.0,
        entry_price: float = 0.0,
        stop_loss: float = 0.0,
        risk_pct: float = None,
        win_rate: float = None,
        avg_win: float = None,
        avg_loss: float = None,
        atr: float = None,
        volatility: float = None,
        cvar_95: float = None,
        drawdown_multiplier: float = 1.0,
    ) -> Dict:
        """
        Calculate position size.
        
        Returns:
            Dict with position_size, risk_amount, method used
        """
        method = method or self.default_method
        risk_pct = risk_pct or self.default_risk_pct
        
        if method == "fixed_fractional":
            size = self._fixed_fractional(account_balance, entry_price, stop_loss, risk_pct)
        elif method == "kelly":
            size = self._kelly(account_balance, entry_price, win_rate, avg_win, avg_loss)
        elif method == "volatility":
            size = self._volatility_adjusted(account_balance, entry_price, atr, risk_pct)
        elif method == "cvar":
            size = self._cvar_based(account_balance, entry_price, cvar_95, risk_pct)
        else:
            size = self._fixed_fractional(account_balance, entry_price, stop_loss, risk_pct)
        
        # Apply drawdown multiplier
        size *= drawdown_multiplier
        
        # Cap at max position size
        max_size = (account_balance * self.max_position_pct / 100) / max(entry_price, 0.001)
        size = min(size, max_size)
        
        # Ensure non-negative
        size = max(0.0, size)
        
        risk_amount = self._calculate_risk_amount(size, entry_price, stop_loss)
        
        result = {
            "position_size": round(size, 8),
            "position_value": round(size * entry_price, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_pct_actual": round(risk_amount / max(account_balance, 1) * 100, 2),
            "method": method,
            "drawdown_multiplier": drawdown_multiplier,
        }
        
        logger.debug(f"Position size: {result['position_size']} ({method}), "
                      f"risk: ${result['risk_amount']:.2f} ({result['risk_pct_actual']:.2f}%)")
        
        return result
    
    def _fixed_fractional(
        self, balance: float, entry: float, stop: float, risk_pct: float
    ) -> float:
        """Fixed fractional: Risk X% of account per trade."""
        if entry <= 0 or stop <= 0:
            return 0.0
        
        risk_amount = balance * (risk_pct / 100)
        risk_per_unit = abs(entry - stop)
        
        if risk_per_unit <= 0:
            return 0.0
        
        return risk_amount / risk_per_unit
    
    def _kelly(
        self, balance: float, entry: float,
        win_rate: float = None, avg_win: float = None, avg_loss: float = None,
    ) -> float:
        """Kelly Criterion: Optimal growth rate position sizing."""
        if win_rate is None or avg_win is None or avg_loss is None:
            logger.warning("Kelly: Missing stats, falling back to fixed fractional")
            return self._fixed_fractional(balance, entry, entry * 0.98, 1.0)
        
        if avg_loss == 0:
            return 0.0
        
        # Kelly fraction: f = (p*b - q) / b
        # where p = win_rate, q = 1-p, b = avg_win/avg_loss
        p = win_rate
        q = 1 - p
        b = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        if b == 0:
            return 0.0
        
        kelly = (p * b - q) / b
        
        # Use fraction of Kelly (safer)
        kelly *= self.kelly_fraction
        
        # Cap at reasonable size
        kelly = max(0.0, min(kelly, 0.25))
        
        position_value = balance * kelly
        if entry > 0:
            return position_value / entry
        return 0.0
    
    def _volatility_adjusted(
        self, balance: float, entry: float, atr: float = None, risk_pct: float = 1.0,
    ) -> float:
        """Volatility-adjusted: Size inversely proportional to ATR."""
        if atr is None or atr <= 0:
            return self._fixed_fractional(balance, entry, entry * 0.98, risk_pct)
        
        risk_amount = balance * (risk_pct / 100)
        # Use 2×ATR as risk distance
        risk_per_unit = 2.0 * atr
        
        if risk_per_unit <= 0:
            return 0.0
        
        return risk_amount / risk_per_unit
    
    def _cvar_based(
        self, balance: float, entry: float, cvar_95: float = None, risk_pct: float = 1.0,
    ) -> float:
        """CVaR-based: Size based on expected tail loss."""
        if cvar_95 is None or cvar_95 == 0:
            return self._fixed_fractional(balance, entry, entry * 0.98, risk_pct)
        
        risk_amount = balance * (risk_pct / 100)
        # cvar_95 is already a percentage of portfolio
        expected_tail_loss_per_unit = abs(cvar_95) * entry
        
        if expected_tail_loss_per_unit <= 0:
            return 0.0
        
        return risk_amount / expected_tail_loss_per_unit
    
    @staticmethod
    def _calculate_risk_amount(size: float, entry: float, stop: float) -> float:
        """Calculate dollar risk for position."""
        if stop <= 0 or entry <= 0:
            return size * entry * 0.02  # Assume 2% risk if no stop
        return abs(entry - stop) * size
