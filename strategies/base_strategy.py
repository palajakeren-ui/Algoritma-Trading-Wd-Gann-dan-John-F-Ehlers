"""
Base Strategy Module
Abstract base class for trading strategies
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from loguru import logger


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = self.config.get('name', 'UnnamedStrategy')
        self.symbols = self.config.get('symbols', ['BTC-USD'])
        self.params = self.config.get('params', {})
        logger.info(f"Strategy {self.name} initialized")
    
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Generate trading signals based on market data.
        
        Args:
            data: Dictionary mapping symbols to DataFrames
            
        Returns:
            List of signal dictionaries:
            {
                'symbol': str,
                'timestamp': datetime,
                'type': 'BUY'|'SELL'|'EXIT',
                'confidence': float,
                'reason': str
            }
        """
        pass
    
    def validate_data(self, df: pd.DataFrame, min_length: int = 50) -> bool:
        """Check if data is sufficient for strategy."""
        if df is None or df.empty:
            return False
        if len(df) < min_length:
            return False
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return False
        return True
    
    def calculate_position_size(self, signal: Dict, portfolio_value: float) -> float:
        """Calculate position size (can be overridden)."""
        risk_pct = self.params.get('risk_per_trade', 0.02)
        return portfolio_value * risk_pct
