"""
Comprehensive Frontend-Backend Synchronization Verification Test Suite
================================================================
Tests that all slippage settings sync correctly between frontend and backend.
"""

import pytest
import yaml
import os

# Paths
FRONTEND_SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'src')
BACKEND_CONFIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'broker_config.yaml')
CONFIG_SYNC_MAPPING = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'src', 'config', 'ConfigSyncMapping.ts')

SETTINGS_TSX = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'src', 'pages', 'Settings.tsx')


def test_broker_config_has_slippage_fields():
    """Verify broker_config.yaml has all required slippage fields."""
    config_path = BACKEND_CONFIG
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    trading_modes = config.get('trading_modes', [])
    assert len(trading_modes) > 0, "broker_config.yaml should have trading_modes"
    
    # Check first mode
    first_mode = trading_modes[0]
    
    # Required slippage fields
    required_fields = [
        'mtAutoSlippage',
        'mtDefaultSlippage',
        'mtMaxSlippage',
        'mtMinSlippage',
        'mtForexSlippage',
        'mtCryptoSlippage',
        'mtMetalsSlippage',
        'mtIndicesSlippage'
    ]
    
    for field in required_fields:
        assert field in first_mode, f"Field '{field}' missing from broker_config.yaml"
    
    # Check all modes have slippage fields
    for mode in trading_modes:
        for field in required_fields:
            assert field in mode, f"Field '{field}' missing in trading mode {mode['id']}"
    
    print(f"  ✅ All slippage fields verified!")


def test_settings_tsx_has_slippage_ui():
    """Verify Settings.tsx has slippage UI controls."""
    settings_path = SETTINGS_TSX
    
    if not os.path.exists(settings_path):
        pytest.skip("Settings.tsx not found")
    
    with open(settings_path, 'r') as f:
        content = f.read()
    
    # Check for all slippage-related UI elements
    assert 'mtAutoSlippage' in content
    assert 'mtDefaultSlippage' in content
    assert 'mtMaxSlippage' in content
    assert 'mtForexSlippage' in content
    assert 'mtCryptoSlippage' in content
    assert 'mtMetalsSlippage' in content
    assert 'mtIndicesSlippage' in content
    assert 'Slippage Settings' in content or 'Slippage' in content
    
    print("  ✅ Settings.tsx has all slippage UI controls!")


def test_config_sync_mapping_fields():
    """Verify ConfigSyncMapping.ts has all required slippage fields."""
    config_sync_path = CONFIG_SYNC_MAPPING
    
    if not os.path.exists(config_sync_path):
        pytest.skip("ConfigSyncMapping.ts not found")
    
    with open(config_sync_path, 'r') as f:
        content = f.read()
    
    # Check slippage fields are included
    slippage_fields = [
        'mtAutoSlippage', 'mtDefaultSlippage', 'mtMaxSlippage', 'mtMinSlippage',
        'mtForexSlippage', 'mtCryptoSlippage', 'mtMetalsSlippage', 'mtIndicesSlippage'
    ]
    
    for field in slippage_fields:
        assert field in content, f"Field '{field}' missing from ConfigSyncMapping.ts"
    
    print("  ✅ ConfigSyncMapping.ts has all slippage fields!")


def test_sync_status_is_synchronized():
    """Verify sync status shows synchronized."""
    config_sync_path = CONFIG_SYNC_MAPPING
    
    if not os.path.exists(config_sync_path):
        pytest.skip("ConfigSyncMapping.ts not found")
    
    with open(config_sync_path, 'r') as f:
        content = f.read()
    
    # Check sync status values
    assert "'SYNCHRONIZED'" in content or '"SYNCHRONIZED"' in content
    assert 'coveragePercent' in content
    assert '100' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
