"""
AI Agent Orchestrator - Central coordination for all AI agents
OpenClaw-style multi-agent system for institutional trading.

This orchestrator:
1. Manages lifecycle of all 4 agents
2. Routes tasks to appropriate agents
3. Enforces mode-based agent permissions
4. Provides unified API for agent interactions
5. Handles agent health monitoring
6. Manages mode transitions

CRITICAL: The orchestrator enforces that no agent bypasses risk controls.
"""

from loguru import logger
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import os
import yaml

from agent.analyst_agent import AnalystAgent
from agent.regime_agent import RegimeAgent
from agent.optimizer_agent import OptimizerAgent
from agent.autonomous_agent import GuardedAutonomousAgent


class AgentRole(str, Enum):
    ANALYST = "analyst"
    REGIME = "regime"
    OPTIMIZER = "optimizer"
    AUTONOMOUS = "autonomous"


# Which agents are active per mode
MODE_AGENT_MAP = {
    0: [],                                              # MODE 0: No agents
    1: [],                                              # MODE 1: No agents (ML only)
    2: [],                                              # MODE 2: No agents (ML dominant)
    3: [AgentRole.ANALYST, AgentRole.REGIME, AgentRole.OPTIMIZER],  # MODE 3: Advisory agents
    4: [AgentRole.ANALYST, AgentRole.REGIME, AgentRole.OPTIMIZER, AgentRole.AUTONOMOUS],  # MODE 4: All agents
}


@dataclass
class AgentEvent:
    """Event logged by the orchestrator."""
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = ""
    agent_id: str = ""
    details: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "details": self.details,
        }


