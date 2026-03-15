from loguru import logger
from typing import Dict

class PortfolioManager:
    """
    Manages position sizing and overall portfolio exposure.
    """
    def __init__(self, risk_config: Dict):
        """
        Initializes the PortfolioManager.

        Args:
            risk_config (Dict): The risk configuration dictionary, which also contains
                                position sizing settings.
        """
        self.config = risk_config
        self.sizing_method = self.config.get("sizing_method", "fixed_fractional")
        logger.info(f"PortfolioManager initialized with sizing method: '{self.sizing_method}'")

    def calculate_position_size(
        self,
        current_equity: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculates the number of units to trade based on the configured sizing method.

        Args:
            current_equity (float): The current total equity of the portfolio.
            entry_price (float): The price at which the trade is entered.
            stop_loss_price (float): The price at which the trade will be exited for a loss.

        Returns:
            float: The number of units (e.g., shares, contracts) to trade. Returns 0 if invalid.
        """
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share <= 0:
            logger.warning("Risk per share is zero or negative. Cannot calculate position size.")
            return 0.0

        if self.sizing_method == "fixed_fractional":
            risk_pct = self.config.get("risk_percentage", 1.5) / 100
            capital_to_risk = current_equity * risk_pct

            position_size = capital_to_risk / risk_per_share

            logger.debug(
                f"Sizing: Equity=${current_equity:,.2f}, Risk={risk_pct:.2%}, "
                f"CapitalToRisk=${capital_to_risk:,.2f}, RiskPerShare=${risk_per_share:,.2f} "
                f"=> Size={position_size:.4f}"
            )
            return position_size

        elif self.sizing_method == "kelly_criterion":
            # Kelly Criterion: f* = (p * b - q) / b
            # p = probability of winning, q = 1 - p, b = ratio of avg win to avg loss
            win_rate = self.config.get("win_rate", 0.55)
            avg_win = self.config.get("average_win", 2.0)
            avg_loss = self.config.get("average_loss", 1.0)
            kelly_fraction = self.config.get("kelly_fraction", 0.5)  # half-Kelly for safety

            if avg_loss <= 0:
                logger.warning("Invalid average_loss for Kelly Criterion. Using fixed_fractional.")
                self.sizing_method = "fixed_fractional"
                return self.calculate_position_size(current_equity, entry_price, stop_loss_price)

            b = avg_win / avg_loss
            q = 1.0 - win_rate
            kelly_f = (win_rate * b - q) / b

            # Apply fraction (half-Kelly is safer) and clamp to [0, max_kelly]
            max_kelly = self.config.get("max_kelly_pct", 25.0) / 100.0
            optimal_f = max(0.0, min(kelly_f * kelly_fraction, max_kelly))

            capital_to_risk = current_equity * optimal_f
            position_size = capital_to_risk / risk_per_share

            logger.debug(
                f"Kelly Criterion: WinRate={win_rate:.2%}, b={b:.2f}, "
                f"f*={kelly_f:.4f}, applied={optimal_f:.4f}, "
                f"CapitalToRisk=${capital_to_risk:,.2f} => Size={position_size:.4f}"
            )
            return position_size

        else:
            logger.error(f"Unsupported sizing method: '{self.sizing_method}'")
            return 0.0

# Example Usage
if __name__ == "__main__":
    mock_risk_config = {
        "sizing_method": "fixed_fractional",
        "risk_percentage": 2.0 # Risk 2% of portfolio per trade
    }

    portfolio_manager = PortfolioManager(mock_risk_config)

    # --- Simulation ---
    equity = 100000.0
    entry = 50000.0
    stop_loss = 48000.0 # $2000 risk per BTC

    size = portfolio_manager.calculate_position_size(
        current_equity=equity,
        entry_price=entry,
        stop_loss_price=stop_loss
    )

    capital_at_risk = size * (entry - stop_loss)

    print("--- Portfolio Manager Test ---")
    print(f"Portfolio Equity: ${equity:,.2f}")
    print(f"Entry Price: ${entry:,.2f}")
    print(f"Stop Loss: ${stop_loss:,.2f}")
    print(f"\nCalculated Position Size: {size:.4f} units")
    print(f"Total Capital at Risk: ${capital_at_risk:,.2f} ({(capital_at_risk/equity):.2%})")
    print("------------------------------")
