"""
Agent Orchestration API - REST endpoints for AI Agent system
Provides frontend access to:
- Agent status & health monitoring
- Mode switching (runtime configurable)
- Market analysis requests
- Trade proposals (Mode 4)
- Regime detection
- Parameter optimization
- Event/audit log
"""

from flask import Blueprint, request, jsonify
from loguru import logger
from typing import Dict, Any
from datetime import datetime
import traceback
import os
import yaml

# Create Blueprint
agent_api = Blueprint('agent_api', __name__, url_prefix='/api/agent')


def _get_orchestrator():
    """Lazy load the agent orchestrator."""
    try:
        from agent.agent_orchestrator import get_agent_orchestrator
        return get_agent_orchestrator()
    except Exception as e:
        logger.error(f"Failed to get orchestrator: {e}")
        return None


def _get_strategy_router():
    """Lazy load the strategy router."""
    try:
        from router.strategy_router import StrategyRouter
        return StrategyRouter()
    except Exception as e:
        logger.error(f"Failed to get strategy router: {e}")
        return None


# =============================================================================
# ORCHESTRATOR STATUS
# =============================================================================

@agent_api.route('/status', methods=['GET'])
def get_agent_status():
    """Get comprehensive agent orchestration status."""
    try:
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        status = orchestrator.get_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        logger.error(f"Agent status error: {e}")
        return jsonify({"error": str(e)}), 500


