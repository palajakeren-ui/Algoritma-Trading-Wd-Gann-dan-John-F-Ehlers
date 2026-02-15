// Enhanced API Service for Gann Quant AI - Synchronized with Backend v2
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:5000';

// ============================================================================
// TYPE DEFINITIONS (Enhanced)
// ============================================================================

export interface BacktestRequest {
  startDate: string;
  endDate: string;
  initialCapital: number;
  symbol: string;
}

export interface BacktestResponse {
  performanceMetrics: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
    totalTrades: number;
  };
  equityCurve: Array<{
    date: string;
    equity: number;
  }>;
  trades: Array<{
    entry_date: string;
    exit_date: string;
    symbol: string;
    side: string;
    entry_price: number;
    exit_price: number;
    quantity: number;
    pnl: number;
    return_pct: number;
  }>;
}

export interface MarketData {
  time: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceUpdate {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change: number;
  changePercent: number;
  timestamp: string;
}

export interface GannLevels {
  angle: number;
  degree: number;
  price: number;
  type: 'support' | 'resistance' | 'major' | 'minor';
  strength: number;
}

export interface Signal {
  timestamp: string;
  symbol: string;
  signal: 'BUY' | 'SELL' | 'NEUTRAL' | 'CAUTION';
  strength: number;
  price: number;
  message: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  realizedPnL: number;
  entryTime: string;
  stopLoss?: number;
  takeProfit?: number;
}

export interface Order {
  orderId: string;
  symbol: string;
  side: string;
  type: string;
  quantity: number;
  price?: number;
  status: string;
  timestamp: string;
}

export interface TradingStatus {
  running: boolean;
  paused: boolean;
  symbols: string[];
  active_trades: number;
  daily_stats: {
    trades: number;
    wins: number;
    losses: number;
    pnl: number;
    max_drawdown: number;
  };
  paper_balance: number;
  positions: Position[];
  timestamp: string;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  message: string;
  timestamp: string;
  config_loaded: boolean;
  live_bot_status?: TradingStatus;
}

export interface ConfigResponse {
  [key: string]: any;
}

export interface AnalysisRequest {
  symbol: string;
  timeframe?: string;
  lookbackDays?: number;
}

export interface GannAnalysisResponse {
  symbol: string;
  currentPrice: number;
  timestamp: string;
  sq9Levels: {
    support: number[];
    resistance: number[];
  };
  gannAngles: any[];
  analysis: {
    nearestSupport: number;
    nearestResistance: number;
  };
}

export interface EhlersAnalysisResponse {
  symbol: string;
  timestamp: string;
  current: {
    mama: number;
    fama: number;
    cycle: number | null;
  };
  history: Array<{
    time: string;
    mama: number;
    fama: number;
    price: number;
  }>;
}

export interface MLPredictionResponse {
  symbol: string;
  timestamp: string;
  prediction: {
    direction: number;
    confidence: number;
    signal: string;
  };
  history: any[];
}

export interface ScannerResponse {
  results: Array<{
    symbol: string;
    direction: string;
    confidence: number;
    entryPrice: number;
    stopLoss: number;
    takeProfit: number;
    riskReward: number;
    timestamp: string;
  }>;
  scannedSymbols: string[];
  timestamp: string;
}

export interface RiskMetrics {
  accountBalance: number;
  totalExposure: number;
  totalUnrealizedPnL: number;
  utilizationPercent: number;
  dailyStats: any;
  maxDrawdown: number;
  timestamp: string;
}

export interface PortfolioSummary {
  accountBalance: number;
  totalValue: number;
  totalPnL: number;
  totalPnLPercent: number;
  openPositions: number;
  dailyStats: any;
  timestamp: string;
}

// ============================================================================
// API SERVICE CLASS
// ============================================================================

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // ============================================================================
  // EXISTING ENDPOINTS (Maintained)
  // ============================================================================

