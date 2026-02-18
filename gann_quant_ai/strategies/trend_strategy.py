"""
Trend Following Strategy
Classic trend following using MA crossover and volatility
"""
import pandas as pd
from typing import Dict, List
from .base_strategy import BaseStrategy
from loguru import logger


class TrendFollowingStrategy(BaseStrategy):
    """Simple trend following strategy."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.fast_period = self.params.get('fast_period', 20)
        self.slow_period = self.params.get('slow_period', 50)
        self.vol_period = self.params.get('vol_period', 20)
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Dict]:
        signals = []
        
        for symbol, df in data.items():
            if not self.validate_data(df, min_length=self.slow_period + 1):
                continue
                
            # Calculate indicators
            df['fast_ma'] = df['close'].rolling(self.fast_period).mean()
            df['slow_ma'] = df['close'].rolling(self.slow_period).mean()
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Crossover logic
            # Bullish: Fast crosses above Slow
            if prev['fast_ma'] <= prev['slow_ma'] and curr['fast_ma'] > curr['slow_ma']:
                signals.append({
                    'symbol': symbol,
                    'timestamp': curr.name,
                    'type': 'BUY',
                    'confidence': 0.7,
                    'reason': f"MA Crossover {self.fast_period}/{self.slow_period}"
                })
                
            # Bearish: Fast crosses below Slow
            elif prev['fast_ma'] >= prev['slow_ma'] and curr['fast_ma'] < curr['slow_ma']:
                signals.append({
                    'symbol': symbol,
                    'timestamp': curr.name,
                    'type': 'SELL',
                    'confidence': 0.7,
                    'reason': f"MA Crossover {self.fast_period}/{self.slow_period}"
                })
                
        return signals
