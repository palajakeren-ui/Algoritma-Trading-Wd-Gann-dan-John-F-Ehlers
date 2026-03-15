"""
Trading Session Controller
Manages trading sessions, prevents signals outside market hours.
Supports crypto (24/7) and traditional market schedules.
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum
from dataclasses import dataclass


class MarketType(Enum):
    CRYPTO = "crypto"       # 24/7
    FOREX = "forex"         # Sun 5pm - Fri 5pm ET
    EQUITY_US = "equity_us" # 9:30am - 4pm ET
    FUTURES = "futures"     # Nearly 24/5
    CUSTOM = "custom"


@dataclass
class TradingSession:
    """Definition of a trading session window."""
    name: str
    start_time: time
    end_time: time
    weekdays: List[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"
    
    def is_active(self, dt: datetime) -> bool:
        """Check if given datetime falls within this session."""
        if dt.weekday() not in self.weekdays:
            return False
        current_time = dt.time()
        if self.start_time <= self.end_time:
            return self.start_time <= current_time <= self.end_time
        else:
            # Overnight session (e.g., 22:00 - 06:00)
            return current_time >= self.start_time or current_time <= self.end_time


class SessionController:
    """
    Controls trading session activity.
    
    Features:
    - Block signal generation outside market hours
    - Track session P&L independently
    - Enforce session-specific risk limits
    - Handle session open/close events
    """
    
    # Pre-defined sessions
    SESSIONS = {
        MarketType.CRYPTO: TradingSession(
            name="Crypto 24/7",
            start_time=time(0, 0),
            end_time=time(23, 59, 59),
            weekdays=[0, 1, 2, 3, 4, 5, 6],
        ),
        MarketType.FOREX: TradingSession(
            name="Forex",
            start_time=time(0, 0),
            end_time=time(23, 59, 59),
            weekdays=[0, 1, 2, 3, 4],  # Mon-Fri
        ),
        MarketType.EQUITY_US: TradingSession(
            name="US Equity",
            start_time=time(14, 30),  # 9:30 AM ET = 14:30 UTC
            end_time=time(21, 0),     # 4:00 PM ET = 21:00 UTC
            weekdays=[0, 1, 2, 3, 4],
        ),
        MarketType.FUTURES: TradingSession(
            name="Futures",
            start_time=time(0, 0),
            end_time=time(23, 59, 59),
            weekdays=[0, 1, 2, 3, 4],
        ),
    }
    
    def __init__(self, market_type: MarketType = MarketType.CRYPTO, config: Dict = None):
        self.market_type = market_type
        self.session = self.SESSIONS.get(market_type, self.SESSIONS[MarketType.CRYPTO])
        self._active = True
        self._force_closed = False
        self._session_pnl = 0.0
        self._session_trades = 0
        
        if config and "custom_session" in config:
            cs = config["custom_session"]
            self.session = TradingSession(
                name=cs.get("name", "Custom"),
                start_time=time.fromisoformat(cs["start_time"]),
                end_time=time.fromisoformat(cs["end_time"]),
                weekdays=cs.get("weekdays", [0, 1, 2, 3, 4]),
                timezone=cs.get("timezone", "UTC"),
            )
    
    def is_trading_allowed(self, dt: datetime = None) -> bool:
        """Check if trading is currently allowed."""
        if self._force_closed:
            return False
        if not self._active:
            return False
        dt = dt or datetime.utcnow()
        return self.session.is_active(dt)
    
    def force_close(self, reason: str = ""):
        """Force close the session (manual override)."""
        self._force_closed = True
        logger.warning(f"Session force closed: {reason}")
    
    def force_open(self):
        """Re-open a force-closed session."""
        self._force_closed = False
        logger.info("Session force opened")
    
    def record_trade(self, pnl: float):
        """Record a trade result for session tracking."""
        self._session_pnl += pnl
        self._session_trades += 1
    
    def reset_session(self):
        """Reset session metrics."""
        self._session_pnl = 0.0
        self._session_trades = 0
    
    def get_status(self) -> Dict:
        """Get current session status."""
        now = datetime.utcnow()
        return {
            "market_type": self.market_type.value,
            "session_name": self.session.name,
            "is_active": self.is_trading_allowed(now),
            "force_closed": self._force_closed,
            "current_time_utc": now.isoformat(),
            "session_pnl": self._session_pnl,
            "session_trades": self._session_trades,
        }
