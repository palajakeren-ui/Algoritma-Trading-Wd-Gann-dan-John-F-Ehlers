# Gann Quant AI - Complete Backend Trading System

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start production server
python start_production.py

# Or use api_v2.py directly
python api_v2.py
```

**Server runs at:** `http://localhost:5000`

---

## 📁 Complete Module Structure

### Core Modules (`/core`)

| Module | Description | Key Features |
|--------|-------------|--------------|
| `signal_engine.py` | AI Signal Generator | Gann, Ehlers, Astro, ML fusion |
| `risk_engine.py` | Risk Management | Max loss, position sizing, kill-switch |
| `execution_gate.py` | AI → Execution Gate | Trading modes, signal filtering |
| `live_execution_engine.py` | Order Execution | Retry, failover, paper trading |
| `multi_account_manager.py` | Multi-Account System | Multiple accounts/exchanges |
| `security_manager.py` | Secure Vault | AES-256 encryption |
| `realtime_data_feed.py` | Real-Time Data | MT4/MT5, FIX, exchanges |
| `trading_orchestrator.py` | Trading Loop | Automated signal→execution |
| `trading_journal.py` | Trade Logging | P&L tracking, analytics |

### API Modules (`/core`)

| Module | Prefix | Description |
|--------|--------|-------------|
| `ai_api.py` | `/api/ai` | AI signals, training |
| `settings_api.py` | `/api/settings` | Settings sync |
| `market_data_api.py` | `/api/market` | Data feed |
| `execution_api.py` | `/api/execution` | Order execution |
| `trading_api.py` | `/api/trading` | Orchestrator, journal |

### Connectors (`/connectors`)

| Connector | Supported |
|-----------|-----------|
| `exchange_connector.py` | Binance, Bybit, OKX, KuCoin, Gate.io, Bitget, MEXC, Kraken, Coinbase, HTX, Crypto.com, BingX, Deribit, Phemex |
| `metatrader_connector.py` | MT4, MT5 |
| `fix_connector.py` | FIX 4.2, 4.4, 5.0 |

---

## 🔌 API Endpoints Summary

### Settings (`/api/settings`)
```
GET  /exchanges          - List exchanges
GET  /brokers            - List brokers
GET  /accounts           - List accounts
POST /accounts           - Create account
POST /connection/test    - Test connection
POST /sync               - Sync settings
GET  /execution-gate/status
POST /execution-gate/mode
POST /kill-switch
```

### Market Data (`/api/market`)
```
GET  /sources            - List data sources
POST /subscribe          - Subscribe symbols
GET  /tick/<symbol>      - Get tick
GET  /price/<symbol>     - Get price
GET  /ohlcv/<symbol>     - Get OHLCV
POST /connector/mt       - Configure MT
POST /connector/fix      - Configure FIX
POST /connector/exchange - Configure exchange
```

### Execution (`/api/execution`)
```
POST /order              - Execute order
GET  /positions          - Get positions
POST /positions/<s>/close - Close position
GET  /paper/balance      - Paper balance
POST /paper/reset        - Reset paper
```

### Trading (`/api/trading`)
```
GET  /orchestrator/status
POST /orchestrator/start
POST /orchestrator/stop
GET  /journal/trades
POST /journal/trades
GET  /reports/metrics
GET  /reports/equity-curve
GET  /reports/daily-pnl
GET  /reports/summary
```

---

## 🔒 Security Features

- ✅ **AES-256 Encryption** - All API keys encrypted at rest
- ✅ **PBKDF2 Key Derivation** - 100,000 iterations
- ✅ **No Plaintext** - Secrets never stored in plaintext
- ✅ **Account Isolation** - Separate credentials per account
- ✅ **Kill Switch** - Global emergency stop

---

## 💹 Risk Management

```python
RiskConfig(
    max_risk_per_trade=2.0,      # 2% per trade
    max_position_size=10.0,      # 10% max position
    max_daily_loss=5.0,          # 5% daily limit
    max_drawdown=20.0,           # 20% max drawdown
    max_leverage=20,             # 20x max leverage
    max_open_positions=5         # 5 concurrent
)
```

---

## 📊 Trading Modes

| Mode | Description |
|------|-------------|
| `manual` | No auto-execution |
| `ai_assisted` | Signals require confirmation |
| `ai_full_auto` | Full autonomous trading |
| `paper_trading` | Simulated trading |

---

## 🎯 Frontend Sync Compatibility

**All API responses are 100% compatible with frontend:**
- Settings.tsx
- Scanner pages
- Risk pages
- Trading pages
- All AI pages

**NO FRONTEND CHANGES REQUIRED**

---

## 📈 Performance Tracking

```json
{
  "metrics": {
    "total_trades": 150,
    "win_rate": 65.5,
    "profit_factor": 2.1,
    "max_drawdown_pct": 8.5,
    "sharpe_ratio": 1.8,
    "total_pnl": 12500
  }
}
```

---

## 🛠️ Environment Variables

```bash
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
FLASK_DEBUG=false
MASTER_KEY=your_secure_master_key
```

---

## ✅ Verification

Run verification script:
```bash
python verify_production_backend.py
```

---

## 📋 Checklist

- [x] Multi-Account System
- [x] 14 Exchange Connectors
- [x] MT4/MT5 Connector
- [x] FIX Protocol Connector
- [x] AI Signal Engine
- [x] Risk Management
- [x] Execution Gate
- [x] Live Execution Engine
- [x] Security Vault (AES-256)
- [x] Real-Time Data Feed
- [x] Trading Orchestrator
- [x] Trading Journal
- [x] Performance Reports
- [x] Settings API
- [x] Market Data API
- [x] Execution API
- [x] Trading API
- [x] Frontend Compatibility

---

**Version:** 2.2.0
**Last Updated:** 2026-01-12
