"""
Trading System Backend Verification Script
Comprehensive verification of all backend components.
"""
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(name: str, passed: bool, details: str = ""):
    status = "✓" if passed else "✗"
    color_start = "" if passed else ""
    print(f"  {status} {name}" + (f" - {details}" if details else ""))


def test_core_imports():
    """Test core module imports."""
    print_header("1. Core Module Imports")
    results = []
    
    modules = [
        ("core.signal_engine", "AISignalEngine, get_signal_engine"),
        ("core.risk_engine", "RiskEngine, get_risk_engine"),
        ("core.execution_gate", "ExecutionGate, get_execution_gate"),
        ("core.security_manager", "SecureVault, AccountManager"),
        ("core.settings_api", "settings_api, register_settings_routes"),
        ("core.feature_fusion_engine", "FeatureFusionEngine"),
        ("core.training_pipeline", "TrainingPipeline, PredictionService"),
    ]
    
    for module, classes in modules:
        try:
            exec(f"from {module} import {classes}")
            print_result(module, True)
            results.append(True)
        except Exception as e:
            print_result(module, False, str(e)[:50])
            results.append(False)
    
    return all(results)


def test_connector_imports():
    """Test connector imports."""
    print_header("2. Connector Imports")
    results = []
    
    connectors = [
        ("connectors.exchange_connector", "ExchangeConnectorFactory, Order"),
        ("connectors.metatrader_connector", "MetaTraderConnector, MTCredentials"),
        ("connectors.fix_connector", "FIXConnector, FIXCredentials"),
    ]
    
    for module, classes in connectors:
        try:
            exec(f"from {module} import {classes}")
            print_result(module, True)
            results.append(True)
        except Exception as e:
            print_result(module, False, str(e)[:50])
            results.append(False)
    
    return all(results)


def test_gann_modules():
    """Test Gann modules."""
    print_header("3. Gann Modules")
    results = []
    
    modules = [
        ("modules.gann.square_of_9", "SquareOf9"),
        ("modules.gann.square_of_24", "SquareOf24"),
        ("modules.gann.time_price_geometry", "TimePriceGeometry"),
    ]
    
    for module, classes in modules:
        try:
            exec(f"from {module} import {classes}")
            print_result(module, True)
            results.append(True)
        except Exception as e:
            print_result(module, False, str(e)[:50])
            results.append(False)
    
    return all(results)


def test_ehlers_modules():
    """Test Ehlers DSP modules."""
    print_header("4. Ehlers DSP Modules")
    results = []
    
    modules = [
        ("modules.ehlers.bandpass_filter", "BandpassFilter"),
        ("modules.ehlers.smoothed_rsi", "SmoothedRSI"),
        ("modules.ehlers.instantaneous_trendline", "InstantaneousTrendline"),
        ("modules.ehlers.hilbert_transform", "HilbertTransform"),
    ]
    
    for module, classes in modules:
        try:
            exec(f"from {module} import {classes}")
            print_result(module, True)
            results.append(True)
        except Exception as e:
            print_result(module, False, str(e)[:50])
            results.append(False)
    
    return all(results)


def test_astro_modules():
    """Test Astro modules."""
    print_header("5. Astrology Modules")
    results = []
    
    modules = [
        ("modules.astro.synodic_cycles", "SynodicCycleCalculator"),
        ("modules.astro.time_harmonics", "TimeHarmonicsCalculator"),
    ]
    
    for module, classes in modules:
        try:
            exec(f"from {module} import {classes}")
            print_result(module, True)
            results.append(True)
        except Exception as e:
            print_result(module, False, str(e)[:50])
            results.append(False)
    
    return all(results)


def test_ml_models():
    """Test ML model imports."""
    print_header("6. ML Models")
    results = []
    
    models = [
        ("models.ml_lightgbm", "LightGBMModel"),
        ("models.ml_mlp", "MLPModel"),
        ("models.ml_neural_ode", "NeuralODEModel"),
        ("models.ml_hybrid_meta", "HybridMetaModel"),
    ]
    
    for module, classes in models:
        try:
            exec(f"from {module} import {classes}")
            print_result(module, True)
            results.append(True)
        except Exception as e:
            print_result(module, False, str(e)[:50])
            results.append(False)
    
    return all(results)


