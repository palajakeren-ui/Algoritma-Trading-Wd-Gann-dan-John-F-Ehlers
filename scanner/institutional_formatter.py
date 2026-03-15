"""
Institutional Formatter Module
Format outputs for institutional reporting
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import json


class InstitutionalFormatter:
    """
    Format trading data for institutional reporting standards.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.firm_name = self.config.get('firm_name', 'Gann Quant AI')
        logger.info("InstitutionalFormatter initialized")
    
    def format_trade_blotter(self, trades: List[Dict]) -> pd.DataFrame:
        """Format trades as institutional blotter"""
        if not trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades)
        
        # Standardize columns
        column_mapping = {
            'symbol': 'Symbol',
            'side': 'Side',
            'quantity': 'Qty',
            'price': 'Exec Price',
            'timestamp': 'Exec Time',
            'order_id': 'Order ID',
            'commission': 'Commission'
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Add calculated fields
        if 'Qty' in df.columns and 'Exec Price' in df.columns:
            df['Notional'] = df['Qty'] * df['Exec Price']
        
        return df
    
    def format_position_report(self, positions: List[Dict]) -> pd.DataFrame:
        """Format positions for reporting"""
        if not positions:
            return pd.DataFrame()
        
        df = pd.DataFrame(positions)
        
        # Add P&L calculations
        if 'entry_price' in df.columns and 'current_price' in df.columns:
            df['Unrealized P&L'] = (df['current_price'] - df['entry_price']) * df.get('quantity', 1)
            df['P&L %'] = ((df['current_price'] / df['entry_price']) - 1) * 100
        
        return df
    
    def format_risk_report(self, risk_data: Dict) -> Dict:
        """Format risk metrics for institutional reporting"""
        return {
            'Report Date': datetime.now().strftime('%Y-%m-%d'),
            'Firm': self.firm_name,
            'Risk Metrics': {
                'VaR (95%)': f"${risk_data.get('var_95', 0):,.2f}",
                'VaR (99%)': f"${risk_data.get('var_99', 0):,.2f}",
                'Expected Shortfall': f"${risk_data.get('es', 0):,.2f}",
                'Max Drawdown': f"{risk_data.get('max_dd', 0):.2%}",
                'Sharpe Ratio': f"{risk_data.get('sharpe', 0):.2f}",
                'Sortino Ratio': f"{risk_data.get('sortino', 0):.2f}"
            },
            'Exposure': {
                'Gross Exposure': f"${risk_data.get('gross_exposure', 0):,.2f}",
                'Net Exposure': f"${risk_data.get('net_exposure', 0):,.2f}",
                'Long Exposure': f"${risk_data.get('long_exposure', 0):,.2f}",
                'Short Exposure': f"${risk_data.get('short_exposure', 0):,.2f}"
            }
        }
    
    def format_performance_report(self, metrics: Dict) -> Dict:
        """Format performance metrics"""
        return {
            'Report Period': {
                'Start': metrics.get('start_date', ''),
                'End': metrics.get('end_date', '')
            },
            'Returns': {
                'Total Return': f"{metrics.get('total_return', 0):.2%}",
                'Annualized Return': f"{metrics.get('ann_return', 0):.2%}",
                'YTD Return': f"{metrics.get('ytd_return', 0):.2%}",
                'MTD Return': f"{metrics.get('mtd_return', 0):.2%}"
            },
            'Risk-Adjusted': {
                'Sharpe Ratio': f"{metrics.get('sharpe', 0):.2f}",
                'Sortino Ratio': f"{metrics.get('sortino', 0):.2f}",
                'Calmar Ratio': f"{metrics.get('calmar', 0):.2f}",
                'Information Ratio': f"{metrics.get('info_ratio', 0):.2f}"
            },
            'Drawdown': {
                'Max Drawdown': f"{metrics.get('max_dd', 0):.2%}",
                'Current Drawdown': f"{metrics.get('current_dd', 0):.2%}",
                'Avg Drawdown': f"{metrics.get('avg_dd', 0):.2%}"
            },
            'Trading Statistics': {
                'Total Trades': metrics.get('total_trades', 0),
                'Win Rate': f"{metrics.get('win_rate', 0):.2%}",
                'Profit Factor': f"{metrics.get('profit_factor', 0):.2f}",
                'Avg Win': f"${metrics.get('avg_win', 0):,.2f}",
                'Avg Loss': f"${metrics.get('avg_loss', 0):,.2f}"
            }
        }
    
    def generate_fix_message(self, order: Dict) -> str:
        """Generate FIX protocol message for order"""
        # Simplified FIX 4.4 format
        fix_fields = {
            '8': 'FIX.4.4',          # BeginString
            '35': 'D',                # MsgType (New Order Single)
            '49': self.firm_name,     # SenderCompID
            '11': order.get('client_order_id', ''),  # ClOrdID
            '55': order.get('symbol', ''),           # Symbol
            '54': '1' if order.get('side') == 'BUY' else '2',  # Side
            '38': str(order.get('quantity', 0)),     # OrderQty
            '40': '2' if order.get('order_type') == 'LIMIT' else '1',  # OrdType
            '44': str(order.get('price', '')),       # Price
            '60': datetime.now().strftime('%Y%m%d-%H:%M:%S')  # TransactTime
        }
        
        # Build FIX message
        body = '\x01'.join([f"{k}={v}" for k, v in fix_fields.items()])
        return body
    
    def export_to_csv(self, data: pd.DataFrame, filepath: str):
        """Export data to CSV"""
        data.to_csv(filepath, index=False)
        logger.info(f"Exported to {filepath}")
    
    def export_to_json(self, data: Dict, filepath: str):
        """Export data to JSON"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Exported to {filepath}")
