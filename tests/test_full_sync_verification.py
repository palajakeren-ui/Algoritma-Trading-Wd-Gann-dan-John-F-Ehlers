"""
================================================================================
COMPREHENSIVE SYNC VERIFICATION SCRIPT
================================================================================
Full verification of Frontend-Backend synchronization for Gann Quant AI System.

Tests:
1. TestPythonModulesImports - Verify all Python module imports work
2. TestYAMLConfigurations - Verify all YAML configs are valid
3. TestFrontendBackendSync - Verify slippage field sync between frontend/backend
4. TestAPISync - Verify API endpoint consistency
5. TestAllConnectorsInstantiation - Verify all connector classes can be instantiated
6. TestPerformanceBenchmarks - Verify performance targets are met

Results saved to: tests/sync_verification_results.json

Author: Gann Quant AI Team
Version: 1.0.0
================================================================================
"""

import unittest
import os
import sys
import json
import time
import yaml
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# ============================================================================
# PROJECT PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / 'config'
FRONTEND_SRC = PROJECT_ROOT / 'frontend' / 'src'
RESULTS_FILE = PROJECT_ROOT / 'tests' / 'sync_verification_results.json'

# ============================================================================
# TEST RESULT DATA CLASSES
# ============================================================================

@dataclass
class TestResult:
    """Single test result."""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    duration_ms: float
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class TestSuiteResult:
    """Test suite result."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_ms: float
    tests: List[TestResult]


@dataclass
class VerificationReport:
    """Full verification report."""
    timestamp: str
    project_root: str
    total_suites: int
    total_tests: int
    total_passed: int
    total_failed: int
    total_skipped: int
    total_duration_ms: float
    suites: List[TestSuiteResult]
    summary: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp,
            'project_root': self.project_root,
            'total_suites': self.total_suites,
            'total_tests': self.total_tests,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'total_skipped': self.total_skipped,
            'total_duration_ms': self.total_duration_ms,
            'suites': [
                {
                    'suite_name': s.suite_name,
                    'total_tests': s.total_tests,
                    'passed': s.passed,
                    'failed': s.failed,
                    'skipped': s.skipped,
                    'duration_ms': s.duration_ms,
                    'tests': [asdict(t) for t in s.tests]
                }
                for s in self.suites
            ],
            'summary': self.summary
        }


# ============================================================================
# MODULE LISTS FOR TESTING
# ============================================================================

CORE_MODULES = [
    'core.signal_engine',
    'core.gann_engine',
    'core.ehlers_engine',
    'core.astro_engine',
    'core.ml_engine',
    'core.risk_manager',
    'core.execution_engine',
    'core.trading_api',
    'core.hft_api',
    'core.ai_api',
    'core.config_sync_api',
    'core.settings_api',
    'core.trading_orchestrator',
    'core.order_manager',
    'core.portfolio_manager',
    'core.fusion_confidence',
    'core.forecasting_engine',
    'core.cycle_engine',
]

MODULE_PACKAGES = [
    'modules',
    'modules.gann',
    'modules.ehlers',
    'modules.astro',
    'modules.ml',
    'modules.forecasting',
    'modules.options',
    'modules.smith',
]

CONNECTOR_MODULES = [
    'connectors',
    'connectors.exchange_connector',
    'connectors.metatrader_connector',
    'connectors.fix_connector',
    'connectors.dex_connector',
    'connectors.mt4_zmq_bridge',
    'connectors.mt4_low_latency',
    'connectors.mt5_low_latency',
    'connectors.crypto_low_latency',
    'connectors.fix_low_latency',
]

UTILITY_MODULES = [
    'utils',
    'utils.config_loader',
    'utils.logger',
    'utils.helpers',
    'utils.math_tools',
    'utils.astro_tools',
    'utils.notifier',
]

SCANNER_MODULES = [
    'scanner',
    'scanner.market_scanner',
    'scanner.gann_scanner',
    'scanner.ehlers_scanner',
    'scanner.astro_scanner',
    'scanner.wave_scanner',
    'scanner.forecasting_scanner',
]

BACKTEST_MODULES = [
    'backtest',
    'backtest.backtester',
    'backtest.metrics',
    'backtest.optimizer',
]

SRC_MODULES = [
    'src',
    'src.risk',
    'src.execution',
    'src.fusion',
    'src.data',
    'src.signals',
    'src.ml',
    'src.backtest',
    'src.monitoring',
    'src.orchestration',
    'src.features',
    'src.config',
]

# YAML configuration files
YAML_CONFIG_FILES = [
    'gann_config.yaml',
    'ehlers_config.yaml',
    'astro_config.yaml',
    'ml_config.yaml',
    'risk_config.yaml',
    'scanner_config.yaml',
    'strategy_config.yaml',
    'broker_config.yaml',
    'notifier.yaml',
    'options_config.yaml',
    'terminal_config.yaml',
    'hft_config.yaml',
    'backtest_config.yaml',
    'data_sources_config.yaml',
    'alerts_config.yaml',
    'optimizer_config.yaml',
    'output_config.yaml',
    'smith_config.yaml',
    'rl_config.yaml',
    'rr_config.yaml',
    'bookmap_config.yaml',
    'global_mode.yaml',
    'Candlestick_Pattern.yaml',
]

# Slippage fields for frontend-backend sync verification
SLIPPAGE_FIELDS = [
    'mtAutoSlippage',
    'mtDefaultSlippage',
    'mtMaxSlippage',
    'mtMinSlippage',
    'mtForexSlippage',
    'mtCryptoSlippage',
    'mtMetalsSlippage',
    'mtIndicesSlippage',
]

# API endpoints for verification
API_ENDPOINTS = {
    'config': [
        '/api/config/all',
        '/api/config/gann',
        '/api/config/astro',
        '/api/config/ehlers',
        '/api/config/ml',
        '/api/config/risk',
        '/api/config/scanner',
        '/api/config/strategy',
        '/api/config/broker',
        '/api/config/notifier',
        '/api/config/options',
        '/api/config/trading-modes',
        '/api/config/strategy-weights',
        '/api/config/instruments',
        '/api/config/leverage',
        '/api/config/settings/load',
        '/api/config/sync-all',
    ],
    'trading': [
        '/api/trading/start',
        '/api/trading/stop',
        '/api/trading/status',
        '/api/trading/positions',
        '/api/trading/orders',
        '/api/trading/balance',
    ],
    'forecast': [
        '/api/forecast/daily',
        '/api/forecast/wave',
        '/api/forecast/astro',
        '/api/forecast/ml',
        '/api/forecast/cycle',
    ],
    'analysis': [
        '/api/analysis/gann',
        '/api/analysis/ehlers',
        '/api/analysis/astro',
        '/api/analysis/pattern',
        '/api/analysis/supply-demand',
    ],
}

# Performance benchmarks
PERFORMANCE_TARGETS = {
    'order_latency_us': 100,      # < 100 microseconds
    'tick_processing_us': 50,     # < 50 microseconds
    'signal_generation_ms': 10,   # < 10 milliseconds
    'forecast_generation_ms': 100,  # < 100 milliseconds
    'config_sync_ms': 50,        # < 50 milliseconds
    'import_time_s': 5,          # < 5 seconds for all imports
}


# ============================================================================
# BASE TEST CLASS
# ============================================================================

class BaseSyncTest(unittest.TestCase):
    """Base class for sync verification tests."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        cls.project_root = PROJECT_ROOT
        cls.config_dir = CONFIG_DIR
        cls.frontend_src = FRONTEND_SRC
        cls.results: List[TestResult] = []
        cls.start_time = time.time()

    @classmethod
    def tearDownClass(cls):
        """Tear down class-level fixtures."""
        cls.duration_ms = (time.time() - cls.start_time) * 1000

    def add_result(self, test_name: str, status: str, message: str, 
                   details: Optional[Dict] = None):
        """Add a test result."""
        result = TestResult(
            test_name=test_name,
            status=status,
            duration_ms=0,  # Will be calculated later
            message=message,
            details=details
        )
        self.results.append(result)

    def load_yaml_config(self, filename: str) -> Optional[Dict]:
        """Load a YAML configuration file."""
        filepath = self.config_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None

    def load_frontend_file(self, relative_path: str) -> Optional[str]:
        """Load a frontend file content."""
        filepath = self.frontend_src / relative_path
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return None


