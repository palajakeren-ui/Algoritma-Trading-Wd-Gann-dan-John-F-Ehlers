"""
Production Data Validator
Institutional-grade data quality validation pipeline.

Validates:
- OHLCV integrity (no NaN in critical fields)
- Timestamp continuity (gap detection)
- Price anomaly detection (outlier rejection)
- Volume sanity checks
- Cross-field consistency (High >= Low, etc.)
- Staleness detection (frozen feed)
"""

import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class DataQuality(Enum):
    """Data quality classification."""
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    REJECTED = "rejected"


@dataclass
class ValidationResult:
    """Result of a data validation check."""
    quality: DataQuality
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)
    rows_removed: int = 0
    gaps_detected: int = 0
    outliers_detected: int = 0
    
    @property
    def passed(self) -> bool:
        return self.quality in (DataQuality.GOOD, DataQuality.WARNING)
    
    def to_dict(self) -> Dict:
        return {
            "quality": self.quality.value,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "stats": self.stats,
            "rows_removed": self.rows_removed,
            "gaps_detected": self.gaps_detected,
            "outliers_detected": self.outliers_detected,
        }


class DataValidator:
    """
    Institutional-grade data validation pipeline.
    
    Performs multi-level validation before data enters the feature engine:
    1. Schema validation (required columns, types)
    2. Integrity checks (OHLCV cross-field consistency)
    3. Gap detection (missing timestamps)
    4. Outlier detection (statistical anomalies)
    5. Staleness detection (frozen feed)
    """
    
    REQUIRED_COLUMNS = {"open", "high", "low", "close", "volume"}
    
    # Z-score threshold for outlier detection
    DEFAULT_OUTLIER_Z_THRESHOLD = 5.0
    
    # Maximum allowed gap as multiple of expected interval
    DEFAULT_MAX_GAP_MULTIPLIER = 3.0
    
    # Maximum % change in single bar (rejects flash crash artifacts)
    DEFAULT_MAX_SINGLE_BAR_PCT = 20.0
    
    # Minimum volume to consider valid (0 volume = suspicious)
    DEFAULT_MIN_VOLUME = 0
    
    # Maximum consecutive same-price bars (staleness)
    DEFAULT_MAX_STALE_BARS = 10
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.outlier_z_threshold = config.get("outlier_z_threshold", self.DEFAULT_OUTLIER_Z_THRESHOLD)
        self.max_gap_multiplier = config.get("max_gap_multiplier", self.DEFAULT_MAX_GAP_MULTIPLIER)
        self.max_single_bar_pct = config.get("max_single_bar_pct", self.DEFAULT_MAX_SINGLE_BAR_PCT)
        self.min_volume = config.get("min_volume", self.DEFAULT_MIN_VOLUME)
        self.max_stale_bars = config.get("max_stale_bars", self.DEFAULT_MAX_STALE_BARS)
        self.strict_mode = config.get("strict_mode", False)
    
    def validate(self, df: pd.DataFrame, timeframe: str = "1h") -> Tuple[pd.DataFrame, ValidationResult]:
        """
        Full validation pipeline. Returns cleaned DataFrame and validation result.
        
        Args:
            df: OHLCV DataFrame with DatetimeIndex
            timeframe: Expected timeframe for gap detection
            
        Returns:
            Tuple of (cleaned_df, ValidationResult)
        """
        result = ValidationResult(quality=DataQuality.GOOD)
        
        if df is None or df.empty:
            result.quality = DataQuality.REJECTED
            result.errors.append("Input DataFrame is None or empty")
            return pd.DataFrame(), result
        
        # Make a copy to avoid mutating input
        df = df.copy()
        original_len = len(df)
        
        # Step 1: Schema validation
        df, result = self._validate_schema(df, result)
        if result.quality == DataQuality.REJECTED:
            return df, result
        
        # Step 2: Normalize column names
        df = self._normalize_columns(df)
        
        # Step 3: Ensure DatetimeIndex
        df, result = self._validate_index(df, result)
        if result.quality == DataQuality.REJECTED:
            return df, result
        
        # Step 4: Remove exact duplicates
        dups = df.index.duplicated(keep='last')
        if dups.any():
            n_dups = dups.sum()
            df = df[~dups]
            result.warnings.append(f"Removed {n_dups} duplicate timestamps")
            result.rows_removed += n_dups
        
        # Step 5: Sort by index
        df = df.sort_index()
        
        # Step 6: OHLCV integrity checks
        df, result = self._validate_ohlcv_integrity(df, result)
        
        # Step 7: Gap detection
        result = self._detect_gaps(df, timeframe, result)
        
        # Step 8: Outlier detection and removal
        df, result = self._detect_outliers(df, result)
        
        # Step 9: Staleness detection
        result = self._detect_staleness(df, result)
        
        # Step 10: NaN handling
        nan_count = df[list(self.REQUIRED_COLUMNS)].isna().sum().sum()
        if nan_count > 0:
            # Forward fill small gaps, drop remaining
            df = df.ffill(limit=3)
            remaining_nan = df[list(self.REQUIRED_COLUMNS)].isna().sum().sum()
            if remaining_nan > 0:
                before = len(df)
                df = df.dropna(subset=list(self.REQUIRED_COLUMNS))
                dropped = before - len(df)
                result.warnings.append(f"Dropped {dropped} rows with unfillable NaN values")
                result.rows_removed += dropped
        
        # Final stats
        result.stats = {
            "original_rows": original_len,
            "final_rows": len(df),
            "rows_removed": result.rows_removed,
            "removal_pct": round((result.rows_removed / max(original_len, 1)) * 100, 2),
            "date_range_start": str(df.index[0]) if len(df) > 0 else None,
            "date_range_end": str(df.index[-1]) if len(df) > 0 else None,
            "completeness_pct": round((1 - df.isna().mean().mean()) * 100, 2),
        }
        
        # Determine final quality
        if result.errors:
            result.quality = DataQuality.CRITICAL if not self.strict_mode else DataQuality.REJECTED
        elif result.warnings:
            result.quality = DataQuality.WARNING
        
        if result.rows_removed > original_len * 0.1:
            result.quality = DataQuality.CRITICAL
            result.errors.append(f"Lost {result.stats['removal_pct']}% of data during validation")
        
        logger.info(f"Data validation complete: {result.quality.value} | "
                     f"{result.stats['final_rows']}/{result.stats['original_rows']} rows | "
                     f"{result.gaps_detected} gaps | {result.outliers_detected} outliers")
        
        return df, result
    
    def _validate_schema(self, df: pd.DataFrame, result: ValidationResult) -> Tuple[pd.DataFrame, ValidationResult]:
        """Validate required columns exist."""
        cols_lower = {c.lower() for c in df.columns}
        missing = self.REQUIRED_COLUMNS - cols_lower
        
        if missing:
            # Check if close at minimum exists
            if "close" not in cols_lower:
                result.quality = DataQuality.REJECTED
                result.errors.append(f"Missing critical columns: {missing}")
                return df, result
            else:
                result.warnings.append(f"Missing optional columns: {missing}")
        
        return df, result
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lowercase."""
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Handle common aliases
        rename_map = {
            "vol": "volume",
            "vol.": "volume",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        return df
    
    def _validate_index(self, df: pd.DataFrame, result: ValidationResult) -> Tuple[pd.DataFrame, ValidationResult]:
        """Ensure DatetimeIndex."""
        if not isinstance(df.index, pd.DatetimeIndex):
            # Try to find a datetime column
            for col in ["date", "datetime", "timestamp", "time"]:
                if col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        df = df.set_index(col)
                        return df, result
                    except Exception:
                        continue
            
            # Try converting index
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                result.quality = DataQuality.REJECTED
                result.errors.append("Cannot convert index to DatetimeIndex")
                return df, result
        
        return df, result
    
    def _validate_ohlcv_integrity(self, df: pd.DataFrame, result: ValidationResult) -> Tuple[pd.DataFrame, ValidationResult]:
        """Validate OHLCV cross-field consistency."""
        bad_rows = pd.Series(False, index=df.index)
        
        if all(c in df.columns for c in ["open", "high", "low", "close"]):
            # High must be >= Low
            hl_violation = df["high"] < df["low"]
            if hl_violation.any():
                n = hl_violation.sum()
                result.warnings.append(f"{n} bars where high < low (swapped)")
                # Fix by swapping
                mask = hl_violation
                df.loc[mask, ["high", "low"]] = df.loc[mask, ["low", "high"]].values
            
            # High must be >= max(Open, Close)
            high_violation = df["high"] < df[["open", "close"]].max(axis=1)
            if high_violation.any():
                n = high_violation.sum()
                result.warnings.append(f"{n} bars where high < max(open, close)")
                df.loc[high_violation, "high"] = df.loc[high_violation, ["open", "close"]].max(axis=1)
            
            # Low must be <= min(Open, Close)  
            low_violation = df["low"] > df[["open", "close"]].min(axis=1)
            if low_violation.any():
                n = low_violation.sum()
                result.warnings.append(f"{n} bars where low > min(open, close)")
                df.loc[low_violation, "low"] = df.loc[low_violation, ["open", "close"]].min(axis=1)
            
            # Single-bar extreme moves (flash crash artifacts)
            pct_change = df["close"].pct_change().abs() * 100
            extreme = pct_change > self.max_single_bar_pct
            if extreme.any():
                n = extreme.sum()
                result.warnings.append(f"{n} bars with >{self.max_single_bar_pct}% single-bar move (potential data artifact)")
                result.outliers_detected += n
                bad_rows |= extreme
        
        # Zero/negative price check
        price_cols = [c for c in ["open", "high", "low", "close"] if c in df.columns]
        for col in price_cols:
            neg = df[col] <= 0
            if neg.any():
                n = neg.sum()
                result.errors.append(f"{n} rows with {col} <= 0")
                bad_rows |= neg
        
        # Volume check
        if "volume" in df.columns:
            neg_vol = df["volume"] < 0
            if neg_vol.any():
                n = neg_vol.sum()
                result.warnings.append(f"{n} rows with negative volume (set to 0)")
                df.loc[neg_vol, "volume"] = 0
        
        # Remove bad rows
        if bad_rows.any():
            n_bad = bad_rows.sum()
            df = df[~bad_rows]
            result.rows_removed += n_bad
        
        return df, result
    
    def _detect_gaps(self, df: pd.DataFrame, timeframe: str, result: ValidationResult) -> ValidationResult:
        """Detect gaps in timestamp continuity."""
        if len(df) < 2:
            return result
        
        # Parse timeframe to expected timedelta
        expected_td = self._timeframe_to_timedelta(timeframe)
        if expected_td is None:
            return result
        
        # Calculate actual deltas
        time_diffs = df.index.to_series().diff()
        max_allowed = expected_td * self.max_gap_multiplier
        
        gaps = time_diffs > max_allowed
        n_gaps = gaps.sum()
        
        if n_gaps > 0:
            result.gaps_detected = int(n_gaps)
            
            # Find the largest gap
            gap_indices = time_diffs[gaps]
            max_gap = gap_indices.max()
            result.warnings.append(
                f"{n_gaps} gaps detected (expected interval: {expected_td}, "
                f"max gap: {max_gap}, threshold: {max_allowed})"
            )
            
            if n_gaps > len(df) * 0.05:
                result.errors.append(f"Excessive gaps: {n_gaps}/{len(df)} intervals ({round(n_gaps/len(df)*100, 1)}%)")
        
        return result
    
    def _detect_outliers(self, df: pd.DataFrame, result: ValidationResult) -> Tuple[pd.DataFrame, ValidationResult]:
        """Detect statistical outliers using modified Z-score."""
        if len(df) < 30:
            return df, result
        
        if "close" not in df.columns:
            return df, result
        
        # Use returns for outlier detection (more stationary than prices)
        returns = df["close"].pct_change().dropna()
        
        if len(returns) < 10:
            return df, result
        
        # Modified Z-score using median absolute deviation (MAD)
        median = returns.median()
        mad = (returns - median).abs().median()
        
        if mad == 0:
            return df, result
        
        modified_z = 0.6745 * (returns - median) / mad
        outliers = modified_z.abs() > self.outlier_z_threshold
        
        if outliers.any():
            n_outliers = outliers.sum()
            result.outliers_detected += n_outliers
            
            if n_outliers <= len(df) * 0.01:
                # Remove only if small percentage
                df = df.drop(outliers[outliers].index)
                result.rows_removed += n_outliers
                result.warnings.append(f"Removed {n_outliers} statistical outliers (Z>{self.outlier_z_threshold})")
            else:
                result.warnings.append(
                    f"Detected {n_outliers} potential outliers but not removing (>{1}% of data). "
                    f"Review data source quality."
                )
        
        return df, result
    
    def _detect_staleness(self, df: pd.DataFrame, result: ValidationResult) -> ValidationResult:
        """Detect frozen/stale data feed."""
        if "close" not in df.columns or len(df) < self.max_stale_bars:
            return result
        
        # Count consecutive same-close prices
        close_diff = df["close"].diff()
        is_stale = close_diff == 0
        
        # Find runs of stale data
        stale_runs = []
        current_run = 0
        for val in is_stale:
            if val:
                current_run += 1
            else:
                if current_run >= self.max_stale_bars:
                    stale_runs.append(current_run)
                current_run = 0
        if current_run >= self.max_stale_bars:
            stale_runs.append(current_run)
        
        if stale_runs:
            total_stale = sum(stale_runs)
            max_run = max(stale_runs)
            result.warnings.append(
                f"Stale data detected: {len(stale_runs)} runs of {self.max_stale_bars}+ "
                f"consecutive identical closes (max run: {max_run} bars, total: {total_stale} bars)"
            )
            
            if max_run > self.max_stale_bars * 5:
                result.errors.append(f"Extremely stale data: {max_run} consecutive identical closes")
        
        return result
    
    @staticmethod
    def _timeframe_to_timedelta(tf: str) -> Optional[timedelta]:
        """Convert timeframe string to timedelta."""
        tf = tf.lower().strip()
        mapping = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "4h": timedelta(hours=4),
            "6h": timedelta(hours=6),
            "8h": timedelta(hours=8),
            "12h": timedelta(hours=12),
            "1d": timedelta(days=1),
            "d1": timedelta(days=1),
            "h1": timedelta(hours=1),
            "h4": timedelta(hours=4),
            "m1": timedelta(minutes=1),
            "m5": timedelta(minutes=5),
            "m15": timedelta(minutes=15),
            "m30": timedelta(minutes=30),
            "w1": timedelta(weeks=1),
        }
        return mapping.get(tf)
    
    def quick_check(self, df: pd.DataFrame) -> bool:
        """Fast sanity check without full validation. Returns True if data looks usable."""
        if df is None or df.empty:
            return False
        if len(df) < 10:
            return False
        
        cols = {c.lower() for c in df.columns}
        if "close" not in cols:
            return False
        
        close_col = [c for c in df.columns if c.lower() == "close"][0]
        if df[close_col].isna().sum() > len(df) * 0.1:
            return False
        if (df[close_col] <= 0).any():
            return False
        
        return True
