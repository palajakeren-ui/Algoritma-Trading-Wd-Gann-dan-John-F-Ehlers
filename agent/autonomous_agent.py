"""
Guarded Autonomous Agent - AI Trade Proposals with Validation Gate
Part of OpenClaw-style AI Agent Orchestration Layer.

Capabilities:
- Propose trades based on multi-engine analysis
- ALL proposals must pass validation gate:
  1. RiskEngine validation
  2. Exposure cap check
  3. Drawdown limit check
  4. Confidence threshold check
  5. Rule alignment check
  6. Cooldown check

CRITICAL CONSTRAINTS:
- NO direct broker access
- NO direct order execution
- ALL trades go through validation gate
- Rate limited to max_proposals_per_hour
"""

import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid


class ProposalStatus(str, Enum):
    PENDING = "pending"
    GATE_PASSED = "gate_passed"
    GATE_FAILED = "gate_failed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
    THROTTLED = "throttled"


@dataclass
class TradeProposal:
    """AI-generated trade proposal."""
    proposal_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None
    
    # Trade details
    symbol: str = ""
    direction: str = ""  # "buy" or "sell"
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    position_size_percent: float = 0.0
    
    # Analysis basis
    rule_signal: Dict = field(default_factory=dict)
    ml_prediction: Dict = field(default_factory=dict)
    ai_reasoning: str = ""
    
    # Confidence
    overall_confidence: float = 0.0
    rule_confidence: float = 0.0
    ml_confidence: float = 0.0
    
    # Validation gate results
    status: ProposalStatus = ProposalStatus.PENDING
    gate_results: Dict = field(default_factory=dict)
    
    # Final decision
    approved_by: str = ""
    rejection_reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size_percent": self.position_size_percent,
            "overall_confidence": self.overall_confidence,
            "rule_confidence": self.rule_confidence,
            "ml_confidence": self.ml_confidence,
            "ai_reasoning": self.ai_reasoning,
            "status": self.status.value,
            "gate_results": self.gate_results,
            "approved_by": self.approved_by,
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class GateCheckResult:
    """Result of a single validation gate check."""
    gate_name: str = ""
    passed: bool = False
    value: float = 0.0
    threshold: float = 0.0
    message: str = ""


