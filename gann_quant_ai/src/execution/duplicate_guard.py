"""
Duplicate Order Prevention
Idempotency guard for order submission.
"""

import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from loguru import logger
from collections import OrderedDict


class DuplicateGuard:
    """
    Prevents duplicate order submission.
    
    Features:
    - Idempotency key generation from order parameters
    - Time-window deduplication (same signal can't trigger twice in X seconds)
    - Per-symbol cooldown periods
    - Thread-safe operation
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.dedup_window_seconds = config.get("dedup_window_seconds", 60)
        self.max_cache_size = config.get("max_cache_size", 10000)
        self.cooldown_seconds = config.get("cooldown_seconds", 10)
        
        self._order_cache: OrderedDict = OrderedDict()
        self._symbol_last_order: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def generate_idempotency_key(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float = 0.0,
        order_type: str = "market",
    ) -> str:
        """Generate a deterministic idempotency key for an order."""
        # Round price and quantity to avoid floating point differences
        key_str = f"{symbol}|{side.upper()}|{round(quantity, 8)}|{round(price, 8)}|{order_type.upper()}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def check_duplicate(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float = 0.0,
        order_type: str = "market",
        idempotency_key: str = None,
    ) -> bool:
        """
        Check if this order is a duplicate.
        
        Returns:
            True if the order IS a duplicate (should be blocked).
            False if the order is OK to submit.
        """
        with self._lock:
            now = datetime.utcnow()
            
            # Check per-symbol cooldown
            if symbol in self._symbol_last_order:
                time_since_last = (now - self._symbol_last_order[symbol]).total_seconds()
                if time_since_last < self.cooldown_seconds:
                    logger.warning(
                        f"DUPLICATE BLOCKED: {symbol} cooldown ({time_since_last:.1f}s < {self.cooldown_seconds}s)"
                    )
                    return True
            
            # Generate or use provided idempotency key
            key = idempotency_key or self.generate_idempotency_key(
                symbol, side, quantity, price, order_type
            )
            
            # Check time-window deduplication
            if key in self._order_cache:
                cached_time = self._order_cache[key]
                time_since = (now - cached_time).total_seconds()
                if time_since < self.dedup_window_seconds:
                    logger.warning(
                        f"DUPLICATE BLOCKED: {symbol} {side} (key={key[:8]}..., "
                        f"last={time_since:.1f}s ago)"
                    )
                    return True
                else:
                    # Update cache time
                    self._order_cache[key] = now
                    self._order_cache.move_to_end(key)
            else:
                self._order_cache[key] = now
            
            # Evict old entries
            self._cleanup(now)
            
            return False
    
    def record_order_sent(self, symbol: str, idempotency_key: str = None):
        """Record that an order was submitted (for cooldown tracking)."""
        with self._lock:
            self._symbol_last_order[symbol] = datetime.utcnow()
            if idempotency_key:
                self._order_cache[idempotency_key] = datetime.utcnow()
    
    def _cleanup(self, now: datetime):
        """Remove expired entries from cache."""
        cutoff = now - timedelta(seconds=self.dedup_window_seconds * 2)
        
        while self._order_cache:
            oldest_key = next(iter(self._order_cache))
            if self._order_cache[oldest_key] < cutoff:
                self._order_cache.popitem(last=False)
            else:
                break
        
        # Also cap size
        while len(self._order_cache) > self.max_cache_size:
            self._order_cache.popitem(last=False)
    
    def reset(self):
        """Reset all caches."""
        with self._lock:
            self._order_cache.clear()
            self._symbol_last_order.clear()
    
    def get_stats(self) -> Dict:
        """Get deduplication statistics."""
        return {
            "cache_size": len(self._order_cache),
            "tracked_symbols": len(self._symbol_last_order),
            "dedup_window_sec": self.dedup_window_seconds,
            "cooldown_sec": self.cooldown_seconds,
        }
