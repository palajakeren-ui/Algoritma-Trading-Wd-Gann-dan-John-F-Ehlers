"""
Gann Forecasting Module
Price and time forecasting using Gann methods
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger


class GannForecasting:
    """
    Gann-based forecasting for price and time projections.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("GannForecasting initialized")
    
    def forecast_price(
        self, 
        df: pd.DataFrame, 
        method: str = 'angle',
        periods: int = 30
    ) -> pd.DataFrame:
        """Forecast future prices using Gann methods"""
        last_price = df['close'].iloc[-1]
        last_date = df.index[-1]
        
        forecasts = []
        
        if method == 'angle':
            # 1x1 angle projection
            daily_move = last_price / 100  # 1% per unit
            
            for i in range(1, periods + 1):
                future_date = last_date + timedelta(days=i)
                
                # Project multiple angles
                angles = {
                    '1x1': last_price + (daily_move * i),
                    '2x1': last_price + (daily_move * i * 2),
                    '1x2': last_price + (daily_move * i * 0.5),
                    '1x1_down': last_price - (daily_move * i),
                }
                
                forecasts.append({
                    'date': future_date,
                    'forecast_1x1_up': angles['1x1'],
                    'forecast_2x1_up': angles['2x1'],
                    'forecast_1x2_up': angles['1x2'],
                    'forecast_1x1_down': angles['1x1_down']
                })
        
        elif method == 'cycle':
            # Cycle-based projection
            cycle_length = 30  # days
            price_range = df['high'].max() - df['low'].min()
            
            for i in range(1, periods + 1):
                future_date = last_date + timedelta(days=i)
                phase = (i % cycle_length) / cycle_length * 2 * np.pi
                
                cycle_component = np.sin(phase) * price_range * 0.1
                
                forecasts.append({
                    'date': future_date,
                    'forecast_high': last_price + cycle_component + price_range * 0.02,
                    'forecast_low': last_price + cycle_component - price_range * 0.02,
                    'forecast_mid': last_price + cycle_component
                })
        
        return pd.DataFrame(forecasts).set_index('date')
    
    def identify_turning_points(self, df: pd.DataFrame, look_ahead: int = 90) -> List[Dict]:
        """Identify potential turning points"""
        turning_points = []
        last_date = df.index[-1]
        
        # Key Gann intervals
        intervals = [7, 14, 21, 28, 30, 45, 60, 90]
        
        for days in intervals:
            if days <= look_ahead:
                tp_date = last_date + timedelta(days=days)
                turning_points.append({
                    'date': tp_date,
                    'days_ahead': days,
                    'type': 'potential_reversal',
                    'confidence': 0.7 if days in [30, 45, 90] else 0.5
                })
        
        return turning_points
    
    def calculate_price_targets(self, high: float, low: float) -> Dict[str, float]:
        """Calculate Gann price targets from range"""
        range_size = high - low
        mid = (high + low) / 2
        
        return {
            '25%_resistance': round(low + range_size * 0.25, 2),
            '50%_level': round(mid, 2),
            '75%_resistance': round(low + range_size * 0.75, 2),
            '100%_target': round(high, 2),
            '150%_extension': round(low + range_size * 1.5, 2),
            '200%_extension': round(low + range_size * 2, 2),
            '25%_support': round(high - range_size * 0.25, 2),
            '50%_support': round(mid, 2),
            '75%_support': round(high - range_size * 0.75, 2)
        }
    
    def generate_forecast_report(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive forecast report"""
        last_price = df['close'].iloc[-1]
        high = df['high'].max()
        low = df['low'].min()
        
        return {
            'current_price': last_price,
            'trend': 'bullish' if last_price > df['close'].mean() else 'bearish',
            'price_targets': self.calculate_price_targets(high, low),
            'turning_points': self.identify_turning_points(df),
            'volatility': round(df['close'].pct_change().std() * 100, 2),
            'generated_at': datetime.now().isoformat()
        }