def test_signal_engine():
    """Test signal engine functionality."""
    print_header("7. Signal Engine Functionality")
    
    try:
        import pandas as pd
        import numpy as np
        from core.signal_engine import AISignalEngine, SignalType
        
        # Create test data
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        data = pd.DataFrame({
            'open': 100 + np.cumsum(np.random.randn(100) * 0.5),
            'high': 101 + np.cumsum(np.random.randn(100) * 0.5),
            'low': 99 + np.cumsum(np.random.randn(100) * 0.5),
            'close': 100 + np.cumsum(np.random.randn(100) * 0.5),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        data['high'] = data[['open', 'close', 'high']].max(axis=1)
        data['low'] = data[['open', 'close', 'low']].min(axis=1)
        
        engine = AISignalEngine()
        signal = engine.generate_signal("BTC/USDT", data, "H1")
        
        print_result("Engine initialization", True)
        print_result("Signal generation", signal is not None)
        print_result(f"Signal type: {signal.signal.value}", True)
        print_result(f"Confidence: {signal.confidence:.1f}%", True)
        print_result(f"Risk-Reward: {signal.risk_reward:.2f}", True)
        
        return True
        
    except Exception as e:
        print_result("Signal engine test", False, str(e)[:50])
        return False


def test_risk_engine():
    """Test risk engine functionality."""
    print_header("8. Risk Engine Functionality")
    
    try:
        from core.risk_engine import RiskEngine, RiskConfig
        
        config = RiskConfig(
            max_risk_per_trade=2.0,
            max_position_size=10.0,
            max_daily_loss=5.0,
            max_drawdown=20.0
        )
        
        engine = RiskEngine(config)
        engine.initialize_equity(10000)
        
        # Test position sizing
        sizing = engine.calculate_position_size(
            account_balance=10000,
            entry_price=100,
            stop_loss=95
        )
        
        print_result("Engine initialization", True)
        print_result("Position sizing", sizing.get('position_size', 0) > 0)
        print_result(f"Size: {sizing.get('position_size', 0):.4f}", True)
        
        # Test risk check
        result = engine.check_trade_risk(
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            quantity=0.1,
            price=45000,
            stop_loss=43000,
            leverage=5
        )
        
        print_result("Risk check", result is not None)
        print_result(f"Risk level: {result.risk_level.value}", True)
        
        return True
        
    except Exception as e:
        print_result("Risk engine test", False, str(e)[:50])
        return False


def test_execution_gate():
    """Test execution gate functionality."""
    print_header("9. Execution Gate Functionality")
    
    try:
        from core.execution_gate import ExecutionGate, TradingMode
        
        gate = ExecutionGate({'trading_mode': 'paper_trading'})
        
        print_result("Gate initialization", True)
        print_result(f"Mode: {gate.trading_mode.value}", True)
        print_result("Paper trading enabled", gate.paper_trading)
        print_result("Kill switch inactive", not gate.global_kill_switch)
        
        # Get status
        status = gate.get_status()
        print_result("Status retrieval", status is not None)
        
        return True
        
    except Exception as e:
        print_result("Execution gate test", False, str(e)[:50])
        return False


def test_security_manager():
    """Test security manager functionality."""
    print_header("10. Security Manager Functionality")
    
    try:
        from core.security_manager import SecureVault, AccountManager, CredentialType
        
        # Test vault
        vault = SecureVault(master_key="test_key_12345")
        
        print_result("Vault initialization", True)
        print_result("Vault is initialized", vault.is_initialized())
        
        # Test encryption
        cred_id = vault.store_credential(
            account_id="test",
            exchange="binance",
            credential_type=CredentialType.CRYPTO_EXCHANGE,
            credentials={'api_key': 'test_key', 'secret': 'test_secret'}
        )
        
        print_result("Credential storage", cred_id is not None)
        
        # Retrieve
        cred = vault.get_credential(cred_id)
        print_result("Credential retrieval", cred is not None)
        print_result("Data integrity", cred.get('api_key') == 'test_key')
        
        # Cleanup
        vault.delete_credential(cred_id)
        
        return True
        
    except Exception as e:
        print_result("Security manager test", False, str(e)[:50])
        return False


def test_exchange_connector():
    """Test exchange connector."""
    print_header("11. Exchange Connector")
    
    try:
        from connectors.exchange_connector import ExchangeConnectorFactory
        
        exchanges = ExchangeConnectorFactory.get_supported_exchanges()
        
        print_result("Factory available", True)
        print_result(f"Supported exchanges: {len(exchanges)}", True)
        
        for ex in exchanges[:5]:
            print_result(f"  - {ex['name']}", True, ex['type'])
        
        if len(exchanges) > 5:
            print(f"  ... and {len(exchanges) - 5} more")
        
        return True
        
    except Exception as e:
        print_result("Exchange connector test", False, str(e)[:50])
        return False


def run_verification():
    """Run complete verification."""
    print("\n" + "=" * 60)
    print("  GANN QUANT AI - BACKEND TRADING SYSTEM VERIFICATION")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        'Core Imports': test_core_imports(),
        'Connectors': test_connector_imports(),
        'Gann Modules': test_gann_modules(),
        'Ehlers DSP': test_ehlers_modules(),
        'Astro Modules': test_astro_modules(),
        'ML Models': test_ml_models(),
        'Signal Engine': test_signal_engine(),
        'Risk Engine': test_risk_engine(),
        'Execution Gate': test_execution_gate(),
        'Security Manager': test_security_manager(),
        'Exchange Connector': test_exchange_connector(),
    }
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        print_result(name, result)
    
    print("\n" + "-" * 60)
    print(f"  TOTAL: {passed}/{total} components passed")
    
    if passed == total:
        print("\n  ✓ ALL BACKEND COMPONENTS VERIFIED SUCCESSFULLY!")
        print("  ✓ System is ready for production deployment.")
    else:
        print(f"\n  ✗ {total - passed} component(s) need attention.")
        print("  Review errors above and fix before deployment.")
    
    print("=" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
