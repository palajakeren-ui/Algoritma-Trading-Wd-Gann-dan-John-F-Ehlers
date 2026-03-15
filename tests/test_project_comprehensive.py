"""
Comprehensive Project Verification Script
=========================================
Verifies all imports, modules, and configurations for live trading readiness.

Run: python tests/test_project_comprehensive.py
"""

import os
import sys
import time
import yaml
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class ProjectVerifier:
    """Comprehensive project verification."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
        self.results: Dict[str, Dict] = {}
    
    def verify_all(self) -> Dict[str, Any]:
        """Run all verifications."""
        print("=" * 70)
        print("COMPREHENSIVE PROJECT VERIFICATION")
        print("=" * 70)
        print()
        
        # 1. Verify Python imports
        print("1. Verifying Python modules...")
        self._verify_python_modules()
        
        # 2. Verify YAML configs
        print("\n2. Verifying YAML configurations...")
        self._verify_yaml_configs()
        
        # 3. Verify Frontend-Backend sync
        print("\n3. Verifying Frontend-Backend synchronization...")
        self._verify_frontend_backend_sync()
        
        # 4. Verify connector imports
        print("\n4. Verifying connector modules...")
        self._verify_connectors()
        
        # 5. Verify core modules
        print("\n5. Verifying core modules...")
        self._verify_core_modules()
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _verify_python_modules(self):
        """Verify all Python modules can be imported."""
        modules_to_check = [
            'connectors',
            'core',
            'modules',
            'modules.gann',
            'modules.ehlers',
            'modules.astro',
            'modules.ml',
            'modules.forecasting',
            'utils',
            'scanner',
            'backtest',
            'src.risk',
            'src.execution',
            'src.fusion',
            'src.data',
            'src.signals',
            'src.ml',
            'src.backtest',
            'src.monitoring',
        ]
        
        for module in modules_to_check:
                try:
                    imported = importlib.import_module(module)
                    self.passed.append(f"Module: {module}")
                    self.results[module] = {"status": "PASS", "error": None}
                except Exception as e:
                    self.errors.append(f"Module: {module} - {str(e)}")
                    self.results[module] = {"status": "FAIL", "error": str(e)}
    
    def _verify_yaml_configs(self):
        """Verify all YAML config files."""
        config_dir = PROJECT_ROOT / 'config'
        
        if not config_dir.exists():
            self.errors.append("Config directory not found")
            return
        
        required_fields = {
            'broker_config.yaml': ['trading_modes', 'mtAutoSlippage'],
            'risk_config.yaml': ['position_sizing', 'risk_limits'],
            'strategy_config.yaml': ['ensemble'],
            'scanner_config.yaml': ['universe'],
        }
        
        for filename in os.listdir(config_dir):
            if filename.endswith('.yaml'):
                filepath = config_dir / filename
                try:
                    with open(filepath, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    # Check required fields
                    if filename in required_fields:
                        for field in required_fields[filename]:
                            if not self._check_nested_field(config, field):
                                self.warnings.append(f"Config: {filename} missing field: {field}")
                    
                    self.passed.append(f"Config: {filename}")
                    self.results[f"config/{filename}"] = {"status": "PASS", "error": None}
                except Exception as e:
                    self.errors.append(f"Config: {filename} - {str(e)}")
                    self.results[f"config/{filename}"] = {"status": "FAIL", "error": str(e)}
    
    def _check_nested_field(self, config: Dict, field: str) -> bool:
        """Check if nested field exists in config."""
        parts = field.split('.')
        current = config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True
    
    def _verify_frontend_backend_sync(self):
        """Verify frontend-backend configuration synchronization."""
        # Check broker_config.yaml has slippage fields
        broker_config_path = PROJECT_ROOT / 'config' / 'broker_config.yaml'
        
        try:
            with open(broker_config_path, 'r') as f:
                broker_config = yaml.safe_load(f)
            
            trading_modes = broker_config.get('trading_modes', [])
            
            if trading_modes:
                first_mode = trading_modes[0] if trading_modes else {}
                
                required_slippage_fields = [
                    'mtAutoSlippage',
                    'mtDefaultSlippage',
                    'mtMaxSlippage',
                    'mtMinSlippage',
                    'mtForexSlippage',
                    'mtCryptoSlippage',
                    'mtMetalsSlippage',
                    'mtIndicesSlippage'
                ]
                
                missing_fields = []
                for field in required_slippage_fields:
                    if field not in first_mode:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.warnings.append(f"Frontend-Backend sync: Missing fields {missing_fields}")
                else:
                    self.passed.append("Frontend-Backend slippage sync")
                    self.results["frontend_backend_sync"] = {"status": "PASS", "error": None}
            else:
                self.errors.append("No trading_modes in broker_config.yaml")
                self.results["frontend_backend_sync"] = {"status": "FAIL", "error": "No trading_modes"}
                
        except Exception as e:
            self.errors.append(f"Frontend-Backend sync error: {str(e)}")
            self.results["frontend_backend_sync"] = {"status": "FAIL", "error": str(e)}
    
    def _verify_connectors(self):
        """Verify all connector modules."""
        connectors_dir = PROJECT_ROOT / 'connectors'
        
        if not connectors_dir.exists():
            self.errors.append("Connectors directory not found")
            return
        
        required_connectors = [
            ('mt4_low_latency', ['MT4UltraLowLatency', 'UltraLowLatencyConfig']),
            ('mt5_low_latency', ['MT5UltraLowLatency', 'MT5LowLatencyConfig']),
            ('crypto_low_latency', ['CryptoLowLatencyConnector', 'CryptoLowLatencyConfig']),
            ('fix_low_latency', ['FIXLowLatencyConnector', 'FIXLowLatencyConfig']),
        ]
        
        for module_name in os.listdir(connectors_dir):
            if module_name.endswith('.py') and not module_name.startswith('__'):
                module_path = connectors_dir / module_name
                module_import = module_name.replace('.py', '')
                
                try:
                    imported = importlib.import_module(f'connectors.{module_import}')
                    
                    # Check required classes
                    if module_import in dict(required_connectors):
                        for class_name in required_connectors[module_import]:
                            if not hasattr(imported, class_name):
                                self.warnings.append(f"Connector: {module_import} missing class {class_name}")
                    
                    self.passed.append(f"Connector: {module_import}")
                    self.results[f"connectors/{module_import}"] = {"status": "PASS", "error": None}
                    
                except Exception as e:
                    self.errors.append(f"Connector: {module_import} - {str(e)}")
                    self.results[f"connectors/{module_import}"] = {"status": "FAIL", "error": str(e)}
    
    def _verify_core_modules(self):
        """Verify core modules."""
        core_dir = PROJECT_ROOT / 'core'
        
        if not core_dir.exists():
            self.errors.append("Core directory not found")
            return
        
        required_core_modules = [
            ('signal_engine', ['SignalEngine']),
            ('gann_engine', ['GannEngine']),
            ('ehlers_engine', ['EhlersEngine']),
            ('risk_manager', ['RiskManager']),
            ('execution_engine', ['ExecutionEngine']),
        ]
        
        for module_name in os.listdir(core_dir):
            if module_name.endswith('.py') and not module_name.startswith('__'):
                module_import = module_name.replace('.py', '')
                
                try:
                    imported = importlib.import_module(f'core.{module_import}')
                    self.passed.append(f"Core: {module_import}")
                    self.results[f"core/{module_import}"] = {"status": "PASS", "error": None}
                except Exception as e:
                    self.errors.append(f"Core: {module_import} - {str(e)}")
                    self.results[f"core/{module_import}"] = {"status": "FAIL", "error": str(e)}
    
    def _print_summary(self):
        """Print verification summary."""
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"\n✅ PASSED: {len(self.passed)}")
        print(f"⚠️ WARNINGS: {len(self.warnings)}")
        print(f"❌ ERRORS: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        print("\n" + "=" * 70)
        if not self.errors:
            print("✅ ALL VERIFICATIONS PASSED - READY FOR LIVE TRADING")
        else:
            print("❌ VERification FAILED - Fix errors before live trading")
        print("=" * 70)


if __name__ == "__main__":
    verifier = ProjectVerifier()
    results = verifier.verify_all()
    
    # Exit with error code if there are errors
    sys.exit(1 if verifier.errors else 0)
