// Type Definitions for Gann Quant AI Frontend
// Synchronized with backend API

// ============================================================================
// FORECAST TYPES
// ============================================================================

export interface DailyForecast {
    date: string;
    bias: 'strong_bullish' | 'bullish' | 'neutral' | 'bearish' | 'strong_bearish';
    confidence: number;
    support: number;
    resistance: number;
    pivot: number;
    target_high: number;
    target_low: number;
    active_cycles: string[];
    narrative: string;
}

export interface DailyForecastResponse {
    symbol: string;
    timestamp: string;
    forecast: DailyForecast;
    multi_day_forecast: DailyForecast[];
}

export interface WaveProjection {
    wave_number: number;
    direction: 'up' | 'down';
    current_price: number;
    target_1: number;
    target_2: number;
    target_3: number;
    expected_duration: number;
    confidence: number;
}

export interface WaveForecastResponse {
    status: string;
    symbol: string;
    timestamp: string;
    wave_count: number;
    waves: Array<{
        number: number;
        direction: string;
        change_pct: number;
    }>;
    projection: WaveProjection;
}

export interface AstroInfluence {
    date: string;
    overall_bias: 'bullish' | 'bearish' | 'neutral';
    bullish_signals: number;
    bearish_signals: number;
    volatile_signals: number;
    average_strength: number;
    events: Array<{
        planet: string;
        aspect: string;
        influence: string;
        strength: number;
    }>;
    lunar: {
        phase: number;
        phase_name: string;
        illumination: number;
        influence: string;
    };
}

export interface AstroForecastResponse {
    timestamp: string;
    daily_influence: AstroInfluence;
    key_dates: Array<{
        date: string;
        event_count: number;
        bullish_count: number;
        bearish_count: number;
        net_bias: string;
        max_strength: number;
        events: Array<{
            planet: string;
            aspect: string;
            influence: string;
        }>;
    }>;
    lunar: any;
}

export interface MLForecastResponse {
    status: string;
    symbol: string;
    timestamp: string;
    current_price: number;
    forecast_direction: 'bullish' | 'bearish';
    avg_confidence: number;
    forecasts: Array<{
        date: string;
        price: number;
        high: number;
        low: number;
        confidence: number;
    }>;
}

// ============================================================================
// CYCLE TYPES
// ============================================================================

export interface CycleInfo {
    type: string;
    period_days: number;
    phase: number;
    phase_position: 'bottom' | 'rising' | 'top' | 'falling';
    strength: number;
}

export interface CycleAnalysisResponse {
    symbol: string;
    timestamp: string;
    fft_cycles: CycleInfo[];
    ehlers_cycle: {
        period: number;
        phase: number;
        phase_position: string;
    };
    lunar_cycle: {
        phase_pct: number;
        phase_name: string;
        market_tendency: string;
        next_new_moon: string;
        next_full_moon: string;
    };
    gann_cycles: {
        upcoming: Array<{
            date: string;
            days_until: number;
            cycle_days: number;
            cycle_name: string;
        }>;
        confluences: Array<{
            date: string;
            cycle_count: number;
            cycles: string[];
            strength: number;
        }>;
    };
    summary: {
        cycle_bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
        bullish_signals: number;
        bearish_signals: number;
        dominant_period: number;
    };
}

// ============================================================================
// REPORT TYPES
// ============================================================================

export interface ReportSection {
    market_summary?: {
        symbol: string;
        current_price: number;
        daily_change: number;
        daily_change_pct: number;
        day_high: number;
        day_low: number;
        period_high: number;
        period_low: number;
        avg_volume: number;
    };
    technical_analysis?: {
        sma_10: number;
        sma_20: number;
        sma_50: number;
        rsi: number;
        rsi_signal: string;
        short_term_trend: string;
        medium_term_trend: string;
        overall_bias: string;
    };
    risk_metrics?: {
        daily_volatility: number;
        annual_volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
        var_95: number;
    };
    trading_summary?: {
        total_trades: number;
        winning_trades: number;
        losing_trades: number;
        win_rate: number;
        total_pnl: number;
        profit_factor: number;
    };
}

export interface GeneratedReport {
    report_id: string;
    generated_at: string;
    symbol: string;
    sections: ReportSection;
    executive_summary: string;
}

// ============================================================================
// CONFIG TYPES
// ============================================================================

export interface GannConfig {
    sq9_levels: number;
    angle_precision: number;
    time_cycles: number[];
    use_natural_squares: boolean;
}

export interface EhlersConfig {
    cycle_length: number;
    mama_fast_limit: number;
    mama_slow_limit: number;
    fisher_period: number;
}

export interface AstroConfig {
    use_lunar: boolean;
    use_planetary: boolean;
    aspect_orb: number;
    planets: string[];
}

