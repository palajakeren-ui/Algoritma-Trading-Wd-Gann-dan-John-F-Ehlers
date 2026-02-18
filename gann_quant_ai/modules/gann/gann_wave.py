"""
Gann Wave Module
Wave analysis and projections using authentic Gann Angle ratios (16x1 to 1x16).

Gann Angles represent the relationship between price movement and time:
- 16x1 = 16 price units per 1 time unit (steepest bullish, ~86.42°)
- 8x1  = 8 price units per 1 time unit (~82.87°)
- 4x1  = 4 price units per 1 time unit (~75.96°)
- 3x1  = 3 price units per 1 time unit (~71.57°)
- 2x1  = 2 price units per 1 time unit (~63.43°)
- 1x1  = 1 price unit per 1 time unit (45° — the Master Angle)
- 1x2  = 1 price unit per 2 time units (~26.57°)
- 1x3  = 1 price unit per 3 time units (~18.43°)
- 1x4  = 1 price unit per 4 time units (~14.04°)
- 1x8  = 1 price unit per 8 time units (~7.13°)
- 1x16 = 1 price unit per 16 time units (~3.58°)
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger


# ═══════════════════════════════════════════════════════════════
# GANN ANGLE DEFINITIONS (Price/Time ratios)
# ═══════════════════════════════════════════════════════════════

GANN_ANGLES = {
    "16x1": {"ratio": 16.0,    "degrees": 86.42, "strength": "extreme_bullish"},
    "8x1":  {"ratio": 8.0,     "degrees": 82.87, "strength": "very_strong_bullish"},
    "4x1":  {"ratio": 4.0,     "degrees": 75.96, "strength": "strong_bullish"},
    "3x1":  {"ratio": 3.0,     "degrees": 71.57, "strength": "bullish"},
    "2x1":  {"ratio": 2.0,     "degrees": 63.43, "strength": "moderate_bullish"},
    "1x1":  {"ratio": 1.0,     "degrees": 45.00, "strength": "balanced"},         # Master Angle
    "1x2":  {"ratio": 0.5,     "degrees": 26.57, "strength": "moderate_bearish"},
    "1x3":  {"ratio": 1/3,     "degrees": 18.43, "strength": "bearish"},
    "1x4":  {"ratio": 0.25,    "degrees": 14.04, "strength": "strong_bearish"},
    "1x8":  {"ratio": 0.125,   "degrees": 7.13,  "strength": "very_strong_bearish"},
    "1x16": {"ratio": 0.0625,  "degrees": 3.58,  "strength": "extreme_bearish"},
}

# Ordered ratios from steepest to flattest
GANN_RATIOS = [16.0, 8.0, 4.0, 3.0, 2.0, 1.0, 0.5, 1/3, 0.25, 0.125, 0.0625]

GANN_ANGLE_NAMES = [
    "16x1", "8x1", "4x1", "3x1", "2x1",
    "1x1",
    "1x2", "1x3", "1x4", "1x8", "1x16",
]

# Retracement ratios derived from Gann angles
GANN_RETRACEMENT_RATIOS = {
    "1x16":  0.0625,   # ~6.25% — shallowest
    "1x8":   0.125,    # ~12.5%
    "1x4":   0.25,     # ~25%
    "1x3":   1/3,      # ~33.3%
    "1x2":   0.5,      # ~50% — critical
    "1x1":   1.0,      # ~100% — full retracement
    "2x1":   2.0,      # ~200% — extension
    "3x1":   3.0,      # ~300% — extension
    "4x1":   4.0,      # ~400% — extension
}


class GannWave:
    """
    Gann Wave Analysis with authentic angle ratios (16x1 to 1x16).
    
    Key concepts:
    - Price above 1x1 (45°) from low = bullish
    - Price below 1x1 (45°) from high = bearish
    - Breaking above/below angle lines = trend change
    - Wave projections use angle ratios for targets
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.price_scale = self.config.get("price_scale", 1.0)  # Scale factor for price/time normalization
        
        # Gann angle ratios: 16x1 down to 1x16
        self.angles = GANN_ANGLES
        self.ratios = GANN_RATIOS
        self.angle_names = GANN_ANGLE_NAMES
        
        logger.info(f"GannWave initialized with {len(self.angles)} Gann angles (16x1 → 1x16)")
    
    def calculate_angle_lines(
        self, 
        pivot_price: float, 
        pivot_bar: int, 
        n_bars: int, 
        direction: str = "up"
    ) -> Dict[str, List[float]]:
        """
        Calculate Gann angle fan lines from a pivot point.
        
        Args:
            pivot_price: Price at the pivot point
            pivot_bar: Bar index of the pivot
            n_bars: Number of bars to project forward
            direction: 'up' from low or 'down' from high
            
        Returns:
            Dict of angle_name → list of projected price levels per bar
        """
        lines = {}
        sign = 1 if direction == "up" else -1
        
        for name, angle_info in self.angles.items():
            ratio = angle_info["ratio"]
            prices = []
            
            for bar in range(n_bars):
                bars_from_pivot = bar
                # Price change = ratio × time_elapsed × price_scale
                price_change = ratio * bars_from_pivot * self.price_scale * sign
                projected_price = pivot_price + price_change
                prices.append(round(projected_price, 2))
            
            lines[name] = prices
        
        return lines
    
    def get_current_angle_position(
        self, 
        current_price: float, 
        pivot_price: float, 
        bars_elapsed: int
    ) -> Dict:
        """
        Determine which Gann angles the current price is between.
        
        Returns:
            Dict with angle_above, angle_below, and bias
        """
        if bars_elapsed <= 0:
            return {"angle_above": "16x1", "angle_below": "1x16", "bias": "neutral"}
        
        # Calculate actual price/time ratio
        price_change = abs(current_price - pivot_price)
        actual_ratio = price_change / (bars_elapsed * self.price_scale) if bars_elapsed > 0 else 0
        
        # Determine direction
        is_above_pivot = current_price > pivot_price
        
        # Find which angles the price is between
        angle_above = None
        angle_below = None
        
        sorted_ratios = sorted(GANN_RATIOS, reverse=True)
        
        for i, ratio in enumerate(sorted_ratios):
            if actual_ratio >= ratio:
                angle_above_idx = max(0, i)
                angle_below_idx = i
                angle_above = GANN_ANGLE_NAMES[angle_above_idx]
                if i > 0:
                    angle_above = GANN_ANGLE_NAMES[i - 1]
                angle_below = GANN_ANGLE_NAMES[i]
                break
        
        if angle_above is None:
            angle_above = "1x16"
            angle_below = "1x16"
        
        # Determine bias based on 1x1 (Master Angle)
        master_angle_price = pivot_price + (1.0 * bars_elapsed * self.price_scale)
        
        if is_above_pivot:
            if current_price > master_angle_price:
                bias = "bullish"
            else:
                bias = "bearish"
        else:
            bias = "bearish"
        
        # Strength based on angle
        if actual_ratio >= 4.0:
            strength = "very_strong"
        elif actual_ratio >= 2.0:
            strength = "strong"
        elif actual_ratio >= 1.0:
            strength = "moderate"
        elif actual_ratio >= 0.5:
            strength = "weak"
        else:
            strength = "very_weak"
        
        return {
            "actual_ratio": round(actual_ratio, 4),
            "actual_degrees": round(np.degrees(np.arctan(actual_ratio)), 2),
            "angle_above": angle_above,
            "angle_below": angle_below,
            "above_1x1_master": is_above_pivot and current_price > master_angle_price,
            "bias": bias,
            "trend_strength": strength,
        }
    
    def project_wave(self, wave_start: float, wave_end: float) -> Dict[str, List[Dict]]:
        """
        Project next wave targets based on Gann angle ratios.
        
        Uses all 11 Gann angles (16x1 to 1x16) for both:
        - Continuation targets (same direction)
        - Retracement targets (opposite direction)
        """
        wave_size = abs(wave_end - wave_start)
        direction = 1 if wave_end > wave_start else -1
        
        # Continuation targets using Gann angle ratios
        continuation = []
        for name in self.angle_names:
            ratio = self.angles[name]["ratio"]
            target = wave_end + (wave_size * ratio * direction)
            continuation.append({
                "angle": name,
                "ratio": ratio,
                "degrees": self.angles[name]["degrees"],
                "target": round(target, 2),
                "move_pct": round(ratio * 100, 2),
                "strength": self.angles[name]["strength"],
            })
        
        # Retracement targets using Gann angle ratios (opposite direction)
        retracement = []
        for name, ratio in GANN_RETRACEMENT_RATIOS.items():
            if ratio <= 1.0:  # Only retrace up to 100%
                target = wave_end - (wave_size * ratio * direction)
                retracement.append({
                    "angle": name,
                    "ratio": ratio,
                    "target": round(target, 2),
                    "retrace_pct": round(ratio * 100, 2),
                })
        
        return {
            "continuation": continuation,
            "retracement": retracement,
            "wave_size": round(wave_size, 2),
            "wave_pct": round((wave_size / wave_start) * 100, 2) if wave_start > 0 else 0,
            "direction": "up" if direction > 0 else "down",
            "key_levels": {
                "1x1_continuation": round(wave_end + (wave_size * 1.0 * direction), 2),
                "2x1_continuation": round(wave_end + (wave_size * 2.0 * direction), 2),
                "1x2_retracement": round(wave_end - (wave_size * 0.5 * direction), 2),
                "1x1_full_retrace": round(wave_end - (wave_size * 1.0 * direction), 2),
            }
        }
    
    def identify_waves(self, df: pd.DataFrame, min_wave_pct: float = 0.05) -> List[Dict]:
        """Identify waves in price data with Gann angle classification."""
        waves = []
        highs = df['high'].values
        lows = df['low'].values
        
        # Find swing points
        swings = []
        for i in range(2, len(df) - 2):
            if highs[i] > max(highs[i-2:i]) and highs[i] > max(highs[i+1:i+3]):
                swings.append({'index': i, 'type': 'high', 'price': float(highs[i])})
            if lows[i] < min(lows[i-2:i]) and lows[i] < min(lows[i+1:i+3]):
                swings.append({'index': i, 'type': 'low', 'price': float(lows[i])})
        
        swings.sort(key=lambda x: x['index'])
        
        # Build waves from swing points
        for i in range(len(swings) - 1):
            s1, s2 = swings[i], swings[i+1]
            wave_pct = abs(s2['price'] - s1['price']) / s1['price'] if s1['price'] > 0 else 0
            
            if wave_pct >= min_wave_pct:
                bars = s2['index'] - s1['index']
                price_change = abs(s2['price'] - s1['price'])
                
                # Calculate wave's Gann angle
                wave_ratio = (price_change / (bars * self.price_scale)) if bars > 0 and self.price_scale > 0 else 0
                wave_degrees = float(np.degrees(np.arctan(wave_ratio)))
                
                # Find closest Gann angle
                closest_angle = self._find_closest_angle(wave_ratio)
                
                waves.append({
                    'start_idx': s1['index'],
                    'end_idx': s2['index'],
                    'start_price': s1['price'],
                    'end_price': s2['price'],
                    'direction': 'up' if s2['price'] > s1['price'] else 'down',
                    'size_pct': round(wave_pct * 100, 2),
                    'bars': bars,
                    'gann_ratio': round(wave_ratio, 4),
                    'gann_degrees': round(wave_degrees, 2),
                    'closest_angle': closest_angle,
                    'projections': self.project_wave(s1['price'], s2['price']),
                })
        
        return waves
    
    def calculate_wave_harmony(self, waves: List[Dict]) -> Dict:
        """
        Calculate wave harmony score using Gann angle ratios.
        
        Perfect harmony = consecutive waves follow exact Gann angle ratios.
        """
        if len(waves) < 2:
            return {"harmony_score": 0.5, "details": []}
        
        harmony_details = []
        
        for i in range(len(waves) - 1):
            w1_size = abs(waves[i]['end_price'] - waves[i]['start_price'])
            w2_size = abs(waves[i+1]['end_price'] - waves[i+1]['start_price'])
            
            if w1_size > 0:
                ratio = w2_size / w1_size
                
                # Find closest Gann angle ratio
                closest_ratio = min(self.ratios, key=lambda x: abs(x - ratio))
                closest_name = self._ratio_to_name(closest_ratio)
                deviation = abs(ratio - closest_ratio) / closest_ratio if closest_ratio > 0 else 1
                harmony = max(0, 1 - deviation)
                
                harmony_details.append({
                    "wave_pair": f"W{i+1}→W{i+2}",
                    "actual_ratio": round(ratio, 4),
                    "closest_gann_angle": closest_name,
                    "closest_gann_ratio": closest_ratio,
                    "deviation_pct": round(deviation * 100, 2),
                    "harmony": round(harmony, 4),
                })
        
        avg_harmony = sum(d["harmony"] for d in harmony_details) / len(harmony_details) if harmony_details else 0.5
        
        return {
            "harmony_score": round(avg_harmony, 4),
            "wave_count": len(waves),
            "pairs_analyzed": len(harmony_details),
            "details": harmony_details,
            "assessment": (
                "Perfect Gann Harmony" if avg_harmony > 0.9 else
                "Strong Harmony" if avg_harmony > 0.75 else
                "Moderate Harmony" if avg_harmony > 0.5 else
                "Weak Harmony" if avg_harmony > 0.25 else
                "No Gann Harmony"
            ),
        }
    
    def get_support_resistance_from_angles(
        self,
        pivot_price: float,
        pivot_bar: int,
        current_bar: int,
        direction: str = "up",
    ) -> List[Dict]:
        """
        Get support/resistance levels from Gann angle lines at the current bar.
        
        Returns list of levels from all 11 angles at the current bar position.
        """
        bars_elapsed = current_bar - pivot_bar
        if bars_elapsed <= 0:
            return []
        
        sign = 1 if direction == "up" else -1
        levels = []
        
        for name, angle_info in self.angles.items():
            ratio = angle_info["ratio"]
            price_at_angle = pivot_price + (ratio * bars_elapsed * self.price_scale * sign)
            
            level_type = "support" if direction == "up" else "resistance"
            if name == "1x1":
                level_type = "master_angle"
            
            levels.append({
                "angle": name,
                "price": round(price_at_angle, 2),
                "degrees": angle_info["degrees"],
                "type": level_type,
                "strength": angle_info["strength"],
            })
        
        return sorted(levels, key=lambda x: x["price"], reverse=True)
    
    def _find_closest_angle(self, ratio: float) -> str:
        """Find the closest Gann angle name for a given ratio."""
        closest_ratio = min(self.ratios, key=lambda x: abs(x - ratio))
        return self._ratio_to_name(closest_ratio)
    
    @staticmethod
    def _ratio_to_name(ratio: float) -> str:
        """Convert a numeric ratio to Gann angle name."""
        ratio_to_name = {
            16.0: "16x1", 8.0: "8x1", 4.0: "4x1", 3.0: "3x1", 2.0: "2x1",
            1.0: "1x1",
            0.5: "1x2", 1/3: "1x3", 0.25: "1x4", 0.125: "1x8", 0.0625: "1x16",
        }
        closest = min(ratio_to_name.keys(), key=lambda x: abs(x - ratio))
        return ratio_to_name[closest]
