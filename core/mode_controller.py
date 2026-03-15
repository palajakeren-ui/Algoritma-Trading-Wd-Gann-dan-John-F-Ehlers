"""
Mode Controller - Centralized runtime mode switching engine.

This module is the SINGLE SOURCE OF TRUTH for the current global mode.
It handles:
1. Mode transition validation
2. Persistence to global_mode.yaml
3. Event emission for mode changes
4. Fallback logic (auto-revert to Mode 0 on failures)
5. Emergency revert capability
6. Mode change audit trail

IMPORTANT: All mode changes MUST go through this controller.
Direct YAML edits will be picked up on next read but won't emit events.
"""

from loguru import logger
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os
import yaml
import threading


class GlobalMode(Enum):
    """Trading system global modes."""
    RULE_ONLY = 0           # Pure deterministic (Gann + Ehlers)
    HYBRID = 1              # Rule generates → ML confirms (DEFAULT)
    ML_DOMINANT = 2         # ML primary, Rule as structural filter
    AI_ASSISTED = 3         # AI advisory + parameter optimization
    GUARDED_AUTONOMOUS = 4  # AI trade proposals via validation gate


# Mode metadata
MODE_INFO = {
    0: {
        "name": "RULE ONLY",
        "description": "Pure deterministic trading using Gann + Ehlers",
        "engines": ["gann", "ehlers"],
        "agents": [],
        "risk_level": "minimal",
        "requires_approval": False,
    },
    1: {
        "name": "HYBRID",
        "description": "Rule generates signal → ML confirms",
        "engines": ["gann", "ehlers", "ml"],
        "agents": [],
        "risk_level": "low",
        "requires_approval": False,
    },
    2: {
        "name": "ML DOMINANT",
        "description": "ML primary signal, Rule as structural filter",
        "engines": ["ml", "gann_filter", "ehlers_filter"],
        "agents": [],
        "risk_level": "medium",
        "requires_approval": False,
    },
    3: {
        "name": "AI ASSISTED",
        "description": "AI advisory + parameter optimization (no trade orders)",
        "engines": ["gann", "ehlers", "ml"],
        "agents": ["analyst", "regime", "optimizer"],
        "risk_level": "medium_high",
        "requires_approval": False,
    },
    4: {
        "name": "GUARDED AUTONOMOUS",
        "description": "AI trade proposals via 6-gate validation + human approval",
        "engines": ["gann", "ehlers", "ml", "ai"],
        "agents": ["analyst", "regime", "optimizer", "autonomous"],
        "risk_level": "high_guarded",
        "requires_approval": True,
    },
}

# Allowed mode transitions (from → [allowed_to])
ALLOWED_TRANSITIONS = {
    0: [1, 2, 3],       # Can go up to AI Assisted from Rule Only
    1: [0, 2, 3],       # Hybrid can go anywhere except directly to Mode 4
    2: [0, 1, 3],       # ML Dominant can go anywhere except directly to Mode 4
    3: [0, 1, 2, 4],    # AI Assisted can go to Mode 4 (must pass through M3 first)
    4: [0, 1, 2, 3],    # Autonomous can go anywhere (including emergency M0)
}


@dataclass
class ModeChangeEvent:
    """Record of a mode change."""
    timestamp: datetime = field(default_factory=datetime.now)
    from_mode: int = 0
    to_mode: int = 0
    reason: str = ""
    initiated_by: str = ""  # "user", "regime_agent", "system", "emergency"
    success: bool = True
    error: str = ""

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "from_mode": self.from_mode,
            "to_mode": self.to_mode,
            "from_name": MODE_INFO.get(self.from_mode, {}).get("name", "UNKNOWN"),
            "to_name": MODE_INFO.get(self.to_mode, {}).get("name", "UNKNOWN"),
            "reason": self.reason,
            "initiated_by": self.initiated_by,
            "success": self.success,
            "error": self.error,
        }


