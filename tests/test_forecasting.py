"""
Tests for Forecasting Module
Comprehensive unit tests for all forecasting functionality
"""
import unittest
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.forecasting import (
    GannDailyForecaster,
    GannWaveAnalyzer,
    AstroCycleProjector,
    MLTimeForecaster,
    ReportGenerator
)


class TestGannDailyForecaster(unittest.TestCase):
    """Test cases for Gann Daily Forecaster"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = {
            'forecast_days': 5,
            'use_cycles': True,
            'angle_set': [1, 2, 3, 4, 8],
            'confidence_threshold': 0.6
        }
        cls.forecaster = GannDailyForecaster(cls.config)
        
        # Generate sample data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        cls.sample_data = pd.DataFrame({
            'open': np.linspace(100, 120, 100) + np.random.normal(0, 1, 100),
            'high': np.linspace(102, 125, 100) + np.random.normal(0, 1, 100),
            'low': np.linspace(98, 115, 100) + np.random.normal(0, 1, 100),
            'close': np.linspace(100, 120, 100) + np.random.normal(0, 1, 100),
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
    
    def test_forecaster_initialization(self):
        """Test forecaster initializes correctly"""
        self.assertIsNotNone(self.forecaster)
    
    def test_daily_forecast(self):
        """Test daily forecast generation"""
        result = self.forecaster.forecast(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('date', result)
        self.assertIn('bias', result)
        self.assertIn('confidence', result)
    
    def test_multi_day_forecast(self):
        """Test multi-day forecast"""
        result = self.forecaster.forecast_multi_day(self.sample_data, days=5)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 5)
    
    def test_support_resistance_calculation(self):
        """Test support/resistance level calculation"""
        result = self.forecaster.calculate_sr_levels(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('support', result)
        self.assertIn('resistance', result)
    
    def test_forecast_with_empty_data(self):
        """Test handling of empty data"""
        empty_df = pd.DataFrame()
        
        with self.assertRaises(Exception):
            self.forecaster.forecast(empty_df)


class TestGannWaveAnalyzer(unittest.TestCase):
    """Test cases for Gann Wave Analyzer"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = {
            'wave_count': 5,
            'min_swing': 0.02
        }
        cls.analyzer = GannWaveAnalyzer(cls.config)
        
        # Generate sample data with wave patterns
        dates = pd.date_range(start='2025-01-01', periods=200, freq='D')
        t = np.linspace(0, 4 * np.pi, 200)
        prices = 100 + 20 * np.sin(t) + 10 * np.sin(2 * t)
        
        cls.sample_data = pd.DataFrame({
            'open': prices - 1,
            'high': prices + 2,
            'low': prices - 2,
            'close': prices,
            'volume': np.random.uniform(1e6, 5e6, 200)
        }, index=dates)
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly"""
        self.assertIsNotNone(self.analyzer)
    
    def test_wave_counting(self):
        """Test wave counting functionality"""
        result = self.analyzer.count_waves(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('wave_count', result)
        self.assertIn('waves', result)
    
    def test_wave_projection(self):
        """Test wave projection"""
        result = self.analyzer.project_wave(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('direction', result)
        self.assertIn('target_1', result)
        self.assertIn('confidence', result)
    
    def test_swing_identification(self):
        """Test swing high/low identification"""
        swings = self.analyzer.identify_swings(self.sample_data)
        
        self.assertIsNotNone(swings)
        self.assertIn('highs', swings)
        self.assertIn('lows', swings)


class TestAstroCycleProjector(unittest.TestCase):
    """Test cases for Astro Cycle Projector"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = {
            'use_lunar': True,
            'use_planetary': True,
            'projection_days': 30
        }
        cls.projector = AstroCycleProjector(cls.config)
    
    def test_projector_initialization(self):
        """Test projector initializes correctly"""
        self.assertIsNotNone(self.projector)
    
    def test_lunar_cycle_projection(self):
        """Test lunar cycle projection"""
        result = self.projector.project_lunar_cycle(datetime.now())
        
        self.assertIsNotNone(result)
        self.assertIn('phase', result)
        self.assertIn('influence', result)
    
    def test_planetary_aspect_projection(self):
        """Test planetary aspect projection"""
        result = self.projector.project_aspects(datetime.now(), days=30)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
    
    def test_combined_projection(self):
        """Test combined astro projection"""
        result = self.projector.project(datetime.now())
        
        self.assertIsNotNone(result)
        self.assertIn('lunar', result)
        self.assertIn('key_dates', result)


