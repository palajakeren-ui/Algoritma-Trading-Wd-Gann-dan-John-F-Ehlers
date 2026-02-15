// Pattern Recognition Utility Functions and Types

export interface DetectedPattern {
  id: string;
  name: string;
  type: PatternType;
  confidence: number;
  priceRange: string;
  timeWindow: string;
  signal: SignalType;
  instrument: string;
  timeframe: string;
  detectedAt: Date;
}

export interface ManualAnalysis {
  id: string;
  timeframe: string;
  instrument: string;
  notes: string;
  patterns: string[];
  bias: SignalType;
  keyLevels: { support: number; resistance: number };
  createdAt: Date;
}

export interface AssetAnalysis {
  id: string;
  symbol: string;
  name: string;
  timeframes: string[];
  lastUpdated: Date;
  patternCount: number;
}

export interface TimePattern {
  cycle: string;
  nextTurn: string;
  daysRemaining: number;
  type: string;
  confidence: number;
}

export interface WaveAnalysis {
  wave: string;
  period: string;
  phase: string;
  target: string;
}

export type PatternType =
  | "Candlestick"
  | "Wave Structure"
  | "Time–Price Wave"
  | "Harmonic Pattern"
  | "Chart Pattern";

export type SignalType = "Bullish" | "Bearish" | "Neutral";

export const TIMEFRAMES = [
  { value: "M1", label: "1 Minute" },
  { value: "M2", label: "2 Minutes" },
  { value: "M3", label: "3 Minutes" },
  { value: "M5", label: "5 Minutes" },
  { value: "M10", label: "10 Minutes" },
  { value: "M15", label: "15 Minutes" },
  { value: "M30", label: "30 Minutes" },
  { value: "M45", label: "45 Minutes" },
  { value: "H1", label: "1 Hour" },
  { value: "H2", label: "2 Hours" },
  { value: "H3", label: "3 Hours" },
  { value: "H4", label: "4 Hours" },
  { value: "D1", label: "1 Day" },
  { value: "W1", label: "1 Week" },
  { value: "MN1", label: "1 Month" },
  { value: "Y1", label: "1 Year" },
] as const;

export const PATTERN_TYPES: PatternType[] = [
  "Candlestick",
  "Wave Structure",
  "Time–Price Wave",
  "Harmonic Pattern",
  "Chart Pattern",
];

// Candlestick Pattern Definitions
const CANDLESTICK_PATTERNS = [
  { name: "Bullish Engulfing", signal: "Bullish" as const, baseConfidence: 0.85 },
  { name: "Bearish Engulfing", signal: "Bearish" as const, baseConfidence: 0.85 },
  { name: "Morning Star", signal: "Bullish" as const, baseConfidence: 0.82 },
  { name: "Evening Star", signal: "Bearish" as const, baseConfidence: 0.82 },
  { name: "Hammer", signal: "Bullish" as const, baseConfidence: 0.78 },
  { name: "Shooting Star", signal: "Bearish" as const, baseConfidence: 0.78 },
  { name: "Doji", signal: "Neutral" as const, baseConfidence: 0.72 },
  { name: "Three White Soldiers", signal: "Bullish" as const, baseConfidence: 0.88 },
  { name: "Three Black Crows", signal: "Bearish" as const, baseConfidence: 0.88 },
  { name: "Piercing Line", signal: "Bullish" as const, baseConfidence: 0.76 },
  { name: "Dark Cloud Cover", signal: "Bearish" as const, baseConfidence: 0.76 },
  { name: "Inverted Hammer", signal: "Bullish" as const, baseConfidence: 0.74 },
  { name: "Hanging Man", signal: "Bearish" as const, baseConfidence: 0.74 },
];

