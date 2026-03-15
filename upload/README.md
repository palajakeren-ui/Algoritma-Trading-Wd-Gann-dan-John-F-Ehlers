# Gann Quant AI

Gann Quant AI is a comprehensive algorithmic trading system based on the principles of W.D. Gann, combined with modern quantitative analysis, machine learning, and advanced signal processing techniques from John F. Ehlers.

## Features

- **Gann Analysis Engine**: Implements Square of 9, Square of 52, Gann Angles, and more.
- **Astro Engine**: Incorporates planetary aspects and retrograde cycles for timing analysis.
- **Ehlers Indicators**: A full suite of Digital Signal Processing (DSP) indicators.
- **Machine Learning Core**: Utilizes MLP, LSTM, and Transformer models for advanced forecasting.
- **Multi-Broker Integration**: Connects with MetaTrader 5, Binance, and other brokers.
- **Advanced Risk Management**: Features sophisticated risk controls and position sizing.
- **Backtesting and Optimization**: Robust backtesting engine with hyperparameter optimization.
- **Dashboard GUI**: A user-friendly interface for monitoring and control.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│              CENAYANG MARKET — 7-PLANE ARCHITECTURE                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PLANE 1: MARKET DATA (Rust) ────────────── HOT PATH                │
│  ├─ WebSocket/FIX/native feed ingestion                              │
│  ├─ Lock-free crossbeam channels (100k bounded)                      │
│  ├─ L2 BTreeMap orderbook (6-dec price precision)                    │
│  ├─ Sequence validation + gap detection + auto-resync                │
│  └─ Latency: <3ms exchange→Rust, P50/P99 histograms                 │
│                                                                      │
│  PLANE 2: EXECUTION (Rust) ──────────────── HOT PATH                │
│  ├─ Idempotent order submission (100k key cache)                     │
│  ├─ Deterministic FIX/WS routing to exchange                         │
│  ├─ Fill event processing + NATS publish                             │
│  └─ Nanosecond latency tracking per order                            │
│                                                                      │
│  PLANE 3: COMPUTE (Cython) ──────────────── ASYNC TO HOT PATH       │
│  ├─ Ehlers DSP: 12 indicators (Fisher, MAMA/FAMA, Cyber Cycle...)   │
│  ├─ Gann Math: 14 modules (SQ9/24/52/144/90/360, Fans, Waves...)   │
│  ├─ Zero look-ahead bias, deterministic computation                  │
│  └─ Fallback: pure Python if Cython not compiled                     │
│                                                                      │
│  PLANE 4: STATE AUTHORITY (Go) ──────────── HOT PATH                │
│  ├─ Single-writer goroutine (authoritative state)                    │
│  ├─ Atomic portfolio transitions via select{}                        │
│  ├─ Monotonic sequence IDs (uint64)                                  │
│  └─ Snapshot+delta replication to frontend                           │
│                                                                      │
│  PLANE 5: AI ADVISORY (Python) ──────────── ADVISORY ONLY           │
│  ├─ 292 Flask routes, 14 API modules                                 │
│  ├─ Stateless signal generation (Gann, Ehlers, Astro, ML)           │
│  ├─ Feature fusion, training pipeline, multi-model ensemble          │
│  └─ WebSocket real-time feed with simulation fallback                │
│                                                                      │
│  PLANE 6: CONTROL (Go) ──────────────────── HOT PATH                │
│  ├─ Global kill-switch (manual + auto on drawdown)                   │
│  ├─ Circuit breaker: 5% max drawdown auto-halt                      │
│  ├─ Daily loss limit: -$10K block                                    │
│  └─ Pre-trade + post-trade risk validation (<100μs)                  │
│                                                                      │
│  PLANE 7: FRONTEND REPLICA (React/TS) ──── READ-ONLY FROM GO       │
│  ├─ 25 pages with lazy-loading + ErrorBoundary                       │
│  ├─ Renders ONLY from authoritative backend state                    │
│  └─ 128 API methods → 292 backend routes (100% coverage)            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Go 1.22+ (optional)
- Rust 1.75+ (optional)
- PostgreSQL + TimescaleDB (production)

### Installation

**1. Backend (Python)**
```bash
# Clone the repository
git clone https://github.com/palajakeren-ui/Algoritma-Trading-Wd-Gann-dan-John-F-Ehlers.git
cd Algoritma-Trading-Wd-Gann-dan-John-F-Ehlers

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials if needed
```

**2. Frontend (React/TypeScript)**
```bash
cd frontend
npm install
npm run dev
# Open → http://localhost:5173
```

