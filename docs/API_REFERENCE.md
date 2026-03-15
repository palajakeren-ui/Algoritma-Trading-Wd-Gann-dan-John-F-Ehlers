# Backend API Reference

## Base URL
```
http://localhost:5000/api
```

---

## 1. Settings API (`/api/settings`)

### Get Exchanges
```
GET /api/settings/exchanges?mode=all|spot|futures
```

**Response:**
```json
{
    "success": true,
    "exchanges": [
        {"id": "binance", "name": "Binance", "type": "both", "hasPassphrase": false},
        ...
    ],
    "count": 14
}
```

### Get Brokers
```
GET /api/settings/brokers
```

**Response:**
```json
{
    "success": true,
    "brokers": [
        {"id": "mt4", "name": "MetaTrader 4", "type": "forex", "protocol": "metatrader"},
        {"id": "mt5", "name": "MetaTrader 5", "type": "forex", "protocol": "metatrader"},
        {"id": "fix_generic", "name": "FIX Protocol", "type": "institutional", "protocol": "fix"}
    ]
}
```

### Get Accounts
```
GET /api/settings/accounts
```

### Create Account
```
POST /api/settings/accounts
```
**Body:**
```json
{
    "name": "My Binance Account",
    "exchange": "binance",
    "account_type": "futures",
    "broker_type": "crypto_exchange",
    "api_key": "xxx",
    "api_secret": "xxx",
    "testnet": true,
    "max_leverage": 20
}
```

### Delete Account
```
DELETE /api/settings/accounts/<account_id>
```

### Test Connection
```
POST /api/settings/connection/test
```
**Body (Crypto):**
```json
{
    "brokerType": "crypto_exchange",
    "exchange": "binance",
    "apiKey": "xxx",
    "apiSecret": "xxx",
    "testnet": true
}
```

**Body (MetaTrader):**
```json
{
    "brokerType": "metatrader",
    "mtType": "mt5",
    "mtLogin": "12345678",
    "mtPassword": "xxx",
    "mtServer": "Demo-Server:443"
}
```

**Body (FIX):**
```json
{
    "brokerType": "fix",
    "fixHost": "fix.broker.com",
    "fixPort": 443,
    "fixSenderCompId": "SENDER",
    "fixTargetCompId": "TARGET"
}
```

### Sync Settings
```
POST /api/settings/sync
```
**Body:**
```json
{
    "tradingModes": [...],
    "instruments": {...},
    "strategyWeights": {...},
    "manualLeverages": [...]
}
```

### Get Execution Gate Status
```
GET /api/settings/execution-gate/status
```

### Set Trading Mode
```
POST /api/settings/execution-gate/mode
```
**Body:**
```json
{
    "mode": "manual|ai_assisted|ai_full_auto|paper_trading"
}
```

### Kill Switch Control
```
POST /api/settings/kill-switch
```
**Body:**
```json
{
    "action": "activate|deactivate|status",
    "confirmation": "CONFIRM_RESUME"  // Required for deactivate
}
```

### Risk Summary
```
GET /api/settings/risk/summary?account_id=default
```

---

## 2. Market Data API (`/api/market`)

### Get Data Sources
```
GET /api/market/sources
```

### Set Primary Source
```
POST /api/market/sources/primary
```
**Body:**
```json
{
    "source": "metatrader|fix|crypto_exchange"
}
```

### Subscribe to Symbols
```
POST /api/market/subscribe
```
**Body:**
```json
{
    "symbols": ["BTC/USDT", "ETH/USDT"]
}
```

### Unsubscribe
```
POST /api/market/unsubscribe
```
**Body:**
```json
{
    "symbols": ["BTC/USDT"]
}
```

### Get Latest Tick
```
GET /api/market/tick/<symbol>
```

### Get Current Price
```
GET /api/market/price/<symbol>
```

### Get OHLCV Data
```
GET /api/market/ohlcv/<symbol>?timeframe=1h&limit=100&source=crypto_exchange
```

### Get Order Book
```
GET /api/market/orderbook/<symbol>?limit=20
```

### Configure MetaTrader Connector
```
POST /api/market/connector/mt
```
**Body:**
```json
{
    "version": "mt5",
    "login": "12345678",
    "password": "xxx",
    "server": "Demo-Server:443",
    "account_type": "demo",
    "broker": "ICMarkets"
}
```

