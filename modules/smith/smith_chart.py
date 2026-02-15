"""
Smith Chart Module
Financial adaptation of Smith Chart for market analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class SmithPoint:
    """A point on the Smith Chart"""
    normalized_price: float
    phase: float
    gamma: complex
    real_coord: float
    imag_coord: float
    zone: str


class SmithChartAnalyzer:
    """
    Smith Chart adapted for financial market analysis.
    Maps price/momentum to impedance-like coordinates.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.reference_price = None
        self.reference_volatility = None
        logger.info("SmithChartAnalyzer initialized")
    
    def set_reference(self, price: float, volatility: float):
        """Set reference values for normalization."""
        self.reference_price = price
        self.reference_volatility = volatility
    
    def price_to_impedance(
        self,
        price: float,
        momentum: float,
        reference_price: float = None
    ) -> complex:
        """
        Convert price and momentum to normalized impedance.
        Real part: normalized price
        Imaginary part: normalized momentum
        """
        if reference_price is None:
            reference_price = self.reference_price or price
        
        # Normalize price relative to reference
        r = price / reference_price
        
        # Normalize momentum (treat as reactive component)
        x = momentum / 100  # Scale momentum
        
        return complex(r, x)
    
    def impedance_to_gamma(self, z: complex) -> complex:
        """Convert impedance to reflection coefficient (gamma)."""
        # Gamma = (Z - Z0) / (Z + Z0), where Z0 = 1 (normalized)
        if abs(z + 1) < 1e-10:
            return complex(1, 0)
        return (z - 1) / (z + 1)
    
    def gamma_to_smith_coords(self, gamma: complex) -> Tuple[float, float]:
        """Convert gamma to Smith Chart coordinates."""
        return gamma.real, gamma.imag
    
    def get_zone(self, gamma: complex) -> str:
        """Determine which zone of the Smith Chart the point is in."""
        r, x = gamma.real, gamma.imag
        magnitude = abs(gamma)
        
        if magnitude < 0.3:
            return "matched"  # Near center - balanced
        elif r > 0.5:
            return "resistive_high"  # Right side - overbought
        elif r < -0.5:
            return "resistive_low"  # Left side - oversold
        elif x > 0.3:
            return "inductive"  # Upper half - positive momentum
        elif x < -0.3:
            return "capacitive"  # Lower half - negative momentum
        else:
            return "transition"
    
    def analyze_point(
        self,
        price: float,
        momentum: float,
        reference_price: float = None
    ) -> SmithPoint:
        """Analyze a single point on the Smith Chart."""
        if reference_price is None:
            reference_price = self.reference_price or price
        
        z = self.price_to_impedance(price, momentum, reference_price)
        gamma = self.impedance_to_gamma(z)
        real_coord, imag_coord = self.gamma_to_smith_coords(gamma)
        zone = self.get_zone(gamma)
        
        # Calculate phase
        phase = np.degrees(np.angle(gamma))
        
        return SmithPoint(
            normalized_price=z.real,
            phase=round(phase, 2),
            gamma=gamma,
            real_coord=round(real_coord, 4),
            imag_coord=round(imag_coord, 4),
            zone=zone
        )
    
    def analyze_trajectory(
        self,
        data: pd.DataFrame,
        lookback: int = 20
    ) -> Dict:
        """Analyze price trajectory on Smith Chart."""
        if len(data) < lookback:
            return {'error': 'Insufficient data'}
        
        recent = data.tail(lookback)
        
        # Set reference as mean price
        ref_price = float(data['close'].mean())
        self.set_reference(ref_price, float(data['close'].std()))
        
        # Calculate momentum
        momentum = recent['close'].pct_change().rolling(5).mean() * 100
        
        points = []
        for i in range(len(recent)):
            if pd.isna(momentum.iloc[i]):
                continue
            
            point = self.analyze_point(
                float(recent['close'].iloc[i]),
                float(momentum.iloc[i]),
                ref_price
            )
            
            points.append({
                'index': i,
                'price': float(recent['close'].iloc[i]),
                'real': point.real_coord,
                'imag': point.imag_coord,
                'phase': point.phase,
                'zone': point.zone
            })
        
        # Analyze trajectory pattern
        pattern = self._analyze_pattern(points)
        
        return {
            'reference_price': ref_price,
            'points': points,
            'current_zone': points[-1]['zone'] if points else 'unknown',
            'pattern': pattern
        }
    
    def _analyze_pattern(self, points: List[Dict]) -> str:
        """Analyze pattern from trajectory points."""
        if len(points) < 5:
            return 'insufficient_data'
        
        # Check clockwise/counterclockwise rotation
        phases = [p['phase'] for p in points]
        phase_diff = np.diff(phases)
        
        avg_rotation = np.mean(phase_diff)
        
        if avg_rotation > 5:
            return 'expanding'  # Counterclockwise - trending up
        elif avg_rotation < -5:
            return 'contracting'  # Clockwise - trending down
        else:
            return 'stable'  # Minor movements
    
    def get_signal(self, point: SmithPoint) -> Dict:
        """Generate trading signal based on Smith Chart position."""
        zone = point.zone
        magnitude = abs(point.gamma)
        
        if zone == 'matched':
            signal = 'neutral'
            strength = 0.3
            desc = "Market in balance"
        elif zone == 'resistive_high':
            signal = 'sell'
            strength = min(0.9, magnitude)
            desc = "Overbought - possible reversal"
        elif zone == 'resistive_low':
            signal = 'buy'
            strength = min(0.9, magnitude)
            desc = "Oversold - possible reversal"
        elif zone == 'inductive':
            signal = 'hold_long'
            strength = 0.6
            desc = "Positive momentum - hold positions"
        elif zone == 'capacitive':
            signal = 'hold_short'
            strength = 0.6
            desc = "Negative momentum - hold shorts"
        else:
            signal = 'watch'
            strength = 0.4
            desc = "Transition zone - wait for clarity"
        
        return {
            'signal': signal,
            'strength': round(strength, 2),
            'description': desc,
            'zone': zone,
            'phase': point.phase
        }


if __name__ == "__main__":
    analyzer = SmithChartAnalyzer()
    
    # Test single point
    point = analyzer.analyze_point(52000, 2.5, 50000)
    print("\n=== Smith Chart Point ===")
    print(f"Normalized Price: {point.normalized_price}")
    print(f"Gamma: {point.gamma}")
    print(f"Coords: ({point.real_coord}, {point.imag_coord})")
    print(f"Zone: {point.zone}")
    
    signal = analyzer.get_signal(point)
    print(f"\nSignal: {signal['signal']} ({signal['strength']:.0%})")
    print(f"Description: {signal['description']}")
