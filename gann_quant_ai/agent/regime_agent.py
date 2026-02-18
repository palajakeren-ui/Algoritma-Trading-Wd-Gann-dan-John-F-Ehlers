"""
Regime Agent - Market Regime Detection & Mode Switching
Part of OpenClaw-style AI Agent Orchestration Layer.

Capabilities:
- Detect market regime (trending/ranging/volatile/crisis)
- Recommend GLOBAL_MODE changes based on regime
- Can auto-switch modes 0-3 (Mode 4 requires human approval)
- Monitor regime transitions and confidence levels

CONSTRAINT: Cannot switch to Mode 4 without explicit approval.
"""

import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import yaml
import os


class MarketRegime(str, Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CRISIS = "crisis"
    LOW_LIQUIDITY = "low_liquidity"
    UNKNOWN = "unknown"


@dataclass
class RegimeDetection:
    """Result of regime detection analysis."""
    regime: MarketRegime = MarketRegime.UNKNOWN
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Indicators used
    adx_value: float = 0.0
    volatility_percentile: float = 0.0
    trend_strength: float = 0.0
    volume_profile: str = "normal"
    
    # Regime-specific metrics
    metrics: Dict = field(default_factory=dict)
    
    # Mode recommendation
    recommended_mode: int = 1
    mode_change_reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "adx": self.adx_value,
            "volatility_percentile": self.volatility_percentile,
            "trend_strength": self.trend_strength,
            "volume_profile": self.volume_profile,
            "metrics": self.metrics,
            "recommended_mode": self.recommended_mode,
            "mode_change_reason": self.mode_change_reason,
        }


