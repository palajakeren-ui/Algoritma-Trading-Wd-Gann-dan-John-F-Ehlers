"""
Forecasting Engine v3.0 - Production Ready
Price forecasting using multiple methods: ML, Gann, Cycles, and Statistical
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class ForecastMethod(Enum):
    GANN_TIME = "gann_time"
    GANN_PRICE = "gann_price"
    CYCLE = "cycle"
    ML = "machine_learning"
    STATISTICAL = "statistical"
    ENSEMBLE = "ensemble"


class ForecastHorizon(Enum):
    INTRADAY = "intraday"      # 1-24 hours
    SHORT_TERM = "short_term"  # 1-7 days
    MEDIUM_TERM = "medium_term"  # 1-4 weeks
    LONG_TERM = "long_term"    # 1-3 months


@dataclass
class PriceForecast:
    """Price forecast result"""
    symbol: str
    method: ForecastMethod
    horizon: ForecastHorizon
    forecast_date: datetime
    target_date: datetime
    current_price: float
    predicted_price: float
    predicted_high: float
    predicted_low: float
    confidence_interval: Tuple[float, float]
    confidence: float
    direction: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    supporting_indicators: List[str]


class ForecastingEngine:
    """
    Production-ready forecasting engine supporting:
    - Gann Price and Time Forecasting
    - Cycle-based Forecasting
    - Statistical Forecasting (Moving Averages, Regression)
    - ML-based Forecasting (if model available)
    - Ensemble Forecasting
    """
    
    # Gann time cycles for forecasting
    GANN_CYCLES = [7, 14, 21, 30, 45, 60, 90, 120, 144, 180, 270, 360]
    
    def __init__(self, config: Dict = None):
        """
        Initialize forecasting engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Settings
        self.lookback_periods = self.config.get('lookback_periods', 100)
        self.forecast_horizons = self.config.get('forecast_horizons', [7, 14, 30])
        
        logger.info("Forecasting Engine initialized")
    
    # ==================== GANN FORECASTING ====================
    
    def forecast_gann_price(
        self,
        data: pd.DataFrame,
        days_ahead: int = 7
    ) -> Dict:
        """
        Forecast price using Gann Square of 9.
        
        Args:
            data: Historical OHLCV data
            days_ahead: Number of days to forecast
            
        Returns:
            Forecast dictionary
        """
        current_price = data['close'].iloc[-1]
        sqrt_price = np.sqrt(current_price)
        
        # Calculate price levels
        levels = {}
        for i in range(1, 9):  # 1-8 levels (45 to 360 degrees)
            angle = 45 * i
            
            # Resistance levels
            resistance = (sqrt_price + (angle / 180)) ** 2
            levels[f'R{i}'] = resistance
            
            # Support levels
            support = (sqrt_price - (angle / 180)) ** 2
            if support > 0:
                levels[f'S{i}'] = support
        
        # Determine likely target based on trend
        ema20 = data['close'].ewm(span=20).mean().iloc[-1]
        ema50 = data['close'].ewm(span=50).mean().iloc[-1]
        
        if current_price > ema20 > ema50:
            # Bullish - target next resistance
            target = levels.get('R1', current_price * 1.05)
            direction = 'BULLISH'
        elif current_price < ema20 < ema50:
            # Bearish - target next support
            target = levels.get('S1', current_price * 0.95)
            direction = 'BEARISH'
        else:
            target = current_price
            direction = 'NEUTRAL'
        
        return {
            'method': 'gann_price',
            'current_price': current_price,
            'predicted_price': target,
            'levels': levels,
            'direction': direction,
            'confidence': 0.65
        }
    
    def forecast_gann_time(
        self,
        data: pd.DataFrame,
        pivot_dates: List[datetime] = None
    ) -> Dict:
        """
        Forecast timing using Gann time cycles.
        
        Returns:
            Timing forecast dictionary
        """
        current_date = data.index[-1]
        
        # Find significant pivot points
        if pivot_dates is None:
            pivot_dates = self._find_pivots(data)
        
        # Calculate upcoming cycle dates
        upcoming_dates = []
        
        for pivot in pivot_dates[-5:]:  # Use last 5 pivots
            for cycle in self.GANN_CYCLES:
                cycle_date = pivot + timedelta(days=cycle)
                if cycle_date > current_date:
                    days_until = (cycle_date - current_date).days
                    if days_until <= 90:  # Within 90 days
                        upcoming_dates.append({
                            'date': cycle_date,
                            'days_until': days_until,
                            'cycle_days': cycle,
                            'from_pivot': pivot
                        })
        
        # Sort by date
        upcoming_dates.sort(key=lambda x: x['days_until'])
        
        # Find clusters (confluence)
        clusters = self._find_date_clusters(upcoming_dates)
        
        return {
            'method': 'gann_time',
            'current_date': current_date,
            'upcoming_cycles': upcoming_dates[:10],
            'clusters': clusters,
            'next_significant_date': clusters[0]['date'] if clusters else None
        }
    
    def _find_pivots(self, data: pd.DataFrame, lookback: int = 50) -> List[datetime]:
        """Find significant pivot points"""
        pivots = []
        
        for i in range(2, min(lookback, len(data) - 2)):
            idx = len(data) - i - 1
            
            # Swing high
            if (data['high'].iloc[idx] > data['high'].iloc[idx-1] and
                data['high'].iloc[idx] > data['high'].iloc[idx+1] and
                data['high'].iloc[idx] > data['high'].iloc[idx-2] and
                data['high'].iloc[idx] > data['high'].iloc[idx+2]):
                pivots.append(data.index[idx])
            
            # Swing low
            if (data['low'].iloc[idx] < data['low'].iloc[idx-1] and
                data['low'].iloc[idx] < data['low'].iloc[idx+1] and
                data['low'].iloc[idx] < data['low'].iloc[idx-2] and
                data['low'].iloc[idx] < data['low'].iloc[idx+2]):
                pivots.append(data.index[idx])
        
        return sorted(set(pivots))
    
    def _find_date_clusters(self, dates: List[Dict], tolerance_days: int = 3) -> List[Dict]:
        """Find clusters of dates (confluence)"""
        if not dates:
            return []
        
        clusters = []
        used = set()
        
        for i, d1 in enumerate(dates):
            if i in used:
                continue
            
            cluster = [d1]
            used.add(i)
            
            for j, d2 in enumerate(dates):
                if j in used or j == i:
                    continue
                
                if abs(d1['days_until'] - d2['days_until']) <= tolerance_days:
                    cluster.append(d2)
                    used.add(j)
            
            if len(cluster) >= 2:
                avg_days = sum(c['days_until'] for c in cluster) / len(cluster)
                clusters.append({
                    'date': d1['date'],
                    'days_until': avg_days,
                    'confluence_count': len(cluster),
                    'strength': len(cluster) / 5  # Normalize
                })
        
        return sorted(clusters, key=lambda x: -x['confluence_count'])
    
    # ==================== CYCLE FORECASTING ====================
    
    def forecast_cycles(
        self,
        data: pd.DataFrame,
        forecast_days: int = 30
    ) -> Dict:
        """
        Forecast using dominant cycle analysis.
        
        Returns:
            Cycle-based forecast
        """
        close = data['close'].values
        n = len(close)
        
        # Detrend data
        trend = np.polyfit(np.arange(n), close, 1)
        detrended = close - (trend[0] * np.arange(n) + trend[1])
        
        # FFT to find dominant cycles
        fft = np.fft.fft(detrended)
        frequencies = np.fft.fftfreq(n)
        
        # Find dominant frequencies
        power = np.abs(fft) ** 2
        dominant_idx = np.argsort(power[1:n//2])[-5:] + 1  # Top 5 cycles
        
        dominant_periods = []
        for idx in dominant_idx:
            if frequencies[idx] > 0:
                period = 1 / frequencies[idx]
                if 5 <= period <= 200:  # Reasonable cycle range
                    dominant_periods.append(int(period))
        
        # Project cycles forward
        future_dates = pd.date_range(
            start=data.index[-1] + timedelta(days=1),
            periods=forecast_days,
            freq='D'
        )
        
        # Simple cycle projection
        projections = []
        for i, date in enumerate(future_dates):
            cycle_value = 0
            for period in dominant_periods:
                # Phase from last data point
                phase = (n + i) * 2 * np.pi / period
                cycle_value += np.sin(phase)
            
            projections.append({
                'date': date,
                'cycle_value': cycle_value,
                'direction': 'UP' if cycle_value > 0 else 'DOWN'
            })
        
        return {
            'method': 'cycle',
            'dominant_periods': dominant_periods,
            'projections': projections,
            'trend_slope': trend[0],
            'trend_direction': 'BULLISH' if trend[0] > 0 else 'BEARISH'
        }
    
    # ==================== STATISTICAL FORECASTING ====================
    
    def forecast_statistical(
        self,
        data: pd.DataFrame,
        days_ahead: int = 7
    ) -> Dict:
        """
        Forecast using statistical methods.
        
        Returns:
            Statistical forecast
        """
        close = data['close']
        current_price = close.iloc[-1]
        
        # Calculate returns
        returns = close.pct_change().dropna()
        
        # Mean and volatility
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Project forward
        expected_return = mean_return * days_ahead
        expected_std = std_return * np.sqrt(days_ahead)
        
        predicted_price = current_price * (1 + expected_return)
        confidence_low = current_price * (1 + expected_return - 2 * expected_std)
        confidence_high = current_price * (1 + expected_return + 2 * expected_std)
        
        # Moving average forecast
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        
        # Linear regression forecast
        x = np.arange(len(close))
        slope, intercept = np.polyfit(x, close.values, 1)
        reg_forecast = slope * (len(close) + days_ahead) + intercept
        
        return {
            'method': 'statistical',
            'current_price': current_price,
            'predicted_price': predicted_price,
            'regression_forecast': reg_forecast,
            'confidence_interval': (confidence_low, confidence_high),
            'daily_return': mean_return,
            'daily_volatility': std_return,
            'sma20': sma20,
            'sma50': sma50,
            'trend': 'BULLISH' if slope > 0 else 'BEARISH'
        }
    
    # ==================== ENSEMBLE FORECASTING ====================
    
    def forecast_ensemble(
        self,
        data: pd.DataFrame,
        days_ahead: int = 7
    ) -> PriceForecast:
        """
        Generate ensemble forecast combining multiple methods.
        
        Returns:
            PriceForecast object
        """
        current_price = data['close'].iloc[-1]
        current_date = data.index[-1]
        target_date = current_date + timedelta(days=days_ahead)
        
        # Get individual forecasts
        gann_forecast = self.forecast_gann_price(data, days_ahead)
        stat_forecast = self.forecast_statistical(data, days_ahead)
        cycle_forecast = self.forecast_cycles(data, days_ahead)
        
        # Weights for ensemble
        weights = {
            'gann': 0.35,
            'statistical': 0.35,
            'cycle': 0.30
        }
        
        # Combine predictions
        predictions = [
            (gann_forecast['predicted_price'], weights['gann'], gann_forecast['confidence']),
            (stat_forecast['predicted_price'], weights['statistical'], 0.5),
            (stat_forecast['regression_forecast'], weights['statistical'] * 0.5, 0.4)
        ]
        
        # Weighted average
        total_weight = sum(p[1] for p in predictions)
        ensemble_price = sum(p[0] * p[1] for p in predictions) / total_weight
        ensemble_confidence = sum(p[2] * p[1] for p in predictions) / total_weight
        
        # Determine direction
        price_change = (ensemble_price - current_price) / current_price
        if price_change > 0.02:
            direction = 'BULLISH'
        elif price_change < -0.02:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'
        
        # Calculate high/low estimates
        volatility = data['close'].pct_change().std() * np.sqrt(days_ahead)
        predicted_high = ensemble_price * (1 + volatility)
        predicted_low = ensemble_price * (1 - volatility)
        
        # Confidence interval
        ci_low = stat_forecast['confidence_interval'][0]
        ci_high = stat_forecast['confidence_interval'][1]
        
        # Determine horizon
        if days_ahead <= 1:
            horizon = ForecastHorizon.INTRADAY
        elif days_ahead <= 7:
            horizon = ForecastHorizon.SHORT_TERM
        elif days_ahead <= 30:
            horizon = ForecastHorizon.MEDIUM_TERM
        else:
            horizon = ForecastHorizon.LONG_TERM
        
        # Supporting indicators
        indicators = []
        if gann_forecast['direction'] == direction:
            indicators.append(f"Gann: {gann_forecast['direction']}")
        if stat_forecast['trend'] == direction:
            indicators.append(f"Trend: {stat_forecast['trend']}")
        if cycle_forecast['trend_direction'] == direction:
            indicators.append(f"Cycle: {cycle_forecast['trend_direction']}")
        
        return PriceForecast(
            symbol=data.attrs.get('symbol', 'UNKNOWN'),
            method=ForecastMethod.ENSEMBLE,
            horizon=horizon,
            forecast_date=datetime.now(),
            target_date=target_date,
            current_price=current_price,
            predicted_price=round(ensemble_price, 2),
            predicted_high=round(predicted_high, 2),
            predicted_low=round(predicted_low, 2),
            confidence_interval=(round(ci_low, 2), round(ci_high, 2)),
            confidence=round(ensemble_confidence, 2),
            direction=direction,
            supporting_indicators=indicators
        )
    
    def forecast_multiple_horizons(
        self,
        data: pd.DataFrame
    ) -> List[PriceForecast]:
        """
        Generate forecasts for multiple time horizons.
        
        Returns:
            List of forecasts for different horizons
        """
        forecasts = []
        
        for days in self.forecast_horizons:
            forecast = self.forecast_ensemble(data, days)
            forecasts.append(forecast)
        
        return forecasts


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1D')
    np.random.seed(42)
    
    # Generate price with trend and cycles
    t = np.arange(200)
    trend = 50000 + t * 20
    cycle = 2000 * np.sin(2 * np.pi * t / 45)
    noise = np.cumsum(np.random.randn(200) * 200)
    price = trend + cycle + noise
    
    data = pd.DataFrame({
        'open': price - np.abs(np.random.randn(200) * 300),
        'high': price + np.abs(np.random.randn(200) * 500),
        'low': price - np.abs(np.random.randn(200) * 500),
        'close': price,
        'volume': np.random.uniform(1e9, 5e9, 200)
    }, index=dates)
    data.attrs['symbol'] = 'BTCUSD'
    
    # Run forecaster
    forecaster = ForecastingEngine({'forecast_horizons': [7, 14, 30]})
    
    print("\n=== Gann Price Forecast ===")
    gann = forecaster.forecast_gann_price(data)
    print(f"Current: ${gann['current_price']:,.2f}")
    print(f"Predicted: ${gann['predicted_price']:,.2f}")
    print(f"Direction: {gann['direction']}")
    
    print("\n=== Statistical Forecast ===")
    stat = forecaster.forecast_statistical(data, 7)
    print(f"Predicted (7d): ${stat['predicted_price']:,.2f}")
    print(f"Confidence: ${stat['confidence_interval'][0]:,.2f} - ${stat['confidence_interval'][1]:,.2f}")
    
    print("\n=== Cycle Forecast ===")
    cycle = forecaster.forecast_cycles(data)
    print(f"Dominant Periods: {cycle['dominant_periods']}")
    print(f"Trend: {cycle['trend_direction']}")
    
    print("\n=== Ensemble Forecast (7 days) ===")
    ensemble = forecaster.forecast_ensemble(data, 7)
    print(f"Predicted: ${ensemble.predicted_price:,.2f}")
    print(f"Range: ${ensemble.predicted_low:,.2f} - ${ensemble.predicted_high:,.2f}")
    print(f"Direction: {ensemble.direction}")
    print(f"Confidence: {ensemble.confidence:.2%}")
    print(f"Supporting: {', '.join(ensemble.supporting_indicators)}")
