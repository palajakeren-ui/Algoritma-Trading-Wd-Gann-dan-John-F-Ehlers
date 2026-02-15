# AI Engine Backend API Documentation

## Overview

This document describes the AI/ML engine endpoints available in the Gann Quant AI backend. These endpoints provide access to advanced trading analysis features including:

- **Training Pipeline**: Train and manage ML models
- **Feature Fusion**: Combine Gann, Astrology, and Ehlers features
- **Predictions**: Generate trading signals with confidence
- **Gann Analysis**: Square of 9/24/52/90/144/360, Time-Price Geometry
- **Ehlers DSP**: Full suite of John Ehlers indicators
- **Astrology**: Synodic cycles and time harmonics

## Base URL

```
http://localhost:5000/api/ai
```

---

## Training Endpoints

### Train Models

**POST** `/api/ai/train`

Train ML models on historical data.

**Request Body:**
```json
{
    "symbol": "BTC-USD",
    "timeframe": "1d",
    "start_date": "2022-01-01",
    "end_date": "2024-01-01",
    "models": ["lightgbm", "xgboost", "mlp"],
    "config": {}
}
```

**Response:**
```json
{
    "status": "success",
    "symbol": "BTC-USD",
    "n_samples": 730,
    "n_features": 45,
    "training_results": {
        "lightgbm": {
            "train_metrics": {"train_auc": 0.85},
            "test_metrics": {"auc": 0.78, "accuracy": 0.71},
            "status": "success"
        }
    },
    "best_model": "lightgbm"
}
```

### Predict

**POST** `/api/ai/predict`

Generate predictions for current market data.

**Request Body:**
```json
{
    "symbol": "BTC-USD",
    "timeframe": "1d",
    "use_ensemble": true
}
```

**Response:**
```json
{
    "status": "success",
    "symbol": "BTC-USD",
    "current_price": 42000.50,
    "predictions": [0.72],
    "confidence": [0.85],
    "latest_signal": {
        "signal": "strong_buy",
        "probability": 0.72,
        "confidence": 0.85
    }
}
```

### Pipeline Status

**GET** `/api/ai/pipeline/status`

Get current training pipeline status.

**Response:**
```json
{
    "status": "success",
    "pipeline_loaded": true,
    "summary": {
        "is_fitted": true,
        "n_trained_models": 5,
        "best_model": "hybrid_meta"
    }
}
```

---

## Feature Fusion Endpoints

### Build Features

**POST** `/api/ai/features/build`

Build fused ML features from price data.

**Request Body:**
```json
{
    "symbol": "BTC-USD",
    "timeframe": "1d",
    "limit": 200
}
```

**Response:**
```json
{
    "status": "success",
    "n_samples": 200,
    "n_features": 45,
    "feature_names": ["return_5d", "rsi_14", "dist_gann_support", ...],
    "latest_features": {
        "return_5d": 0.023,
        "rsi_14": 58.5
    }
}
```

---

## Gann Analysis Endpoints

### Square of 9

**POST** `/api/ai/gann/square-of-9`

Calculate Gann Square of 9 levels.

**Request Body:**
```json
{
    "price": 42000,
    "n_levels": 5
}
```

**Response:**
```json
{
    "status": "success",
    "initial_price": 42000,
    "support": [41500, 40800, 39500],
    "resistance": [42500, 43200, 44000]
}
```

### Square of 24

**POST** `/api/ai/gann/square-of-24`

Calculate Gann Square of 24 levels with time harmonics.

**Request Body:**
```json
{
    "price": 42000,
    "n_levels": 5
}
```

**Response:**
```json
{
    "status": "success",
    "initial_price": 42000,
    "support": [...],
    "resistance": [...],
    "time_harmonics": [
        {"time_value": 24, "significance": "major", "description": "1x base cycle"}
    ],
    "price_angles": [
        {"angle": 0, "price": 42000, "cardinal": true}
    ]
}
```

### Time-Price Geometry

**POST** `/api/ai/gann/time-price-geometry`

Calculate Gann Time-Price Geometry with all angles.

**Request Body:**
```json
{
    "pivot_price": 38000,
    "current_price": 42000,
    "pivot_time": 0,
    "current_time": 100
}
```

**Response:**
```json
{
    "status": "success",
    "support_levels": [
        {"angle": "1x1", "price": 40500, "significance": "major"}
    ],
    "resistance_levels": [...],
    "time_targets": [
        {"days": 90, "date": "2024-04-01", "significance": "major"}
    ],
    "vibration_levels": {...}
}
```

---

## Ehlers DSP Endpoints

### Full Ehlers Analysis

