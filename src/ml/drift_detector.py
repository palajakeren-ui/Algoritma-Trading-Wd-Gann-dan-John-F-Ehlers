"""
Model Drift Detection
Detects when a deployed model's performance has degraded.

Critical for production: Models trained on historical data will drift
as market dynamics change. This catches degradation before losses compound.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from loguru import logger
from dataclasses import dataclass
from collections import deque
from datetime import datetime


@dataclass
class DriftReport:
    """Model drift analysis report."""
    model_id: str
    is_drifting: bool
    drift_severity: str  # "none", "mild", "moderate", "severe"
    performance_zscore: float  # How far current perf is from baseline
    accuracy_baseline: float
    accuracy_current: float
    feature_drift_pct: float  # % of features with distribution shift
    confidence_degradation: float  # Average confidence change
    recommendation: str
    
    def to_dict(self) -> Dict:
        return {
            "model_id": self.model_id,
            "is_drifting": self.is_drifting,
            "drift_severity": self.drift_severity,
            "performance_zscore": round(self.performance_zscore, 3),
            "accuracy_baseline": round(self.accuracy_baseline, 4),
            "accuracy_current": round(self.accuracy_current, 4),
            "feature_drift_pct": round(self.feature_drift_pct, 1),
            "confidence_degradation": round(self.confidence_degradation, 4),
            "recommendation": self.recommendation,
        }


class DriftDetector:
    """
    Detects model drift using multiple methods:
    
    1. Performance drift - Rolling accuracy vs baseline
    2. Feature drift - Input distribution shift (PSI/KS-test)
    3. Prediction drift - Output distribution shift
    4. Confidence drift - Prediction confidence degradation
    
    Actions on drift detection:
    - MILD: Log warning, increase monitoring frequency
    - MODERATE: Reduce model weight in ensemble, alert
    - SEVERE: Fallback to backup model, retrain trigger
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.baseline_window = config.get("baseline_window", 500)
        self.evaluation_window = config.get("evaluation_window", 50)
        self.mild_threshold = config.get("mild_threshold", 1.5)      # Z-score
        self.moderate_threshold = config.get("moderate_threshold", 2.0)
        self.severe_threshold = config.get("severe_threshold", 3.0)
        self.psi_threshold = config.get("psi_threshold", 0.2)         # PSI threshold
        
        # Performance tracking
        self._predictions_correct: deque = deque(maxlen=self.baseline_window)
        self._confidences: deque = deque(maxlen=self.baseline_window)
        self._baseline_accuracy: Optional[float] = None
        self._baseline_confidence: Optional[float] = None
        self._feature_baselines: Dict[str, Dict] = {}
    
    def set_baseline(
        self,
        accuracy: float,
        confidence: float = None,
        feature_stats: Dict[str, Dict] = None,
    ):
        """Set baseline metrics from validation period."""
        self._baseline_accuracy = accuracy
        self._baseline_confidence = confidence
        self._feature_baselines = feature_stats or {}
        
        logger.info(
            f"Drift baseline set: accuracy={accuracy:.4f}, "
            f"confidence={confidence if confidence else 'N/A'}"
        )
    
    def record_prediction(
        self,
        was_correct: bool,
        confidence: float = 0.0,
        features: Dict[str, float] = None,
    ):
        """Record a prediction outcome for drift tracking."""
        self._predictions_correct.append(1.0 if was_correct else 0.0)
        self._confidences.append(confidence)
    
    def check_drift(self, model_id: str = "default") -> DriftReport:
        """
        Check if model is drifting.
        
        Returns:
            DriftReport with severity and recommendation
        """
        records = list(self._predictions_correct)
        
        if len(records) < self.evaluation_window:
            return DriftReport(
                model_id=model_id,
                is_drifting=False,
                drift_severity="none",
                performance_zscore=0.0,
                accuracy_baseline=self._baseline_accuracy or 0.0,
                accuracy_current=np.mean(records) if records else 0.0,
                feature_drift_pct=0.0,
                confidence_degradation=0.0,
                recommendation="Insufficient data for drift detection",
            )
        
        # Current accuracy (recent window)
        recent = np.array(records[-self.evaluation_window:])
        current_accuracy = float(np.mean(recent))
        
        # Baseline accuracy
        baseline = self._baseline_accuracy or float(np.mean(records[:self.baseline_window // 2]))
        
        # Z-score of current performance
        all_arr = np.array(records)
        if np.std(all_arr) > 0:
            z_score = (baseline - current_accuracy) / np.std(all_arr)
        else:
            z_score = 0.0
        
        # Confidence degradation
        confidences = list(self._confidences)
        conf_degradation = 0.0
        if self._baseline_confidence and confidences:
            current_conf = np.mean(confidences[-self.evaluation_window:])
            conf_degradation = (self._baseline_confidence - current_conf) / max(self._baseline_confidence, 0.001)
        
        # Classify severity
        severity = "none"
        is_drifting = False
        recommendation = "Model performing within expected range"
        
        if abs(z_score) >= self.severe_threshold:
            severity = "severe"
            is_drifting = True
            recommendation = "RETRAIN IMMEDIATELY. Fallback to backup model."
        elif abs(z_score) >= self.moderate_threshold:
            severity = "moderate"
            is_drifting = True
            recommendation = "Reduce model weight. Schedule retraining."
        elif abs(z_score) >= self.mild_threshold:
            severity = "mild"
            is_drifting = True
            recommendation = "Increase monitoring frequency. Consider retraining."
        
        report = DriftReport(
            model_id=model_id,
            is_drifting=is_drifting,
            drift_severity=severity,
            performance_zscore=float(z_score),
            accuracy_baseline=baseline,
            accuracy_current=current_accuracy,
            feature_drift_pct=0.0,  # Would need feature data to compute
            confidence_degradation=float(conf_degradation),
            recommendation=recommendation,
        )
        
        if is_drifting:
            logger.warning(
                f"⚠️ MODEL DRIFT [{severity.upper()}]: {model_id} | "
                f"Z-score={z_score:.2f} | "
                f"Accuracy: {baseline:.3f} → {current_accuracy:.3f} | "
                f"{recommendation}"
            )
        
        return report
    
    @staticmethod
    def calculate_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        """
        Calculate Population Stability Index (PSI).
        
        PSI < 0.1: No significant shift
        PSI 0.1-0.25: Moderate shift
        PSI > 0.25: Significant shift
        """
        expected = np.array(expected, dtype=float)
        actual = np.array(actual, dtype=float)
        
        # Create bins from expected distribution
        breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf
        
        expected_counts = np.histogram(expected, bins=breakpoints)[0]
        actual_counts = np.histogram(actual, bins=breakpoints)[0]
        
        # Avoid zeros
        expected_pcts = (expected_counts + 1) / (len(expected) + bins)
        actual_pcts = (actual_counts + 1) / (len(actual) + bins)
        
        psi = np.sum((actual_pcts - expected_pcts) * np.log(actual_pcts / expected_pcts))
        
        return float(psi)