export interface ConfigSyncRequest {
    trading?: {
        symbols?: string[];
        timeframe?: string;
        mode?: string;
    };
    risk?: {
        max_position_size?: number;
        max_daily_loss?: number;
        max_drawdown?: number;
    };
    scanner?: {
        scan_interval?: number;
        min_confidence?: number;
    };
    display?: {
        theme?: string;
        chart_style?: string;
    };
}

// ============================================================================
// SMITH CHART TYPES
// ============================================================================

export interface SmithChartPoint {
    normalized_price: number;
    phase: number;
    real_coord: number;
    imag_coord: number;
    zone: 'matched' | 'resistive_high' | 'resistive_low' | 'inductive' | 'capacitive' | 'transition';
}

export interface SmithChartSignal {
    signal: 'buy' | 'sell' | 'hold_long' | 'hold_short' | 'watch' | 'neutral';
    strength: number;
    description: string;
    zone: string;
    phase: number;
}

// ============================================================================
// OPTIONS TYPES
// ============================================================================

export interface OptionGreeks {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
}

export interface OptionsSentiment {
    sentiment: 'bullish' | 'bearish' | 'neutral';
    score: number;
    put_call_ratio: number;
    max_pain: number;
    key_levels: number[];
}

export interface VolatilitySurfaceData {
    atm_iv: number;
    skew: number;
    strikes_count: number;
    expiries_count: number;
}

// ============================================================================
// TRADING MODE TYPES (Synchronized with Backend)
// ============================================================================

export interface TradingModeConfig {
    id: string;
    name: string;
    mode: 'spot' | 'futures';
    enabled: boolean;
    leverage: number;
    marginMode: 'cross' | 'isolated';
    openLotSize: number;
    trailingStop: boolean;
    trailingStopDistance: number;
    autoDeleverage: boolean;
    hedgingEnabled: boolean;
    selectedInstrument: string;
    riskType: 'dynamic' | 'fixed';
    riskPerTrade: number;
    kellyFraction: number;
    adaptiveSizing: boolean;
    volatilityAdjustment: boolean;
    drawdownProtection: boolean;
    maxDrawdown: number;
    dailyLossLimit: number;
    weeklyLossLimit: number;
    breakEvenOnProfit: boolean;
    liquidationAlert: number;
    fixedRiskPerTrade: number;
    fixedMaxDrawdown: number;
    riskRewardRatio: number;
    fixedLotSize: number;
    maxOpenPositions: number;
    brokerType: 'crypto_exchange' | 'metatrader' | 'fix' | 'none';
    exchange: string;
    endpoint: string;
    apiKey: string;
    apiSecret: string;
    passphrase: string;
    testnet: boolean;
    brokerConnected: boolean;
    timeEntryEnabled: boolean;
    entryStartTime: string;
    entryEndTime: string;
    useMultiTf: boolean;
    confirmationTimeframes: string[];
}

export interface ManualLeverageConfig {
    instrument: string;
    leverage: number;
    marginMode: 'cross' | 'isolated';
}

// ============================================================================
// GANN VIBRATION MATRIX TYPES
// ============================================================================

export interface VibrationMatrixEntry {
    degree: number;
    priceUp: number;
    priceDown: number;
    timeEquivalent: string;
    significance: 'cardinal' | 'ordinal' | 'minor';
    nature: string;
}

export interface VibrationMatrixResponse {
    symbol: string;
    basePrice: number;
    timestamp: string;
    matrix: VibrationMatrixEntry[];
}

// ============================================================================
// GANN SUPPLY & DEMAND TYPES
// ============================================================================

export interface SupplyDemandZone {
    price: number;
    strength: number;
    type: string;
    distance_percent: number;
    timestamp: string;
}

export interface GannSupplyDemandResponse {
    symbol: string;
    currentPrice: number;
    timestamp: string;
    supplyZones: SupplyDemandZone[];
    demandZones: SupplyDemandZone[];
    sq9Levels: {
        support: number[];
        resistance: number[];
    };
}

// ============================================================================
// SYNC TYPES
// ============================================================================

export interface SyncSettingsPayload {
    tradingModes?: TradingModeConfig[];
    instruments?: Record<string, any[]>;
    strategyWeights?: Record<string, any[]>;
    manualLeverages?: ManualLeverageConfig[];
}

export interface SyncResponse {
    status: string;
    message: string;
    timestamp: string;
    syncedSections?: string[];
}

// ============================================================================
// RISK-REWARD TYPES
// ============================================================================

export interface RiskRewardAnalysis {
    riskAmount: number;
    rewardAmount: number;
    riskRewardRatio: number;
    positionSize: number;
    winRateToBreakeven: number;
    expectedValue: number;
    riskPercent: number;
}

// ============================================================================
// PATTERN RECOGNITION TYPES
// ============================================================================

export interface PatternMatch {
    name: string;
    type: 'bullish' | 'bearish' | 'neutral';
    strength: number;
    index: number;
    date: string;
    description: string;
}

export interface PatternScanResponse {
    symbol: string;
    timeframe: string;
    timestamp: string;
    patterns: PatternMatch[];
}