// Elliott Wave Patterns
const ELLIOTT_PATTERNS = [
  { name: "Wave 1 (Impulse)", targetMultiplier: 1.03, days: "3–5", signal: "Bullish" as const },
  { name: "Wave 2 (Corrective)", targetMultiplier: 0.98, days: "2–4", signal: "Bearish" as const },
  { name: "Wave 3 (Impulse)", targetMultiplier: 1.08, days: "7–14", signal: "Bullish" as const },
  { name: "Wave 4 (Corrective)", targetMultiplier: 1.04, days: "5–8", signal: "Bearish" as const },
  { name: "Wave 5 (Impulse)", targetMultiplier: 1.12, days: "10–20", signal: "Bullish" as const },
  { name: "Wave A (Corrective)", targetMultiplier: 0.95, days: "4–7", signal: "Bearish" as const },
  { name: "Wave B (Corrective)", targetMultiplier: 0.98, days: "3–6", signal: "Bullish" as const },
  { name: "Wave C (Corrective)", targetMultiplier: 0.90, days: "7–12", signal: "Bearish" as const },
];

// Gann Wave Patterns
const GANN_PATTERNS = [
  { name: "Uptrend Cycle 1", projection: 1.05, hours: "12–24", signal: "Bullish" as const },
  { name: "Uptrend Cycle 2", projection: 1.08, hours: "24–48", signal: "Bullish" as const },
  { name: "Uptrend Cycle 3", projection: 1.12, hours: "48–96", signal: "Bullish" as const },
  { name: "Downtrend Cycle 1", projection: 0.95, hours: "12–24", signal: "Bearish" as const },
  { name: "Downtrend Cycle 2", projection: 0.92, hours: "24–48", signal: "Bearish" as const },
  { name: "Reversal Window", projection: 1.03, hours: "6–12", signal: "Neutral" as const },
];

// Harmonic Patterns
const HARMONIC_PATTERNS = [
  { name: "AB=CD", range: [0.98, 1.04] as [number, number] },
  { name: "Gartley", range: [0.97, 1.05] as [number, number] },
  { name: "Butterfly", range: [0.95, 1.08] as [number, number] },
  { name: "Bat", range: [0.96, 1.06] as [number, number] },
  { name: "Crab", range: [0.94, 1.10] as [number, number] },
  { name: "Shark", range: [0.93, 1.07] as [number, number] },
  { name: "Cypher", range: [0.97, 1.05] as [number, number] },
  { name: "Three Drives", range: [0.96, 1.06] as [number, number] },
];

// Chart Patterns
const CHART_PATTERNS = [
  { name: "Head & Shoulders", signal: "Bearish" as const },
  { name: "Inverse Head & Shoulders", signal: "Bullish" as const },
  { name: "Double Top", signal: "Bearish" as const },
  { name: "Double Bottom", signal: "Bullish" as const },
  { name: "Triple Top", signal: "Bearish" as const },
  { name: "Triple Bottom", signal: "Bullish" as const },
  { name: "Ascending Triangle", signal: "Bullish" as const },
  { name: "Descending Triangle", signal: "Bearish" as const },
  { name: "Symmetrical Triangle", signal: "Neutral" as const },
  { name: "Bull Flag", signal: "Bullish" as const },
  { name: "Bear Flag", signal: "Bearish" as const },
  { name: "Cup & Handle", signal: "Bullish" as const },
  { name: "Rising Wedge", signal: "Bearish" as const },
  { name: "Falling Wedge", signal: "Bullish" as const },
  { name: "Rectangle", signal: "Neutral" as const },
  { name: "Pennant", signal: "Neutral" as const },
];