class AgentOrchestrator:
    """
    Central orchestrator for the AI Agent system.
    
    Architecture:
    ┌──────────────────────┐
    │   Agent Orchestrator │
    │                      │
    │  ┌─────────────────┐ │
    │  │  Analyst Agent   │ │  ← Read-only analysis
    │  ├─────────────────┤ │
    │  │  Regime Agent    │ │  ← Regime detection + mode control
    │  ├─────────────────┤ │
    │  │  Optimizer Agent │ │  ← Parameter tuning
    │  ├─────────────────┤ │
    │  │  Autonomous Agent│ │  ← Guarded trade proposals
    │  └─────────────────┘ │
    │                      │
    │  Mode Controller     │  ← Enforces permissions per mode
    │  Health Monitor      │  ← Watches agent health
    │  Event Logger        │  ← Audit trail
    └──────────────────────┘
    """
    
    def __init__(self, config: Dict = None, risk_engine=None):
        self.config = config or {}
        self.risk_engine = risk_engine
        
        # Current global mode
        self._current_mode = self._load_mode()
        
        # Initialize agents
        self.analyst = AnalystAgent(config=config)
        self.regime = RegimeAgent(
            config=config, 
            config_path=os.path.join("config", "global_mode.yaml")
        )
        self.optimizer = OptimizerAgent(config=config)
        self.autonomous = GuardedAutonomousAgent(
            config=config, 
            risk_engine=risk_engine
        )
        
        # Agent registry
        self.agents = {
            AgentRole.ANALYST: self.analyst,
            AgentRole.REGIME: self.regime,
            AgentRole.OPTIMIZER: self.optimizer,
            AgentRole.AUTONOMOUS: self.autonomous,
        }
        
        # Event log
        self.events: List[AgentEvent] = []
        self._max_events = 1000
        
        # Health monitoring
        self._monitor_thread = None
        self._monitoring = False
        self._health_check_interval = 30  # seconds
        
        # Apply initial mode permissions
        self._apply_mode_permissions()
        
        logger.info(f"AgentOrchestrator initialized (mode={self._current_mode})")
    
    @property
    def current_mode(self) -> int:
        return self._current_mode
    
    def get_status(self) -> Dict:
        """Get comprehensive orchestrator status."""
        return {
            "current_mode": self._current_mode,
            "mode_name": self._get_mode_name(),
            "active_agents": self._get_active_agent_ids(),
            "agents": {
                role.value: agent.get_status()
                for role, agent in self.agents.items()
            },
            "total_events": len(self.events),
            "monitoring_active": self._monitoring,
            "timestamp": datetime.now().isoformat(),
        }
    
    def switch_mode(self, target_mode: int, reason: str = "", force: bool = False) -> Dict:
        """
        Switch the global trading mode.
        
        Delegates to RegimeAgent for the actual switch,
        then updates agent permissions accordingly.
        """
        result = self.regime.switch_mode(
            target_mode=target_mode,
            reason=reason,
            force=force,
        )
        
        if result.get("success"):
            self._current_mode = target_mode
            self._apply_mode_permissions()
            
            self._log_event("mode_switch", "orchestrator", {
                "from_mode": result.get("previous_mode"),
                "to_mode": target_mode,
                "reason": reason,
            })
        
        return result
    
    def force_safe_mode(self, reason: str = "Emergency") -> Dict:
        """Force switch to Mode 0 (RULE ONLY) - emergency."""
        result = self.regime.force_revert_to_safe_mode(reason)
        
        if result.get("success"):
            self._current_mode = 0
            self._apply_mode_permissions()
            
            self._log_event("emergency_revert", "orchestrator", {
                "reason": reason,
                "previous_mode": result.get("previous_mode"),
            })
        
        return result
    
    def analyze_market(
        self,
        symbol: str,
        price_data=None,
        gann_levels: Dict = None,
        ehlers_indicators: Dict = None,
        ml_predictions: Dict = None,
    ) -> Dict:
        """
        Request market analysis from the Analyst Agent.
        Available in Modes 3 and 4.
        """
        if not self._is_agent_active(AgentRole.ANALYST):
            return {"error": f"Analyst agent not active in Mode {self._current_mode}"}
        
        report = self.analyst.summarize_market(
            symbol=symbol,
            price_data=price_data,
            gann_levels=gann_levels,
            ehlers_indicators=ehlers_indicators,
            ml_predictions=ml_predictions,
            regime=self.regime.current_regime.value,
        )
        
        self._log_event("market_analysis", self.analyst.AGENT_ID, {
            "symbol": symbol,
            "confidence": report.confidence,
        })
        
        return report.to_dict()
    
    def explain_trade(self, signal: Dict, components: Dict = None) -> Dict:
        """Request trade explanation from the Analyst Agent."""
        if not self._is_agent_active(AgentRole.ANALYST):
            return {"error": f"Analyst agent not active in Mode {self._current_mode}"}
        
        report = self.analyst.explain_trade(
            signal=signal,
            rule_components=components,
        )
        
        return report.to_dict()
    
    def detect_regime(self, price_data, volume_data=None, ehlers_data=None) -> Dict:
        """
        Run regime detection and optionally auto-switch mode.
        Available in Modes 3 and 4.
        """
        if not self._is_agent_active(AgentRole.REGIME):
            return {"error": f"Regime agent not active in Mode {self._current_mode}"}
        
        detection = self.regime.detect_regime(
            price_data=price_data,
            volume_data=volume_data,
            ehlers_data=ehlers_data,
        )
        
        # Auto-switch if recommended
        switch_result = self.regime.auto_switch_on_regime(detection)
        if switch_result and switch_result.get("success"):
            self._current_mode = switch_result["new_mode"]
            self._apply_mode_permissions()
        
        self._log_event("regime_detection", self.regime.AGENT_ID, {
            "regime": detection.regime.value,
            "confidence": detection.confidence,
            "recommended_mode": detection.recommended_mode,
            "auto_switched": switch_result is not None and switch_result.get("success", False),
        })
        
        return detection.to_dict()
    
    def optimize_parameters(
        self,
        price_data=None,
        params: List[str] = None,
    ) -> Dict:
        """
        Run parameter optimization.
        Available in Modes 3 and 4.
        """
        if not self._is_agent_active(AgentRole.OPTIMIZER):
            return {"error": f"Optimizer agent not active in Mode {self._current_mode}"}
        
        proposal = self.optimizer.propose_config_changes(
            price_data=price_data,
            params_to_optimize=params,
        )
        
        self._log_event("optimization", self.optimizer.AGENT_ID, {
            "changes_proposed": len(proposal.changes),
        })
        
        return proposal.to_dict()
    
    def propose_trade(
        self,
        symbol: str,
        rule_signal: Dict,
        ml_prediction: Dict,
        risk_state: Dict = None,
        market_context: Dict = None,
    ) -> Dict:
        """
        Request a trade proposal from the Autonomous Agent.
        Only available in Mode 4.
        """
        if not self._is_agent_active(AgentRole.AUTONOMOUS):
            return {
                "error": f"Autonomous agent not active in Mode {self._current_mode}. "
                         f"Requires Mode 4 (Guarded Autonomous)."
            }
        
        proposal = self.autonomous.propose_trade(
            symbol=symbol,
            rule_signal=rule_signal,
            ml_prediction=ml_prediction,
            market_context=market_context,
            risk_state=risk_state,
        )
        
        self._log_event("trade_proposal", self.autonomous.AGENT_ID, {
            "symbol": symbol,
            "direction": proposal.direction,
            "confidence": proposal.overall_confidence,
            "status": proposal.status.value,
        })
        
        return proposal.to_dict()
    
    def approve_trade_proposal(self, proposal_id: str) -> Dict:
        """Approve a pending trade proposal (human approval)."""
        if not self._is_agent_active(AgentRole.AUTONOMOUS):
            return {"error": "Autonomous agent not active"}
        
        result = self.autonomous.approve_proposal(proposal_id, approved_by="human")
        
        self._log_event("proposal_approved", "human", {
            "proposal_id": proposal_id,
        })
        
        return result
    
    def reject_trade_proposal(self, proposal_id: str, reason: str = "") -> Dict:
        """Reject a pending trade proposal."""
        if not self._is_agent_active(AgentRole.AUTONOMOUS):
            return {"error": "Autonomous agent not active"}
        
        return self.autonomous.reject_proposal(proposal_id, reason)
    
    def answer_query(self, query: str, context: Dict = None) -> Dict:
        """Answer a natural language query via Analyst Agent."""
        if not self._is_agent_active(AgentRole.ANALYST):
            return {"error": f"Analyst agent not active in Mode {self._current_mode}"}
        
        report = self.analyst.answer_query(query, context)
        return report.to_dict()
    
    def start_monitoring(self):
        """Start background health monitoring of all agents."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True,
            name="agent-health-monitor"
        )
        self._monitor_thread.start()
        logger.info("Agent health monitoring started")
    
    def stop_monitoring(self):
        """Stop background health monitoring."""
        self._monitoring = False
        logger.info("Agent health monitoring stopped")
    
    def get_events(self, limit: int = 50) -> List[Dict]:
        """Get recent orchestrator events."""
        return [e.to_dict() for e in self.events[-limit:]]
    
    def get_agent_reports(self, agent_role: str, limit: int = 20) -> List[Dict]:
        """Get recent reports from a specific agent."""
        if agent_role == "analyst":
            return self.analyst.get_report_history(limit)
        elif agent_role == "regime":
            return self.regime.get_regime_history(limit)
        elif agent_role == "optimizer":
            return self.optimizer.get_optimization_history(limit)
        elif agent_role == "autonomous":
            return self.autonomous.get_proposal_history(limit)
        return []
    
    # ===== Private Methods =====
    
    def _load_mode(self) -> int:
        """Load current mode from config."""
        try:
            config_path = os.path.join("config", "global_mode.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    cfg = yaml.safe_load(f)
                    return cfg.get("global_mode", {}).get("current_mode", 1)
        except Exception as e:
            logger.warning(f"Could not load mode: {e}")
        return 1  # Default HYBRID
    
    def _get_mode_name(self) -> str:
        """Get human-readable mode name."""
        names = {
            0: "RULE ONLY",
            1: "HYBRID",
            2: "ML DOMINANT",
            3: "AI ASSISTED",
            4: "GUARDED AUTONOMOUS",
        }
        return names.get(self._current_mode, "UNKNOWN")
    
    def _get_active_agent_ids(self) -> List[str]:
        """Get list of currently active agent IDs."""
        active_roles = MODE_AGENT_MAP.get(self._current_mode, [])
        return [role.value for role in active_roles]
    
    def _is_agent_active(self, role: AgentRole) -> bool:
        """Check if an agent role is active in current mode."""
        active_roles = MODE_AGENT_MAP.get(self._current_mode, [])
        return role in active_roles
    
    def _apply_mode_permissions(self):
        """Apply permissions based on current mode."""
        active_roles = MODE_AGENT_MAP.get(self._current_mode, [])
        
        # Enable/disable autonomous agent
        if AgentRole.AUTONOMOUS in active_roles:
            self.autonomous.enable()
        else:
            self.autonomous.disable()
        
        logger.info(
            f"Mode {self._current_mode} ({self._get_mode_name()}): "
            f"Active agents: {[r.value for r in active_roles]}"
        )
    
    def _health_monitor_loop(self):
        """Background thread for monitoring agent health."""
        while self._monitoring:
            try:
                for role, agent in self.agents.items():
                    status = agent.get_status()
                    health = status.get("health", 0)
                    
                    if health < 50:
                        logger.warning(f"Agent {role.value} health low: {health}")
                        self._log_event("health_warning", role.value, {
                            "health": health,
                        })
                    
                    if health < 20:
                        # Critical health - force safe mode
                        logger.error(f"Agent {role.value} health critical: {health}")
                        self.force_safe_mode(
                            f"Agent {role.value} health critical ({health})"
                        )
                
                time.sleep(self._health_check_interval)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                time.sleep(10)
    
    def _log_event(self, event_type: str, agent_id: str, details: Dict = None):
        """Log an orchestrator event."""
        event = AgentEvent(
            event_type=event_type,
            agent_id=agent_id,
            details=details or {},
        )
        self.events.append(event)
        if len(self.events) > self._max_events:
            self.events = self.events[-self._max_events:]


# ===== Global Instance =====

_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator(config: Dict = None, risk_engine=None) -> AgentOrchestrator:
    """Get or create the global agent orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator(config=config, risk_engine=risk_engine)
    return _orchestrator
