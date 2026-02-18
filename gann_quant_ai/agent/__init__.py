"""
AI Agent Orchestration Layer
OpenClaw-style multi-agent system for institutional trading.

Agent Roles:
- Analyst Agent: Market analysis & trade explanation
- Regime Agent: Market regime detection & mode switching
- Optimizer Agent: Parameter tuning & backtesting
- Autonomous Agent: Guarded trade proposals (validation gate required)

CRITICAL: No agent has direct broker access.
"""

from agent.agent_orchestrator import AgentOrchestrator, get_agent_orchestrator
from agent.analyst_agent import AnalystAgent
from agent.regime_agent import RegimeAgent
from agent.optimizer_agent import OptimizerAgent
from agent.autonomous_agent import GuardedAutonomousAgent

__all__ = [
    'AgentOrchestrator',
    'get_agent_orchestrator',
    'AnalystAgent',
    'RegimeAgent',
    'OptimizerAgent',
    'GuardedAutonomousAgent',
]
