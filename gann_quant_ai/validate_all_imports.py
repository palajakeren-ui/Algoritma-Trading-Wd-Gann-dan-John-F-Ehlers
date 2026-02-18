"""Full system import validation."""
import sys
import importlib

sys.path.insert(0, ".")

test_modules = [
    # core/
    "core", "core.astro_engine", "core.gann_engine", "core.ehlers_engine",
    "core.signal_engine", "core.risk_engine", "core.execution_engine",
    "core.ml_engine", "core.data_feed", "core.trading_orchestrator",
    "core.forecasting_engine", "core.feature_builder",
    "core.cycle_engine", "core.pattern_recognition",
    "core.hft_engine", "core.preprocessor",
    # modules/
    "modules", "modules.gann", "modules.ehlers", "modules.astro",
    "modules.gann.gann_wave", "modules.gann.gann_angles", "modules.gann.square_of_9",
    "modules.gann.square_of_144", "modules.gann.square_of_360",
    "modules.gann.gann_time", "modules.gann.gann_forecasting",
    "modules.gann.spiral_gann", "modules.gann.time_price_geometry",
    "modules.ehlers.super_smoother", "modules.ehlers.cyber_cycle",
    "modules.ehlers.bandpass_filter", "modules.ehlers.roofing_filter",
    "modules.ehlers.fisher_transform", "modules.ehlers.hilbert_transform",
    "modules.ehlers.mama", "modules.ehlers.sinewave_indicator",
    "modules.ehlers.smoothed_rsi", "modules.ehlers.decycler",
    "modules.ehlers.instantaneous_trendline",
    "modules.astro.astro_ephemeris", "modules.astro.planetary_aspects",
    "modules.astro.retrograde_cycles", "modules.astro.synodic_cycles",
    "modules.astro.time_harmonics", "modules.astro.zodiac_degrees",
    "modules.forecasting", "modules.forecasting.gann_forecast_daily",
    "modules.forecasting.gann_wave_projection",
    "modules.forecasting.astro_cycle_projection",
    "modules.ml", "modules.ml.features", "modules.ml.models",
    "modules.ml.predictor", "modules.ml.trainer",
    # connectors/
    "connectors", "connectors.exchange_connector",
    "connectors.metatrader_connector", "connectors.dex_connector",
    # backtest/
    "backtest", "backtest.backtester", "backtest.metrics", "backtest.optimizer",
    "backtest.forecasting_evaluator",
    # models/
    "models", "models.ml_randomforest", "models.ml_xgboost",
    "models.ml_lstm", "models.ml_ensemble", "models.ml_lightgbm",
    "models.ml_mlp", "models.ml_transformer",
    # strategies/
    "strategies", "strategies.base_strategy",
    "strategies.gann_strategy", "strategies.trend_strategy",
    # utils/
    "utils", "utils.config_loader", "utils.helpers",
    "utils.math_tools", "utils.logger",
    # scanner/
    "scanner", "scanner.market_scanner", "scanner.gann_scanner",
    "scanner.ehlers_scanner", "scanner.astro_scanner",
    "scanner.wave_scanner", "scanner.hybrid_scanner",
    # monitoring/
    "monitoring.alert_manager", "monitoring.dashboard_metrics",
    "monitoring.latency_monitor",
    # indicators/
    "indicators.sacred_math_indicators", "indicators.wave_indicators",
    # router/
    "router", "router.strategy_router",
    # agent/
    "agent", "agent.agent_orchestrator", "agent.analyst_agent",
    # src/ (institutional layer)
    "src.data.validator", "src.data.cleaner", "src.data.session_controller",
    "src.risk.cvar", "src.risk.monte_carlo", "src.risk.circuit_breaker",
    "src.risk.drawdown_protector", "src.risk.pre_trade_check",
    "src.risk.position_sizer", "src.risk.portfolio_risk",
    "src.execution.slippage_model", "src.execution.retry_engine",
    "src.execution.duplicate_guard", "src.execution.latency_logger",
    "src.execution.order_router",
    "src.fusion.regime_detector", "src.fusion.adaptive_weighting",
    "src.ml.walk_forward", "src.ml.drift_detector",
    "src.monitoring.trade_journal",
    "src.features.gann_features", "src.features.ehlers_features",
    "src.features.technical_features", "src.features.feature_pipeline",
    "src.signals.signal_generator", "src.signals.confidence_calibrator",
    "src.backtest.event_backtester", "src.backtest.performance_analyzer",
    "src.orchestration.mode_controller", "src.orchestration.trading_loop",
    "src.config.production_config",
]

ok = []
fail = []

for mod in test_modules:
    try:
        importlib.import_module(mod)
        ok.append(mod)
    except Exception as e:
        err_msg = str(e).split("\n")[0][:100]
        fail.append((mod, err_msg))

print(f"PASSED: {len(ok)}/{len(test_modules)}")
print(f"FAILED: {len(fail)}/{len(test_modules)}")
print()

if fail:
    print("=== FAILURES ===")
    for mod, err in fail:
        print(f"  X {mod}")
        print(f"    -> {err}")
    print()

print("=== PASSED ===")
for m in ok:
    print(f"  OK {m}")
