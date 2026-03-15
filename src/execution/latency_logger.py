"""
Execution Latency Logger
Tracks and reports on execution latency metrics.
"""

import time
import threading
from typing import Dict, Optional, List
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import numpy as np


@dataclass
class LatencyRecord:
    """Single latency measurement."""
    order_id: str
    symbol: str
    broker: str
    operation: str  # 'submit', 'cancel', 'modify'
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True


class LatencyLogger:
    """
    Tracks execution latency for all order operations.
    
    Metrics:
    - Per-broker latency (mean, median, p95, p99, max)
    - Latency trend detection (degradation alerts)
    - Broker comparison analytics
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.alert_threshold_ms = config.get("alert_threshold_ms", 1000)
        self.critical_threshold_ms = config.get("critical_threshold_ms", 5000)
        self.max_records = config.get("max_records", 50000)
        
        self._records: deque = deque(maxlen=self.max_records)
        self._broker_stats: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def start_timer(self) -> float:
        """Start a latency timer. Returns start time."""
        return time.perf_counter()
    
    def record(
        self,
        order_id: str,
        symbol: str,
        broker: str,
        operation: str,
        start_time: float,
        success: bool = True,
    ):
        """
        Record a latency measurement.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            broker: Broker name
            operation: 'submit', 'cancel', 'modify'
            start_time: From start_timer()
            success: Whether operation succeeded
        """
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        record = LatencyRecord(
            order_id=order_id,
            symbol=symbol,
            broker=broker,
            operation=operation,
            latency_ms=latency_ms,
            success=success,
        )
        
        with self._lock:
            self._records.append(record)
            self._update_broker_stats(broker, latency_ms)
        
        # Alert on high latency
        if latency_ms > self.critical_threshold_ms:
            logger.critical(
                f"🔴 CRITICAL LATENCY: {broker} {operation} {order_id}: {latency_ms:.0f}ms"
            )
        elif latency_ms > self.alert_threshold_ms:
            logger.warning(
                f"⚠️ HIGH LATENCY: {broker} {operation} {order_id}: {latency_ms:.0f}ms"
            )
        else:
            logger.debug(f"Latency: {broker} {operation} {latency_ms:.1f}ms")
    
    def _update_broker_stats(self, broker: str, latency_ms: float):
        """Update running broker statistics."""
        if broker not in self._broker_stats:
            self._broker_stats[broker] = {
                "count": 0,
                "sum": 0.0,
                "min": float('inf'),
                "max": 0.0,
                "recent_latencies": deque(maxlen=1000),
            }
        
        stats = self._broker_stats[broker]
        stats["count"] += 1
        stats["sum"] += latency_ms
        stats["min"] = min(stats["min"], latency_ms)
        stats["max"] = max(stats["max"], latency_ms)
        stats["recent_latencies"].append(latency_ms)
    
    def get_stats(self, broker: str = None) -> Dict:
        """Get latency statistics."""
        if broker and broker in self._broker_stats:
            return self._format_broker_stats(broker)
        
        result = {}
        for b in self._broker_stats:
            result[b] = self._format_broker_stats(b)
        
        return {
            "total_records": len(self._records),
            "brokers": result,
        }
    
    def _format_broker_stats(self, broker: str) -> Dict:
        """Format broker statistics."""
        stats = self._broker_stats[broker]
        latencies = list(stats["recent_latencies"])
        
        if not latencies:
            return {"count": 0}
        
        arr = np.array(latencies)
        return {
            "count": stats["count"],
            "mean_ms": round(float(np.mean(arr)), 1),
            "median_ms": round(float(np.median(arr)), 1),
            "p95_ms": round(float(np.percentile(arr, 95)), 1),
            "p99_ms": round(float(np.percentile(arr, 99)), 1),
            "min_ms": round(stats["min"], 1),
            "max_ms": round(stats["max"], 1),
            "std_ms": round(float(np.std(arr)), 1),
        }
