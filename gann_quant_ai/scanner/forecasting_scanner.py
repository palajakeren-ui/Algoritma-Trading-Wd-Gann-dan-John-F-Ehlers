"""
Forecasting Scanner Module
Scans for forecasting opportunities
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class ForecastingScanner:
    """
    Scanner for price forecasting opportunities.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("ForecastingScanner initialized")
    
    def scan(self, df: pd.DataFrame, symbol: str = '') -> List[Dict]:
        """Scan for forecasting signals"""
        results = []
        
        # Trend analysis
        trend = self._analyze_trend(df)
        if trend['strength'] > 0.6:
            results.append({
                'type': 'trend_forecast',
                'symbol': symbol,
                'direction': trend['direction'],
                'strength': trend['strength'],
                'target': trend['target'],
                'timeframe': '1-5 days'
            })
        
        # Cycle analysis
        cycles = self._analyze_cycles(df)
        for cycle in cycles:
            results.append({
                'type': 'cycle_forecast',
                'symbol': symbol,
                **cycle
            })
        
        # Reversal points
        reversals = self._find_reversal_signals(df)
        for rev in reversals:
            results.append({
                'type': 'reversal_forecast',
                'symbol': symbol,
                **rev
            })
        
        return results
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze current trend"""
        close = df['close']
        
        # Calculate trend using linear regression
        x = np.arange(len(close))
        slope, intercept = np.polyfit(x, close.values, 1)
        
        # R-squared for trend strength
        y_pred = slope * x + intercept
        ss_res = np.sum((close.values - y_pred) ** 2)
        ss_tot = np.sum((close.values - close.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Project target
        current_price = close.iloc[-1]
        projected = intercept + slope * (len(close) + 5)  # 5 bars ahead
        
        return {
            'direction': 'bullish' if slope > 0 else 'bearish',
            'strength': abs(r_squared),
            'slope': slope,
            'target': round(projected, 2),
            'current': current_price
        }
    
    def _analyze_cycles(self, df: pd.DataFrame, min_period: int = 10, max_period: int = 50) -> List[Dict]:
        """Analyze price cycles"""
        close = df['close'].values
        cycles = []
        
        # Simple cycle detection using autocorrelation
        for period in range(min_period, min(max_period, len(close) // 3)):
            if period >= len(close):
                continue
            
            correlation = np.corrcoef(close[:-period], close[period:])[0, 1]
            
            if correlation > 0.5:
                # Check cycle position
                position = len(close) % period
                next_peak = period - position if position < period / 2 else period * 2 - position
                
                cycles.append({
                    'period': period,
                    'correlation': round(correlation, 3),
                    'position': position,
                    'next_turn_bars': next_peak,
                    'phase': 'ascending' if close[-1] > close[-period//2] else 'descending'
                })
        
        return sorted(cycles, key=lambda x: x['correlation'], reverse=True)[:3]
    
    def _find_reversal_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Find potential reversal signals"""
        reversals = []
        close = df['close']
        high = df['high']
        low = df['low']
        
        # Check for oversold/overbought
        rsi = self._calculate_rsi(close)
        
        if rsi.iloc[-1] < 30:
            reversals.append({
                'signal': 'oversold',
                'rsi': round(rsi.iloc[-1], 2),
                'expected_direction': 'up',
                'confidence': 0.6
            })
        elif rsi.iloc[-1] > 70:
            reversals.append({
                'signal': 'overbought',
                'rsi': round(rsi.iloc[-1], 2),
                'expected_direction': 'down',
                'confidence': 0.6
            })
        
        # Check for divergence (simplified)
        price_slope = close.iloc[-10:].values[-1] - close.iloc[-10:].values[0]
        rsi_slope = rsi.iloc[-10:].values[-1] - rsi.iloc[-10:].values[0]
        
        if (price_slope > 0 and rsi_slope < 0):
            reversals.append({
                'signal': 'bearish_divergence',
                'expected_direction': 'down',
                'confidence': 0.7
            })
        elif (price_slope < 0 and rsi_slope > 0):
            reversals.append({
                'signal': 'bullish_divergence',
                'expected_direction': 'up',
                'confidence': 0.7
            })
        
        return reversals
    
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def generate_forecast(self, df: pd.DataFrame, horizon: int = 5) -> Dict:
        """Generate price forecast"""
        close = df['close']
        
        # Multiple methods
        forecasts = {}
        
        # 1. Linear trend
        x = np.arange(len(close))
        slope, intercept = np.polyfit(x, close.values, 1)
        linear_forecast = [intercept + slope * (len(close) + i) for i in range(1, horizon + 1)]
        forecasts['linear'] = linear_forecast
        
        # 2. Moving average projection
        ma = close.rolling(20).mean().iloc[-1]
        ma_forecast = [ma] * horizon
        forecasts['ma'] = ma_forecast
        
        # 3. Exponential smoothing
        alpha = 0.3
        es = close.ewm(alpha=alpha, adjust=False).mean().iloc[-1]
        es_forecast = [es] * horizon
        forecasts['exp_smooth'] = es_forecast
        
        # Ensemble
        ensemble = [
            (linear_forecast[i] + ma_forecast[i] + es_forecast[i]) / 3
            for i in range(horizon)
        ]
        
        return {
            'current_price': close.iloc[-1],
            'horizon': horizon,
            'forecasts': {
                'linear': [round(x, 2) for x in linear_forecast],
                'moving_average': [round(x, 2) for x in ma_forecast],
                'exp_smoothing': [round(x, 2) for x in es_forecast],
                'ensemble': [round(x, 2) for x in ensemble]
            },
            'direction': 'up' if ensemble[-1] > close.iloc[-1] else 'down',
            'projected_change_pct': round((ensemble[-1] / close.iloc[-1] - 1) * 100, 2)
        }
