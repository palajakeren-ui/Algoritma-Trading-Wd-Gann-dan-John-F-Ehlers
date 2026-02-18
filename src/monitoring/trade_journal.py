"""
Production Trade Journal
Immutable audit trail of every trade decision and execution.

In an institutional setting, the trade journal is a REGULATORY REQUIREMENT.
Every decision, signal, risk check, and execution must be logged permanently.
"""

import json
import csv
import os
import threading
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger
from dataclasses import dataclass, field, asdict


@dataclass
class TradeJournalEntry:
    """Immutable record of a trade decision."""
    timestamp: str
    trade_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    
    # Signal context
    signal_source: str = ""
    signal_score: float = 0.0
    regime: str = ""
    confidence: float = 0.0
    
    # Risk context
    risk_score: float = 0.0
    position_size_method: str = ""
    stop_loss: float = 0.0
    take_profit: float = 0.0
    drawdown_at_entry: float = 0.0
    
    # Execution context
    execution_latency_ms: float = 0.0
    slippage_bps: float = 0.0
    retry_count: int = 0
    broker: str = ""
    order_type: str = ""
    
    # Outcome
    outcome: str = ""  # 'win', 'loss', 'breakeven', 'open'
    exit_reason: str = ""  # 'take_profit', 'stop_loss', 'signal_reversal', 'manual'
    duration_minutes: float = 0.0
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0
    
    # Notes
    notes: str = ""
    tags: List[str] = field(default_factory=list)


class TradeJournal:
    """
    Persistent trade journal with multiple output formats.
    
    Features:
    - Append-only (immutable entries)
    - CSV + JSON dual format
    - Thread-safe
    - Automatic daily file rotation
    - Performance analytics
    """
    
    def __init__(self, journal_dir: str = "data/journal"):
        self.journal_dir = journal_dir
        os.makedirs(journal_dir, exist_ok=True)
        
        self._entries: List[TradeJournalEntry] = []
        self._lock = threading.Lock()
        self._current_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    def log_trade(self, entry: TradeJournalEntry):
        """Log a trade entry to journal."""
        with self._lock:
            self._entries.append(entry)
            self._write_csv(entry)
            self._write_json(entry)
        
        log_msg = (
            f"📝 JOURNAL: {entry.trade_id} | {entry.symbol} {entry.side} "
            f"{entry.quantity:.6f} @ {entry.entry_price:.4f}"
        )
        if entry.exit_price > 0:
            log_msg += (
                f" → {entry.exit_price:.4f} | PnL=${entry.pnl:.2f} "
                f"({entry.pnl_pct:.2f}%) | {entry.outcome}"
            )
        logger.info(log_msg)
    
    def log_open(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        signal_source: str = "",
        signal_score: float = 0.0,
        regime: str = "",
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        broker: str = "",
        **kwargs,
    ) -> TradeJournalEntry:
        """Convenience method to log a trade open."""
        entry = TradeJournalEntry(
            timestamp=datetime.utcnow().isoformat(),
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            signal_source=signal_source,
            signal_score=signal_score,
            regime=regime,
            stop_loss=stop_loss,
            take_profit=take_profit,
            broker=broker,
            outcome="open",
        )
        for k, v in kwargs.items():
            if hasattr(entry, k):
                setattr(entry, k, v)
        self.log_trade(entry)
        return entry
    
    def log_close(
        self,
        trade_id: str,
        exit_price: float,
        pnl: float,
        exit_reason: str = "",
        **kwargs,
    ):
        """Log a trade close (updates the matching open entry)."""
        # Find the open entry
        entry = None
        for e in reversed(self._entries):
            if e.trade_id == trade_id and e.outcome == "open":
                entry = e
                break
        
        if entry is None:
            logger.warning(f"Trade {trade_id} not found in journal for close")
            return
        
        entry.exit_price = exit_price
        entry.pnl = pnl
        entry.exit_reason = exit_reason
        
        if entry.entry_price > 0:
            if entry.side.upper() in ("BUY", "LONG"):
                entry.pnl_pct = ((exit_price - entry.entry_price) / entry.entry_price) * 100
            else:
                entry.pnl_pct = ((entry.entry_price - exit_price) / entry.entry_price) * 100
        
        entry.outcome = "win" if pnl > 0 else ("loss" if pnl < 0 else "breakeven")
        
        for k, v in kwargs.items():
            if hasattr(entry, k):
                setattr(entry, k, v)
        
        # Write the close entry
        self.log_trade(entry)
    
    def _write_csv(self, entry: TradeJournalEntry):
        """Append entry to daily CSV file."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        filepath = os.path.join(self.journal_dir, f"trades_{date_str}.csv")
        
        entry_dict = asdict(entry)
        entry_dict["tags"] = ",".join(entry.tags)
        
        file_exists = os.path.exists(filepath)
        
        try:
            with open(filepath, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=entry_dict.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(entry_dict)
        except Exception as e:
            logger.error(f"Failed to write CSV journal: {e}")
    
    def _write_json(self, entry: TradeJournalEntry):
        """Append entry to daily JSON file."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        filepath = os.path.join(self.journal_dir, f"trades_{date_str}.jsonl")
        
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                json.dump(asdict(entry), f)
                f.write("\n")
        except Exception as e:
            logger.error(f"Failed to write JSONL journal: {e}")
    
    def get_performance_summary(self, last_n: int = None) -> Dict:
        """Get performance analytics from journal entries."""
        entries = self._entries
        if last_n:
            entries = entries[-last_n:]
        
        closed = [e for e in entries if e.outcome in ("win", "loss", "breakeven")]
        
        if not closed:
            return {"total_trades": 0}
        
        wins = [e for e in closed if e.outcome == "win"]
        losses = [e for e in closed if e.outcome == "loss"]
        
        total_pnl = sum(e.pnl for e in closed)
        win_pnl = sum(e.pnl for e in wins) if wins else 0
        loss_pnl = sum(abs(e.pnl) for e in losses) if losses else 0
        
        return {
            "total_trades": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": round(len(wins) / max(len(closed), 1) * 100, 1),
            "total_pnl": round(total_pnl, 2),
            "avg_pnl": round(total_pnl / max(len(closed), 1), 2),
            "avg_win": round(sum(e.pnl for e in wins) / max(len(wins), 1), 2),
            "avg_loss": round(sum(e.pnl for e in losses) / max(len(losses), 1), 2),
            "profit_factor": round(win_pnl / max(loss_pnl, 0.01), 2),
            "avg_slippage_bps": round(
                sum(e.slippage_bps for e in closed) / max(len(closed), 1), 2
            ),
            "avg_latency_ms": round(
                sum(e.execution_latency_ms for e in closed) / max(len(closed), 1), 1
            ),
            "by_signal_source": self._by_field(closed, "signal_source"),
            "by_regime": self._by_field(closed, "regime"),
        }
    
    @staticmethod
    def _by_field(entries, field: str) -> Dict:
        """Group performance by a specific field."""
        groups = {}
        for e in entries:
            val = getattr(e, field, "unknown") or "unknown"
            if val not in groups:
                groups[val] = {"trades": 0, "pnl": 0.0, "wins": 0}
            groups[val]["trades"] += 1
            groups[val]["pnl"] = round(groups[val]["pnl"] + e.pnl, 2)
            if e.outcome == "win":
                groups[val]["wins"] += 1
        
        for val in groups:
            groups[val]["win_rate"] = round(
                groups[val]["wins"] / max(groups[val]["trades"], 1) * 100, 1
            )
        
        return groups
