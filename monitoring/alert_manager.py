"""
Alert Manager Module
Handles system and trading alerts
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class AlertManager:
    """Manages system and trading alerts."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.alerts = []
        self.handlers = []
        logger.info("AlertManager initialized")
    
    def add_handler(self, handler_type: str, handler_config: Dict):
        """Add a notification handler (e.g., email, telegram)."""
        # Placeholders for actual implementations
        if handler_type == 'email':
            self.handlers.append({'type': 'email', 'config': handler_config})
        elif handler_type == 'telegram':
            self.handlers.append({'type': 'telegram', 'config': handler_config})
        elif handler_type == 'webhook':
            self.handlers.append({'type': 'webhook', 'config': handler_config})
            
    def trigger_alert(self, title: str, message: str, level: str = 'INFO', tags: List[str] = None):
        """Trigger a new alert."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'message': message,
            'level': level,
            'tags': tags or []
        }
        
        self.alerts.append(alert)
        
        # Log via Loguru
        if level == 'ERROR':
            logger.error(f"ALERT: {title} - {message}")
        elif level == 'WARNING':
            logger.warning(f"ALERT: {title} - {message}")
        else:
            logger.info(f"ALERT: {title} - {message}")
            
        # Dispatch to external handlers
        self._dispatch(alert)
        
    def _dispatch(self, alert: Dict):
        """Dispatch alert to registered handlers."""
        for handler in self.handlers:
            try:
                # Mock dispatch logic
                pass
            except Exception as e:
                logger.error(f"Failed to dispatch alert to {handler['type']}: {e}")
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts."""
        return sorted(self.alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]


# Global instance
alert_system = AlertManager()
