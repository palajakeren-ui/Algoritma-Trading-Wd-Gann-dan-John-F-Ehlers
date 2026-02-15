from loguru import logger
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """Normalizes a value to a 0-1 range, clipped at the boundaries."""
    if max_val == min_val:
        return 0.5
    clipped = np.clip(value, min_val, max_val)
    return (clipped - min_val) / (max_val - min_val)

def calculate_fusion_confidence(
    row: pd.Series,
    ensemble_weights: Dict[str, float],
) -> Tuple[float, float, str]:
    """
    Calculates a weighted fusion confidence score for a buy and sell signal.

    Args:
        row (pd.Series): A row of data containing all indicator and prediction values.
        ensemble_weights (Dict[str, float]): The weights for each engine from config.

    Returns:
        Tuple[float, float, str]: (buy_score, sell_score, dominant_signal)
    """
    buy_scores = {}
    sell_scores = {}

    # --- 1. Gann Score ---
    # Score is higher the closer price is to a support/resistance level.
    if 'dist_to_gann_sup' in row and pd.notna(row['dist_to_gann_sup']):
        buy_scores['gann'] = 1.0 - normalize_score(row['dist_to_gann_sup'], 0, 0.02) # Full score if within 2%
    if 'dist_to_gann_res' in row and pd.notna(row['dist_to_gann_res']):
        sell_scores['gann'] = 1.0 - normalize_score(row['dist_to_gann_res'], 0, 0.02)

    # --- 2. Ehlers Score ---
    # Score is based on how extreme the Fisher Transform is.
    if 'fisher' in row and pd.notna(row['fisher']):
        buy_scores['ehlers'] = normalize_score(row['fisher'], -2.5, -1.0) # Score increases as fisher goes from -1 to -2.5
        sell_scores['ehlers'] = normalize_score(row['fisher'], 1.0, 2.5) # Score increases as fisher goes from 1 to 2.5

    # --- 3. Astro Score ---
    # A flat score is given if a significant event is present on that day.
    if 'is_astro_event' in row and row['is_astro_event'] == 1:
        buy_scores['astro'] = 1.0
        sell_scores['astro'] = 1.0

    # --- 4. ML Score ---
    # Score is directly from the model's prediction probability.
    if 'prob_up' in row and pd.notna(row['prob_up']):
        buy_scores['ml'] = row['prob_up']
    if 'prob_down' in row and pd.notna(row['prob_down']):
        sell_scores['ml'] = row['prob_down']

    # --- 5. Fusion Calculation ---
    total_buy_score = 0.0
    total_sell_score = 0.0
    total_weight = 0.0

    all_keys = set(buy_scores.keys()) | set(sell_scores.keys())

    for engine in all_keys:
        weight = ensemble_weights.get(engine, 0.0)
        if weight > 0:
            total_weight += weight
            total_buy_score += buy_scores.get(engine, 0.0) * weight
            total_sell_score += sell_scores.get(engine, 0.0) * weight

    final_buy_score = total_buy_score / total_weight if total_weight > 0 else 0.0
    final_sell_score = total_sell_score / total_weight if total_weight > 0 else 0.0

    dominant_signal = "none"
    if final_buy_score > final_sell_score:
        dominant_signal = "BUY"
    elif final_sell_score > final_buy_score:
        dominant_signal = "SELL"

    return final_buy_score, final_sell_score, dominant_signal
