"""
Reporter Module
Generate trading reports and summaries
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class Reporter:
    """
    Generate comprehensive trading reports.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        logger.info("Reporter initialized")
    
    def daily_report(self, trades: List[Dict], positions: List[Dict], metrics: Dict) -> Dict:
        """Generate daily trading report"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Summarize trades
        trade_summary = self._summarize_trades(trades)
        
        # Summarize positions
        position_summary = self._summarize_positions(positions)
        
        return {
            'report_date': today,
            'report_type': 'daily',
            'trade_summary': trade_summary,
            'position_summary': position_summary,
            'performance_metrics': metrics,
            'generated_at': datetime.now().isoformat()
        }
    
    def weekly_report(self, daily_reports: List[Dict]) -> Dict:
        """Aggregate daily reports into weekly"""
        if not daily_reports:
            return {}
        
        total_pnl = sum(r.get('trade_summary', {}).get('total_pnl', 0) for r in daily_reports)
        total_trades = sum(r.get('trade_summary', {}).get('total_trades', 0) for r in daily_reports)
        
        return {
            'report_type': 'weekly',
            'period_start': daily_reports[0].get('report_date'),
            'period_end': daily_reports[-1].get('report_date'),
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'avg_daily_pnl': total_pnl / len(daily_reports) if daily_reports else 0,
            'days_reported': len(daily_reports)
        }
    
    def strategy_report(self, strategy_name: str, performance: Dict) -> Dict:
        """Generate strategy-specific report"""
        return {
            'strategy': strategy_name,
            'returns': {
                'total': performance.get('total_return', 0),
                'annualized': performance.get('annualized_return', 0),
                'monthly_avg': performance.get('avg_monthly_return', 0)
            },
            'risk': {
                'volatility': performance.get('volatility', 0),
                'max_drawdown': performance.get('max_drawdown', 0),
                'sharpe': performance.get('sharpe_ratio', 0)
            },
            'trading': {
                'total_trades': performance.get('total_trades', 0),
                'win_rate': performance.get('win_rate', 0),
                'profit_factor': performance.get('profit_factor', 0)
            }
        }
    
    def _summarize_trades(self, trades: List[Dict]) -> Dict:
        """Summarize trade activity"""
        if not trades:
            return {'total_trades': 0, 'total_pnl': 0}
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        winning = [t for t in trades if t.get('pnl', 0) > 0]
        losing = [t for t in trades if t.get('pnl', 0) < 0]
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': len(winning) / len(trades) if trades else 0,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(trades) if trades else 0,
            'gross_profit': sum(t.get('pnl', 0) for t in winning),
            'gross_loss': sum(t.get('pnl', 0) for t in losing)
        }
    
    def _summarize_positions(self, positions: List[Dict]) -> Dict:
        """Summarize current positions"""
        if not positions:
            return {'total_positions': 0}
        
        long_positions = [p for p in positions if p.get('side') == 'long']
        short_positions = [p for p in positions if p.get('side') == 'short']
        
        total_value = sum(p.get('market_value', 0) for p in positions)
        total_pnl = sum(p.get('unrealized_pnl', 0) for p in positions)
        
        return {
            'total_positions': len(positions),
            'long_count': len(long_positions),
            'short_count': len(short_positions),
            'total_market_value': total_value,
            'total_unrealized_pnl': total_pnl
        }
    
    def generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML formatted report"""
        html = f"""
        <html>
        <head>
            <title>Trading Report - {report_data.get('report_date', 'Today')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background-color: #4CAF50; color: white; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Trading Report</h1>
            <p>Date: {report_data.get('report_date', '')}</p>
            
            <h2>Trade Summary</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Trades</td><td>{report_data.get('trade_summary', {}).get('total_trades', 0)}</td></tr>
                <tr><td>Win Rate</td><td>{report_data.get('trade_summary', {}).get('win_rate', 0):.1%}</td></tr>
                <tr><td>Total P&L</td><td>${report_data.get('trade_summary', {}).get('total_pnl', 0):,.2f}</td></tr>
            </table>
            
            <h2>Position Summary</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Open Positions</td><td>{report_data.get('position_summary', {}).get('total_positions', 0)}</td></tr>
                <tr><td>Unrealized P&L</td><td>${report_data.get('position_summary', {}).get('total_unrealized_pnl', 0):,.2f}</td></tr>
            </table>
            
            <p><small>Generated: {report_data.get('generated_at', '')}</small></p>
        </body>
        </html>
        """
        return html