class GuardedAutonomousAgent:
    """
    Guarded Autonomous Agent - Proposes trades with mandatory validation.
    
    This agent can analyze market conditions using all available engines
    and propose trades, but EVERY proposal must pass the validation gate
    system before it can be executed.
    
    The agent NEVER has direct broker access.
    The agent NEVER executes trades directly.
    
    Validation Gate Pipeline:
    1. Risk Engine validation (position sizing, exposure)
    2. Exposure cap check (total portfolio exposure)
    3. Drawdown limit check (current drawdown vs limit)
    4. Confidence threshold (minimum 75%)
    5. Rule alignment check (must not contradict major rules)
    6. Cooldown check (minimum interval between proposals)
    """
    
    AGENT_ID = "autonomous-agent"
    AGENT_NAME = "Guarded Autonomous Agent"
    AGENT_VERSION = "1.0.0"
    
    # Gate thresholds
    MIN_CONFIDENCE = 0.75
    MAX_EXPOSURE = 0.25  # 25% max total exposure
    MAX_DRAWDOWN = 0.15  # 15% max drawdown
    MIN_RULE_AGREEMENT = 0.50  # 50% rule sources must agree
    MIN_COOLDOWN_MINUTES = 5  # Min 5 mins between proposals
    MAX_PROPOSALS_PER_HOUR = 10
    PROPOSAL_TIMEOUT_MINUTES = 15
    
    def __init__(self, config: Dict = None, risk_engine=None):
        self.config = config or {}
        self.risk_engine = risk_engine
        self.status = "idle"
        self.health = 100
        self.tasks_completed = 0
        self.current_task = None
        
        # Proposal tracking
        self.pending_proposals: List[TradeProposal] = []
        self.proposal_history: List[TradeProposal] = []
        self._max_history = 500
        
        # Rate limiting
        self._proposals_this_hour = 0
        self._last_proposal_time = datetime.min
        self._hour_start = datetime.now()
        
        # Gate configuration (from config)
        gate_cfg = config.get("validation_gate", {}) if config else {}
        self.MIN_CONFIDENCE = gate_cfg.get("min_confidence", 0.75)
        self.MAX_EXPOSURE = gate_cfg.get("max_total_exposure", 0.25)
        self.MAX_DRAWDOWN = gate_cfg.get("max_drawdown", 0.15)
        
        # Flag: is this agent enabled?
        self.enabled = False  # Must be explicitly enabled (Mode 4 only)
        
        logger.info(f"GuardedAutonomousAgent v{self.AGENT_VERSION} initialized (enabled={self.enabled})")
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.AGENT_ID,
            "name": self.AGENT_NAME,
            "version": self.AGENT_VERSION,
            "status": self.status,
            "health": self.health,
            "tasks_completed": self.tasks_completed,
            "current_task": self.current_task,
            "enabled": self.enabled,
            "pending_proposals": len(self.pending_proposals),
            "proposals_this_hour": self._proposals_this_hour,
            "max_proposals_per_hour": self.MAX_PROPOSALS_PER_HOUR,
        }
    
    def enable(self):
        """Enable the autonomous agent (should only be called in Mode 4)."""
        self.enabled = True
        logger.warning("GuardedAutonomousAgent ENABLED - Mode 4 active")
    
    def disable(self):
        """Disable the autonomous agent."""
        self.enabled = False
        logger.info("GuardedAutonomousAgent DISABLED")
    
    def propose_trade(
        self,
        symbol: str,
        rule_signal: Dict,
        ml_prediction: Dict,
        market_context: Dict = None,
        risk_state: Dict = None,
    ) -> TradeProposal:
        """
        Generate a trade proposal based on multi-engine analysis.
        
        The proposal will automatically go through the validation gate.
        
        Args:
            symbol: Trading symbol
            rule_signal: Rule engine signal output
            ml_prediction: ML model prediction
            market_context: Additional market context
            risk_state: Current risk engine state
            
        Returns:
            TradeProposal with validation gate results
        """
        if not self.enabled:
            proposal = TradeProposal(
                symbol=symbol,
                status=ProposalStatus.REJECTED,
                rejection_reason="Autonomous agent is not enabled (requires Mode 4)",
            )
            return proposal
        
        self.status = "proposing"
        self.current_task = f"Proposing trade: {symbol}"
        
        try:
            # Rate limiting
            if not self._check_rate_limit():
                proposal = TradeProposal(
                    symbol=symbol,
                    status=ProposalStatus.THROTTLED,
                    rejection_reason=f"Rate limit exceeded ({self.MAX_PROPOSALS_PER_HOUR}/hour)",
                )
                return proposal
            
            # Build proposal
            proposal = self._build_proposal(symbol, rule_signal, ml_prediction, market_context)
            
            # Run through validation gate
            proposal = self._run_validation_gate(proposal, risk_state)
            
            # Store proposal
            self._store_proposal(proposal)
            
            self.tasks_completed += 1
            self._proposals_this_hour += 1
            self._last_proposal_time = datetime.now()
            
            logger.info(
                f"GuardedAutonomousAgent: Proposal {proposal.proposal_id} "
                f"for {symbol} - Status: {proposal.status.value}"
            )
            
            return proposal
            
        except Exception as e:
            logger.error(f"GuardedAutonomousAgent proposal error: {e}")
            return TradeProposal(
                symbol=symbol,
                status=ProposalStatus.GATE_FAILED,
                rejection_reason=f"Error during proposal: {str(e)}",
            )
        finally:
            self.status = "idle"
            self.current_task = None
    
    def approve_proposal(self, proposal_id: str, approved_by: str = "human") -> Dict:
        """
        Approve a pending proposal for execution.
        
        Only proposals that passed the validation gate can be approved.
        """
        proposal = self._find_proposal(proposal_id)
        
        if not proposal:
            return {"success": False, "error": f"Proposal {proposal_id} not found"}
        
        if proposal.status != ProposalStatus.GATE_PASSED:
            return {
                "success": False,
                "error": f"Proposal status is {proposal.status.value}, not gate_passed",
            }
        
        # Check if expired
        if proposal.expires_at and datetime.now() > proposal.expires_at:
            proposal.status = ProposalStatus.EXPIRED
            return {"success": False, "error": "Proposal has expired"}
        
        proposal.status = ProposalStatus.APPROVED
        proposal.approved_by = approved_by
        
        logger.info(f"Proposal {proposal_id} approved by {approved_by}")
        
        return {
            "success": True,
            "proposal": proposal.to_dict(),
            "message": "Proposal approved. Ready for execution layer.",
        }
    
    def reject_proposal(self, proposal_id: str, reason: str = "") -> Dict:
        """Reject a pending proposal."""
        proposal = self._find_proposal(proposal_id)
        
        if not proposal:
            return {"success": False, "error": f"Proposal {proposal_id} not found"}
        
        proposal.status = ProposalStatus.REJECTED
        proposal.rejection_reason = reason or "Manually rejected"
        
        return {"success": True, "message": f"Proposal {proposal_id} rejected"}
    
    def get_pending_proposals(self) -> List[Dict]:
        """Get all pending proposals."""
        self._cleanup_expired()
        return [
            p.to_dict() for p in self.pending_proposals
            if p.status in [ProposalStatus.PENDING, ProposalStatus.GATE_PASSED]
        ]
    
    def get_proposal_history(self, limit: int = 50) -> List[Dict]:
        return [p.to_dict() for p in self.proposal_history[-limit:]]
    
    # ===== Private Methods =====
    
    def _build_proposal(
        self,
        symbol: str,
        rule_signal: Dict,
        ml_prediction: Dict,
        context: Dict = None,
    ) -> TradeProposal:
        """Build a trade proposal from analysis outputs."""
        proposal = TradeProposal(
            proposal_id=f"auto-{uuid.uuid4().hex[:8]}",
            expires_at=datetime.now() + timedelta(minutes=self.PROPOSAL_TIMEOUT_MINUTES),
            symbol=symbol,
            rule_signal=rule_signal,
            ml_prediction=ml_prediction,
        )
        
        # Determine direction
        rule_dir = rule_signal.get("direction", "hold")
        ml_prob = ml_prediction.get("probability", 0.5)
        
        if rule_dir in ["buy", "long", "BUY"] and ml_prob > 0.5:
            proposal.direction = "buy"
        elif rule_dir in ["sell", "short", "SELL"] and ml_prob < 0.5:
            proposal.direction = "sell"
        else:
            proposal.direction = "hold"
        
        # Set prices
        proposal.entry_price = rule_signal.get("entry_price", 0)
        proposal.stop_loss = rule_signal.get("stop_loss", 0)
        proposal.take_profit = rule_signal.get("take_profit", 0)
        
        # Calculate confidence
        proposal.rule_confidence = rule_signal.get("confidence", 0.5)
        proposal.ml_confidence = abs(ml_prob - 0.5) * 2  # Convert to 0-1 scale
        proposal.overall_confidence = (
            proposal.rule_confidence * 0.4 + proposal.ml_confidence * 0.6
        )
        
        # Position sizing recommendation (conservative)
        proposal.position_size_percent = min(0.02, proposal.overall_confidence * 0.03)
        
        # AI reasoning
        proposal.ai_reasoning = self._generate_reasoning(proposal, context)
        
        return proposal
    
    def _run_validation_gate(
        self, proposal: TradeProposal, risk_state: Dict = None
    ) -> TradeProposal:
        """
        Run proposal through the complete validation gate pipeline.
        ALL gates must pass for the proposal to proceed.
        """
        risk_state = risk_state or {}
        gate_results = {}
        all_passed = True
        
        # Gate 1: Risk Engine Validation
        gate1 = self._gate_risk_engine(proposal, risk_state)
        gate_results["risk_engine"] = gate1.__dict__
        if not gate1.passed:
            all_passed = False
        
        # Gate 2: Exposure Cap
        gate2 = self._gate_exposure_cap(risk_state)
        gate_results["exposure_cap"] = gate2.__dict__
        if not gate2.passed:
            all_passed = False
        
        # Gate 3: Drawdown Limit
        gate3 = self._gate_drawdown_limit(risk_state)
        gate_results["drawdown_limit"] = gate3.__dict__
        if not gate3.passed:
            all_passed = False
        
        # Gate 4: Confidence Threshold
        gate4 = self._gate_confidence(proposal)
        gate_results["confidence"] = gate4.__dict__
        if not gate4.passed:
            all_passed = False
        
        # Gate 5: Rule Alignment
        gate5 = self._gate_rule_alignment(proposal)
        gate_results["rule_alignment"] = gate5.__dict__
        if not gate5.passed:
            all_passed = False
        
        # Gate 6: Cooldown
        gate6 = self._gate_cooldown()
        gate_results["cooldown"] = gate6.__dict__
        if not gate6.passed:
            all_passed = False
        
        proposal.gate_results = gate_results
        
        if all_passed:
            proposal.status = ProposalStatus.GATE_PASSED
        else:
            proposal.status = ProposalStatus.GATE_FAILED
            failed_gates = [k for k, v in gate_results.items() if not v.get("passed", False)]
            proposal.rejection_reason = f"Failed gates: {', '.join(failed_gates)}"
        
        return proposal
    
    def _gate_risk_engine(self, proposal: TradeProposal, risk_state: Dict) -> GateCheckResult:
        """Gate 1: Risk Engine validation."""
        result = GateCheckResult(gate_name="risk_engine_validation")
        
        # Check with risk engine if available
        if self.risk_engine:
            try:
                risk_check = self.risk_engine.check_trade_risk(
                    symbol=proposal.symbol,
                    side=proposal.direction,
                    order_type="market",
                    quantity=proposal.position_size_percent,
                    price=proposal.entry_price,
                    stop_loss=proposal.stop_loss,
                )
                result.passed = risk_check.passed
                result.message = "; ".join(risk_check.messages) if hasattr(risk_check, 'messages') else "Risk check done"
            except Exception as e:
                result.passed = False
                result.message = f"Risk engine error: {str(e)}"
        else:
            # Without risk engine, use basic self-validation
            result.passed = (
                proposal.entry_price > 0
                and proposal.stop_loss > 0
                and proposal.direction in ["buy", "sell"]
            )
            result.message = "Basic self-validation (no risk engine connected)"
        
        return result
    
    def _gate_exposure_cap(self, risk_state: Dict) -> GateCheckResult:
        """Gate 2: Check total exposure against cap."""
        result = GateCheckResult(
            gate_name="exposure_cap_check",
            threshold=self.MAX_EXPOSURE,
        )
        
        current_exposure = risk_state.get("total_exposure", 0)
        result.value = current_exposure
        result.passed = current_exposure < self.MAX_EXPOSURE
        result.message = (
            f"Exposure: {current_exposure:.2%} / {self.MAX_EXPOSURE:.2%} "
            f"({'OK' if result.passed else 'EXCEEDED'})"
        )
        
        return result
    
    def _gate_drawdown_limit(self, risk_state: Dict) -> GateCheckResult:
        """Gate 3: Check current drawdown against limit."""
        result = GateCheckResult(
            gate_name="drawdown_limit_check",
            threshold=self.MAX_DRAWDOWN,
        )
        
        current_dd = abs(risk_state.get("current_drawdown", 0))
        result.value = current_dd
        result.passed = current_dd < self.MAX_DRAWDOWN
        result.message = (
            f"Drawdown: {current_dd:.2%} / {self.MAX_DRAWDOWN:.2%} "
            f"({'OK' if result.passed else 'LIMIT BREACHED'})"
        )
        
        return result
    
    def _gate_confidence(self, proposal: TradeProposal) -> GateCheckResult:
        """Gate 4: Check overall confidence threshold."""
        result = GateCheckResult(
            gate_name="confidence_threshold",
            threshold=self.MIN_CONFIDENCE,
            value=proposal.overall_confidence,
        )
        
        result.passed = proposal.overall_confidence >= self.MIN_CONFIDENCE
        result.message = (
            f"Confidence: {proposal.overall_confidence:.2%} / {self.MIN_CONFIDENCE:.2%} "
            f"({'OK' if result.passed else 'TOO LOW'})"
        )
        
        return result
    
    def _gate_rule_alignment(self, proposal: TradeProposal) -> GateCheckResult:
        """Gate 5: Check alignment with rule engine signals."""
        result = GateCheckResult(
            gate_name="rule_alignment_check",
            threshold=self.MIN_RULE_AGREEMENT,
        )
        
        rule_dir = proposal.rule_signal.get("direction", "hold")
        
        if proposal.direction == "hold":
            result.passed = True
            result.value = 1.0
            result.message = "No trade direction - skip alignment check"
        elif rule_dir == proposal.direction or rule_dir in [proposal.direction.upper()]:
            result.passed = True
            result.value = 1.0
            result.message = "Trade aligned with rule engine"
        elif rule_dir == "hold" or rule_dir == "neutral":
            result.passed = True
            result.value = 0.5
            result.message = "Rule engine neutral - no contradiction"
        else:
            result.passed = False
            result.value = 0.0
            result.message = f"Trade contradicts rule engine (AI={proposal.direction}, Rule={rule_dir})"
        
        return result
    
    def _gate_cooldown(self) -> GateCheckResult:
        """Gate 6: Check minimum cooldown between proposals."""
        result = GateCheckResult(
            gate_name="cooldown_check",
            threshold=self.MIN_COOLDOWN_MINUTES,
        )
        
        elapsed = (datetime.now() - self._last_proposal_time).total_seconds() / 60
        result.value = elapsed
        result.passed = elapsed >= self.MIN_COOLDOWN_MINUTES
        result.message = (
            f"Time since last proposal: {elapsed:.1f}min / {self.MIN_COOLDOWN_MINUTES}min "
            f"({'OK' if result.passed else 'COOLDOWN ACTIVE'})"
        )
        
        return result
    
    def _generate_reasoning(self, proposal: TradeProposal, context: Dict = None) -> str:
        """Generate human-readable reasoning for the trade proposal."""
        parts = [
            f"AI Trade Proposal: {proposal.direction.upper()} {proposal.symbol}",
            f"Confidence: {proposal.overall_confidence:.0%} "
            f"(Rule: {proposal.rule_confidence:.0%}, ML: {proposal.ml_confidence:.0%})",
        ]
        
        if proposal.entry_price:
            parts.append(f"Entry: ${proposal.entry_price:,.2f}")
        if proposal.stop_loss:
            parts.append(f"Stop Loss: ${proposal.stop_loss:,.2f}")
        if proposal.take_profit:
            parts.append(f"Take Profit: ${proposal.take_profit:,.2f}")
        
        if proposal.rule_signal.get("gann_support"):
            parts.append("✅ Gann support level nearby")
        if proposal.rule_signal.get("ehlers_confirm"):
            parts.append("✅ Ehlers cycle confirmation")
        
        return "\n".join(parts)
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        # Reset hourly counter
        if (datetime.now() - self._hour_start).total_seconds() > 3600:
            self._proposals_this_hour = 0
            self._hour_start = datetime.now()
        
        return self._proposals_this_hour < self.MAX_PROPOSALS_PER_HOUR
    
    def _find_proposal(self, proposal_id: str) -> Optional[TradeProposal]:
        """Find a proposal by ID."""
        for p in self.pending_proposals:
            if p.proposal_id == proposal_id:
                return p
        for p in self.proposal_history:
            if p.proposal_id == proposal_id:
                return p
        return None
    
    def _store_proposal(self, proposal: TradeProposal):
        """Store proposal in appropriate list."""
        if proposal.status in [ProposalStatus.PENDING, ProposalStatus.GATE_PASSED]:
            self.pending_proposals.append(proposal)
        
        self.proposal_history.append(proposal)
        if len(self.proposal_history) > self._max_history:
            self.proposal_history = self.proposal_history[-self._max_history:]
    
    def _cleanup_expired(self):
        """Clean up expired proposals."""
        now = datetime.now()
        for p in self.pending_proposals:
            if p.expires_at and now > p.expires_at:
                p.status = ProposalStatus.EXPIRED
        
        self.pending_proposals = [
            p for p in self.pending_proposals
            if p.status in [ProposalStatus.PENDING, ProposalStatus.GATE_PASSED]
        ]
