"""
Slippage Model
Volume-aware, volatility-aware slippage estimation and monitoring.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque


@dataclass
class SlippageRecord:
    """Record of slippage for a single order."""
    order_id: str
    symbol: str
    side: str
    expected_price: float
    actual_price: float
    slippage_bps: float  # Basis points
    volume: float
    volatility: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SlippageModel:
    """
    Estimates and monitors execution slippage.
    
    Models:
    1. Fixed percentage (naive)
    2. Volume-dependent (sqrt market impact)
    3. Volatility-adjusted
    4. Historical calibrated (learns from actual fills)
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.base_slippage_bps = config.get("base_slippage_bps", 5.0)  # 0.05%
        self.volume_impact_factor = config.get("volume_impact_factor", 0.1)
        self.volatility_factor = config.get("volatility_factor", 0.5)
        
        # Historical tracking
        self._records: deque = deque(maxlen=10000)
        self._symbol_stats: Dict[str, Dict] = {}
    
    def estimate_slippage(
        self,
        price: float,
        side: str,
        quantity: float,
        avg_volume: float = None,
        current_volatility: float = None,
        order_book_depth: float = None,
    ) -> float:
        """
        Estimate slippage for an order.
        
        Returns:
            Expected slippage in price units.
        """
        slippage_bps = self.base_slippage_bps
        
        # Volume impact (square root model - Almgren-Chriss)
        if avg_volume and avg_volume > 0:
            participation_rate = quantity / avg_volume
            volume_impact = self.volume_impact_factor * np.sqrt(participation_rate) * 10000
            slippage_bps += volume_impact
        
        # Volatility adjustment
        if current_volatility and current_volatility > 0:
            vol_adjustment = self.volatility_factor * current_volatility * 10000
            slippage_bps += vol_adjustment
        
        # Order book depth (if available)
        if order_book_depth and order_book_depth > 0:
            depth_ratio = quantity * price / order_book_depth
            if depth_ratio > 0.1:  # Order > 10% of visible depth
                slippage_bps *= (1 + depth_ratio)
        
        slippage_price = price * (slippage_bps / 10000)
        
        # Direction: buy = positive slippage, sell = negative
        if side.upper() in ("BUY", "LONG"):
            return slippage_price
        else:
            return -slippage_price
    
    def record_actual_slippage(
        self,
        order_id: str,
        symbol: str,
        side: str,
        expected_price: float,
        actual_price: float,
        volume: float = 0,
        volatility: float = 0,
    ):
        """Record actual slippage from a filled order."""
        if expected_price <= 0:
            return
        
        slippage_price = actual_price - expected_price
        slippage_bps = (slippage_price / expected_price) * 10000
        
        record = SlippageRecord(
            order_id=order_id,
            symbol=symbol,
            side=side,
            expected_price=expected_price,
            actual_price=actual_price,
            slippage_bps=slippage_bps,
            volume=volume,
            volatility=volatility,
        )
        self._records.append(record)
        
        # Update symbol stats
        if symbol not in self._symbol_stats:
            self._symbol_stats[symbol] = {
                "total_records": 0,
                "mean_slippage_bps": 0.0,
                "max_slippage_bps": 0.0,
                "sum_slippage_bps": 0.0,
            }
        
        stats = self._symbol_stats[symbol]
        stats["total_records"] += 1
        stats["sum_slippage_bps"] += abs(slippage_bps)
        stats["mean_slippage_bps"] = stats["sum_slippage_bps"] / stats["total_records"]
        stats["max_slippage_bps"] = max(stats["max_slippage_bps"], abs(slippage_bps))
        
        if abs(slippage_bps) > 50:  # >0.5% slippage
            logger.warning(
                f"HIGH SLIPPAGE on {symbol}: {slippage_bps:.1f}bps "
                f"(expected={expected_price:.4f}, actual={actual_price:.4f})"
            )
    
    def get_stats(self, symbol: str = None) -> Dict:
        """Get slippage statistics."""
        if symbol and symbol in self._symbol_stats:
            return self._symbol_stats[symbol]
        
        if not self._records:
            return {"total_records": 0, "mean_slippage_bps": 0.0}
        
        all_bps = [abs(r.slippage_bps) for r in self._records]
        return {
            "total_records": len(self._records),
            "mean_slippage_bps": round(np.mean(all_bps), 2),
            "median_slippage_bps": round(np.median(all_bps), 2),
            "p95_slippage_bps": round(np.percentile(all_bps, 95), 2),
            "max_slippage_bps": round(max(all_bps), 2),
            "per_symbol": {k: v for k, v in self._symbol_stats.items()},
        }
