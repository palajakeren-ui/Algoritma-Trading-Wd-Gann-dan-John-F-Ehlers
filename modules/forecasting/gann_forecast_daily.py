"""
Gann Daily Forecast Module
Generates daily market forecasts using Gann methodologies
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class ForecastBias(Enum):
    """Forecast bias types"""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class DailyForecast:
    """Daily forecast result"""
    date: datetime
    bias: ForecastBias
    confidence: float
    support_level: float
    resistance_level: float
    pivot_point: float
    target_high: float
    target_low: float
    time_cycles_active: List[str]
    key_angles: List[float]
    narrative: str


class GannDailyForecaster:
    """
    Generates daily market forecasts using Gann techniques.
    Combines Square of 9, time cycles, and angle analysis.
    """
    
    # Gann key time cycles (in days)
    TIME_CYCLES = [7, 14, 21, 28, 30, 45, 49, 52, 60, 90, 120, 144, 180, 270, 360]
    
    # Gann cardinal angles
    CARDINAL_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315, 360]
    
    def __init__(self, config: Dict = None):
        """Initialize the Gann daily forecaster."""
        self.config = config or {}
        logger.info("GannDailyForecaster initialized")
    
    def calculate_sq9_level(self, base_price: float, angle: float) -> float:
        """Calculate Square of 9 price level for given angle."""
        sqrt_price = np.sqrt(base_price)
        rotation = angle / 360.0
        new_sqrt = sqrt_price + rotation
        return new_sqrt ** 2
    
    def calculate_pivot_levels(self, high: float, low: float, close: float) -> Dict:
        """Calculate pivot point and support/resistance levels."""
        pivot = (high + low + close) / 3
        
        return {
            'pivot': round(pivot, 2),
            'r1': round(2 * pivot - low, 2),
            'r2': round(pivot + (high - low), 2),
            'r3': round(high + 2 * (pivot - low), 2),
            's1': round(2 * pivot - high, 2),
            's2': round(pivot - (high - low), 2),
            's3': round(low - 2 * (high - pivot), 2)
        }
    
    def calculate_gann_levels(self, current_price: float, cycle_low: float, cycle_high: float) -> Dict:
        """Calculate Gann-based support and resistance levels."""
        range_size = cycle_high - cycle_low
        
        # Gann percentage levels
        levels = {
            'extreme_low': cycle_low,
            '12.5%': cycle_low + range_size * 0.125,
            '25%': cycle_low + range_size * 0.25,
            '33.3%': cycle_low + range_size * 0.333,
            '37.5%': cycle_low + range_size * 0.375,
            '50%': cycle_low + range_size * 0.5,
            '62.5%': cycle_low + range_size * 0.625,
            '66.7%': cycle_low + range_size * 0.667,
            '75%': cycle_low + range_size * 0.75,
            '87.5%': cycle_low + range_size * 0.875,
            'extreme_high': cycle_high
        }
        
        # Find nearest support and resistance
        support = max([v for v in levels.values() if v < current_price], default=cycle_low)
        resistance = min([v for v in levels.values() if v > current_price], default=cycle_high)
        
        return {
            'levels': {k: round(v, 2) for k, v in levels.items()},
            'nearest_support': round(support, 2),
            'nearest_resistance': round(resistance, 2)
        }
    
    def check_time_cycles(self, date: datetime, pivot_dates: List[datetime]) -> List[Dict]:
        """Check which time cycles are active from pivot dates."""
        active_cycles = []
        
        for pivot_date in pivot_dates:
            days_since = (date - pivot_date).days
            
            for cycle in self.TIME_CYCLES:
                # Check if date falls on or near a cycle
                if abs(days_since - cycle) <= 2 or abs(days_since % cycle) <= 2:
                    active_cycles.append({
                        'cycle': cycle,
                        'from_date': pivot_date.isoformat(),
                        'days_since': days_since,
                        'cycle_name': self._get_cycle_name(cycle)
                    })
        
        return active_cycles
    
    def _get_cycle_name(self, days: int) -> str:
        """Get descriptive name for a time cycle."""
        names = {
            7: "Weekly",
            14: "Bi-Weekly",
            21: "Minor",
            28: "Lunar Month",
            30: "Monthly",
            45: "45-Day",
            49: "7x7 Master",
            52: "Year in Weeks",
            60: "60-Day",
            90: "Quarterly",
            120: "4-Month",
            144: "Fibonacci 144",
            180: "Semi-Annual",
            270: "270-Day",
            360: "Annual"
        }
        return names.get(days, f"{days}-Day")
    
    def calculate_price_angle(self, price: float, base_price: float, time_units: int) -> float:
        """Calculate the angle of price movement."""
        if time_units == 0:
            return 0
        
        price_change = price - base_price
        angle_rad = np.arctan2(price_change, time_units)
        angle_deg = np.degrees(angle_rad)
        
        return round(angle_deg, 2)
    
    def determine_bias(
        self,
        current_price: float,
        gann_levels: Dict,
        active_cycles: List[Dict],
        price_angle: float
    ) -> Tuple[ForecastBias, float]:
        """Determine forecast bias based on Gann analysis."""
        support = gann_levels['nearest_support']
        resistance = gann_levels['nearest_resistance']
        
        # Position within range
        if resistance != support:
            position = (current_price - support) / (resistance - support)
        else:
            position = 0.5
        
        # Base score (0 = bearish, 1 = bullish)
        score = 0.5
        
        # Price position influence
        if position < 0.25:
            score += 0.15  # Near support - bouncing
        elif position > 0.75:
            score -= 0.15  # Near resistance - reversal likely
        
        # Angle influence
        if price_angle > 45:
            score += 0.15  # Strong uptrend
        elif price_angle > 15:
            score += 0.08
        elif price_angle < -45:
            score -= 0.15  # Strong downtrend
        elif price_angle < -15:
            score -= 0.08
        
        # Time cycle influence
        if len(active_cycles) >= 2:
            score += 0.1  # Confluence often marks turning points
        
        # Determine bias
        if score >= 0.7:
            bias = ForecastBias.STRONG_BULLISH
        elif score >= 0.55:
            bias = ForecastBias.BULLISH
        elif score <= 0.3:
            bias = ForecastBias.STRONG_BEARISH
        elif score <= 0.45:
            bias = ForecastBias.BEARISH
        else:
            bias = ForecastBias.NEUTRAL
        
        # Confidence based on cycle confluence
        confidence = min(0.9, 0.5 + len(active_cycles) * 0.1)
        
        return bias, confidence
    
    def generate_forecast(
        self,
        data: pd.DataFrame,
        target_date: datetime = None,
        pivot_dates: List[datetime] = None
    ) -> DailyForecast:
        """
        Generate a daily Gann-based forecast.
        
        Args:
            data: OHLCV DataFrame with historical data
            target_date: Date to forecast for (default: today)
            pivot_dates: List of significant pivot dates
            
        Returns:
            DailyForecast object
        """
        if target_date is None:
            target_date = datetime.now()
        
        # Get current price data
        if data is None or data.empty:
            raise ValueError("Price data is required for forecast")
        
        current = data.iloc[-1]
        current_price = float(current['close'])
        
        # Calculate cycle highs and lows (last 30 bars)
        recent = data.tail(30)
        cycle_high = float(recent['high'].max())
        cycle_low = float(recent['low'].min())
        
        # Calculate pivot levels
        pivot_levels = self.calculate_pivot_levels(
            float(current['high']),
            float(current['low']),
            float(current['close'])
        )
        
        # Calculate Gann levels
        gann_levels = self.calculate_gann_levels(current_price, cycle_low, cycle_high)
        
        # Find pivot dates if not provided
        if pivot_dates is None:
            pivot_dates = self._find_pivot_dates(data)
        
        # Check active time cycles
        active_cycles = self.check_time_cycles(target_date, pivot_dates)
        
        # Calculate price angle
        if len(data) >= 10:
            base_price = float(data.iloc[-10]['close'])
            price_angle = self.calculate_price_angle(current_price, base_price, 10)
        else:
            price_angle = 0
        
        # Determine bias
        bias, confidence = self.determine_bias(
            current_price, gann_levels, active_cycles, price_angle
        )
        
        # Calculate targets
        daily_range = float(recent['high'].mean() - recent['low'].mean())
        
        if bias in [ForecastBias.STRONG_BULLISH, ForecastBias.BULLISH]:
            target_high = gann_levels['nearest_resistance']
            target_low = max(current_price - daily_range * 0.5, gann_levels['nearest_support'])
        else:
            target_high = min(current_price + daily_range * 0.5, gann_levels['nearest_resistance'])
            target_low = gann_levels['nearest_support']
        
        # Generate narrative
        narrative = self._generate_narrative(
            bias, confidence, active_cycles, gann_levels, current_price
        )
        
        return DailyForecast(
            date=target_date,
            bias=bias,
            confidence=confidence,
            support_level=gann_levels['nearest_support'],
            resistance_level=gann_levels['nearest_resistance'],
            pivot_point=pivot_levels['pivot'],
            target_high=round(target_high, 2),
            target_low=round(target_low, 2),
            time_cycles_active=[c['cycle_name'] for c in active_cycles],
            key_angles=self.CARDINAL_ANGLES,
            narrative=narrative
        )
    
    def _find_pivot_dates(self, data: pd.DataFrame, lookback: int = 50) -> List[datetime]:
        """Find significant pivot dates in price data."""
        pivots = []
        recent = data.tail(lookback)
        
        for i in range(2, len(recent) - 2):
            idx = recent.index[i]
            
            # Swing high
            if (recent.iloc[i]['high'] > recent.iloc[i-1]['high'] and
                recent.iloc[i]['high'] > recent.iloc[i-2]['high'] and
                recent.iloc[i]['high'] > recent.iloc[i+1]['high'] and
                recent.iloc[i]['high'] > recent.iloc[i+2]['high']):
                if isinstance(idx, pd.Timestamp):
                    pivots.append(idx.to_pydatetime())
            
            # Swing low
            if (recent.iloc[i]['low'] < recent.iloc[i-1]['low'] and
                recent.iloc[i]['low'] < recent.iloc[i-2]['low'] and
                recent.iloc[i]['low'] < recent.iloc[i+1]['low'] and
                recent.iloc[i]['low'] < recent.iloc[i+2]['low']):
                if isinstance(idx, pd.Timestamp):
                    pivots.append(idx.to_pydatetime())
        
        return pivots
    
    def _generate_narrative(
        self,
        bias: ForecastBias,
        confidence: float,
        active_cycles: List[Dict],
        gann_levels: Dict,
        current_price: float
    ) -> str:
        """Generate a human-readable forecast narrative."""
        bias_text = {
            ForecastBias.STRONG_BULLISH: "strongly bullish",
            ForecastBias.BULLISH: "bullish",
            ForecastBias.NEUTRAL: "neutral",
            ForecastBias.BEARISH: "bearish",
            ForecastBias.STRONG_BEARISH: "strongly bearish"
        }
        
        parts = [f"The market outlook is {bias_text[bias]} with {confidence*100:.0f}% confidence."]
        
        if active_cycles:
            cycle_names = [c['cycle_name'] for c in active_cycles[:3]]
            parts.append(f"Active Gann cycles: {', '.join(cycle_names)}.")
        
        parts.append(f"Key support at {gann_levels['nearest_support']:.2f}, "
                    f"resistance at {gann_levels['nearest_resistance']:.2f}.")
        
        return " ".join(parts)
    
    def generate_multi_day_forecast(
        self,
        data: pd.DataFrame,
        days_ahead: int = 7
    ) -> List[Dict]:
        """Generate forecasts for multiple days ahead."""
        forecasts = []
        pivot_dates = self._find_pivot_dates(data)
        
        for day in range(days_ahead):
            target_date = datetime.now() + timedelta(days=day)
            
            try:
                forecast = self.generate_forecast(data, target_date, pivot_dates)
                forecasts.append({
                    'date': forecast.date.strftime('%Y-%m-%d'),
                    'bias': forecast.bias.value,
                    'confidence': forecast.confidence,
                    'support': forecast.support_level,
                    'resistance': forecast.resistance_level,
                    'pivot': forecast.pivot_point,
                    'target_high': forecast.target_high,
                    'target_low': forecast.target_low,
                    'cycles': forecast.time_cycles_active,
                    'narrative': forecast.narrative
                })
            except Exception as e:
                logger.error(f"Error generating forecast for day {day}: {e}")
        
        return forecasts


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1D')
    np.random.seed(42)
    
    price = 50000
    prices = [price]
    for _ in range(99):
        price = price * (1 + np.random.randn() * 0.02)
        prices.append(price)
    
    data = pd.DataFrame({
        'open': [p * 0.99 for p in prices],
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 100)
    }, index=dates)
    
    forecaster = GannDailyForecaster()
    
    print("\n=== Daily Forecast ===")
    forecast = forecaster.generate_forecast(data)
    print(f"Date: {forecast.date.strftime('%Y-%m-%d')}")
    print(f"Bias: {forecast.bias.value}")
    print(f"Confidence: {forecast.confidence:.0%}")
    print(f"Support: {forecast.support_level:.2f}")
    print(f"Resistance: {forecast.resistance_level:.2f}")
    print(f"Active Cycles: {forecast.time_cycles_active}")
    print(f"Narrative: {forecast.narrative}")
    
    print("\n=== 7-Day Forecast ===")
    multi_day = forecaster.generate_multi_day_forecast(data)
    for f in multi_day:
        print(f"{f['date']}: {f['bias']} (conf: {f['confidence']:.0%})")
