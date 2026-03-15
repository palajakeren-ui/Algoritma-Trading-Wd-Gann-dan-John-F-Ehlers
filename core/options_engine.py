"""
Options Engine v3.0 - Production Ready
Options analysis, pricing, and strategy recommendation engine
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from scipy.stats import norm
import math


class OptionStyle(Enum):
    EUROPEAN = "european"
    AMERICAN = "american"


class OptionType(Enum):
    CALL = "call"
    PUT = "put"


class VolatilityModel(Enum):
    HISTORICAL = "historical"
    GARCH = "garch"
    IMPLIED = "implied"


@dataclass
class OptionPricing:
    """Option pricing result"""
    theoretical_price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    implied_volatility: float
    intrinsic_value: float
    time_value: float
    moneyness: str  # 'ITM', 'ATM', 'OTM'


@dataclass
class StrategyRecommendation:
    """Strategy recommendation"""
    strategy_name: str
    market_outlook: str  # 'bullish', 'bearish', 'neutral', 'volatile'
    risk_level: str  # 'low', 'medium', 'high'
    max_profit: float
    max_loss: float
    breakeven: List[float]
    probability_of_profit: float
    legs: List[Dict]
    description: str


class OptionsEngine:
    """
    Production-ready options analysis engine supporting:
    - Black-Scholes pricing
    - Greeks calculation
    - Implied volatility calculation
    - Historical volatility analysis
    - Strategy recommendations
    - Risk analysis
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize options engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Settings
        self.risk_free_rate = self.config.get('risk_free_rate', 0.05)  # 5%
        self.trading_days = self.config.get('trading_days', 252)
        
        logger.info("Options Engine initialized")
    
    # ==================== BLACK-SCHOLES PRICING ====================
    
    def black_scholes_price(
        self,
        S: float,          # Spot price
        K: float,          # Strike price
        T: float,          # Time to expiry (years)
        r: float,          # Risk-free rate
        sigma: float,      # Volatility
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Black-Scholes option price.
        
        Returns:
            Option price
        """
        if T <= 0:
            # At expiration
            if option_type == OptionType.CALL:
                return max(0, S - K)
            else:
                return max(0, K - S)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == OptionType.CALL:
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        return price
    
    def calculate_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType = OptionType.CALL
    ) -> Dict[str, float]:
        """
        Calculate all Greeks.
        
        Returns:
            Dictionary with delta, gamma, theta, vega, rho
        """
        if T <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
        
        sqrt_T = np.sqrt(T)
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        
        # PDF at d1
        pdf_d1 = norm.pdf(d1)
        
        # Delta
        if option_type == OptionType.CALL:
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        # Gamma (same for calls and puts)
        gamma = pdf_d1 / (S * sigma * sqrt_T)
        
        # Theta (per day)
        term1 = -(S * pdf_d1 * sigma) / (2 * sqrt_T)
        if option_type == OptionType.CALL:
            term2 = r * K * np.exp(-r * T) * norm.cdf(d2)
            theta = (term1 - term2) / self.trading_days
        else:
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            theta = (term1 + term2) / self.trading_days
        
        # Vega (per 1% volatility change)
        vega = S * sqrt_T * pdf_d1 / 100
        
        # Rho (per 1% interest rate change)
        if option_type == OptionType.CALL:
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        return {
            'delta': round(delta, 4),
            'gamma': round(gamma, 6),
            'theta': round(theta, 4),
            'vega': round(vega, 4),
            'rho': round(rho, 4)
        }
    
    def price_option(
        self,
        spot: float,
        strike: float,
        days_to_expiry: int,
        volatility: float,
        option_type: OptionType = OptionType.CALL,
        risk_free_rate: float = None
    ) -> OptionPricing:
        """
        Full option pricing with Greeks.
        
        Returns:
            OptionPricing object
        """
        r = risk_free_rate or self.risk_free_rate
        T = days_to_expiry / self.trading_days
        
        # Calculate price
        price = self.black_scholes_price(spot, strike, T, r, volatility, option_type)
        
        # Calculate Greeks
        greeks = self.calculate_greeks(spot, strike, T, r, volatility, option_type)
        
        # Intrinsic and time value
        if option_type == OptionType.CALL:
            intrinsic = max(0, spot - strike)
        else:
            intrinsic = max(0, strike - spot)
        
        time_value = price - intrinsic
        
        # Moneyness
        ratio = spot / strike
        if option_type == OptionType.CALL:
            if ratio > 1.02:
                moneyness = 'ITM'
            elif ratio < 0.98:
                moneyness = 'OTM'
            else:
                moneyness = 'ATM'
        else:
            if ratio < 0.98:
                moneyness = 'ITM'
            elif ratio > 1.02:
                moneyness = 'OTM'
            else:
                moneyness = 'ATM'
        
        return OptionPricing(
            theoretical_price=round(price, 4),
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            implied_volatility=volatility,
            intrinsic_value=round(intrinsic, 4),
            time_value=round(time_value, 4),
            moneyness=moneyness
        )
    
    # ==================== IMPLIED VOLATILITY ====================
    
    def calculate_implied_volatility(
        self,
        market_price: float,
        spot: float,
        strike: float,
        days_to_expiry: int,
        option_type: OptionType = OptionType.CALL,
        risk_free_rate: float = None,
        precision: float = 0.0001,
        max_iterations: int = 100
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson.
        
        Returns:
            Implied volatility
        """
        r = risk_free_rate or self.risk_free_rate
        T = days_to_expiry / self.trading_days
        
        if T <= 0:
            return 0
        
        # Initial guess
        sigma = 0.3
        
        for _ in range(max_iterations):
            price = self.black_scholes_price(spot, strike, T, r, sigma, option_type)
            diff = price - market_price
            
            if abs(diff) < precision:
                return sigma
            
            # Vega for Newton-Raphson
            d1 = (np.log(spot / strike) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            vega = spot * np.sqrt(T) * norm.pdf(d1)
            
            if vega < 1e-10:
                break
            
            sigma = sigma - diff / vega
            sigma = max(0.01, min(5.0, sigma))
        
        return sigma
    
    # ==================== VOLATILITY ANALYSIS ====================
    
    def calculate_historical_volatility(
        self,
        data: pd.DataFrame,
        window: int = 20,
        annualize: bool = True
    ) -> pd.Series:
        """
        Calculate historical volatility.
        
        Returns:
            Volatility series
        """
        returns = np.log(data['close'] / data['close'].shift(1))
        vol = returns.rolling(window=window).std()
        
        if annualize:
            vol = vol * np.sqrt(self.trading_days)
        
        return vol
    
    def volatility_cone(
        self,
        data: pd.DataFrame,
        windows: List[int] = [10, 20, 30, 60, 90]
    ) -> Dict:
        """
        Calculate volatility cone (min, max, percentiles).
        
        Returns:
            Volatility cone data
        """
        cone = {}
        
        for window in windows:
            vol = self.calculate_historical_volatility(data, window).dropna()
            
            if len(vol) > 0:
                cone[window] = {
                    'current': vol.iloc[-1],
                    'min': vol.min(),
                    'max': vol.max(),
                    'mean': vol.mean(),
                    'median': vol.median(),
                    'percentile_25': vol.quantile(0.25),
                    'percentile_75': vol.quantile(0.75)
                }
        
        return cone
    
    def is_volatility_elevated(
        self,
        data: pd.DataFrame,
        threshold_percentile: float = 75
    ) -> Tuple[bool, float]:
        """
        Check if current volatility is elevated.
        
        Returns:
            Tuple of (is_elevated, current_percentile)
        """
        vol = self.calculate_historical_volatility(data, 20).dropna()
        
        if len(vol) < 30:
            return False, 50
        
        current = vol.iloc[-1]
        percentile = (vol < current).sum() / len(vol) * 100
        
        return percentile > threshold_percentile, percentile
    
    # ==================== STRATEGY RECOMMENDATIONS ====================
    
    def recommend_strategy(
        self,
        spot: float,
        outlook: str,  # 'bullish', 'bearish', 'neutral', 'volatile'
        volatility: float,
        days_to_expiry: int,
        risk_tolerance: str = 'medium'  # 'low', 'medium', 'high'
    ) -> List[StrategyRecommendation]:
        """
        Recommend options strategies based on outlook.
        
        Returns:
            List of strategy recommendations
        """
        recommendations = []
        
        # ATM strike
        atm = round(spot, -2)  # Round to nearest 100
        
        if outlook == 'bullish':
            recommendations.extend(self._bullish_strategies(spot, atm, volatility, days_to_expiry, risk_tolerance))
        elif outlook == 'bearish':
            recommendations.extend(self._bearish_strategies(spot, atm, volatility, days_to_expiry, risk_tolerance))
        elif outlook == 'neutral':
            recommendations.extend(self._neutral_strategies(spot, atm, volatility, days_to_expiry, risk_tolerance))
        elif outlook == 'volatile':
            recommendations.extend(self._volatile_strategies(spot, atm, volatility, days_to_expiry, risk_tolerance))
        
        return recommendations
    
    def _bullish_strategies(
        self,
        spot: float,
        atm: float,
        vol: float,
        dte: int,
        risk: str
    ) -> List[StrategyRecommendation]:
        """Generate bullish strategy recommendations"""
        strategies = []
        T = dte / self.trading_days
        r = self.risk_free_rate
        
        # 1. Long Call
        call_price = self.black_scholes_price(spot, atm, T, r, vol, OptionType.CALL)
        strategies.append(StrategyRecommendation(
            strategy_name="Long Call",
            market_outlook="bullish",
            risk_level="medium",
            max_profit=float('inf'),
            max_loss=call_price * 100,
            breakeven=[atm + call_price],
            probability_of_profit=0.45,
            legs=[{'type': 'CALL', 'strike': atm, 'action': 'BUY', 'premium': call_price}],
            description="Simple bullish bet with unlimited profit potential"
        ))
        
        # 2. Bull Call Spread
        otm_strike = atm * 1.05
        long_call = self.black_scholes_price(spot, atm, T, r, vol, OptionType.CALL)
        short_call = self.black_scholes_price(spot, otm_strike, T, r, vol, OptionType.CALL)
        net_debit = long_call - short_call
        
        strategies.append(StrategyRecommendation(
            strategy_name="Bull Call Spread",
            market_outlook="bullish",
            risk_level="low",
            max_profit=(otm_strike - atm - net_debit) * 100,
            max_loss=net_debit * 100,
            breakeven=[atm + net_debit],
            probability_of_profit=0.55,
            legs=[
                {'type': 'CALL', 'strike': atm, 'action': 'BUY', 'premium': long_call},
                {'type': 'CALL', 'strike': otm_strike, 'action': 'SELL', 'premium': short_call}
            ],
            description="Limited risk bullish spread"
        ))
        
        return strategies
    
    def _bearish_strategies(
        self,
        spot: float,
        atm: float,
        vol: float,
        dte: int,
        risk: str
    ) -> List[StrategyRecommendation]:
        """Generate bearish strategy recommendations"""
        strategies = []
        T = dte / self.trading_days
        r = self.risk_free_rate
        
        # 1. Long Put
        put_price = self.black_scholes_price(spot, atm, T, r, vol, OptionType.PUT)
        strategies.append(StrategyRecommendation(
            strategy_name="Long Put",
            market_outlook="bearish",
            risk_level="medium",
            max_profit=atm * 100 - put_price * 100,
            max_loss=put_price * 100,
            breakeven=[atm - put_price],
            probability_of_profit=0.45,
            legs=[{'type': 'PUT', 'strike': atm, 'action': 'BUY', 'premium': put_price}],
            description="Simple bearish bet with high profit potential"
        ))
        
        # 2. Bear Put Spread
        otm_strike = atm * 0.95
        long_put = self.black_scholes_price(spot, atm, T, r, vol, OptionType.PUT)
        short_put = self.black_scholes_price(spot, otm_strike, T, r, vol, OptionType.PUT)
        net_debit = long_put - short_put
        
        strategies.append(StrategyRecommendation(
            strategy_name="Bear Put Spread",
            market_outlook="bearish",
            risk_level="low",
            max_profit=(atm - otm_strike - net_debit) * 100,
            max_loss=net_debit * 100,
            breakeven=[atm - net_debit],
            probability_of_profit=0.55,
            legs=[
                {'type': 'PUT', 'strike': atm, 'action': 'BUY', 'premium': long_put},
                {'type': 'PUT', 'strike': otm_strike, 'action': 'SELL', 'premium': short_put}
            ],
            description="Limited risk bearish spread"
        ))
        
        return strategies
    
    def _neutral_strategies(
        self,
        spot: float,
        atm: float,
        vol: float,
        dte: int,
        risk: str
    ) -> List[StrategyRecommendation]:
        """Generate neutral strategy recommendations"""
        strategies = []
        T = dte / self.trading_days
        r = self.risk_free_rate
        
        # Iron Condor
        put_sell = atm * 0.95
        put_buy = atm * 0.90
        call_sell = atm * 1.05
        call_buy = atm * 1.10
        
        credit = (
            self.black_scholes_price(spot, put_sell, T, r, vol, OptionType.PUT) -
            self.black_scholes_price(spot, put_buy, T, r, vol, OptionType.PUT) +
            self.black_scholes_price(spot, call_sell, T, r, vol, OptionType.CALL) -
            self.black_scholes_price(spot, call_buy, T, r, vol, OptionType.CALL)
        )
        
        width = put_sell - put_buy
        
        strategies.append(StrategyRecommendation(
            strategy_name="Iron Condor",
            market_outlook="neutral",
            risk_level="low",
            max_profit=credit * 100,
            max_loss=(width - credit) * 100,
            breakeven=[put_sell - credit, call_sell + credit],
            probability_of_profit=0.65,
            legs=[
                {'type': 'PUT', 'strike': put_buy, 'action': 'BUY'},
                {'type': 'PUT', 'strike': put_sell, 'action': 'SELL'},
                {'type': 'CALL', 'strike': call_sell, 'action': 'SELL'},
                {'type': 'CALL', 'strike': call_buy, 'action': 'BUY'}
            ],
            description="High probability neutral strategy"
        ))
        
        return strategies
    
    def _volatile_strategies(
        self,
        spot: float,
        atm: float,
        vol: float,
        dte: int,
        risk: str
    ) -> List[StrategyRecommendation]:
        """Generate volatility strategies"""
        strategies = []
        T = dte / self.trading_days
        r = self.risk_free_rate
        
        # Long Straddle
        call_price = self.black_scholes_price(spot, atm, T, r, vol, OptionType.CALL)
        put_price = self.black_scholes_price(spot, atm, T, r, vol, OptionType.PUT)
        total_cost = call_price + put_price
        
        strategies.append(StrategyRecommendation(
            strategy_name="Long Straddle",
            market_outlook="volatile",
            risk_level="medium",
            max_profit=float('inf'),
            max_loss=total_cost * 100,
            breakeven=[atm - total_cost, atm + total_cost],
            probability_of_profit=0.35,
            legs=[
                {'type': 'CALL', 'strike': atm, 'action': 'BUY', 'premium': call_price},
                {'type': 'PUT', 'strike': atm, 'action': 'BUY', 'premium': put_price}
            ],
            description="Bet on high volatility in either direction"
        ))
        
        return strategies
    
    def analyze_position_risk(
        self,
        legs: List[Dict],
        spot: float,
        days_to_expiry: int,
        volatility: float
    ) -> Dict:
        """
        Analyze risk of an options position.
        
        Returns:
            Risk analysis dictionary
        """
        T = days_to_expiry / self.trading_days
        r = self.risk_free_rate
        
        # Calculate position Greeks
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        
        for leg in legs:
            option_type = OptionType.CALL if leg['type'] == 'CALL' else OptionType.PUT
            greeks = self.calculate_greeks(spot, leg['strike'], T, r, volatility, option_type)
            
            multiplier = 1 if leg['action'] == 'BUY' else -1
            
            total_delta += greeks['delta'] * multiplier
            total_gamma += greeks['gamma'] * multiplier
            total_theta += greeks['theta'] * multiplier
            total_vega += greeks['vega'] * multiplier
        
        return {
            'net_delta': round(total_delta, 4),
            'net_gamma': round(total_gamma, 6),
            'net_theta': round(total_theta, 4),
            'net_vega': round(total_vega, 4),
            'delta_exposure': total_delta * spot,
            'daily_decay': total_theta * 100,
            'volatility_risk': total_vega * 100
        }


# Example usage
if __name__ == "__main__":
    engine = OptionsEngine()
    
    # Price an option
    spot = 50000
    strike = 50000
    days = 30
    vol = 0.6
    
    print("\n=== Option Pricing ===")
    pricing = engine.price_option(spot, strike, days, vol, OptionType.CALL)
    print(f"Theoretical Price: ${pricing.theoretical_price:.2f}")
    print(f"Delta: {pricing.delta:.4f}")
    print(f"Gamma: {pricing.gamma:.6f}")
    print(f"Theta: ${pricing.theta:.4f}/day")
    print(f"Vega: ${pricing.vega:.4f}/1% vol")
    print(f"Moneyness: {pricing.moneyness}")
    
    # Calculate IV
    print("\n=== Implied Volatility ===")
    market_price = 3500
    iv = engine.calculate_implied_volatility(market_price, spot, strike, days, OptionType.CALL)
    print(f"Market Price: ${market_price}")
    print(f"Implied Volatility: {iv:.2%}")
    
    # Strategy recommendations
    print("\n=== Strategy Recommendations ===")
    strategies = engine.recommend_strategy(spot, 'bullish', vol, days, 'medium')
    for strat in strategies:
        print(f"\n{strat.strategy_name}:")
        print(f"  Max Profit: ${strat.max_profit:,.0f}" if strat.max_profit != float('inf') else "  Max Profit: Unlimited")
        print(f"  Max Loss: ${strat.max_loss:,.0f}")
        print(f"  Breakeven: {[f'${b:,.2f}' for b in strat.breakeven]}")
        print(f"  P(Profit): {strat.probability_of_profit:.0%}")
