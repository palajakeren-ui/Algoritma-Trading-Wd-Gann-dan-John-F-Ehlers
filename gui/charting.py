import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_backtest_results(
    price_data: pd.DataFrame,
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame
) -> go.Figure:
    """
    Creates an interactive Plotly chart of the backtest results.

    Args:
        price_data (pd.DataFrame): The original OHLCV price data.
        equity_curve (pd.DataFrame): The equity curve from the backtest.
        trades (pd.DataFrame): The log of executed trades.

    Returns:
        go.Figure: A Plotly figure object.
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Trade Analysis', 'Portfolio Equity'),
        row_heights=[0.7, 0.3]
    )

    # --- Plot 1: Price and Trades ---
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=price_data.index,
        open=price_data['open'],
        high=price_data['high'],
        low=price_data['low'],
        close=price_data['close'],
        name='Price'
    ), row=1, col=1)

    # Add trade markers
    if not trades.empty:
        buy_trades = trades[trades['side'] == 'long']
        sell_trades = trades[trades['side'] == 'short']

        # Buy entry markers
        fig.add_trace(go.Scatter(
            x=buy_trades['entry_date'],
            y=buy_trades['entry_price'],
            mode='markers',
            marker=dict(color='green', symbol='triangle-up', size=10),
            name='Buy Entry'
        ), row=1, col=1)

        # Sell entry markers
        fig.add_trace(go.Scatter(
            x=sell_trades['entry_date'],
            y=sell_trades['entry_price'],
            mode='markers',
            marker=dict(color='red', symbol='triangle-down', size=10),
            name='Sell Entry'
        ), row=1, col=1)

        # Exit markers (connecting entry and exit)
        for _, trade in trades.iterrows():
            fig.add_shape(type="line",
                x0=trade['entry_date'], y0=trade['entry_price'],
                x1=trade['exit_date'], y1=trade['exit_price'],
                line=dict(color="blue" if trade['pnl'] > 0 else "orange", width=1, dash="dot"),
                row=1, col=1
            )

    # --- Plot 2: Equity Curve ---
    fig.add_trace(go.Scatter(
        x=equity_curve.index,
        y=equity_curve['equity'],
        mode='lines',
        name='Equity',
        line=dict(color='blue')
    ), row=2, col=1)

    # --- Layout and Styling ---
    fig.update_layout(
        title_text='Backtest Results',
        height=800,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Portfolio Value (USD)", row=2, col=1)

    return fig