  async runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
    return this.request<BacktestResponse>('/run_backtest', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getMarketData(symbol: string, timeframe: string, startDate: string, endDate: string): Promise<MarketData[]> {
    return this.request<MarketData[]>(`/market-data/${symbol}`, {
      method: 'POST',
      body: JSON.stringify({ timeframe, startDate, endDate }),
    });
  }

  async getGannLevels(symbol: string, price: number): Promise<GannLevels[]> {
    return this.request<GannLevels[]>(`/gann-levels/${symbol}`, {
      method: 'POST',
      body: JSON.stringify({ price }),
    });
  }

  async getSignals(symbol: string): Promise<Signal[]> {
    return this.request<Signal[]>(`/signals/${symbol}`);
  }

  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getConfig(): Promise<ConfigResponse> {
    return this.request<ConfigResponse>('/config');
  }

  // ============================================================================
  // NEW ENDPOINTS - Market Data
  // ============================================================================

  async getLatestPrice(symbol: string): Promise<PriceUpdate> {
    return this.request<PriceUpdate>(`/market-data/${symbol}/latest`);
  }

  // ============================================================================
  // NEW ENDPOINTS - Advanced Analytics
  // ============================================================================

  async getGannFullAnalysis(data: AnalysisRequest): Promise<GannAnalysisResponse> {
    return this.request<GannAnalysisResponse>('/gann/full-analysis', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getEhlersAnalysis(data: AnalysisRequest): Promise<EhlersAnalysisResponse> {
    return this.request<EhlersAnalysisResponse>('/ehlers/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAstroAnalysis(data: AnalysisRequest): Promise<any> {
    return this.request<any>('/astro/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMLPrediction(data: AnalysisRequest): Promise<MLPredictionResponse> {
    return this.request<MLPredictionResponse>('/ml/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Live Trading Control
  // ============================================================================

  async startTrading(symbols?: string[]): Promise<any> {
    return this.request<any>('/trading/start', {
      method: 'POST',
      body: JSON.stringify({ symbols }),
    });
  }

  async stopTrading(): Promise<any> {
    return this.request<any>('/trading/stop', {
      method: 'POST',
    });
  }

  async pauseTrading(): Promise<any> {
    return this.request<any>('/trading/pause', {
      method: 'POST',
    });
  }

  async resumeTrading(): Promise<any> {
    return this.request<any>('/trading/resume', {
      method: 'POST',
    });
  }

  async getTradingStatus(): Promise<TradingStatus> {
    return this.request<TradingStatus>('/trading/status');
  }

  // ============================================================================
  // NEW ENDPOINTS - Position Management
  // ============================================================================

  async getPositions(): Promise<Position[]> {
    return this.request<Position[]>('/positions');
  }

  async getPosition(symbol: string): Promise<Position> {
    return this.request<Position>(`/positions/${symbol}`);
  }

  async closePosition(positionId: string, symbol: string): Promise<any> {
    return this.request<any>(`/positions/${positionId}/close`, {
      method: 'POST',
      body: JSON.stringify({ symbol }),
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Order Management
  // ============================================================================

  async createOrder(order: {
    symbol: string;
    side: string;
    quantity: number;
    type?: string;
    price?: number;
    stopLoss?: number;
    takeProfit?: number;
  }): Promise<any> {
    return this.request<any>('/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  }

  async getOrders(): Promise<Order[]> {
    return this.request<Order[]>('/orders');
  }

  async cancelOrder(orderId: string): Promise<any> {
    return this.request<any>(`/orders/${orderId}`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Risk Management
  // ============================================================================

  async getRiskMetrics(): Promise<RiskMetrics> {
    return this.request<RiskMetrics>('/risk/metrics');
  }

  async calculatePositionSize(data: {
    accountBalance: number;
    riskPercent: number;
    entryPrice: number;
    stopLoss: number;
  }): Promise<any> {
    return this.request<any>('/risk/calculate-position-size', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Scanner
  // ============================================================================

  async runScanner(data: {
    symbols?: string[];
    timeframe?: string;
  }): Promise<ScannerResponse> {
    return this.request<ScannerResponse>('/scanner/scan', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Portfolio
  // ============================================================================

  async getPortfolioSummary(): Promise<PortfolioSummary> {
    return this.request<PortfolioSummary>('/portfolio/summary');
  }

  // ============================================================================
  // NEW ENDPOINTS - Forecasting
  // ============================================================================

  async getDailyForecast(data: {
    symbol?: string;
    lookbackDays?: number;
  }): Promise<any> {
    return this.request<any>('/forecast/daily', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getWaveForecast(data: {
    symbol?: string;
    lookbackDays?: number;
  }): Promise<any> {
    return this.request<any>('/forecast/waves', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAstroForecast(data: {
    daysAhead?: number;
  }): Promise<any> {
    return this.request<any>('/forecast/astro', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMLForecast(data: {
    symbol?: string;
    forecastDays?: number;
    lookbackDays?: number;
  }): Promise<any> {
    return this.request<any>('/forecast/ml', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Cycle Analysis
  // ============================================================================

  async analyzeCycles(data: {
    symbol?: string;
    lookbackDays?: number;
  }): Promise<any> {
    return this.request<any>('/cycles/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Configuration Sync
  // ============================================================================

  async syncConfig(config: {
    trading?: any;
    risk?: any;
    scanner?: any;
    display?: any;
  }): Promise<any> {
    return this.request<any>('/config/sync', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getGannConfig(): Promise<any> {
    return this.request<any>('/config/gann');
  }

  async updateGannConfig(config: any): Promise<any> {
    return this.request<any>('/config/gann', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getEhlersConfig(): Promise<any> {
    return this.request<any>('/config/ehlers');
  }

  async updateEhlersConfig(config: any): Promise<any> {
    return this.request<any>('/config/ehlers', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getAstroConfig(): Promise<any> {
    return this.request<any>('/config/astro');
  }

  async updateAstroConfig(config: any): Promise<any> {
    return this.request<any>('/config/astro', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // ============================================================================
  // NEW ENDPOINTS - Reports
  // ============================================================================

  async generateReport(data: {
    symbol?: string;
    lookbackDays?: number;
    trades?: any[];
    analysis?: any;
  }): Promise<any> {
    return this.request<any>('/reports/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // FRONTEND-BACKEND SYNC ENDPOINTS
  // ============================================================================

  async syncAllSettings(settings: {
    tradingModes?: any[];
    instruments?: any;
    strategyWeights?: any;
    manualLeverages?: any[];
  }): Promise<any> {
    return this.request<any>('/settings/sync-all', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  async loadAllSettings(): Promise<any> {
    return this.request<any>('/settings/load-all');
  }

  async getTradingModes(): Promise<any> {
    return this.request<any>('/config/trading-modes');
  }

  async saveTradingModes(modes: any[]): Promise<any> {
    return this.request<any>('/config/trading-modes', {
      method: 'POST',
      body: JSON.stringify({ modes }),
    });
  }

  async getRiskConfig(): Promise<any> {
    return this.request<any>('/config/risk');
  }

  async updateRiskConfig(config: any): Promise<any> {
    return this.request<any>('/config/risk', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getScannerConfig(): Promise<any> {
    return this.request<any>('/config/scanner');
  }

  async updateScannerConfig(config: any): Promise<any> {
    return this.request<any>('/config/scanner', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getInstruments(): Promise<any> {
    return this.request<any>('/instruments');
  }

  async saveInstruments(instruments: any): Promise<any> {
    return this.request<any>('/instruments', {
      method: 'POST',
      body: JSON.stringify(instruments),
    });
  }

  async getStrategyWeights(): Promise<any> {
    return this.request<any>('/config/strategies');
  }

  async saveStrategyWeights(weights: any): Promise<any> {
    return this.request<any>('/config/strategies', {
      method: 'POST',
      body: JSON.stringify(weights),
    });
  }

  async optimizeStrategyWeights(data: {
    timeframe: string;
    metric: string;
    startDate: string;
    endDate: string;
    symbol?: string; // Optional, maybe optimize for specific symbol or global
  }): Promise<any> {
    return this.request<any>('/strategies/optimize', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getLeverageConfig(): Promise<any> {
    return this.request<any>('/config/leverage');
  }

  async saveLeverageConfig(leverages: any[]): Promise<any> {
    return this.request<any>('/config/leverage', {
      method: 'POST',
      body: JSON.stringify({ manualLeverages: leverages }),
    });
  }

  // ============================================================================
  // SMITH CHART ENDPOINTS
  // ============================================================================

  async getSmithChartAnalysis(data: {
    symbol?: string;
    lookbackDays?: number;
  }): Promise<any> {
    return this.request<any>('/smith/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // OPTIONS ENDPOINTS
  // ============================================================================

  async getOptionsAnalysis(data: {
    symbol?: string;
    expiryDays?: number;
  }): Promise<any> {
    return this.request<any>('/options/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async calculateOptionsGreeks(data: {
    spotPrice: number;
    strikePrice: number;
    timeToExpiry: number;
    volatility: number;
    riskFreeRate?: number;
    optionType?: string;
  }): Promise<any> {
    return this.request<any>('/options/greeks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // RISK-REWARD ENDPOINTS
  // ============================================================================

  async calculateRiskReward(data: {
    entryPrice: number;
    stopLoss: number;
    takeProfit: number;
    accountBalance?: number;
    riskPercent?: number;
  }): Promise<any> {
    return this.request<any>('/rr/calculate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // PATTERN RECOGNITION ENDPOINTS
  // ============================================================================

  async scanPatterns(data: {
    symbol?: string;
    timeframe?: string;
    lookbackDays?: number;
  }): Promise<any> {
    return this.request<any>('/patterns/scan', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // GANN ADVANCED ENDPOINTS
  // ============================================================================

  async getGannVibrationMatrix(data: {
    symbol?: string;
    basePrice?: number;
  }): Promise<any> {
    return this.request<any>('/gann/vibration-matrix', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getGannSupplyDemand(data: {
    symbol?: string;
    timeframe?: string;
    lookbackDays?: number;
  }): Promise<any> {
    return this.request<any>('/gann/supply-demand', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // BROKER CONNECTION ENDPOINTS
  // ============================================================================

  async testBrokerConnection(data: {
    brokerType: string;
    exchange?: string;
    apiKey?: string;
    apiSecret?: string;
    testnet?: boolean;
    mtType?: string;
    mtLogin?: string;
    mtPassword?: string;
    mtServer?: string;
    fixHost?: string;
    fixPort?: number;
    fixSenderCompId?: string;
    fixTargetCompId?: string;
  }): Promise<any> {
    return this.request<any>('/broker/test-connection', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getBinanceBalance(): Promise<any> {
    return this.request<any>('/broker/binance/balance');
  }

  async getMT5Positions(): Promise<any> {
    return this.request<any>('/broker/mt5/positions');
  }

  // ============================================================================
  // ML TRAINING ENDPOINTS
  // ============================================================================

  async getMLConfig(): Promise<any> {
    return this.request<any>('/ml/config');
  }

  async saveMLConfig(config: any): Promise<any> {
    return this.request<any>('/ml/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async startMLTraining(data: {
    config?: any;
    modelType?: string;
  }): Promise<any> {
    return this.request<any>('/ml/train', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTrainingStatus(trainingId: string): Promise<any> {
    return this.request<any>(`/ml/training-status/${trainingId}`);
  }

  async startAutoTuning(data: {
    searchMethod?: string;
    maxTrials?: number;
  }): Promise<any> {
    return this.request<any>('/ml/auto-tune', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getEnsembleConfig(): Promise<any> {
    return this.request<any>('/ml/ensemble');
  }

  async saveEnsembleConfig(config: any): Promise<any> {
    return this.request<any>('/ml/ensemble', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async exportMLModel(data: {
    modelId: string;
    format: string;
  }): Promise<any> {
    return this.request<any>('/ml/export', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // ALERT CONFIGURATION ENDPOINTS
  // ============================================================================

  async getAlertConfig(): Promise<any> {
    return this.request<any>('/alerts/config');
  }

  async saveAlertConfig(config: any): Promise<any> {
    return this.request<any>('/alerts/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async testAlertChannel(channel: string, config: any): Promise<any> {
    return this.request<any>(`/alerts/test/${channel}`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async sendAlert(data: {
    type: string;
    message: string;
    channels: string[];
  }): Promise<any> {
    return this.request<any>('/alerts/send', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // CONFIG SYNC API - Full YAML Config Synchronization
  // ============================================================================

  async getAllConfigs(): Promise<any> {
    return this.request<any>('/config/all');
  }

  async syncAllConfigsToBackend(settings: {
    tradingModes?: any[];
    strategyWeights?: any;
    instruments?: any;
    manualLeverages?: any[];
    riskSettings?: any;
    notificationSettings?: any;
    mlConfig?: any;
  }): Promise<any> {
    return this.request<any>('/config/sync-all', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  async loadSettingsFromBackend(): Promise<any> {
    return this.request<any>('/config/settings/load');
  }

  async saveSettingsToBackend(settings: {
    tradingModes?: any[];
    manualLeverages?: any[];
    strategyWeights?: any;
    instruments?: any;
  }): Promise<any> {
    return this.request<any>('/config/settings/save', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  // Individual Config Endpoints
  async getGannConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/gann');
  }

  async updateGannConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/gann', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getAstroConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/astro');
  }

  async updateAstroConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/astro', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getEhlersConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/ehlers');
  }

  async updateEhlersConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/ehlers', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getMLConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/ml');
  }

  async updateMLConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/ml', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getRiskConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/risk');
  }

  async updateRiskConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/risk', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getScannerConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/scanner');
  }

  async updateScannerConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/scanner', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getStrategyConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/strategy');
  }

  async updateStrategyConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/strategy', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getBrokerConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/broker');
  }

  async updateBrokerConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/broker', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getNotifierConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/notifier');
  }

  async updateNotifierConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/notifier', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getOptionsConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/options');
  }

  async updateOptionsConfigToYaml(config: any): Promise<any> {
    return this.request<any>('/config/options', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Frontend-Specific Sync Endpoints
  async getTradingModesFromYaml(): Promise<any> {
    return this.request<any>('/config/trading-modes');
  }

  async saveTradingModesToYaml(modes: any[]): Promise<any> {
    return this.request<any>('/config/trading-modes', {
      method: 'POST',
      body: JSON.stringify({ modes }),
    });
  }

  async getStrategyWeightsFromYaml(): Promise<any> {
    return this.request<any>('/config/strategy-weights');
  }

  async saveStrategyWeightsToYaml(weights: any): Promise<any> {
    return this.request<any>('/config/strategy-weights', {
      method: 'POST',
      body: JSON.stringify({ weights }),
    });
  }

  async getInstrumentsFromYaml(): Promise<any> {
    return this.request<any>('/config/instruments');
  }

  async saveInstrumentsToYaml(instruments: any): Promise<any> {
    return this.request<any>('/config/instruments', {
      method: 'POST',
      body: JSON.stringify({ instruments }),
    });
  }

  async getLeverageConfigFromYaml(): Promise<any> {
    return this.request<any>('/config/leverage');
  }

  async saveLeverageConfigToYaml(manualLeverages: any[]): Promise<any> {
    return this.request<any>('/config/leverage', {
      method: 'POST',
      body: JSON.stringify({ manualLeverages }),
    });
  }
}

export const apiService = new ApiService();
export default apiService;