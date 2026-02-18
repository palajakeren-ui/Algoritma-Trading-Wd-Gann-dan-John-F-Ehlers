---
description: Start backend and frontend development servers
---

# Development Workflow — Cenayang Market / Gann Quant AI

This workflow describes how to start the Gann Quant AI application for development.

## Prerequisites

1. Python 3.10+ with pip installed
2. Node.js 18+ with npm installed
3. All dependencies installed

## Steps

### Step 1: Install Backend Dependencies

```bash
cd gann_quant_ai
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies

```bash
cd gann_quant_ai/frontend
npm install
```

// turbo
### Step 3: Start Backend Server

```bash
cd gann_quant_ai
python api_v2.py
```

The backend will start on http://localhost:5000

**Expected:** All 12 blueprints register successfully:
- sync, ai_api, settings_api, market_data_api
- execution_api, trading_api, config_sync_api, hft_api
- missing_endpoints, safety_api, bookmap_terminal_api, analytics_api

**Note:** Warnings about `ccxt`, `XGBoost`, `TensorFlow`, `cryptography` are non-blocking.

### Step 4: Start Frontend Server

In a new terminal:

```bash
cd gann_quant_ai/frontend
npm run dev
```

The frontend will start on http://localhost:5173

## Verification

1. Open http://localhost:5173 in your browser
2. Check that the Dashboard loads correctly
3. Verify WebSocket connection indicator shows "Live"
4. Navigate to Settings and verify backend sync works
5. Test health endpoint: `curl http://localhost:5000/api/health`
6. Test scanner: `curl -X POST http://localhost:5000/api/scanner/scan -H "Content-Type: application/json" -d "{\"symbols\": [\"BTCUSDT\"]}"`
7. Test forecasting: `curl -X POST http://localhost:5000/api/forecast/daily -H "Content-Type: application/json" -d "{\"symbol\": \"BTCUSDT\"}"`

## Key URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:5000/api |
| Health Check | http://localhost:5000/api/health |

## Architecture Overview

- **Backend**: Flask + 12 Blueprints → 263 Routes
- **Frontend**: React + TypeScript + Vite → 24 Pages, 74 API methods
- **Sync**: 74/74 frontend endpoints matched (100%)

## Troubleshooting

### WebSocket Connection Failed
- Ensure backend is running on port 5000
- Check CORS settings in api_v2.py

### API Errors
- Check backend console for error messages
- Verify all config files exist in config/ directory

### Frontend Build Errors
- Run `npm install` to ensure all dependencies
- Check for TypeScript errors with `npm run type-check`

### Port 5000 Already in Use
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```
