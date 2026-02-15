"""
Options Greeks Calculator Module
Complete Greeks calculation for options
"""
import numpy as np
from scipy.stats import norm
from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class OptionGreeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class GreeksCalculator:
    """Calculates option Greeks using Black-Scholes model."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("GreeksCalculator initialized")
    
    def _d1(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 for Black-Scholes."""
        if T <= 0 or sigma <= 0:
            return 0
        return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    
    def _d2(self, d1: float, sigma: float, T: float) -> float:
        """Calculate d2 for Black-Scholes."""
        if T <= 0:
            return 0
        return d1 - sigma * np.sqrt(T)
    
    def calculate_greeks(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        option_type: str = 'call'
    ) -> OptionGreeks:
        """
        Calculate all Greeks for an option.
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annualized)
            risk_free_rate: Risk-free rate
            option_type: 'call' or 'put'
        """
        S, K, T, r, sigma = spot, strike, time_to_expiry, risk_free_rate, volatility
        
        if T <= 0:
            # Expired option
            if option_type == 'call':
                return OptionGreeks(1 if S > K else 0, 0, 0, 0, 0)
            else:
                return OptionGreeks(-1 if S < K else 0, 0, 0, 0, 0)
        
        d1 = self._d1(S, K, T, r, sigma)
        d2 = self._d2(d1, sigma, T)
        
        # Delta
        if option_type == 'call':
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        # Gamma (same for call and put)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta
        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        if option_type == 'call':
            theta = term1 - r * K * np.exp(-r * T) * norm.cdf(d2)
        else:
            theta = term1 + r * K * np.exp(-r * T) * norm.cdf(-d2)
        theta = theta / 365  # Convert to daily
        
        # Vega (same for call and put)
        vega = S * np.sqrt(T) * norm.pdf(d1) / 100  # Per 1% IV change
        
        # Rho
        if option_type == 'call':
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        return OptionGreeks(
            delta=round(delta, 4),
            gamma=round(gamma, 6),
            theta=round(theta, 4),
            vega=round(vega, 4),
            rho=round(rho, 4)
        )
    
    def calculate_all(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float
    ) -> Dict:
        """Calculate Greeks for both call and put."""
        call = self.calculate_greeks(spot, strike, time_to_expiry, volatility, risk_free_rate, 'call')
        put = self.calculate_greeks(spot, strike, time_to_expiry, volatility, risk_free_rate, 'put')
        
        return {
            'call': {
                'delta': call.delta,
                'gamma': call.gamma,
                'theta': call.theta,
                'vega': call.vega,
                'rho': call.rho
            },
            'put': {
                'delta': put.delta,
                'gamma': put.gamma,
                'theta': put.theta,
                'vega': put.vega,
                'rho': put.rho
            }
        }
    
    def portfolio_greeks(self, positions: list) -> OptionGreeks:
        """Calculate aggregate Greeks for a portfolio of options."""
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        
        for pos in positions:
            greeks = self.calculate_greeks(
                pos['spot'], pos['strike'], pos['time_to_expiry'],
                pos['volatility'], pos['risk_free_rate'], pos['option_type']
            )
            quantity = pos.get('quantity', 1)
            
            total_delta += greeks.delta * quantity
            total_gamma += greeks.gamma * quantity
            total_theta += greeks.theta * quantity
            total_vega += greeks.vega * quantity
            total_rho += greeks.rho * quantity
        
        return OptionGreeks(
            delta=round(total_delta, 4),
            gamma=round(total_gamma, 6),
            theta=round(total_theta, 4),
            vega=round(total_vega, 4),
            rho=round(total_rho, 4)
        )


if __name__ == "__main__":
    calc = GreeksCalculator()
    
    # Test single option
    greeks = calc.calculate_greeks(
        spot=50000,
        strike=52000,
        time_to_expiry=30/365,
        volatility=0.6,
        risk_free_rate=0.05,
        option_type='call'
    )
    
    print("\n=== Call Option Greeks ===")
    print(f"Delta: {greeks.delta}")
    print(f"Gamma: {greeks.gamma}")
    print(f"Theta: {greeks.theta}")
    print(f"Vega: {greeks.vega}")
    print(f"Rho: {greeks.rho}")