**3. Cython Acceleration (Optional)**
```bash
cd cython_compute
python setup.py build_ext --inplace
```

**4. Go Orchestrator (Optional - Production)**
```bash
cd go_api
go run ./cmd/orchestrator
```

**5. Rust Gateway (Optional - Production)**
```bash
cd rust_engine
cargo run --release
```

## ⚡ QUICK START

```bash
# Backend
pip install -r requirements.txt
python api_v2.py
# API running on port 5000

# Frontend
cd frontend && npm install && npm run build && npm run start
# Open → http://localhost:5173
```

## 🚀 SYSTEM STATS

| Metric | Value | Status |
|--------|-------|--------|
| Frontend Pages | 25 (code-split) | ✅ |
| Frontend Components | 99+ | ✅ |
| Frontend API Methods | 128 | ✅ |
| Backend Route Modules | 14 | ✅ |
| Backend Total Routes | 292 | ✅ |
| Core Python Files | 50 | ✅ |
| Cython Compute Modules | 4 files (26 functions) | ✅ |
| Go Orchestrator | 625 lines | ✅ |
| Rust Gateway | 490 lines, 4 async tasks | ✅ |
| DB Schema | 10 tables + audit trail | ✅ |

## 📁 Project Structure

```
Algoritma-Trading-Wd-Gann-dan-John-F-Ehlers/
├── api_v2.py                     # Main Flask API (292 routes)
├── api_sync.py                   # Sync routes
├── start_production.py           # Production startup
├── live_trading.py               # Live trading bot
│
├── cython_compute/               # Cython Compute Plane
│   ├── __init__.py               # Auto-fallback wrapper
│   ├── setup.py                  # Cython build config
│   ├── ehlers_dsp.pyx            # 12 Ehlers DSP indicators
│   └── gann_math.pyx             # 14 Gann math modules
│
├── core/                         # 50 files — Engines + 12 API modules
│   ├── gann_engine.py            # Gann analysis engine
│   ├── ehlers_engine.py          # Ehlers DSP engine
│   ├── astro_engine.py           # Astrological cycles
│   ├── ml_engine.py              # Machine learning engine
│   ├── risk_engine.py            # Risk management
│   ├── execution_engine.py       # Order execution
│   └── [12 *_api.py files]       # API route modules
│
├── go_api/                       # Go Orchestrator
│   ├── cmd/orchestrator/main.go  # State Authority
│   └── internal/{handlers,middleware,models,ws}/
│
├── rust_engine/                  # Rust Gateway
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs               # 4 async tasks
│       ├── orderbook/mod.rs      # L2 orderbook
│       ├── execution/mod.rs      # Order execution
│       └── risk/mod.rs           # Risk math
│
├── frontend/src/                 # React/TypeScript/Vite
│   ├── App.tsx                   # 25 routes + ErrorBoundary
│   ├── pages/ (25)               # All lazy-loaded
│   ├── components/ (99+)         # UI components
│   ├── services/apiService.ts    # 128 API methods
│   └── context/DataFeedContext   # WebSocket feed
│
├── scanner/                      # 13 scanner modules
├── models/                       # 12 ML models
├── modules/                      # gann, ehlers, astro, ml
├── connectors/                   # 5 exchange connectors
├── backtest/                     # Backtesting engine
├── strategies/                   # Trading strategies
├── config/                       # 23 YAML configs
└── tests/                        # Test suite
```

## 🔧 API Endpoints

| Module | Routes | Description |
|--------|--------|-------------|
| bookmap_terminal_api | 39 | Order book & tape data |
| api_sync | 27 | State synchronization |
| config_sync_api | 24 | Configuration sync |
| hft_api | 22 | High-frequency trading |
| agent_orchestration_api | 21 | AI agent control |
| trading_api | 19 | Order management |
| settings_api | 18 | System settings |
| analytics_api | 15 | Performance analytics |
| execution_api | 14 | Trade execution |
| market_data_api | 14 | Market data feed |
| ai_api | 11 | AI predictions |
| safety_api | 10 | Kill switch & safety |
| **TOTAL** | **292** | |

## 📊 Cython Compute Modules

### Ehlers DSP Indicators

| # | Indicator | Performance |
|---|-----------|-------------|
| 1 | Fisher Transform | <50μs/bar |
| 2 | Super Smoother | <20μs/bar |
| 3 | MAMA/FAMA | <100μs/bar |
| 4 | Cyber Cycle | <30μs/bar |
| 5 | Sinewave Indicator | <80μs/bar |
| 6 | Decycler Oscillator | <25μs/bar |
| 7 | Smoothed RSI | <40μs/bar |
| 8 | Instantaneous Trendline | <20μs/bar |
| 9 | Dominant Cycle | <60μs/bar |
| 10 | Roofing Filter | <30μs/bar |
| 11 | Bandpass Filter | <25μs/bar |
| 12 | Hilbert Transform | <35μs/bar |

