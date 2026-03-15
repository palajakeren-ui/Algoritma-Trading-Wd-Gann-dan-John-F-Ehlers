"""
Risk View Module
Interface for Risk Management settings and monitor
"""
from loguru import logger

class RiskView:
    """View for Risk Management."""
    def __init__(self):
        logger.info("GUI: RiskView initialized")
        
    def update_metrics(self, metrics):
        print(f"Updating risk metrics: {metrics}")
