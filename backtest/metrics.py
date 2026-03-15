import pandas as pd
import numpy as np
from loguru import logger

def calculate_performance_metrics(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    initial_capital: float
) -> dict:
    """
    Calculates key performance metrics from backtest results.

    Args:
        equity_curve (pd.DataFrame): DataFrame of portfolio equity over time.
        trades (pd.DataFrame): DataFrame of all executed trades.
        initial_capital (float): The starting capital.

    Returns:
        dict: A dictionary of calculated performance metrics.
    """
    logger.info("Calculating performance metrics...")

    if equity_curve.empty:
        logger.warning("Equity curve is empty, cannot calculate metrics.")
        return {}

    metrics = {}

    # --- Profitability Metrics ---
    final_equity = equity_curve['equity'].iloc[-1]
    metrics['Final Portfolio Value'] = final_equity
    metrics['Total Net Profit'] = final_equity - initial_capital
    metrics['Total Return (%)'] = ((final_equity / initial_capital) - 1) * 100

    # --- Trade Metrics ---
    if not trades.empty:
        metrics['Total Trades'] = len(trades)
        wins = trades[trades['pnl'] > 0]
        losses = trades[trades['pnl'] <= 0]
        metrics['Winning Trades'] = len(wins)
        metrics['Losing Trades'] = len(losses)
        metrics['Win Rate (%)'] = (len(wins) / len(trades) * 100) if len(trades) > 0 else 0
        metrics['Average Win ($)'] = wins['pnl'].mean()
        metrics['Average Loss ($)'] = losses['pnl'].mean()
        metrics['Profit Factor'] = abs(wins['pnl'].sum() / losses['pnl'].sum()) if losses['pnl'].sum() != 0 else np.inf
        metrics['Avg Trade PnL ($)'] = trades['pnl'].mean()
        metrics['Expectancy ($)'] = (wins['pnl'].mean() * (metrics['Win Rate (%)'] / 100)) + (losses['pnl'].mean() * (1 - (metrics['Win Rate (%)'] / 100)))

    # --- Risk & Return Metrics ---
    returns = equity_curve['equity'].pct_change().dropna()

    # Sharpe Ratio (assuming 0 risk-free rate and daily returns)
    if returns.std() != 0:
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) # Annualized
    else:
        sharpe_ratio = 0.0
    metrics['Sharpe Ratio'] = sharpe_ratio

    # Max Drawdown
    cumulative_max = equity_curve['equity'].cummax()
    drawdown = (equity_curve['equity'] - cumulative_max) / cumulative_max
    metrics['Max Drawdown (%)'] = abs(drawdown.min() * 100)

    # Calmar Ratio
    annual_return = returns.mean() * 252
    metrics['Calmar Ratio'] = annual_return / abs(drawdown.min()) if drawdown.min() != 0 else np.inf

    logger.success("Performance metrics calculated.")

    # Format metrics for printing
    formatted_metrics = {k: (f"{v:.2f}" if isinstance(v, (int, float)) else v) for k, v in metrics.items()}
    return formatted_metrics

# Example Usage
if __name__ == '__main__':
    # Create mock backtest results
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=100))
    equity = 10000 * (1 + np.random.randn(100).cumsum() * 0.001)
    mock_equity_curve = pd.DataFrame({'equity': equity}, index=dates)

    mock_trades = pd.DataFrame([
        {'pnl': 200}, {'pnl': -100}, {'pnl': 300}, {'pnl': -50}, {'pnl': 150}
    ])

    initial_cap = 10000.0

    # Calculate metrics
    performance = calculate_performance_metrics(mock_equity_curve, mock_trades, initial_cap)

    print("--- Performance Metrics Test ---")
    import json
    print(json.dumps(performance, indent=2))
    print("--------------------------------")
