import pandas as pd
import numpy as np

def mama(data: pd.DataFrame, fast_limit: float = 0.5, slow_limit: float = 0.05) -> pd.DataFrame:
    """
    Calculates the MESA Adaptive Moving Average (MAMA) and its signal line (FAMA).

    Args:
        data (pd.DataFrame): DataFrame with 'close' prices.
        fast_limit (float): The fastest alpha value for the EMA.
        slow_limit (float): The slowest alpha value for the EMA.

    Returns:
        pd.DataFrame: A DataFrame with 'MAMA' and 'FAMA' columns.
    """
    close = data['close']

    # Smooth price and calculate period
    smooth = (4 * close + 3 * close.shift(1) + 2 * close.shift(2) + close.shift(3)) / 10.0
    detrender = (0.0962 * smooth + 0.5769 * smooth.shift(2) - 0.5769 * smooth.shift(4) - 0.0962 * smooth.shift(6)) * (0.075 * 0 + 0.54) # Simplified period calc

    # InPhase and Quadrature components
    q1 = (0.0962 * detrender + 0.5769 * detrender.shift(2) - 0.5769 * detrender.shift(4) - 0.0962 * detrender.shift(6)) * (0.075 * 0 + 0.54)
    i1 = detrender.shift(3)

    # Hilbert Transform
    jI = (0.0962 * i1 + 0.5769 * i1.shift(2) - 0.5769 * i1.shift(4) - 0.0962 * i1.shift(6)) * (0.075 * 0 + 0.54)
    jQ = (0.0962 * q1 + 0.5769 * q1.shift(2) - 0.5769 * q1.shift(4) - 0.0962 * q1.shift(6)) * (0.075 * 0 + 0.54)

    # Phase
    i2 = i1 - jQ
    q2 = q1 + jI
    i2 = 0.2 * i2 + 0.8 * i2.shift(1)
    q2 = 0.2 * q2 + 0.8 * q2.shift(1)

    re = i2 * i2.shift(1) + q2 * q2.shift(1)
    im = i2 * q2.shift(1) - q2 * i2.shift(1)
    re = 0.2 * re + 0.8 * re.shift(1)
    im = 0.2 * im + 0.8 * im.shift(1)

    period = 2 * np.pi * np.sqrt(re**2 + im**2) / np.arctan2(im, re) if (re != 0.0) & (im != 0.0) else pd.Series(0, index=close.index)
    period = np.nan_to_num(period, nan=0)

    # Adaptive Alpha
    alpha = fast_limit / (period / 10.0)
    alpha = np.where(alpha < slow_limit, slow_limit, alpha)
    alpha = np.where(alpha > fast_limit, fast_limit, alpha)

    # MAMA and FAMA calculation using iterative approach to avoid lookahead bias
    mama_series = pd.Series(index=close.index, dtype=float)
    fama_series = pd.Series(index=close.index, dtype=float)

    mama_val = 0.0
    fama_val = 0.0
    for i in range(len(close)):
        if pd.notna(alpha[i]) and pd.notna(close[i]):
            if i > 0 and pd.notna(mama_series.iloc[i-1]):
                mama_val = alpha[i] * close[i] + (1 - alpha[i]) * mama_series.iloc[i-1]
            else:
                mama_val = close[i]

            if i > 0 and pd.notna(fama_series.iloc[i-1]):
                fama_val = 0.5 * alpha[i] * mama_val + (1 - 0.5 * alpha[i]) * fama_series.iloc[i-1]
            else:
                fama_val = close[i]

            mama_series.iloc[i] = mama_val
            fama_series.iloc[i] = fama_val

    return pd.DataFrame({'MAMA': mama_series, 'FAMA': fama_series}, index=data.index)
