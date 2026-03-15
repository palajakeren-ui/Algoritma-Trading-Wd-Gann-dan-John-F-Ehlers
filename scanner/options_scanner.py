"""
Options Scanner v3.0 - Production Ready
Options chain analysis and trading opportunity scanner
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from scipy.stats import norm
import math


class OptionType(Enum):
    CALL = "call"
    PUT = "put"


class StrategyType(Enum):
    # Directional
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    SHORT_CALL = "short_call"
    SHORT_PUT = "short_put"
    
    # Spreads
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    BULL_PUT_SPREAD = "bull_put_spread"
    BEAR_CALL_SPREAD = "bear_call_spread"
    
    # Neutral
    LONG_STRADDLE = "long_straddle"
    LONG_STRANGLE = "long_strangle"
    SHORT_STRADDLE = "short_straddle"
    SHORT_STRANGLE = "short_strangle"
    IRON_CONDOR = "iron_condor"
    IRON_BUTTERFLY = "iron_butterfly"
    
    # Calendar
    CALENDAR_SPREAD = "calendar_spread"
    DIAGONAL_SPREAD = "diagonal_spread"


@dataclass
class OptionContract:
    """Single option contract"""
    symbol: str
    underlying: str
    option_type: OptionType
    strike: float
    expiration: datetime
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float = 0.0


@dataclass
class OptionsOpportunity:
    """Options trading opportunity"""
    strategy: StrategyType
    underlying: str
    direction: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    contracts: List[OptionContract]
    max_profit: float
    max_loss: float
    breakeven: List[float]
    probability_of_profit: float
    expected_value: float
    risk_reward: float
    days_to_expiry: int
    score: float  # 0-100
    notes: List[str]


class OptionsScanner:
    """
    Production-ready options scanner supporting:
    - Options chain analysis
    - Greeks calculation (Black-Scholes)
    - Strategy identification
    - Probability analysis
    - Unusual activity detection
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize options scanner.
        
        Args:
            config: Scanner configuration
        """
        self.config = config or {}
        
        # Settings
        self.risk_free_rate = self.config.get('risk_free_rate', 0.05)  # 5%
        self.min_volume = self.config.get('min_volume', 100)
        self.min_oi = self.config.get('min_open_interest', 500)
        self.max_spread_pct = self.config.get('max_spread_pct', 5.0)  # Max bid-ask spread
        
        logger.info("Options Scanner initialized")
    
    # ==================== BLACK-SCHOLES ====================
    
    def black_scholes(
        self,
        S: float,  # Current price
        K: float,  # Strike
        T: float,  # Time to expiry (years)
        r: float,  # Risk-free rate
        sigma: float,  # Volatility
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Black-Scholes option price.
        
        Returns:
            Theoretical option price
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
        Calculate option Greeks.
        
        Returns:
            Dictionary with delta, gamma, theta, vega, rho
        """
        if T <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        if option_type == OptionType.CALL:
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        # Gamma
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta (per day)
        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        if option_type == OptionType.CALL:
            term2 = r * K * np.exp(-r * T) * norm.cdf(d2)
            theta = (term1 - term2) / 365
        else:
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            theta = (term1 + term2) / 365
        
        # Vega (per 1% move in volatility)
        vega = S * np.sqrt(T) * norm.pdf(d1) / 100
        
        # Rho (per 1% move in interest rates)
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
    
    def implied_volatility(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: OptionType = OptionType.CALL,
        precision: float = 0.0001,
        max_iterations: int = 100
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Returns:
            Implied volatility
        """
        sigma = 0.3  # Initial guess
        
        for _ in range(max_iterations):
            price = self.black_scholes(S, K, T, r, sigma, option_type)
            diff = price - option_price
            
            if abs(diff) < precision:
                return sigma
            
            # Vega for Newton-Raphson
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            vega = S * np.sqrt(T) * norm.pdf(d1)
            
            if vega < 1e-10:
                break
            
            sigma = sigma - diff / vega
            sigma = max(0.01, min(5.0, sigma))  # Bound sigma
        
        return sigma
    
    # ==================== CHAIN ANALYSIS ====================
    
    def analyze_chain(
        self,
        calls: pd.DataFrame,
        puts: pd.DataFrame,
        current_price: float,
        expiration: datetime
    ) -> Dict:
        """
        Analyze options chain.
        
        Args:
            calls: DataFrame with call options
            puts: DataFrame with put options
            current_price: Current underlying price
            expiration: Options expiration date
            
        Returns:
            Analysis dictionary
        """
        days_to_expiry = (expiration - datetime.now()).days
        T = max(days_to_expiry / 365, 1/365)
        
        analysis = {
            'current_price': current_price,
            'expiration': expiration,
            'days_to_expiry': days_to_expiry,
            'call_volume': calls['volume'].sum() if 'volume' in calls.columns else 0,
            'put_volume': puts['volume'].sum() if 'volume' in puts.columns else 0,
            'call_oi': calls['open_interest'].sum() if 'open_interest' in calls.columns else 0,
            'put_oi': puts['open_interest'].sum() if 'open_interest' in puts.columns else 0,
            'atm_call_iv': 0,
            'atm_put_iv': 0,
            'skew': 0,
            'max_pain': 0
        }
        
        # Put/Call ratio
        if analysis['call_volume'] > 0:
            analysis['put_call_ratio'] = analysis['put_volume'] / analysis['call_volume']
        else:
            analysis['put_call_ratio'] = 0
        
        # Find ATM options
        if 'strike' in calls.columns:
            atm_strike = calls.loc[(calls['strike'] - current_price).abs().idxmin(), 'strike']
            atm_call = calls[calls['strike'] == atm_strike].iloc[0] if len(calls[calls['strike'] == atm_strike]) > 0 else None
            atm_put = puts[puts['strike'] == atm_strike].iloc[0] if len(puts[puts['strike'] == atm_strike]) > 0 else None
            
            if atm_call is not None and 'implied_volatility' in calls.columns:
                analysis['atm_call_iv'] = atm_call['implied_volatility']
            if atm_put is not None and 'implied_volatility' in puts.columns:
                analysis['atm_put_iv'] = atm_put['implied_volatility']
            
            # IV Skew (25 delta put IV - 25 delta call IV)
            if 'delta' in calls.columns and 'delta' in puts.columns:
                call_25d = calls[(calls['delta'] - 0.25).abs() < 0.1]
                put_25d = puts[(puts['delta'].abs() - 0.25).abs() < 0.1]
                
                if len(call_25d) > 0 and len(put_25d) > 0:
                    analysis['skew'] = put_25d['implied_volatility'].mean() - call_25d['implied_volatility'].mean()
        
        # Max Pain (price where most options expire worthless)
        analysis['max_pain'] = self._calculate_max_pain(calls, puts, current_price)
        
        return analysis
    
    def _calculate_max_pain(
        self,
        calls: pd.DataFrame,
        puts: pd.DataFrame,
        current_price: float
    ) -> float:
        """Calculate max pain price"""
        if 'strike' not in calls.columns:
            return current_price
        
        strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
        min_pain = float('inf')
        max_pain_price = current_price
        
        for test_price in strikes:
            total_pain = 0
            
            # Call pain
            for _, call in calls.iterrows():
                if test_price > call['strike']:
                    total_pain += (test_price - call['strike']) * call.get('open_interest', 0)
            
            # Put pain
            for _, put in puts.iterrows():
                if test_price < put['strike']:
                    total_pain += (put['strike'] - test_price) * put.get('open_interest', 0)
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_price = test_price
        
        return max_pain_price
    
    # ==================== OPPORTUNITY DETECTION ====================
    
    def find_opportunities(
        self,
        calls: pd.DataFrame,
        puts: pd.DataFrame,
        current_price: float,
        expiration: datetime,
        direction: str = None  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    ) -> List[OptionsOpportunity]:
        """
        Find options trading opportunities.
        
        Args:
            calls: Call options chain
            puts: Put options chain
            current_price: Current underlying price
            expiration: Options expiration
            direction: Expected market direction
            
        Returns:
            List of opportunities sorted by score
        """
        opportunities = []
        days_to_expiry = (expiration - datetime.now()).days
        
        if days_to_expiry <= 0:
            return opportunities
        
        # Simple directional opportunities
        if direction == 'BULLISH' or direction is None:
            # Find bull call spread opportunities
            bull_spreads = self._find_bull_call_spreads(calls, current_price, days_to_expiry)
            opportunities.extend(bull_spreads)
            
            # Find long call opportunities
            long_calls = self._find_long_calls(calls, current_price, days_to_expiry)
            opportunities.extend(long_calls)
        
        if direction == 'BEARISH' or direction is None:
            # Find bear put spread opportunities
            bear_spreads = self._find_bear_put_spreads(puts, current_price, days_to_expiry)
            opportunities.extend(bear_spreads)
            
            # Find long put opportunities
            long_puts = self._find_long_puts(puts, current_price, days_to_expiry)
            opportunities.extend(long_puts)
        
        if direction == 'NEUTRAL' or direction is None:
            # Find iron condor opportunities
            iron_condors = self._find_iron_condors(calls, puts, current_price, days_to_expiry)
            opportunities.extend(iron_condors)
        
        # Sort by score
        return sorted(opportunities, key=lambda x: -x.score)
    
    def _find_long_calls(
        self,
        calls: pd.DataFrame,
        current_price: float,
        days_to_expiry: int
    ) -> List[OptionsOpportunity]:
        """Find good long call opportunities"""
        opportunities = []
        
        if 'strike' not in calls.columns:
            return opportunities
        
        # Look for slightly OTM calls (2-10% above current price)
        target_min = current_price * 1.02
        target_max = current_price * 1.10
        
        candidates = calls[
            (calls['strike'] >= target_min) & 
            (calls['strike'] <= target_max)
        ]
        
        for _, call in candidates.iterrows():
            strike = call['strike']
            premium = call.get('ask', call.get('last', 0))
            
            if premium <= 0:
                continue
            
            # Calculate metrics
            breakeven = strike + premium
            max_loss = premium * 100  # Per contract
            
            # Estimate max profit (conservative: 2x premium target)
            max_profit = premium * 100  # Could be unlimited
            
            # Probability of profit (simplified)
            distance_pct = (strike - current_price) / current_price
            pop = max(0.1, 0.5 - distance_pct)  # Simplified
            
            score = self._calculate_opportunity_score(
                risk_reward=2.0,
                probability=pop,
                liquidity=call.get('volume', 0) + call.get('open_interest', 0),
                days_to_expiry=days_to_expiry
            )
            
            if score > 50:
                opportunities.append(OptionsOpportunity(
                    strategy=StrategyType.LONG_CALL,
                    underlying=call.get('underlying', 'UNKNOWN'),
                    direction='BULLISH',
                    contracts=[self._row_to_contract(call, OptionType.CALL)],
                    max_profit=max_profit,
                    max_loss=max_loss,
                    breakeven=[breakeven],
                    probability_of_profit=pop,
                    expected_value=(max_profit * pop) - (max_loss * (1 - pop)),
                    risk_reward=2.0,
                    days_to_expiry=days_to_expiry,
                    score=score,
                    notes=[f"Strike: ${strike}", f"Premium: ${premium}"]
                ))
        
        return opportunities
    
    def _find_long_puts(
        self,
        puts: pd.DataFrame,
        current_price: float,
        days_to_expiry: int
    ) -> List[OptionsOpportunity]:
        """Find good long put opportunities"""
        opportunities = []
        
        if 'strike' not in puts.columns:
            return opportunities
        
        # Look for slightly OTM puts (2-10% below current price)
        target_min = current_price * 0.90
        target_max = current_price * 0.98
        
        candidates = puts[
            (puts['strike'] >= target_min) & 
            (puts['strike'] <= target_max)
        ]
        
        for _, put in candidates.iterrows():
            strike = put['strike']
            premium = put.get('ask', put.get('last', 0))
            
            if premium <= 0:
                continue
            
            breakeven = strike - premium
            max_loss = premium * 100
            max_profit = (strike - premium) * 100  # Max if goes to 0
            
            distance_pct = (current_price - strike) / current_price
            pop = max(0.1, 0.5 - distance_pct)
            
            score = self._calculate_opportunity_score(
                risk_reward=max_profit / max_loss if max_loss > 0 else 0,
                probability=pop,
                liquidity=put.get('volume', 0) + put.get('open_interest', 0),
                days_to_expiry=days_to_expiry
            )
            
            if score > 50:
                opportunities.append(OptionsOpportunity(
                    strategy=StrategyType.LONG_PUT,
                    underlying=put.get('underlying', 'UNKNOWN'),
                    direction='BEARISH',
                    contracts=[self._row_to_contract(put, OptionType.PUT)],
                    max_profit=max_profit,
                    max_loss=max_loss,
                    breakeven=[breakeven],
                    probability_of_profit=pop,
                    expected_value=(max_profit * pop) - (max_loss * (1 - pop)),
                    risk_reward=max_profit / max_loss if max_loss > 0 else 0,
                    days_to_expiry=days_to_expiry,
                    score=score,
                    notes=[f"Strike: ${strike}", f"Premium: ${premium}"]
                ))
        
        return opportunities
    
    def _find_bull_call_spreads(
        self,
        calls: pd.DataFrame,
        current_price: float,
        days_to_expiry: int
    ) -> List[OptionsOpportunity]:
        """Find bull call spread opportunities"""
        opportunities = []
        
        if 'strike' not in calls.columns:
            return opportunities
        
        strikes = sorted(calls['strike'].unique())
        
        for i, long_strike in enumerate(strikes):
            if long_strike > current_price * 1.05:
                continue
            
            for short_strike in strikes[i+1:]:
                if short_strike < current_price * 1.02:
                    continue
                if short_strike > current_price * 1.15:
                    break
                
                long_call = calls[calls['strike'] == long_strike].iloc[0] if len(calls[calls['strike'] == long_strike]) > 0 else None
                short_call = calls[calls['strike'] == short_strike].iloc[0] if len(calls[calls['strike'] == short_strike]) > 0 else None
                
                if long_call is None or short_call is None:
                    continue
                
                debit = long_call.get('ask', 0) - short_call.get('bid', 0)
                if debit <= 0:
                    continue
                
                max_profit = (short_strike - long_strike - debit) * 100
                max_loss = debit * 100
                breakeven = long_strike + debit
                
                if max_profit <= 0:
                    continue
                
                risk_reward = max_profit / max_loss if max_loss > 0 else 0
                
                # Probability calculation
                pop = min(0.7, 0.5 + (current_price - long_strike) / current_price)
                
                score = self._calculate_opportunity_score(
                    risk_reward=risk_reward,
                    probability=pop,
                    liquidity=long_call.get('volume', 0) + short_call.get('volume', 0),
                    days_to_expiry=days_to_expiry
                )
                
                if score > 55:
                    opportunities.append(OptionsOpportunity(
                        strategy=StrategyType.BULL_CALL_SPREAD,
                        underlying=long_call.get('underlying', 'UNKNOWN'),
                        direction='BULLISH',
                        contracts=[
                            self._row_to_contract(long_call, OptionType.CALL),
                            self._row_to_contract(short_call, OptionType.CALL)
                        ],
                        max_profit=max_profit,
                        max_loss=max_loss,
                        breakeven=[breakeven],
                        probability_of_profit=pop,
                        expected_value=(max_profit * pop) - (max_loss * (1 - pop)),
                        risk_reward=risk_reward,
                        days_to_expiry=days_to_expiry,
                        score=score,
                        notes=[
                            f"Buy ${long_strike} Call",
                            f"Sell ${short_strike} Call",
                            f"Net Debit: ${debit}"
                        ]
                    ))
        
        return opportunities[:5]  # Return top 5
    
    def _find_bear_put_spreads(
        self,
        puts: pd.DataFrame,
        current_price: float,
        days_to_expiry: int
    ) -> List[OptionsOpportunity]:
        """Find bear put spread opportunities"""
        opportunities = []
        
        if 'strike' not in puts.columns:
            return opportunities
        
        strikes = sorted(puts['strike'].unique(), reverse=True)
        
        for i, long_strike in enumerate(strikes):
            if long_strike < current_price * 0.95:
                continue
            
            for short_strike in strikes[i+1:]:
                if short_strike > current_price * 0.98:
                    continue
                if short_strike < current_price * 0.85:
                    break
                
                long_put = puts[puts['strike'] == long_strike].iloc[0] if len(puts[puts['strike'] == long_strike]) > 0 else None
                short_put = puts[puts['strike'] == short_strike].iloc[0] if len(puts[puts['strike'] == short_strike]) > 0 else None
                
                if long_put is None or short_put is None:
                    continue
                
                debit = long_put.get('ask', 0) - short_put.get('bid', 0)
                if debit <= 0:
                    continue
                
                max_profit = (long_strike - short_strike - debit) * 100
                max_loss = debit * 100
                breakeven = long_strike - debit
                
                if max_profit <= 0:
                    continue
                
                risk_reward = max_profit / max_loss if max_loss > 0 else 0
                pop = min(0.7, 0.5 + (long_strike - current_price) / current_price)
                
                score = self._calculate_opportunity_score(
                    risk_reward=risk_reward,
                    probability=pop,
                    liquidity=long_put.get('volume', 0) + short_put.get('volume', 0),
                    days_to_expiry=days_to_expiry
                )
                
                if score > 55:
                    opportunities.append(OptionsOpportunity(
                        strategy=StrategyType.BEAR_PUT_SPREAD,
                        underlying=long_put.get('underlying', 'UNKNOWN'),
                        direction='BEARISH',
                        contracts=[
                            self._row_to_contract(long_put, OptionType.PUT),
                            self._row_to_contract(short_put, OptionType.PUT)
                        ],
                        max_profit=max_profit,
                        max_loss=max_loss,
                        breakeven=[breakeven],
                        probability_of_profit=pop,
                        expected_value=(max_profit * pop) - (max_loss * (1 - pop)),
                        risk_reward=risk_reward,
                        days_to_expiry=days_to_expiry,
                        score=score,
                        notes=[
                            f"Buy ${long_strike} Put",
                            f"Sell ${short_strike} Put",
                            f"Net Debit: ${debit}"
                        ]
                    ))
        
        return opportunities[:5]
    
    def _find_iron_condors(
        self,
        calls: pd.DataFrame,
        puts: pd.DataFrame,
        current_price: float,
        days_to_expiry: int
    ) -> List[OptionsOpportunity]:
        """Find iron condor opportunities"""
        opportunities = []
        
        if 'strike' not in calls.columns or 'strike' not in puts.columns:
            return opportunities
        
        # Standard iron condor: sell OTM put spread + sell OTM call spread
        target_delta = 0.15  # ~15 delta wings
        
        # Find appropriate strikes
        put_sell_strike = current_price * 0.95  # 5% below
        put_buy_strike = current_price * 0.90   # 10% below
        call_sell_strike = current_price * 1.05  # 5% above
        call_buy_strike = current_price * 1.10   # 10% above
        
        # Find closest strikes
        put_sell = puts.iloc[(puts['strike'] - put_sell_strike).abs().argsort()[:1]]
        put_buy = puts.iloc[(puts['strike'] - put_buy_strike).abs().argsort()[:1]]
        call_sell = calls.iloc[(calls['strike'] - call_sell_strike).abs().argsort()[:1]]
        call_buy = calls.iloc[(calls['strike'] - call_buy_strike).abs().argsort()[:1]]
        
        if len(put_sell) == 0 or len(put_buy) == 0 or len(call_sell) == 0 or len(call_buy) == 0:
            return opportunities
        
        put_sell = put_sell.iloc[0]
        put_buy = put_buy.iloc[0]
        call_sell = call_sell.iloc[0]
        call_buy = call_buy.iloc[0]
        
        # Calculate credit received
        credit = (
            put_sell.get('bid', 0) - put_buy.get('ask', 0) +
            call_sell.get('bid', 0) - call_buy.get('ask', 0)
        )
        
        if credit <= 0:
            return opportunities
        
        # Calculate risk
        put_width = put_sell['strike'] - put_buy['strike']
        call_width = call_buy['strike'] - call_sell['strike']
        max_width = max(put_width, call_width)
        
        max_loss = (max_width - credit) * 100
        max_profit = credit * 100
        
        lower_breakeven = put_sell['strike'] - credit
        upper_breakeven = call_sell['strike'] + credit
        
        # High probability strategy
        pop = 0.65  # Typical iron condor POP
        
        score = self._calculate_opportunity_score(
            risk_reward=max_profit / max_loss if max_loss > 0 else 0,
            probability=pop,
            liquidity=sum([
                put_sell.get('volume', 0), put_buy.get('volume', 0),
                call_sell.get('volume', 0), call_buy.get('volume', 0)
            ]),
            days_to_expiry=days_to_expiry
        )
        
        if score > 50:
            opportunities.append(OptionsOpportunity(
                strategy=StrategyType.IRON_CONDOR,
                underlying=call_sell.get('underlying', 'UNKNOWN'),
                direction='NEUTRAL',
                contracts=[
                    self._row_to_contract(put_buy, OptionType.PUT),
                    self._row_to_contract(put_sell, OptionType.PUT),
                    self._row_to_contract(call_sell, OptionType.CALL),
                    self._row_to_contract(call_buy, OptionType.CALL)
                ],
                max_profit=max_profit,
                max_loss=max_loss,
                breakeven=[lower_breakeven, upper_breakeven],
                probability_of_profit=pop,
                expected_value=(max_profit * pop) - (max_loss * (1 - pop)),
                risk_reward=max_profit / max_loss if max_loss > 0 else 0,
                days_to_expiry=days_to_expiry,
                score=score,
                notes=[
                    f"Sell {put_sell['strike']}/{call_sell['strike']} Strangle",
                    f"Buy {put_buy['strike']}/{call_buy['strike']} Wings",
                    f"Credit: ${credit:.2f}"
                ]
            ))
        
        return opportunities
    
    def _row_to_contract(self, row: pd.Series, option_type: OptionType) -> OptionContract:
        """Convert DataFrame row to OptionContract"""
        return OptionContract(
            symbol=row.get('symbol', ''),
            underlying=row.get('underlying', ''),
            option_type=option_type,
            strike=row.get('strike', 0),
            expiration=row.get('expiration', datetime.now()),
            bid=row.get('bid', 0),
            ask=row.get('ask', 0),
            last=row.get('last', 0),
            volume=row.get('volume', 0),
            open_interest=row.get('open_interest', 0),
            implied_volatility=row.get('implied_volatility', 0),
            delta=row.get('delta', 0),
            gamma=row.get('gamma', 0),
            theta=row.get('theta', 0),
            vega=row.get('vega', 0)
        )
    
    def _calculate_opportunity_score(
        self,
        risk_reward: float,
        probability: float,
        liquidity: int,
        days_to_expiry: int
    ) -> float:
        """Calculate opportunity score (0-100)"""
        # Risk/reward component (0-40 points)
        rr_score = min(40, risk_reward * 20)
        
        # Probability component (0-30 points)
        prob_score = probability * 30
        
        # Liquidity component (0-15 points)
        liq_score = min(15, (liquidity / 1000) * 5)
        
        # Time component (0-15 points)
        # Prefer 20-45 days to expiry
        if 20 <= days_to_expiry <= 45:
            time_score = 15
        elif 10 <= days_to_expiry < 20 or 45 < days_to_expiry <= 60:
            time_score = 10
        else:
            time_score = 5
        
        return min(100, rr_score + prob_score + liq_score + time_score)


# Example usage
if __name__ == "__main__":
    # Create sample options chain
    current_price = 50000
    strikes = np.arange(45000, 56000, 1000)
    expiration = datetime.now() + timedelta(days=30)
    
    calls = pd.DataFrame({
        'strike': strikes,
        'bid': [max(0, current_price - s) + np.random.rand() * 500 for s in strikes],
        'ask': [max(0, current_price - s) + np.random.rand() * 500 + 50 for s in strikes],
        'last': [max(0, current_price - s) + np.random.rand() * 500 + 25 for s in strikes],
        'volume': np.random.randint(100, 5000, len(strikes)),
        'open_interest': np.random.randint(500, 10000, len(strikes)),
        'implied_volatility': np.random.uniform(0.4, 0.8, len(strikes)),
        'delta': [max(0, 1 - (s - current_price) / current_price) for s in strikes],
        'underlying': 'BTC'
    })
    
    puts = pd.DataFrame({
        'strike': strikes,
        'bid': [max(0, s - current_price) + np.random.rand() * 500 for s in strikes],
        'ask': [max(0, s - current_price) + np.random.rand() * 500 + 50 for s in strikes],
        'last': [max(0, s - current_price) + np.random.rand() * 500 + 25 for s in strikes],
        'volume': np.random.randint(100, 5000, len(strikes)),
        'open_interest': np.random.randint(500, 10000, len(strikes)),
        'implied_volatility': np.random.uniform(0.4, 0.8, len(strikes)),
        'delta': [-max(0, (current_price - s) / current_price) for s in strikes],
        'underlying': 'BTC'
    })
    
    # Run scanner
    scanner = OptionsScanner()
    
    # Analyze chain
    analysis = scanner.analyze_chain(calls, puts, current_price, expiration)
    print("\n=== Chain Analysis ===")
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    # Find opportunities
    opportunities = scanner.find_opportunities(calls, puts, current_price, expiration, direction='BULLISH')
    
    print(f"\n=== Found {len(opportunities)} Opportunities ===")
    for opp in opportunities[:5]:
        print(f"\n{opp.strategy.value}:")
        print(f"  Direction: {opp.direction}")
        print(f"  Max Profit: ${opp.max_profit:.2f}")
        print(f"  Max Loss: ${opp.max_loss:.2f}")
        print(f"  Risk/Reward: {opp.risk_reward:.2f}")
        print(f"  Probability: {opp.probability_of_profit:.2%}")
        print(f"  Score: {opp.score:.1f}")
