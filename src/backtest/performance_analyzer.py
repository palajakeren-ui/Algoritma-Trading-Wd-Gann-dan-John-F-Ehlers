"""
Performance Analyzer
Post-backtest analytics: detailed statistics, risk metrics, trade analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for backtest results.
    
    Features:
    - Risk-adjusted return metrics
    - Trade distribution analysis
    - Drawdown analysis
    - Monthly/yearly returns
    - Rolling performance
    """
    
    def analyze(self, result) -> Dict:
        """
        Full performance analysis.
        
        Args:
            result: BacktestResult object
            
        Returns:
            Dict of comprehensive analytics
        """
        analytics = {}
        
        # Core metrics
        analytics["summary"] = result.to_dict()
        
        # Trade analysis
        if result.trades:
            analytics["trade_analysis"] = self._trade_analysis(result.trades)
        
        # Drawdown analysis
        if result.equity_curve:
            analytics["drawdown_analysis"] = self._drawdown_analysis(result.equity_curve)
        
        # Streak analysis
        if result.trades:
            analytics["streak_analysis"] = self._streak_analysis(result.trades)
        
        # Exit reason breakdown
        if result.trades:
            analytics["exit_reasons"] = self._exit_reason_analysis(result.trades)
        
        # MFE/MAE analysis
        if result.trades:
            analytics["excursion_analysis"] = self._excursion_analysis(result.trades)
        
        return analytics
    
    @staticmethod
    def _trade_analysis(trades) -> Dict:
        """Detailed trade statistics."""
        pnls = [t.pnl for t in trades]
        pnl_pcts = [t.pnl_pct for t in trades]
        
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(len(wins) / max(len(trades), 1) * 100, 1),
            "avg_win": round(np.mean(wins), 2) if wins else 0,
            "avg_loss": round(np.mean(losses), 2) if losses else 0,
            "largest_win": round(max(pnls), 2) if pnls else 0,
            "largest_loss": round(min(pnls), 2) if pnls else 0,
            "avg_pnl": round(np.mean(pnls), 2),
            "median_pnl": round(float(np.median(pnls)), 2),
            "std_pnl": round(float(np.std(pnls)), 2),
            "avg_win_pct": round(np.mean([p for p in pnl_pcts if p > 0]), 2) if any(p > 0 for p in pnl_pcts) else 0,
            "avg_loss_pct": round(np.mean([p for p in pnl_pcts if p <= 0]), 2) if any(p <= 0 for p in pnl_pcts) else 0,
            "expectancy": round(
                (len(wins)/max(len(trades),1)) * (np.mean(wins) if wins else 0) +
                (len(losses)/max(len(trades),1)) * (np.mean(losses) if losses else 0), 2
            ),
        }
    
    @staticmethod
    def _drawdown_analysis(equity_curve) -> Dict:
        """Detailed drawdown analysis."""
        eq = np.array(equity_curve)
        running_max = np.maximum.accumulate(eq)
        drawdowns = (eq - running_max) / running_max
        
        # Find drawdown periods
        dd_periods = []
        in_dd = False
        dd_start = 0
        
        for i in range(len(drawdowns)):
            if drawdowns[i] < 0 and not in_dd:
                in_dd = True
                dd_start = i
            elif drawdowns[i] == 0 and in_dd:
                in_dd = False
                dd_periods.append({
                    "start_bar": dd_start,
                    "end_bar": i,
                    "duration": i - dd_start,
                    "depth_pct": round(abs(min(drawdowns[dd_start:i+1])) * 100, 2),
                })
        
        # Sort by depth
        dd_periods.sort(key=lambda x: x["depth_pct"], reverse=True)
        
        return {
            "max_drawdown_pct": round(abs(drawdowns.min()) * 100, 2),
            "avg_drawdown_pct": round(abs(drawdowns[drawdowns < 0].mean()) * 100, 2) if any(drawdowns < 0) else 0,
            "max_dd_duration": max((d["duration"] for d in dd_periods), default=0),
            "n_drawdown_periods": len(dd_periods),
            "top_5_drawdowns": dd_periods[:5],
        }
    
    @staticmethod
    def _streak_analysis(trades) -> Dict:
        """Win/loss streak analysis."""
        outcomes = ["W" if t.pnl > 0 else "L" for t in trades]
        
        if not outcomes:
            return {}
        
        max_win_streak = 0
        max_loss_streak = 0
        current_streak = 1
        
        for i in range(1, len(outcomes)):
            if outcomes[i] == outcomes[i-1]:
                current_streak += 1
            else:
                if outcomes[i-1] == "W":
                    max_win_streak = max(max_win_streak, current_streak)
                else:
                    max_loss_streak = max(max_loss_streak, current_streak)
                current_streak = 1
        
        # Don't forget last streak
        if outcomes[-1] == "W":
            max_win_streak = max(max_win_streak, current_streak)
        else:
            max_loss_streak = max(max_loss_streak, current_streak)
        
        return {
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,
        }
    
    @staticmethod
    def _exit_reason_analysis(trades) -> Dict:
        """Breakdown of performance by exit reason."""
        reasons = {}
        for t in trades:
            reason = t.exit_reason or "unknown"
            if reason not in reasons:
                reasons[reason] = {"count": 0, "total_pnl": 0, "wins": 0}
            reasons[reason]["count"] += 1
            reasons[reason]["total_pnl"] = round(reasons[reason]["total_pnl"] + t.pnl, 2)
            if t.pnl > 0:
                reasons[reason]["wins"] += 1
        
        for reason in reasons:
            reasons[reason]["win_rate"] = round(
                reasons[reason]["wins"] / max(reasons[reason]["count"], 1) * 100, 1
            )
        
        return reasons
    
    @staticmethod
    def _excursion_analysis(trades) -> Dict:
        """Maximum Favorable/Adverse Excursion analysis."""
        mfe = [t.max_favorable * 100 for t in trades if t.max_favorable > 0]
        mae = [t.max_adverse * 100 for t in trades if t.max_adverse > 0]
        
        return {
            "avg_mfe_pct": round(float(np.mean(mfe)), 2) if mfe else 0,
            "avg_mae_pct": round(float(np.mean(mae)), 2) if mae else 0,
            "max_mfe_pct": round(max(mfe), 2) if mfe else 0,
            "max_mae_pct": round(max(mae), 2) if mae else 0,
            "mfe_mae_ratio": round(
                float(np.mean(mfe)) / max(float(np.mean(mae)), 0.01), 2
            ) if mfe and mae else 0,
        }