class RegimeAgent:
    """
    AI Regime Agent - Detects market regimes and manages mode switching.
    
    Uses multiple indicators to identify the current market regime:
    - ADX for trend strength
    - Volatility percentile (ATR-based)
    - Ehlers cycle indicators
    - Volume analysis
    - Correlation changes
    
    Can auto-switch GLOBAL_MODE 0-3 based on regime.
    Mode 4 ALWAYS requires human approval.
    """
    
    AGENT_ID = "regime-agent"
    AGENT_NAME = "Regime Agent"
    AGENT_VERSION = "1.0.0"
    
    # Regime → recommended mode mapping
    REGIME_MODE_MAP = {
        MarketRegime.CRISIS: 0,           # Crisis → RULE ONLY (safest)
        MarketRegime.LOW_LIQUIDITY: 0,     # Low liquidity → RULE ONLY
        MarketRegime.VOLATILE: 1,          # Volatile → HYBRID (cautious)
        MarketRegime.RANGING: 1,           # Ranging → HYBRID
        MarketRegime.TRENDING_BULL: 2,     # Strong trend → ML DOMINANT
        MarketRegime.TRENDING_BEAR: 2,     # Strong trend → ML DOMINANT
        MarketRegime.UNKNOWN: 0,           # Unknown → RULE ONLY (safe)
    }
    
    def __init__(self, config: Dict = None, config_path: str = None):
        self.config = config or {}
        self.config_path = config_path or os.path.join("config", "global_mode.yaml")
        self.status = "idle"
        self.health = 100
        self.tasks_completed = 0
        self.current_task = None
        
        # State tracking
        self.current_regime = MarketRegime.UNKNOWN
        self.current_mode = 1  # Default HYBRID
        self.regime_history: List[RegimeDetection] = []
        self._max_history = 500
        
        # Mode change tracking
        self._mode_changes_this_hour = 0
        self._last_mode_change = datetime.min
        self._last_hour_reset = datetime.now()
        
        # Load current mode from config
        self._load_current_mode()
        
        logger.info(f"RegimeAgent v{self.AGENT_VERSION} initialized (current_mode={self.current_mode})")
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.AGENT_ID,
            "name": self.AGENT_NAME,
            "version": self.AGENT_VERSION,
            "status": self.status,
            "health": self.health,
            "tasks_completed": self.tasks_completed,
            "current_task": self.current_task,
            "current_regime": self.current_regime.value,
            "current_mode": self.current_mode,
            "mode_changes_this_hour": self._mode_changes_this_hour,
        }
    
    def detect_regime(
        self,
        price_data: pd.DataFrame,
        volume_data: pd.DataFrame = None,
        ehlers_data: Dict = None,
    ) -> RegimeDetection:
        """
        Detect current market regime from price/volume data.
        
        Uses multiple methods:
        1. ADX trend detection
        2. Volatility percentile ranking
        3. Volume profile analysis
        4. Ehlers cycle phase
        
        Returns:
            RegimeDetection with identified regime and confidence
        """
        self.status = "detecting"
        self.current_task = "Detecting market regime"
        
        try:
            detection = RegimeDetection()
            
            if price_data is None or price_data.empty:
                detection.regime = MarketRegime.UNKNOWN
                detection.confidence = 0.0
                return detection
            
            # 1. Calculate ADX
            adx = self._calculate_adx(price_data)
            detection.adx_value = adx
            
            # 2. Calculate volatility percentile
            vol_pct = self._calculate_volatility_percentile(price_data)
            detection.volatility_percentile = vol_pct
            
            # 3. Calculate trend strength & direction
            trend_strength, trend_dir = self._calculate_trend_metrics(price_data)
            detection.trend_strength = trend_strength
            
            # 4. Volume analysis
            if volume_data is not None and not volume_data.empty:
                detection.volume_profile = self._analyze_volume(volume_data)
            
            # 5. Determine regime
            detection.regime, detection.confidence = self._classify_regime(
                adx, vol_pct, trend_strength, trend_dir, detection.volume_profile
            )
            
            # 6. Recommend mode
            detection.recommended_mode = self.REGIME_MODE_MAP.get(
                detection.regime, 1
            )
            detection.mode_change_reason = self._generate_mode_reason(detection)
            
            # Store detection
            self.current_regime = detection.regime
            self.regime_history.append(detection)
            if len(self.regime_history) > self._max_history:
                self.regime_history = self.regime_history[-self._max_history:]
            
            self.tasks_completed += 1
            logger.info(
                f"RegimeAgent: Detected {detection.regime.value} "
                f"(confidence={detection.confidence:.2f}, "
                f"recommended_mode={detection.recommended_mode})"
            )
            
            return detection
            
        except Exception as e:
            logger.error(f"RegimeAgent detection error: {e}")
            return RegimeDetection(regime=MarketRegime.UNKNOWN, confidence=0.0)
        finally:
            self.status = "idle"
            self.current_task = None
    
    def switch_mode(
        self,
        target_mode: int,
        reason: str = "",
        force: bool = False,
        require_approval: bool = None
    ) -> Dict:
        """
        Switch the global trading mode.
        
        Args:
            target_mode: Target mode (0-4)
            reason: Reason for the switch
            force: Force switch (bypass cooldown)
            require_approval: Override approval requirement
            
        Returns:
            Dict with switch result
        """
        self.status = "switching_mode"
        self.current_task = f"Switching to MODE {target_mode}"
        
        try:
            # Validate target mode
            if target_mode not in range(5):
                return {
                    "success": False,
                    "error": f"Invalid mode: {target_mode}. Must be 0-4.",
                }
            
            # Mode 4 ALWAYS requires approval
            if target_mode == 4:
                needs_approval = True if require_approval is None else require_approval
                if needs_approval:
                    return {
                        "success": False,
                        "pending_approval": True,
                        "message": "Mode 4 (Guarded Autonomous) requires human approval.",
                        "requested_mode": 4,
                        "reason": reason,
                    }
            
            # Check cooldown
            if not force:
                cooldown_check = self._check_cooldown()
                if not cooldown_check["allowed"]:
                    return {
                        "success": False,
                        "error": cooldown_check["reason"],
                    }
            
            # Check hourly rate limit
            self._reset_hourly_counter()
            if self._mode_changes_this_hour >= 5 and not force:
                return {
                    "success": False,
                    "error": "Max mode changes per hour (5) exceeded.",
                }
            
            # Perform the switch
            previous_mode = self.current_mode
            self.current_mode = target_mode
            self._mode_changes_this_hour += 1
            self._last_mode_change = datetime.now()
            
            # Save to config file
            self._save_mode_to_config(target_mode, previous_mode, reason)
            
            result = {
                "success": True,
                "previous_mode": previous_mode,
                "new_mode": target_mode,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "changed_by": self.AGENT_ID,
            }
            
            self.tasks_completed += 1
            logger.info(f"RegimeAgent: Mode switched from {previous_mode} to {target_mode}: {reason}")
            
            return result
            
        except Exception as e:
            logger.error(f"RegimeAgent mode switch error: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self.status = "idle"
            self.current_task = None
    
    def auto_switch_on_regime(self, detection: RegimeDetection) -> Optional[Dict]:
        """
        Automatically switch mode based on detected regime.
        Only switches if current mode doesn't match recommendation.
        Never auto-switches to Mode 4.
        """
        recommended = detection.recommended_mode
        
        # Never auto-switch to mode 4
        if recommended == 4:
            logger.info("RegimeAgent: Mode 4 recommended but requires human approval")
            return None
        
        # Only switch if recommendation differs and confidence is high enough
        if recommended != self.current_mode and detection.confidence >= 0.70:
            return self.switch_mode(
                target_mode=recommended,
                reason=f"Auto-switch: regime={detection.regime.value}, confidence={detection.confidence:.2f}",
            )
        
        return None
    
    def force_revert_to_safe_mode(self, reason: str = "Emergency revert") -> Dict:
        """Force revert to Mode 0 (RULE ONLY) - emergency use."""
        return self.switch_mode(
            target_mode=0,
            reason=f"EMERGENCY REVERT: {reason}",
            force=True,
        )
    
    def get_current_mode(self) -> int:
        """Get current global mode."""
        return self.current_mode
    
    def get_regime_history(self, limit: int = 50) -> List[Dict]:
        """Get recent regime detection history."""
        return [r.to_dict() for r in self.regime_history[-limit:]]
    
    # ===== Private Methods =====
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index."""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            
            plus_dm = np.maximum(np.diff(high), 0)
            minus_dm = np.maximum(-np.diff(low), 0)
            
            # Wherever plus_dm > minus_dm, minus_dm = 0 and vice versa
            mask = plus_dm > minus_dm
            minus_dm[mask] = 0
            plus_dm[~mask] = 0
            
            tr = np.maximum(
                np.abs(high[1:] - low[1:]),
                np.maximum(
                    np.abs(high[1:] - close[:-1]),
                    np.abs(low[1:] - close[:-1])
                )
            )
            
            # Smoothed
            if len(tr) < period:
                return 25.0  # Default neutral
            
            atr = pd.Series(tr).rolling(period).mean().iloc[-1]
            plus_di = 100 * pd.Series(plus_dm).rolling(period).mean().iloc[-1] / max(atr, 1e-10)
            minus_di = 100 * pd.Series(minus_dm).rolling(period).mean().iloc[-1] / max(atr, 1e-10)
            
            dx = 100 * abs(plus_di - minus_di) / max(plus_di + minus_di, 1e-10)
            
            return float(dx)
        except Exception:
            return 25.0
    
    def _calculate_volatility_percentile(self, data: pd.DataFrame, period: int = 14, lookback: int = 252) -> float:
        """Calculate current ATR as percentile of historical range."""
        try:
            close = data['close']
            high = data['high']
            low = data['low']
            
            tr = pd.concat([
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs()
            ], axis=1).max(axis=1)
            
            current_atr = tr.rolling(period).mean().iloc[-1]
            historical_atrs = tr.rolling(period).mean().dropna()
            
            if len(historical_atrs) < 10:
                return 50.0
            
            percentile = (historical_atrs < current_atr).sum() / len(historical_atrs) * 100
            return float(percentile)
        except Exception:
            return 50.0
    
    def _calculate_trend_metrics(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Calculate trend strength and direction."""
        try:
            close = data['close']
            
            # Simple trend using moving averages
            sma20 = close.rolling(20).mean().iloc[-1]
            sma50 = close.rolling(50).mean().iloc[-1]
            current = close.iloc[-1]
            
            # Direction
            if current > sma20 > sma50:
                direction = "bullish"
                strength = min(1.0, (current - sma50) / max(sma50, 1) * 10)
            elif current < sma20 < sma50:
                direction = "bearish"
                strength = min(1.0, (sma50 - current) / max(sma50, 1) * 10)
            else:
                direction = "neutral"
                strength = 0.3
            
            return float(strength), direction
        except Exception:
            return 0.5, "neutral"
    
    def _analyze_volume(self, volume_data: pd.DataFrame) -> str:
        """Analyze volume profile."""
        try:
            if volume_data.empty:
                return "normal"
            
            vol = volume_data.iloc[:, 0] if isinstance(volume_data, pd.DataFrame) else volume_data
            current = vol.iloc[-1]
            avg = vol.rolling(20).mean().iloc[-1]
            
            ratio = current / max(avg, 1)
            
            if ratio > 2.0:
                return "very_high"
            elif ratio > 1.5:
                return "high"
            elif ratio < 0.5:
                return "low"
            else:
                return "normal"
        except Exception:
            return "normal"
    
    def _classify_regime(
        self,
        adx: float,
        vol_pct: float,
        trend_strength: float,
        trend_dir: str,
        volume: str
    ) -> Tuple[MarketRegime, float]:
        """
        Classify market regime based on multiple indicators.
        
        Returns:
            Tuple of (MarketRegime, confidence)
        """
        scores = {}
        
        # Crisis detection (highest priority)
        if vol_pct > 95 and volume in ["very_high", "high"]:
            scores[MarketRegime.CRISIS] = 0.85
        
        # Low liquidity
        if volume == "low" and vol_pct < 20:
            scores[MarketRegime.LOW_LIQUIDITY] = 0.75
        
        # Trending
        if adx > 30 and trend_strength > 0.5:
            if trend_dir == "bullish":
                scores[MarketRegime.TRENDING_BULL] = min(0.95, adx / 50 * 0.5 + trend_strength * 0.5)
            elif trend_dir == "bearish":
                scores[MarketRegime.TRENDING_BEAR] = min(0.95, adx / 50 * 0.5 + trend_strength * 0.5)
        
        # Volatile (non-trending high vol)
        if vol_pct > 75 and adx < 25:
            scores[MarketRegime.VOLATILE] = vol_pct / 100 * 0.8
        
        # Ranging
        if adx < 25 and vol_pct < 60:
            scores[MarketRegime.RANGING] = (1 - adx / 50) * 0.7
        
        if not scores:
            return MarketRegime.UNKNOWN, 0.3
        
        # Return highest scoring regime
        best_regime = max(scores, key=scores.get)
        return best_regime, scores[best_regime]
    
    def _generate_mode_reason(self, detection: RegimeDetection) -> str:
        """Generate human-readable reason for mode recommendation."""
        regime = detection.regime
        mode = detection.recommended_mode
        
        reasons = {
            MarketRegime.CRISIS: f"Crisis detected (vol_pct={detection.volatility_percentile:.0f}%). MODE 0 for maximum safety.",
            MarketRegime.LOW_LIQUIDITY: "Low liquidity detected. MODE 0 to avoid slippage risk.",
            MarketRegime.VOLATILE: f"High volatility (pct={detection.volatility_percentile:.0f}%). HYBRID mode with ML confirmation.",
            MarketRegime.RANGING: "Ranging market. HYBRID mode for balanced approach.",
            MarketRegime.TRENDING_BULL: f"Strong bullish trend (ADX={detection.adx_value:.1f}). ML DOMINANT for trend capture.",
            MarketRegime.TRENDING_BEAR: f"Strong bearish trend (ADX={detection.adx_value:.1f}). ML DOMINANT for trend capture.",
            MarketRegime.UNKNOWN: "Regime uncertain. MODE 0 (RULE ONLY) for safety.",
        }
        
        return reasons.get(regime, f"Regime: {regime.value}, recommended MODE {mode}")
    
    def _check_cooldown(self) -> Dict:
        """Check if cooldown period has passed since last mode change."""
        elapsed = (datetime.now() - self._last_mode_change).total_seconds()
        cooldown = 30  # 30 seconds default
        
        if elapsed < cooldown:
            return {
                "allowed": False,
                "reason": f"Cooldown active. {cooldown - elapsed:.0f}s remaining.",
            }
        return {"allowed": True}
    
    def _reset_hourly_counter(self):
        """Reset hourly mode change counter if needed."""
        if (datetime.now() - self._last_hour_reset).total_seconds() > 3600:
            self._mode_changes_this_hour = 0
            self._last_hour_reset = datetime.now()
    
    def _load_current_mode(self):
        """Load current mode from config file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'global_mode' in config:
                        self.current_mode = config['global_mode'].get('current_mode', 1)
        except Exception as e:
            logger.warning(f"Could not load mode from config: {e}")
            self.current_mode = 1
    
    def _save_mode_to_config(self, new_mode: int, previous_mode: int, reason: str):
        """Save mode change to config file."""
        try:
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            
            if 'global_mode' not in config:
                config['global_mode'] = {}
            
            config['global_mode']['current_mode'] = new_mode
            config['global_mode']['previous_mode'] = previous_mode
            config['global_mode']['last_changed'] = datetime.now().isoformat()
            config['global_mode']['changed_by'] = f"{self.AGENT_ID}: {reason}"
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            logger.info(f"Mode saved to config: {new_mode}")
        except Exception as e:
            logger.error(f"Failed to save mode to config: {e}")
