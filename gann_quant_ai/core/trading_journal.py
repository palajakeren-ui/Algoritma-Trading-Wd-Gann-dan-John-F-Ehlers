"""
Trading Journal & Reporting System
Comprehensive trade logging and performance analytics.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv


@dataclass
class TradeEntry:
    """Single trade entry for journal."""
    id: str
    symbol: str
    side: str  # buy/sell
    entry_time: datetime
    entry_price: float
    quantity: float
    leverage: int = 1
    
    # Exit info (filled when closed)
    exit_time: datetime = None
    exit_price: float = None
    
    # Results
    pnl: float = 0.0
    pnl_pct: float = 0.0
    fees: float = 0.0
    
    # Metadata
    signal_type: str = ""
    signal_confidence: float = 0.0
    strategy: str = ""
    timeframe: str = ""
    exchange: str = ""
    account_id: str = ""
    
    # Risk
    stop_loss: float = None
    take_profit: float = None
    risk_reward: float = None
    
    # Notes
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Status
    is_open: bool = True
    is_winner: bool = False
    
    def calculate_pnl(self):
        """Calculate P&L when trade is closed."""
        if self.exit_price is None:
            return
        
        if self.side == 'buy':
            self.pnl = (self.exit_price - self.entry_price) * self.quantity * self.leverage - self.fees
            self.pnl_pct = (self.exit_price - self.entry_price) / self.entry_price * 100 * self.leverage
        else:
            self.pnl = (self.entry_price - self.exit_price) * self.quantity * self.leverage - self.fees
            self.pnl_pct = (self.entry_price - self.exit_price) / self.entry_price * 100 * self.leverage
        
        self.is_winner = self.pnl > 0
        self.is_open = False
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'entry_time': self.entry_time.isoformat(),
            'entry_price': self.entry_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'leverage': self.leverage,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'fees': self.fees,
            'signal_type': self.signal_type,
            'signal_confidence': self.signal_confidence,
            'strategy': self.strategy,
            'timeframe': self.timeframe,
            'exchange': self.exchange,
            'account_id': self.account_id,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_reward': self.risk_reward,
            'notes': self.notes,
            'tags': self.tags,
            'is_open': self.is_open,
            'is_winner': self.is_winner
        }


@dataclass
class PerformanceMetrics:
    """Trading performance metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    avg_trade: float = 0.0
    avg_hold_time_hours: float = 0.0
    
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 2),
            'total_pnl': round(self.total_pnl, 2),
            'gross_profit': round(self.gross_profit, 2),
            'gross_loss': round(self.gross_loss, 2),
            'profit_factor': round(self.profit_factor, 2),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'largest_win': round(self.largest_win, 2),
            'largest_loss': round(self.largest_loss, 2),
            'avg_trade': round(self.avg_trade, 2),
            'avg_hold_time_hours': round(self.avg_hold_time_hours, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'max_drawdown_pct': round(self.max_drawdown_pct, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'max_consecutive_wins': self.max_consecutive_wins,
            'max_consecutive_losses': self.max_consecutive_losses
        }


class TradingJournal:
    """
    Trading Journal & Reporting System.
    
    Features:
    - Trade logging with full metadata
    - Performance analytics
    - Equity curve tracking
    - Strategy analysis
    - Export to CSV/JSON
    - Daily/weekly/monthly reports
    """
    
    def __init__(self, journal_path: str = None):
        self.journal_path = Path(journal_path or "outputs/journal")
        self.journal_path.mkdir(parents=True, exist_ok=True)
        
        # Trade storage
        self.trades: Dict[str, TradeEntry] = {}
        self.closed_trades: List[TradeEntry] = []
        
        # Equity curve
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.initial_capital: float = 10000.0
        
        # Load existing journal
        self._load_journal()
        
        logger.info("TradingJournal initialized")
    
    # ========================
    # Trade Management
    # ========================
    
    def log_trade_entry(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        leverage: int = 1,
        signal_type: str = "",
        signal_confidence: float = 0.0,
        strategy: str = "",
        timeframe: str = "",
        exchange: str = "",
        account_id: str = "",
        stop_loss: float = None,
        take_profit: float = None,
        notes: str = "",
        tags: List[str] = None
    ) -> str:
        """Log a new trade entry."""
        trade_id = f"TRADE_{int(datetime.now().timestamp() * 1000)}"
        
        # Calculate R:R
        risk_reward = None
        if stop_loss and take_profit:
            if side == 'buy':
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
            
            if risk > 0:
                risk_reward = reward / risk
        
        trade = TradeEntry(
            id=trade_id,
            symbol=symbol,
            side=side,
            entry_time=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage,
            signal_type=signal_type,
            signal_confidence=signal_confidence,
            strategy=strategy,
            timeframe=timeframe,
            exchange=exchange,
            account_id=account_id,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=risk_reward,
            notes=notes,
            tags=tags or []
        )
        
        self.trades[trade_id] = trade
        self._save_journal()
        
        logger.info(f"Trade logged: {trade_id} - {side.upper()} {quantity} {symbol} @ {entry_price}")
        
        return trade_id
    
    def log_trade_exit(
        self,
        trade_id: str,
        exit_price: float,
        fees: float = 0.0,
        notes: str = ""
    ) -> Optional[TradeEntry]:
        """Log trade exit."""
        if trade_id not in self.trades:
            logger.warning(f"Trade not found: {trade_id}")
            return None
        
        trade = self.trades[trade_id]
        trade.exit_time = datetime.now()
        trade.exit_price = exit_price
        trade.fees = fees
        
        if notes:
            trade.notes += f" | Exit: {notes}"
        
        # Calculate P&L
        trade.calculate_pnl()
        
        # Move to closed trades
        self.closed_trades.append(trade)
        del self.trades[trade_id]
        
        # Update equity curve
        current_equity = self.equity_curve[-1][1] if self.equity_curve else self.initial_capital
        new_equity = current_equity + trade.pnl
        self.equity_curve.append((datetime.now(), new_equity))
        
        self._save_journal()
        
        logger.info(f"Trade closed: {trade_id} - P&L: ${trade.pnl:.2f} ({trade.pnl_pct:+.2f}%)")
        
        return trade
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades."""
        return [t.to_dict() for t in self.trades.values()]
    
    def get_closed_trades(self, limit: int = 100) -> List[Dict]:
        """Get closed trades."""
        return [t.to_dict() for t in self.closed_trades[-limit:]]
    
    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Get trade by ID."""
        if trade_id in self.trades:
            return self.trades[trade_id].to_dict()
        
        for trade in self.closed_trades:
            if trade.id == trade_id:
                return trade.to_dict()
        
        return None
    
    # ========================
    # Analytics
    # ========================
    
    def calculate_metrics(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        symbol: str = None,
        strategy: str = None
    ) -> PerformanceMetrics:
        """Calculate performance metrics."""
        metrics = PerformanceMetrics()
        
        # Filter trades
        trades = self.closed_trades.copy()
        
        if start_date:
            trades = [t for t in trades if t.entry_time >= start_date]
        if end_date:
            trades = [t for t in trades if t.entry_time <= end_date]
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        if strategy:
            trades = [t for t in trades if t.strategy == strategy]
        
        if not trades:
            return metrics
        
        metrics.total_trades = len(trades)
        
        # Win/Loss
        winners = [t for t in trades if t.is_winner]
        losers = [t for t in trades if not t.is_winner]
        
        metrics.winning_trades = len(winners)
        metrics.losing_trades = len(losers)
        metrics.win_rate = len(winners) / len(trades) * 100 if trades else 0
        
        # P&L
        metrics.total_pnl = sum(t.pnl for t in trades)
        metrics.gross_profit = sum(t.pnl for t in winners)
        metrics.gross_loss = abs(sum(t.pnl for t in losers))
        
        if metrics.gross_loss > 0:
            metrics.profit_factor = metrics.gross_profit / metrics.gross_loss
        
        # Averages
        if winners:
            metrics.avg_win = metrics.gross_profit / len(winners)
            metrics.largest_win = max(t.pnl for t in winners)
        
        if losers:
            metrics.avg_loss = metrics.gross_loss / len(losers)
            metrics.largest_loss = abs(min(t.pnl for t in losers))
        
        metrics.avg_trade = metrics.total_pnl / len(trades)
        
        # Hold time
        hold_times = []
        for t in trades:
            if t.exit_time and t.entry_time:
                hold_hours = (t.exit_time - t.entry_time).total_seconds() / 3600
                hold_times.append(hold_hours)
        
        if hold_times:
            metrics.avg_hold_time_hours = np.mean(hold_times)
        
        # Drawdown
        if self.equity_curve:
            equity_values = [e[1] for e in self.equity_curve]
            peak = equity_values[0]
            max_dd = 0
            max_dd_pct = 0
            
            for eq in equity_values:
                if eq > peak:
                    peak = eq
                dd = peak - eq
                dd_pct = dd / peak * 100 if peak > 0 else 0
                
                if dd > max_dd:
                    max_dd = dd
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
            
            metrics.max_drawdown = max_dd
            metrics.max_drawdown_pct = max_dd_pct
        
        # Consecutive wins/losses
        current_streak = 0
        streak_type = None
        
        for t in trades:
            if t.is_winner:
                if streak_type == 'win':
                    current_streak += 1
                else:
                    current_streak = 1
                    streak_type = 'win'
                metrics.max_consecutive_wins = max(metrics.max_consecutive_wins, current_streak)
            else:
                if streak_type == 'loss':
                    current_streak += 1
                else:
                    current_streak = 1
                    streak_type = 'loss'
                metrics.max_consecutive_losses = max(metrics.max_consecutive_losses, current_streak)
        
        # Sharpe Ratio (simplified)
        if len(trades) > 1:
            returns = [t.pnl_pct for t in trades]
            if np.std(returns) > 0:
                metrics.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        
        return metrics
    
    def get_equity_curve(self) -> List[Dict]:
        """Get equity curve data."""
        return [
            {'timestamp': ts.isoformat(), 'equity': eq}
            for ts, eq in self.equity_curve
        ]
    
    def get_daily_pnl(self, days: int = 30) -> List[Dict]:
        """Get daily P&L."""
        start_date = datetime.now() - timedelta(days=days)
        
        daily = {}
        for trade in self.closed_trades:
            if trade.exit_time and trade.exit_time >= start_date:
                date_key = trade.exit_time.strftime('%Y-%m-%d')
                if date_key not in daily:
                    daily[date_key] = {'pnl': 0, 'trades': 0, 'wins': 0}
                daily[date_key]['pnl'] += trade.pnl
                daily[date_key]['trades'] += 1
                if trade.is_winner:
                    daily[date_key]['wins'] += 1
        
        return [
            {
                'date': date,
                'pnl': round(data['pnl'], 2),
                'trades': data['trades'],
                'win_rate': round(data['wins'] / data['trades'] * 100, 1) if data['trades'] > 0 else 0
            }
            for date, data in sorted(daily.items())
        ]
    
    def get_symbol_stats(self) -> List[Dict]:
        """Get stats by symbol."""
        symbol_stats = {}
        
        for trade in self.closed_trades:
            if trade.symbol not in symbol_stats:
                symbol_stats[trade.symbol] = {
                    'symbol': trade.symbol,
                    'trades': 0,
                    'wins': 0,
                    'pnl': 0
                }
            
            symbol_stats[trade.symbol]['trades'] += 1
            symbol_stats[trade.symbol]['pnl'] += trade.pnl
            if trade.is_winner:
                symbol_stats[trade.symbol]['wins'] += 1
        
        return [
            {
                **stats,
                'pnl': round(stats['pnl'], 2),
                'win_rate': round(stats['wins'] / stats['trades'] * 100, 1) if stats['trades'] > 0 else 0
            }
            for stats in symbol_stats.values()
        ]
    
    # ========================
    # Export
    # ========================
    
    def export_to_csv(self, filepath: str = None) -> str:
        """Export trades to CSV."""
        filepath = filepath or str(self.journal_path / f"trades_{datetime.now().strftime('%Y%m%d')}.csv")
        
        all_trades = list(self.trades.values()) + self.closed_trades
        
        if not all_trades:
            return filepath
        
        fieldnames = list(all_trades[0].to_dict().keys())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for trade in all_trades:
                writer.writerow(trade.to_dict())
        
        logger.info(f"Trades exported to: {filepath}")
        return filepath
    
    def export_to_json(self, filepath: str = None) -> str:
        """Export trades to JSON."""
        filepath = filepath or str(self.journal_path / f"trades_{datetime.now().strftime('%Y%m%d')}.json")
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'open_trades': [t.to_dict() for t in self.trades.values()],
            'closed_trades': [t.to_dict() for t in self.closed_trades],
            'metrics': self.calculate_metrics().to_dict(),
            'equity_curve': self.get_equity_curve()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Journal exported to: {filepath}")
        return filepath
    
    # ========================
    # Persistence
    # ========================
    
    def _save_journal(self):
        """Save journal to disk."""
        filepath = self.journal_path / "journal.json"
        
        data = {
            'initial_capital': self.initial_capital,
            'open_trades': [t.to_dict() for t in self.trades.values()],
            'closed_trades': [t.to_dict() for t in self.closed_trades],
            'equity_curve': [(ts.isoformat(), eq) for ts, eq in self.equity_curve],
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_journal(self):
        """Load journal from disk."""
        filepath = self.journal_path / "journal.json"
        
        if not filepath.exists():
            # Initialize equity curve
            self.equity_curve = [(datetime.now(), self.initial_capital)]
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.initial_capital = data.get('initial_capital', 10000)
            
            # Load equity curve
            self.equity_curve = [
                (datetime.fromisoformat(ts), eq)
                for ts, eq in data.get('equity_curve', [])
            ]
            
            if not self.equity_curve:
                self.equity_curve = [(datetime.now(), self.initial_capital)]
            
            # Load closed trades
            for td in data.get('closed_trades', []):
                trade = TradeEntry(
                    id=td['id'],
                    symbol=td['symbol'],
                    side=td['side'],
                    entry_time=datetime.fromisoformat(td['entry_time']),
                    entry_price=td['entry_price'],
                    quantity=td['quantity'],
                    leverage=td.get('leverage', 1),
                    exit_time=datetime.fromisoformat(td['exit_time']) if td.get('exit_time') else None,
                    exit_price=td.get('exit_price'),
                    pnl=td.get('pnl', 0),
                    pnl_pct=td.get('pnl_pct', 0),
                    fees=td.get('fees', 0),
                    signal_type=td.get('signal_type', ''),
                    strategy=td.get('strategy', ''),
                    is_open=False,
                    is_winner=td.get('is_winner', False)
                )
                self.closed_trades.append(trade)
            
            logger.info(f"Loaded {len(self.closed_trades)} trades from journal")
            
        except Exception as e:
            logger.error(f"Failed to load journal: {e}")
            self.equity_curve = [(datetime.now(), self.initial_capital)]


# Global instance
_journal: Optional[TradingJournal] = None


def get_trading_journal() -> TradingJournal:
    """Get or create trading journal."""
    global _journal
    if _journal is None:
        _journal = TradingJournal()
    return _journal


if __name__ == "__main__":
    # Test journal
    journal = TradingJournal()
    
    # Log a trade
    trade_id = journal.log_trade_entry(
        symbol="BTC/USDT",
        side="buy",
        entry_price=45000,
        quantity=0.1,
        leverage=5,
        signal_type="STRONG_BUY",
        signal_confidence=85.0,
        strategy="Gann + ML",
        stop_loss=44000,
        take_profit=48000,
        notes="Good setup"
    )
    
    # Exit trade
    journal.log_trade_exit(
        trade_id=trade_id,
        exit_price=47000,
        fees=10
    )
    
    # Get metrics
    metrics = journal.calculate_metrics()
    print("\n=== Performance Metrics ===")
    print(json.dumps(metrics.to_dict(), indent=2))
    
    # Export
    journal.export_to_json()