@agent_api.route('/agents', methods=['GET'])
def list_agents():
    """List all agents with their current status."""
    try:
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        agents = {
            role: agent.get_status()
            for role, agent in [
                ("analyst", orchestrator.analyst),
                ("regime", orchestrator.regime),
                ("optimizer", orchestrator.optimizer),
                ("autonomous", orchestrator.autonomous),
            ]
        }
        
        return jsonify({"success": True, "agents": agents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# MODE CONTROL
# =============================================================================

@agent_api.route('/mode', methods=['GET'])
def get_current_mode():
    """Get current global mode."""
    try:
        # Read from config file
        config_path = os.path.join("config", "global_mode.yaml")
        mode_data = {"current_mode": 1, "mode_name": "HYBRID"}
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                cfg = yaml.safe_load(f)
                if cfg and 'global_mode' in cfg:
                    mode_num = cfg['global_mode'].get('current_mode', 1)
                    mode_names = {
                        0: "RULE ONLY",
                        1: "HYBRID",
                        2: "ML DOMINANT",
                        3: "AI ASSISTED",
                        4: "GUARDED AUTONOMOUS",
                    }
                    mode_data = {
                        "current_mode": mode_num,
                        "mode_name": mode_names.get(mode_num, "UNKNOWN"),
                        "previous_mode": cfg['global_mode'].get('previous_mode', 0),
                        "last_changed": cfg['global_mode'].get('last_changed', ''),
                        "changed_by": cfg['global_mode'].get('changed_by', ''),
                    }
        
        return jsonify({"success": True, "data": mode_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/mode', methods=['POST'])
def switch_mode():
    """
    Switch global mode.
    
    Request body:
    {
        "target_mode": 0-4,
        "reason": "optional reason",
        "force": false
    }
    """
    try:
        data = request.get_json()
        target_mode = data.get('target_mode')
        reason = data.get('reason', 'Manual switch via API')
        force = data.get('force', False)
        
        if target_mode is None or target_mode not in range(5):
            return jsonify({"error": "target_mode must be 0-4"}), 400
        
        orchestrator = _get_orchestrator()
        if orchestrator:
            result = orchestrator.switch_mode(target_mode, reason, force)
        else:
            # Direct config update as fallback
            result = _direct_mode_switch(target_mode, reason)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Mode switch error: {e}")
        return jsonify({"error": str(e)}), 500


@agent_api.route('/mode/revert', methods=['POST'])
def emergency_revert():
    """Emergency revert to Mode 0 (RULE ONLY)."""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Emergency revert via API')
        
        orchestrator = _get_orchestrator()
        if orchestrator:
            result = orchestrator.force_safe_mode(reason)
        else:
            result = _direct_mode_switch(0, f"EMERGENCY: {reason}")
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# MARKET ANALYSIS (Analyst Agent)
# =============================================================================

@agent_api.route('/analyze', methods=['POST'])
def analyze_market():
    """
    Request market analysis from Analyst Agent.
    
    Request body:
    {
        "symbol": "BTC-USD",
        "include_gann": true,
        "include_ehlers": true,
        "include_ml": true
    }
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTC-USD')
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        result = orchestrator.analyze_market(
            symbol=symbol,
            gann_levels=data.get('gann_levels'),
            ehlers_indicators=data.get('ehlers_indicators'),
            ml_predictions=data.get('ml_predictions'),
        )
        
        return jsonify({"success": True, "analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/explain', methods=['POST'])
def explain_trade():
    """
    Request trade explanation from Analyst Agent.
    
    Request body:
    {
        "signal": {...},
        "components": {...}
    }
    """
    try:
        data = request.get_json()
        signal = data.get('signal', {})
        components = data.get('components')
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        result = orchestrator.explain_trade(signal, components)
        return jsonify({"success": True, "explanation": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/query', methods=['POST'])
def query_agent():
    """
    Ask a natural language query to the Analyst Agent.
    
    Request body:
    {
        "query": "Why was the last BTC trade generated?",
        "context": {}
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', {})
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        result = orchestrator.answer_query(query, context)
        return jsonify({"success": True, "response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# REGIME DETECTION (Regime Agent)
# =============================================================================

@agent_api.route('/regime', methods=['GET'])
def get_current_regime():
    """Get current detected market regime."""
    try:
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({
                "success": True,
                "regime": "unknown",
                "confidence": 0,
            })
        
        return jsonify({
            "success": True,
            "regime": orchestrator.regime.current_regime.value,
            "current_mode": orchestrator.current_mode,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/regime/detect', methods=['POST'])
def detect_regime():
    """
    Trigger regime detection.
    
    Request body:
    {
        "symbol": "BTC-USD",
        "auto_switch": true
    }
    """
    try:
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        # This would normally use real price data
        # For now, return regime status
        return jsonify({
            "success": True,
            "regime": orchestrator.regime.current_regime.value,
            "mode": orchestrator.current_mode,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# PARAMETER OPTIMIZATION (Optimizer Agent)
# =============================================================================

@agent_api.route('/optimize', methods=['POST'])
def run_optimization():
    """
    Run parameter optimization.
    
    Request body:
    {
        "parameters": ["ml_probability_threshold", "confidence_threshold"],
        "apply_results": false
    }
    """
    try:
        data = request.get_json() or {}
        params = data.get('parameters')
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        result = orchestrator.optimize_parameters(params=params)
        return jsonify({"success": True, "optimization": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/optimize/restore', methods=['POST'])
def restore_defaults():
    """Restore all optimized parameters to defaults."""
    try:
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        result = orchestrator.optimizer.restore_defaults()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# TRADE PROPOSALS (Autonomous Agent - Mode 4 only)
# =============================================================================

@agent_api.route('/proposals', methods=['GET'])
def get_proposals():
    """Get all pending trade proposals."""
    try:
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"success": True, "proposals": []})
        
        proposals = orchestrator.autonomous.get_pending_proposals()
        return jsonify({"success": True, "proposals": proposals})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/proposals/history', methods=['GET'])
def get_proposal_history():
    """Get trade proposal history."""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"success": True, "history": []})
        
        history = orchestrator.autonomous.get_proposal_history(limit)
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/proposals/<proposal_id>/approve', methods=['POST'])
def approve_proposal(proposal_id):
    """Approve a pending trade proposal."""
    try:
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        result = orchestrator.approve_trade_proposal(proposal_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/proposals/<proposal_id>/reject', methods=['POST'])
def reject_proposal(proposal_id):
    """Reject a pending trade proposal."""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"error": "Orchestrator not available"}), 503
        
        result = orchestrator.reject_trade_proposal(proposal_id, reason)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# STRATEGY ROUTER
# =============================================================================

@agent_api.route('/router/status', methods=['GET'])
def get_router_status():
    """Get strategy router status and stats."""
    try:
        router = _get_strategy_router()
        if not router:
            return jsonify({"error": "Router not available"}), 503
        
        return jsonify({
            "success": True,
            "stats": router.get_routing_stats(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/router/signals', methods=['GET'])
def get_routed_signals():
    """Get recent routed signal history."""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        router = _get_strategy_router()
        if not router:
            return jsonify({"success": True, "signals": []})
        
        signals = router.get_signal_history(limit)
        return jsonify({"success": True, "signals": signals})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# EVENTS & AUDIT LOG
# =============================================================================

@agent_api.route('/events', methods=['GET'])
def get_events():
    """Get orchestrator event log."""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"success": True, "events": []})
        
        events = orchestrator.get_events(limit)
        return jsonify({"success": True, "events": events})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_api.route('/reports/<agent_role>', methods=['GET'])
def get_agent_reports(agent_role):
    """Get reports from a specific agent."""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        orchestrator = _get_orchestrator()
        if not orchestrator:
            return jsonify({"success": True, "reports": []})
        
        reports = orchestrator.get_agent_reports(agent_role, limit)
        return jsonify({"success": True, "reports": reports})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# GLOBAL MODE CONFIG
# =============================================================================

@agent_api.route('/config/global_mode', methods=['GET'])
def get_global_mode_config():
    """Get complete global mode configuration."""
    try:
        config_path = os.path.join("config", "global_mode.yaml")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return jsonify({"success": True, "config": config})
        else:
            return jsonify({"error": "global_mode.yaml not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _direct_mode_switch(target_mode: int, reason: str) -> Dict:
    """Direct mode switch via config file (fallback when orchestrator unavailable)."""
    try:
        config_path = os.path.join("config", "global_mode.yaml")
        config = {}
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        
        previous = config.get("global_mode", {}).get("current_mode", 1)
        
        if "global_mode" not in config:
            config["global_mode"] = {}
        
        config["global_mode"]["current_mode"] = target_mode
        config["global_mode"]["previous_mode"] = previous
        config["global_mode"]["last_changed"] = datetime.now().isoformat()
        config["global_mode"]["changed_by"] = reason
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return {
            "success": True,
            "previous_mode": previous,
            "new_mode": target_mode,
            "reason": reason,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# REGISTER ROUTES
# =============================================================================

def register_agent_routes(app):
    """Register agent API routes with Flask app."""
    app.register_blueprint(agent_api)
    logger.info("Agent API routes registered")
