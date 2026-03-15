"""
Time Recommender Module
Recommend optimal trading times
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class TimeRecommender:
    """
    Recommend optimal trading times based on analysis.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("TimeRecommender initialized")
    
    def get_recommendations(
        self,
        symbol: str,
        df: pd.DataFrame,
        analysis_type: str = 'all'
    ) -> List[Dict]:
        """Get time-based trading recommendations"""
        recommendations = []
        
        if analysis_type in ['all', 'volatility']:
            vol_recs = self._volatility_timing(df)
            recommendations.extend(vol_recs)
        
        if analysis_type in ['all', 'session']:
            session_recs = self._session_timing(symbol)
            recommendations.extend(session_recs)
        
        if analysis_type in ['all', 'cycle']:
            cycle_recs = self._cycle_timing(df)
            recommendations.extend(cycle_recs)
        
        return recommendations
    
    def _volatility_timing(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze volatility patterns for timing"""
        recs = []
        
        if 'hour' not in df.columns and hasattr(df.index, 'hour'):
            df = df.copy()
            df['hour'] = df.index.hour
        elif 'hour' not in df.columns:
            return []
        
        # Calculate hourly volatility
        hourly_vol = df.groupby('hour')['close'].apply(
            lambda x: x.pct_change().std()
        ).sort_values(ascending=False)
        
        # High volatility hours
        high_vol_hours = hourly_vol.head(3).index.tolist()
        low_vol_hours = hourly_vol.tail(3).index.tolist()
        
        recs.append({
            'type': 'volatility',
            'recommendation': 'High volatility trading',
            'hours': high_vol_hours,
            'reason': 'Best for momentum strategies'
        })
        
        recs.append({
            'type': 'volatility',
            'recommendation': 'Low volatility trading',
            'hours': low_vol_hours,
            'reason': 'Best for mean reversion'
        })
        
        return recs
    
    def _session_timing(self, symbol: str) -> List[Dict]:
        """Get session-based timing recommendations"""
        recs = []
        
        # Market sessions (UTC)
        sessions = {
            'asian': {'start': 0, 'end': 8, 'desc': 'Asian Session'},
            'london': {'start': 8, 'end': 16, 'desc': 'London Session'},
            'new_york': {'start': 13, 'end': 21, 'desc': 'New York Session'},
            'overlap': {'start': 13, 'end': 16, 'desc': 'London-NY Overlap'}
        }
        
        # Crypto is 24/7
        if symbol.upper() in ['BTC', 'ETH', 'BTCUSD', 'ETHUSD']:
            recs.append({
                'type': 'session',
                'recommendation': 'London-NY overlap',
                'hours': list(range(13, 17)),
                'reason': 'Highest liquidity period'
            })
        else:
            recs.append({
                'type': 'session',
                'recommendation': 'Primary market hours',
                'hours': list(range(9, 16)),
                'reason': 'Regular trading hours'
            })
        
        return recs
    
    def _cycle_timing(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze cycles for timing"""
        recs = []
        close = df['close']
        
        # Weekly pattern
        if hasattr(df.index, 'dayofweek'):
            daily_returns = close.pct_change()
            df_temp = pd.DataFrame({'returns': daily_returns, 'dow': df.index.dayofweek})
            
            avg_by_day = df_temp.groupby('dow')['returns'].mean()
            
            best_day = avg_by_day.idxmax()
            worst_day = avg_by_day.idxmin()
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            recs.append({
                'type': 'weekly_cycle',
                'recommendation': f'Best day: {day_names[best_day]}',
                'day_of_week': best_day,
                'avg_return': float(avg_by_day[best_day]),
                'reason': 'Historically strongest day'
            })
            
            recs.append({
                'type': 'weekly_cycle',
                'recommendation': f'Weakest day: {day_names[worst_day]}',
                'day_of_week': worst_day,
                'avg_return': float(avg_by_day[worst_day]),
                'reason': 'Historically weakest day'
            })
        
        return recs
    
    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming market events"""
        events = []
        today = datetime.now()
        
        # Options expiration (3rd Friday)
        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            if check_date.weekday() == 4:  # Friday
                day_of_month = check_date.day
                if 15 <= day_of_month <= 21:  # 3rd week
                    events.append({
                        'date': check_date.strftime('%Y-%m-%d'),
                        'event': 'Options Expiration',
                        'impact': 'high',
                        'recommendation': 'Expect increased volatility'
                    })
        
        # Month end
        next_month = (today.month % 12) + 1
        if next_month == 1:
            year = today.year + 1
        else:
            year = today.year
        
        month_end = datetime(year if next_month != 1 else today.year, 
                            next_month if next_month != 1 else 12, 1) - timedelta(days=1)
        
        if (month_end - today).days <= days_ahead:
            events.append({
                'date': month_end.strftime('%Y-%m-%d'),
                'event': 'Month End Rebalancing',
                'impact': 'medium',
                'recommendation': 'Window dressing trades possible'
            })
        
        return events
