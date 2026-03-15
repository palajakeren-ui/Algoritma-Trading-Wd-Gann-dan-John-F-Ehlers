import pandas as pd
from loguru import logger
from typing import Dict, Tuple, Optional

def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates the Average True Range (ATR)."""
    high_low = data['high'] - data['low']
    high_close = (data['high'] - data['close'].shift()).abs()
    low_close = (data['low'] - data['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

class RiskManager:
    """
    Manages risk parameters for trades, such as stop loss and take profit levels.
    """
    def __init__(self, risk_config: Dict, price_data: pd.DataFrame):
        """
        Initializes the RiskManager.

        Args:
            risk_config (Dict): The risk configuration dictionary.
            price_data (pd.DataFrame): The full history of price data, needed for ATR calculation.
        """
        self.config = risk_config
        self.price_data = price_data
        self._prepare_indicators()
        logger.info("RiskManager initialized.")

    def _prepare_indicators(self):
        """Pre-calculates any indicators needed for risk management, like ATR."""
        atr_period = self.config.get("atr_period", 14)
        self.price_data['atr'] = calculate_atr(self.price_data, period=atr_period)

    def get_exit_levels(
        self,
        entry_price: float,
        trade_side: str,
        timestamp: pd.Timestamp
    ) -> Optional[Tuple[float, float]]:
        """
        Determines the stop loss and take profit levels for a new trade.

        Args:
            entry_price (float): The entry price of the trade.
            trade_side (str): 'long' or 'short'.
            timestamp (pd.Timestamp): The timestamp of the trade entry.

        Returns:
            Optional[Tuple[float, float]]: A tuple of (stop_loss, take_profit), or None if invalid.
        """
        sl_method = self.config.get("stop_loss_method", "percentage")
        tp_method = self.config.get("take_profit_method", "rr_ratio")
        rr_ratio = self.config.get("risk_reward_ratio", 2.0)

        stop_loss = 0.0

        # --- Calculate Stop Loss ---
        if sl_method == "atr":
            atr_multiplier = self.config.get("atr_multiplier", 2.0)
            atr_value = self.price_data.at[timestamp, 'atr']
            if pd.isna(atr_value):
                logger.warning(f"ATR not available for {timestamp}. Falling back to percentage SL.")
                sl_method = "percentage" # Fallback
            else:
                if trade_side == 'long':
                    stop_loss = entry_price - (atr_value * atr_multiplier)
                else: # short
                    stop_loss = entry_price + (atr_value * atr_multiplier)

        if sl_method == "percentage": # Default or fallback
            sl_pct = self.config.get("stop_loss_percentage", 2.0) / 100
            if trade_side == 'long':
                stop_loss = entry_price * (1 - sl_pct)
            else: # short
                stop_loss = entry_price * (1 + sl_pct)

        if stop_loss <= 0: return None

        # --- Calculate Take Profit ---
        risk_per_share = abs(entry_price - stop_loss)

        if tp_method == "rr_ratio":
            if trade_side == 'long':
                take_profit = entry_price + (risk_per_share * rr_ratio)
            else: # short
                take_profit = entry_price - (risk_per_share * rr_ratio)
        else: # Fallback to rr_ratio
            logger.warning(f"Take profit method '{tp_method}' not implemented. Using 'rr_ratio'.")
            if trade_side == 'long':
                take_profit = entry_price + (risk_per_share * rr_ratio)
            else: # short
                take_profit = entry_price - (risk_per_share * rr_ratio)

        logger.debug(f"For {trade_side} trade at {entry_price:.2f}: SL={stop_loss:.2f}, TP={take_profit:.2f}")
        return stop_loss, take_profit

# Example Usage
if __name__ == "__main__":
    from core.data_feed import DataFeed
    mock_risk_config = {
        "stop_loss_method": "atr",
        "atr_period": 14,
        "atr_multiplier": 2.5,
        "take_profit_method": "rr_ratio",
        "risk_reward_ratio": 3.0
    }

    data_feed = DataFeed({})
    price_data = data_feed.get_historical_data("BTC-USD", "1d", "2022-01-01")

    if price_data is not None:
        risk_manager = RiskManager(mock_risk_config, price_data)

        # Simulate a long trade on the last day
        last_day = price_data.iloc[-1]
        entry_ts = last_day.name
        entry_p = last_day.close

        sl, tp = risk_manager.get_exit_levels(entry_p, 'long', entry_ts)

        print("--- Risk Manager Test (Long Trade) ---")
        print(f"Trade Entry Date: {entry_ts.date()}")
        print(f"Entry Price: ${entry_p:,.2f}")
        print(f"ATR on Entry: ${risk_manager.price_data.at[entry_ts, 'atr']:,.2f}")
        print(f"Stop Loss: ${sl:,.2f}")
        print(f"Take Profit: ${tp:,.2f}")
        print("--------------------------------------")
