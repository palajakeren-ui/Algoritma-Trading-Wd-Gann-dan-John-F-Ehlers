"""
Logger Module
Centralized logging configuration
"""
import sys
from loguru import logger
from typing import Optional
from datetime import datetime


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days"
):
    """
    Configure the logger.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        rotation: Log rotation size
        retention: Log retention period
    """
    # Remove default logger
    logger.remove()
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # File handler if specified
    if log_file:
        logger.add(
            log_file,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    logger.info(f"Logger configured with level={level}")


def get_logger(name: str = None):
    """Get a logger instance"""
    return logger.bind(name=name) if name else logger


class TradingLogger:
    """
    Specialized logger for trading operations.
    """
    
    def __init__(self, name: str = "trading"):
        self.name = name
        self.trade_log = []
    
    def log_trade(self, trade_data: dict):
        """Log a trade execution"""
        trade_data['timestamp'] = datetime.now().isoformat()
        self.trade_log.append(trade_data)
        logger.info(f"TRADE: {trade_data}")
    
    def log_signal(self, signal_data: dict):
        """Log a trading signal"""
        logger.info(f"SIGNAL: {signal_data}")
    
    def log_order(self, order_data: dict):
        """Log an order"""
        logger.info(f"ORDER: {order_data}")
    
    def log_error(self, error_msg: str, exception: Exception = None):
        """Log an error"""
        if exception:
            logger.error(f"ERROR: {error_msg} - {str(exception)}")
        else:
            logger.error(f"ERROR: {error_msg}")
    
    def log_performance(self, metrics: dict):
        """Log performance metrics"""
        logger.info(f"PERFORMANCE: {metrics}")
    
    def get_trade_history(self):
        """Get trade log history"""
        return self.trade_log


# Initialize default logger
setup_logger()
