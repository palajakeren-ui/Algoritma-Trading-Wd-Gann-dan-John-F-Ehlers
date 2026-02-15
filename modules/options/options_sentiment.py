"""
Options Sentiment Module
Analyzes options market sentiment
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class SentimentResult:
    sentiment: str  # 'bullish', 'bearish', 'neutral'
    score: float  # -1 to 1
    put_call_ratio: float
    max_pain: float
    key_levels: List[float]


class OptionsSentimentAnalyzer:
    """Analyzes options market sentiment indicators."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("OptionsSentimentAnalyzer initialized")
    
    def calculate_put_call_ratio(
        self,
        call_volume: float,
        put_volume: float
    ) -> Dict:
        """Calculate put/call ratio and interpret sentiment."""
        if call_volume == 0:
            ratio = float('inf') if put_volume > 0 else 1.0
        else:
            ratio = put_volume / call_volume
        
        # Interpretation
        if ratio > 1.2:
            sentiment = 'bearish'
            description = "High put activity indicates bearish sentiment"
        elif ratio < 0.7:
            sentiment = 'bullish'
            description = "High call activity indicates bullish sentiment"
        else:
            sentiment = 'neutral'
            description = "Balanced options activity"
        
        return {
            'ratio': round(ratio, 3),
            'sentiment': sentiment,
            'description': description,
            'call_volume': call_volume,
            'put_volume': put_volume
        }
    
    def calculate_max_pain(
        self,
        options_chain: List[Dict],
        spot_price: float
    ) -> Dict:
        """
        Calculate max pain (price where option writers maximize profit).
        
        Args:
            options_chain: List of options with strike, type, and open_interest
            spot_price: Current spot price
        """
        strikes = sorted(set(opt['strike'] for opt in options_chain))
        
        if not strikes:
            return {'max_pain': spot_price, 'distance': 0}
        
        min_loss = float('inf')
        max_pain_strike = spot_price
        
        for test_price in strikes:
            total_loss = 0
            
            for opt in options_chain:
                strike = opt['strike']
                oi = opt.get('open_interest', 0)
                opt_type = opt.get('type', 'call')
                
                if opt_type == 'call':
                    # Call ITM loss
                    if test_price > strike:
                        total_loss += (test_price - strike) * oi
                else:
                    # Put ITM loss
                    if test_price < strike:
                        total_loss += (strike - test_price) * oi
            
            if total_loss < min_loss:
                min_loss = total_loss
                max_pain_strike = test_price
        
        return {
            'max_pain': max_pain_strike,
            'distance': abs(spot_price - max_pain_strike),
            'distance_pct': abs(spot_price - max_pain_strike) / spot_price * 100
        }
    
    def analyze_open_interest(
        self,
        options_chain: List[Dict]
    ) -> Dict:
        """Analyze open interest distribution."""
        calls = [opt for opt in options_chain if opt.get('type') == 'call']
        puts = [opt for opt in options_chain if opt.get('type') == 'put']
        
        total_call_oi = sum(opt.get('open_interest', 0) for opt in calls)
        total_put_oi = sum(opt.get('open_interest', 0) for opt in puts)
        
        # Find key levels (highest OI)
        all_opts = sorted(options_chain, key=lambda x: x.get('open_interest', 0), reverse=True)
        key_levels = [opt['strike'] for opt in all_opts[:5]]
        
        return {
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'oi_ratio': total_put_oi / total_call_oi if total_call_oi > 0 else 1,
            'key_levels': key_levels
        }
    
    def analyze_skew(
        self,
        options_chain: List[Dict],
        spot_price: float
    ) -> Dict:
        """Analyze IV skew between puts and calls."""
        atm_range = 0.05  # 5% from ATM
        
        atm_calls = [opt for opt in options_chain 
                     if opt.get('type') == 'call' and 
                     abs(opt['strike'] - spot_price) / spot_price < atm_range]
        
        otm_puts = [opt for opt in options_chain 
                    if opt.get('type') == 'put' and 
                    opt['strike'] < spot_price * 0.95]
        
        avg_call_iv = np.mean([opt.get('iv', 0.3) for opt in atm_calls]) if atm_calls else 0.3
        avg_put_iv = np.mean([opt.get('iv', 0.3) for opt in otm_puts]) if otm_puts else 0.3
        
        skew = avg_put_iv - avg_call_iv
        
        return {
            'atm_call_iv': round(avg_call_iv * 100, 2),
            'otm_put_iv': round(avg_put_iv * 100, 2),
            'skew': round(skew * 100, 2),
            'interpretation': 'Fear premium' if skew > 0.05 else 'Normal' if skew > -0.05 else 'Complacency'
        }
    
    def get_sentiment(
        self,
        options_chain: List[Dict],
        spot_price: float,
        call_volume: float = None,
        put_volume: float = None
    ) -> SentimentResult:
        """Get overall options sentiment."""
        # Calculate metrics
        if call_volume is not None and put_volume is not None:
            pcr = self.calculate_put_call_ratio(call_volume, put_volume)
        else:
            pcr = {'ratio': 1.0, 'sentiment': 'neutral'}
        
        max_pain = self.calculate_max_pain(options_chain, spot_price)
        oi_analysis = self.analyze_open_interest(options_chain)
        
        # Aggregate score
        score = 0
        
        # PCR contribution
        if pcr['ratio'] > 1.2:
            score -= 0.3
        elif pcr['ratio'] < 0.7:
            score += 0.3
        
        # Max pain contribution
        if max_pain['max_pain'] > spot_price * 1.02:
            score += 0.2
        elif max_pain['max_pain'] < spot_price * 0.98:
            score -= 0.2
        
        # Determine overall sentiment
        if score > 0.2:
            sentiment = 'bullish'
        elif score < -0.2:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return SentimentResult(
            sentiment=sentiment,
            score=round(score, 2),
            put_call_ratio=pcr['ratio'],
            max_pain=max_pain['max_pain'],
            key_levels=oi_analysis['key_levels']
        )


if __name__ == "__main__":
    analyzer = OptionsSentimentAnalyzer()
    
    # Test with mock data
    options_chain = [
        {'strike': 48000, 'type': 'call', 'open_interest': 1000, 'iv': 0.55},
        {'strike': 50000, 'type': 'call', 'open_interest': 2000, 'iv': 0.50},
        {'strike': 52000, 'type': 'call', 'open_interest': 1500, 'iv': 0.48},
        {'strike': 48000, 'type': 'put', 'open_interest': 1500, 'iv': 0.58},
        {'strike': 50000, 'type': 'put', 'open_interest': 1800, 'iv': 0.55},
        {'strike': 52000, 'type': 'put', 'open_interest': 500, 'iv': 0.52},
    ]
    
    result = analyzer.get_sentiment(options_chain, 50000, 5000, 4000)
    
    print("\n=== Options Sentiment ===")
    print(f"Sentiment: {result.sentiment}")
    print(f"Score: {result.score}")
    print(f"P/C Ratio: {result.put_call_ratio}")
    print(f"Max Pain: {result.max_pain}")
    print(f"Key Levels: {result.key_levels}")
