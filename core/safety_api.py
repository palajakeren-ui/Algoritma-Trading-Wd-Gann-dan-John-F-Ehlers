"""
Live Trading Safety & Kill Switch Module
Provides comprehensive safety controls for live trading.
"""
from flask import Blueprint, request, jsonify
from loguru import logger
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import os
import json

safety_api = Blueprint('safety_api', __name__, url_prefix='/api/safety')

# ============================================================================
# GLOBAL SAFETY STATE
# ============================================================================

class TradingSafetyManager:
    """Manages all trading safety controls."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.kill_switch_active = False
        self.trading_paused = False
        self.mode = 'paper'  # 'paper' | 'live'
        self.max_daily_loss_percent = 5.0
        self.max_position_size_percent = 10.0
        self.max_drawdown_percent = 15.0
        self.current_daily_pnl = 0.0
        self.current_drawdown = 0.0
        self.emergency_contacts = []
        self.last_safety_check = None
        self.safety_log = []
        
        # Load state from file
        self._load_state()
    
    def _get_state_file(self) -> str:
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        return os.path.join(config_dir, 'safety_state.json')
    
    def _load_state(self):
        """Load safety state from file."""
        try:
            state_file = self._get_state_file()
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.kill_switch_active = state.get('kill_switch_active', False)
                    self.mode = state.get('mode', 'paper')
                    self.max_daily_loss_percent = state.get('max_daily_loss_percent', 5.0)
                    self.max_position_size_percent = state.get('max_position_size_percent', 10.0)
                    self.max_drawdown_percent = state.get('max_drawdown_percent', 15.0)
        except Exception as e:
            logger.warning(f"Failed to load safety state: {e}")
    
    def _save_state(self):
        """Save safety state to file."""
        try:
            state_file = self._get_state_file()
            state = {
                'kill_switch_active': self.kill_switch_active,
                'mode': self.mode,
                'max_daily_loss_percent': self.max_daily_loss_percent,
                'max_position_size_percent': self.max_position_size_percent,
                'max_drawdown_percent': self.max_drawdown_percent,
                'last_updated': datetime.now().isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save safety state: {e}")
    
    def activate_kill_switch(self, reason: str = "Manual activation") -> bool:
        """Activate kill switch - stops all trading immediately."""
        self.kill_switch_active = True
        self._save_state()
        self._log_safety_event("KILL_SWITCH_ACTIVATED", reason)
        logger.warning(f"🛑 KILL SWITCH ACTIVATED: {reason}")
        return True
    
    def deactivate_kill_switch(self, confirmation_code: str = None) -> bool:
        """Deactivate kill switch - requires confirmation."""
        if confirmation_code != "CONFIRM_DEACTIVATE":
            logger.warning("Kill switch deactivation requires confirmation code")
            return False
        
        self.kill_switch_active = False
        self._save_state()
        self._log_safety_event("KILL_SWITCH_DEACTIVATED", "Manual deactivation")
        logger.info("✅ Kill switch deactivated")
        return True
    
    def set_trading_mode(self, mode: str) -> bool:
        """Set trading mode (paper/live)."""
        if mode not in ['paper', 'live']:
            return False
        
        old_mode = self.mode
        self.mode = mode
        self._save_state()
        self._log_safety_event("MODE_CHANGED", f"{old_mode} -> {mode}")
        logger.info(f"Trading mode changed: {old_mode} -> {mode}")
        return True
    
    def check_trade_allowed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a trade is allowed based on safety rules."""
        result = {
            'allowed': True,
            'reasons': [],
            'warnings': []
        }
        
        # Kill switch check
        if self.kill_switch_active:
            result['allowed'] = False
            result['reasons'].append("Kill switch is active")
            return result
        
        # Trading paused check
        if self.trading_paused:
            result['allowed'] = False
            result['reasons'].append("Trading is paused")
            return result
        
        # Daily loss check
        if self.current_daily_pnl <= -self.max_daily_loss_percent:
            result['allowed'] = False
            result['reasons'].append(f"Daily loss limit reached ({self.max_daily_loss_percent}%)")
            self.activate_kill_switch("Daily loss limit exceeded")
            return result
        
        # Drawdown check
        if self.current_drawdown >= self.max_drawdown_percent:
            result['allowed'] = False
            result['reasons'].append(f"Max drawdown reached ({self.max_drawdown_percent}%)")
            self.activate_kill_switch("Max drawdown exceeded")
            return result
        
        # Position size check
        position_size = params.get('position_size_percent', 0)
        if position_size > self.max_position_size_percent:
            result['allowed'] = False
            result['reasons'].append(f"Position size exceeds limit ({self.max_position_size_percent}%)")
            return result
        
        # Warnings
        if self.current_daily_pnl <= -self.max_daily_loss_percent * 0.8:
            result['warnings'].append("Approaching daily loss limit")
        
        if self.current_drawdown >= self.max_drawdown_percent * 0.8:
            result['warnings'].append("Approaching max drawdown")
        
        self.last_safety_check = datetime.now()
        return result
    
    def _log_safety_event(self, event_type: str, details: str):
        """Log safety event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details
        }
        self.safety_log.append(event)
        # Keep only last 100 events
        if len(self.safety_log) > 100:
            self.safety_log = self.safety_log[-100:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current safety status."""
        return {
            'kill_switch_active': self.kill_switch_active,
            'trading_paused': self.trading_paused,
            'mode': self.mode,
            'limits': {
                'max_daily_loss_percent': self.max_daily_loss_percent,
                'max_position_size_percent': self.max_position_size_percent,
                'max_drawdown_percent': self.max_drawdown_percent
            },
            'current_metrics': {
                'daily_pnl': self.current_daily_pnl,
                'drawdown': self.current_drawdown
            },
            'last_safety_check': self.last_safety_check.isoformat() if self.last_safety_check else None,
            'recent_events': self.safety_log[-10:]
        }


