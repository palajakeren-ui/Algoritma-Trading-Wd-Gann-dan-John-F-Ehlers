"""
Report Generator Module
Generates comprehensive trading reports
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger
import json


@dataclass
class ReportSection:
    title: str
    content: str
    data: Optional[Dict] = None


class ReportGenerator:
    """Generates comprehensive trading and analysis reports."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("ReportGenerator initialized")
    
    def generate_market_summary(self, data: pd.DataFrame, symbol: str = "UNKNOWN") -> Dict:
        """Generate market summary section."""
        if data is None or data.empty:
            return {'error': 'No data available'}
        
        current = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else current
        
        change = float(current['close'] - prev['close'])
        change_pct = (change / prev['close']) * 100 if prev['close'] != 0 else 0
        
        # Calculate period metrics
        high_52w = float(data['high'].max())
        low_52w = float(data['low'].min())
        avg_volume = float(data['volume'].mean()) if 'volume' in data else 0
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': float(current['close']),
            'daily_change': round(change, 2),
            'daily_change_pct': round(change_pct, 2),
            'day_high': float(current['high']),
            'day_low': float(current['low']),
            'period_high': high_52w,
            'period_low': low_52w,
            'avg_volume': avg_volume,
            'data_points': len(data)
        }
    
    def generate_technical_analysis(self, data: pd.DataFrame) -> Dict:
        """Generate technical analysis section."""
        df = data.copy()
        
        # Calculate indicators
        df['sma_10'] = df['close'].rolling(10).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        current = df.iloc[-1]
        
        # Trend analysis
        trend = "bullish" if current['sma_10'] > current['sma_20'] else "bearish"
        longer_trend = "bullish" if current['sma_20'] > current['sma_50'] else "bearish"
        
        # RSI analysis
        rsi = float(current['rsi']) if not pd.isna(current['rsi']) else 50
        if rsi > 70:
            rsi_signal = "overbought"
        elif rsi < 30:
            rsi_signal = "oversold"
        else:
            rsi_signal = "neutral"
        
        return {
            'sma_10': round(float(current['sma_10']), 2) if not pd.isna(current['sma_10']) else None,
            'sma_20': round(float(current['sma_20']), 2) if not pd.isna(current['sma_20']) else None,
            'sma_50': round(float(current['sma_50']), 2) if not pd.isna(current['sma_50']) else None,
            'rsi': round(rsi, 2),
            'rsi_signal': rsi_signal,
            'short_term_trend': trend,
            'medium_term_trend': longer_trend,
            'overall_bias': 'bullish' if trend == 'bullish' and longer_trend == 'bullish' else
                           'bearish' if trend == 'bearish' and longer_trend == 'bearish' else 'neutral'
        }
    
    def generate_risk_metrics(self, data: pd.DataFrame) -> Dict:
        """Generate risk metrics section."""
        returns = data['close'].pct_change().dropna()
        
        if len(returns) < 2:
            return {'error': 'Insufficient data for risk metrics'}
        
        # Calculate metrics
        volatility_daily = float(returns.std())
        volatility_annual = volatility_daily * np.sqrt(252)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        avg_return = float(returns.mean()) * 252
        sharpe = (avg_return - 0.02) / volatility_annual if volatility_annual > 0 else 0
        
        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = float(drawdown.min())
        
        # VaR (95%)
        var_95 = float(np.percentile(returns, 5))
        
        return {
            'daily_volatility': round(volatility_daily * 100, 2),
            'annual_volatility': round(volatility_annual * 100, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(max_dd * 100, 2),
            'var_95': round(var_95 * 100, 2),
            'avg_daily_return': round(float(returns.mean()) * 100, 4)
        }
    
    def generate_trading_summary(self, trades: List[Dict]) -> Dict:
        """Generate trading summary from trade list."""
        if not trades:
            return {'total_trades': 0, 'message': 'No trades to analyze'}
        
        df = pd.DataFrame(trades)
        
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]
        
        total_pnl = float(df['pnl'].sum())
        win_rate = len(wins) / len(df) * 100 if len(df) > 0 else 0
        
        avg_win = float(wins['pnl'].mean()) if len(wins) > 0 else 0
        avg_loss = float(losses['pnl'].mean()) if len(losses) > 0 else 0
        
        profit_factor = abs(wins['pnl'].sum() / losses['pnl'].sum()) if losses['pnl'].sum() != 0 else float('inf')
        
        return {
            'total_trades': len(df),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'Infinite',
            'largest_win': round(float(wins['pnl'].max()), 2) if len(wins) > 0 else 0,
            'largest_loss': round(float(losses['pnl'].min()), 2) if len(losses) > 0 else 0
        }
    
    def generate_full_report(
        self,
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        trades: List[Dict] = None,
        analysis_results: Dict = None
    ) -> Dict:
        """Generate complete report."""
        report = {
            'report_id': f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generated_at': datetime.now().isoformat(),
            'symbol': symbol,
            'sections': {}
        }
        
        # Market summary
        report['sections']['market_summary'] = self.generate_market_summary(data, symbol)
        
        # Technical analysis
        report['sections']['technical_analysis'] = self.generate_technical_analysis(data)
        
        # Risk metrics
        report['sections']['risk_metrics'] = self.generate_risk_metrics(data)
        
        # Trading summary
        if trades:
            report['sections']['trading_summary'] = self.generate_trading_summary(trades)
        
        # Additional analysis
        if analysis_results:
            report['sections']['additional_analysis'] = analysis_results
        
        # Generate executive summary
        report['executive_summary'] = self._generate_executive_summary(report)
        
        return report
    
    def _generate_executive_summary(self, report: Dict) -> str:
        """Generate executive summary text."""
        sections = report.get('sections', {})
        
        parts = [f"Report for {report['symbol']} generated on {report['generated_at'][:10]}."]
        
        if 'market_summary' in sections:
            ms = sections['market_summary']
            parts.append(f"Current price: {ms.get('current_price', 'N/A')}, "
                        f"change: {ms.get('daily_change_pct', 0):.2f}%.")
        
        if 'technical_analysis' in sections:
            ta = sections['technical_analysis']
            parts.append(f"Technical bias: {ta.get('overall_bias', 'neutral')}. "
                        f"RSI: {ta.get('rsi', 50):.0f} ({ta.get('rsi_signal', 'neutral')}).")
        
        if 'risk_metrics' in sections:
            rm = sections['risk_metrics']
            parts.append(f"Volatility: {rm.get('annual_volatility', 0):.1f}% annual. "
                        f"Max drawdown: {rm.get('max_drawdown', 0):.1f}%.")
        
        if 'trading_summary' in sections:
            ts = sections['trading_summary']
            parts.append(f"Trading: {ts.get('total_trades', 0)} trades, "
                        f"win rate: {ts.get('win_rate', 0):.1f}%.")
        
        return " ".join(parts)
    
    def export_to_json(self, report: Dict, filepath: str = None) -> str:
        """Export report to JSON file."""
        if filepath is None:
            filepath = f"outputs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filepath


if __name__ == "__main__":
    # Test with sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1D')
    np.random.seed(42)
    
    price = 50000
    prices = [price]
    for _ in range(99):
        price = price * (1 + np.random.randn() * 0.015)
        prices.append(price)
    
    data = pd.DataFrame({
        'open': [p * 0.998 for p in prices],
        'high': [p * 1.015 for p in prices],
        'low': [p * 0.985 for p in prices],
        'close': prices,
        'volume': np.random.uniform(1e9, 5e9, 100)
    }, index=dates)
    
    trades = [
        {'entry_date': '2024-01-10', 'exit_date': '2024-01-15', 'side': 'BUY', 'pnl': 500},
        {'entry_date': '2024-01-20', 'exit_date': '2024-01-25', 'side': 'SELL', 'pnl': -200},
        {'entry_date': '2024-02-01', 'exit_date': '2024-02-05', 'side': 'BUY', 'pnl': 800}
    ]
    
    generator = ReportGenerator()
    report = generator.generate_full_report(data, 'BTC-USD', trades)
    
    print("\n=== Report Summary ===")
    print(report['executive_summary'])