class ModeController:
    """
    Centralized mode controller for the trading system.
    
    Architecture:
    ┌──────────────────────────────────────────────┐
    │              MODE CONTROLLER                  │
    │                                              │
    │  ┌─────────┐  ┌──────────┐  ┌────────────┐  │
    │  │ Validate │→│ Persist  │→│ Emit Events│  │
    │  └─────────┘  └──────────┘  └────────────┘  │
    │                                              │
    │  ┌──────────────────────────────────────┐    │
    │  │    Fallback & Emergency Logic         │    │
    │  └──────────────────────────────────────┘    │
    └──────────────────────────────────────────────┘
    
    Usage:
        controller = get_mode_controller()
        controller.switch_mode(3, "User requested AI Assisted", "user")
        current = controller.current_mode
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_path = os.path.join(config_dir, "global_mode.yaml")
        self._lock = threading.RLock()

        # State
        self._current_mode: int = 1  # Default: HYBRID
        self._previous_mode: int = 0
        self._mode_change_history: List[ModeChangeEvent] = []
        self._max_history: int = 200

        # Event callbacks
        self._on_mode_change: List[Callable] = []
        self._on_emergency_revert: List[Callable] = []

        # Load from config
        self._load_from_config()

        logger.info(f"ModeController initialized | Current mode: {self._current_mode} ({self.mode_name})")

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def current_mode(self) -> int:
        """Get current mode number."""
        return self._current_mode

    @property
    def mode_name(self) -> str:
        """Get current mode name."""
        return MODE_INFO.get(self._current_mode, {}).get("name", "UNKNOWN")

    @property
    def previous_mode(self) -> int:
        """Get previous mode number."""
        return self._previous_mode

    @property
    def mode_info(self) -> Dict:
        """Get current mode metadata."""
        return MODE_INFO.get(self._current_mode, {})

    @property
    def active_engines(self) -> List[str]:
        """Get list of active engines for current mode."""
        return MODE_INFO.get(self._current_mode, {}).get("engines", [])

    @property
    def active_agents(self) -> List[str]:
        """Get list of active agents for current mode."""
        return MODE_INFO.get(self._current_mode, {}).get("agents", [])

    @property
    def is_ai_active(self) -> bool:
        """Check if any AI agents are active."""
        return self._current_mode >= 3

    @property
    def is_autonomous(self) -> bool:
        """Check if autonomous trading is active."""
        return self._current_mode == 4

    # =========================================================================
    # MODE SWITCHING
    # =========================================================================

    def switch_mode(
        self,
        target_mode: int,
        reason: str = "",
        initiated_by: str = "user",
        force: bool = False,
    ) -> Dict:
        """
        Switch the global trading mode.
        
        Args:
            target_mode: Target mode (0-4)
            reason: Reason for the switch
            initiated_by: Who initiated ("user", "regime_agent", "system", "emergency")
            force: Force the switch (bypasses transition validation)
        
        Returns:
            Dict with success status and details
        """
        with self._lock:
            # Validate target
            if target_mode not in range(5):
                return {
                    "success": False,
                    "error": f"Invalid mode: {target_mode}. Must be 0-4.",
                }

            # No-op if same mode
            if target_mode == self._current_mode:
                return {
                    "success": True,
                    "message": f"Already in mode {target_mode} ({self.mode_name})",
                    "current_mode": self._current_mode,
                }

            # Validate transition
            if not force and target_mode not in ALLOWED_TRANSITIONS.get(self._current_mode, []):
                # Special: allow direct M0 revert from anywhere
                if target_mode == 0:
                    pass  # Always allow reverting to M0
                else:
                    return {
                        "success": False,
                        "error": f"Direct transition M{self._current_mode}→M{target_mode} not allowed. "
                                 f"Allowed: {ALLOWED_TRANSITIONS.get(self._current_mode, [])}",
                    }

            # Mode 4 requires explicit human approval
            if target_mode == 4 and initiated_by not in ("user", "emergency"):
                return {
                    "success": False,
                    "pending_approval": True,
                    "error": "Mode 4 (Guarded Autonomous) requires explicit human approval",
                }

            # Execute transition
            old_mode = self._current_mode
            self._previous_mode = old_mode
            self._current_mode = target_mode

            # Persist to config
            self._save_to_config(reason, initiated_by)

            # Log event
            event = ModeChangeEvent(
                from_mode=old_mode,
                to_mode=target_mode,
                reason=reason,
                initiated_by=initiated_by,
                success=True,
            )
            self._mode_change_history.append(event)
            if len(self._mode_change_history) > self._max_history:
                self._mode_change_history = self._mode_change_history[-self._max_history:]

            # Emit events
            for callback in self._on_mode_change:
                try:
                    callback(old_mode, target_mode, reason)
                except Exception as e:
                    logger.warning(f"Mode change callback error: {e}")

            logger.success(
                f"Mode switched: M{old_mode} ({MODE_INFO[old_mode]['name']}) → "
                f"M{target_mode} ({MODE_INFO[target_mode]['name']}) | "
                f"Reason: {reason} | By: {initiated_by}"
            )

            return {
                "success": True,
                "previous_mode": old_mode,
                "new_mode": target_mode,
                "mode_name": MODE_INFO[target_mode]["name"],
                "active_engines": MODE_INFO[target_mode]["engines"],
                "active_agents": MODE_INFO[target_mode]["agents"],
                "reason": reason,
                "initiated_by": initiated_by,
            }

    def emergency_revert(self, reason: str = "Emergency") -> Dict:
        """
        Immediately revert to Mode 0 (RULE ONLY).
        
        This bypasses ALL validation and transition rules.
        Intended for:
        - System failures
        - AI anomalies
        - Risk limit breaches
        - Manual kill switch
        """
        with self._lock:
            old_mode = self._current_mode
            self._previous_mode = old_mode
            self._current_mode = 0

            # Persist
            self._save_to_config(f"EMERGENCY: {reason}", "emergency")

            # Log event
            event = ModeChangeEvent(
                from_mode=old_mode,
                to_mode=0,
                reason=f"EMERGENCY: {reason}",
                initiated_by="emergency",
                success=True,
            )
            self._mode_change_history.append(event)

            # Emit emergency callbacks
            for callback in self._on_emergency_revert:
                try:
                    callback(old_mode, reason)
                except Exception as e:
                    logger.error(f"Emergency revert callback error: {e}")

            # Also emit regular mode change callbacks
            for callback in self._on_mode_change:
                try:
                    callback(old_mode, 0, f"EMERGENCY: {reason}")
                except Exception as e:
                    logger.warning(f"Mode change callback error: {e}")

            logger.warning(
                f"⚠️ EMERGENCY REVERT: M{old_mode} → M0 (RULE ONLY) | Reason: {reason}"
            )

            return {
                "success": True,
                "previous_mode": old_mode,
                "new_mode": 0,
                "mode_name": "RULE ONLY",
                "reason": f"EMERGENCY: {reason}",
                "initiated_by": "emergency",
            }

    def restore_previous(self, reason: str = "Restore") -> Dict:
        """Restore the previous mode."""
        if self._previous_mode == self._current_mode:
            return {"success": False, "error": "No previous mode to restore"}
        return self.switch_mode(self._previous_mode, reason, "system")

    # =========================================================================
    # VALIDATION & QUERY
    # =========================================================================

    def can_switch_to(self, target_mode: int) -> Dict:
        """Check if a mode switch is allowed."""
        if target_mode == self._current_mode:
            return {"allowed": True, "reason": "Already in this mode"}

        if target_mode == 0:
            return {"allowed": True, "reason": "Emergency revert always allowed"}

        allowed = target_mode in ALLOWED_TRANSITIONS.get(self._current_mode, [])
        return {
            "allowed": allowed,
            "reason": f"Transition M{self._current_mode}→M{target_mode} {'allowed' if allowed else 'not allowed'}",
            "allowed_targets": ALLOWED_TRANSITIONS.get(self._current_mode, []),
        }

    def is_engine_active(self, engine_name: str) -> bool:
        """Check if a specific engine should be active."""
        return engine_name in self.active_engines

    def is_agent_active(self, agent_name: str) -> bool:
        """Check if a specific agent should be active."""
        return agent_name in self.active_agents

    def get_status(self) -> Dict:
        """Get comprehensive mode controller status."""
        return {
            "current_mode": self._current_mode,
            "mode_name": self.mode_name,
            "previous_mode": self._previous_mode,
            "mode_info": self.mode_info,
            "active_engines": self.active_engines,
            "active_agents": self.active_agents,
            "is_ai_active": self.is_ai_active,
            "is_autonomous": self.is_autonomous,
            "allowed_transitions": ALLOWED_TRANSITIONS.get(self._current_mode, []),
            "total_switches": len(self._mode_change_history),
        }

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get mode change history."""
        return [e.to_dict() for e in self._mode_change_history[-limit:]]

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    def on_mode_change(self, callback: Callable):
        """Register callback for mode changes. Signature: (old_mode, new_mode, reason)"""
        self._on_mode_change.append(callback)

    def on_emergency_revert(self, callback: Callable):
        """Register callback for emergency reverts. Signature: (old_mode, reason)"""
        self._on_emergency_revert.append(callback)

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _load_from_config(self):
        """Load mode from global_mode.yaml."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    cfg = yaml.safe_load(f)
                if cfg and 'global_mode' in cfg:
                    self._current_mode = cfg['global_mode'].get('current_mode', 1)
                    self._previous_mode = cfg['global_mode'].get('previous_mode', 0)
                    logger.debug(f"Loaded mode from config: M{self._current_mode}")
        except Exception as e:
            logger.error(f"Failed to load mode config: {e}")
            self._current_mode = 1  # Safe default

    def _save_to_config(self, reason: str = "", initiated_by: str = ""):
        """Persist current mode to global_mode.yaml."""
        try:
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}

            if 'global_mode' not in config:
                config['global_mode'] = {}

            config['global_mode']['current_mode'] = self._current_mode
            config['global_mode']['previous_mode'] = self._previous_mode
            config['global_mode']['last_changed'] = datetime.now().isoformat()
            config['global_mode']['changed_by'] = initiated_by
            config['global_mode']['change_reason'] = reason

            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.debug(f"Mode persisted to config: M{self._current_mode}")
        except Exception as e:
            logger.error(f"Failed to save mode config: {e}")

    def reload(self):
        """Force reload mode from config file."""
        with self._lock:
            self._load_from_config()


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_mode_controller: Optional[ModeController] = None


def get_mode_controller(config_dir: str = "config") -> ModeController:
    """Get or create the global mode controller."""
    global _mode_controller
    if _mode_controller is None:
        _mode_controller = ModeController(config_dir)
    return _mode_controller
