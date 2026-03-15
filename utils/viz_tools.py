"""
Visualization Tools Module
Chart and graph generation utilities
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class VizTools:
    """
    Visualization utilities for trading analysis.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.style = self.config.get('style', 'dark_background')
        
        if HAS_MATPLOTLIB:
            plt.style.use(self.style)
        
        logger.info("VizTools initialized")
    
    def plot_candlestick(
        self,
        df: pd.DataFrame,
        title: str = "Price Chart",
        figsize: Tuple[int, int] = (14, 7),
        save_path: str = None
    ):
        """Plot candlestick chart"""
        if not HAS_MATPLOTLIB:
            logger.warning("Matplotlib not installed")
            return
        
        fig, ax = plt.subplots(figsize=figsize)
        
        for i, (idx, row) in enumerate(df.iterrows()):
            color = 'green' if row['close'] >= row['open'] else 'red'
            
            # Body
            ax.bar(i, abs(row['close'] - row['open']),
                   bottom=min(row['open'], row['close']),
                   color=color, width=0.8)
            
            # Wick
            ax.vlines(i, row['low'], row['high'], color=color, linewidth=1)
        
        ax.set_title(title)
        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close()
        return fig
    
    def plot_equity_curve(
        self,
        equity: pd.Series,
        title: str = "Equity Curve",
        figsize: Tuple[int, int] = (12, 6),
        save_path: str = None
    ):
        """Plot equity curve"""
        if not HAS_MATPLOTLIB:
            return
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(equity.values, color='cyan', linewidth=2)
        ax.fill_between(range(len(equity)), equity.values, alpha=0.3)
        
        ax.set_title(title)
        ax.set_xlabel('Time')
        ax.set_ylabel('Equity')
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close()
        return fig
    
    def plot_drawdown(
        self,
        equity: pd.Series,
        title: str = "Drawdown",
        figsize: Tuple[int, int] = (12, 4),
        save_path: str = None
    ):
        """Plot drawdown chart"""
        if not HAS_MATPLOTLIB:
            return
        
        peak = equity.cummax()
        drawdown = (equity - peak) / peak * 100
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.fill_between(range(len(drawdown)), drawdown.values, color='red', alpha=0.7)
        ax.axhline(y=0, color='white', linewidth=0.5)
        
        ax.set_title(title)
        ax.set_xlabel('Time')
        ax.set_ylabel('Drawdown %')
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close()
        return fig
    
    def plot_gann_square(
        self,
        center_price: float,
        levels: Dict[str, List[float]],
        current_price: float = None,
        figsize: Tuple[int, int] = (10, 10),
        save_path: str = None
    ):
        """Plot Gann Square visualization"""
        if not HAS_MATPLOTLIB:
            return
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Draw concentric squares
        for i, level in enumerate(levels.get('resistance', [])):
            rect = mpatches.Rectangle(
                (-level/2, -level/2), level, level,
                fill=False, edgecolor='red', alpha=0.5
            )
            ax.add_patch(rect)
        
        for i, level in enumerate(levels.get('support', [])):
            rect = mpatches.Rectangle(
                (-level/2, -level/2), level, level,
                fill=False, edgecolor='green', alpha=0.5
            )
            ax.add_patch(rect)
        
        # Center point
        ax.plot(0, 0, 'wo', markersize=10)
        ax.annotate(f'${center_price:,.2f}', (0, 0), color='white', ha='center')
        
        ax.set_xlim(-center_price, center_price)
        ax.set_ylim(-center_price, center_price)
        ax.set_aspect('equal')
        ax.set_title('Gann Square')
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close()
        return fig
    
    def plot_correlation_matrix(
        self,
        df: pd.DataFrame,
        title: str = "Correlation Matrix",
        figsize: Tuple[int, int] = (10, 8),
        save_path: str = None
    ):
        """Plot correlation matrix heatmap"""
        if not HAS_MATPLOTLIB:
            return
        
        corr = df.corr()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        im = ax.imshow(corr.values, cmap='RdYlGn', vmin=-1, vmax=1)
        
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha='right')
        ax.set_yticklabels(corr.columns)
        
        plt.colorbar(im)
        ax.set_title(title)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close()
        return fig
    
    def plot_signals(
        self,
        df: pd.DataFrame,
        signals: pd.DataFrame,
        title: str = "Price with Signals",
        figsize: Tuple[int, int] = (14, 7),
        save_path: str = None
    ):
        """Plot price with buy/sell signals"""
        if not HAS_MATPLOTLIB:
            return
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(df['close'].values, color='white', linewidth=1)
        
        # Plot signals
        if 'signal' in signals.columns:
            buys = signals[signals['signal'] == 'BUY']
            sells = signals[signals['signal'] == 'SELL']
            
            for idx in buys.index:
                if idx < len(df):
                    ax.scatter(idx, df['close'].iloc[idx], color='green', marker='^', s=100)
            
            for idx in sells.index:
                if idx < len(df):
                    ax.scatter(idx, df['close'].iloc[idx], color='red', marker='v', s=100)
        
        ax.set_title(title)
        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close()
        return fig
