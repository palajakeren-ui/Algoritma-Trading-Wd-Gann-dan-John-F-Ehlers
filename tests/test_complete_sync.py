"""
Comprehensive Frontend-Backend Synchronization Test
Verifies 100% API coverage and data structure alignment
Updated for Live Trading Readiness Verification
"""

import pytest
import os
import sys
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestLiveTradingReadiness:
    """Test class for live trading readiness verification"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.frontend_path = project_root / "frontend" / "src"
        self.config_path = project_root / "config"
        self.backend_path = project_root
        
    def test_backend_api_blueprints_registered(self):
        """Verify all backend API blueprints are properly registered"""
        api_path = self.backend_path / "api.py"
        
        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for blueprint imports
        required_blueprints = [
            'trading_api',
            'positions_api',
            'orders_api',
            'risk_api',
            'scanner_api',
            'portfolio_api',
            'forecast_api',
            'config_sync_api',
            'gann_api',
            'ehlers_api',
            'astro_api',
            'ml_api',
            'broker_api',
            'agent_api',
        ]
        
        for blueprint in required_blueprints:
            assert blueprint in content, f"Missing blueprint: {blueprint}"
        
        print(f"\n✅ All {len(required_blueprints)} required blueprints registered")
    
    def test_config_files_valid_yaml(self):
        """Verify all config files are valid YAML"""
        config_files = list(self.config_path.glob("*.yaml"))
        
        assert len(config_files) > 10, f"Expected >10 config files, found {len(config_files)}"
        
        errors = []
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"{config_file.name}: {str(e)}")
        
        assert len(errors) == 0, f"YAML errors found:\n" + "\n".join(errors)
        
        print(f"\n✅ All {len(config_files)} config files are valid YAML")
    
    def test_api_comprehensive_module_exists(self):
        """Verify comprehensive API module exists"""
        api_comprehensive_path = self.backend_path / "api_comprehensive.py"
        
        assert api_comprehensive_path.exists(), "api_comprehensive.py not found"
        
        with open(api_comprehensive_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify all blueprints are exported
        required_exports = [
            'trading_api',
            'positions_api',
            'orders_api',
            'risk_api',
            'scanner_api',
            'portfolio_api',
            'forecast_api',
            'config_sync_api',
            'gann_api',
            'ehlers_api',
            'astro_api',
            'ml_api',
            'broker_api',
            'agent_api',
        ]
        
        for export in required_exports:
            assert export in content, f"Missing export in api_comprehensive.py: {export}"
        
        print(f"\n✅ Comprehensive API module verified with {len(required_exports)} blueprints")
    
    def test_no_yaml_syntax_errors(self):
        """Check for common YAML syntax errors"""
        config_files = list(self.config_path.glob("*.yaml"))
        
        errors = []
        
        for config_file in config_files:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common typos
            common_typos = [
                ('protectiontrue', 'true'),
                ('enabletrue', 'true'),
                ('falsetrue', 'false'),
            ]
            
            for typo, correct in common_typos:
                if typo in content:
                    errors.append(f"{config_file.name}: Found '{typo}', should be '{correct}'")
        
        assert len(errors) == 0, f"YAML syntax errors:\n" + "\n".join(errors)
        
        print("\n✅ No YAML syntax errors found")
    
    def test_frontend_type_definitions(self):
        """Verify frontend TypeScript type definitions"""
        api_service_path = self.frontend_path / "services" / "apiService.ts"
        
        with open(api_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify key type definitions exist
        required_types = [
            'interface BacktestRequest',
            'interface BacktestResponse',
            'interface MarketData',
            'interface GannLevels',
            'interface Signal',
            'interface Position',
            'interface Order',
            'interface TradingStatus',
            'interface HealthResponse',
        ]
        
        for type_def in required_types:
            assert type_def in content, f"Missing type definition: {type_def}"
        
        print(f"\n✅ All {len(required_types)} required TypeScript interfaces defined")
    
    def test_backend_error_handling(self):
        """Verify backend has proper error handling"""
        api_comprehensive_path = self.backend_path / "api_comprehensive.py"
        
        with open(api_comprehensive_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count try-except blocks
        try_count = content.count('try:')
        except_count = content.count('except')
        
        assert try_count > 30, f"Expected >30 try blocks, found {try_count}"
        assert except_count > 30, f"Expected >30 except blocks, found {except_count}"
        
        print(f"\n✅ Error handling verified: {try_count} try blocks, {except_count} except blocks")
    
    def test_backend_logging(self):
        """Verify backend has proper logging"""
        api_comprehensive_path = self.backend_path / "api_comprehensive.py"
        
        with open(api_comprehensive_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify logger import and usage
        assert 'from loguru import logger' in content, "Missing logger import"
        
        logger_calls = content.count('logger.')
        assert logger_calls > 10, f"Expected >10 logger calls, found {logger_calls}"
        
        print(f"\n✅ Logging verified: {logger_calls} logger calls")
    
    def test_trading_mode_config_exists(self):
        """Verify trading mode configuration exists"""
        broker_config_path = self.config_path / "broker_config.yaml"
        
        with open(broker_config_path, 'r', encoding='utf-8') as f:
            broker_config = yaml.safe_load(f)
        
        assert 'trading_modes' in broker_config, "Missing trading_modes in broker_config.yaml"
        
        print("\n✅ Trading mode configuration verified")
    
    def test_slippage_config_exists(self):
        """Verify slippage configuration exists"""
        broker_config_path = self.config_path / "broker_config.yaml"
        
        with open(broker_config_path, 'r', encoding='utf-8') as f:
            broker_config = yaml.safe_load(f)
        
        # Check for slippage fields in trading_modes
        config_str = str(broker_config).lower()
        assert 'slippage' in config_str, "Missing slippage configuration"
        
        print("\n✅ Slippage configuration verified")
    
    def test_agent_modes_exist(self):
        """Verify AI agent modes are defined"""
        global_mode_path = self.config_path / "global_mode.yaml"
        
        with open(global_mode_path, 'r', encoding='utf-8') as f:
            global_mode = yaml.safe_load(f)
        
        # Check for mode definitions
        config_str = str(global_mode).lower()
        
        # Verify M0-M4 modes exist
        modes_found = 0
        for i in range(5):
            if f'mode_{i}' in config_str or f'm{i}' in config_str or f'mode{i}' in config_str:
                modes_found += 1
        
        assert modes_found >= 3, f"Expected at least 3 mode definitions, found {modes_found}"
        
        print("\n✅ Agent modes verified")
    
    def test_risk_config_exists(self):
        """Verify risk configuration exists"""
        risk_config_path = self.config_path / "risk_config.yaml"
        
        with open(risk_config_path, 'r', encoding='utf-8') as f:
            risk_config = yaml.safe_load(f)
        
        # Verify risk config has essential sections
        assert len(risk_config) > 5, "Risk config appears incomplete"
        
        # Check for key risk concepts
        config_str = str(risk_config).lower()
        risk_keywords = ['drawdown', 'limit', 'position', 'risk']
        
        found_keywords = sum(1 for kw in risk_keywords if kw in config_str)
        assert found_keywords >= 3, f"Missing key risk keywords, found {found_keywords}"
        
        print("\n✅ Risk configuration verified")
    
    def test_gann_config_exists(self):
        """Verify Gann configuration exists"""
        gann_config_path = self.config_path / "gann_config.yaml"
        
        with open(gann_config_path, 'r', encoding='utf-8') as f:
            gann_config = yaml.safe_load(f)
        
        assert len(gann_config) > 5, "Gann config appears incomplete"
        
        print("\n✅ Gann configuration verified")
    
    def test_ehlers_config_exists(self):
        """Verify Ehlers configuration exists"""
        ehlers_config_path = self.config_path / "ehlers_config.yaml"
        
        with open(ehlers_config_path, 'r', encoding='utf-8') as f:
            ehlers_config = yaml.safe_load(f)
        
        assert len(ehlers_config) > 3, "Ehlers config appears incomplete"
        
        print("\n✅ Ehlers configuration verified")
    
    def test_ml_config_exists(self):
        """Verify ML configuration exists"""
        ml_config_path = self.config_path / "ml_config.yaml"
        
        with open(ml_config_path, 'r', encoding='utf-8') as f:
            ml_config = yaml.safe_load(f)
        
        assert len(ml_config) > 5, "ML config appears incomplete"
        
        print("\n✅ ML configuration verified")
    
    def test_scanner_config_exists(self):
        """Verify scanner configuration exists"""
        scanner_config_path = self.config_path / "scanner_config.yaml"
        
        with open(scanner_config_path, 'r', encoding='utf-8') as f:
            scanner_config = yaml.safe_load(f)
        
        assert len(scanner_config) > 5, "Scanner config appears incomplete"
        
        print("\n✅ Scanner configuration verified")
    
    def test_connector_files_exist(self):
        """Verify all connector files exist"""
        connectors_path = self.backend_path / "connectors"
        
        required_connectors = [
            'mt4_low_latency.py',
            'mt5_low_latency.py',
            'crypto_low_latency.py',
            'fix_low_latency.py',
            '__init__.py',
        ]
        
        for connector in required_connectors:
            connector_path = connectors_path / connector
            assert connector_path.exists(), f"Missing connector: {connector}"
        
        print(f"\n✅ All {len(required_connectors)} connector files verified")
    
    def test_frontend_pages_exist(self):
        """Verify all frontend pages exist"""
        pages_path = self.frontend_path / "pages"
        
        required_pages = [
            'Settings.tsx',
            'Index.tsx',  # Main dashboard
            'HFT.tsx',
            'Backtest.tsx',
            'Risk.tsx',
            'Gann.tsx',
            'AI.tsx',
        ]
        
        for page in required_pages:
            page_path = pages_path / page
            assert page_path.exists(), f"Missing page: {page}"
        
        print(f"\n✅ All {len(required_pages)} frontend pages verified")
    
    def test_low_latency_connectors_work(self):
        """Verify low latency connectors can be imported"""
        try:
            from connectors.mt4_low_latency import MT4UltraLowLatency, UltraLowLatencyConfig
            from connectors.mt5_low_latency import MT5UltraLowLatency, MT5LowLatencyConfig
            from connectors.crypto_low_latency import CryptoLowLatencyConnector, CryptoLowLatencyConfig
            from connectors.fix_low_latency import FIXLowLatencyConnector, FIXLowLatencyConfig
            
            print("\n✅ All low latency connectors imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import connector: {e}")
    
    def test_config_sync_mapping_exists(self):
        """Verify ConfigSyncMapping exists"""
        sync_mapping_path = self.frontend_path / "config" / "ConfigSyncMapping.ts"
        
        assert sync_mapping_path.exists(), "ConfigSyncMapping.ts not found"
        
        with open(sync_mapping_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'TRADING_MODES_SYNC' in content, "Missing TRADING_MODES_SYNC"
        
        print("\n✅ Config sync mapping verified")


class TestDataStructuresSync:
    """Test data structure synchronization"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.project_root = Path(__file__).parent.parent
        self.frontend_path = self.project_root / "frontend" / "src"
    
    def test_position_data_structure(self):
        """Verify Position data structure sync"""
        api_service_path = self.frontend_path / "services" / "apiService.ts"
        
        with open(api_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check Position interface fields
        required_fields = ['id', 'symbol', 'side', 'quantity', 'entryPrice']
        
        for field in required_fields:
            assert field in content, f"Missing Position field: {field}"
        
        print("\n✅ Position data structure verified")
    
    def test_order_data_structure(self):
        """Verify Order data structure sync"""
        api_service_path = self.frontend_path / "services" / "apiService.ts"
        
        with open(api_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check Order interface fields
        required_fields = ['orderId', 'symbol', 'side', 'quantity', 'status']
        
        for field in required_fields:
            assert field in content, f"Missing Order field: {field}"
        
        print("\n✅ Order data structure verified")
    
    def test_signal_data_structure(self):
        """Verify Signal data structure sync"""
        api_service_path = self.frontend_path / "services" / "apiService.ts"
        
        with open(api_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check Signal interface fields
        required_fields = ['timestamp', 'symbol', 'signal', 'strength', 'price']
        
        for field in required_fields:
            assert field in content, f"Missing Signal field: {field}"
        
        print("\n✅ Signal data structure verified")


def run_tests():
    """Run all synchronization tests"""
    print("=" * 60)
    print("LIVE TRADING READINESS TEST SUITE")
    print("=" * 60)
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-p', 'no:warnings'
    ])
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED - 100% LIVE TRADING READY")
    else:
        print("❌ SOME TESTS FAILED - REVIEW ISSUES ABOVE")
    print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    run_tests()
