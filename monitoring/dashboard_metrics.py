"""
Dashboard Metrics Module
Calculates real-time metrics for the monitoring dashboard
"""
import psutil
import time
from typing import Dict
from datetime import datetime
from loguru import logger


class SystemMonitor:
    """Monitors system resources."""
    
    @staticmethod
    def get_system_stats() -> Dict:
        """Get CPU and Memory usage."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }


class TradingMonitor:
    """Monitors active trading metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.trade_count = 0
        self.error_count = 0
        self.last_update = time.time()
        
    def record_trade(self):
        self.trade_count += 1
        self.last_update = time.time()
        
    def record_error(self):
        self.error_count += 1
        
    def get_stats(self) -> Dict:
        uptime = time.time() - self.start_time
        return {
            'uptime_seconds': int(uptime),
            'trades_session': self.trade_count,
            'errors_session': self.error_count,
            'status': 'HEALTHY' if self.error_count < 5 else 'DEGRADED'
        }


if __name__ == "__main__":
    print(SystemMonitor.get_system_stats())
