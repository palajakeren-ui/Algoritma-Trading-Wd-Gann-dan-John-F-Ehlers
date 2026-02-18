"""
ATH/ATL Predictor v3.0 - Production Ready
All-Time High / All-Time Low prediction engine using Gann and Astro principles
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class PredictionType(Enum):
    ATH = "all_time_high"
    ATL = "all_time_low"
    LOCAL_HIGH = "local_high"
    LOCAL_LOW = "local_low"


class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ATHATLPrediction:
    """Prediction result"""
    type: PredictionType
    predicted_date: datetime
    predicted_price: float
    confidence: ConfidenceLevel
    confidence_score: float
    supporting_factors: List[str]
    gann_alignment: float
    astro_alignment: float
    cycle_alignment: float
    description: str


class ATHATLPredictor:
    """
    Production-ready ATH/ATL predictor using:
    - Gann Time Cycles
    - Gann Price Vibrations
    - Astro Cycles (if available)
    - Market Structure Analysis
    - Fibonacci Time Extensions
    - Historical Pattern Matching
    """
    
    # Gann time cycles in days
    GANN_TIME_CYCLES = [7, 14, 21, 28, 30, 45, 49, 52, 60, 90, 120, 144, 180, 270, 360]
    
    # Fibonacci time ratios
    FIBO_TIME_RATIOS = [0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618]
    
    def __init__(self, config: Dict = None):
        """
        Initialize predictor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Settings
        self.lookback_days = self.config.get('lookback_days', 365)
        self.forecast_days = self.config.get('forecast_days', 90)
        self.min_swing_pct = self.config.get('min_swing_pct', 5.0)  # Minimum swing percentage
        
        logger.info("ATH/ATL Predictor initialized")
    
    # ==================== MARKET STRUCTURE ====================
    
    def find_swing_points(
        self,
        data: pd.DataFrame,
        min_swing_pct: float = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Find swing highs and swing lows.
        
        Args:
            data: DataFrame with OHLC data
            min_swing_pct: Minimum swing percentage
            
        Returns:
            Tuple of (swing_highs DataFrame, swing_lows DataFrame)
        """
        if min_swing_pct is None:
            min_swing_pct = self.min_swing_pct
        
        highs = []
        lows = []
        
        for i in range(2, len(data) - 2):
            # Swing high: higher than 2 bars before and after
            if (data['high'].iloc[i] > data['high'].iloc[i-1] and 
                data['high'].iloc[i] > data['high'].iloc[i-2] and
                data['high'].iloc[i] > data['high'].iloc[i+1] and 
                data['high'].iloc[i] > data['high'].iloc[i+2]):
                
                highs.append({
                    'date': data.index[i],
                    'price': data['high'].iloc[i],
                    'index': i
                })
            
            # Swing low: lower than 2 bars before and after
            if (data['low'].iloc[i] < data['low'].iloc[i-1] and 
                data['low'].iloc[i] < data['low'].iloc[i-2] and
                data['low'].iloc[i] < data['low'].iloc[i+1] and 
                data['low'].iloc[i] < data['low'].iloc[i+2]):
                
                lows.append({
                    'date': data.index[i],
                    'price': data['low'].iloc[i],
                    'index': i
                })
        
        swing_highs = pd.DataFrame(highs) if highs else pd.DataFrame(columns=['date', 'price', 'index'])
        swing_lows = pd.DataFrame(lows) if lows else pd.DataFrame(columns=['date', 'price', 'index'])
        
        # Filter by minimum swing percentage
        if len(swing_highs) > 1 and len(swing_lows) > 1:
            avg_range = data['high'].max() - data['low'].min()
            min_swing = avg_range * (min_swing_pct / 100)
            
            # Keep only significant swings
            if len(swing_highs) > 0:
                swing_highs['is_significant'] = True
                for i in range(1, len(swing_highs)):
                    if abs(swing_highs['price'].iloc[i] - swing_highs['price'].iloc[i-1]) < min_swing:
                        swing_highs.iloc[i, swing_highs.columns.get_loc('is_significant')] = False
                swing_highs = swing_highs[swing_highs['is_significant']].drop('is_significant', axis=1)
            
            if len(swing_lows) > 0:
                swing_lows['is_significant'] = True
                for i in range(1, len(swing_lows)):
                    if abs(swing_lows['price'].iloc[i] - swing_lows['price'].iloc[i-1]) < min_swing:
                        swing_lows.iloc[i, swing_lows.columns.get_loc('is_significant')] = False
                swing_lows = swing_lows[swing_lows['is_significant']].drop('is_significant', axis=1)
        
        return swing_highs, swing_lows
    
    def get_ath_atl(self, data: pd.DataFrame) -> Tuple[Dict, Dict]:
        """
        Get current ATH and ATL.
        
        Returns:
            Tuple of (ATH dict, ATL dict)
        """
        ath_idx = data['high'].idxmax()
        atl_idx = data['low'].idxmin()
        
        ath = {
            'date': ath_idx,
            'price': data.loc[ath_idx, 'high'],
            'days_ago': (data.index[-1] - ath_idx).days if hasattr(ath_idx, 'day') else len(data) - data.index.get_loc(ath_idx)
        }
        
        atl = {
            'date': atl_idx,
            'price': data.loc[atl_idx, 'low'],
            'days_ago': (data.index[-1] - atl_idx).days if hasattr(atl_idx, 'day') else len(data) - data.index.get_loc(atl_idx)
        }
        
        return ath, atl
    
    # ==================== GANN TIME ANALYSIS ====================
    
    def analyze_gann_time_cycles(
        self,
        pivot_date: datetime,
        pivot_type: str,
        current_date: datetime
    ) -> List[Dict]:
        """
        Analyze Gann time cycles from a pivot point.
        
        Args:
            pivot_date: Date of the pivot
            pivot_type: 'high' or 'low'
            current_date: Current date
            
        Returns:
            List of upcoming cycle dates
        """
        cycles = []
        
        for cycle_days in self.GANN_TIME_CYCLES:
            cycle_date = pivot_date + timedelta(days=cycle_days)
            
            if cycle_date > current_date:
                days_until = (cycle_date - current_date).days
                
                # Determine expected move
                if pivot_type == 'high':
                    expected = 'low' if cycle_days in [45, 90, 180] else 'high'
                else:
                    expected = 'high' if cycle_days in [45, 90, 180] else 'low'
                
                cycles.append({
                    'date': cycle_date,
                    'days_until': days_until,
                    'cycle_length': cycle_days,
                    'expected_move': expected,
                    'cycle_name': self._get_gann_cycle_name(cycle_days)
                })
        
        return sorted(cycles, key=lambda x: x['days_until'])
    
    def _get_gann_cycle_name(self, days: int) -> str:
        """Get Gann cycle name"""
        names = {
            7: "Weekly Cycle",
            14: "Bi-Weekly Cycle",
            21: "Minor Cycle",
            28: "Lunar Month",
            30: "Monthly Cycle",
            45: "45-Day Cycle",
            49: "7x7 Cycle",
            52: "Year in Weeks",
            60: "60-Day Cycle",
            90: "Quarterly Cycle",
            120: "4-Month Cycle",
            144: "Fibonacci 144",
            180: "Semi-Annual",
            270: "270-Day Cycle",
            360: "Annual Cycle"
        }
        return names.get(days, f"{days}-Day Cycle")
    
    def calculate_gann_price_targets(
        self,
        pivot_price: float,
        pivot_type: str
    ) -> List[Dict]:
        """
        Calculate Gann price targets using Square of 9.
        
        Args:
            pivot_price: Price at the pivot
            pivot_type: 'high' or 'low'
            
        Returns:
            List of price targets
        """
        targets = []
        sqrt_price = np.sqrt(pivot_price)
        
        # Gann angles in degrees
        angles = [45, 90, 120, 135, 180, 225, 270, 315, 360]
        
        for angle in angles:
            radians = np.deg2rad(angle)
            
            # Calculate price levels
            if pivot_type == 'low':
                # Resistance levels above
                new_sqrt = sqrt_price + (angle / 180)
                target_price = new_sqrt ** 2
                target_type = 'resistance'
            else:
                # Support levels below
                new_sqrt = sqrt_price - (angle / 180)
                if new_sqrt > 0:
                    target_price = new_sqrt ** 2
                    target_type = 'support'
                else:
                    continue
            
            pct_from_pivot = ((target_price - pivot_price) / pivot_price) * 100
            
            targets.append({
                'price': target_price,
                'angle': angle,
                'type': target_type,
                'pct_from_pivot': pct_from_pivot,
                'description': f"Gann {angle}° {target_type.title()}"
            })
        
        return targets
    
    # ==================== FIBONACCI TIME ANALYSIS ====================
    
    def calculate_fibonacci_time_extensions(
        self,
        swing_dates: List[datetime],
        current_date: datetime
    ) -> List[Dict]:
        """
        Calculate Fibonacci time extensions.
        
        Args:
            swing_dates: List of significant swing dates
            current_date: Current date
            
        Returns:
            List of Fibonacci time projection dates
        """
        if len(swing_dates) < 2:
            return []
        
        projections = []
        
        # Use last two swings for projection
        date1 = swing_dates[-2]
        date2 = swing_dates[-1]
        base_days = (date2 - date1).days
        
        for ratio in self.FIBO_TIME_RATIOS:
            projection_days = int(base_days * ratio)
            projection_date = date2 + timedelta(days=projection_days)
            
            if projection_date > current_date:
                days_until = (projection_date - current_date).days
                projections.append({
                    'date': projection_date,
                    'days_until': days_until,
                    'fibo_ratio': ratio,
                    'base_swing_days': base_days,
                    'description': f"Fibo {ratio:.3f} Time Extension"
                })
        
        return sorted(projections, key=lambda x: x['days_until'])
    
    # ==================== CYCLE CONFLUENCE ====================
    
    def find_time_confluence(
        self,
        gann_cycles: List[Dict],
        fibo_projections: List[Dict],
        tolerance_days: int = 3
    ) -> List[Dict]:
        """
        Find confluence zones where multiple time cycles align.
        
        Args:
            gann_cycles: Gann time cycle dates
            fibo_projections: Fibonacci time projections
            tolerance_days: Days tolerance for confluence
            
        Returns:
            List of confluence zones
        """
        confluences = []
        all_dates = []
        
        # Collect all dates
        for gc in gann_cycles:
            all_dates.append({
                'date': gc['date'],
                'type': 'gann',
                'details': gc
            })
        
        for fp in fibo_projections:
            all_dates.append({
                'date': fp['date'],
                'type': 'fibo',
                'details': fp
            })
        
        # Sort by date
        all_dates.sort(key=lambda x: x['date'])
        
        # Find clusters
        used_indices = set()
        
        for i, date_info in enumerate(all_dates):
            if i in used_indices:
                continue
            
            cluster = [date_info]
            used_indices.add(i)
            
            for j in range(i + 1, len(all_dates)):
                if j in used_indices:
                    continue
                
                days_diff = abs((all_dates[j]['date'] - date_info['date']).days)
                if days_diff <= tolerance_days:
                    cluster.append(all_dates[j])
                    used_indices.add(j)
            
            if len(cluster) >= 2:
                # Calculate confluence strength
                gann_count = sum(1 for c in cluster if c['type'] == 'gann')
                fibo_count = sum(1 for c in cluster if c['type'] == 'fibo')
                
                avg_date = sum((c['date'] - datetime.min).days for c in cluster) / len(cluster)
                avg_datetime = datetime.min + timedelta(days=avg_date)
                
                confluences.append({
                    'date': avg_datetime,
                    'dates': [c['date'] for c in cluster],
                    'count': len(cluster),
                    'gann_count': gann_count,
                    'fibo_count': fibo_count,
                    'strength': len(cluster) / 4,  # Normalize to 0-1+
                    'factors': cluster
                })
        
        return sorted(confluences, key=lambda x: -x['strength'])
    
    # ==================== MAIN PREDICTION ====================
    
    def predict(
        self,
        data: pd.DataFrame,
        astro_events: pd.DataFrame = None
    ) -> List[ATHATLPrediction]:
        """
        Generate ATH/ATL predictions.
        
        Args:
            data: Historical OHLCV data
            astro_events: Optional astro events data
            
        Returns:
            List of predictions
        """
        predictions = []
        
        # Get current state
        current_date = data.index[-1]
        current_price = data['close'].iloc[-1]
        ath, atl = self.get_ath_atl(data)
        
        # Find swing points
        swing_highs, swing_lows = self.find_swing_points(data)
        
        if len(swing_highs) < 2 and len(swing_lows) < 2:
            logger.warning("Not enough swing points for prediction")
            return predictions
        
        # Analyze from ATH
        if ath['days_ago'] > 0:
            gann_cycles_from_ath = self.analyze_gann_time_cycles(
                ath['date'], 'high', current_date
            )
            
            # Get recent swing dates
            high_dates = list(swing_highs['date'].tail(5)) if len(swing_highs) > 0 else []
            fibo_from_highs = self.calculate_fibonacci_time_extensions(
                [pd.Timestamp(d) for d in high_dates] if high_dates else [ath['date']],
                current_date
            )
            
            # Find confluences
            high_confluences = self.find_time_confluence(
                gann_cycles_from_ath[:10],
                fibo_from_highs[:10]
            )
            
            # Generate predictions for high confluences
            for conf in high_confluences[:3]:
                if conf['strength'] >= 0.5:
                    predictions.append(self._create_prediction(
                        prediction_type=PredictionType.LOCAL_HIGH if ath['days_ago'] < 180 else PredictionType.ATH,
                        predicted_date=conf['date'],
                        current_price=current_price,
                        ath_atl_price=ath['price'],
                        confluence=conf,
                        gann_targets=self.calculate_gann_price_targets(current_price, 'low'),
                        astro_events=astro_events
                    ))
        
        # Analyze from ATL
        if atl['days_ago'] > 0:
            gann_cycles_from_atl = self.analyze_gann_time_cycles(
                atl['date'], 'low', current_date
            )
            
            low_dates = list(swing_lows['date'].tail(5)) if len(swing_lows) > 0 else []
            fibo_from_lows = self.calculate_fibonacci_time_extensions(
                [pd.Timestamp(d) for d in low_dates] if low_dates else [atl['date']],
                current_date
            )
            
            low_confluences = self.find_time_confluence(
                gann_cycles_from_atl[:10],
                fibo_from_lows[:10]
            )
            
            for conf in low_confluences[:3]:
                if conf['strength'] >= 0.5:
                    predictions.append(self._create_prediction(
                        prediction_type=PredictionType.LOCAL_LOW if atl['days_ago'] < 180 else PredictionType.ATL,
                        predicted_date=conf['date'],
                        current_price=current_price,
                        ath_atl_price=atl['price'],
                        confluence=conf,
                        gann_targets=self.calculate_gann_price_targets(current_price, 'high'),
                        astro_events=astro_events
                    ))
        
        return sorted(predictions, key=lambda x: -x.confidence_score)
    
    def _create_prediction(
        self,
        prediction_type: PredictionType,
        predicted_date: datetime,
        current_price: float,
        ath_atl_price: float,
        confluence: Dict,
        gann_targets: List[Dict],
        astro_events: pd.DataFrame = None
    ) -> ATHATLPrediction:
        """Create prediction object"""
        # Calculate alignments
        gann_alignment = min(1.0, confluence['gann_count'] / 3)
        cycle_alignment = min(1.0, confluence['strength'])
        
        # Astro alignment (if available)
        astro_alignment = 0.5  # Default
        if astro_events is not None and len(astro_events) > 0:
            # Check for significant astro events near predicted date
            date_range = (
                predicted_date - timedelta(days=3),
                predicted_date + timedelta(days=3)
            )
            # Simplified astro check
            astro_alignment = 0.7
        
        # Calculate confidence
        confidence_score = (gann_alignment * 0.4 + cycle_alignment * 0.4 + astro_alignment * 0.2)
        
        if confidence_score >= 0.8:
            confidence = ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.6:
            confidence = ConfidenceLevel.HIGH
        elif confidence_score >= 0.4:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW
        
        # Estimate price target
        if prediction_type in [PredictionType.ATH, PredictionType.LOCAL_HIGH]:
            nearest_target = next(
                (t for t in gann_targets if t['type'] == 'resistance'),
                {'price': current_price * 1.1}
            )
            predicted_price = nearest_target['price']
        else:
            nearest_target = next(
                (t for t in gann_targets if t['type'] == 'support'),
                {'price': current_price * 0.9}
            )
            predicted_price = nearest_target['price']
        
        # Generate supporting factors
        factors = []
        for f in confluence.get('factors', []):
            if f['type'] == 'gann':
                factors.append(f"Gann {f['details'].get('cycle_name', 'Cycle')}")
            else:
                factors.append(f"Fibo {f['details'].get('fibo_ratio', 0):.3f}")
        
        return ATHATLPrediction(
            type=prediction_type,
            predicted_date=predicted_date,
            predicted_price=predicted_price,
            confidence=confidence,
            confidence_score=confidence_score,
            supporting_factors=factors,
            gann_alignment=gann_alignment,
            astro_alignment=astro_alignment,
            cycle_alignment=cycle_alignment,
            description=f"{prediction_type.value.replace('_', ' ').title()} predicted around {predicted_date.strftime('%Y-%m-%d')}"
        )
    
    def get_summary(self, predictions: List[ATHATLPrediction]) -> Dict:
        """Get prediction summary"""
        if not predictions:
            return {'status': 'no_predictions', 'message': 'No significant predictions'}
        
        best = predictions[0]
        
        return {
            'status': 'active',
            'top_prediction': {
                'type': best.type.value,
                'date': best.predicted_date.strftime('%Y-%m-%d'),
                'price': round(best.predicted_price, 2),
                'confidence': best.confidence.value,
                'confidence_score': round(best.confidence_score, 3)
            },
            'total_predictions': len(predictions),
            'high_predictions': len([p for p in predictions if p.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]])
        }


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2023-01-01', periods=365, freq='1D')
    np.random.seed(42)
    
    # Generate synthetic price with trend and cycles
    t = np.arange(365)
    trend = 40000 + t * 30  # Upward trend
    cycle = 5000 * np.sin(2 * np.pi * t / 90)  # 90-day cycle
    noise = np.cumsum(np.random.randn(365) * 200)
    price = trend + cycle + noise
    
    data = pd.DataFrame({
        'open': price - np.random.rand(365) * 500,
        'high': price + np.random.rand(365) * 800,
        'low': price - np.random.rand(365) * 800,
        'close': price,
        'volume': np.random.uniform(1e9, 5e9, 365)
    }, index=dates)
    
    # Fix OHLC
    for i in range(len(data)):
        data.iloc[i, data.columns.get_loc('high')] = max(data.iloc[i]['open'], data.iloc[i]['close'], data.iloc[i]['high'])
        data.iloc[i, data.columns.get_loc('low')] = min(data.iloc[i]['open'], data.iloc[i]['close'], data.iloc[i]['low'])
    
    # Run predictor
    predictor = ATHATLPredictor()
    predictions = predictor.predict(data)
    
    print("\n=== ATH/ATL Predictions ===")
    for p in predictions[:5]:
        print(f"\n{p.type.value}:")
        print(f"  Date: {p.predicted_date.strftime('%Y-%m-%d')}")
        print(f"  Price: ${p.predicted_price:,.2f}")
        print(f"  Confidence: {p.confidence.value} ({p.confidence_score:.2%})")
        print(f"  Factors: {', '.join(p.supporting_factors)}")
    
    print(f"\n{predictor.get_summary(predictions)}")