class TestMLTimeForecaster(unittest.TestCase):
    """Test cases for ML Time Forecaster"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = {
            'model_type': 'gradient_boosting',
            'forecast_horizon': 5,
            'confidence_interval': 0.95
        }
        cls.forecaster = MLTimeForecaster(cls.config)
        
        # Generate sample data
        dates = pd.date_range(start='2025-01-01', periods=200, freq='D')
        np.random.seed(42)
        
        cls.sample_data = pd.DataFrame({
            'open': np.linspace(100, 120, 200) + np.random.normal(0, 2, 200),
            'high': np.linspace(102, 125, 200) + np.random.normal(0, 2, 200),
            'low': np.linspace(98, 115, 200) + np.random.normal(0, 2, 200),
            'close': np.linspace(100, 120, 200) + np.random.normal(0, 2, 200),
            'volume': np.random.uniform(1e6, 5e6, 200)
        }, index=dates)
    
    def test_forecaster_initialization(self):
        """Test forecaster initializes correctly"""
        self.assertIsNotNone(self.forecaster)
    
    def test_time_series_forecast(self):
        """Test time series forecasting"""
        result = self.forecaster.forecast(self.sample_data, horizon=5)
        
        self.assertIsNotNone(result)
        self.assertIn('forecasts', result)
        self.assertEqual(len(result['forecasts']), 5)
    
    def test_confidence_intervals(self):
        """Test confidence interval calculation"""
        result = self.forecaster.forecast(self.sample_data, horizon=5)
        
        self.assertIsNotNone(result)
        for forecast in result.get('forecasts', []):
            self.assertIn('high', forecast)
            self.assertIn('low', forecast)


class TestReportGenerator(unittest.TestCase):
    """Test cases for Report Generator"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = {
            'report_type': 'daily',
            'include_charts': False
        }
        cls.generator = ReportGenerator(cls.config)
        
        # Generate sample data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
        
        cls.sample_data = pd.DataFrame({
            'open': np.linspace(100, 120, 100),
            'high': np.linspace(102, 125, 100),
            'low': np.linspace(98, 115, 100),
            'close': np.linspace(100, 120, 100),
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
    
    def test_generator_initialization(self):
        """Test generator initializes correctly"""
        self.assertIsNotNone(self.generator)
    
    def test_daily_report_generation(self):
        """Test daily report generation"""
        result = self.generator.generate_daily(self.sample_data, 'BTCUSDT')
        
        self.assertIsNotNone(result)
        self.assertIn('report_id', result)
        self.assertIn('generated_at', result)
    
    def test_executive_summary(self):
        """Test executive summary generation"""
        result = self.generator.generate_summary(self.sample_data, 'BTCUSDT')
        
        self.assertIsNotNone(result)
        self.assertIn('executive_summary', result)


class TestForecastingIntegration(unittest.TestCase):
    """Integration tests for Forecasting module"""
    
    def test_combined_forecast(self):
        """Test combining multiple forecasting methods"""
        # Generate sample data
        dates = pd.date_range(start='2025-01-01', periods=200, freq='D')
        np.random.seed(42)
        
        data = pd.DataFrame({
            'open': np.linspace(100, 120, 200) + np.random.normal(0, 2, 200),
            'high': np.linspace(102, 125, 200) + np.random.normal(0, 2, 200),
            'low': np.linspace(98, 115, 200) + np.random.normal(0, 2, 200),
            'close': np.linspace(100, 120, 200) + np.random.normal(0, 2, 200),
            'volume': np.random.uniform(1e6, 5e6, 200)
        }, index=dates)
        
        # Test individual forecasters
        gann_forecaster = GannDailyForecaster({})
        wave_analyzer = GannWaveAnalyzer({})
        
        gann_result = gann_forecaster.forecast(data)
        wave_result = wave_analyzer.count_waves(data)
        
        self.assertIsNotNone(gann_result)
        self.assertIsNotNone(wave_result)


if __name__ == '__main__':
    unittest.main()
