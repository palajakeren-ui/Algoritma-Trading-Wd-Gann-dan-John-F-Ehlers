"""
Gann Wave Module
Wave analysis and projections
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger


class GannWave:
    """
    Gann Wave Analysis for price projections.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        # Gann wave ratios
        self.ratios = [0.25, 0.333, 0.5, 0.618, 0.667, 0.75, 1.0, 1.25, 1.333, 1.5, 1.618, 2.0]
        logger.info("GannWave initialized")
    
    def project_wave(self, wave_start: float, wave_end: float) -> Dict[str, List[float]]:
        """Project next wave targets based on current wave"""
        wave_size = abs(wave_end - wave_start)
        direction = 1 if wave_end > wave_start else -1
        
        # Continuation targets (same direction)
        continuation = []
        for ratio in self.ratios:
            target = wave_end + (wave_size * ratio * direction)
            continuation.append(round(target, 2))
        
        # Retracement targets (opposite direction)
        retracement = []
        for ratio in [0.25, 0.333, 0.382, 0.5, 0.618, 0.667, 0.75, 1.0]:
            target = wave_end - (wave_size * ratio * direction)
            retracement.append(round(target, 2))
        
        return {
            'continuation': continuation,
            'retracement': retracement,
            'wave_size': round(wave_size, 2),
            'direction': 'up' if direction > 0 else 'down'
        }
    
    def identify_waves(self, df: pd.DataFrame, min_wave_pct: float = 0.05) -> List[Dict]:
        """Identify waves in price data"""
        waves = []
        highs = df['high'].values
        lows = df['low'].values
        
        # Find swing points
        swings = []
        for i in range(2, len(df) - 2):
            if highs[i] > max(highs[i-2:i]) and highs[i] > max(highs[i+1:i+3]):
                swings.append({'index': i, 'type': 'high', 'price': highs[i]})
            if lows[i] < min(lows[i-2:i]) and lows[i] < min(lows[i+1:i+3]):
                swings.append({'index': i, 'type': 'low', 'price': lows[i]})
        
        swings.sort(key=lambda x: x['index'])
        
        # Build waves from swing points
        for i in range(len(swings) - 1):
            s1, s2 = swings[i], swings[i+1]
            wave_pct = abs(s2['price'] - s1['price']) / s1['price']
            
            if wave_pct >= min_wave_pct:
                waves.append({
                    'start_idx': s1['index'],
                    'end_idx': s2['index'],
                    'start_price': s1['price'],
                    'end_price': s2['price'],
                    'direction': 'up' if s2['price'] > s1['price'] else 'down',
                    'size_pct': round(wave_pct * 100, 2),
                    'bars': s2['index'] - s1['index']
                })
        
        return waves
    
    def calculate_wave_harmony(self, waves: List[Dict]) -> float:
        """Calculate wave harmony score"""
        if len(waves) < 2:
            return 0.5
        
        # Compare consecutive wave ratios to ideal Gann ratios
        harmony_scores = []
        
        for i in range(len(waves) - 1):
            w1_size = abs(waves[i]['end_price'] - waves[i]['start_price'])
            w2_size = abs(waves[i+1]['end_price'] - waves[i+1]['start_price'])
            
            if w1_size > 0:
                ratio = w2_size / w1_size
                # Find closest Gann ratio
                closest = min(self.ratios, key=lambda x: abs(x - ratio))
                deviation = abs(ratio - closest)
                harmony = max(0, 1 - deviation)
                harmony_scores.append(harmony)
        
        return sum(harmony_scores) / len(harmony_scores) if harmony_scores else 0.5
