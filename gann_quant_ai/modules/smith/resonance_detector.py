"""
Resonance Detector Module
Detects market resonance patterns (price harmonics)
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class ResonancePoint:
    frequency: float
    amplitude: float
    phase: float
    quality_factor: float
    is_resonant: bool


class ResonanceDetector:
    """Detects resonance patterns in market data."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.q_threshold = self.config.get('q_threshold', 5)
        logger.info("ResonanceDetector initialized")
    
    def calculate_fft(self, data: pd.Series) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate FFT of price data."""
        n = len(data)
        
        # Detrend
        trend = np.polyfit(np.arange(n), data.values, 1)
        detrended = data.values - (trend[0] * np.arange(n) + trend[1])
        
        # Apply window
        windowed = detrended * np.hanning(n)
        
        # FFT
        fft_result = np.fft.fft(windowed)
        frequencies = np.fft.fftfreq(n)
        amplitudes = np.abs(fft_result) / n
        phases = np.angle(fft_result)
        
        return frequencies[:n//2], amplitudes[:n//2], phases[:n//2]
    
    def find_resonances(
        self,
        data: pd.DataFrame,
        min_period: int = 5,
        max_period: int = 100
    ) -> List[ResonancePoint]:
        """Find resonance points (dominant frequencies)."""
        close = data['close']
        freqs, amps, phases = self.calculate_fft(close)
        
        resonances = []
        n = len(close)
        
        for i in range(1, len(freqs)):
            if freqs[i] <= 0:
                continue
            
            period = 1 / freqs[i]
            
            if min_period <= period <= max_period:
                # Check if local maximum
                if i > 0 and i < len(amps) - 1:
                    if amps[i] > amps[i-1] and amps[i] > amps[i+1]:
                        # Calculate Q factor (sharpness)
                        bandwidth = self._estimate_bandwidth(amps, i)
                        q = freqs[i] / bandwidth if bandwidth > 0 else 0
                        
                        resonances.append(ResonancePoint(
                            frequency=float(freqs[i]),
                            amplitude=float(amps[i]),
                            phase=float(np.degrees(phases[i])),
                            quality_factor=round(q, 2),
                            is_resonant=q > self.q_threshold
                        ))
        
        # Sort by amplitude
        resonances.sort(key=lambda x: -x.amplitude)
        
        return resonances[:10]  # Top 10
    
    def _estimate_bandwidth(self, amps: np.ndarray, peak_idx: int) -> float:
        """Estimate bandwidth at -3dB points."""
        peak_amp = amps[peak_idx]
        threshold = peak_amp / np.sqrt(2)
        
        # Find left edge
        left = peak_idx
        while left > 0 and amps[left] > threshold:
            left -= 1
        
        # Find right edge
        right = peak_idx
        while right < len(amps) - 1 and amps[right] > threshold:
            right += 1
        
        return (right - left) / len(amps)
    
    def detect_harmonic_series(
        self,
        resonances: List[ResonancePoint]
    ) -> Dict:
        """Detect if resonances form a harmonic series."""
        if len(resonances) < 2:
            return {'is_harmonic': False}
        
        # Sort by frequency
        sorted_res = sorted(resonances, key=lambda x: x.frequency)
        
        fundamental = sorted_res[0].frequency
        
        harmonics = []
        for res in sorted_res[1:]:
            ratio = res.frequency / fundamental
            nearest_int = round(ratio)
            
            if abs(ratio - nearest_int) < 0.1 and nearest_int > 1:
                harmonics.append({
                    'frequency': res.frequency,
                    'harmonic_number': nearest_int,
                    'amplitude': res.amplitude
                })
        
        is_harmonic = len(harmonics) >= 2
        
        return {
            'is_harmonic': is_harmonic,
            'fundamental_freq': fundamental,
            'fundamental_period': 1 / fundamental if fundamental > 0 else 0,
            'harmonics': harmonics
        }
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """Complete resonance analysis."""
        resonances = self.find_resonances(data)
        
        if not resonances:
            return {
                'status': 'no_resonances',
                'resonances': []
            }
        
        harmonic_analysis = self.detect_harmonic_series(resonances)
        
        # Get strongest resonance
        strongest = resonances[0]
        
        return {
            'status': 'success',
            'resonance_count': len(resonances),
            'dominant_resonance': {
                'period': 1 / strongest.frequency if strongest.frequency > 0 else 0,
                'amplitude': strongest.amplitude,
                'q_factor': strongest.quality_factor,
                'phase': strongest.phase
            },
            'resonances': [
                {
                    'period': 1 / r.frequency if r.frequency > 0 else 0,
                    'amplitude': r.amplitude,
                    'q_factor': r.quality_factor,
                    'is_resonant': r.is_resonant
                }
                for r in resonances
            ],
            'harmonic_analysis': harmonic_analysis
        }
    
    def get_resonance_signal(self, resonances: List[ResonancePoint]) -> Dict:
        """Generate signal based on resonance analysis."""
        if not resonances:
            return {'signal': 'neutral', 'strength': 0}
        
        strongest = resonances[0]
        
        if not strongest.is_resonant:
            return {
                'signal': 'neutral',
                'strength': 0.3,
                'description': 'No strong resonance detected'
            }
        
        phase = strongest.phase
        
        if -45 <= phase <= 45:
            signal = 'buy'
            desc = "Bullish resonance phase"
        elif 135 <= phase or phase <= -135:
            signal = 'sell'
            desc = "Bearish resonance phase"
        else:
            signal = 'watch'
            desc = "Transition phase"
        
        strength = min(0.9, strongest.quality_factor / 20)
        
        return {
            'signal': signal,
            'strength': round(strength, 2),
            'description': desc,
            'dominant_period': round(1 / strongest.frequency, 1) if strongest.frequency > 0 else 0
        }





if __name__ == "__main__":
    # Test
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1D')
    np.random.seed(42)
    
    t = np.arange(200)
    cycle1 = 1000 * np.sin(2 * np.pi * t / 30)  # 30-day cycle
    cycle2 = 500 * np.sin(2 * np.pi * t / 60)   # 60-day cycle
    trend = 50000 + t * 10
    noise = np.cumsum(np.random.randn(200) * 50)
    
    prices = trend + cycle1 + cycle2 + noise
    
    data = pd.DataFrame({
        'open': prices * 0.998,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 200)
    }, index=dates)
    
    detector = ResonanceDetector()
    result = detector.analyze(data)
    
    print("\n=== Resonance Analysis ===")
    print(f"Resonances found: {result['resonance_count']}")
    
    if result.get('dominant_resonance'):
        dom = result['dominant_resonance']
        print(f"\nDominant Resonance:")
        print(f"  Period: {dom['period']:.1f} days")
        print(f"  Q Factor: {dom['q_factor']}")
        print(f"  Phase: {dom['phase']:.0f}°")
