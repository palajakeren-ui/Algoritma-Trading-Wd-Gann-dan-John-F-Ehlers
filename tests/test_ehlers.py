import pytest
import pandas as pd
import numpy as np
from modules.ehlers.fisher_transform import fisher_transform

@pytest.fixture
def sample_price_data():
    """Creates a sample DataFrame for testing."""
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=20))
    data = {
        'high': np.array([105, 106, 104, 108, 110, 112, 109, 107, 105, 108, 110, 111, 113, 115, 114, 112, 110, 108, 106, 107]),
        'low': np.array([100, 102, 101, 105, 108, 110, 107, 105, 103, 106, 108, 109, 111, 113, 112, 110, 108, 106, 104, 105]),
        'close': np.array([102, 104, 103, 107, 109, 111, 108, 106, 104, 107, 109, 110, 112, 114, 113, 111, 109, 107, 105, 106])
    }
    return pd.DataFrame(data, index=dates)

def test_fisher_transform_output_shape_and_columns(sample_price_data):
    """Tests that the output has the correct shape and columns."""
    result = fisher_transform(sample_price_data, period=10)
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] == sample_price_data.shape[0]
    assert 'fisher' in result.columns
    assert 'fisher_signal' in result.columns

def test_fisher_transform_signal_line(sample_price_data):
    """Tests that the signal line is a shifted version of the fisher line."""
    result = fisher_transform(sample_price_data, period=10)
    # The first signal value should be NaN
    assert pd.isna(result['fisher_signal'].iloc[0])
    # The second signal value should equal the first fisher value
    assert np.isclose(result['fisher_signal'].iloc[1], result['fisher'].iloc[0])
    # The last signal value should equal the second to last fisher value
    assert np.isclose(result['fisher_signal'].iloc[-1], result['fisher'].iloc[-2])

def test_fisher_transform_missing_columns():
    """Tests that it raises an error if required columns are missing."""
    bad_data = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    with pytest.raises(ValueError):
        fisher_transform(bad_data)

def test_fisher_transform_values_are_finite(sample_price_data):
    """Tests that the calculation does not result in infinity."""
    result = fisher_transform(sample_price_data, period=5)
    assert np.all(np.isfinite(result['fisher'].dropna()))
    assert np.all(np.isfinite(result['fisher_signal'].dropna()))