// Generate Auto-Detected Patterns
export const generateAutoPatterns = (
  price: number,
  instrument: string,
  selectedTimeframe: string
): DetectedPattern[] => {
  const now = new Date();
  const patterns: DetectedPattern[] = [];

  // Generate Candlestick Patterns
  const selectedCandlestick = CANDLESTICK_PATTERNS.filter(() => Math.random() > 0.65);
  selectedCandlestick.forEach((p, idx) => {
    const futureDate = new Date(now.getTime() + (idx + 1) * 3600000);
    const priceLevel = price * (0.99 + Math.random() * 0.02);
    const confidence = Math.min(p.baseConfidence + Math.random() * 0.08, 0.95);

    patterns.push({
      id: `candle-${Date.now()}-${idx}`,
      name: p.name,
      type: "Candlestick",
      confidence,
      priceRange: `Konfirmasi: ${priceLevel.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
      timeWindow: `valid pada ${now.toISOString().split('T')[0]} ${now.toTimeString().slice(0, 5)}–${futureDate.toTimeString().slice(0, 5)} UTC`,
      signal: p.signal,
      instrument,
      timeframe: selectedTimeframe,
      detectedAt: now,
    });
  });

  // Generate Elliott Wave Pattern
  const selectedElliott = ELLIOTT_PATTERNS[Math.floor(Math.random() * ELLIOTT_PATTERNS.length)];
  const elliottConfidence = 0.78 + Math.random() * 0.15;
  const targetPrice = price * selectedElliott.targetMultiplier;
  const peakDate = new Date(now.getTime() + (7 + Math.random() * 14) * 86400000);

  patterns.push({
    id: `elliott-${Date.now()}`,
    name: `Elliott Wave — ${selectedElliott.name}`,
    type: "Wave Structure",
    confidence: Math.min(elliottConfidence, 0.92),
    priceRange: `Target: ${targetPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
    timeWindow: `next ${selectedElliott.days} days (peak probability ~${peakDate.toISOString().split('T')[0]})`,
    signal: selectedElliott.signal,
    instrument,
    timeframe: "D1",
    detectedAt: now,
  });

  // Generate Gann Wave Pattern
  const selectedGann = GANN_PATTERNS[Math.floor(Math.random() * GANN_PATTERNS.length)];
  const gannConfidence = 0.75 + Math.random() * 0.15;
  const gannTarget = price * selectedGann.projection;
  const gannDate = new Date(now.getTime() + (3 + Math.random() * 10) * 86400000);

  patterns.push({
    id: `gann-${Date.now()}`,
    name: `Gann Wave — ${selectedGann.name}`,
    type: "Time–Price Wave",
    confidence: Math.min(gannConfidence, 0.90),
    priceRange: `Projection: ${gannTarget.toLocaleString(undefined, { maximumFractionDigits: 2 })} (reversal area)`,
    timeWindow: `~${gannDate.toISOString().split('T')[0]} ±${selectedGann.hours} hours`,
    signal: selectedGann.signal,
    instrument,
    timeframe: "H4",
    detectedAt: now,
  });

  // Generate Harmonic Pattern
  const selectedHarmonic = HARMONIC_PATTERNS[Math.floor(Math.random() * HARMONIC_PATTERNS.length)];
  const harmonicConfidence = 0.70 + Math.random() * 0.18;
  const rangeStart = price * selectedHarmonic.range[0];
  const rangeEnd = price * selectedHarmonic.range[1];
  const daysToComplete = 3 + Math.floor(Math.random() * 8);

  patterns.push({
    id: `harmonic-${Date.now()}`,
    name: `Harmonic ${selectedHarmonic.name} (confluence)`,
    type: "Harmonic Pattern",
    confidence: Math.min(harmonicConfidence, 0.88),
    priceRange: `Range: ${rangeStart.toLocaleString(undefined, { maximumFractionDigits: 2 })} → ${rangeEnd.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
    timeWindow: `${daysToComplete}–${daysToComplete + 3} days to completion`,
    signal: rangeEnd > rangeStart ? "Bullish" : "Bearish",
    instrument,
    timeframe: "H4",
    detectedAt: now,
  });

  // Generate Chart Pattern
  const selectedChartPatterns = CHART_PATTERNS.filter(() => Math.random() > 0.8);
  selectedChartPatterns.forEach((p, idx) => {
    const chartConfidence = 0.68 + Math.random() * 0.22;
    const breakoutPrice = price * (p.signal === "Bullish" ? 1.02 + Math.random() * 0.05 : 0.95 + Math.random() * 0.03);

    patterns.push({
      id: `chart-${Date.now()}-${idx}`,
      name: p.name,
      type: "Chart Pattern",
      confidence: Math.min(chartConfidence, 0.90),
      priceRange: `Breakout: ${breakoutPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
      timeWindow: `forming over ${2 + Math.floor(Math.random() * 10)} periods`,
      signal: p.signal,
      instrument,
      timeframe: TIMEFRAMES[8 + Math.floor(Math.random() * 4)].value,
      detectedAt: now,
    });
  });

  return patterns;
};

// Generate Pattern Narration
export const generatePatternNarration = (patterns: DetectedPattern[]): string[] => {
  const narrations: string[] = [];

  const bullishPatterns = patterns.filter(p => p.signal === "Bullish" && p.confidence >= 0.75);
  const bearishPatterns = patterns.filter(p => p.signal === "Bearish" && p.confidence >= 0.75);

  const topBullish = bullishPatterns.sort((a, b) => b.confidence - a.confidence).slice(0, 3);
  const topBearish = bearishPatterns.sort((a, b) => b.confidence - a.confidence).slice(0, 2);

  topBullish.forEach(p => {
    if (p.type === "Candlestick") {
      narrations.push(`**${p.name}** pada ${p.priceRange.replace(/.*: /, '')} (${p.timeWindow}) memberikan sinyal masuk awal dengan confidence ${(p.confidence * 100).toFixed(0)}%.`);
    } else if (p.type === "Wave Structure") {
      narrations.push(`**${p.name}** — ${p.priceRange} dalam ${p.timeWindow}. Setup impulsif dengan target terukur.`);
    } else if (p.type === "Time–Price Wave") {
      narrations.push(`**${p.name}** menunjuk reversal window (${p.priceRange}) — gunakan untuk manajemen TP bagian/scale-out.`);
    } else if (p.type === "Harmonic Pattern") {
      narrations.push(`**${p.name}** confluence di ${p.priceRange}, estimasi ${p.timeWindow}.`);
    } else {
      narrations.push(`**${p.name}** terdeteksi dengan confidence ${(p.confidence * 100).toFixed(0)}% — ${p.priceRange}.`);
    }
  });

  topBearish.forEach(p => {
    narrations.push(`⚠️ **${p.name}** (${p.type}) menunjukkan potensi reversal bearish di ${p.priceRange}. Pertimbangkan risk management.`);
  });

  return narrations;
};

// Enrich Candles with Gann Wave Data
export const enrichWithGannWaves = (candles: any[]) => {
  if (!candles || !candles.length) return [];

  const prices = candles.map(c => c.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice - minPrice;

  return candles.map((c, i) => {
    // Cycle calculations based on index
    const cycle1 = Math.sin(i / 8) * (range * 0.05);   // Fast cycle
    const cycle2 = Math.sin(i / 20) * (range * 0.15);  // Medium cycle
    const cycle3 = Math.cos(i / 45) * (range * 0.25);  // Slow cycle

    // We center the waves on the price trend (approximated by moving average or just price)
    // To make it look like an overlay, we project it around the current close
    // But typically Gann waves are distinct cycles. We'll overlay them on the chart.

    // Let's create a "Composite Wave" that tends to lead price
    const composite = cycle1 + cycle2 + cycle3;

    return {
      ...c,
      gannStart: c.close, // Anchor for fill
      gann_fast: c.close + cycle1,
      gann_medium: c.close + cycle2,
      gann_slow: c.close + cycle3,
      gann_composite: c.close + composite * 0.5, // Dampen for overlay
    };
  });
};

// Enrich Candles with Elliott Wave Data
export const enrichWithElliottWaves = (candles: any[]) => {
  if (!candles || !candles.length) return [];

  // Simple logic to visualize wave-like structures on existing data
  return candles.map((c, i) => {
    // Smoothed price for wave baseline
    const smoothed = i > 3
      ? (c.close + candles[i - 1].close + candles[i - 2].close + candles[i - 3].close) / 4
      : c.close;

    // Fractal wave component
    const fractal = Math.sin(i / 5) * (c.close * 0.002);
    const majorWave = Math.sin(i / 34) * (c.close * 0.01);

    const waveProjection = smoothed + majorWave + fractal;

    return {
      ...c,
      elliott_wave: waveProjection,
      elliott_channel_upper: waveProjection * 1.01,
      elliott_channel_lower: waveProjection * 0.99,
      elliott_impulse: i % 20 < 10 ? waveProjection * 1.005 : null, // Visualize impulse phases
    };
  });
};

// Generate Time Cycle Data
export const generateTimeCycleData = (): TimePattern[] => {
  const now = new Date();
  return [
    { cycle: "90 Days", nextTurn: new Date(now.getTime() + 45 * 86400000).toISOString().split('T')[0], daysRemaining: 45, type: "Major", confidence: 92 },
    { cycle: "60 Days", nextTurn: new Date(now.getTime() + 30 * 86400000).toISOString().split('T')[0], daysRemaining: 30, type: "Medium", confidence: 85 },
    { cycle: "30 Days", nextTurn: new Date(now.getTime() + 12 * 86400000).toISOString().split('T')[0], daysRemaining: 12, type: "Minor", confidence: 78 },
    { cycle: "15 Days", nextTurn: new Date(now.getTime() + 3 * 86400000).toISOString().split('T')[0], daysRemaining: 3, type: "Minor", confidence: 72 },
    { cycle: "7 Days", nextTurn: new Date(now.getTime() + 2 * 86400000).toISOString().split('T')[0], daysRemaining: 2, type: "Micro", confidence: 65 },
  ];
};

// Generate Gann Wave Analysis
export const generateGannWaveAnalysis = (currentPrice: number): WaveAnalysis[] => [
  { wave: "Primary Wave", period: "180 days", phase: "Ascending", target: (currentPrice * 1.15).toFixed(2) },
  { wave: "Secondary Wave", period: "60 days", phase: "Peak", target: (currentPrice * 1.05).toFixed(2) },
  { wave: "Tertiary Wave", period: "20 days", phase: "Descending", target: (currentPrice * 0.98).toFixed(2) },
  { wave: "Minor Wave", period: "7 days", phase: "Trough", target: (currentPrice * 0.96).toFixed(2) },
];

// Get Confidence Color
export const getConfidenceColor = (conf: number): string => {
  if (conf >= 0.85) return "text-success";
  if (conf >= 0.70) return "text-accent";
  return "text-warning";
};

// Initial Example Patterns
export const getInitialPatterns = (instrument: string): DetectedPattern[] => [
  {
    id: "init-1",
    name: "Bullish Engulfing",
    type: "Candlestick",
    confidence: 0.88,
    priceRange: "Konfirmasi: 101,700",
    timeWindow: "valid pada 2025-11-04 15:25:00–16:25:00 UTC",
    signal: "Bullish",
    instrument,
    timeframe: "H1",
    detectedAt: new Date(),
  },
  {
    id: "init-2",
    name: "Morning Star",
    type: "Candlestick",
    confidence: 0.80,
    priceRange: "Level: 101,800",
    timeWindow: "2025-11-03 → 2025-11-04 (daily close)",
    signal: "Bullish",
    instrument,
    timeframe: "D1",
    detectedAt: new Date(),
  },
  {
    id: "init-3",
    name: "Elliott Wave — Wave 3 (impulse)",
    type: "Wave Structure",
    confidence: 0.85,
    priceRange: "Target: 102,200",
    timeWindow: "next 7–14 days (peak probability ~2025-11-11)",
    signal: "Bullish",
    instrument,
    timeframe: "D1",
    detectedAt: new Date(),
  },
  {
    id: "init-4",
    name: "Gann Wave — Uptrend Cycle 3",
    type: "Time–Price Wave",
    confidence: 0.83,
    priceRange: "Projection: 103,000 (reversal area)",
    timeWindow: "~2025-11-16 ±6–12 hours",
    signal: "Bullish",
    instrument,
    timeframe: "H4",
    detectedAt: new Date(),
  },
  {
    id: "init-5",
    name: "Harmonic AB=CD (confluence)",
    type: "Harmonic Pattern",
    confidence: 0.76,
    priceRange: "Range: 101,500 → 102,200",
    timeWindow: "5–8 days to completion",
    signal: "Bullish",
    instrument,
    timeframe: "H4",
    detectedAt: new Date(),
  },
];
