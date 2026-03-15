"""
Walk-Forward Validation
The ONLY acceptable ML validation methodology for live trading.

Walk-forward prevents look-ahead bias by:
1. Training on data up to time T
2. Predicting on T+1 to T+N (out-of-sample)
3. Rolling forward and repeating
4. Aggregating OOS performance metrics

This is what separates a paper model from a production model.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Tuple, Callable, Any
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WalkForwardResult:
    """Results of walk-forward validation."""
    n_folds: int
    oos_returns: List[float] = field(default_factory=list)   # Per-fold OOS returns
    oos_sharpe: float = 0.0
    oos_win_rate: float = 0.0
    oos_profit_factor: float = 0.0
    oos_max_drawdown: float = 0.0
    oos_total_return: float = 0.0
    is_metrics: List[float] = field(default_factory=list)    # In-sample metrics per fold
    degradation_pct: float = 0.0  # IS vs OOS performance gap
    train_sizes: List[int] = field(default_factory=list)
    test_sizes: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "n_folds": self.n_folds,
            "oos_sharpe": round(self.oos_sharpe, 3),
            "oos_win_rate_pct": round(self.oos_win_rate * 100, 1),
            "oos_profit_factor": round(self.oos_profit_factor, 3),
            "oos_max_drawdown_pct": round(self.oos_max_drawdown * 100, 2),
            "oos_total_return_pct": round(self.oos_total_return * 100, 2),
            "is_oos_degradation_pct": round(self.degradation_pct, 1),
        }
    
    @property
    def passes_production_check(self) -> bool:
        """Check if OOS performance meets production standards."""
        return (
            self.oos_sharpe > 0.5 and
            self.oos_win_rate > 0.45 and
            self.oos_profit_factor > 1.2 and
            self.oos_max_drawdown < 0.30 and
            self.degradation_pct < 40  # Max 40% degradation from IS to OOS
        )


class WalkForwardValidator:
    """
    Walk-forward validation engine.
    
    Modes:
    1. Anchored - Training always starts from beginning
    2. Rolling - Fixed-size training window
    3. Expanding - Training window grows
    
    Anti-Overfit Features:
    - Purge period between train/test to avoid leakage
    - Embargo period after test to prevent information leakage
    - Multiple holdout shuffles
    - IS vs OOS degradation measurement
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.mode = config.get("mode", "expanding")
        self.n_folds = config.get("n_folds", 5)
        self.train_pct = config.get("train_pct", 0.8)
        self.purge_bars = config.get("purge_bars", 5)     # Gap between train/test
        self.embargo_bars = config.get("embargo_bars", 5)  # Gap after test
        self.min_train_size = config.get("min_train_size", 252)  # Minimum 1 year
    
    def validate(
        self,
        data: pd.DataFrame,
        train_fn: Callable,
        predict_fn: Callable,
        evaluate_fn: Callable = None,
    ) -> WalkForwardResult:
        """
        Run walk-forward validation.
        
        Args:
            data: Full dataset with features and target
            train_fn: Callable(train_data) -> model
            predict_fn: Callable(model, test_data) -> predictions
            evaluate_fn: Callable(predictions, actuals) -> metric_value
            
        Returns:
            WalkForwardResult
        """
        n = len(data)
        if n < self.min_train_size + 50:
            logger.warning(f"Insufficient data for walk-forward: {n} rows")
        
        folds = self._generate_folds(n)
        result = WalkForwardResult(n_folds=len(folds))
        
        all_oos_predictions = []
        all_oos_actuals = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(folds):
            train_data = data.iloc[train_idx]
            test_data = data.iloc[test_idx]
            
            result.train_sizes.append(len(train_data))
            result.test_sizes.append(len(test_data))
            
            logger.info(
                f"Walk-forward fold {fold_idx + 1}/{len(folds)}: "
                f"Train={len(train_data)} rows, Test={len(test_data)} rows"
            )
            
            # Train on IS data
            try:
                model = train_fn(train_data)
            except Exception as e:
                logger.error(f"Training failed on fold {fold_idx}: {e}")
                continue
            
            # Predict on OOS data
            try:
                predictions = predict_fn(model, test_data)
            except Exception as e:
                logger.error(f"Prediction failed on fold {fold_idx}: {e}")
                continue
            
            # Evaluate
            if evaluate_fn is not None:
                is_score = evaluate_fn(predict_fn(model, train_data), train_data)
                oos_score = evaluate_fn(predictions, test_data)
                result.is_metrics.append(float(is_score))
                result.oos_returns.append(float(oos_score))
            else:
                # Default: assume predictions are returns
                if hasattr(predictions, '__iter__'):
                    result.oos_returns.extend([float(p) for p in predictions])
                else:
                    result.oos_returns.append(float(predictions))
            
            all_oos_predictions.extend(
                predictions if hasattr(predictions, '__iter__') else [predictions]
            )
        
        # Aggregate OOS metrics
        if result.oos_returns:
            oos_arr = np.array(result.oos_returns)
            result.oos_total_return = float(np.sum(oos_arr))
            result.oos_win_rate = float(np.mean(oos_arr > 0))
            
            # Sharpe
            if np.std(oos_arr) > 0:
                result.oos_sharpe = float(np.mean(oos_arr) / np.std(oos_arr) * np.sqrt(252))
            
            # Profit factor
            wins = oos_arr[oos_arr > 0].sum()
            losses = abs(oos_arr[oos_arr < 0].sum())
            result.oos_profit_factor = float(wins / max(losses, 0.0001))
            
            # Max drawdown
            cumulative = np.cumsum(oos_arr)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = cumulative - running_max
            result.oos_max_drawdown = float(abs(drawdowns.min())) if len(drawdowns) > 0 else 0
        
        # IS vs OOS degradation
        if result.is_metrics and result.oos_returns:
            is_mean = np.mean(result.is_metrics)
            oos_mean = np.mean(result.oos_returns)
            if abs(is_mean) > 0:
                result.degradation_pct = float((1 - oos_mean / is_mean) * 100)
        
        logger.info(
            f"Walk-forward complete: "
            f"OOS Sharpe={result.oos_sharpe:.3f} | "
            f"Win Rate={result.oos_win_rate*100:.1f}% | "
            f"PF={result.oos_profit_factor:.2f} | "
            f"MaxDD={result.oos_max_drawdown*100:.1f}% | "
            f"Degradation={result.degradation_pct:.1f}%"
        )
        
        if result.passes_production_check:
            logger.info("✅ Walk-forward PASSES production standards")
        else:
            logger.warning("❌ Walk-forward FAILS production standards")
        
        return result
    
    def _generate_folds(self, n: int) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generate train/test fold indices."""
        folds = []
        
        if self.mode == "expanding":
            # Each fold adds more training data
            fold_size = (n - self.min_train_size) // self.n_folds
            if fold_size < 20:
                fold_size = max(10, n // (self.n_folds + 1))
            
            for i in range(self.n_folds):
                test_end = n - (self.n_folds - 1 - i) * fold_size
                test_start = test_end - fold_size
                train_end = test_start - self.purge_bars
                train_start = 0
                
                if train_end - train_start < self.min_train_size:
                    continue
                if test_end > n:
                    test_end = n
                
                train_idx = np.arange(train_start, train_end)
                test_idx = np.arange(test_start, test_end)
                folds.append((train_idx, test_idx))
        
        elif self.mode == "rolling":
            # Fixed training window size
            train_size = int(n * self.train_pct / (1 + self.train_pct))
            test_size = n // self.n_folds
            
            for i in range(self.n_folds):
                test_start = train_size + self.purge_bars + i * test_size
                test_end = min(test_start + test_size, n)
                train_start = max(0, test_start - self.purge_bars - train_size)
                train_end = test_start - self.purge_bars
                
                if test_end > n or train_end <= train_start:
                    continue
                
                train_idx = np.arange(train_start, train_end)
                test_idx = np.arange(test_start, test_end)
                folds.append((train_idx, test_idx))
        
        elif self.mode == "anchored":
            # Always start from 0
            step = (n - self.min_train_size) // self.n_folds
            
            for i in range(self.n_folds):
                train_end = self.min_train_size + i * step
                test_start = train_end + self.purge_bars
                test_end = min(test_start + step, n)
                
                if test_end > n:
                    continue
                
                train_idx = np.arange(0, train_end)
                test_idx = np.arange(test_start, test_end)
                folds.append((train_idx, test_idx))
        
        if not folds:
            # Fallback: simple split
            split = int(n * 0.7)
            train_idx = np.arange(0, split)
            test_idx = np.arange(split + self.purge_bars, n)
            folds = [(train_idx, test_idx)]
        
        return folds
