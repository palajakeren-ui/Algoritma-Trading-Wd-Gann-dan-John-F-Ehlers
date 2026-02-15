"""
Notifier Module
Notification system for alerts and updates
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class Notifier:
    """
    Multi-channel notification system.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.channels = self.config.get('channels', [])
        self.notification_history = []
        
        logger.info("Notifier initialized")
    
    def send(self, message: str, title: str = "Alert", level: str = "info", data: Dict = None):
        """Send notification to all configured channels"""
        if not self.enabled:
            return
        
        notification = {
            'title': title,
            'message': message,
            'level': level,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.notification_history.append(notification)
        
        for channel in self.channels:
            try:
                if channel['type'] == 'telegram':
                    self._send_telegram(notification, channel)
                elif channel['type'] == 'discord':
                    self._send_discord(notification, channel)
                elif channel['type'] == 'email':
                    self._send_email(notification, channel)
                elif channel['type'] == 'webhook':
                    self._send_webhook(notification, channel)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel['type']}: {e}")
    
    def _send_telegram(self, notification: Dict, channel: Dict):
        """Send Telegram notification"""
        if not HAS_REQUESTS:
            logger.warning("requests library not installed")
            return
        
        bot_token = channel.get('bot_token')
        chat_id = channel.get('chat_id')
        
        if not bot_token or not chat_id:
            return
        
        text = f"*{notification['title']}*\n\n{notification['message']}"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram notification sent")
    
    def _send_discord(self, notification: Dict, channel: Dict):
        """Send Discord webhook notification"""
        if not HAS_REQUESTS:
            return
        
        webhook_url = channel.get('webhook_url')
        if not webhook_url:
            return
        
        color = {'info': 3447003, 'warning': 16776960, 'error': 15158332, 'success': 3066993}
        
        payload = {
            'embeds': [{
                'title': notification['title'],
                'description': notification['message'],
                'color': color.get(notification['level'], 3447003),
                'timestamp': notification['timestamp']
            }]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in [200, 204]:
            logger.info("Discord notification sent")
    
    def _send_email(self, notification: Dict, channel: Dict):
        """Send email notification"""
        # Would normally use smtplib
        logger.info(f"Email notification: {notification['title']}")
    
    def _send_webhook(self, notification: Dict, channel: Dict):
        """Send generic webhook notification"""
        if not HAS_REQUESTS:
            return
        
        url = channel.get('url')
        if not url:
            return
        
        response = requests.post(url, json=notification, timeout=10)
        logger.info(f"Webhook sent, status: {response.status_code}")
    
    def trade_alert(self, trade_data: Dict):
        """Send trade execution alert"""
        symbol = trade_data.get('symbol', 'Unknown')
        side = trade_data.get('side', 'Unknown')
        price = trade_data.get('price', 0)
        quantity = trade_data.get('quantity', 0)
        
        message = f"**{side.upper()}** {quantity} {symbol} @ ${price:,.2f}"
        self.send(message, title="Trade Executed", level="success", data=trade_data)
    
    def signal_alert(self, signal_data: Dict):
        """Send signal alert"""
        symbol = signal_data.get('symbol', 'Unknown')
        signal = signal_data.get('signal', 'Unknown')
        strength = signal_data.get('strength', 0)
        
        message = f"**{signal}** signal for {symbol}\nStrength: {strength:.0%}"
        self.send(message, title="Trading Signal", level="info", data=signal_data)
    
    def risk_alert(self, risk_data: Dict):
        """Send risk alert"""
        message = f"Risk threshold breached!\n{json.dumps(risk_data, indent=2)}"
        self.send(message, title="⚠️ Risk Alert", level="warning", data=risk_data)
    
    def error_alert(self, error_msg: str, error_data: Dict = None):
        """Send error alert"""
        self.send(error_msg, title="❌ Error", level="error", data=error_data)
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get notification history"""
        return self.notification_history[-limit:]