**POST** `/api/ai/ehlers/analyze`

Complete Ehlers DSP analysis with all indicators.

**Request Body:**
```json
{
    "symbol": "BTC-USD",
    "timeframe": "1d",
    "indicators": ["all"]
}
```

**Available Indicators:**
- `fisher` - Fisher Transform
- `mama` - MAMA/FAMA
- `bandpass` - Bandpass Filter
- `smoothed_rsi` - Smoothed RSI
- `itrend` - Instantaneous Trendline
- `hilbert` - Hilbert Transform

**Response:**
```json
{
    "status": "success",
    "symbol": "BTC-USD",
    "current_price": 42000,
    "indicators": {
        "fisher": {
            "current": 1.25,
            "signal": 0.95,
            "direction": "bullish"
        },
        "mama": {
            "mama": 41800,
            "fama": 41500,
            "direction": "bullish"
        },
        "bandpass": {
            "value": 0.35,
            "signal": 1
        },
        "smoothed_rsi": {
            "value": 62.5,
            "overbought": false,
            "oversold": false
        },
        "hilbert": {
            "period": 18.5,
            "phase": 45.2
        }
    }
}
```

---

## Astrology Endpoints

### Synodic Cycles

**GET** `/api/ai/astro/synodic-cycles`

Get current synodic cycle analysis.

**Response:**
```json
{
    "status": "success",
    "current_phases": [
        {
            "cycle": "Jupiter-Saturn",
            "phase_degrees": 125.5,
            "phase_name": "Gibbous",
            "days_to_next_conjunction": 4532
        }
    ],
    "time_harmonics": [
        {"date": "2024-04-15", "days": 90, "significance": "major"}
    ],
    "time_clusters": [
        {"date": "2024-03-21", "score": 85.5}
    ]
}
```

### Time Harmonics

**POST** `/api/ai/astro/time-harmonics`

Calculate time harmonics from a pivot date.

**Request Body:**
```json
{
    "pivot_date": "2024-01-15"
}
```

**Response:**
```json
{
    "status": "success",
    "pivot_date": "2024-01-15",
    "gann_targets": [
        {"date": "2024-04-14", "days": 90, "significance": "major"}
    ],
    "fibonacci_targets": [...],
    "time_clusters": [...]
}
```

---

## Model Management Endpoints

### List Models

**GET** `/api/ai/models/list`

List available ML models and their status.

**Response:**
```json
{
    "status": "success",
    "models": [
        {"id": "lightgbm", "name": "LightGBM", "type": "gradient_boosting", "available": true},
        {"id": "xgboost", "name": "XGBoost", "type": "gradient_boosting", "available": true},
        {"id": "mlp", "name": "MLP Neural Network", "type": "deep_learning", "available": true},
        {"id": "lstm", "name": "LSTM", "type": "deep_learning", "available": true},
        {"id": "transformer", "name": "Transformer", "type": "deep_learning", "available": true},
        {"id": "neural_ode", "name": "Neural ODE", "type": "deep_learning", "available": true},
        {"id": "hybrid_meta", "name": "Hybrid Meta (Stacking)", "type": "ensemble", "available": true}
    ],
    "total": 8,
    "available_count": 7
}
```

---

## Available ML Models

| Model | Type | Description |
|-------|------|-------------|
| LightGBM | Gradient Boosting | Fast, efficient gradient boosting |
| XGBoost | Gradient Boosting | Extreme gradient boosting |
| MLP | Neural Network | Multi-layer perceptron |
| LSTM | Neural Network | Long short-term memory |
| Transformer | Neural Network | Attention-based model |
| Neural ODE | Neural Network | Continuous-time dynamics |
| Hybrid Meta | Ensemble | Stacking of multiple models |
| Random Forest | Tree-based | Tree ensemble |

---

## Feature Categories

### Technical Features
- Returns (1d, 3d, 5d, 10d, 20d, 60d)
- Volatility (10d, 20d, 60d)
- RSI, MACD, Bollinger Bands
- Moving average distances
- ATR, Volume features

### Gann Features
- Distance to nearest support/resistance
- Gann angle positions
- Time cycle proximity
- Square of 9 position

### Ehlers Features
- Fisher Transform values
- MAMA/FAMA positions
- Bandpass filter output
- Hilbert Transform period/phase
- Instantaneous trendline

### Astrology Features
- Planetary aspect presence
- Moon phase
- Retrograde status
- Synodic cycle phases

---

## Error Responses

All endpoints return consistent error format:

```json
{
    "status": "error",
    "message": "Error description"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (invalid input)
- `500` - Server Error
