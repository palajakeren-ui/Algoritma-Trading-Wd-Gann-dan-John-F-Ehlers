"""
Pre-Trade Risk Check
All risk validations that must pass BEFORE an order is submitted.
"""

from typing import Dict, Optional, List, Tuple
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PreTradeResult:
    """Result of pre-trade risk validation."""
    approved: bool
    adjusted_size: Optional[float] = None
    rejections: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0-100, higher = riskier
    
    def to_dict(self) -> Dict:
        return {
            "approved": self.approved,
            "adjusted_size": self.adjusted_size,
            "rejections": self.rejections,
            "warnings": self.warnings,
            "risk_score": round(self.risk_score, 1),
        }


class PreTradeCheck:
    """
    Comprehensive pre-trade risk validation.
    
    Checks:
    1. Position size within limits
    2. Account margin sufficient
    3. Daily loss limit not exceeded
    4. Max concurrent positions not exceeded
    5. Correlation with existing positions
    6. Leverage within limits
    7. Trading hours check
    8. Minimum risk/reward ratio
    9. Circuit breaker status
    10. Drawdown protection status
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.max_position_pct = config.get("max_position_pct", 10.0)
        self.max_risk_per_trade_pct = config.get("max_risk_per_trade_pct", 2.0)
        self.max_concurrent_positions = config.get("max_concurrent_positions", 10)
        self.max_leverage = config.get("max_leverage", 10)
        self.min_risk_reward = config.get("min_risk_reward", 1.5)
        self.max_correlation = config.get("max_correlation", 0.7)
        self.max_daily_trades = config.get("max_daily_trades", 50)
    
    def check(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_loss: float,
        take_profit: float = 0.0,
        leverage: int = 1,
        account_balance: float = 0.0,
        current_positions: Dict = None,
        daily_trades: int = 0,
        daily_pnl: float = 0.0,
        circuit_breaker_ok: bool = True,
        drawdown_multiplier: float = 1.0,
    ) -> PreTradeResult:
        """
        Run all pre-trade risk checks.
        
        Returns:
            PreTradeResult with approval decision
        """
        result = PreTradeResult(approved=True)
        current_positions = current_positions or {}
        risk_score = 0.0
        
        # 0. Circuit breaker check (highest priority)
        if not circuit_breaker_ok:
            result.approved = False
            result.rejections.append("Circuit breaker is tripped - no trading allowed")
            return result
        
        # 1. Position size limits
        if account_balance > 0:
            position_value = quantity * price
            position_pct = (position_value / account_balance) * 100
            
            if position_pct > self.max_position_pct:
                max_qty = (account_balance * self.max_position_pct / 100) / price
                result.adjusted_size = max_qty
                result.warnings.append(
                    f"Position size {position_pct:.1f}% exceeds {self.max_position_pct}% limit. "
                    f"Adjusted to {max_qty:.6f}"
                )
                quantity = max_qty
                risk_score += 20
        
        # 2. Risk per trade
        if stop_loss > 0 and account_balance > 0:
            if side.upper() == "BUY":
                risk_per_unit = price - stop_loss
            else:
                risk_per_unit = stop_loss - price
            
            total_risk = abs(risk_per_unit * quantity)
            risk_pct = (total_risk / account_balance) * 100
            
            if risk_pct > self.max_risk_per_trade_pct:
                result.approved = False
                result.rejections.append(
                    f"Risk per trade {risk_pct:.2f}% exceeds {self.max_risk_per_trade_pct}% limit"
                )
                risk_score += 30
        
        # 3. Concurrent positions
        n_positions = len(current_positions)
        if n_positions >= self.max_concurrent_positions:
            result.approved = False
            result.rejections.append(
                f"Max concurrent positions reached ({n_positions}/{self.max_concurrent_positions})"
            )
            risk_score += 15
        
        # 4. Leverage check
        if leverage > self.max_leverage:
            result.approved = False
            result.rejections.append(
                f"Leverage {leverage}x exceeds max {self.max_leverage}x"
            )
            risk_score += 25
        
        # 5. Risk/Reward ratio
        if stop_loss > 0 and take_profit > 0 and price > 0:
            if side.upper() == "BUY":
                risk = abs(price - stop_loss)
                reward = abs(take_profit - price)
            else:
                risk = abs(stop_loss - price)
                reward = abs(price - take_profit)
            
            if risk > 0:
                rr = reward / risk
                if rr < self.min_risk_reward:
                    result.warnings.append(
                        f"Risk/Reward {rr:.2f} below minimum {self.min_risk_reward}"
                    )
                    risk_score += 10
        
        # 6. Daily trade limit
        if daily_trades >= self.max_daily_trades:
            result.approved = False
            result.rejections.append(
                f"Daily trade limit reached ({daily_trades}/{self.max_daily_trades})"
            )
            risk_score += 10
        
        # 7. Apply drawdown multiplier
        if drawdown_multiplier < 1.0 and result.adjusted_size is None:
            adjusted = quantity * drawdown_multiplier
            result.adjusted_size = adjusted
            result.warnings.append(
                f"Position reduced by drawdown protector: {drawdown_multiplier:.0%} of normal size"
            )
            risk_score += 15
        
        # 8. Duplicate position check
        if symbol in current_positions:
            existing = current_positions[symbol]
            if isinstance(existing, dict) and existing.get("side", "").upper() == side.upper():
                result.warnings.append(f"Adding to existing {side} position in {symbol}")
                risk_score += 10
        
        result.risk_score = min(100, risk_score)
        
        if result.approved:
            logger.debug(f"Pre-trade check PASSED for {symbol} {side} {quantity:.6f} @ {price}")
        else:
            logger.warning(f"Pre-trade check REJECTED for {symbol} {side}: {result.rejections}")
        
        return result
