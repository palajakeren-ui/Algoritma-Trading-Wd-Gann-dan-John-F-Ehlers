"""
AI Backend Verification Script
Tests all AI modules and engines are properly implemented and importable.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all module imports."""
    results = {'passed': [], 'failed': []}
    
    # Test Gann modules
    try:
        from modules.gann import SquareOf9, SquareOf24, TimePriceGeometry
        results['passed'].append('modules.gann')
    except Exception as e:
        results['failed'].append(('modules.gann', str(e)))
    
    # Test Ehlers modules
    try:
        from modules.ehlers import (
            fisher_transform, mama, cyber_cycle, 
            bandpass_filter, smoothed_rsi, instantaneous_trendline, hilbert_transform
        )
        results['passed'].append('modules.ehlers')
    except Exception as e:
        results['failed'].append(('modules.ehlers', str(e)))
    
    # Test Astro modules
    try:
        from modules.astro import (
            AstroEphemeris, find_planetary_aspects,
            SynodicCycleCalculator, TimeHarmonicsCalculator
        )
        results['passed'].append('modules.astro')
    except Exception as e:
        results['failed'].append(('modules.astro', str(e)))
    
    # Test ML models
    try:
        from models import (
            LightGBMModel, MLPModel, NeuralODEModel, 
            HybridMetaModel, RandomForestModel
        )
        results['passed'].append('models')
    except Exception as e:
        results['failed'].append(('models', str(e)))
    
    # Test core modules
    try:
        from core import (
            FeatureFusionEngine, TrainingPipeline, 
            PredictionService
        )
        results['passed'].append('core.ai_modules')
    except Exception as e:
        results['failed'].append(('core.ai_modules', str(e)))
    
    # Test API
    try:
        from core.ai_api import ai_api, register_ai_routes
        results['passed'].append('core.ai_api')
    except Exception as e:
        results['failed'].append(('core.ai_api', str(e)))
    
    return results


