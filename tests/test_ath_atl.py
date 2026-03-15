"""
Tests for ATH/ATL Predictor Module
Comprehensive unit tests for All-Time High/Low prediction functionality
"""
import unittest
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.ath_atl_predictor import ATHATLPredictor


class TestAthAtlPredictor(unittest.TestCase):
    """Test cases for ATH/ATL Predictor"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = {
            'lookback_period': 100,
            'sensitivity': 0.02,
            'momentum_window': 14,
            'volume_threshold': 1.5
        }
        cls.predictor = ATHATLPredictor(cls.config)
        
        # Generate sample price data
        dates = pd.date_range(start='2025-01-01', periods=200, freq='D')
        np.random.seed(42)
        
        # Simulate trend with ATH/ATL points
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 200)
        prices = base_price * np.exp(np.cumsum(returns))
        
        cls.sample_data = pd.DataFrame({
            'date': dates,
            'open': prices * (1 - np.random.uniform(0, 0.01, 200)),
            'high': prices * (1 + np.random.uniform(0, 0.02, 200)),
            'low': prices * (1 - np.random.uniform(0, 0.02, 200)),
            'close': prices,
            'volume': np.random.uniform(1000000, 5000000, 200)
        })
        cls.sample_data.set_index('date', inplace=True)
    
    def test_predictor_initialization(self):
        """Test predictor initializes correctly"""
        self.assertIsNotNone(self.predictor)
        self.assertEqual(self.predictor.config.get('lookback_period'), 100)
    
    def test_identify_ath(self):
        """Test ATH identification"""
        result = self.predictor.identify_ath(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('ath_price', result)
        self.assertIn('ath_date', result)
        self.assertGreater(result['ath_price'], 0)
    
    def test_identify_atl(self):
        """Test ATL identification"""
        result = self.predictor.identify_atl(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('atl_price', result)
        self.assertIn('atl_date', result)
        self.assertGreater(result['atl_price'], 0)
    
    def test_predict_ath_probability(self):
        """Test ATH probability prediction"""
        result = self.predictor.predict_ath_probability(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('probability', result)
        self.assertGreaterEqual(result['probability'], 0)
        self.assertLessEqual(result['probability'], 1)
    
    def test_predict_atl_probability(self):
        """Test ATL probability prediction"""
        result = self.predictor.predict_atl_probability(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('probability', result)
        self.assertGreaterEqual(result['probability'], 0)
        self.assertLessEqual(result['probability'], 1)
    
    def test_calculate_distance_to_ath(self):
        """Test distance to ATH calculation"""
        distance = self.predictor.distance_to_ath(self.sample_data)
        
        self.assertIsNotNone(distance)
        self.assertIsInstance(distance, (int, float))
    
    def test_calculate_distance_to_atl(self):
        """Test distance to ATL calculation"""
        distance = self.predictor.distance_to_atl(self.sample_data)
        
        self.assertIsNotNone(distance)
        self.assertIsInstance(distance, (int, float))
    
    def test_full_analysis(self):
        """Test full ATH/ATL analysis"""
        result = self.predictor.analyze(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('current_price', result)
        self.assertIn('ath', result)
        self.assertIn('atl', result)
        self.assertIn('ath_probability', result)
        self.assertIn('atl_probability', result)
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        empty_df = pd.DataFrame()
        
        with self.assertRaises(Exception):
            self.predictor.analyze(empty_df)
    
    def test_momentum_calculation(self):
        """Test momentum indicator calculation"""
        momentum = self.predictor.calculate_momentum(self.sample_data)
        
        self.assertIsNotNone(momentum)
        self.assertEqual(len(momentum), len(self.sample_data))


class TestATHATLIntegration(unittest.TestCase):
    """Integration tests for ATH/ATL module"""
    
    def test_predictor_with_real_data_structure(self):
        """Test with realistic market data structure"""
        config = {}
        predictor = ATHATLPredictor(config)
        
        # Create realistic OHLCV data
        dates = pd.date_range(start='2025-06-01', periods=100, freq='D')
        data = pd.DataFrame({
            'open': np.linspace(100, 120, 100) + np.random.normal(0, 2, 100),
            'high': np.linspace(102, 125, 100) + np.random.normal(0, 2, 100),
            'low': np.linspace(98, 115, 100) + np.random.normal(0, 2, 100),
            'close': np.linspace(100, 120, 100) + np.random.normal(0, 2, 100),
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
        
        result = predictor.analyze(data)
        
        self.assertIsNotNone(result)
        self.assertIn('timestamp', result)


if __name__ == '__main__':
    unittest.main()
