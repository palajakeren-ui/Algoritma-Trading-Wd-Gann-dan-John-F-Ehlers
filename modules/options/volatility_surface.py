"""
Volatility Surface Module
Constructs and analyzes implied volatility surfaces
"""
import numpy as np
from scipy.stats import norm
from scipy.interpolate import RectBivariateSpline
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class VolatilitySurfacePoint:
    strike: float
    time_to_expiry: float
    implied_volatility: float
    delta: float
    moneyness: float


class VolatilitySurface:
    """Constructs and analyzes implied volatility surfaces."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.surface = None
        self.strikes = None
        self.expiries = None
        logger.info("VolatilitySurface initialized")
    
    def calculate_implied_volatility(
        self,
        option_price: float,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        option_type: str = 'call'
    ) -> Optional[float]:
        """Calculate implied volatility using Newton-Raphson."""
        iv = 0.5  # Initial guess
        
        for _ in range(100):
            price, vega = self._bs_price_and_vega(
                spot, strike, time_to_expiry, iv, risk_free_rate, option_type
            )
            
            diff = price - option_price
            
            if abs(diff) < 0.0001:
                return iv
            
            if vega == 0:
                break
            
            iv -= diff / vega
            iv = max(0.01, min(5.0, iv))
        
        return None
    
    def _bs_price_and_vega(
        self,
        S: float, K: float, T: float, sigma: float, r: float, opt_type: str
    ) -> Tuple[float, float]:
        """Calculate Black-Scholes price and vega."""
        if T <= 0 or sigma <= 0:
            return (0, 0)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if opt_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        vega = S * np.sqrt(T) * norm.pdf(d1)
        
        return price, vega
    
    def build_surface(
        self,
        options_data: List[Dict],
        spot: float,
        risk_free_rate: float = 0.05
    ) -> bool:
        """
        Build volatility surface from options data.
        
        Args:
            options_data: List of dicts with strike, expiry, price, type
            spot: Current spot price
        """
        points = []
        
        for opt in options_data:
            iv = self.calculate_implied_volatility(
                opt['price'], spot, opt['strike'], opt['expiry'],
                risk_free_rate, opt.get('type', 'call')
            )
            
            if iv is not None:
                moneyness = opt['strike'] / spot
                points.append({
                    'strike': opt['strike'],
                    'expiry': opt['expiry'],
                    'iv': iv,
                    'moneyness': moneyness
                })
        
        if len(points) < 4:
            logger.warning("Insufficient data points for surface")
            return False
        
        # Store surface data
        self.strikes = sorted(set(p['strike'] for p in points))
        self.expiries = sorted(set(p['expiry'] for p in points))
        
        # Create surface matrix
        iv_matrix = np.zeros((len(self.strikes), len(self.expiries)))
        
        for p in points:
            i = self.strikes.index(p['strike'])
            j = self.expiries.index(p['expiry'])
            iv_matrix[i, j] = p['iv']
        
        # Fill zeros with interpolation
        iv_matrix = self._fill_surface(iv_matrix)
        
        # Create interpolator
        try:
            self.surface = RectBivariateSpline(
                self.strikes, self.expiries, iv_matrix
            )
        except:
            self.surface = None
            return False
        
        return True
    
    def _fill_surface(self, matrix: np.ndarray) -> np.ndarray:
        """Fill missing values in surface."""
        # Simple fill with neighbors
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if matrix[i, j] == 0:
                    neighbors = []
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            ni, nj = i + di, j + dj
                            if 0 <= ni < matrix.shape[0] and 0 <= nj < matrix.shape[1]:
                                if matrix[ni, nj] > 0:
                                    neighbors.append(matrix[ni, nj])
                    if neighbors:
                        matrix[i, j] = np.mean(neighbors)
                    else:
                        matrix[i, j] = 0.3  # Default IV
        
        return matrix
    
    def get_iv(self, strike: float, expiry: float) -> float:
        """Get interpolated IV for given strike and expiry."""
        if self.surface is None:
            return 0.3
        
        try:
            return float(self.surface(strike, expiry)[0, 0])
        except:
            return 0.3
    
    def get_term_structure(self, strike: float) -> Dict:
        """Get term structure of volatility for a strike."""
        if self.surface is None or self.expiries is None:
            return {}
        
        ivs = []
        for exp in self.expiries:
            ivs.append({
                'expiry': exp,
                'iv': self.get_iv(strike, exp)
            })
        
        return {
            'strike': strike,
            'term_structure': ivs
        }
    
    def get_skew(self, expiry: float, spot: float) -> Dict:
        """Get volatility skew for an expiry."""
        if self.surface is None or self.strikes is None:
            return {}
        
        skew_data = []
        for strike in self.strikes:
            moneyness = strike / spot
            iv = self.get_iv(strike, expiry)
            skew_data.append({
                'strike': strike,
                'moneyness': round(moneyness, 3),
                'iv': round(iv * 100, 2)
            })
        
        return {
            'expiry': expiry,
            'skew': skew_data
        }
    
    def analyze_surface(self, spot: float) -> Dict:
        """Perform complete surface analysis."""
        if self.surface is None:
            return {'error': 'Surface not built'}
        
        atm_iv = self.get_iv(spot, self.expiries[0] if self.expiries else 0.1)
        
        # Calculate skew measures
        if self.strikes and len(self.strikes) > 2:
            otm_put_strike = min(self.strikes, key=lambda x: abs(x - spot * 0.9))
            otm_call_strike = min(self.strikes, key=lambda x: abs(x - spot * 1.1))
            
            put_iv = self.get_iv(otm_put_strike, self.expiries[0])
            call_iv = self.get_iv(otm_call_strike, self.expiries[0])
            
            skew = put_iv - call_iv
        else:
            skew = 0
        
        return {
            'atm_iv': round(atm_iv * 100, 2),
            'skew': round(skew * 100, 2),
            'strikes_count': len(self.strikes) if self.strikes else 0,
            'expiries_count': len(self.expiries) if self.expiries else 0
        }


if __name__ == "__main__":
    surface = VolatilitySurface()
    
    # Mock options data
    options_data = [
        {'strike': 48000, 'expiry': 0.1, 'price': 3500, 'type': 'call'},
        {'strike': 50000, 'expiry': 0.1, 'price': 2000, 'type': 'call'},
        {'strike': 52000, 'expiry': 0.1, 'price': 800, 'type': 'call'},
        {'strike': 48000, 'expiry': 0.25, 'price': 4500, 'type': 'call'},
        {'strike': 50000, 'expiry': 0.25, 'price': 3000, 'type': 'call'},
        {'strike': 52000, 'expiry': 0.25, 'price': 1800, 'type': 'call'},
    ]
    
    success = surface.build_surface(options_data, 50000)
    
    if success:
        print("\n=== Volatility Surface ===")
        analysis = surface.analyze_surface(50000)
        print(f"ATM IV: {analysis['atm_iv']}%")
        print(f"Skew: {analysis['skew']}%")
    else:
        print("Failed to build surface")
