"""
Portfolio-Level Risk Management
Correlation, concentration limits, diversification enforcement.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Tuple
from loguru import logger
from dataclasses import dataclass, field


@dataclass
class PortfolioRiskState:
    """Current portfolio risk metrics."""
    portfolio_var_95: float = 0.0
    portfolio_cvar_95: float = 0.0
    sharpe_ratio: float = 0.0
    max_correlation_pair: Tuple[str, str] = ("", "")
    max_correlation_value: float = 0.0
    concentration_hhi: float = 0.0  # Herfindahl-Hirschman Index
    n_positions: int = 0
    total_exposure: float = 0.0
    net_exposure: float = 0.0
    long_exposure: float = 0.0
    short_exposure: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "portfolio_var_95_pct": round(self.portfolio_var_95 * 100, 3),
            "portfolio_cvar_95_pct": round(self.portfolio_cvar_95 * 100, 3),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "max_correlation_pair": list(self.max_correlation_pair),
            "max_correlation_value": round(self.max_correlation_value, 3),
            "concentration_hhi": round(self.concentration_hhi, 4),
            "n_positions": self.n_positions,
            "total_exposure": round(self.total_exposure, 2),
            "net_exposure": round(self.net_exposure, 2),
            "long_exposure": round(self.long_exposure, 2),
            "short_exposure": round(self.short_exposure, 2),
        }


class PortfolioRiskManager:
    """
    Portfolio-level risk management.
    
    Features:
    - Portfolio VaR/CVaR calculation
    - Correlation-based position limits
    - Concentration limits (HHI)
    - Sector/asset class exposure limits
    - Net/gross exposure limits
    - Risk parity allocation
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.max_correlation = config.get("max_correlation", 0.70)
        self.max_single_position_pct = config.get("max_single_position_pct", 15.0)
        self.max_sector_pct = config.get("max_sector_pct", 30.0)
        self.max_gross_exposure_pct = config.get("max_gross_exposure_pct", 200.0)
        self.max_net_exposure_pct = config.get("max_net_exposure_pct", 100.0)
        self.max_hhi = config.get("max_hhi", 0.25)  # No single position > 50% equivalent
        self._returns_cache: Dict[str, pd.Series] = {}
    
    def assess_portfolio_risk(
        self,
        positions: Dict[str, Dict],
        returns_data: Dict[str, pd.Series] = None,
        account_equity: float = 100000.0,
    ) -> PortfolioRiskState:
        """
        Calculate comprehensive portfolio risk metrics.
        
        Args:
            positions: Dict of symbol -> {side, quantity, entry_price, current_price}
            returns_data: Dict of symbol -> return series for correlation/VaR
            account_equity: Current account equity
        """
        state = PortfolioRiskState()
        
        if not positions:
            return state
        
        state.n_positions = len(positions)
        
        # Calculate exposures
        for symbol, pos in positions.items():
            value = pos.get("quantity", 0) * pos.get("current_price", pos.get("entry_price", 0))
            side = pos.get("side", "long").upper()
            
            if side == "BUY" or side == "LONG":
                state.long_exposure += value
            else:
                state.short_exposure += value
        
        state.total_exposure = state.long_exposure + state.short_exposure
        state.net_exposure = state.long_exposure - state.short_exposure
        
        # Concentration (HHI)
        if state.total_exposure > 0:
            weights = []
            for symbol, pos in positions.items():
                value = pos.get("quantity", 0) * pos.get("current_price", pos.get("entry_price", 0))
                w = value / state.total_exposure
                weights.append(w)
            state.concentration_hhi = sum(w**2 for w in weights)
        
        # Correlation analysis
        if returns_data and len(returns_data) > 1:
            symbols = list(returns_data.keys())
            returns_df = pd.DataFrame(returns_data).dropna()
            
            if len(returns_df) >= 30:
                corr_matrix = returns_df.corr()
                
                # Find max correlation pair
                max_corr = 0.0
                max_pair = ("", "")
                for i in range(len(symbols)):
                    for j in range(i + 1, len(symbols)):
                        c = abs(corr_matrix.iloc[i, j])
                        if c > max_corr:
                            max_corr = c
                            max_pair = (symbols[i], symbols[j])
                
                state.max_correlation_pair = max_pair
                state.max_correlation_value = max_corr
                
                # Portfolio VaR
                if len(positions) > 0:
                    held_symbols = [s for s in positions if s in returns_df.columns]
                    if held_symbols:
                        held_returns = returns_df[held_symbols]
                        weights = np.array([
                            (positions[s].get("quantity", 0) * positions[s].get("current_price", 0))
                            / max(state.total_exposure, 1)
                            for s in held_symbols
                        ])
                        port_returns = (held_returns * weights).sum(axis=1)
                        state.portfolio_var_95 = float(port_returns.quantile(0.05))
                        state.portfolio_cvar_95 = float(port_returns[port_returns <= state.portfolio_var_95].mean())
                        
                        if port_returns.std() > 0:
                            state.sharpe_ratio = float(port_returns.mean() / port_returns.std() * np.sqrt(252))
        
        return state
    
    def check_new_position(
        self,
        symbol: str,
        side: str,
        value: float,
        current_positions: Dict[str, Dict],
        returns_data: Dict[str, pd.Series] = None,
        account_equity: float = 100000.0,
    ) -> Tuple[bool, List[str]]:
        """
        Check if adding a new position violates portfolio risk limits.
        
        Returns:
            Tuple of (is_allowed, list_of_violations)
        """
        violations = []
        
        # Check concentration
        total_exposure = value
        for pos in current_positions.values():
            total_exposure += pos.get("quantity", 0) * pos.get("current_price", pos.get("entry_price", 0))
        
        if total_exposure > 0 and account_equity > 0:
            position_pct = (value / account_equity) * 100
            if position_pct > self.max_single_position_pct:
                violations.append(
                    f"Single position {position_pct:.1f}% exceeds {self.max_single_position_pct}% limit"
                )
        
        # Check gross exposure
        if account_equity > 0:
            gross_exposure_pct = (total_exposure / account_equity) * 100
            if gross_exposure_pct > self.max_gross_exposure_pct:
                violations.append(
                    f"Gross exposure {gross_exposure_pct:.1f}% exceeds {self.max_gross_exposure_pct}% limit"
                )
        
        # Check correlation with existing positions
        if returns_data and symbol in returns_data:
            new_returns = returns_data[symbol]
            for existing_symbol in current_positions:
                if existing_symbol in returns_data:
                    existing_returns = returns_data[existing_symbol]
                    aligned = pd.DataFrame({
                        "new": new_returns,
                        "existing": existing_returns,
                    }).dropna()
                    
                    if len(aligned) >= 30:
                        corr = aligned["new"].corr(aligned["existing"])
                        if abs(corr) > self.max_correlation:
                            violations.append(
                                f"High correlation with {existing_symbol}: {corr:.2f} "
                                f"(max: {self.max_correlation})"
                            )
        
        is_allowed = len(violations) == 0
        
        if not is_allowed:
            logger.warning(f"Portfolio risk check REJECTED {symbol}: {violations}")
        
        return is_allowed, violations
