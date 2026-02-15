"""
Risk-Reward Engine v3.0 - Production Ready
Advanced risk-reward analysis and position sizing
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from dataclasses import dataclass, field
from enum import Enum


class RRRating(Enum):
    EXCELLENT = "excellent"  # R:R >= 3:1
    GOOD = "good"           # R:R >= 2:1
    ACCEPTABLE = "acceptable"  # R:R >= 1.5:1
    POOR = "poor"           # R:R < 1.5:1


class TradeQuality(Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    AVOID = "AVOID"


@dataclass
class RRAnalysis:
    """Risk-Reward analysis result"""
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    rr_rating: RRRating
    risk_percentage: float
    reward_percentage: float
    breakeven_winrate: float
    expected_value: float
    position_size: float
    position_value: float
    notes: List[str]


@dataclass
class TradeSetup:
    """Complete trade setup with R:R analysis"""
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float]
    take_profit_3: Optional[float]
    risk_reward: float
    quality: TradeQuality
    position_size: float
    risk_amount: float
    expected_profit: float
    win_probability: float
    reasoning: List[str]


class RREngine:
    """
    Production-ready Risk-Reward engine supporting:
    - R:R ratio calculation
    - Multi-target analysis
    - Position sizing
    - Expected value calculation
    - Trade quality scoring
    - Kelly criterion sizing
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize R:R engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Risk settings
        self.account_balance = self.config.get('account_balance', 100000)
        self.risk_per_trade = self.config.get('risk_per_trade', 0.01)  # 1%
        self.max_position_pct = self.config.get('max_position_pct', 0.1)  # 10%
        self.min_rr_ratio = self.config.get('min_rr_ratio', 1.5)
        
        logger.info("Risk-Reward Engine initialized")
    
    def set_account_balance(self, balance: float):
        """Update account balance"""
        self.account_balance = balance
    
    # ==================== BASIC R:R CALCULATION ====================
    
    def calculate_rr(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float,
        direction: str = 'LONG'
    ) -> RRAnalysis:
        """
        Calculate basic risk-reward analysis.
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            direction: 'LONG' or 'SHORT'
            
        Returns:
            RRAnalysis object
        """
        # Calculate risk and reward
        if direction.upper() == 'LONG':
            risk = entry - stop_loss
            reward = take_profit - entry
        else:
            risk = stop_loss - entry
            reward = entry - take_profit
        
        if risk <= 0:
            return self._invalid_rr("Invalid stop loss - no risk")
        
        if reward <= 0:
            return self._invalid_rr("Invalid take profit - no reward")
        
        # R:R ratio
        rr_ratio = reward / risk
        
        # Rating
        if rr_ratio >= 3:
            rating = RRRating.EXCELLENT
        elif rr_ratio >= 2:
            rating = RRRating.GOOD
        elif rr_ratio >= 1.5:
            rating = RRRating.ACCEPTABLE
        else:
            rating = RRRating.POOR
        
        # Percentages
        risk_pct = (risk / entry) * 100
        reward_pct = (reward / entry) * 100
        
        # Breakeven winrate
        breakeven_wr = 1 / (1 + rr_ratio)
        
        # Position sizing
        risk_amount = self.account_balance * self.risk_per_trade
        position_size = risk_amount / risk
        position_value = position_size * entry
        
        # Cap position size
        max_value = self.account_balance * self.max_position_pct
        if position_value > max_value:
            position_size = max_value / entry
            position_value = max_value
        
        # Expected value (assuming 50% winrate as baseline)
        assumed_winrate = 0.5
        ev = (assumed_winrate * reward * position_size) - ((1 - assumed_winrate) * risk * position_size)
        
        # Notes
        notes = []
        if rr_ratio >= 3:
            notes.append("Excellent R:R - high quality setup")
        elif rr_ratio >= 2:
            notes.append("Good R:R - acceptable setup")
        elif rr_ratio < 1.5:
            notes.append("Poor R:R - consider skipping")
        
        if breakeven_wr > 0.5:
            notes.append(f"Requires {breakeven_wr:.1%} winrate to be profitable")
        
        return RRAnalysis(
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=round(risk * position_size, 2),
            reward_amount=round(reward * position_size, 2),
            risk_reward_ratio=round(rr_ratio, 2),
            rr_rating=rating,
            risk_percentage=round(risk_pct, 2),
            reward_percentage=round(reward_pct, 2),
            breakeven_winrate=round(breakeven_wr, 3),
            expected_value=round(ev, 2),
            position_size=round(position_size, 6),
            position_value=round(position_value, 2),
            notes=notes
        )
    
    def _invalid_rr(self, reason: str) -> RRAnalysis:
        """Return invalid R:R analysis"""
        return RRAnalysis(
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            risk_amount=0,
            reward_amount=0,
            risk_reward_ratio=0,
            rr_rating=RRRating.POOR,
            risk_percentage=0,
            reward_percentage=0,
            breakeven_winrate=1.0,
            expected_value=0,
            position_size=0,
            position_value=0,
            notes=[reason]
        )
    
    # ==================== MULTI-TARGET ANALYSIS ====================
    
    def calculate_multi_target_rr(
        self,
        entry: float,
        stop_loss: float,
        targets: List[Tuple[float, float]],  # List of (price, allocation %)
        direction: str = 'LONG'
    ) -> Dict:
        """
        Calculate R:R for multiple take profit targets.
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            targets: List of (target_price, allocation_percentage)
            direction: 'LONG' or 'SHORT'
            
        Returns:
            Multi-target analysis dictionary
        """
        # Validate targets
        total_allocation = sum(t[1] for t in targets)
        if abs(total_allocation - 100) > 0.1:
            logger.warning(f"Target allocations don't sum to 100%: {total_allocation}%")
        
        # Calculate risk
        if direction.upper() == 'LONG':
            risk = entry - stop_loss
        else:
            risk = stop_loss - entry
        
        if risk <= 0:
            return {'error': 'Invalid stop loss'}
        
        # Analyze each target
        target_analyses = []
        weighted_rr = 0
        weighted_ev = 0
        
        for i, (price, alloc_pct) in enumerate(targets):
            if direction.upper() == 'LONG':
                reward = price - entry
            else:
                reward = entry - price
            
            rr = reward / risk if risk > 0 else 0
            weight = alloc_pct / 100
            
            target_analyses.append({
                'target_num': i + 1,
                'price': price,
                'allocation_pct': alloc_pct,
                'reward': reward,
                'rr_ratio': round(rr, 2),
                'contribution_to_rr': round(rr * weight, 2)
            })
            
            weighted_rr += rr * weight
            
            # EV calculation (50% winrate assumption)
            assumed_wr = 0.5
            target_ev = (assumed_wr * reward * weight) - ((1 - assumed_wr) * risk * weight)
            weighted_ev += target_ev
        
        # Overall rating
        if weighted_rr >= 3:
            rating = RRRating.EXCELLENT
        elif weighted_rr >= 2:
            rating = RRRating.GOOD
        elif weighted_rr >= 1.5:
            rating = RRRating.ACCEPTABLE
        else:
            rating = RRRating.POOR
        
        return {
            'entry': entry,
            'stop_loss': stop_loss,
            'risk_per_unit': risk,
            'targets': target_analyses,
            'weighted_rr': round(weighted_rr, 2),
            'rating': rating.value,
            'breakeven_winrate': round(1 / (1 + weighted_rr), 3) if weighted_rr > 0 else 1.0,
            'expected_value_per_unit': round(weighted_ev, 4)
        }
    
    # ==================== POSITION SIZING ====================
    
    def calculate_position_size(
        self,
        entry: float,
        stop_loss: float,
        risk_amount: float = None,
        risk_percentage: float = None
    ) -> Dict:
        """
        Calculate optimal position size.
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            risk_amount: Dollar amount to risk (optional)
            risk_percentage: Percentage of account to risk (optional)
            
        Returns:
            Position sizing dictionary
        """
        if risk_amount is None:
            if risk_percentage is None:
                risk_percentage = self.risk_per_trade
            risk_amount = self.account_balance * risk_percentage
        
        risk_per_unit = abs(entry - stop_loss)
        
        if risk_per_unit == 0:
            return {'error': 'Invalid stop loss distance'}
        
        position_size = risk_amount / risk_per_unit
        position_value = position_size * entry
        
        # Check against max position
        max_value = self.account_balance * self.max_position_pct
        capped = position_value > max_value
        
        if capped:
            position_size = max_value / entry
            position_value = max_value
            actual_risk = position_size * risk_per_unit
        else:
            actual_risk = risk_amount
        
        return {
            'position_size': round(position_size, 6),
            'position_value': round(position_value, 2),
            'risk_per_unit': round(risk_per_unit, 4),
            'risk_amount': round(actual_risk, 2),
            'risk_percentage': round((actual_risk / self.account_balance) * 100, 2),
            'leverage_used': round(position_value / self.account_balance, 2),
            'capped': capped,
            'max_position_value': max_value
        }
    
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> Dict:
        """
        Calculate Kelly criterion position sizing.
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount
            
        Returns:
            Kelly analysis dictionary
        """
        if avg_loss == 0:
            return {'error': 'Average loss cannot be zero'}
        
        # Win/Loss ratio
        win_loss_ratio = avg_win / avg_loss
        
        # Kelly percentage
        kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Half Kelly (more conservative)
        half_kelly = kelly_pct / 2
        
        # Quarter Kelly (very conservative)
        quarter_kelly = kelly_pct / 4
        
        return {
            'win_rate': win_rate,
            'win_loss_ratio': round(win_loss_ratio, 2),
            'full_kelly': round(kelly_pct * 100, 2),
            'half_kelly': round(half_kelly * 100, 2),
            'quarter_kelly': round(quarter_kelly * 100, 2),
            'recommended': 'half_kelly',
            'position_with_kelly': round(self.account_balance * half_kelly, 2) if half_kelly > 0 else 0,
            'notes': [
                'Full Kelly is aggressive and can lead to large drawdowns',
                'Half Kelly provides good growth with lower risk',
                'Use Quarter Kelly for conservative approach'
            ] if kelly_pct > 0 else ['Negative Kelly - system is not profitable']
        }
    
    # ==================== TRADE QUALITY SCORING ====================
    
    def score_trade_setup(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float,
        direction: str,
        confluence_count: int = 0,
        trend_aligned: bool = False,
        at_support_resistance: bool = False,
        volume_confirmed: bool = False,
        momentum_aligned: bool = False
    ) -> TradeSetup:
        """
        Score and analyze a trade setup.
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price  
            take_profit: Take profit price
            direction: 'LONG' or 'SHORT'
            confluence_count: Number of confirming signals
            trend_aligned: Whether trade is with the trend
            at_support_resistance: Whether entry is at key level
            volume_confirmed: Whether volume supports the move
            momentum_aligned: Whether momentum supports direction
            
        Returns:
            TradeSetup object with quality rating
        """
        # Calculate R:R
        rr_analysis = self.calculate_rr(entry, stop_loss, take_profit, direction)
        rr = rr_analysis.risk_reward_ratio
        
        # Quality scoring
        score = 0
        reasoning = []
        
        # R:R contribution (max 40 points)
        if rr >= 3:
            score += 40
            reasoning.append("Excellent R:R >= 3:1")
        elif rr >= 2.5:
            score += 35
            reasoning.append("Very good R:R >= 2.5:1")
        elif rr >= 2:
            score += 30
            reasoning.append("Good R:R >= 2:1")
        elif rr >= 1.5:
            score += 20
            reasoning.append("Acceptable R:R >= 1.5:1")
        else:
            score += 5
            reasoning.append("Poor R:R < 1.5:1")
        
        # Confluence (max 20 points)
        confluence_points = min(20, confluence_count * 5)
        score += confluence_points
        if confluence_count >= 3:
            reasoning.append(f"Strong confluence: {confluence_count} confirming signals")
        elif confluence_count >= 2:
            reasoning.append(f"Moderate confluence: {confluence_count} confirming signals")
        
        # Trend alignment (10 points)
        if trend_aligned:
            score += 10
            reasoning.append("Trade aligned with higher TF trend")
        
        # Support/Resistance (10 points)
        if at_support_resistance:
            score += 10
            reasoning.append("Entry at key S/R level")
        
        # Volume (10 points)
        if volume_confirmed:
            score += 10
            reasoning.append("Volume confirms the move")
        
        # Momentum (10 points)
        if momentum_aligned:
            score += 10
            reasoning.append("Momentum supports direction")
        
        # Determine quality grade
        if score >= 85:
            quality = TradeQuality.A_PLUS
        elif score >= 70:
            quality = TradeQuality.A
        elif score >= 55:
            quality = TradeQuality.B
        elif score >= 40:
            quality = TradeQuality.C
        else:
            quality = TradeQuality.AVOID
        
        # Win probability estimate based on factors
        base_prob = 0.45
        if trend_aligned:
            base_prob += 0.05
        if at_support_resistance:
            base_prob += 0.05
        if volume_confirmed:
            base_prob += 0.03
        if momentum_aligned:
            base_prob += 0.03
        if confluence_count >= 3:
            base_prob += 0.05
        
        win_prob = min(0.7, base_prob)
        
        # Expected profit
        expected_profit = (win_prob * rr_analysis.reward_amount) - ((1 - win_prob) * rr_analysis.risk_amount)
        
        return TradeSetup(
            symbol='',  # To be filled by caller
            direction=direction,
            entry=entry,
            stop_loss=stop_loss,
            take_profit_1=take_profit,
            take_profit_2=None,
            take_profit_3=None,
            risk_reward=rr,
            quality=quality,
            position_size=rr_analysis.position_size,
            risk_amount=rr_analysis.risk_amount,
            expected_profit=round(expected_profit, 2),
            win_probability=round(win_prob, 2),
            reasoning=reasoning
        )
    
    # ==================== UTILITY METHODS ====================
    
    def calculate_stop_from_rr(
        self,
        entry: float,
        take_profit: float,
        target_rr: float,
        direction: str = 'LONG'
    ) -> float:
        """
        Calculate stop loss given entry, TP, and desired R:R.
        
        Returns:
            Stop loss price
        """
        if direction.upper() == 'LONG':
            reward = take_profit - entry
            risk = reward / target_rr
            stop_loss = entry - risk
        else:
            reward = entry - take_profit
            risk = reward / target_rr
            stop_loss = entry + risk
        
        return round(stop_loss, 2)
    
    def calculate_tp_from_rr(
        self,
        entry: float,
        stop_loss: float,
        target_rr: float,
        direction: str = 'LONG'
    ) -> float:
        """
        Calculate take profit given entry, SL, and desired R:R.
        
        Returns:
            Take profit price
        """
        if direction.upper() == 'LONG':
            risk = entry - stop_loss
            reward = risk * target_rr
            take_profit = entry + reward
        else:
            risk = stop_loss - entry
            reward = risk * target_rr
            take_profit = entry - reward
        
        return round(take_profit, 2)
    
    def generate_multiple_targets(
        self,
        entry: float,
        stop_loss: float,
        rr_ratios: List[float] = [1.5, 2.0, 3.0],
        direction: str = 'LONG'
    ) -> List[Dict]:
        """
        Generate multiple take profit targets.
        
        Returns:
            List of target dictionaries
        """
        targets = []
        
        for rr in rr_ratios:
            tp = self.calculate_tp_from_rr(entry, stop_loss, rr, direction)
            targets.append({
                'rr_ratio': rr,
                'price': tp,
                'distance_pct': round(abs(tp - entry) / entry * 100, 2)
            })
        
        return targets


