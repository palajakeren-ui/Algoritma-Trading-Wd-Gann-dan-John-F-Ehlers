import pandas as pd
from loguru import logger
from typing import Dict, Optional

# Import specific Ehlers indicator functions
from modules.ehlers.fisher_transform import fisher_transform
from modules.ehlers.mama import mama
from modules.ehlers.cyber_cycle import cyber_cycle

class EhlersEngine:
    """
    The main engine for calculating various John F. Ehlers indicators.
    It reads the configuration and applies the specified indicators to the price data.
    """
    def __init__(self, ehlers_config: Dict):
        """
        Initializes the EhlersEngine with its configuration.

        Args:
            ehlers_config (Dict): A dictionary containing all Ehlers-related settings.
        """
        self.config = ehlers_config
        logger.info("EhlersEngine initialized.")

    def calculate_all_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all enabled Ehlers indicators and appends them to the price data.

        Args:
            price_data (pd.DataFrame): The input OHLCV data.

        Returns:
            pd.DataFrame: The original DataFrame augmented with the calculated indicator columns.
        """
        if price_data.empty:
            logger.warning("Cannot calculate Ehlers indicators: price_data is empty.")
            return price_data

        logger.info("Calculating all enabled Ehlers indicators...")

        # Create a copy to avoid modifying the original DataFrame
        augmented_data = price_data.copy()

        # --- Fisher Transform ---
        if "fisher_transform" in self.config:
            params = self.config["fisher_transform"]
            try:
                fisher_df = fisher_transform(augmented_data, period=params.get('period', 10))
                augmented_data = augmented_data.join(fisher_df)
                logger.debug("Fisher Transform calculated and added.")
            except Exception as e:
                logger.error(f"Failed to calculate Fisher Transform: {e}")

        # --- MAMA ---
        if "mama" in self.config:
            params = self.config["mama"]
            try:
                mama_df = mama(augmented_data, fast_limit=params.get('fast_limit', 0.5), slow_limit=params.get('slow_limit', 0.05))
                augmented_data = augmented_data.join(mama_df)
                logger.debug("MAMA indicator calculated and added.")
            except Exception as e:
                logger.error(f"Failed to calculate MAMA: {e}")

        # --- Cyber Cycle ---
        if "cyber_cycle" in self.config:
            params = self.config["cyber_cycle"]
            try:
                cycle_df = cyber_cycle(augmented_data, alpha=params.get('alpha', 0.07))
                augmented_data = augmented_data.join(cycle_df)
                logger.debug("Cyber Cycle indicator calculated and added.")
            except Exception as e:
                logger.error(f"Failed to calculate Cyber Cycle: {e}")

        logger.success("Ehlers indicator calculation complete.")
        return augmented_data

# Example Usage
if __name__ == '__main__':
    from core.data_feed import DataFeed

    # 1. Load mock configuration
    mock_ehlers_config = {
        "fisher_transform": {
            "period": 15
        },
        "mama": { # Example of a configured but not implemented indicator
            "fast_limit": 0.5,
            "slow_limit": 0.05
        }
    }

    # 2. Fetch some real data for testing
    data_feed = DataFeed(broker_config={})
    btc_data = data_feed.get_historical_data("BTC-USD", "1d", "2022-01-01")

    if btc_data is not None:
        # 3. Initialize and run the engine
        ehlers_engine = EhlersEngine(ehlers_config=mock_ehlers_config)
        data_with_indicators = ehlers_engine.calculate_all_indicators(btc_data)

        print("\n--- Ehlers Engine Test ---")
        # Print the last 5 rows with the new indicator columns
        print(data_with_indicators[['close', 'fisher', 'fisher_signal']].tail())
        print("-" * 28)
