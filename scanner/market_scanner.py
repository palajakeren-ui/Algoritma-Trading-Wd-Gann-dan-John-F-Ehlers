import pandas as pd
from loguru import logger
from typing import Dict, List
from tqdm import tqdm

# Import core components and individual scanners
from core.data_feed import DataFeed
from core.gann_engine import GannEngine
from core.ehlers_engine import EhlersEngine
from scanner.gann_scanner import scan_gann_sq9_proximity
from scanner.ehlers_scanner import scan_ehlers_fisher_state

class MarketScanner:
    """
    Orchestrates the market scanning process based on scanner_config.yaml.
    It iterates through specified assets and timeframes, applying a set of
    pre-defined analytical criteria to find potential trading opportunities.
    """
    def __init__(self, config: Dict):
        self.config = config
        self.scanner_config = config.get("scanner_config", {})

        # Initialize core components needed for scanning
        self.data_feed = DataFeed(config.get("broker_config", {}))
        self.gann_engine = GannEngine(config.get("gann_config", {}))
        self.ehlers_engine = EhlersEngine(config.get("ehlers_config", {}))

        logger.info("MarketScanner initialized.")

    def run_scan(self):
        """
        Executes the market scan based on the configuration.
        """
        assets = self.scanner_config.get("assets_to_scan", [])
        timeframes = self.scanner_config.get("timeframes_to_scan", [])
        criteria = self.scanner_config.get("scan_criteria", [])

        if not all([assets, timeframes, criteria]):
            logger.error("Scanner configuration is incomplete. Check assets, timeframes, and criteria.")
            return pd.DataFrame()

        logger.info(f"Starting market scan for {len(assets)} assets across {len(timeframes)} timeframes.")

        scan_results = []

        # Use tqdm for a progress bar
        for asset in tqdm(assets, desc="Scanning Assets"):
            for timeframe in timeframes:
                # 1. Fetch data for the current asset/timeframe
                price_data = self.data_feed.get_historical_data(asset, timeframe, start_date="2022-01-01") # Lookback of ~1 year
                if price_data is None or price_data.empty:
                    logger.warning(f"Could not get data for {asset} on {timeframe}. Skipping.")
                    continue

                # 2. Run analyses
                gann_levels = self.gann_engine.calculate_sq9_levels(price_data)
                data_with_indicators = self.ehlers_engine.calculate_all_indicators(price_data)

                # 3. Apply scan criteria
                passed_criteria = True
                reasons = []

                for criterion in criteria:
                    engine = criterion.get("engine")
                    function = criterion.get("function")
                    params = criterion.get("params", {})

                    result = False
                    reason = ""

                    if engine == "gann_scanner" and function == "is_near_sq9_level":
                        result, reason = scan_gann_sq9_proximity(data_with_indicators.iloc[-1], gann_levels, **params)
                    elif engine == "ehlers_scanner" and function == "is_fisher_extreme":
                        result, reason = scan_ehlers_fisher_state(data_with_indicators.iloc[-1], **params)
                    else:
                        logger.warning(f"Unknown scan criterion: {engine}.{function}")
                        passed_criteria = False
                        break

                    if result:
                        reasons.append(reason)
                    else:
                        passed_criteria = False
                        break # If one criterion fails, no need to check others

                # 4. If all criteria passed, add to results
                if passed_criteria:
                    scan_results.append({
                        "asset": asset,
                        "timeframe": timeframe,
                        "last_close": data_with_indicators.iloc[-1].close,
                        "reason": " & ".join(reasons)
                    })
                    logger.success(f"Opportunity found for {asset} ({timeframe}): {' & '.join(reasons)}")

        results_df = pd.DataFrame(scan_results)
        logger.info(f"Scan complete. Found {len(results_df)} potential opportunities.")

        # Save to CSV if configured
        output_path = self.scanner_config.get("output_path", "outputs/market_scanner_output.csv")
        results_df.to_csv(output_path, index=False)
        logger.info(f"Scanner results saved to {output_path}")

        return results_df