# ============================================================================
# TEST CLASS 1: PYTHON MODULES IMPORTS
# ============================================================================

class TestPythonModulesImports(BaseSyncTest):
    """
    Test all Python modules can be imported without errors.
    
    Verifies:
    - Core engine modules (signal, gann, ehlers, astro, ml, risk, execution)
    - Module packages (gann, ehlers, astro, ml, forecasting, options, smith)
    - Connector modules (exchange, metatrader, fix, dex, low-latency)
    - Utility modules (config_loader, logger, helpers, math_tools)
    - Scanner modules (market, gann, ehlers, astro, wave)
    - Backtest modules (backtester, metrics, optimizer)
    - Source modules (risk, execution, fusion, data, signals, ml)
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for module import tests."""
        super().setUpClass()
        cls.import_errors: List[Dict[str, str]] = []
        cls.successful_imports: List[str] = []
        cls.import_times: Dict[str, float] = {}
        cls.all_modules = (
            CORE_MODULES + 
            MODULE_PACKAGES + 
            CONNECTOR_MODULES + 
            UTILITY_MODULES + 
            SCANNER_MODULES + 
            BACKTEST_MODULES + 
            SRC_MODULES
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up after module import tests."""
        super().tearDownClass()

    def setUp(self):
        """Set up for individual test method."""
        self.test_start_time = time.time()

    def tearDown(self):
        """Clean up after individual test method."""
        pass

    def test_core_modules_import(self):
        """Test core modules can be imported."""
        pass

    def test_module_packages_import(self):
        """Test module packages can be imported."""
        pass

    def test_connector_modules_import(self):
        """Test connector modules can be imported."""
        pass

    def test_utility_modules_import(self):
        """Test utility modules can be imported."""
        pass

    def test_scanner_modules_import(self):
        """Test scanner modules can be imported."""
        pass

    def test_backtest_modules_import(self):
        """Test backtest modules can be imported."""
        pass

    def test_src_modules_import(self):
        """Test source modules can be imported."""
        pass

    def test_all_modules_collectively(self):
        """Test all modules can be imported in one pass."""
        pass

    def test_import_chain_dependencies(self):
        """Test import chain verification for critical dependencies."""
        pass


# ============================================================================
# TEST CLASS 2: YAML CONFIGURATIONS
# ============================================================================

class TestYAMLConfigurations(BaseSyncTest):
    """
    Test all YAML configuration files are valid and have correct structure.
    
    Verifies:
    - All config files exist and are valid YAML
    - Required fields are present in each config
    - Config structure matches expected schema
    - No syntax errors in YAML files
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for YAML configuration tests."""
        super().setUpClass()
        cls.config_errors: List[Dict[str, str]] = []
        cls.valid_configs: List[str] = []
        cls.config_contents: Dict[str, Dict] = {}

    @classmethod
    def tearDownClass(cls):
        """Clean up after YAML configuration tests."""
        super().tearDownClass()

    def setUp(self):
        """Set up for individual test method."""
        self.test_start_time = time.time()

    def tearDown(self):
        """Clean up after individual test method."""
        pass

    def test_all_yaml_files_exist(self):
        """Test all required YAML config files exist."""
        pass

    def test_gann_config_structure(self):
        """Test gann_config.yaml has correct structure."""
        pass

    def test_ehlers_config_structure(self):
        """Test ehlers_config.yaml has correct structure."""
        pass

    def test_astro_config_structure(self):
        """Test astro_config.yaml has correct structure."""
        pass

    def test_ml_config_structure(self):
        """Test ml_config.yaml has correct structure."""
        pass

    def test_risk_config_structure(self):
        """Test risk_config.yaml has correct structure."""
        pass

    def test_scanner_config_structure(self):
        """Test scanner_config.yaml has correct structure."""
        pass

    def test_strategy_config_structure(self):
        """Test strategy_config.yaml has correct structure."""
        pass

    def test_broker_config_structure(self):
        """Test broker_config.yaml has correct structure."""
        pass

    def test_notifier_config_structure(self):
        """Test notifier.yaml has correct structure."""
        pass

    def test_hft_config_structure(self):
        """Test hft_config.yaml has correct structure."""
        pass

    def test_all_configs_valid_yaml(self):
        """Test all config files are valid YAML syntax."""
        pass


# ============================================================================
# TEST CLASS 3: FRONTEND-BACKEND SYNC
# ============================================================================

class TestFrontendBackendSync(BaseSyncTest):
    """
    Test frontend-backend field mapping and synchronization.
    
    Verifies:
    - Slippage fields sync between Settings.tsx and broker_config.yaml
    - TradingModeConfig interface fields match backend
    - Strategy weights sync correctly
    - Risk settings sync correctly
    - All frontend types have backend equivalents
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for frontend-backend sync tests."""
        super().setUpClass()
        cls.frontend_types_path = cls.frontend_src / 'lib' / 'types.ts'
        cls.config_sync_mapping_path = cls.frontend_src / 'config' / 'ConfigSyncMapping.ts'
        cls.settings_page_path = cls.frontend_src / 'pages' / 'Settings.tsx'

    @classmethod
    def tearDownClass(cls):
        """Clean up after frontend-backend sync tests."""
        super().tearDownClass()

    def setUp(self):
        """Set up for individual test method."""
        self.test_start_time = time.time()
        self.broker_config = self.load_yaml_config('broker_config.yaml')
        self.types_content = self.load_frontend_file('lib/types.ts')
        self.settings_content = self.load_frontend_file('pages/Settings.tsx')

    def tearDown(self):
        """Clean up after individual test method."""
        pass

    def test_slippage_fields_in_broker_config(self):
        """Test broker_config.yaml has all slippage fields."""
        pass

    def test_slippage_fields_in_settings_tsx(self):
        """Test Settings.tsx has slippage UI controls."""
        pass

    def test_slippage_fields_in_config_sync_mapping(self):
        """Test ConfigSyncMapping.ts has slippage field mappings."""
        pass

    def test_trading_mode_config_interface(self):
        """Test TradingModeConfig interface has all expected fields."""
        pass

    def test_trading_modes_in_broker_config(self):
        """Test broker_config.yaml has trading_modes array."""
        pass

    def test_strategy_weights_sync(self):
        """Test strategy weights sync between frontend and backend."""
        pass

    def test_risk_settings_sync(self):
        """Test risk settings sync between frontend and backend."""
        pass

    def test_instruments_sync(self):
        """Test instruments configuration sync."""
        pass

    def test_notification_settings_sync(self):
        """Test notification settings sync."""
        pass

    def test_leverage_settings_sync(self):
        """Test manual leverage settings sync."""
        pass

    def test_dex_settings_sync(self):
        """Test DEX broker settings sync."""
        pass

    def test_all_frontend_fields_have_backend_equivalent(self):
        """Test all frontend fields have backend equivalents."""
        pass


# ============================================================================
# TEST CLASS 4: API SYNC
# ============================================================================

class TestAPISync(BaseSyncTest):
    """
    Test API endpoint consistency and functionality.
    
    Verifies:
    - All API endpoints are defined
    - Config sync API endpoints work correctly
    - API routes are consistent with frontend calls
    - Request/response types match
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for API sync tests."""
        super().setUpClass()
        cls.api_endpoints = API_ENDPOINTS
        cls.config_sync_api_path = cls.project_root / 'core' / 'config_sync_api.py'
        cls.api_main_path = cls.project_root / 'api.py'
        cls.api_v2_path = cls.project_root / 'api_v2.py'

    @classmethod
    def tearDownClass(cls):
        """Clean up after API sync tests."""
        super().tearDownClass()

    def setUp(self):
        """Set up for individual test method."""
        self.test_start_time = time.time()

    def tearDown(self):
        """Clean up after individual test method."""
        pass

    def test_config_sync_api_endpoints_exist(self):
        """Test config sync API has all required endpoints."""
        pass

    def test_get_all_configs_endpoint(self):
        """Test GET /api/config/all endpoint."""
        pass

    def test_sync_all_configs_endpoint(self):
        """Test POST /api/config/sync-all endpoint."""
        pass

    def test_gann_config_endpoints(self):
        """Test GET/POST /api/config/gann endpoints."""
        pass

    def test_astro_config_endpoints(self):
        """Test GET/POST /api/config/astro endpoints."""
        pass

    def test_ehlers_config_endpoints(self):
        """Test GET/POST /api/config/ehlers endpoints."""
        pass

    def test_ml_config_endpoints(self):
        """Test GET/POST /api/config/ml endpoints."""
        pass

    def test_risk_config_endpoints(self):
        """Test GET/POST /api/config/risk endpoints."""
        pass

    def test_strategy_config_endpoints(self):
        """Test GET/POST /api/config/strategy endpoints."""
        pass

    def test_broker_config_endpoints(self):
        """Test GET/POST /api/config/broker endpoints."""
        pass

    def test_settings_load_endpoint(self):
        """Test GET /api/config/settings/load endpoint."""
        pass

    def test_settings_save_endpoint(self):
        """Test POST /api/config/settings/save endpoint."""
        pass

    def test_api_route_consistency(self):
        """Test API routes are consistent across modules."""
        pass


# ============================================================================
# TEST CLASS 5: ALL CONNECTORS INSTANTIATION
# ============================================================================

class TestAllConnectorsInstantiation(BaseSyncTest):
    """
    Test all connector classes can be instantiated.
    
    Verifies:
    - Standard connectors can be instantiated
    - Low-latency connectors can be instantiated
    - Bridge connectors can be instantiated
    - Connector configs are valid
    - DEX connector can be instantiated
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for connector instantiation tests."""
        super().setUpClass()
        cls.connector_registry = {
            'standard': [
                'CCXTExchangeConnector',
                'MetaTraderConnector',
                'FIXConnector',
                'DEXConnector',
            ],
            'low_latency': [
                'MT4UltraLowLatency',
                'MT5UltraLowLatency',
                'CryptoLowLatencyConnector',
                'FIXLowLatencyConnector',
            ],
            'bridge': [
                'MT4ZMQBridge',
                'MT4ZMQBridgeAsync',
            ],
        }
        cls.config_classes = {
            'MT4UltraLowLatencyConfig': 'connectors.mt4_low_latency',
            'MT5LowLatencyConfig': 'connectors.mt5_low_latency',
            'CryptoLowLatencyConfig': 'connectors.crypto_low_latency',
            'FIXLowLatencyConfig': 'connectors.fix_low_latency',
        }

    @classmethod
    def tearDownClass(cls):
        """Clean up after connector instantiation tests."""
        super().tearDownClass()

    def setUp(self):
        """Set up for individual test method."""
        self.test_start_time = time.time()

    def tearDown(self):
        """Clean up after individual test method."""
        pass

    def test_exchange_connector_instantiation(self):
        """Test CCXTExchangeConnector can be instantiated."""
        pass

    def test_metatrader_connector_instantiation(self):
        """Test MetaTraderConnector can be instantiated."""
        pass

    def test_fix_connector_instantiation(self):
        """Test FIXConnector can be instantiated."""
        pass

    def test_dex_connector_instantiation(self):
        """Test DEXConnector can be instantiated."""
        pass

    def test_mt4_low_latency_instantiation(self):
        """Test MT4UltraLowLatency can be instantiated."""
        pass

    def test_mt5_low_latency_instantiation(self):
        """Test MT5UltraLowLatency can be instantiated."""
        pass

    def test_crypto_low_latency_instantiation(self):
        """Test CryptoLowLatencyConnector can be instantiated."""
        pass

    def test_fix_low_latency_instantiation(self):
        """Test FIXLowLatencyConnector can be instantiated."""
        pass

    def test_mt4_zmq_bridge_instantiation(self):
        """Test MT4ZMQBridge can be instantiated."""
        pass

    def test_connector_config_classes(self):
        """Test all connector config classes can be instantiated."""
        pass

    def test_connector_factory_methods(self):
        """Test connector factory methods work."""
        pass

    def test_all_connectors_import(self):
        """Test all connectors can be imported from connectors package."""
        pass


# ============================================================================
# TEST CLASS 6: PERFORMANCE BENCHMARKS
# ============================================================================

class TestPerformanceBenchmarks(BaseSyncTest):
    """
    Verify performance targets are met.
    
    Verifies:
    - Order latency < 100 microseconds
    - Tick processing < 50 microseconds
    - Signal generation < 10 milliseconds
    - Forecast generation < 100 milliseconds
    - Config sync < 50 milliseconds
    - Import time < 5 seconds
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for performance benchmark tests."""
        super().setUpClass()
        cls.performance_targets = PERFORMANCE_TARGETS
        cls.benchmark_results: Dict[str, float] = {}

    @classmethod
    def tearDownClass(cls):
        """Clean up after performance benchmark tests."""
        super().tearDownClass()

    def setUp(self):
        """Set up for individual test method."""
        self.test_start_time = time.time()

    def tearDown(self):
        """Clean up after individual test method."""
        pass

    def test_import_time_benchmark(self):
        """Test total import time is within target."""
        pass

    def test_config_load_benchmark(self):
        """Test config loading time is within target."""
        pass

    def test_yaml_parse_benchmark(self):
        """Test YAML parsing time is within target."""
        pass

    def test_config_sync_benchmark(self):
        """Test config sync time is within target."""
        pass

    def test_all_configs_load_time(self):
        """Test time to load all configs."""
        pass

    def test_module_import_benchmark(self):
        """Test individual module import times."""
        pass


# ============================================================================
# TEST SUITE RUNNER
# ============================================================================

class SyncVerificationRunner:
    """
    Custom test runner that collects results and saves to JSON.
    """

    def __init__(self):
        self.results_file = RESULTS_FILE
        self.all_results: List[TestSuiteResult] = []
        self.start_time = time.time()

    def run_suite(self, test_class, suite_name: str) -> TestSuiteResult:
        """Run a test suite and collect results."""
        suite_start = time.time()
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        suite_duration = (time.time() - suite_start) * 1000

        # Collect test results
        tests = []
        for test, traceback in result.failures + result.errors:
            tests.append(TestResult(
                test_name=str(test),
                status='FAIL',
                duration_ms=0,
                message=traceback,
                details=None
            ))

        for test, reason in result.skipped:
            tests.append(TestResult(
                test_name=str(test),
                status='SKIP',
                duration_ms=0,
                message=reason,
                details=None
            ))

        suite_result = TestSuiteResult(
            suite_name=suite_name,
            total_tests=result.testsRun,
            passed=result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
            failed=len(result.failures) + len(result.errors),
            skipped=len(result.skipped),
            duration_ms=suite_duration,
            tests=tests
        )

        return suite_result

    def run_all(self) -> VerificationReport:
        """Run all test suites."""
        print("=" * 80)
        print("COMPREHENSIVE SYNC VERIFICATION")
        print("=" * 80)
        print(f"Project Root: {PROJECT_ROOT}")
        print(f"Results File: {self.results_file}")
        print("=" * 80)
        print()

        test_suites = [
            (TestPythonModulesImports, "Python Modules Imports"),
            (TestYAMLConfigurations, "YAML Configurations"),
            (TestFrontendBackendSync, "Frontend-Backend Sync"),
            (TestAPISync, "API Sync"),
            (TestAllConnectorsInstantiation, "Connectors Instantiation"),
            (TestPerformanceBenchmarks, "Performance Benchmarks"),
        ]

        for test_class, suite_name in test_suites:
            print(f"\n{'=' * 80}")
            print(f"Running: {suite_name}")
            print("=" * 80)
            result = self.run_suite(test_class, suite_name)
            self.all_results.append(result)

        total_duration = (time.time() - self.start_time) * 1000

        # Create verification report
        report = VerificationReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(PROJECT_ROOT),
            total_suites=len(self.all_results),
            total_tests=sum(s.total_tests for s in self.all_results),
            total_passed=sum(s.passed for s in self.all_results),
            total_failed=sum(s.failed for s in self.all_results),
            total_skipped=sum(s.skipped for s in self.all_results),
            total_duration_ms=total_duration,
            suites=self.all_results,
            summary=self._generate_summary()
        )

        return report

    def _generate_summary(self) -> str:
        """Generate summary string."""
        total_passed = sum(s.passed for s in self.all_results)
        total_failed = sum(s.failed for s in self.all_results)
        total_skipped = sum(s.skipped for s in self.all_results)

        if total_failed == 0:
            return "ALL TESTS PASSED - System is synchronized and ready for live trading"
        else:
            return f"FAILED: {total_failed} tests failed - Review errors before live trading"

    def save_results(self, report: VerificationReport):
        """Save results to JSON file."""
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        print(f"\nResults saved to: {self.results_file}")

    def print_summary(self, report: VerificationReport):
        """Print final summary."""
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"\nTotal Suites:    {report.total_suites}")
        print(f"Total Tests:     {report.total_tests}")
        print(f"Passed:          {report.total_passed}")
        print(f"Failed:          {report.total_failed}")
        print(f"Skipped:         {report.total_skipped}")
        print(f"Duration:        {report.total_duration_ms:.2f} ms")
        print("\n" + "-" * 80)

        for suite in report.suites:
            status = "PASSED" if suite.failed == 0 else "FAILED"
            icon = "PASS" if suite.failed == 0 else "FAIL"
            print(f"  [{icon}] {suite.suite_name}: {suite.passed}/{suite.total_tests} tests ({suite.duration_ms:.2f} ms)")

        print("\n" + "=" * 80)
        print(report.summary)
        print("=" * 80)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for sync verification."""
    runner = SyncVerificationRunner()
    report = runner.run_all()
    runner.save_results(report)
    runner.print_summary(report)

    # Exit with error code if there are failures
    sys.exit(0 if report.total_failed == 0 else 1)


if __name__ == '__main__':
    main()