# Global safety manager instance
safety_manager = TradingSafetyManager()


# ============================================================================
# SAFETY API ENDPOINTS
# ============================================================================

@safety_api.route('/status', methods=['GET'])
def get_safety_status():
    """Get current safety status."""
    try:
        status = safety_manager.get_status()
        return jsonify({
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get safety status: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/kill-switch', methods=['GET'])
def get_kill_switch_status():
    """Get kill switch status."""
    try:
        return jsonify({
            "success": True,
            "active": safety_manager.kill_switch_active,
            "mode": safety_manager.mode,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get kill switch status: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/kill-switch/activate', methods=['POST'])
def activate_kill_switch():
    """Activate kill switch."""
    try:
        data = request.json or {}
        reason = data.get('reason', 'Manual activation')
        
        if safety_manager.activate_kill_switch(reason):
            return jsonify({
                "success": True,
                "message": "Kill switch activated",
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to activate kill switch"}), 500
    except Exception as e:
        logger.error(f"Failed to activate kill switch: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/kill-switch/deactivate', methods=['POST'])
def deactivate_kill_switch():
    """Deactivate kill switch (requires confirmation)."""
    try:
        data = request.json or {}
        confirmation = data.get('confirmationCode')
        
        if not confirmation:
            return jsonify({
                "error": "Confirmation code required",
                "requiredCode": "CONFIRM_DEACTIVATE"
            }), 400
        
        if safety_manager.deactivate_kill_switch(confirmation):
            return jsonify({
                "success": True,
                "message": "Kill switch deactivated",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Invalid confirmation code"}), 400
    except Exception as e:
        logger.error(f"Failed to deactivate kill switch: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/mode', methods=['GET'])
def get_trading_mode():
    """Get current trading mode."""
    try:
        return jsonify({
            "success": True,
            "mode": safety_manager.mode,
            "isSafe": safety_manager.mode == 'paper',
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get trading mode: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/mode', methods=['POST'])
def set_trading_mode():
    """Set trading mode."""
    try:
        data = request.json or {}
        mode = data.get('mode')
        
        if mode not in ['paper', 'live']:
            return jsonify({
                "error": "Invalid mode. Must be 'paper' or 'live'"
            }), 400
        
        # Extra safety for live mode
        if mode == 'live':
            confirmation = data.get('confirmLive')
            if not confirmation:
                return jsonify({
                    "error": "Live trading requires confirmation",
                    "requiresConfirmation": True
                }), 400
        
        if safety_manager.set_trading_mode(mode):
            return jsonify({
                "success": True,
                "mode": mode,
                "message": f"Trading mode set to {mode}",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to set trading mode"}), 500
    except Exception as e:
        logger.error(f"Failed to set trading mode: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/limits', methods=['GET'])
def get_safety_limits():
    """Get safety limits."""
    try:
        return jsonify({
            "success": True,
            "limits": {
                "maxDailyLossPercent": safety_manager.max_daily_loss_percent,
                "maxPositionSizePercent": safety_manager.max_position_size_percent,
                "maxDrawdownPercent": safety_manager.max_drawdown_percent
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get safety limits: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/limits', methods=['POST'])
def update_safety_limits():
    """Update safety limits."""
    try:
        data = request.json or {}
        
        if 'maxDailyLossPercent' in data:
            safety_manager.max_daily_loss_percent = float(data['maxDailyLossPercent'])
        if 'maxPositionSizePercent' in data:
            safety_manager.max_position_size_percent = float(data['maxPositionSizePercent'])
        if 'maxDrawdownPercent' in data:
            safety_manager.max_drawdown_percent = float(data['maxDrawdownPercent'])
        
        safety_manager._save_state()
        
        return jsonify({
            "success": True,
            "message": "Safety limits updated",
            "limits": {
                "maxDailyLossPercent": safety_manager.max_daily_loss_percent,
                "maxPositionSizePercent": safety_manager.max_position_size_percent,
                "maxDrawdownPercent": safety_manager.max_drawdown_percent
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to update safety limits: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/check-trade', methods=['POST'])
def check_trade_allowed():
    """Check if a trade is allowed based on safety rules."""
    try:
        data = request.json or {}
        
        result = safety_manager.check_trade_allowed(data)
        
        return jsonify({
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to check trade: {e}")
        return jsonify({"error": str(e)}), 500


@safety_api.route('/events', methods=['GET'])
def get_safety_events():
    """Get recent safety events."""
    try:
        return jsonify({
            "success": True,
            "events": safety_manager.safety_log,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get safety events: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# REGISTRATION
# ============================================================================

def register_safety_routes(app):
    """Register safety API routes with Flask app."""
    app.register_blueprint(safety_api)
    logger.info("Safety API routes registered")


# Export safety manager for use by other modules
def get_safety_manager() -> TradingSafetyManager:
    """Get the global safety manager instance."""
    return safety_manager
