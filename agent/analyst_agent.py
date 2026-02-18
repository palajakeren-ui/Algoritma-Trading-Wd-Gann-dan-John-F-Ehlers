"""
Analyst Agent - Market Analysis & Trade Explanation
Part of OpenClaw-style AI Agent Orchestration Layer.

Capabilities:
- Explain trade rationale (why a signal was generated)
- Summarize current market conditions
- Answer user queries about positions, signals, and market state
- Generate human-readable market briefs

CONSTRAINT: Read-only access. Cannot modify state or place orders.
"""

import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class AnalystQueryType(str, Enum):
    TRADE_EXPLANATION = "trade_explanation"
    MARKET_SUMMARY = "market_summary"
    POSITION_ANALYSIS = "position_analysis"
    SIGNAL_BREAKDOWN = "signal_breakdown"
    RISK_ASSESSMENT = "risk_assessment"
    CORRELATION_REPORT = "correlation_report"


@dataclass
class AnalystReport:
    """Structured analyst report output."""
    report_id: str = ""
    query_type: AnalystQueryType = AnalystQueryType.MARKET_SUMMARY
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Content
    title: str = ""
    summary: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Analysis components
    gann_analysis: Dict = field(default_factory=dict)
    ehlers_analysis: Dict = field(default_factory=dict)
    ml_analysis: Dict = field(default_factory=dict)
    regime_analysis: Dict = field(default_factory=dict)
    
    # Confidence
    confidence: float = 0.0
    data_quality: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "query_type": self.query_type.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "summary": self.summary,
            "details": self.details,
            "gann_analysis": self.gann_analysis,
            "ehlers_analysis": self.ehlers_analysis,
            "ml_analysis": self.ml_analysis,
            "regime_analysis": self.regime_analysis,
            "confidence": self.confidence,
            "data_quality": self.data_quality,
        }


