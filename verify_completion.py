"""
Verification Script
Verifies that all new modules can be imported without errors.
"""
import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_imports():
    logger.info("Verifying imports...")
    errors = []
    
    modules_to_test = [
        # ML
        "modules.ml.features",
        "modules.ml.models",
        "modules.ml.predictor",
        "modules.ml.trainer",
        
        # Options
        "modules.options.greeks_calculator",
        "modules.options.options_sentiment",
        "modules.options.volatility_surface",
        
        # Smith Chart
        "modules.smith.smith_chart",
        "modules.smith.impedance_mapping",
        "modules.smith.resonance_detector",
        
        # Forecasting
        "modules.forecasting.astro_cycle_projection",
        "modules.forecasting.gann_forecast_daily",
        "modules.forecasting.gann_wave_projection",
        "modules.forecasting.ml_time_forecast",
        "modules.forecasting.report_generator",
        
        # Indicators
        "indicators.Candlestick_Pattern",
        "indicators.astro_indicators",
        "indicators.ehlers_indicators",
        "indicators.gann_indicators",
        "indicators.ml_features",
        "indicators.options_greeks",
        
        # Strategies
        "strategies.trend_strategy",
        "strategies.gann_strategy",
        
        # Scanners
        "scanner.gann_scanner",
        "scanner.ehlers_scanner",
        "scanner.wave_scanner"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            logger.success(f"Successfully imported {module}")
        except Exception as e:
            logger.error(f"Failed to import {module}: {e}")
            errors.append((module, str(e)))
            
    if errors:
        logger.error(f"Verification failed with {len(errors)} errors.")
        for mod, err in errors:
            print(f"- {mod}: {err}")
    else:
        logger.success("All modules verified successfully!")

if __name__ == "__main__":
    verify_imports()
