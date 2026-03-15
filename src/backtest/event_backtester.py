"""
Event-Driven Backtester
Simulates live trading conditions: bar-by-bar processing, no look-ahead bias.

Key differences from vector backtesting:
1. Processes one bar at a time (no future data access)
2. Simulates order fills with slippage
3. Enforces risk checks on each trade
4. Tracks commission and fees
5. Produces realistic equity curves
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Callable, Any, Tuple
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    initial_capital: float = 100000.0
    commission_pct: float = 0.1       # 0.1% per trade
    slippage_bps: float = 5.0         # 5 basis points
    risk_per_trade_pct: float = 1.0
    max_positions: int = 5
    max_leverage: int = 1
    require_stop_loss: bool = True
    use_circuit_breaker: bool = True
    circuit_breaker_dd_pct: float = 15.0


@dataclass 
class BacktestTrade:
    """Record of a single backtest trade."""
    id: int
    symbol: str
    side: str
    entry_bar: int
    entry_time: Any
    entry_price: float
    quantity: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    exit_bar: int = 0
    exit_time: Any = None
    exit_price: float = 0.0
    exit_reason: str = ""
    
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    slippage_cost: float = 0.0
    bars_held: int = 0
    max_favorable: float = 0.0
    max_adverse: float = 0.0


@dataclass
class BacktestResult:
    """Complete backtest result."""
    config: BacktestConfig
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    timestamps: List[Any] = field(default_factory=list)
    
    # Aggregate metrics
    total_return_pct: float = 0.0
    cagr_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0
    avg_trade_pnl: float = 0.0
    avg_bars_held: float = 0.0
    total_trades: int = 0
    total_commission: float = 0.0
    total_slippage_cost: float = 0.0
    calmar_ratio: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_return_pct": round(self.total_return_pct, 2),
            "cagr_pct": round(self.cagr_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "sortino_ratio": round(self.sortino_ratio, 3),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "calmar_ratio": round(self.calmar_ratio, 3),
            "win_rate_pct": round(self.win_rate_pct, 1),
            "profit_factor": round(self.profit_factor, 2),
            "total_trades": self.total_trades,
            "avg_trade_pnl": round(self.avg_trade_pnl, 2),
            "avg_bars_held": round(self.avg_bars_held, 1),
            "total_commission": round(self.total_commission, 2),
            "total_slippage": round(self.total_slippage_cost, 2),
        }


class EventBacktester:
    """
    Event-driven backtesting engine.
    
    Usage:
        bt = EventBacktester(config)
        result = bt.run(
            data=ohlcv_df,
            strategy_fn=my_strategy,
        )
    
    where strategy_fn(bar_data, positions, equity) -> list of orders
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
    
    def run(
        self,
        data: pd.DataFrame,
        strategy_fn: Callable,
        symbol: str = "BTCUSDT",
        warmup_bars: int = 100,
    ) -> BacktestResult:
        """
        Run event-driven backtest.
        
        Args:
            data: OHLCV DataFrame
            strategy_fn: Callable(context) -> List[Dict]
                context = {
                    "bar_idx": int,
                    "current_bar": Series,
                    "history": DataFrame (up to current bar, no future),
                    "positions": Dict,
                    "equity": float,
                    "cash": float,
                }
                returns list of order dicts: [{"side": "buy", "quantity": 0.1, "stop_loss": 100, ...}]
            symbol: Symbol name
            warmup_bars: Bars to skip for warmup
            
        Returns:
            BacktestResult with trades and metrics
        """
        n = len(data)
        
        if n < warmup_bars + 50:
            logger.error(f"Insufficient data for backtest: {n} bars")
            return BacktestResult(config=self.config)
        
        # State
        equity = self.config.initial_capital
        cash = self.config.initial_capital
        positions: Dict[str, BacktestTrade] = {}
        closed_trades: List[BacktestTrade] = []
        equity_curve = [equity]
        timestamps = [data.index[warmup_bars] if hasattr(data.index, '__getitem__') else warmup_bars]
        trade_counter = 0
        peak_equity = equity
        circuit_breaker_tripped = False
        
        logger.info(f"Backtest START: {n} bars, warmup={warmup_bars}, capital=${self.config.initial_capital:,.0f}")
        
        for bar_idx in range(warmup_bars, n):
            current_bar = data.iloc[bar_idx]
            bar_time = data.index[bar_idx] if hasattr(data.index, '__getitem__') else bar_idx
            
            # 1. Update existing positions (check SL/TP)
            positions_to_close = []
            for pos_id, pos in positions.items():
                bar_high = float(current_bar.get("high", current_bar.get("close", 0)))
                bar_low = float(current_bar.get("low", current_bar.get("close", 0)))
                bar_close = float(current_bar.get("close", 0))
                
                # Track MFE/MAE
                if pos.side == "BUY":
                    pos.max_favorable = max(pos.max_favorable, (bar_high - pos.entry_price) / pos.entry_price)
                    pos.max_adverse = max(pos.max_adverse, (pos.entry_price - bar_low) / pos.entry_price)
                else:
                    pos.max_favorable = max(pos.max_favorable, (pos.entry_price - bar_low) / pos.entry_price)
                    pos.max_adverse = max(pos.max_adverse, (bar_high - pos.entry_price) / pos.entry_price)
                
                # Stop loss check
                if pos.stop_loss > 0:
                    if pos.side == "BUY" and bar_low <= pos.stop_loss:
                        positions_to_close.append((pos_id, pos.stop_loss, "stop_loss"))
                        continue
                    elif pos.side == "SELL" and bar_high >= pos.stop_loss:
                        positions_to_close.append((pos_id, pos.stop_loss, "stop_loss"))
                        continue
                
                # Take profit check
                if pos.take_profit > 0:
                    if pos.side == "BUY" and bar_high >= pos.take_profit:
                        positions_to_close.append((pos_id, pos.take_profit, "take_profit"))
                        continue
                    elif pos.side == "SELL" and bar_low <= pos.take_profit:
                        positions_to_close.append((pos_id, pos.take_profit, "take_profit"))
                        continue
            
            # Close positions
            for pos_id, exit_price, exit_reason in positions_to_close:
                pos = positions[pos_id]
                pos = self._close_position(pos, exit_price, bar_idx, bar_time, exit_reason)
                cash += pos.quantity * exit_price + pos.pnl - pos.commission
                closed_trades.append(pos)
                del positions[pos_id]
            
            # 2. Calculate current equity
            unrealized_pnl = 0
            bar_close = float(current_bar.get("close", 0))
            for pos in positions.values():
                if pos.side == "BUY":
                    unrealized_pnl += (bar_close - pos.entry_price) * pos.quantity
                else:
                    unrealized_pnl += (pos.entry_price - bar_close) * pos.quantity
            
            equity = cash + sum(p.quantity * bar_close for p in positions.values()) + unrealized_pnl
            equity_curve.append(equity)
            timestamps.append(bar_time)
            
            # 3. Circuit breaker check
            if self.config.use_circuit_breaker:
                if equity > peak_equity:
                    peak_equity = equity
                dd_pct = (peak_equity - equity) / peak_equity * 100
                if dd_pct >= self.config.circuit_breaker_dd_pct:
                    if not circuit_breaker_tripped:
                        circuit_breaker_tripped = True
                        logger.warning(f"Circuit breaker tripped at bar {bar_idx}: DD={dd_pct:.1f}%")
                        # Close all positions
                        for pos_id in list(positions.keys()):
                            pos = positions[pos_id]
                            pos = self._close_position(pos, bar_close, bar_idx, bar_time, "circuit_breaker")
                            cash += pos.quantity * bar_close + pos.pnl - pos.commission
                            closed_trades.append(pos)
                        positions.clear()
                    continue
            
            # 4. Run strategy (no look-ahead: only history up to current bar)
            if not circuit_breaker_tripped:
                context = {
                    "bar_idx": bar_idx,
                    "current_bar": current_bar,
                    "history": data.iloc[:bar_idx + 1],  # Up to and including current
                    "positions": {k: v for k, v in positions.items()},
                    "equity": equity,
                    "cash": cash,
                    "n_positions": len(positions),
                }
                
                try:
                    orders = strategy_fn(context)
                except Exception as e:
                    logger.error(f"Strategy error at bar {bar_idx}: {e}")
                    orders = []
                
                # 5. Process orders
                if orders and isinstance(orders, list):
                    for order in orders:
                        if len(positions) >= self.config.max_positions:
                            break
                        
                        side = order.get("side", "").upper()
                        if side not in ("BUY", "SELL"):
                            continue
                        
                        # Position sizing
                        quantity = order.get("quantity", 0)
                        if quantity <= 0:
                            risk_amount = equity * (self.config.risk_per_trade_pct / 100)
                            stop_loss = order.get("stop_loss", 0)
                            if stop_loss > 0 and bar_close > 0:
                                risk_per_unit = abs(bar_close - stop_loss)
                                if risk_per_unit > 0:
                                    quantity = risk_amount / risk_per_unit
                                else:
                                    quantity = risk_amount / (bar_close * 0.02)
                            else:
                                quantity = risk_amount / (bar_close * 0.02) if bar_close > 0 else 0
                        
                        if quantity <= 0:
                            continue
                        
                        # Stop loss requirement
                        stop_loss = order.get("stop_loss", 0)
                        if self.config.require_stop_loss and stop_loss <= 0:
                            continue
                        
                        # Apply slippage to entry
                        slippage = bar_close * (self.config.slippage_bps / 10000)
                        entry_price = bar_close + slippage if side == "BUY" else bar_close - slippage
                        
                        # Commission
                        commission = quantity * entry_price * (self.config.commission_pct / 100)
                        
                        trade_counter += 1
                        trade = BacktestTrade(
                            id=trade_counter,
                            symbol=symbol,
                            side=side,
                            entry_bar=bar_idx,
                            entry_time=bar_time,
                            entry_price=entry_price,
                            quantity=quantity,
                            stop_loss=stop_loss,
                            take_profit=order.get("take_profit", 0),
                            commission=commission,
                            slippage_cost=slippage * quantity,
                        )
                        
                        cash -= quantity * entry_price + commission
                        positions[f"trade_{trade_counter}"] = trade
        
        # Close remaining positions at last bar
        last_close = float(data.iloc[-1].get("close", 0))
        last_time = data.index[-1] if hasattr(data.index, '__getitem__') else n - 1
        for pos_id in list(positions.keys()):
            pos = positions[pos_id]
            pos = self._close_position(pos, last_close, n - 1, last_time, "end_of_data")
            closed_trades.append(pos)
        
        # Build result
        result = BacktestResult(
            config=self.config,
            trades=closed_trades,
            equity_curve=equity_curve,
            timestamps=timestamps,
            total_trades=len(closed_trades),
        )
        
        # Calculate metrics
        self._calculate_metrics(result)
        
        logger.info(
            f"Backtest COMPLETE: {result.total_trades} trades | "
            f"Return={result.total_return_pct:.1f}% | "
            f"Sharpe={result.sharpe_ratio:.3f} | "
            f"MaxDD={result.max_drawdown_pct:.1f}% | "
            f"WinRate={result.win_rate_pct:.1f}% | "
            f"PF={result.profit_factor:.2f}"
        )
        
        return result
    
    def _close_position(
        self, pos: BacktestTrade, exit_price: float,
        bar_idx: int, bar_time: Any, reason: str,
    ) -> BacktestTrade:
        """Close a position and calculate PnL."""
        # Apply slippage to exit
        slippage = exit_price * (self.config.slippage_bps / 10000)
        if pos.side == "BUY":
            actual_exit = exit_price - slippage
        else:
            actual_exit = exit_price + slippage
        
        # Commission
        exit_commission = pos.quantity * actual_exit * (self.config.commission_pct / 100)
        pos.commission += exit_commission
        pos.slippage_cost += slippage * pos.quantity
        
        # PnL
        if pos.side == "BUY":
            pos.pnl = (actual_exit - pos.entry_price) * pos.quantity - pos.commission
        else:
            pos.pnl = (pos.entry_price - actual_exit) * pos.quantity - pos.commission
        
        pos.pnl_pct = (pos.pnl / (pos.entry_price * pos.quantity)) * 100 if pos.entry_price > 0 else 0
        
        pos.exit_bar = bar_idx
        pos.exit_time = bar_time
        pos.exit_price = actual_exit
        pos.exit_reason = reason
        pos.bars_held = bar_idx - pos.entry_bar
        
        return pos
    
    def _calculate_metrics(self, result: BacktestResult):
        """Calculate aggregate performance metrics."""
        if not result.trades:
            return
        
        # Basic trade stats
        wins = [t for t in result.trades if t.pnl > 0]
        losses = [t for t in result.trades if t.pnl <= 0]
        
        result.win_rate_pct = (len(wins) / max(len(result.trades), 1)) * 100
        result.avg_trade_pnl = sum(t.pnl for t in result.trades) / max(len(result.trades), 1)
        result.avg_bars_held = sum(t.bars_held for t in result.trades) / max(len(result.trades), 1)
        result.total_commission = sum(t.commission for t in result.trades)
        result.total_slippage_cost = sum(t.slippage_cost for t in result.trades)
        
        # Profit factor
        gross_wins = sum(t.pnl for t in wins) if wins else 0
        gross_losses = abs(sum(t.pnl for t in losses)) if losses else 0.01
        result.profit_factor = gross_wins / max(gross_losses, 0.01)
        
        # Equity curve metrics
        eq = np.array(result.equity_curve)
        if len(eq) < 2:
            return
        
        initial = eq[0]
        final = eq[-1]
        result.total_return_pct = ((final - initial) / initial) * 100
        
        # Daily-like returns for Sharpe calculation
        returns = np.diff(eq) / eq[:-1]
        returns = returns[~np.isnan(returns)]
        
        if len(returns) > 0 and np.std(returns) > 0:
            result.sharpe_ratio = float(np.mean(returns) / np.std(returns) * np.sqrt(252))
            
            # Sortino (downside deviation only)
            downside = returns[returns < 0]
            if len(downside) > 0:
                dd_std = np.std(downside)
                result.sortino_ratio = float(np.mean(returns) / dd_std * np.sqrt(252)) if dd_std > 0 else 0
        
        # Max drawdown
        running_max = np.maximum.accumulate(eq)
        drawdowns = (eq - running_max) / running_max
        result.max_drawdown_pct = float(abs(drawdowns.min())) * 100
        
        # Calmar ratio
        if result.max_drawdown_pct > 0:
            result.calmar_ratio = result.total_return_pct / result.max_drawdown_pct
        
        # CAGR
        n_bars = len(eq)
        if n_bars > 252 and final > 0 and initial > 0:
            years = n_bars / 252
            result.cagr_pct = ((final / initial) ** (1 / years) - 1) * 100