class AnalystAgent:
    """
    AI Analyst Agent - Provides market analysis and trade explanations.
    
    This agent is READ-ONLY. It observes system state but cannot modify it.
    It has no access to execution or broker systems.
    
    Capabilities:
    1. Explain why a trade signal was generated
    2. Summarize current market conditions across engines
    3. Answer natural language queries about positions/market
    4. Generate structured analysis reports
    """
    
    AGENT_ID = "analyst-agent"
    AGENT_NAME = "Analyst Agent"
    AGENT_VERSION = "1.0.0"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.status = "idle"
        self.health = 100
        self.tasks_completed = 0
        self.current_task = None
        self.last_report: Optional[AnalystReport] = None
        self._report_history: List[AnalystReport] = []
        self._max_history = 100
        
        logger.info(f"AnalystAgent v{self.AGENT_VERSION} initialized")
    
    def get_status(self) -> Dict:
        """Get current agent status."""
        return {
            "agent_id": self.AGENT_ID,
            "name": self.AGENT_NAME,
            "version": self.AGENT_VERSION,
            "status": self.status,
            "health": self.health,
            "tasks_completed": self.tasks_completed,
            "current_task": self.current_task,
            "last_report_time": self.last_report.timestamp.isoformat() if self.last_report else None,
        }
    
    def explain_trade(
        self,
        signal: Dict,
        rule_components: Dict = None,
        ml_prediction: Dict = None,
        market_context: Dict = None
    ) -> AnalystReport:
        """
        Generate a comprehensive explanation of why a trade signal was produced.
        
        Args:
            signal: The generated trade signal
            rule_components: Gann/Ehlers rule engine outputs
            ml_prediction: ML model prediction details
            market_context: Current market state
            
        Returns:
            AnalystReport with detailed trade explanation
        """
        self.status = "analyzing"
        self.current_task = f"Explaining trade: {signal.get('symbol', 'unknown')}"
        logger.info(f"AnalystAgent: Explaining trade for {signal.get('symbol')}")
        
        try:
            report = AnalystReport(
                report_id=f"trade-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                query_type=AnalystQueryType.TRADE_EXPLANATION,
                title=f"Trade Explanation: {signal.get('symbol', 'N/A')} {signal.get('direction', 'N/A')}",
            )
            
            # Analyze Gann components
            if rule_components:
                gann_data = rule_components.get("gann", {})
                report.gann_analysis = self._analyze_gann_component(gann_data, signal)
                
                ehlers_data = rule_components.get("ehlers", {})
                report.ehlers_analysis = self._analyze_ehlers_component(ehlers_data, signal)
            
            # Analyze ML component
            if ml_prediction:
                report.ml_analysis = self._analyze_ml_component(ml_prediction, signal)
            
            # Build summary
            report.summary = self._build_trade_summary(signal, report)
            report.details = {
                "signal": signal,
                "rule_alignment": self._check_rule_alignment(rule_components),
                "ml_confidence": ml_prediction.get("probability", 0) if ml_prediction else 0,
                "market_context": market_context or {},
            }
            
            report.confidence = self._calculate_report_confidence(report)
            report.data_quality = self._assess_data_quality(signal, rule_components, ml_prediction)
            
            self._store_report(report)
            return report
            
        except Exception as e:
            logger.error(f"AnalystAgent error in explain_trade: {e}")
            return AnalystReport(
                title="Error generating explanation",
                summary=f"Analysis failed: {str(e)}",
                confidence=0.0
            )
        finally:
            self.status = "idle"
            self.current_task = None
    
    def summarize_market(
        self,
        symbol: str,
        price_data: pd.DataFrame = None,
        gann_levels: Dict = None,
        ehlers_indicators: Dict = None,
        ml_predictions: Dict = None,
        regime: str = None
    ) -> AnalystReport:
        """
        Generate comprehensive market summary for a symbol.
        
        Combines analysis from all engines into a human-readable brief.
        """
        self.status = "analyzing"
        self.current_task = f"Market summary: {symbol}"
        logger.info(f"AnalystAgent: Generating market summary for {symbol}")
        
        try:
            report = AnalystReport(
                report_id=f"market-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                query_type=AnalystQueryType.MARKET_SUMMARY,
                title=f"Market Summary: {symbol}",
            )
            
            # Current price info
            current_price = None
            if price_data is not None and not price_data.empty:
                current_price = float(price_data['close'].iloc[-1])
            
            # Gann analysis
            if gann_levels:
                report.gann_analysis = {
                    "nearest_support": gann_levels.get("support", []),
                    "nearest_resistance": gann_levels.get("resistance", []),
                    "key_angles": gann_levels.get("angles", {}),
                    "time_cycles": gann_levels.get("cycles", {}),
                    "interpretation": self._interpret_gann_position(current_price, gann_levels),
                }
            
            # Ehlers analysis
            if ehlers_indicators:
                report.ehlers_analysis = {
                    "cycle_phase": ehlers_indicators.get("cycle_phase", "unknown"),
                    "trend_strength": ehlers_indicators.get("trend_strength", 0),
                    "dominant_cycle": ehlers_indicators.get("dominant_cycle", 0),
                    "interpretation": self._interpret_ehlers(ehlers_indicators),
                }
            
            # ML analysis
            if ml_predictions:
                report.ml_analysis = {
                    "direction_probability": ml_predictions.get("probability", 0.5),
                    "predicted_direction": "bullish" if ml_predictions.get("probability", 0.5) > 0.5 else "bearish",
                    "model_agreement": ml_predictions.get("ensemble_agreement", 0),
                    "feature_importance": ml_predictions.get("top_features", []),
                }
            
            # Regime
            if regime:
                report.regime_analysis = {
                    "current_regime": regime,
                    "regime_confidence": 0.75,
                }
            
            # Build comprehensive summary
            report.summary = self._build_market_summary(symbol, current_price, report)
            report.confidence = self._calculate_report_confidence(report)
            
            self._store_report(report)
            return report
            
        except Exception as e:
            logger.error(f"AnalystAgent error in summarize_market: {e}")
            return AnalystReport(title=f"Error summarizing {symbol}", summary=str(e))
        finally:
            self.status = "idle"
            self.current_task = None
    
    def answer_query(self, query: str, context: Dict = None) -> AnalystReport:
        """
        Answer a natural language query about current market/trading state.
        
        Args:
            query: User's question
            context: Relevant system state data
        """
        self.status = "analyzing"
        self.current_task = f"Answering query"
        
        try:
            report = AnalystReport(
                report_id=f"query-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                query_type=AnalystQueryType.MARKET_SUMMARY,
                title=f"Query Response",
            )
            
            context = context or {}
            
            # Parse query intent
            query_lower = query.lower()
            
            if any(w in query_lower for w in ["why", "explain", "reason"]):
                report.summary = self._explain_context(context)
            elif any(w in query_lower for w in ["risk", "exposure", "drawdown"]):
                report.summary = self._assess_risk_context(context)
            elif any(w in query_lower for w in ["position", "trade", "open"]):
                report.summary = self._summarize_positions(context)
            elif any(w in query_lower for w in ["signal", "entry", "buy", "sell"]):
                report.summary = self._summarize_signals(context)
            else:
                report.summary = self._general_analysis(context)
            
            report.details = {"query": query, "context_keys": list(context.keys())}
            report.confidence = 0.70
            
            self._store_report(report)
            return report
            
        except Exception as e:
            logger.error(f"AnalystAgent query error: {e}")
            return AnalystReport(title="Query Error", summary=str(e))
        finally:
            self.status = "idle"
            self.current_task = None
    
    # ===== Private Analysis Methods =====
    
    def _analyze_gann_component(self, gann_data: Dict, signal: Dict) -> Dict:
        """Analyze Gann contribution to the signal."""
        analysis = {
            "contributing_factors": [],
            "support_levels": gann_data.get("support", []),
            "resistance_levels": gann_data.get("resistance", []),
            "time_cycle_alignment": gann_data.get("cycle_alignment", False),
            "angle_confluence": gann_data.get("angle_confluence", 0),
        }
        
        if gann_data.get("sq9_signal"):
            analysis["contributing_factors"].append("Square of 9 level confluence detected")
        if gann_data.get("time_cycle_hit"):
            analysis["contributing_factors"].append("Gann time cycle target reached")
        if gann_data.get("angle_support"):
            analysis["contributing_factors"].append("Price supported by Gann angle")
        
        return analysis
    
    def _analyze_ehlers_component(self, ehlers_data: Dict, signal: Dict) -> Dict:
        """Analyze Ehlers DSP contribution to the signal."""
        analysis = {
            "contributing_factors": [],
            "fisher_value": ehlers_data.get("fisher", 0),
            "cycle_phase": ehlers_data.get("phase", "unknown"),
            "trend_mode": ehlers_data.get("trend_mode", "unknown"),
        }
        
        if ehlers_data.get("fisher_crossover"):
            analysis["contributing_factors"].append("Fisher Transform crossover detected")
        if ehlers_data.get("mama_signal"):
            analysis["contributing_factors"].append("MAMA trend signal active")
        if ehlers_data.get("cycle_bottom"):
            analysis["contributing_factors"].append("Ehlers cycle near bottom")
        
        return analysis
    
    def _analyze_ml_component(self, ml_data: Dict, signal: Dict) -> Dict:
        """Analyze ML model contribution to the signal."""
        return {
            "probability": ml_data.get("probability", 0.5),
            "model_used": ml_data.get("model", "ensemble"),
            "feature_importance": ml_data.get("top_features", []),
            "ensemble_agreement": ml_data.get("agreement", 0),
            "contributing_factors": [
                f"ML probability: {ml_data.get('probability', 0.5):.2%}",
                f"Model: {ml_data.get('model', 'ensemble')}",
            ],
        }
    
    def _check_rule_alignment(self, rule_components: Dict) -> Dict:
        """Check alignment between different rule sources."""
        if not rule_components:
            return {"aligned": False, "agreement_score": 0}
        
        signals = []
        if "gann" in rule_components:
            signals.append(rule_components["gann"].get("direction", "neutral"))
        if "ehlers" in rule_components:
            signals.append(rule_components["ehlers"].get("direction", "neutral"))
        
        if not signals:
            return {"aligned": False, "agreement_score": 0}
        
        # Calculate agreement
        bullish = sum(1 for s in signals if s in ["buy", "bullish", "long"])
        bearish = sum(1 for s in signals if s in ["sell", "bearish", "short"])
        total = len(signals)
        
        agreement = max(bullish, bearish) / total if total > 0 else 0
        direction = "bullish" if bullish > bearish else "bearish" if bearish > bullish else "neutral"
        
        return {
            "aligned": agreement >= 0.6,
            "agreement_score": agreement,
            "dominant_direction": direction,
            "sources_checked": total,
        }
    
    def _build_trade_summary(self, signal: Dict, report: AnalystReport) -> str:
        """Build human-readable trade explanation."""
        parts = []
        symbol = signal.get("symbol", "Unknown")
        direction = signal.get("direction", "N/A")
        
        parts.append(f"📊 Trade Signal: {direction.upper()} {symbol}")
        
        # Gann reasoning
        if report.gann_analysis.get("contributing_factors"):
            parts.append("\n🔷 Gann Analysis:")
            for f in report.gann_analysis["contributing_factors"]:
                parts.append(f"  • {f}")
        
        # Ehlers reasoning
        if report.ehlers_analysis.get("contributing_factors"):
            parts.append("\n📐 Ehlers DSP:")
            for f in report.ehlers_analysis["contributing_factors"]:
                parts.append(f"  • {f}")
        
        # ML reasoning
        if report.ml_analysis.get("contributing_factors"):
            parts.append("\n🤖 ML Confirmation:")
            for f in report.ml_analysis["contributing_factors"]:
                parts.append(f"  • {f}")
        
        return "\n".join(parts)
    
    def _build_market_summary(self, symbol: str, price: float, report: AnalystReport) -> str:
        """Build market condition summary."""
        parts = [f"📈 Market Brief: {symbol}"]
        
        if price:
            parts.append(f"Current Price: ${price:,.2f}")
        
        if report.regime_analysis:
            parts.append(f"Regime: {report.regime_analysis.get('current_regime', 'unknown').title()}")
        
        if report.gann_analysis:
            interp = report.gann_analysis.get("interpretation", "")
            if interp:
                parts.append(f"Gann: {interp}")
        
        if report.ehlers_analysis:
            interp = report.ehlers_analysis.get("interpretation", "")
            if interp:
                parts.append(f"Ehlers: {interp}")
        
        if report.ml_analysis:
            prob = report.ml_analysis.get("direction_probability", 0.5)
            direction = report.ml_analysis.get("predicted_direction", "neutral")
            parts.append(f"ML: {direction.title()} ({prob:.0%} probability)")
        
        return "\n".join(parts)
    
    def _interpret_gann_position(self, price: float, levels: Dict) -> str:
        """Interpret current price position relative to Gann levels."""
        if not price or not levels:
            return "Insufficient data for Gann interpretation"
        
        supports = levels.get("support", [])
        resistances = levels.get("resistance", [])
        
        if supports and resistances:
            nearest_sup = min(supports, key=lambda x: abs(x - price)) if supports else None
            nearest_res = min(resistances, key=lambda x: abs(x - price)) if resistances else None
            
            if nearest_sup and nearest_res:
                sup_dist = abs(price - nearest_sup) / price * 100
                res_dist = abs(nearest_res - price) / price * 100
                
                if sup_dist < 1.0:
                    return f"Price near key Gann support at ${nearest_sup:,.2f} ({sup_dist:.1f}% away)"
                elif res_dist < 1.0:
                    return f"Price testing Gann resistance at ${nearest_res:,.2f} ({res_dist:.1f}% away)"
                else:
                    return f"Price between support ${nearest_sup:,.2f} and resistance ${nearest_res:,.2f}"
        
        return "Gann levels calculated but no key confluence"
    
    def _interpret_ehlers(self, indicators: Dict) -> str:
        """Interpret Ehlers indicator state."""
        phase = indicators.get("cycle_phase", "unknown")
        strength = indicators.get("trend_strength", 0)
        
        if phase == "bullish" and strength > 0.6:
            return "Strong bullish cycle phase with confirmed trend"
        elif phase == "bearish" and strength > 0.6:
            return "Strong bearish cycle phase with confirmed downtrend"
        elif phase == "bullish":
            return "Emerging bullish cycle, trend developing"
        elif phase == "bearish":
            return "Emerging bearish cycle, caution advised"
        else:
            return "Neutral cycle phase, no clear directional bias"
    
    def _calculate_report_confidence(self, report: AnalystReport) -> float:
        """Calculate overall confidence of the report."""
        scores = []
        
        if report.gann_analysis:
            scores.append(0.7 if report.gann_analysis.get("contributing_factors") else 0.3)
        if report.ehlers_analysis:
            scores.append(0.7 if report.ehlers_analysis.get("contributing_factors") else 0.3)
        if report.ml_analysis:
            ml_conf = report.ml_analysis.get("probability", 0.5)
            scores.append(min(1.0, abs(ml_conf - 0.5) * 2 + 0.3))
        
        return np.mean(scores) if scores else 0.5
    
    def _assess_data_quality(self, signal: Dict, rules: Dict, ml: Dict) -> float:
        """Assess quality of input data."""
        quality = 0.5
        if signal:
            quality += 0.1
        if rules:
            quality += 0.2
        if ml:
            quality += 0.2
        return min(1.0, quality)
    
    def _explain_context(self, ctx: Dict) -> str:
        return f"Based on current system state with {len(ctx)} context items loaded."
    
    def _assess_risk_context(self, ctx: Dict) -> str:
        risk = ctx.get("risk", {})
        return f"Current risk state: drawdown={risk.get('drawdown', 'N/A')}, exposure={risk.get('exposure', 'N/A')}"
    
    def _summarize_positions(self, ctx: Dict) -> str:
        positions = ctx.get("positions", [])
        return f"Currently {len(positions)} open positions."
    
    def _summarize_signals(self, ctx: Dict) -> str:
        signals = ctx.get("signals", [])
        return f"Currently {len(signals)} pending signals."
    
    def _general_analysis(self, ctx: Dict) -> str:
        return "System is operating normally. All engines active."
    
    def _store_report(self, report: AnalystReport):
        """Store report in history."""
        self._report_history.append(report)
        if len(self._report_history) > self._max_history:
            self._report_history = self._report_history[-self._max_history:]
        self.last_report = report
        self.tasks_completed += 1
    
    def get_report_history(self, limit: int = 20) -> List[Dict]:
        """Get recent report history."""
        return [r.to_dict() for r in self._report_history[-limit:]]