def test_instantiation():
    """Test module instantiation."""
    results = {'passed': [], 'failed': []}
    
    # Test Gann Square of 9
    try:
        from modules.gann.square_of_9 import SquareOf9
        sq9 = SquareOf9(100.0)
        levels = sq9.get_levels(5)
        assert 'support' in levels and 'resistance' in levels
        results['passed'].append('SquareOf9')
    except Exception as e:
        results['failed'].append(('SquareOf9', str(e)))
    
    # Test Gann Square of 24
    try:
        from modules.gann.square_of_24 import SquareOf24
        sq24 = SquareOf24(100.0)
        levels = sq24.get_levels(5)
        assert 'support' in levels and 'resistance' in levels
        results['passed'].append('SquareOf24')
    except Exception as e:
        results['failed'].append(('SquareOf24', str(e)))
    
    # Test Time-Price Geometry
    try:
        from modules.gann.time_price_geometry import TimePriceGeometry
        tpg = TimePriceGeometry()
        angles = tpg.angles  # Use .angles attribute instead of method
        assert len(angles) > 0
        results['passed'].append('TimePriceGeometry')
    except Exception as e:
        results['failed'].append(('TimePriceGeometry', str(e)))
    
    # Test Bandpass Filter
    try:
        import pandas as pd
        import numpy as np
        from modules.ehlers.bandpass_filter import BandpassFilter
        
        data = pd.DataFrame({
            'close': np.random.randn(100) + 100
        })
        bp = BandpassFilter()
        result = bp.calculate(data)
        assert 'bandpass' in result.columns
        results['passed'].append('BandpassFilter')
    except Exception as e:
        results['failed'].append(('BandpassFilter', str(e)))
    
    # Test Smoothed RSI
    try:
        from modules.ehlers.smoothed_rsi import SmoothedRSI
        
        data = pd.DataFrame({
            'close': np.random.randn(100) + 100
        })
        srsi = SmoothedRSI()
        result = srsi.calculate(data)
        assert 'smoothed_rsi' in result.columns
        results['passed'].append('SmoothedRSI')
    except Exception as e:
        results['failed'].append(('SmoothedRSI', str(e)))
    
    # Test Hilbert Transform
    try:
        from modules.ehlers.hilbert_transform import HilbertTransform
        
        data = pd.DataFrame({
            'close': np.random.randn(100) + 100
        })
        ht = HilbertTransform()
        result = ht.calculate(data)
        assert 'hilbert_period' in result.columns
        results['passed'].append('HilbertTransform')
    except Exception as e:
        results['failed'].append(('HilbertTransform', str(e)))
    
    # Test Synodic Cycles
    try:
        from modules.astro.synodic_cycles import SynodicCycleCalculator
        from datetime import datetime
        
        calc = SynodicCycleCalculator()
        phases = calc.get_current_cycle_phases()
        assert len(phases) > 0
        results['passed'].append('SynodicCycleCalculator')
    except Exception as e:
        results['failed'].append(('SynodicCycleCalculator', str(e)))
    
    # Test Time Harmonics
    try:
        from modules.astro.time_harmonics import TimeHarmonicsCalculator
        from datetime import datetime
        
        calc = TimeHarmonicsCalculator()
        projections = calc.calculate_gann_time_projections(datetime.now())
        assert len(projections) > 0
        results['passed'].append('TimeHarmonicsCalculator')
    except Exception as e:
        results['failed'].append(('TimeHarmonicsCalculator', str(e)))
    
    # Test Feature Fusion Engine
    try:
        from core.feature_fusion_engine import FeatureFusionEngine
        
        engine = FeatureFusionEngine()
        results['passed'].append('FeatureFusionEngine')
    except Exception as e:
        results['failed'].append(('FeatureFusionEngine', str(e)))
    
    # Test Training Pipeline
    try:
        from core.training_pipeline import TrainingPipeline
        
        pipeline = TrainingPipeline()
        results['passed'].append('TrainingPipeline')
    except Exception as e:
        results['failed'].append(('TrainingPipeline', str(e)))
    
    # Test LightGBM Model
    try:
        from models.ml_lightgbm import LightGBMModel
        
        model = LightGBMModel()
        results['passed'].append('LightGBMModel')
    except Exception as e:
        results['failed'].append(('LightGBMModel', str(e)))
    
    # Test MLP Model
    try:
        from models.ml_mlp import MLPModel
        
        model = MLPModel({'hidden_layers': [64, 32]})
        results['passed'].append('MLPModel')
    except Exception as e:
        results['failed'].append(('MLPModel', str(e)))
    
    # Test Neural ODE Model
    try:
        from models.ml_neural_ode import NeuralODEModel
        
        model = NeuralODEModel()
        results['passed'].append('NeuralODEModel')
    except Exception as e:
        results['failed'].append(('NeuralODEModel', str(e)))
    
    # Test Hybrid Meta Model
    try:
        from models.ml_hybrid_meta import HybridMetaModel
        
        model = HybridMetaModel()
        results['passed'].append('HybridMetaModel')
    except Exception as e:
        results['failed'].append(('HybridMetaModel', str(e)))
    
    return results


def run_verification():
    """Run full verification."""
    print("=" * 60)
    print("AI Backend Verification")
    print("=" * 60)
    
    # Test imports
    print("\n[1] Testing Module Imports...")
    import_results = test_imports()
    
    for module in import_results['passed']:
        print(f"  ✓ {module}")
    
    for module, error in import_results['failed']:
        print(f"  ✗ {module}: {error}")
    
    # Test instantiation
    print("\n[2] Testing Module Instantiation...")
    inst_results = test_instantiation()
    
    for module in inst_results['passed']:
        print(f"  ✓ {module}")
    
    for module, error in inst_results['failed']:
        print(f"  ✗ {module}: {error}")
    
    # Summary
    total_passed = len(import_results['passed']) + len(inst_results['passed'])
    total_failed = len(import_results['failed']) + len(inst_results['failed'])
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("✓ All AI backend modules verified successfully!")
    else:
        print("✗ Some modules have issues. Please fix before running.")
    
    print("=" * 60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
