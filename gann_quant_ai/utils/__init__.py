"""
Utils Module
Utility functions and helpers for Gann Quant AI
"""
# Simple imports that won't cause circular dependency issues
from .config_loader import load_config, load_all_configs

# Lazy imports for other modules to avoid import errors
def get_logger(name=None):
    """Get a logger instance"""
    from .logger import get_logger as _get_logger
    return _get_logger(name)

__all__ = [
    'load_config',
    'load_all_configs',
    'get_logger',
]
