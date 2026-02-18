# Settings Frontend-Backend Synchronization Verification

## Description
Verify that frontend Settings page is fully synchronized with all YAML config files in the backend config folder.

## Pre-requisites
- Backend running on port 5000
- Frontend running on port 5173

## Verification Steps

1. Start the backend server:
   ```bash
   cd gann_quant_ai
   python api_v2.py
   ```
   // turbo

2. Start the frontend dev server:
   ```bash
   cd gann_quant_ai/frontend
   npm run dev
   ```
   // turbo

3. Open browser and navigate to `http://localhost:5173/settings`

4. Verify Trading Modes Settings:
   - Check Spot/Futures modes are loaded
   - Modify risk per trade percentage
   - Modify max drawdown
   - Enable/disable trading modes

5. Verify Strategy Weights are synced:
   - Check all 6 strategies (Gann, Astro, Ehlers, ML, Pattern, Options)
   - Modify weights for each timeframe
   - Verify weights sum to 100%

6. Verify Instruments Configuration:
   - Check Forex, Crypto, Indices, Commodities, Stocks
   - Add/remove instruments
   - Enable/disable specific symbols

7. Verify Risk Settings (Dynamic and Fixed modes):
   - Switch between Dynamic and Fixed risk mode
   - For Dynamic: Kelly fraction, volatility adjustment
   - For Fixed: Fixed lot size, fixed R:R ratio

8. Save Settings and verify YAML sync:
   - Click "Save All Settings"
   - Check backend logs for "Config saved to YAML" messages
   - Verify changes in config/*.yaml files

## Expected Results

### YAML Files Updated:
| Settings Section | YAML File |
|-----------------|-----------|
| Trading Modes | broker_config.yaml |
| Strategy Weights | strategy_config.yaml |
| Risk Settings (Dynamic) | risk_config.yaml |
| Risk Settings (Fixed) | risk_config.yaml |
| Instruments | scanner_config.yaml |
| Notifications | notifier.yaml |
| Leverage Settings | broker_config.yaml |

### API Endpoints Used:
- `POST /api/config/sync-all` - Main sync endpoint
- `GET /api/config/settings/load` - Load all settings
- `POST /api/config/settings/save` - Save all settings
- Individual endpoints for each config type

## Troubleshooting

### If settings don't sync:
1. Check browser console for errors
2. Verify backend is running and CORS is enabled
3. Check `api_v2.py` logs for registration errors
4. Verify `config_sync_api.py` is properly imported

### If YAML files don't update:
1. Check file permissions on config folder
2. Verify PyYAML is installed: `pip install pyyaml`
3. Check backend logs for file write errors