# Example usage
if __name__ == "__main__":
    engine = RREngine({
        'account_balance': 100000,
        'risk_per_trade': 0.01,
        'max_position_pct': 0.1
    })
    
    print("\n=== Basic R:R Analysis ===")
    analysis = engine.calculate_rr(
        entry=50000,
        stop_loss=49000,
        take_profit=53000,
        direction='LONG'
    )
    print(f"Entry: ${analysis.entry_price:,.2f}")
    print(f"Stop Loss: ${analysis.stop_loss:,.2f}")
    print(f"Take Profit: ${analysis.take_profit:,.2f}")
    print(f"Risk/Reward: {analysis.risk_reward_ratio}:1")
    print(f"Rating: {analysis.rr_rating.value}")
    print(f"Position Size: {analysis.position_size:.6f}")
    print(f"Risk Amount: ${analysis.risk_amount:,.2f}")
    print(f"Reward Amount: ${analysis.reward_amount:,.2f}")
    print(f"Breakeven Winrate: {analysis.breakeven_winrate:.1%}")
    
    print("\n=== Multi-Target Analysis ===")
    multi = engine.calculate_multi_target_rr(
        entry=50000,
        stop_loss=49000,
        targets=[
            (51500, 33),  # TP1: 1.5R, 33%
            (52000, 33),  # TP2: 2R, 33%
            (53000, 34)   # TP3: 3R, 34%
        ],
        direction='LONG'
    )
    print(f"Weighted R:R: {multi['weighted_rr']}:1")
    print(f"Rating: {multi['rating']}")
    for t in multi['targets']:
        print(f"  TP{t['target_num']}: ${t['price']:,.2f} ({t['rr_ratio']}R, {t['allocation_pct']}%)")
    
    print("\n=== Trade Quality Scoring ===")
    setup = engine.score_trade_setup(
        entry=50000,
        stop_loss=49000,
        take_profit=53000,
        direction='LONG',
        confluence_count=4,
        trend_aligned=True,
        at_support_resistance=True,
        volume_confirmed=True,
        momentum_aligned=True
    )
    print(f"Quality: {setup.quality.value}")
    print(f"Win Probability: {setup.win_probability:.0%}")
    print(f"Expected Profit: ${setup.expected_profit:,.2f}")
    print("Reasoning:")
    for r in setup.reasoning:
        print(f"  • {r}")
    
    print("\n=== Kelly Criterion ===")
    kelly = engine.kelly_criterion(
        win_rate=0.55,
        avg_win=2000,
        avg_loss=1000
    )
    print(f"Win Rate: {kelly['win_rate']:.0%}")
    print(f"Win/Loss Ratio: {kelly['win_loss_ratio']}")
    print(f"Full Kelly: {kelly['full_kelly']:.1f}%")
    print(f"Half Kelly: {kelly['half_kelly']:.1f}%")
    print(f"Position Size (Half Kelly): ${kelly['position_with_kelly']:,.2f}")
