import pandas as pd
import numpy as np
from typing import Dict

def fisher_transform(data: pd.DataFrame, period: int = 10) -> pd.DataFrame:
    """
    Calculates the Ehlers Fisher Transform.

    The Fisher Transform converts price data into a Gaussian normal distribution,
    which helps in identifying price reversals with sharp, clear signals.
    Signals are typically generated when the Fisher line crosses its signal line.

    Args:
        data (pd.DataFrame): DataFrame containing 'high' and 'low' columns.
        period (int): The lookback period for the calculation.

    Returns:
        pd.DataFrame: A DataFrame with 'fisher' and 'fisher_signal' columns.
    """
    if 'high' not in data.columns or 'low' not in data.columns:
        raise ValueError("Input DataFrame must contain 'high' and 'low' columns.")

    # Calculate the median price
    median_price = (data['high'] + data['low']) / 2

    highest_high = median_price.rolling(window=period).max()
    lowest_low = median_price.rolling(window=period).min()

    # Value is a number between -1 and 1
    # Simplified version of Ehlers' value calculation for stability
    value = 2 * ((median_price - lowest_low) / (highest_high - lowest_low) - 0.5)
    value = value.fillna(0) # Handle initial NaNs
    value = value.clip(-0.999, 0.999) # Clip to avoid infinity in log

    # Fisher Transform calculation
    fisher = 0.5 * np.log((1 + value) / (1 - value))

    # Create a signal line (one-period lag of the Fisher line)
    fisher_signal = fisher.shift(1)

    result_df = pd.DataFrame({
        'fisher': fisher,
        'fisher_signal': fisher_signal
    }, index=data.index)

    return result_df

# Example Usage
if __name__ == '__main__':
    from core.data_feed import DataFeed
    import matplotlib.pyplot as plt

    # Fetch some data for testing
    data_feed = DataFeed(broker_config={})
    btc_data = data_feed.get_historical_data("BTC-USD", "1d", "2022-01-01", "2023-01-01")

    if btc_data is not None:
        # Calculate Fisher Transform
        fisher_df = fisher_transform(btc_data, period=10)

        # Combine with price data for plotting
        btc_data = btc_data.join(fisher_df)

        print("--- Fisher Transform Calculation ---")
        print(btc_data[['close', 'fisher', 'fisher_signal']].tail(10))
        print("------------------------------------")

        # Plotting
        fig, axes = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

        # Plot price
        axes[0].plot(btc_data.index, btc_data['close'], label='BTC Close Price')
        axes[0].set_title('BTC/USD Price')
        axes[0].legend()
        axes[0].grid(True)

        # Plot Fisher Transform
        axes[1].plot(btc_data.index, btc_data['fisher'], label='Fisher Transform', color='blue')
        axes[1].plot(btc_data.index, btc_data['fisher_signal'], label='Signal Line', color='red', linestyle='--')
        axes[1].axhline(0, color='gray', linestyle='--')
        axes[1].set_title('Ehlers Fisher Transform (10-period)')
        axes[1].legend()
        axes[1].grid(True)

        plt.tight_layout()
        # To avoid blocking in a non-interactive environment, we'll save the figure instead of showing it.
        plt.savefig("outputs/charts/fisher_transform_example.png")
        print("\nSaved example chart to outputs/charts/fisher_transform_example.png")
