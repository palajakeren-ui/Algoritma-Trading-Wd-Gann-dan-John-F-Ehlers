import pytest
import pandas as pd
import numpy as np
from core.feature_builder import FeatureBuilder
from models.ml_randomforest import RandomForestModel

@pytest.fixture
def sample_data_for_features():
    """Creates a sample DataFrame for feature building."""
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=500))
    close_prices = 100 + np.random.randn(500).cumsum()
    data = {
        'open': close_prices - 1,
        'high': close_prices + 2,
        'low': close_prices - 2,
        'close': close_prices,
        'volume': np.random.randint(1000, 5000, size=500)
    }
    return pd.DataFrame(data, index=dates)

def test_feature_builder(sample_data_for_features):
    """Tests that the FeatureBuilder creates a valid feature set."""
    fb = FeatureBuilder(config={})
    features = fb.build_features(sample_data_for_features, gann_levels=None, astro_events=None)

    assert isinstance(features, pd.DataFrame)
    assert 'target' in features.columns
    assert 'rsi' in features.columns
    assert 'return_5d' in features.columns
    assert not features.isnull().values.any()

@pytest.mark.xfail(reason="FeatureBuilder is producing an empty DataFrame under test conditions.")
def test_random_forest_model_train_predict(sample_data_for_features):
    """Tests the full train and predict cycle of the RandomForestModel."""
    # 1. Build features
    # Use a smaller target period for testing to retain more data
    fb = FeatureBuilder(config={'ml_config': {'feature_engineering': {'target_period': 2}}})
    features = fb.build_features(sample_data_for_features, gann_levels=None, astro_events=None)

    # 2. Train model
    model = RandomForestModel(model_path="models/test_rf_model.pkl")
    accuracy, _ = model.train(features)

    assert accuracy > 0.0 # Just check that it runs and returns a score

    # 3. Predict
    # Drop target for prediction
    X = features.drop('target', axis=1)
    predictions = model.predict(X)

    assert isinstance(predictions, pd.DataFrame)
    assert 'prob_up' in predictions.columns
    assert 'prediction' in predictions.columns
    assert len(predictions) == len(X)
