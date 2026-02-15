"""
Core Module - Gann Quant AI Trading Engine
Contains all core trading components and analysis engines
"""
from .data_feed import DataFeed
from .gann_engine import GannEngine
from .ehlers_engine import EhlersEngine
from .ehlers_indicators import EhlersIndicators
from .astro_engine import AstroEngine
from .ml_engine import MLEngine
from .risk_manager import RiskManager
from .pattern_recognition import PatternRecognition
from .options_engine import OptionsEngine
from .rr_engine import RREngine
from .cycle_engine import CycleEngine
from .execution_engine import ExecutionEngine
from .order_manager import OrderManager
from .portfolio_manager import PortfolioManager
from .forecasting_engine import ForecastingEngine
from .ath_atl_predictor import ATHATLPredictor
from .mtf_engine import MTFEngine
from .preprocessor import Preprocessor
from .feature_builder import FeatureBuilder
from .fusion_confidence import calculate_fusion_confidence
from .feature_fusion_engine import FeatureFusionEngine, create_fused_features
from .training_pipeline import TrainingPipeline, PredictionService, create_training_pipeline
from .ai_api import ai_api, register_ai_routes

# Production-grade modules
from .signal_engine import AISignalEngine, AISignal, SignalType, get_signal_engine
from .risk_engine import RiskEngine, RiskConfig, RiskCheckResult, get_risk_engine
from .execution_gate import ExecutionGate, TradingMode, ExecutionRequest, get_execution_gate
from .security_manager import SecureVault, AccountManager, get_secure_vault, get_account_manager
from .multi_account_manager import MultiAccountManager, BrokerType, get_multi_account_manager
from .live_execution_engine import LiveExecutionEngine, ExecutionMode, get_execution_engine
from .realtime_data_feed import RealTimeDataFeed, Tick, OHLCV, DataSource, get_data_feed
from .trading_orchestrator import TradingOrchestrator, get_orchestrator
from .trading_journal import TradingJournal, TradeEntry, PerformanceMetrics, get_trading_journal
from .settings_api import settings_api, register_settings_routes
from .market_data_api import market_data_api, register_market_data_routes
from .execution_api import execution_api, register_execution_routes
from .trading_api import trading_api, register_trading_routes

__all__ = [
    'DataFeed',
    'GannEngine',
    'EhlersEngine',
    'EhlersIndicators',
    'AstroEngine',
    'MLEngine',
    'RiskManager',
    'PatternRecognition',
    'OptionsEngine',
    'RREngine',
    'CycleEngine',
    'ExecutionEngine',
    'OrderManager',
    'PortfolioManager',
    'ForecastingEngine',
    'ATHATLPredictor',
    'MTFEngine',
    'Preprocessor',
    'FeatureBuilder',
    'calculate_fusion_confidence',
    # AI Engine modules
    'FeatureFusionEngine',
    'create_fused_features',
    'TrainingPipeline',
    'PredictionService',
    'create_training_pipeline',
    'ai_api',
    'register_ai_routes',
    # Production modules
    'AISignalEngine',
    'AISignal',
    'SignalType',
    'get_signal_engine',
    'RiskEngine',
    'RiskConfig',
    'RiskCheckResult',
    'get_risk_engine',
    'ExecutionGate',
    'TradingMode',
    'ExecutionRequest',
    'get_execution_gate',
    'SecureVault',
    'AccountManager',
    'get_secure_vault',
    'get_account_manager',
    'MultiAccountManager',
    'BrokerType',
    'get_multi_account_manager',
    'LiveExecutionEngine',
    'ExecutionMode',
    'get_execution_engine',
    'RealTimeDataFeed',
    'Tick',
    'OHLCV',
    'DataSource',
    'get_data_feed',
    'TradingOrchestrator',
    'get_orchestrator',
    'TradingJournal',
    'TradeEntry',
    'PerformanceMetrics',
    'get_trading_journal',
    'settings_api',
    'register_settings_routes',
    'market_data_api',
    'register_market_data_routes',
    'execution_api',
    'register_execution_routes',
    'trading_api',
    'register_trading_routes',
]

__version__ = '2.2.0'


