"""
Options Pricer Module
Black-Scholes and other options pricing models
"""
import numpy as np
from scipy.stats import norm
from typing import Dict, Optional, Tuple
from loguru import logger


class OptionsPricer:
    """
    Options pricing using various models.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("OptionsPricer initialized")
    
    def black_scholes(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        option_type: str = 'call'
    ) -> Dict:
        """
        Black-Scholes option pricing.
        
        Args:
            spot: Current price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annualized)
            risk_free_rate: Risk-free interest rate
            option_type: 'call' or 'put'
        """
        if time_to_expiry <= 0:
            # Expired option - intrinsic value only
            if option_type == 'call':
                return {'price': max(0, spot - strike), 'delta': 1 if spot > strike else 0}
            else:
                return {'price': max(0, strike - spot), 'delta': -1 if spot < strike else 0}
        
        d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / \
             (volatility * np.sqrt(time_to_expiry))
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        if option_type == 'call':
            price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
            delta = norm.cdf(d1)
        else:
            price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)
            delta = norm.cdf(d1) - 1
        
        # Greeks
        gamma = norm.pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))
        theta = -(spot * norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry)) - \
                risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * \
                (norm.cdf(d2) if option_type == 'call' else norm.cdf(-d2))
        vega = spot * np.sqrt(time_to_expiry) * norm.pdf(d1) / 100  # Per 1% IV change
        
        return {
            'price': round(price, 4),
            'delta': round(delta, 4),
            'gamma': round(gamma, 6),
            'theta': round(theta / 365, 4),  # Per day
            'vega': round(vega, 4),
            'd1': round(d1, 4),
            'd2': round(d2, 4)
        }
    
    def implied_volatility(
        self,
        option_price: float,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        option_type: str = 'call',
        precision: float = 0.0001
    ) -> Optional[float]:
        """Calculate implied volatility using Newton-Raphson"""
        iv = 0.5  # Initial guess
        
        for _ in range(100):
            result = self.black_scholes(spot, strike, time_to_expiry, iv, risk_free_rate, option_type)
            price_diff = result['price'] - option_price
            
            if abs(price_diff) < precision:
                return round(iv, 4)
            
            vega = result['vega'] * 100  # Convert back
            if vega == 0:
                break
            
            iv -= price_diff / vega
            iv = max(0.01, min(5.0, iv))  # Clamp
        
        return None
    
    def binomial_tree(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        option_type: str = 'call',
        american: bool = True,
        steps: int = 100
    ) -> float:
        """
        Binomial tree pricing (supports American options).
        """
        dt = time_to_expiry / steps
        u = np.exp(volatility * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(risk_free_rate * dt) - d) / (u - d)
        discount = np.exp(-risk_free_rate * dt)
        
        # Build price tree
        prices = np.zeros(steps + 1)
        for i in range(steps + 1):
            prices[i] = spot * (u ** (steps - i)) * (d ** i)
        
        # Option values at expiry
        if option_type == 'call':
            values = np.maximum(prices - strike, 0)
        else:
            values = np.maximum(strike - prices, 0)
        
        # Backward induction
        for step in range(steps - 1, -1, -1):
            for i in range(step + 1):
                values[i] = (p * values[i] + (1 - p) * values[i + 1]) * discount
                
                if american:
                    price_at_node = spot * (u ** (step - i)) * (d ** i)
                    if option_type == 'call':
                        intrinsic = max(price_at_node - strike, 0)
                    else:
                        intrinsic = max(strike - price_at_node, 0)
                    values[i] = max(values[i], intrinsic)
        
        return round(values[0], 4)
    
    def put_call_parity(self, call_price: float, spot: float, strike: float,
                        time_to_expiry: float, risk_free_rate: float) -> float:
        """Calculate put price from call using put-call parity"""
        return call_price - spot + strike * np.exp(-risk_free_rate * time_to_expiry)
