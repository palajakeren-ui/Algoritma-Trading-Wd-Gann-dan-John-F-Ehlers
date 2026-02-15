# Backend Trading System - Complete Documentation

## Overview

This document describes the comprehensive, production-ready backend trading system for the Gann Quant AI platform.

## Architecture

```
gann_quant_ai/
├── core/                       # Core trading engines
│   ├── signal_engine.py        # AI Signal Engine
│   ├── risk_engine.py          # Risk Management Engine
│   ├── execution_gate.py       # AI → Execution Gate
│   ├── security_manager.py     # Credential Vault & Multi-Account
│   ├── settings_api.py         # Frontend Settings Sync API
│   ├── feature_fusion_engine.py # Feature Fusion
│   ├── training_pipeline.py    # ML Training Pipeline
│   └── ai_api.py              # AI Engine API
│
├── connectors/                 # Exchange & Broker Connectors
│   ├── exchange_connector.py   # Multi-Exchange (CCXT)
│   ├── metatrader_connector.py # MT4/MT5 Connector
│   ├── fix_connector.py        # FIX Protocol Connector
│   └── __init__.py
│
├── modules/
│   ├── gann/                   # WD Gann Modules
│   │   ├── square_of_9.py
│   │   ├── square_of_24.py
│   │   └── time_price_geometry.py
│   ├── ehlers/                 # John Ehlers DSP
│   │   ├── bandpass_filter.py
│   │   ├── smoothed_rsi.py
│   │   ├── instantaneous_trendline.py
│   │   └── hilbert_transform.py
│   └── astro/                  # Astrology & Cycles
│       ├── synodic_cycles.py
│       └── time_harmonics.py
│
├── models/                     # ML Models
│   ├── ml_lightgbm.py
│   ├── ml_mlp.py
│   ├── ml_neural_ode.py
│   ├── ml_hybrid_meta.py
│   └── __init__.py
│
└── api_v2.py                   # Main Flask API
```

## 1. AI-Driven Engine (signal_engine.py)

### Features
- **Signal Types**: BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
- **Confidence Score**: 0-100% with strength levels
- **Reason & Explanation**: Detailed reasoning for each signal
- **Model Attribution**: Contribution breakdown by source

### Analysis Components
- WD Gann (Square of 9, 24, Time-Price Geometry)
- Astrology & Market Cycles (Synodic cycles, Time harmonics)
- John Ehlers DSP (All formulas)
- Machine Learning Models
- Pattern Recognition

### API Endpoint
```
POST /api/ai/signal/generate
{
    "symbol": "BTC/USDT",
    "timeframe": "H1"
}
```

## 2. Machine Learning

### Available Models
- **LightGBM** - Fast gradient boosting
- **XGBoost** - Extreme gradient boosting
- **MLP** - Multi-layer perceptron
- **Hybrid Meta Model** - Stacking ensemble
- **Neural ODE** - Continuous-time dynamics
- **Random Forest** - Ensemble learning

### Model Registry
```python
from models import get_model, MODEL_REGISTRY
model = get_model('lightgbm')
```

### Training Pipeline
```
POST /api/ai/train
{
    "symbol": "BTC/USDT",
    "model_type": "lightgbm",
    "train_days": 365
}
```

## 3. AI → Execution Gate (execution_gate.py)

### Trading Modes
- **MANUAL**: Requires user approval for each trade
- **AI_ASSISTED**: AI recommends, user confirms
- **AI_FULL_AUTO**: Fully autonomous execution
- **PAPER_TRADING**: Simulated execution

### Flow
```
AI Signal → Risk Check → Mode Check → Execution/Queue
```

### Safety Features
- Global kill switch
- Risk violation blocking
- Maximum concurrent orders limit

### API Endpoints
```
GET  /api/settings/execution-gate/status
POST /api/settings/execution-gate/mode
POST /api/settings/kill-switch
```

## 4. Exchange & Broker Connectors

### Supported Exchanges (Crypto)
| Exchange | Spot | Futures | Passphrase |
|----------|------|---------|------------|
| Binance  | ✓    | ✓       | No         |
| Bybit    | ✓    | ✓       | No         |
| OKX      | ✓    | ✓       | Yes        |
| KuCoin   | ✓    | ✓       | Yes        |
| Gate.io  | ✓    | ✓       | No         |
| Bitget   | ✓    | ✓       | Yes        |
| MEXC     | ✓    | ✓       | No         |
| Kraken   | ✓    | ✓       | No         |
| Coinbase | ✓    | -       | No         |
| HTX      | ✓    | ✓       | No         |
| Crypto.com| ✓   | ✓       | No         |
| BingX    | ✓    | ✓       | No         |
| Deribit  | -    | ✓       | No         |
| Phemex   | ✓    | ✓       | No         |

### MetaTrader (Forex)
- MT4 and MT5 support
- Demo and Live accounts
- EA bridge integration

### FIX Protocol
- FIX 4.2, 4.4, 5.0 support
- SSL/TLS encryption
- Session management
- Institutional trading

### API Endpoints
```
GET  /api/settings/exchanges
GET  /api/settings/brokers
POST /api/settings/connection/test
```

## 5. Multi-Account System

### Features
- Multiple accounts per exchange
- Multiple exchanges per user
- Account ↔ Broker ↔ Credential mapping
- Account-aware execution

### Account Management
```
GET    /api/settings/accounts
POST   /api/settings/accounts
DELETE /api/settings/accounts/<id>
```

## 6. Risk Management (risk_engine.py)

### Controls
- **Per-Trade Risk**: Maximum % per trade
- **Position Size**: Maximum position as % of account
- **Daily Loss Limit**: Maximum daily loss %
- **Weekly Loss Limit**: Maximum weekly loss %
- **Max Drawdown**: Maximum drawdown threshold
- **Leverage Cap**: Maximum allowed leverage
- **Max Open Positions**: Concurrent position limit

### Features
- Kelly criterion position sizing
- ATR-based dynamic stops
- Volatility adjustment
- Global kill switch

### API Endpoint
```
GET /api/settings/risk/summary
```

## 7. Security & Credentials (security_manager.py)

### SecureVault
- AES-256 encryption (via cryptography library)
- PBKDF2 key derivation
- No plaintext storage
- Audit logging

### Features
- Encrypted API keys and secrets
- Encrypted FIX credentials
- Account isolation
- Secure vault abstraction

## 8. Execution Engine

### Features
- Spot & Futures execution
- Order lifecycle management
- Retry & failover logic
- Paper trading mode (switchable)

### Order Types
- Market
- Limit
- Stop Loss
- Take Profit
- Trailing Stop

## 9. Frontend Settings Sync

### API Endpoints
```
GET  /api/settings/exchanges       # Get supported exchanges
GET  /api/settings/brokers         # Get supported brokers
GET  /api/settings/accounts        # Get trading accounts
POST /api/settings/accounts        # Create account
POST /api/settings/connection/test # Test connection
POST /api/settings/sync            # Sync all settings
GET  /api/settings/sync            # Get synced settings
GET  /api/settings/trading-modes   # Get trading modes
POST /api/settings/trading-modes   # Save trading modes
```

## Supported Frontend Pages

All endpoints are compatible with:
- Scanner
- Risk
- PatternRecognition
- GannTools
- HFT
- Options
- SlippageSpike
- TradingMode
- Reports
- Journal
- Settings

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
python api_v2.py
```

## Environment Variables

```env
FLASK_ENV=development
FLASK_PORT=5000
MASTER_KEY=your_secure_master_key
```

## Version

Backend Version: 2.2.0
Last Updated: 2026-01-12
