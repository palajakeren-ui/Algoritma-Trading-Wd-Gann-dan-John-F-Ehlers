"""
Conditional Value at Risk (CVaR / Expected Shortfall) Calculator
Institutional-grade tail risk measurement.

CVaR answers: "Given we're in the worst X% of scenarios, what's the average loss?"
This is the gold standard for institutional risk measurement, superior to VaR.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Tuple
from loguru import logger
from dataclasses import dataclass


@dataclass
class CVaRResult:
    """CVaR calculation result."""
    var_95: float          # 95% Value at Risk
    var_99: float          # 99% Value at Risk
    cvar_95: float         # 95% Conditional VaR (Expected Shortfall)
    cvar_99: float         # 99% Conditional VaR (Expected Shortfall)
    max_loss: float        # Maximum historical loss
    mean_return: float     # Mean return
    volatility: float      # Return volatility (annualized)
    skewness: float        # Return skewness
    kurtosis: float        # Return kurtosis (excess)
    n_observations: int    # Number of observations used
    method: str            # Calculation method used
    
    def to_dict(self) -> Dict:
        return {
            "var_95": round(self.var_95, 6),
            "var_99": round(self.var_99, 6),
            "cvar_95": round(self.cvar_95, 6),
            "cvar_99": round(self.cvar_99, 6),
            "max_loss": round(self.max_loss, 6),
            "mean_return": round(self.mean_return, 6),
            "volatility_annual": round(self.volatility, 6),
            "skewness": round(self.skewness, 4),
            "kurtosis": round(self.kurtosis, 4),
            "n_observations": self.n_observations,
            "method": self.method,
        }
    
    @property
    def is_dangerous(self) -> bool:
        """Check if risk metrics indicate dangerous conditions."""
        return (
            self.cvar_99 < -0.10 or  # >10% expected loss in worst 1% scenarios
            self.kurtosis > 10 or     # Fat tails
            self.volatility > 1.0     # >100% annualized vol
        )


class CVaRCalculator:
    """
    Calculates CVaR using multiple methods:
    
    1. Historical Simulation - Direct from return distribution
    2. Parametric (Gaussian) - Assumes normal distribution
    3. Cornish-Fisher - Adjusts for skewness and kurtosis
    4. Monte Carlo CVaR - Simulated distribution
    """
    
    # Annualization factors by data frequency
    ANNUALIZATION = {
        "1m": np.sqrt(252 * 24 * 60),
        "5m": np.sqrt(252 * 24 * 12),
        "15m": np.sqrt(252 * 24 * 4),
        "1h": np.sqrt(252 * 24),
        "4h": np.sqrt(252 * 6),
        "1d": np.sqrt(252),
        "1w": np.sqrt(52),
    }
    
    def __init__(self, confidence_levels: List[float] = None):
        self.confidence_levels = confidence_levels or [0.95, 0.99]
    
    def calculate(
        self,
        returns: pd.Series,
        method: str = "historical",
        timeframe: str = "1d"
    ) -> CVaRResult:
        """
        Calculate CVaR for a return series.
        
        Args:
            returns: Series of returns (NOT prices)
            method: 'historical', 'parametric', 'cornish_fisher'
            timeframe: Data frequency for annualization
            
        Returns:
            CVaRResult with all risk metrics
        """
        returns = returns.dropna()
        
        if len(returns) < 30:
            logger.warning(f"CVaR calculation with only {len(returns)} observations - results unreliable")
        
        ann_factor = self.ANNUALIZATION.get(timeframe, np.sqrt(252))
        
        if method == "historical":
            var_95, cvar_95 = self._historical_cvar(returns, 0.95)
            var_99, cvar_99 = self._historical_cvar(returns, 0.99)
        elif method == "parametric":
            var_95, cvar_95 = self._parametric_cvar(returns, 0.95)
            var_99, cvar_99 = self._parametric_cvar(returns, 0.99)
        elif method == "cornish_fisher":
            var_95, cvar_95 = self._cornish_fisher_cvar(returns, 0.95)
            var_99, cvar_99 = self._cornish_fisher_cvar(returns, 0.99)
        else:
            raise ValueError(f"Unknown CVaR method: {method}")
        
        vol = returns.std() * ann_factor
        skew = float(returns.skew()) if len(returns) > 3 else 0.0
        kurt = float(returns.kurtosis()) if len(returns) > 4 else 0.0
        
        result = CVaRResult(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            max_loss=float(returns.min()),
            mean_return=float(returns.mean()),
            volatility=vol,
            skewness=skew,
            kurtosis=kurt,
            n_observations=len(returns),
            method=method,
        )
        
        logger.debug(
            f"CVaR [{method}]: VaR95={var_95:.4f}, CVaR95={cvar_95:.4f}, "
            f"VaR99={var_99:.4f}, CVaR99={cvar_99:.4f}, Vol={vol:.4f}"
        )
        
        return result
    
    def _historical_cvar(self, returns: pd.Series, confidence: float) -> Tuple[float, float]:
        """Historical simulation CVaR."""
        alpha = 1 - confidence
        var = float(returns.quantile(alpha))
        cvar = float(returns[returns <= var].mean())
        return var, cvar
    
    def _parametric_cvar(self, returns: pd.Series, confidence: float) -> Tuple[float, float]:
        """Parametric (Gaussian) CVaR."""
        from scipy import stats
        
        mu = returns.mean()
        sigma = returns.std()
        alpha = 1 - confidence
        
        z = stats.norm.ppf(alpha)
        var = mu + sigma * z
        
        # CVaR for Gaussian: E[X | X < VaR] = mu - sigma * phi(z) / alpha
        cvar = mu - sigma * stats.norm.pdf(z) / alpha
        
        return float(var), float(cvar)
    
    def _cornish_fisher_cvar(self, returns: pd.Series, confidence: float) -> Tuple[float, float]:
        """Cornish-Fisher expansion - adjusts for skewness and kurtosis."""
        from scipy import stats
        
        mu = returns.mean()
        sigma = returns.std()
        s = returns.skew()    # Skewness
        k = returns.kurtosis()  # Excess kurtosis
        alpha = 1 - confidence
        
        z = stats.norm.ppf(alpha)
        
        # Cornish-Fisher expansion
        z_cf = (z + 
                (z**2 - 1) * s / 6 + 
                (z**3 - 3*z) * k / 24 - 
                (2*z**3 - 5*z) * s**2 / 36)
        
        var = mu + sigma * z_cf
        
        # Approximate CVaR using historical for tail
        cvar_returns = returns[returns <= var]
        if len(cvar_returns) > 0:
            cvar = float(cvar_returns.mean())
        else:
            cvar = var * 1.2  # Conservative estimate
        
        return float(var), float(cvar)
    
    def rolling_cvar(
        self,
        returns: pd.Series,
        window: int = 252,
        confidence: float = 0.95
    ) -> pd.DataFrame:
        """
        Calculate rolling CVaR over a window.
        
        Returns DataFrame with var and cvar columns.
        """
        var_series = []
        cvar_series = []
        
        for i in range(window, len(returns)):
            window_returns = returns.iloc[i-window:i]
            var, cvar = self._historical_cvar(window_returns, confidence)
            var_series.append(var)
            cvar_series.append(cvar)
        
        idx = returns.index[window:]
        return pd.DataFrame({
            f"var_{int(confidence*100)}": var_series,
            f"cvar_{int(confidence*100)}": cvar_series,
        }, index=idx)
    
    def portfolio_cvar(
        self,
        returns_matrix: pd.DataFrame,
        weights: np.ndarray,
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        """
        Calculate portfolio-level VaR and CVaR.
        
        Args:
            returns_matrix: DataFrame of asset returns (each column = one asset)
            weights: Portfolio weights
            confidence: Confidence level
            
        Returns:
            Tuple of (portfolio_var, portfolio_cvar)
        """
        portfolio_returns = (returns_matrix * weights).sum(axis=1)
        return self._historical_cvar(portfolio_returns, confidence)
