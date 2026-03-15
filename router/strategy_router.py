"""
Strategy Router - Central signal routing based on GLOBAL_MODE

Routes signals through the appropriate pipeline:
MODE 0: Signal = Rule (Gann + Ehlers only)
MODE 1: Rule + ML confirmation (Rule=BUY AND ML_prob > threshold → BUY)
MODE 2: ML dominant, Rule as structural filter
MODE 3: AI can override parameters, not orders
MODE 4: AI can propose trades → validation gate

The Strategy Router sits between the engines and the Risk Engine.
It NEVER bypasses Risk Engine validation.
"""

import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os
import yaml


class SignalDecision(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class RoutedSignal:
    """Signal output from the Strategy Router."""
    signal_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Signal
    symbol: str = ""
    decision: SignalDecision = SignalDecision.HOLD
    confidence: float = 0.0
    
    # Routing info
    mode: int = 0
    mode_name: str = ""
    routing_path: str = ""  # Which engines contributed
    
    # Component signals
    rule_signal: Dict = field(default_factory=dict)
    ml_signal: Dict = field(default_factory=dict)
    ai_signal: Dict = field(default_factory=dict)
    
    # Entry/Exit levels
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    position_size_pct: float = 0.0
    
    # Attribution
    signal_sources: List[str] = field(default_factory=list)
    source_weights: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "decision": self.decision.value,
            "confidence": self.confidence,
            "mode": self.mode,
            "mode_name": self.mode_name,
            "routing_path": self.routing_path,
            "rule_signal": self.rule_signal,
            "ml_signal": self.ml_signal,
            "ai_signal": self.ai_signal,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size_pct": self.position_size_pct,
            "signal_sources": self.signal_sources,
            "source_weights": self.source_weights,
            "metadata": self.metadata,
        }


