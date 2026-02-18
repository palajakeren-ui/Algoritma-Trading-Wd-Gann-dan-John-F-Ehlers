"""
Confidence Calibrator
Adjusts raw signal confidence to match actual hit rates.

A signal claiming 80% confidence should be correct 80% of the time.
Without calibration, ML models and signal sources often produce
overconfident or underconfident scores.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger
from collections import deque


class ConfidenceCalibrator:
    """
    Platt scaling / isotonic regression calibration for signal confidence.
    
    Process:
    1. Collect (predicted_confidence, actual_outcome) pairs
    2. Bin predictions into confidence buckets
    3. Calculate actual hit rate per bucket
    4. Build calibration mapping
    5. Apply to future predictions
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.n_bins = config.get("n_bins", 10)
        self.min_samples = config.get("min_samples", 30)
        self.window_size = config.get("window_size", 1000)
        
        # Per-source calibration data
        self._data: Dict[str, deque] = {}
        self._calibration_map: Dict[str, Dict[int, float]] = {}
    
    def record(self, source: str, predicted_confidence: float, was_correct: bool):
        """
        Record a prediction outcome for calibration.
        
        Args:
            source: Signal source name
            predicted_confidence: Original confidence (0-1)
            was_correct: Whether the prediction was correct
        """
        if source not in self._data:
            self._data[source] = deque(maxlen=self.window_size)
        
        self._data[source].append((predicted_confidence, 1.0 if was_correct else 0.0))
        
        # Recalibrate periodically
        if len(self._data[source]) % 50 == 0:
            self._build_calibration(source)
    
    def calibrate(self, source: str, raw_confidence: float) -> float:
        """
        Apply calibration to a raw confidence score.
        
        Args:
            source: Signal source name
            raw_confidence: Raw confidence (0-1)
            
        Returns:
            Calibrated confidence (0-1)
        """
        if source not in self._calibration_map:
            return raw_confidence
        
        cal_map = self._calibration_map[source]
        bin_idx = min(int(raw_confidence * self.n_bins), self.n_bins - 1)
        
        # Interpolate between bins
        if bin_idx in cal_map:
            return cal_map[bin_idx]
        
        return raw_confidence
    
    def _build_calibration(self, source: str):
        """Build calibration mapping from collected data."""
        data = list(self._data.get(source, []))
        
        if len(data) < self.min_samples:
            return
        
        # Bin predictions
        bins = [[] for _ in range(self.n_bins)]
        
        for conf, outcome in data:
            bin_idx = min(int(conf * self.n_bins), self.n_bins - 1)
            bins[bin_idx].append(outcome)
        
        # Calculate actual hit rate per bin
        cal_map = {}
        for i, bin_data in enumerate(bins):
            if len(bin_data) >= 3:  # Need at least 3 samples
                cal_map[i] = float(np.mean(bin_data))
            else:
                # Default: use the bin center
                cal_map[i] = (i + 0.5) / self.n_bins
        
        self._calibration_map[source] = cal_map
        
        logger.debug(
            f"Calibration built for {source}: "
            f"{', '.join(f'bin{i}:{v:.2f}' for i, v in cal_map.items())}"
        )
    
    def get_calibration_report(self) -> Dict:
        """Get calibration quality report."""
        report = {}
        
        for source, data in self._data.items():
            if len(data) < self.min_samples:
                report[source] = {"status": "insufficient_data", "n_samples": len(data)}
                continue
            
            records = list(data)
            confs = [r[0] for r in records]
            outcomes = [r[1] for r in records]
            
            # Brier score (lower = better calibrated)
            brier = float(np.mean([(c - o) ** 2 for c, o in records]))
            
            # Expected Calibration Error
            ece = self._calculate_ece(confs, outcomes)
            
            report[source] = {
                "n_samples": len(records),
                "brier_score": round(brier, 4),
                "ece": round(ece, 4),
                "avg_confidence": round(float(np.mean(confs)), 3),
                "actual_accuracy": round(float(np.mean(outcomes)), 3),
                "calibrated": bool(ece < 0.1),
            }
        
        return report
    
    def _calculate_ece(self, confidences: List[float], outcomes: List[float]) -> float:
        """Calculate Expected Calibration Error."""
        bins = [[] for _ in range(self.n_bins)]
        bin_confs = [[] for _ in range(self.n_bins)]
        
        for conf, out in zip(confidences, outcomes):
            idx = min(int(conf * self.n_bins), self.n_bins - 1)
            bins[idx].append(out)
            bin_confs[idx].append(conf)
        
        total = len(confidences)
        ece = 0.0
        
        for i in range(self.n_bins):
            if bins[i]:
                avg_conf = np.mean(bin_confs[i])
                avg_acc = np.mean(bins[i])
                ece += (len(bins[i]) / total) * abs(avg_acc - avg_conf)
        
        return float(ece)
