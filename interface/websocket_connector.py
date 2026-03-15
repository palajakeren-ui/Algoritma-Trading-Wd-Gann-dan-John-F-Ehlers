"""
WebSocket Connector Module
Generic WebSocket connection handler
"""
import websocket
import threading
import time
import json
from typing import Callable, Dict, Optional
from loguru import logger


class WebSocketConnector:
    """Generic WebSocket Connector."""
    
    def __init__(self, url: str, on_message: Callable[[str], None], on_error: Optional[Callable] = None):
        self.url = url
        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.ws = None
        self.thread = None
        self.running = False
        
    def _on_message(self, ws, message):
        if self.on_message_callback:
            self.on_message_callback(message)
            
    def _on_error(self, ws, error):
        logger.error(f"WebSocket Error: {error}")
        if self.on_error_callback:
            self.on_error_callback(error)
            
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket Closed")
        self.running = False
        
    def _on_open(self, ws):
        logger.info(f"WebSocket Connected to {self.url}")
        self.running = True
        
    def connect(self):
        """Start WebSocket connection in a thread."""
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()
        
    def send(self, data: Dict):
        """Send data/json."""
        if self.ws and self.running:
            self.ws.send(json.dumps(data))
        else:
            logger.warning("WebSocket not connected, cannot send.")
            
    def disconnect(self):
        """Close connection."""
        if self.ws:
            self.ws.close()
        self.running = False


if __name__ == "__main__":
    def print_msg(msg): print(msg)
    # Test with echo server
    ws = WebSocketConnector("wss://echo.websocket.org", print_msg)
    ws.connect()
    time.sleep(2)
    ws.send({"test": "hello"})
    time.sleep(2)
    ws.disconnect()
