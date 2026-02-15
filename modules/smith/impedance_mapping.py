"""
Impedance Mapping Module
Maps financial metrics to impedance-like values
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class ImpedanceReading:
    resistance: float  # Real component (price relative)
    reactance: float   # Imaginary component (momentum/volatility)
    magnitude: float
    phase: float
    vswr: float  # Volatility Standing Wave Ratio


class ImpedanceMapper:
    """Maps financial data to impedance representations."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("ImpedanceMapper initialized")
    
    def calculate_price_impedance(
        self,
        current_price: float,
        reference_price: float,
        momentum: float
    ) -> ImpedanceReading:
        """
        Calculate price impedance.
        
        Args:
            current_price: Current price
            reference_price: Reference/average price
            momentum: Price momentum (rate of change)
        """
        # Resistance = normalized price
        r = current_price / reference_price
        
        # Reactance = momentum component
        x = momentum * 10  # Scale for visibility
        
        # Complex impedance
        z = complex(r, x)
        
        magnitude = abs(z)
        phase = np.degrees(np.arctan2(x, r))
        
        # VSWR - inspired calculation for volatility
        gamma = abs((z - 1) / (z + 1)) if abs(z + 1) > 0.001 else 1
        vswr = (1 + gamma) / (1 - gamma) if gamma < 0.99 else float('inf')
        
        return ImpedanceReading(
            resistance=round(r, 4),
            reactance=round(x, 4),
            magnitude=round(magnitude, 4),
            phase=round(phase, 2),
            vswr=round(vswr, 2) if vswr != float('inf') else 999
        )
    
    def calculate_volatility_impedance(
        self,
        current_vol: float,
        avg_vol: float,
        vol_trend: float
    ) -> ImpedanceReading:
        """Calculate volatility-based impedance."""
        r = current_vol / avg_vol if avg_vol > 0 else 1
        x = vol_trend * 20
        
        z = complex(r, x)
        magnitude = abs(z)
        phase = np.degrees(np.arctan2(x, r))
        
        gamma = abs((z - 1) / (z + 1)) if abs(z + 1) > 0.001 else 1
        vswr = (1 + gamma) / (1 - gamma) if gamma < 0.99 else float('inf')
        
        return ImpedanceReading(
            resistance=round(r, 4),
            reactance=round(x, 4),
            magnitude=round(magnitude, 4),
            phase=round(phase, 2),
            vswr=round(vswr, 2) if vswr != float('inf') else 999
        )
    
    def map_ohlcv(self, data: pd.DataFrame, lookback: int = 20) -> Dict:
        """Map OHLCV data to impedance values."""
        if len(data) < lookback:
            return {'error': 'Insufficient data'}
        
        recent = data.tail(lookback)
        
        # Calculate reference values
        ref_price = float(data['close'].rolling(lookback).mean().iloc[-1])
        
        # Calculate momentum
        momentum = float((data['close'].iloc[-1] / data['close'].iloc[-5] - 1) * 100)
        
        # Price impedance
        price_z = self.calculate_price_impedance(
            float(data['close'].iloc[-1]),
            ref_price,
            momentum
        )
        
        # Volatility
        returns = data['close'].pct_change()
        current_vol = float(returns.tail(5).std())
        avg_vol = float(returns.rolling(lookback).std().iloc[-1])
        vol_trend = float((current_vol - avg_vol) / avg_vol) if avg_vol > 0 else 0
        
        vol_z = self.calculate_volatility_impedance(current_vol, avg_vol, vol_trend)
        
        return {
            'price_impedance': {
                'resistance': price_z.resistance,
                'reactance': price_z.reactance,
                'magnitude': price_z.magnitude,
                'phase': price_z.phase,
                'vswr': price_z.vswr
            },
            'volatility_impedance': {
                'resistance': vol_z.resistance,
                'reactance': vol_z.reactance,
                'magnitude': vol_z.magnitude,
                'phase': vol_z.phase,
                'vswr': vol_z.vswr
            },
            'reference_price': ref_price,
            'current_price': float(data['close'].iloc[-1]),
            'momentum': momentum
        }
    
    def get_matching_condition(self, reading: ImpedanceReading) -> str:
        """Determine market matching condition."""
        r = reading.resistance
        x = abs(reading.reactance)
        
        if 0.9 <= r <= 1.1 and x < 0.1:
            return "matched"  # Perfect balance
        elif r > 1.5:
            return "overextended"  # Price too high
        elif r < 0.7:
            return "undervalued"  # Price too low
        elif x > 0.5:
            return "reactive"  # High momentum
        else:
            return "slight_mismatch"
    
    def calculate_reflection_loss(self, reading: ImpedanceReading) -> float:
        """Calculate equivalent of reflection loss (potential reversal strength)."""
        gamma = abs(complex(reading.resistance - 1, reading.reactance) / 
                   complex(reading.resistance + 1, reading.reactance))
        
        if gamma >= 1:
            return 0
        
        return_loss = -20 * np.log10(gamma) if gamma > 0.001 else 60
        return round(return_loss, 2)


if __name__ == "__main__":
    mapper = ImpedanceMapper()
    
    # Test
    reading = mapper.calculate_price_impedance(52000, 50000, 2.5)
    
    print("\n=== Price Impedance ===")
    print(f"Resistance: {reading.resistance}")
    print(f"Reactance: {reading.reactance}")
    print(f"Magnitude: {reading.magnitude}")
    print(f"Phase: {reading.phase}°")
    print(f"VSWR: {reading.vswr}")
    
    condition = mapper.get_matching_condition(reading)
    print(f"\nCondition: {condition}")
    
    reflection_loss = mapper.calculate_reflection_loss(reading)
    print(f"Reflection Loss: {reflection_loss} dB")