### Configure FIX Connector
```
POST /api/market/connector/fix
```
**Body:**
```json
{
    "host": "fix.broker.com",
    "port": 443,
    "sender_comp_id": "SENDER",
    "target_comp_id": "TARGET",
    "username": "xxx",
    "password": "xxx",
    "version": "FIX.4.4",
    "ssl_enabled": true
}
```

### Configure Exchange Connector
```
POST /api/market/connector/exchange
```
**Body:**
```json
{
    "exchange": "binance",
    "api_key": "xxx",
    "api_secret": "xxx",
    "testnet": true,
    "mode": "spot|futures"
}
```

### Stream Control
```
POST /api/market/stream/start
POST /api/market/stream/stop
GET /api/market/stream/status
```

---

## 3. Execution API (`/api/execution`)

### Get Status
```
GET /api/execution/status
```

### Set Execution Mode
```
POST /api/execution/mode
```
**Body:**
```json
{
    "mode": "live|paper|simulation"
}
```

### Execute Order
```
POST /api/execution/order
```
**Body:**
```json
{
    "symbol": "BTC/USDT",
    "side": "buy|sell",
    "order_type": "market|limit",
    "quantity": 0.1,
    "price": 45000,
    "exchange": "binance",
    "account_id": "default",
    "stop_loss": 44000,
    "take_profit": 48000,
    "leverage": 5,
    "reduce_only": false,
    "post_only": false,
    "time_in_force": "GTC"
}
```

### Cancel Order
```
DELETE /api/execution/order/<order_id>?symbol=BTC/USDT&exchange=binance
```

### Cancel All Orders
```
POST /api/execution/orders/cancel-all
```
**Body:**
```json
{
    "symbol": "BTC/USDT",  // Optional
    "exchange": "binance"   // Optional
}
```

### Get Open Orders
```
GET /api/execution/orders/open?symbol=BTC/USDT&exchange=binance
```

### Get Positions
```
GET /api/execution/positions?exchange=binance
```

### Close Position
```
POST /api/execution/positions/<symbol>/close
```
**Body:**
```json
{
    "exchange": "binance",
    "quantity": 0.05  // Optional, closes all if not provided
}
```

### Close All Positions
```
POST /api/execution/positions/close-all
```

### Get Execution History
```
GET /api/execution/history?limit=50
```

### Paper Trading
```
GET /api/execution/paper/balance
POST /api/execution/paper/balance  {"balance": 100000}
GET /api/execution/paper/trades?limit=50
POST /api/execution/paper/reset  {"balance": 100000}
```

---

## 4. AI API (`/api/ai`)

### Generate Signal
```
POST /api/ai/signal/generate
```
**Body:**
```json
{
    "symbol": "BTC/USDT",
    "timeframe": "H1"
}
```

### Get Signal History
```
GET /api/ai/signals?symbol=BTC/USDT&limit=50
```

### Train Model
```
POST /api/ai/train
```
**Body:**
```json
{
    "symbol": "BTC/USDT",
    "model_type": "lightgbm",
    "train_days": 365
}
```

### Predict
```
POST /api/ai/predict
```
**Body:**
```json
{
    "symbol": "BTC/USDT",
    "features": {...}
}
```

### Model Registry
```
GET /api/ai/models
GET /api/ai/models/<model_id>
DELETE /api/ai/models/<model_id>
```

---

## 5. Scanner API (`/api/scanner`)

### Run Scan
```
POST /api/scanner/run
```

### Get Results
```
GET /api/scanner/results
```

---

## 6. Analysis API

### Gann Analysis
```
POST /api/gann/analyze
GET /api/gann/square-of-9/<price>
GET /api/gann/time-price-geometry
```

### Ehlers DSP
```
POST /api/ehlers/analyze
GET /api/ehlers/indicators
```

### Astrology
```
POST /api/astro/analyze
GET /api/astro/cycles
```

---

## Error Response Format

All errors follow this format:
```json
{
    "success": false,
    "error": "Error message description"
}
```

## Authentication

Currently, the API does not require authentication. For production, implement:
- JWT authentication
- API key authentication
- Rate limiting

---

## WebSocket Events

Connect to: `ws://localhost:5000`

### Subscribe to Price Updates
```javascript
socket.emit('subscribe_price', { symbol: 'BTC/USDT' });
socket.on('price_update', (data) => { ... });
```

### Subscribe to Signals
```javascript
socket.emit('subscribe_signals', { symbols: ['BTC/USDT'] });
socket.on('signal', (data) => { ... });
```

---

## Version

API Version: 2.2.0
Last Updated: 2026-01-12
