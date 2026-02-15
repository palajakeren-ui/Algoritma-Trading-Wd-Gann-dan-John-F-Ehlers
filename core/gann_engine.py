import pandas as pd
from loguru import logger
from typing import Dict, List, Optional

from modules.gann.square_of_9 import SquareOf9
from modules.gann.gann_angles import calculate_gann_angles

class GannEngine:
    """
    The main engine for performing all Gann-related analysis, including
    Square of 9, Gann Angles, and Time Cycles.
    """
    def __init__(self, gann_config: Dict):
        """
        Initializes the GannEngine with its configuration.

        Args:
            gann_config (Dict): A dictionary containing all Gann-related settings.
        """
        self.config = gann_config
        self.sq9_calculator = None
        logger.info("GannEngine initialized.")

    def calculate_sq9_levels(self, price_data: pd.DataFrame) -> Optional[Dict[str, List[float]]]:
        """
        Calculates Square of 9 support and resistance levels.

        It determines the initial price from the provided data based on the
        configuration and then uses the SquareOf9 module to get the levels.

        Args:
            price_data (pd.DataFrame): A DataFrame containing at least 'high', 'low', 'close' columns.

        Returns:
            Optional[Dict[str, List[float]]]: A dictionary with 'support' and 'resistance'
                                              levels, or None if calculation fails.
        """
        if price_data.empty:
            logger.warning("Cannot calculate Square of 9 levels: price_data is empty.")
            return None

        # Determine the initial price for the calculator
        initial_price = self.config.get("square_of_9", {}).get("initial_price", 0.0)

        if initial_price <= 0.0:
            # Auto-detect the initial price from the most recent significant pivot
            # For simplicity, we'll use the most recent high/low in this example.
            lookback = self.config.get("square_of_9", {}).get("auto_pivot_lookback", 100)
            recent_data = price_data.tail(lookback)
            recent_high = recent_data['high'].max()
            recent_low = recent_data['low'].min()

            # Choose the pivot closer to the last close price
            last_close = recent_data['close'].iloc[-1]
            # yfinance can return a Series, so extract the scalar value with .item()
            if isinstance(last_close, (pd.Series, pd.DataFrame)):
                last_close = last_close.item()

            if abs(last_close - recent_high) < abs(last_close - recent_low):
                initial_price = recent_high
                logger.info(f"Auto-detected SQ9 initial price (recent high): {initial_price:.2f}")
            else:
                initial_price = recent_low
                logger.info(f"Auto-detected SQ9 initial price (recent low): {initial_price:.2f}")

        if initial_price <= 0:
            logger.error("Failed to determine a valid positive initial price for SQ9.")
            return None

        # Initialize the calculator and get levels
        try:
            self.sq9_calculator = SquareOf9(initial_price=initial_price)
            n_levels = self.config.get("square_of_9", {}).get("levels_to_generate", 5)
            levels = self.sq9_calculator.get_levels(n_levels=n_levels)
            return levels
        except Exception as e:
            logger.error(f"Error calculating Square of 9 levels: {e}")
            return None

    def calculate_gann_angles(self, price_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Finds a significant pivot and calculates Gann Angles from it.
        """
        angle_config = self.config.get("gann_angles", {})
        if not angle_config:
            logger.info("Gann Angles not configured. Skipping calculation.")
            return None

        # Auto-detect pivot
        lookback = angle_config.get("pivot_lookback", 200)
        recent_data = price_data.tail(lookback)

        pivot_type = angle_config.get("anchor_point", "low")
        if pivot_type == "low":
            pivot_price = recent_data['low'].min()
            pivot_date = recent_data['low'].idxmin()
        else:
            pivot_price = recent_data['high'].max()
            pivot_date = recent_data['high'].idxmax()

        pivot_point = {'date': pivot_date, 'price': pivot_price, 'type': pivot_type}
        logger.info(f"Auto-detected Gann Angle pivot: {pivot_type} at {pivot_price:.2f} on {pivot_date.date()}")

        angles_df = calculate_gann_angles(
            price_data=price_data,
            pivot_point=pivot_point,
            time_units_per_price_unit=angle_config.get("time_units_per_price_unit", 1.0),
            angles=angle_config.get("angles_to_draw", ["1x1"])
        )
        return angles_df

    def analyze_time_cycles(self, price_data: pd.DataFrame) -> Optional[Dict]:
        """
        Analyzes Gann Time Cycles from significant pivot points.
        Projects future cycle dates using Gann's natural time periods:
        90, 120, 144, 180, 270, 360 calendar days.

        Args:
            price_data: DataFrame with OHLCV data (DatetimeIndex).

        Returns:
            Dict with 'pivots', 'cycle_dates', and 'confluence_zones', or None.
        """
        time_config = self.config.get("time_cycles", {})
        gann_periods = time_config.get("periods", [90, 120, 144, 180, 270, 360])
        lookback = time_config.get("pivot_lookback", 200)
        confluence_tolerance = time_config.get("confluence_tolerance_days", 5)

        if price_data.empty or len(price_data) < 20:
            logger.warning("Insufficient data for Gann Time Cycle analysis.")
            return None

        logger.info("Performing Gann Time Cycle analysis...")

        recent = price_data.tail(lookback)

        # --- 1. Find significant pivots ---
        pivots = []
        # Major High
        high_idx = recent['high'].idxmax()
        pivots.append({'date': high_idx, 'price': float(recent.at[high_idx, 'high']), 'type': 'high'})
        # Major Low
        low_idx = recent['low'].idxmin()
        pivots.append({'date': low_idx, 'price': float(recent.at[low_idx, 'low']), 'type': 'low'})

        # --- 2. Project future cycle dates from each pivot ---
        cycle_dates = []
        for pivot in pivots:
            for period in gann_periods:
                future_date = pivot['date'] + pd.Timedelta(days=period)
                cycle_dates.append({
                    'date': future_date,
                    'from_pivot': pivot['date'].isoformat() if hasattr(pivot['date'], 'isoformat') else str(pivot['date']),
                    'pivot_type': pivot['type'],
                    'period_days': period,
                    'label': f"Gann {period}d from {pivot['type']}"
                })

        # --- 3. Find confluence zones (multiple cycles landing near same date) ---
        confluence_zones = []
        sorted_dates = sorted(cycle_dates, key=lambda x: x['date'])
        visited = set()
        for i, cd in enumerate(sorted_dates):
            if i in visited:
                continue
            cluster = [cd]
            for j in range(i + 1, len(sorted_dates)):
                if j in visited:
                    continue
                diff = abs((sorted_dates[j]['date'] - cd['date']).days)
                if diff <= confluence_tolerance:
                    cluster.append(sorted_dates[j])
                    visited.add(j)
            if len(cluster) >= 2:
                avg_date = cd['date']  # Use first date as representative
                confluence_zones.append({
                    'date': avg_date.isoformat() if hasattr(avg_date, 'isoformat') else str(avg_date),
                    'strength': len(cluster),
                    'contributing_cycles': [c['label'] for c in cluster]
                })

        # Sort confluence by strength descending
        confluence_zones.sort(key=lambda x: x['strength'], reverse=True)

        logger.success(f"Gann Time Cycle analysis complete: {len(cycle_dates)} projections, "
                       f"{len(confluence_zones)} confluence zones.")

        return {
            'pivots': [
                {
                    'date': p['date'].isoformat() if hasattr(p['date'], 'isoformat') else str(p['date']),
                    'price': p['price'],
                    'type': p['type']
                }
                for p in pivots
            ],
            'cycle_dates': [
                {**cd, 'date': cd['date'].isoformat() if hasattr(cd['date'], 'isoformat') else str(cd['date'])}
                for cd in cycle_dates
            ],
            'confluence_zones': confluence_zones
        }


# Example Usage
if __name__ == '__main__':
    # This requires a mock config and data for testing.
    from core.data_feed import DataFeed

    # 1. Load mock configuration
    mock_gann_config = {
        "square_of_9": {
            "initial_price": 0.0, # Auto-detect
            "levels_to_generate": 4,
            "auto_pivot_lookback": 200
        }
    }

    # 2. Fetch some real data for testing
    data_feed = DataFeed(broker_config={})
    btc_data = data_feed.get_historical_data("BTC-USD", "1d", "2022-01-01", "2023-01-01")

    if btc_data is not None:
        # 3. Initialize and run the engine
        gann_engine = GannEngine(gann_config=mock_gann_config)
        sq9_levels = gann_engine.calculate_sq9_levels(price_data=btc_data)

        if sq9_levels:
            print("\n--- Gann Square of 9 Analysis ---")
            last_close = btc_data['close'].iloc[-1]
            print(f"Last Close Price: {last_close:.2f}")

            print("\nCalculated Support Levels:")
            for level in reversed(sq9_levels['support']):
                print(f"{level:.2f}")

            print("\nCalculated Resistance Levels:")
            for level in sq9_levels['resistance']:
                print(f"{level:.2f}")
            print("-" * 35)
