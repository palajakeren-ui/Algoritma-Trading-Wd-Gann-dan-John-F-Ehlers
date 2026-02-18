"""
Monte Carlo Risk Stress Testing
Institutional-grade equity curve simulation and stress analysis.

Simulates thousands of possible equity paths to assess:
- Probability of ruin
- Expected max drawdown distribution
- Confidence intervals for final equity
- Worst-case scenarios under stress
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Tuple
from loguru import logger
from dataclasses import dataclass, field
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


@dataclass
class MonteCarloResult:
    """Results of Monte Carlo simulation."""
    n_simulations: int
    n_steps: int
    
    # Equity path statistics
    mean_final_equity: float
    median_final_equity: float
    worst_case_equity: float      # 1st percentile
    best_case_equity: float       # 99th percentile
    std_final_equity: float
    
    # Risk metrics
    mean_max_drawdown: float
    worst_max_drawdown: float     # 99th percentile worst DD
    prob_of_ruin: float           # P(equity < ruin_threshold)
    prob_of_profit: float         # P(final_equity > initial)
    
    # Confidence intervals
    ci_95_lower: float
    ci_95_upper: float
    ci_99_lower: float
    ci_99_upper: float
    
    # Distribution of max drawdowns
    dd_percentiles: Dict[str, float] = field(default_factory=dict)
    
    # Raw paths for visualization
    equity_paths: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict:
        return {
            "n_simulations": self.n_simulations,
            "n_steps": self.n_steps,
            "mean_final_equity": round(self.mean_final_equity, 2),
            "median_final_equity": round(self.median_final_equity, 2),
            "worst_case_equity_1pct": round(self.worst_case_equity, 2),
            "best_case_equity_99pct": round(self.best_case_equity, 2),
            "std_final_equity": round(self.std_final_equity, 2),
            "mean_max_drawdown_pct": round(self.mean_max_drawdown * 100, 2),
            "worst_max_drawdown_pct": round(self.worst_max_drawdown * 100, 2),
            "prob_of_ruin_pct": round(self.prob_of_ruin * 100, 2),
            "prob_of_profit_pct": round(self.prob_of_profit * 100, 2),
            "ci_95": [round(self.ci_95_lower, 2), round(self.ci_95_upper, 2)],
            "ci_99": [round(self.ci_99_lower, 2), round(self.ci_99_upper, 2)],
            "dd_percentiles": {k: round(v * 100, 2) for k, v in self.dd_percentiles.items()},
        }
    
    @property
    def passes_institutional_check(self) -> bool:
        """Check if simulation results meet institutional risk standards."""
        return (
            self.prob_of_ruin < 0.01 and          # <1% probability of ruin
            self.worst_max_drawdown < 0.30 and     # <30% worst-case drawdown
            self.mean_max_drawdown < 0.15 and      # <15% average max drawdown  
            self.prob_of_profit > 0.55              # >55% probability of profit
        )


class MonteCarloSimulator:
    """
    Monte Carlo equity curve simulator.
    
    Methods:
    1. Bootstrap Simulation - Resample from actual trade returns
    2. Parametric Simulation - Generate returns from fitted distribution
    3. Block Bootstrap - Preserve autocorrelation
    4. Stress Testing - Apply stress scenarios to paths
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.n_simulations = config.get("n_simulations", 10000)
        self.ruin_threshold_pct = config.get("ruin_threshold_pct", 0.5)  # 50% loss = ruin
        self.random_seed = config.get("random_seed", None)
    
    def simulate_equity_paths(
        self,
        trade_returns: np.ndarray,
        initial_equity: float = 100000.0,
        n_trades_forward: int = 500,
        method: str = "bootstrap",
        store_paths: bool = False,
    ) -> MonteCarloResult:
        """
        Simulate future equity paths based on historical trade returns.
        
        Args:
            trade_returns: Array of trade returns (as fractions, e.g., 0.02 = 2%)
            initial_equity: Starting equity
            n_trades_forward: Number of trades to simulate forward
            method: 'bootstrap', 'parametric', 'block_bootstrap'
            store_paths: Whether to store all simulated paths (memory intensive)
            
        Returns:
            MonteCarloResult with comprehensive statistics
        """
        if len(trade_returns) < 10:
            logger.warning("Monte Carlo: <10 historical trades, results unreliable")
        
        rng = np.random.RandomState(self.random_seed)
        n_sims = self.n_simulations
        ruin_level = initial_equity * self.ruin_threshold_pct
        
        logger.info(f"Monte Carlo: {n_sims} simulations × {n_trades_forward} trades "
                     f"| Method: {method} | Initial: ${initial_equity:,.0f}")
        
        # Generate simulated return sequences
        if method == "bootstrap":
            sim_returns = self._bootstrap(trade_returns, n_sims, n_trades_forward, rng)
        elif method == "parametric":
            sim_returns = self._parametric(trade_returns, n_sims, n_trades_forward, rng)
        elif method == "block_bootstrap":
            sim_returns = self._block_bootstrap(trade_returns, n_sims, n_trades_forward, rng)
        else:
            raise ValueError(f"Unknown simulation method: {method}")
        
        # Compute equity paths
        # equity_paths shape: (n_sims, n_trades_forward + 1)
        cumulative_returns = np.cumprod(1 + sim_returns, axis=1)
        equity_paths = initial_equity * np.column_stack([
            np.ones(n_sims),  # Initial equity
            cumulative_returns,
        ])
        
        # Final equities
        final_equities = equity_paths[:, -1]
        
        # Max drawdowns per path
        max_drawdowns = np.zeros(n_sims)
        for i in range(n_sims):
            path = equity_paths[i]
            running_max = np.maximum.accumulate(path)
            drawdowns = (path - running_max) / running_max
            max_drawdowns[i] = drawdowns.min()  # Most negative
        
        max_drawdowns = np.abs(max_drawdowns)  # Make positive for reporting
        
        # Probability of ruin
        hit_ruin = np.any(equity_paths <= ruin_level, axis=1)
        prob_ruin = np.mean(hit_ruin)
        
        # Probability of profit
        prob_profit = np.mean(final_equities > initial_equity)
        
        # Percentiles
        p1, p5, p25, p50, p75, p95, p99 = np.percentile(
            final_equities, [1, 5, 25, 50, 75, 95, 99]
        )
        
        dd_percentiles = {
            "p50": float(np.percentile(max_drawdowns, 50)),
            "p75": float(np.percentile(max_drawdowns, 75)),
            "p90": float(np.percentile(max_drawdowns, 90)),
            "p95": float(np.percentile(max_drawdowns, 95)),
            "p99": float(np.percentile(max_drawdowns, 99)),
        }
        
        result = MonteCarloResult(
            n_simulations=n_sims,
            n_steps=n_trades_forward,
            mean_final_equity=float(np.mean(final_equities)),
            median_final_equity=float(p50),
            worst_case_equity=float(p1),
            best_case_equity=float(p99),
            std_final_equity=float(np.std(final_equities)),
            mean_max_drawdown=float(np.mean(max_drawdowns)),
            worst_max_drawdown=float(np.percentile(max_drawdowns, 99)),
            prob_of_ruin=float(prob_ruin),
            prob_of_profit=float(prob_profit),
            ci_95_lower=float(p5),
            ci_95_upper=float(p95),
            ci_99_lower=float(p1),
            ci_99_upper=float(p99),
            dd_percentiles=dd_percentiles,
            equity_paths=equity_paths if store_paths else None,
        )
        
        logger.info(
            f"Monte Carlo complete: "
            f"Mean=${result.mean_final_equity:,.0f} | "
            f"P(ruin)={result.prob_of_ruin*100:.1f}% | "
            f"P(profit)={result.prob_of_profit*100:.1f}% | "
            f"Mean MaxDD={result.mean_max_drawdown*100:.1f}% | "
            f"Worst MaxDD={result.worst_max_drawdown*100:.1f}%"
        )
        
        if not result.passes_institutional_check:
            logger.warning("⚠️ Monte Carlo FAILS institutional risk standards")
        
        return result
    
    def _bootstrap(
        self, returns: np.ndarray, n_sims: int, n_steps: int, rng: np.random.RandomState
    ) -> np.ndarray:
        """Standard bootstrap: random sampling with replacement."""
        indices = rng.randint(0, len(returns), size=(n_sims, n_steps))
        return returns[indices]
    
    def _parametric(
        self, returns: np.ndarray, n_sims: int, n_steps: int, rng: np.random.RandomState
    ) -> np.ndarray:
        """Parametric: fit distribution and sample."""
        mu = np.mean(returns)
        sigma = np.std(returns)
        
        # Use Student's t-distribution to capture fat tails
        from scipy import stats
        
        # Fit t-distribution
        try:
            df, loc, scale = stats.t.fit(returns)
            sim_returns = stats.t.rvs(df, loc=loc, scale=scale, size=(n_sims, n_steps), random_state=rng)
        except Exception:
            # Fallback to normal
            sim_returns = rng.normal(mu, sigma, size=(n_sims, n_steps))
        
        return sim_returns
    
    def _block_bootstrap(
        self, returns: np.ndarray, n_sims: int, n_steps: int, rng: np.random.RandomState
    ) -> np.ndarray:
        """Block bootstrap: preserves autocorrelation structure."""
        block_size = max(5, int(np.sqrt(len(returns))))
        n_blocks = (n_steps // block_size) + 1
        
        sim_returns = np.zeros((n_sims, n_steps))
        
        for sim in range(n_sims):
            path = np.array([], dtype=float)
            for _ in range(n_blocks):
                start = rng.randint(0, max(1, len(returns) - block_size))
                block = returns[start:start + block_size]
                path = np.concatenate([path, block])
            sim_returns[sim] = path[:n_steps]
        
        return sim_returns
    
    def stress_test(
        self,
        trade_returns: np.ndarray,
        initial_equity: float = 100000.0,
        scenarios: Dict[str, Dict] = None,
    ) -> Dict[str, MonteCarloResult]:
        """
        Run Monte Carlo under different stress scenarios.
        
        Args:
            trade_returns: Historical trade returns
            initial_equity: Starting equity
            scenarios: Dict of scenario_name -> {return_shock, vol_multiplier}
            
        Returns:
            Dict of scenario_name -> MonteCarloResult
        """
        if scenarios is None:
            scenarios = {
                "base_case": {"return_shock": 0.0, "vol_multiplier": 1.0},
                "mild_stress": {"return_shock": -0.005, "vol_multiplier": 1.5},
                "severe_stress": {"return_shock": -0.01, "vol_multiplier": 2.0},
                "crisis": {"return_shock": -0.02, "vol_multiplier": 3.0},
                "black_swan": {"return_shock": -0.05, "vol_multiplier": 5.0},
            }
        
        results = {}
        for name, params in scenarios.items():
            # Adjust returns for stress scenario
            shocked_returns = trade_returns.copy()
            shocked_returns = shocked_returns + params.get("return_shock", 0.0)
            
            vol_mult = params.get("vol_multiplier", 1.0)
            if vol_mult != 1.0:
                mean_r = np.mean(shocked_returns)
                shocked_returns = mean_r + (shocked_returns - mean_r) * vol_mult
            
            logger.info(f"Stress test scenario: {name}")
            results[name] = self.simulate_equity_paths(
                shocked_returns,
                initial_equity=initial_equity,
                n_trades_forward=500,
                method="bootstrap",
            )
        
        return results