class StrategyRouter:
    """
    Strategy Router - Routes signals based on global mode.
    
    Architecture:
    
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ Rule Engine  │   │  ML Engine   │   │  AI Agents   │
    │ (Gann+Ehlers)│   │ (Ensemble)   │   │ (Orchestrator)│
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                  │
           └────────────┬────┴──────────────────┘
                        │
                 ┌──────▼──────┐
                 │   Strategy  │
                 │   Router    │ ← Mode-based routing logic
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐
                 │ Risk Engine │ ← Final authority
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐
                 │  Execution  │
                 └─────────────┘
    
    Routing Logic:
    - MODE 0: signal = rule_engine_output
    - MODE 1: signal = rule_signal IF ml_confirms(rule_signal)
    - MODE 2: signal = ml_signal IF rule_allows(ml_signal)
    - MODE 3: signal = hybrid_signal + ai_parameter_adjustments
    - MODE 4: signal = hybrid_signal OR ai_proposals(validated)
    """
    
    MODE_NAMES = {
        0: "RULE ONLY",
        1: "HYBRID",
        2: "ML DOMINANT",
        3: "AI ASSISTED",
        4: "GUARDED AUTONOMOUS",
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Load global mode
        self._current_mode = self._load_mode()
        
        # Configuration thresholds
        self._ml_prob_threshold = self.config.get("ml_probability_threshold", 0.60)
        self._rule_confidence_threshold = self.config.get("confidence_threshold", 0.55)
        self._ml_dominant_threshold = self.config.get("ml_dominant_threshold", 0.70)
        
        # Signal history
        self._signal_history: List[RoutedSignal] = []
        self._max_history = 500
        
        # Counter
        self._signal_counter = 0
        
        logger.info(
            f"StrategyRouter initialized (mode={self._current_mode}, "
            f"ml_threshold={self._ml_prob_threshold})"
        )
    
    @property
    def current_mode(self) -> int:
        return self._current_mode
    
    @current_mode.setter
    def current_mode(self, mode: int):
        """Set mode with validation."""
        if mode in range(5):
            old_mode = self._current_mode
            self._current_mode = mode
            logger.info(f"StrategyRouter: Mode changed from {old_mode} to {mode}")
        else:
            logger.error(f"Invalid mode: {mode}")
    
    def route_signal(
        self,
        symbol: str,
        rule_output: Dict = None,
        ml_output: Dict = None,
        ai_output: Dict = None,
        price_data: pd.DataFrame = None,
    ) -> RoutedSignal:
        """
        Route signal through the appropriate pipeline based on current mode.
        
        Args:
            symbol: Trading symbol
            rule_output: Output from rule engine (Gann + Ehlers)
            ml_output: Output from ML engine (probability 0-1)
            ai_output: Output from AI agents (advisory/proposals)
            price_data: Current price data
            
        Returns:
            RoutedSignal with the final signal decision
        """
        self._signal_counter += 1
        
        signal = RoutedSignal(
            signal_id=f"sig-{self._signal_counter}-{datetime.now().strftime('%H%M%S')}",
            symbol=symbol,
            mode=self._current_mode,
            mode_name=self.MODE_NAMES.get(self._current_mode, "UNKNOWN"),
            rule_signal=rule_output or {},
            ml_signal=ml_output or {},
            ai_signal=ai_output or {},
        )
        
        try:
            if self._current_mode == 0:
                signal = self._route_mode_0(signal)
            elif self._current_mode == 1:
                signal = self._route_mode_1(signal)
            elif self._current_mode == 2:
                signal = self._route_mode_2(signal)
            elif self._current_mode == 3:
                signal = self._route_mode_3(signal)
            elif self._current_mode == 4:
                signal = self._route_mode_4(signal)
            else:
                # Unknown mode → fallback to MODE 0
                logger.warning(f"Unknown mode {self._current_mode}, falling back to MODE 0")
                signal = self._route_mode_0(signal)
            
            # Set price levels from rule output
            if rule_output:
                signal.entry_price = rule_output.get("entry_price", signal.entry_price)
                signal.stop_loss = rule_output.get("stop_loss", signal.stop_loss)
                signal.take_profit = rule_output.get("take_profit", signal.take_profit)
            
            # Store signal
            self._signal_history.append(signal)
            if len(self._signal_history) > self._max_history:
                self._signal_history = self._signal_history[-self._max_history:]
            
            logger.info(
                f"StrategyRouter [{signal.mode_name}]: "
                f"{symbol} → {signal.decision.value} "
                f"(conf={signal.confidence:.2f}, path={signal.routing_path})"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"StrategyRouter error: {e}")
            signal.decision = SignalDecision.HOLD
            signal.confidence = 0.0
            signal.metadata["error"] = str(e)
            return signal
    
    def _route_mode_0(self, signal: RoutedSignal) -> RoutedSignal:
        """
        MODE 0: RULE ONLY
        Signal comes purely from Rule Engine (Gann + Ehlers).
        No ML. No AI. Fully deterministic.
        """
        rule = signal.rule_signal
        
        if not rule:
            signal.decision = SignalDecision.HOLD
            signal.confidence = 0.0
            signal.routing_path = "rule_only(no_data)"
            return signal
        
        # Extract rule direction and confidence
        direction = rule.get("direction", "hold").upper()
        confidence = rule.get("confidence", 0.0)
        
        # Map direction to decision
        if direction in ["BUY", "LONG"] and confidence >= self._rule_confidence_threshold:
            signal.decision = SignalDecision.BUY
            if confidence >= 0.80:
                signal.decision = SignalDecision.STRONG_BUY
        elif direction in ["SELL", "SHORT"] and confidence >= self._rule_confidence_threshold:
            signal.decision = SignalDecision.SELL
            if confidence >= 0.80:
                signal.decision = SignalDecision.STRONG_SELL
        else:
            signal.decision = SignalDecision.HOLD
        
        signal.confidence = confidence
        signal.signal_sources = ["gann_engine", "ehlers_engine"]
        signal.source_weights = {"gann_engine": 0.5, "ehlers_engine": 0.5}
        signal.routing_path = "rule_only"
        
        return signal
    
    def _route_mode_1(self, signal: RoutedSignal) -> RoutedSignal:
        """
        MODE 1: HYBRID (Default)
        Rule generates signal, ML confirms.
        Logic: Rule=BUY AND ML_prob > threshold → BUY
        """
        rule = signal.rule_signal
        ml = signal.ml_signal
        
        if not rule:
            signal.decision = SignalDecision.HOLD
            signal.routing_path = "hybrid(no_rule_data)"
            return signal
        
        rule_direction = rule.get("direction", "hold").upper()
        rule_confidence = rule.get("confidence", 0.0)
        ml_probability = ml.get("probability", 0.5) if ml else 0.5
        
        # Rule must first generate a signal
        if rule_direction in ["BUY", "LONG"] and rule_confidence >= self._rule_confidence_threshold:
            # ML must confirm
            if ml_probability >= self._ml_prob_threshold:
                signal.decision = SignalDecision.BUY
                signal.confidence = (rule_confidence * 0.5 + ml_probability * 0.5)
                signal.routing_path = "hybrid(rule_buy+ml_confirm)"
            else:
                signal.decision = SignalDecision.HOLD
                signal.confidence = rule_confidence * 0.3
                signal.routing_path = "hybrid(rule_buy+ml_reject)"
                signal.metadata["ml_rejection"] = f"ML prob {ml_probability:.2f} < threshold {self._ml_prob_threshold}"
        
        elif rule_direction in ["SELL", "SHORT"] and rule_confidence >= self._rule_confidence_threshold:
            # For sell, ML probability should be below (1 - threshold)
            if (1 - ml_probability) >= self._ml_prob_threshold:
                signal.decision = SignalDecision.SELL
                signal.confidence = (rule_confidence * 0.5 + (1 - ml_probability) * 0.5)
                signal.routing_path = "hybrid(rule_sell+ml_confirm)"
            else:
                signal.decision = SignalDecision.HOLD
                signal.confidence = rule_confidence * 0.3
                signal.routing_path = "hybrid(rule_sell+ml_reject)"
        else:
            signal.decision = SignalDecision.HOLD
            signal.confidence = 0.0
            signal.routing_path = "hybrid(no_rule_signal)"
        
        signal.signal_sources = ["gann_engine", "ehlers_engine", "ml_engine"]
        signal.source_weights = {"gann_engine": 0.3, "ehlers_engine": 0.2, "ml_engine": 0.5}
        
        return signal
    
    def _route_mode_2(self, signal: RoutedSignal) -> RoutedSignal:
        """
        MODE 2: ML DOMINANT
        ML generates primary signal, Rule acts as structural filter.
        ML signal blocked if it violates major Gann/Ehlers structural levels.
        """
        rule = signal.rule_signal
        ml = signal.ml_signal
        
        if not ml:
            # Fallback to rule if no ML
            signal.routing_path = "ml_dominant(fallback_to_rule)"
            return self._route_mode_0(signal)
        
        ml_probability = ml.get("probability", 0.5)
        rule_direction = rule.get("direction", "neutral").upper() if rule else "NEUTRAL"
        rule_confidence = rule.get("confidence", 0.0) if rule else 0.0
        
        # ML determines direction
        if ml_probability >= self._ml_dominant_threshold:
            ml_direction = "BUY"
        elif (1 - ml_probability) >= self._ml_dominant_threshold:
            ml_direction = "SELL"
        else:
            ml_direction = "HOLD"
        
        if ml_direction == "HOLD":
            signal.decision = SignalDecision.HOLD
            signal.confidence = 0.0
            signal.routing_path = "ml_dominant(ml_neutral)"
            return signal
        
        # Rule structural filter
        structural_violation = False
        
        if rule_direction != "NEUTRAL" and rule_direction != "HOLD":
            # Check if ML contradicts rule
            if (ml_direction == "BUY" and rule_direction in ["SELL", "SHORT"]):
                # ML wants to buy but rule says sell - check confidence
                if rule_confidence >= 0.70:
                    structural_violation = True
                    signal.metadata["structural_block"] = "ML buy blocked by strong rule sell signal"
            elif (ml_direction == "SELL" and rule_direction in ["BUY", "LONG"]):
                if rule_confidence >= 0.70:
                    structural_violation = True
                    signal.metadata["structural_block"] = "ML sell blocked by strong rule buy signal"
        
        if structural_violation:
            signal.decision = SignalDecision.HOLD
            signal.confidence = ml_probability * 0.3
            signal.routing_path = "ml_dominant(structural_filter_blocked)"
        else:
            signal.decision = SignalDecision.BUY if ml_direction == "BUY" else SignalDecision.SELL
            signal.confidence = ml_probability
            signal.routing_path = "ml_dominant(ml_signal_passed_filter)"
        
        signal.signal_sources = ["ml_engine", "gann_engine", "ehlers_engine"]
        signal.source_weights = {"ml_engine": 0.7, "gann_engine": 0.2, "ehlers_engine": 0.1}
        
        return signal
    
    def _route_mode_3(self, signal: RoutedSignal) -> RoutedSignal:
        """
        MODE 3: AI ASSISTED
        Uses hybrid signal (Mode 1) but AI can adjust parameters.
        AI adjustments come through ai_output.
        AI CANNOT modify orders, only parameters.
        """
        # Start with hybrid routing
        signal = self._route_mode_1(signal)
        signal.routing_path = f"ai_assisted({signal.routing_path})"
        
        # Apply AI parameter adjustments (if any)
        ai = signal.ai_signal
        if ai and ai.get("parameter_adjustments"):
            adjustments = ai["parameter_adjustments"]
            
            # AI can adjust thresholds within bounds
            if "ml_probability_threshold" in adjustments:
                adjusted = adjustments["ml_probability_threshold"]
                # Bound check (max 30% deviation)
                default = 0.60
                if abs(adjusted - default) / default <= 0.30:
                    self._ml_prob_threshold = adjusted
                    signal.metadata["ai_adjusted_ml_threshold"] = adjusted
            
            if "confidence_threshold" in adjustments:
                adjusted = adjustments["confidence_threshold"]
                default = 0.55
                if abs(adjusted - default) / default <= 0.30:
                    self._rule_confidence_threshold = adjusted
                    signal.metadata["ai_adjusted_confidence"] = adjusted
            
            signal.metadata["ai_adjustments_applied"] = True
        
        signal.signal_sources.append("ai_agents")
        signal.source_weights["ai_agents"] = 0.1
        
        return signal
    
    def _route_mode_4(self, signal: RoutedSignal) -> RoutedSignal:
        """
        MODE 4: GUARDED AUTONOMOUS
        Uses hybrid signal by default.
        AI can also propose trades (handled by autonomous agent).
        AI proposals must pass validation gate before being considered.
        """
        # Start with hybrid routing
        signal = self._route_mode_1(signal)
        
        # Check if AI has an approved proposal
        ai = signal.ai_signal
        if ai and ai.get("approved_proposal"):
            proposal = ai["approved_proposal"]
            
            # Only use proposal if it passed validation gate
            if proposal.get("status") == "approved":
                direction = proposal.get("direction", "").upper()
                
                if direction in ["BUY", "LONG"]:
                    signal.decision = SignalDecision.BUY
                elif direction in ["SELL", "SHORT"]:
                    signal.decision = SignalDecision.SELL
                
                signal.confidence = max(signal.confidence, proposal.get("confidence", 0))
                signal.entry_price = proposal.get("entry_price", signal.entry_price)
                signal.stop_loss = proposal.get("stop_loss", signal.stop_loss)
                signal.take_profit = proposal.get("take_profit", signal.take_profit)
                signal.routing_path = f"guarded_autonomous(ai_approved_proposal)"
                signal.metadata["ai_proposal_id"] = proposal.get("proposal_id")
        else:
            signal.routing_path = f"guarded_autonomous({signal.routing_path})"
        
        signal.signal_sources.append("ai_autonomous")
        signal.source_weights["ai_autonomous"] = 0.2
        
        return signal
    
    def set_mode(self, mode: int):
        """Set the routing mode (convenience method for orchestrator integration)."""
        self.current_mode = mode
    
    def update_thresholds(self, thresholds: Dict) -> Dict:
        """Update router thresholds (called by Optimizer Agent in Mode 3+)."""
        updated = {}
        
        if "ml_probability_threshold" in thresholds:
            self._ml_prob_threshold = thresholds["ml_probability_threshold"]
            updated["ml_probability_threshold"] = self._ml_prob_threshold
        
        if "confidence_threshold" in thresholds:
            self._rule_confidence_threshold = thresholds["confidence_threshold"]
            updated["confidence_threshold"] = self._rule_confidence_threshold
        
        if "ml_dominant_threshold" in thresholds:
            self._ml_dominant_threshold = thresholds["ml_dominant_threshold"]
            updated["ml_dominant_threshold"] = self._ml_dominant_threshold
        
        logger.info(f"StrategyRouter thresholds updated: {updated}")
        return {"success": True, "updated": updated}
    
    def get_signal_history(self, limit: int = 50) -> List[Dict]:
        """Get recent signal history."""
        return [s.to_dict() for s in self._signal_history[-limit:]]
    
    def get_routing_stats(self) -> Dict:
        """Get routing statistics."""
        total = len(self._signal_history)
        if total == 0:
            return {"total_signals": 0}
        
        decisions = [s.decision.value for s in self._signal_history]
        
        return {
            "total_signals": total,
            "current_mode": self._current_mode,
            "mode_name": self.MODE_NAMES.get(self._current_mode, "UNKNOWN"),
            "decision_distribution": {
                "BUY": decisions.count("BUY"),
                "SELL": decisions.count("SELL"),
                "HOLD": decisions.count("HOLD"),
                "STRONG_BUY": decisions.count("STRONG_BUY"),
                "STRONG_SELL": decisions.count("STRONG_SELL"),
            },
            "avg_confidence": float(np.mean([s.confidence for s in self._signal_history])),
            "thresholds": {
                "ml_probability": self._ml_prob_threshold,
                "rule_confidence": self._rule_confidence_threshold,
                "ml_dominant": self._ml_dominant_threshold,
            },
        }
    
    def _load_mode(self) -> int:
        """Load current mode from config file."""
        try:
            config_path = os.path.join("config", "global_mode.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    cfg = yaml.safe_load(f)
                    return cfg.get("global_mode", {}).get("current_mode", 1)
        except Exception as e:
            logger.warning(f"Could not load mode: {e}")
        return 1