### Gann Math Modules

| # | Module | Output |
|---|--------|--------|
| 1 | Wave Ratios | 16 harmonic levels |
| 2 | Fan Angles | 9 angles × N bars |
| 3 | Elliott + Fibonacci | 10 retr + 10 ext |
| 4 | Square of 9 | 8 upper + 8 lower |
| 5 | Square of 24 | 24 levels |
| 6 | Square of 52 | 52 levels |
| 7 | Square of 144 | 144 levels |
| 8 | Square of 90 | 8 levels |
| 9 | Square of 360 | 12 upper + 12 lower |
| 10 | Box Projections | 9 price + 9 time |
| 11 | Hexagon Geometry | Ring-based grid |
| 12 | Supply/Demand | Zone levels |
| 13 | Time-Price Square | 12 targets |
| 14 | Planetary Harmonics | 8 cycle phases |

## 🔒 Risk Management

### Pre-Trade Gates

```
PRE-TRADE GATES (<100μs):
  ┌─────────────────────────────────────────────────────┐
  │ Gate 1: Kill Switch      → IF active → REJECT       │
  │ Gate 2: Max Drawdown     → IF dd >= 5% → REJECT     │
  │ Gate 3: Position Size    → IF > $100K → REJECT      │
  │ Gate 4: Daily Loss       → IF < -$10K → REJECT      │
  │ Gate 5: Capital          → IF BUY > cash → REJECT   │
  └─────────────────────────────────────────────────────┘
```

### Kill Switch

```bash
# Activate kill switch
curl -X POST http://localhost:8090/api/kill-switch

# Deactivate kill switch
curl -X POST "http://localhost:8090/api/kill-switch?active=false"
```

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `orders` | Full order lifecycle |
| `fills` | Every execution fill |
| `positions` | Current open positions |
| `portfolio_snapshots` | 5-min equity snapshots |
| `ai_signals` | Every AI prediction |
| `risk_events` | Risk checks + rejections |
| `latency_metrics` | Performance tracking |
| `health_logs` | Service health checks |
| `audit_trail` | Immutable append-only log |
| `trade_history` | VIEW: orders + fills |

## 🌐 Exchange Support

| Exchange | Status | Type |
|----------|--------|------|
| Binance | ✅ Ready | Spot & Futures |
| MetaTrader 5 | ✅ Ready | Forex & CFD |
| Bybit | ✅ Ready | Futures |
| OKX | ✅ Ready | Spot & Futures |
| OANDA | ✅ Ready | Forex |

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_gann.py -v

# Run with coverage
python -m pytest tests/ --cov=core --cov=modules
```

## 🐳 Docker Deployment

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📈 Monitoring

### Prometheus Metrics

- `cenayang_ticks_total` - Total ticks processed
- `cenayang_latency_ns` - Processing latency histogram
- `cenayang_orders_total` - Total orders submitted
- `cenayang_kill_switch_active` - Kill switch status

### Grafana Dashboard

Access at `http://localhost:3001`
- Default credentials: admin / admin123

## 📝 License

Copyright © 2024 - Gann Quant AI Trading System

## ⚠️ DISCLAIMER

Sistem trading ini untuk tujuan edukasi dan penelitian.
Trading cryptocurrency dan forex melibatkan risiko tinggi.
Selalu lakukan backtesting menyeluruh sebelum live trading.
Gunakan manajemen risiko yang tepat.

## 🌐 CENAYANG MARKET

- **Twitter/X**: [@CenayangMarket](https://x.com/CenayangMarket)
- **Instagram**: [@cenayang.market](https://www.instagram.com/cenayang.market)
- **TikTok**: [@cenayang.market](https://www.tiktok.com/@cenayang.market)
- **Facebook**: [Cenayang.Market](https://www.facebook.com/Cenayang.Market)
- **Telegram**: [@cenayangmarket](https://t.me/cenayangmarket)
- **Saweria**: [CenayangMarket](https://saweria.co/CenayangMarket)
- **Trakteer**: [Cenayang.Market](https://trakteer.id/Cenayang.Market/tip)
- **Patreon**: [Cenayangmarket](https://patreon.com/Cenayangmarket)

---

Built with ❤️ by **Cenayang Market** Team 🚀
