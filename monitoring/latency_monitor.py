"""
Latency Monitor Module
Measures and tracks system latency
"""
import time
import requests
from typing import Dict, List, Optional
from loguru import logger
import numpy as np


class LatencyMonitor:
    """Tracks latency of critical components."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.api_pings = []
        self.db_pings = []
        self.feed_pings = []
        
    def record_latency(self, component: str, duration_ms: float):
        """Record a latency measurement."""
        if component == 'api':
            self.api_pings.append(duration_ms)
            if len(self.api_pings) > self.window_size:
                self.api_pings.pop(0)
        elif component == 'feed':
            self.feed_pings.append(duration_ms)
            if len(self.feed_pings) > self.window_size:
                self.feed_pings.pop(0)
                
    def check_connection(self, url: str = "https://google.com") -> Optional[float]:
        """Check internet connectivity latency."""
        try:
            start = time.perf_counter()
            requests.get(url, timeout=2)
            end = time.perf_counter()
            latency = (end - start) * 1000
            return latency
        except Exception:
            return None
            
    def get_stats(self) -> Dict:
        """Get latency statistics."""
        stats = {}
        
        for name, data in [('api', self.api_pings), ('feed', self.feed_pings)]:
            if data:
                stats[name] = {
                    'avg_ms': round(np.mean(data), 2),
                    'max_ms': round(np.max(data), 2),
                    'p95_ms': round(np.percentile(data, 95), 2),
                    'current_ms': round(data[-1], 2)
                }
            else:
                stats[name] = {'status': 'nodata'}
                
        return stats


if __name__ == "__main__":
    monitor = LatencyMonitor()
    lat = monitor.check_connection()
    if lat:
        monitor.record_latency('api', lat)
        print(monitor.get_stats())
