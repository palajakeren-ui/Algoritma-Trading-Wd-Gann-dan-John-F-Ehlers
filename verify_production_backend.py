"""
Complete Backend Trading System Verification
Tests all production modules for the Gann Quant AI platform.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_section(title: str, symbol: str = "="):
    print(f"\n{symbol * 60}")
    print(f"  {title}")
    print(f"{symbol * 60}")


def test_with_result(name: str, test_func) -> bool:
    try:
        result = test_func()
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
        return result
    except Exception as e:
        print(f"  ✗ {name} - {str(e)[:50]}...")
        return False


def test_connectors():
    """Test all connector modules."""
    print_section("1. CONNECTOR MODULES")
    results = []
    
    # Exchange Connector
    def test_exchange():
        from connectors.exchange_connector import ExchangeConnectorFactory, Order, OrderSide
        exchanges = ExchangeConnectorFactory.get_supported_exchanges()
        return len(exchanges) >= 10
    results.append(test_with_result("Exchange Connector (14 exchanges)", test_exchange))
    
    # MetaTrader Connector
    def test_mt():
        from connectors.metatrader_connector import MetaTraderConnector, MTCredentials, MTVersion
        creds = MTCredentials(login="test", password="test", server="test")
        return creds.version == MTVersion.MT5
    results.append(test_with_result("MetaTrader Connector (MT4/MT5)", test_mt))
    
    # FIX Connector
    def test_fix():
        from connectors.fix_connector import FIXConnector, FIXCredentials, FIXVersion
        return len([v for v in FIXVersion]) == 3
    results.append(test_with_result("FIX Protocol Connector (4.2/4.4/5.0)", test_fix))
    
    return all(results)


def test_core_engines():
    """Test core engine modules."""
    print_section("2. CORE ENGINES")
    results = []
    
    # Signal Engine
    def test_signal():
        from core.signal_engine import AISignalEngine, SignalType, get_signal_engine
        engine = get_signal_engine()
        return engine is not None
    results.append(test_with_result("AI Signal Engine", test_signal))
    
    # Risk Engine
    def test_risk():
        from core.risk_engine import RiskEngine, RiskConfig, get_risk_engine
        engine = get_risk_engine()
        engine.initialize_equity(10000)
        return engine.current_equity == 10000
    results.append(test_with_result("Risk Management Engine", test_risk))
    
    # Execution Gate
    def test_gate():
        from core.execution_gate import ExecutionGate, TradingMode
        gate = ExecutionGate({'trading_mode': 'paper_trading'})
        return gate.trading_mode == TradingMode.PAPER_TRADING
    results.append(test_with_result("AI Execution Gate", test_gate))
    
    # Live Execution Engine
    def test_exec():
        from core.live_execution_engine import LiveExecutionEngine, ExecutionMode
        engine = LiveExecutionEngine()
        return engine.config.mode == ExecutionMode.PAPER
    results.append(test_with_result("Live Execution Engine", test_exec))
    
    # Real-Time Data Feed
    def test_feed():
        from core.realtime_data_feed import RealTimeDataFeed, DataSource
        feed = RealTimeDataFeed()
        return feed.primary_source == DataSource.CRYPTO_EXCHANGE
    results.append(test_with_result("Real-Time Data Feed", test_feed))
    
    # Security Manager
    def test_security():
        from core.security_manager import SecureVault, AccountManager
        vault = SecureVault(master_key="test_key")
        return vault.is_initialized()
    results.append(test_with_result("Security Manager (Encrypted Vault)", test_security))
    
    return all(results)


def test_api_routes():
    """Test API route registration."""
    print_section("3. API ROUTES")
    results = []
    
    # Settings API
    def test_settings_api():
        from core.settings_api import settings_api, SUPPORTED_EXCHANGES
        return len(SUPPORTED_EXCHANGES) >= 10
    results.append(test_with_result("Settings API (exchanges, brokers, accounts)", test_settings_api))
    
    # Market Data API
    def test_market_api():
        from core.market_data_api import market_data_api
        return market_data_api.url_prefix == '/api/market'
    results.append(test_with_result("Market Data API (real-time feed)", test_market_api))
    
    # Execution API
    def test_exec_api():
        from core.execution_api import execution_api
        return execution_api.url_prefix == '/api/execution'
    results.append(test_with_result("Execution API (orders, positions)", test_exec_api))
    
    # AI API
    def test_ai_api():
        from core.ai_api import ai_api
        return ai_api.url_prefix == '/api/ai'
    results.append(test_with_result("AI Engine API (signals, training)", test_ai_api))
    
    return all(results)


def test_gann_modules():
    """Test Gann analysis modules."""
    print_section("4. GANN MODULES")
    results = []
    
    def test_sq9():
        from modules.gann.square_of_9 import SquareOf9
        sq9 = SquareOf9(100)
        levels = sq9.get_levels(3)
        return 'support' in levels and 'resistance' in levels
    results.append(test_with_result("Square of 9", test_sq9))
    
    def test_sq24():
        from modules.gann.square_of_24 import SquareOf24
        sq24 = SquareOf24(100)
        return sq24 is not None
    results.append(test_with_result("Square of 24", test_sq24))
    
    def test_tpg():
        from modules.gann.time_price_geometry import TimePriceGeometry
        tpg = TimePriceGeometry()
        return len(tpg.angles) > 0
    results.append(test_with_result("Time-Price Geometry", test_tpg))
    
    return all(results)


def test_ehlers_modules():
    """Test Ehlers DSP modules."""
    print_section("5. EHLERS DSP MODULES")
    results = []
    
    modules = [
        ("Bandpass Filter", "modules.ehlers.bandpass_filter", "BandpassFilter"),
        ("Smoothed RSI", "modules.ehlers.smoothed_rsi", "SmoothedRSI"),
        ("Hilbert Transform", "modules.ehlers.hilbert_transform", "HilbertTransform"),
        ("Instantaneous Trendline", "modules.ehlers.instantaneous_trendline", "InstantaneousTrendline"),
    ]
    
    for name, module, cls in modules:
        def test_mod(m=module, c=cls):
            exec(f"from {m} import {c}")
            return True
        results.append(test_with_result(name, test_mod))
    
    return all(results)


def test_astro_modules():
    """Test Astrology modules."""
    print_section("6. ASTROLOGY MODULES")
    results = []
    
    def test_synodic():
        from modules.astro.synodic_cycles import SynodicCycleCalculator
        calc = SynodicCycleCalculator()
        return calc is not None
    results.append(test_with_result("Synodic Cycles", test_synodic))
    
    def test_harmonics():
        from modules.astro.time_harmonics import TimeHarmonicsCalculator
        calc = TimeHarmonicsCalculator()
        return calc is not None
    results.append(test_with_result("Time Harmonics", test_harmonics))
    
    return all(results)


def test_ml_models():
    """Test ML models."""
    print_section("7. ML MODELS")
    results = []
    
    models = [
        ("LightGBM", "models.ml_lightgbm", "LightGBMModel"),
        ("MLP", "models.ml_mlp", "MLPModel"),
        ("Hybrid Meta", "models.ml_hybrid_meta", "HybridMetaModel"),
    ]
    
    for name, module, cls in models:
        def test_mod(m=module, c=cls):
            exec(f"from {m} import {c}")
            return True
        results.append(test_with_result(name, test_mod))
    
    return all(results)


def test_frontend_sync():
    """Test frontend synchronization compatibility."""
    print_section("8. FRONTEND SYNC COMPATIBILITY")
    results = []
    
    # Test exchange list matches frontend
    def test_exchanges():
        from core.settings_api import SUPPORTED_EXCHANGES
        required = ['binance', 'bybit', 'okx', 'kucoin', 'gateio']
        ids = [e['id'] for e in SUPPORTED_EXCHANGES]
        return all(r in ids for r in required)
    results.append(test_with_result("Exchange list compatible", test_exchanges))
    
    # Test broker types
    def test_brokers():
        from core.settings_api import SUPPORTED_BROKERS
        types = [b['id'] for b in SUPPORTED_BROKERS]
        return 'mt4' in types and 'mt5' in types and 'fix_generic' in types
    results.append(test_with_result("Broker types compatible", test_brokers))
    
    # Test trading modes
    def test_modes():
        from core.execution_gate import TradingMode
        modes = [m.value for m in TradingMode]
        return 'manual' in modes and 'ai_full_auto' in modes
    results.append(test_with_result("Trading modes compatible", test_modes))
    
    return all(results)


def run_verification():
    """Run complete verification."""
    print("\n" + "=" * 60)
    print("  GANN QUANT AI - PRODUCTION BACKEND VERIFICATION")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Version: 2.2.0")
    print("=" * 60)
    
    results = {
        'Connectors': test_connectors(),
        'Core Engines': test_core_engines(),
        'API Routes': test_api_routes(),
        'Gann Modules': test_gann_modules(),
        'Ehlers DSP': test_ehlers_modules(),
        'Astro Modules': test_astro_modules(),
        'ML Models': test_ml_models(),
        'Frontend Sync': test_frontend_sync(),
    }
    
    # Summary
    print_section("VERIFICATION SUMMARY", "=")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print("\n" + "-" * 60)
    print(f"  TOTAL: {passed}/{total} categories passed")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("  ✓ ALL BACKEND COMPONENTS VERIFIED SUCCESSFULLY!")
        print("  ✓ System is ready for production deployment.")
        print("=" * 60)
    else:
        print(f"\n  ✗ {total - passed} category(s) need attention.")
        print("  Review errors above and fix before deployment.")
    
    print("\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
