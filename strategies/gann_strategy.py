"""
Gann Strategy
Strategy based on Gann angles and Square of 9
"""
import pandas as pd
from typing import Dict, List
from .base_strategy import BaseStrategy
from indicators.gann_indicators import square_of_nine
from loguru import logger


class GannStrategy(BaseStrategy):
    """Trading strategy based on Gann principles."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.tolerance = self.params.get('tolerance', 0.01) # 1%
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Dict]:
        signals = []
        
        for symbol, df in data.items():
            if not self.validate_data(df):
                continue
            
            current_price = float(df['close'].iloc[-1])
            prev_price = float(df['close'].iloc[-2])
            
            # Get key levels
            levels = square_of_nine(current_price)
            
            # Check for bounce off support or rejection at resistance
            nearest_level = min(levels, key=lambda x: abs(x - current_price))
            pct_diff = abs(current_price - nearest_level) / nearest_level
            
            if pct_diff <= self.tolerance:
                # Potential interaction
                
                # Check for bounce (Bullish)
                # If we were above, dipped near, and are now moving up
                if current_price > nearest_level and current_price > prev_price:
                    signals.append({
                        'symbol': symbol,
                        'timestamp': df.index[-1],
                        'type': 'BUY',
                        'confidence': 0.6,
                        'reason': f"Bounce off Gann level {nearest_level:.2f}"
                    })
                    
                # Check for rejection (Bearish)
                # If we were below, rallied near, and are now moving down
                elif current_price < nearest_level and current_price < prev_price:
                    signals.append({
                        'symbol': symbol,
                        'timestamp': df.index[-1],
                        'type': 'SELL',
                        'confidence': 0.6,
                        'reason': f"Rejection at Gann level {nearest_level:.2f}"
                    })
                    
        return signals
