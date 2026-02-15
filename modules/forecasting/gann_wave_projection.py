"""
Gann Wave Projection Module
Projects future price movements using Gann wave analysis
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class WaveType(Enum):
    IMPULSE = "impulse"
    CORRECTIVE = "corrective"
    EXTENSION = "extension"
    CONSOLIDATION = "consolidation"


class WaveDirection(Enum):
    UP = "up"
    DOWN = "down"


@dataclass
class GannWave:
    wave_number: int
    wave_type: WaveType
    direction: WaveDirection
    start_price: float
    end_price: float
    start_date: datetime
    end_date: datetime
    duration_bars: int
    price_change: float
    price_change_pct: float


class GannWaveAnalyzer:
    GANN_RATIOS = [0.25, 0.333, 0.5, 0.618, 0.667, 0.75, 1.0, 1.25, 1.5, 1.618, 2.0]
    TIME_RATIOS = [0.5, 0.618, 1.0, 1.272, 1.618, 2.0]
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.swing_threshold = self.config.get('swing_threshold', 0.03)
        logger.info("GannWaveAnalyzer initialized")
    
    def identify_swings(self, data: pd.DataFrame) -> List[Dict]:
        swings = []
        n = len(data)
        if n < 5:
            return swings
        
        for i in range(2, n - 2):
            high = float(data.iloc[i]['high'])
            low = float(data.iloc[i]['low'])
            
            if (high >= data.iloc[i-1]['high'] and high >= data.iloc[i+1]['high']):
                swings.append({'index': i, 'date': data.index[i], 'price': high, 'type': 'high'})
            
            if (low <= data.iloc[i-1]['low'] and low <= data.iloc[i+1]['low']):
                swings.append({'index': i, 'date': data.index[i], 'price': low, 'type': 'low'})
        
        filtered = [swings[0]] if swings else []
        for swing in swings[1:]:
            last = filtered[-1]
            pct = abs(swing['price'] - last['price']) / last['price']
            if pct >= self.swing_threshold and swing['type'] != last['type']:
                filtered.append(swing)
        
        return filtered
    
    def identify_waves(self, swings: List[Dict]) -> List[GannWave]:
        waves = []
        for i in range(len(swings) - 1):
            start, end = swings[i], swings[i + 1]
            direction = WaveDirection.UP if end['price'] > start['price'] else WaveDirection.DOWN
            change = end['price'] - start['price']
            pct = change / start['price'] * 100
            duration = end['index'] - start['index']
            wave_type = WaveType.IMPULSE if abs(pct) > 5 else WaveType.CONSOLIDATION
            
            start_dt = start['date'].to_pydatetime() if hasattr(start['date'], 'to_pydatetime') else start['date']
            end_dt = end['date'].to_pydatetime() if hasattr(end['date'], 'to_pydatetime') else end['date']
            
            waves.append(GannWave(
                wave_number=len(waves) + 1, wave_type=wave_type, direction=direction,
                start_price=start['price'], end_price=end['price'],
                start_date=start_dt, end_date=end_dt,
                duration_bars=duration, price_change=change, price_change_pct=pct
            ))
        return waves
    
    def project_next_wave(self, waves: List[GannWave], current_price: float) -> Dict:
        if not waves:
            return {}
        
        last = waves[-1]
        direction = WaveDirection.DOWN if last.direction == WaveDirection.UP else WaveDirection.UP
        avg_move = np.mean([abs(w.price_change) for w in waves])
        avg_duration = int(np.mean([w.duration_bars for w in waves]))
        
        if direction == WaveDirection.UP:
            targets = [current_price + avg_move * r for r in [0.5, 1.0, 1.618]]
        else:
            targets = [current_price - avg_move * r for r in [0.5, 1.0, 1.618]]
        
        return {
            'wave_number': last.wave_number + 1,
            'direction': direction.value,
            'current_price': current_price,
            'target_1': round(targets[0], 2),
            'target_2': round(targets[1], 2),
            'target_3': round(targets[2], 2),
            'expected_duration': avg_duration,
            'confidence': 0.65
        }
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        swings = self.identify_swings(data)
        if len(swings) < 2:
            return {'status': 'insufficient_data'}
        
        waves = self.identify_waves(swings)
        current_price = float(data.iloc[-1]['close'])
        projection = self.project_next_wave(waves, current_price)
        
        return {
            'status': 'success',
            'wave_count': len(waves),
            'waves': [{'number': w.wave_number, 'direction': w.direction.value, 
                       'change_pct': round(w.price_change_pct, 2)} for w in waves],
            'projection': projection
        }
