"""
Mode Controller
Controls trading mode: PAPER, LIVE_DRY, LIVE_ARMED.
Prevents accidental live trading deployment.
"""

from enum import Enum
from typing import Dict, Optional
from loguru import logger
from datetime import datetime


class TradingMode(Enum):
    PAPER = "paper"           # Simulated orders only
    LIVE_DRY = "live_dry"     # Real data, simulated orders, logs everything
    LIVE_ARMED = "live_armed" # REAL orders — requires explicit confirmation


class ModeController:
    """
    Guards against accidental live trading.
    
    Requirements for LIVE_ARMED:
    - Explicit confirmation key
    - Circuit breaker initialized
    - Minimum paper trading duration met
    - Walk-forward validation passed
    - Capital limit set
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self._mode = TradingMode.PAPER
        self._confirmation_key = config.get("confirmation_key", "")
        self.min_paper_days = config.get("min_paper_days", 90)
        self.max_live_capital = config.get("max_live_capital", 50000)
        
        self._paper_start_date: Optional[datetime] = None
        self._wf_validation_passed = False
        self._circuit_breaker_ready = False
        
        logger.info(f"Mode controller initialized: {self._mode.value}")
    
    @property
    def mode(self) -> TradingMode:
        return self._mode
    
    @property
    def is_paper(self) -> bool:
        return self._mode == TradingMode.PAPER
    
    @property
    def is_live(self) -> bool:
        return self._mode == TradingMode.LIVE_ARMED
    
    def set_paper_mode(self):
        """Switch to paper trading."""
        self._mode = TradingMode.PAPER
        self._paper_start_date = datetime.utcnow()
        logger.info("🟢 Mode: PAPER TRADING")
    
    def set_live_dry_mode(self):
        """Switch to live dry run (real data, simulated orders)."""
        self._mode = TradingMode.LIVE_DRY
        logger.info("🟡 Mode: LIVE DRY RUN")
    
    def set_live_armed(self, confirmation_key: str, capital_limit: float = None) -> bool:
        """
        Arm the system for LIVE trading.
        
        Args:
            confirmation_key: Must match the configured key
            capital_limit: Maximum capital to deploy
            
        Returns:
            True if armed successfully
        """
        # Check confirmation key
        if confirmation_key != self._confirmation_key:
            logger.error("❌ LIVE ARMED REJECTED: Invalid confirmation key")
            return False
        
        # Check paper trading duration
        if self._paper_start_date:
            paper_days = (datetime.utcnow() - self._paper_start_date).days
            if paper_days < self.min_paper_days:
                logger.error(
                    f"❌ LIVE ARMED REJECTED: Paper trading {paper_days} days "
                    f"< required {self.min_paper_days} days"
                )
                return False
        
        # Check walk-forward
        if not self._wf_validation_passed:
            logger.error("❌ LIVE ARMED REJECTED: Walk-forward validation not passed")
            return False
        
        # Check circuit breaker
        if not self._circuit_breaker_ready:
            logger.error("❌ LIVE ARMED REJECTED: Circuit breaker not initialized")
            return False
        
        # Set capital limit
        if capital_limit:
            self.max_live_capital = capital_limit
        
        self._mode = TradingMode.LIVE_ARMED
        logger.critical(
            f"🔴 MODE: LIVE ARMED | Capital limit: ${self.max_live_capital:,.0f} | "
            f"THIS IS REAL MONEY"
        )
        return True
    
    def mark_wf_passed(self):
        """Mark walk-forward validation as passed."""
        self._wf_validation_passed = True
        logger.info("Walk-forward validation: PASSED")
    
    def mark_circuit_breaker_ready(self):
        """Mark circuit breaker as initialized."""
        self._circuit_breaker_ready = True
        logger.info("Circuit breaker: READY")
    
    def get_status(self) -> Dict:
        """Get mode controller status."""
        paper_days = 0
        if self._paper_start_date:
            paper_days = (datetime.utcnow() - self._paper_start_date).days
        
        return {
            "mode": self._mode.value,
            "is_live": self.is_live,
            "paper_trading_days": paper_days,
            "min_paper_days_required": self.min_paper_days,
            "wf_validation_passed": self._wf_validation_passed,
            "circuit_breaker_ready": self._circuit_breaker_ready,
            "max_live_capital": self.max_live_capital,
            "ready_for_live": (
                self._wf_validation_passed and
                self._circuit_breaker_ready and
                paper_days >= self.min_paper_days
            ),
        }
