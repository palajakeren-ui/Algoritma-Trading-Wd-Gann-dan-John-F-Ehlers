"""
Forecasting Evaluator Module
Evaluates and scores forecasting accuracy
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime


class ForecastingEvaluator:
    """
    Evaluates forecasting accuracy for price predictions.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the evaluator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.evaluation_history = []
        logger.info("ForecastingEvaluator initialized")
    
    def evaluate_price_forecast(
        self,
        actual_prices: pd.Series,
        predicted_prices: pd.Series,
        tolerance_pct: float = 1.0
    ) -> Dict:
        """
        Evaluate price forecast accuracy.
        
        Args:
            actual_prices: Actual price series
            predicted_prices: Predicted price series
            tolerance_pct: Tolerance percentage for accuracy calculation
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Align series
        actual = actual_prices.iloc[:len(predicted_prices)]
        predicted = predicted_prices.iloc[:len(actual)]
        
        # Calculate metrics
        mae = np.mean(np.abs(actual - predicted))
        mse = np.mean((actual - predicted) ** 2)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # Directional accuracy
        actual_direction = np.sign(actual.diff())
        predicted_direction = np.sign(predicted.diff())
        direction_accuracy = np.mean(actual_direction == predicted_direction) * 100
        
        # Within tolerance
        tolerance = actual * (tolerance_pct / 100)
        within_tolerance = np.mean(np.abs(actual - predicted) <= tolerance) * 100
        
        metrics = {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'mape': float(mape),
            'direction_accuracy': float(direction_accuracy),
            'within_tolerance_pct': float(within_tolerance),
            'tolerance_used': tolerance_pct,
            'sample_size': len(actual),
            'timestamp': datetime.now().isoformat()
        }
        
        self.evaluation_history.append(metrics)
        logger.info(f"Forecast evaluation: MAPE={mape:.2f}%, Direction={direction_accuracy:.1f}%")
        
        return metrics
    
    def evaluate_turning_points(
        self,
        actual_prices: pd.Series,
        predicted_turning_points: List[datetime],
        window_bars: int = 5
    ) -> Dict:
        """
        Evaluate turning point prediction accuracy.
        
        Args:
            actual_prices: Actual price series
            predicted_turning_points: List of predicted turning point dates
            window_bars: Window around prediction to check for actual turning point
            
        Returns:
            Dictionary of metrics
        """
        # Find actual turning points (local min/max)
        actual_highs = actual_prices[(actual_prices.shift(1) < actual_prices) & 
                                      (actual_prices.shift(-1) < actual_prices)]
        actual_lows = actual_prices[(actual_prices.shift(1) > actual_prices) & 
                                     (actual_prices.shift(-1) > actual_prices)]
        
        actual_turning_points = pd.concat([actual_highs, actual_lows]).sort_index()
        
        # Check predictions
        hits = 0
        for pred_date in predicted_turning_points:
            # Check if any actual turning point within window
            for actual_date in actual_turning_points.index:
                diff = abs((pred_date - actual_date).days)
                if diff <= window_bars:
                    hits += 1
                    break
        
        hit_rate = (hits / len(predicted_turning_points) * 100) if predicted_turning_points else 0
        
        metrics = {
            'predicted_count': len(predicted_turning_points),
            'actual_count': len(actual_turning_points),
            'hits': hits,
            'hit_rate_pct': float(hit_rate),
            'window_bars': window_bars,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Turning point evaluation: Hit rate={hit_rate:.1f}%")
        return metrics
    
    def evaluate_support_resistance(
        self,
        actual_prices: pd.Series,
        sr_levels: List[float],
        touch_tolerance_pct: float = 0.5
    ) -> Dict:
        """
        Evaluate support/resistance level accuracy.
        
        Args:
            actual_prices: Actual price series
            sr_levels: List of S/R levels
            touch_tolerance_pct: Tolerance for considering a "touch"
            
        Returns:
            Dictionary of metrics
        """
        touches = {level: 0 for level in sr_levels}
        reactions = {level: 0 for level in sr_levels}
        
        for i in range(1, len(actual_prices) - 1):
            price = actual_prices.iloc[i]
            prev_price = actual_prices.iloc[i - 1]
            next_price = actual_prices.iloc[i + 1]
            
            for level in sr_levels:
                tolerance = level * (touch_tolerance_pct / 100)
                
                if abs(price - level) <= tolerance:
                    touches[level] += 1
                    
                    # Check for reaction (reversal)
                    if (prev_price < level and next_price < level) or \
                       (prev_price > level and next_price > level):
                        reactions[level] += 1
        
        total_touches = sum(touches.values())
        total_reactions = sum(reactions.values())
        reaction_rate = (total_reactions / total_touches * 100) if total_touches > 0 else 0
        
        metrics = {
            'levels_count': len(sr_levels),
            'total_touches': total_touches,
            'total_reactions': total_reactions,
            'reaction_rate_pct': float(reaction_rate),
            'level_details': {str(l): {'touches': t, 'reactions': reactions[l]} 
                            for l, t in touches.items()},
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"S/R evaluation: {total_touches} touches, {reaction_rate:.1f}% reaction rate")
        return metrics
    
    def get_summary_report(self) -> Dict:
        """Get summary of all evaluations"""
        if not self.evaluation_history:
            return {"message": "No evaluations performed yet"}
        
        mapes = [e.get('mape', 0) for e in self.evaluation_history if 'mape' in e]
        dir_accs = [e.get('direction_accuracy', 0) for e in self.evaluation_history if 'direction_accuracy' in e]
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'avg_mape': float(np.mean(mapes)) if mapes else None,
            'avg_direction_accuracy': float(np.mean(dir_accs)) if dir_accs else None,
            'best_mape': float(min(mapes)) if mapes else None,
            'evaluation_dates': [e['timestamp'] for e in self.evaluation_history]
        }


# Example usage
if __name__ == '__main__':
    evaluator = ForecastingEvaluator()
    
    # Generate dummy data
    dates = pd.date_range('2024-01-01', periods=100)
    actual = pd.Series(100 + np.cumsum(np.random.randn(100)), index=dates)
    predicted = actual + np.random.randn(100) * 2  # Add some noise
    
    # Evaluate
    metrics = evaluator.evaluate_price_forecast(actual, predicted)
    print("Evaluation metrics:", metrics)
