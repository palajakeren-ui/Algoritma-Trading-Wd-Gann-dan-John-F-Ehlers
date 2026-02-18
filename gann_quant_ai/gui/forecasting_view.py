"""
Forecasting View Module
Interface for price forecasting visualization
"""
from loguru import logger

class ForecastingView:
    """View for Forecasts."""
    def __init__(self):
        logger.info("GUI: ForecastingView initialized")
        
    def display_forecast(self, forecast_data):
        print("Displaying forecast chart...")
