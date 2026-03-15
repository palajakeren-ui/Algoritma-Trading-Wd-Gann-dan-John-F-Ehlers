import { useState, useEffect, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Cell,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Crosshair,
  Layers,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Eye,
  EyeOff,
  Activity,
} from "lucide-react";
import { DetectedPattern } from "@/lib/patternUtils";

interface CandleData {
  time: number;
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  patternId?: string;
}

interface InteractiveCandlestickChartProps {
  currentPrice: number;
  patterns: DetectedPattern[];
  instrument: string;
  timeframe: string;
  isLive?: boolean;
}

export const InteractiveCandlestickChart = ({
  currentPrice,
  patterns,
  instrument,
  timeframe,
  isLive = true,
}: InteractiveCandlestickChartProps) => {
  const [candleData, setCandleData] = useState<CandleData[]>([]);
  const [showPatternOverlay, setShowPatternOverlay] = useState(true);
  const [showVolume, setShowVolume] = useState(true);
  const [selectedPattern, setSelectedPattern] = useState<DetectedPattern | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);

  // Generate realistic candlestick data
  useEffect(() => {
    const generateCandles = () => {
      const candles: CandleData[] = [];
      let price = currentPrice * 0.98;
      const now = Date.now();
      
      for (let i = 0; i < 60; i++) {
        const volatility = price * 0.003;
        const trend = Math.sin(i / 10) * volatility * 0.5;
        
        const open = price;
        const change = (Math.random() - 0.48) * volatility * 2 + trend;
        const close = open + change;
        
        const high = Math.max(open, close) + Math.random() * volatility * 0.5;
        const low = Math.min(open, close) - Math.random() * volatility * 0.5;
        
        candles.push({
          time: i,
          timestamp: new Date(now - (60 - i) * 60000),
          open: Number(open.toFixed(2)),
          high: Number(high.toFixed(2)),
          low: Number(low.toFixed(2)),
          close: Number(close.toFixed(2)),
          volume: Math.floor(1000000 + Math.random() * 2000000),
        });
        
        price = close;
      }
      
      return candles;
    };

    setCandleData(generateCandles());
  }, [currentPrice, instrument, timeframe]);

  // Update last candle in real-time
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      setCandleData((prev) => {
        if (prev.length === 0) return prev;
        
        const newData = [...prev];
        const lastCandle = { ...newData[newData.length - 1] };
        
        const volatility = lastCandle.close * 0.001;
        const change = (Math.random() - 0.5) * volatility * 2;
        
        lastCandle.close = Number((lastCandle.close + change).toFixed(2));
        lastCandle.high = Math.max(lastCandle.high, lastCandle.close);
        lastCandle.low = Math.min(lastCandle.low, lastCandle.close);
        lastCandle.volume += Math.floor(Math.random() * 50000);
        
        newData[newData.length - 1] = lastCandle;
        return newData;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isLive]);

  // Map patterns to price levels for overlay
  const patternOverlays = useMemo(() => {
    if (!showPatternOverlay || patterns.length === 0) return [];

    return patterns.slice(0, 5).map((pattern, idx) => {
      const basePrice = candleData.length > 0 
        ? candleData[candleData.length - 1].close 
        : currentPrice;
      
      const offset = (idx - 2) * (basePrice * 0.01);
      const priceLevel = basePrice + offset;
      
      return {
        pattern,
        priceLevel,
        startIndex: Math.max(0, candleData.length - 20 - idx * 5),
        endIndex: candleData.length - 1,
      };
    });
  }, [patterns, candleData, showPatternOverlay, currentPrice]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.[0]) return null;
    
    const data = payload[0].payload as CandleData;
    const isGreen = data.close >= data.open;
    
    return (
      <div className="rounded-lg border border-border bg-card p-3 shadow-lg">
        <div className="mb-2 text-xs text-muted-foreground">
          {data.timestamp.toLocaleTimeString()}
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <span className="text-muted-foreground">Open:</span>
          <span className="font-mono text-foreground">${data.open.toLocaleString()}</span>
          <span className="text-muted-foreground">High:</span>
          <span className="font-mono text-foreground">${data.high.toLocaleString()}</span>
          <span className="text-muted-foreground">Low:</span>
          <span className="font-mono text-foreground">${data.low.toLocaleString()}</span>
          <span className="text-muted-foreground">Close:</span>
          <span className={`font-mono font-medium ${isGreen ? "text-success" : "text-destructive"}`}>
            ${data.close.toLocaleString()}
          </span>
          <span className="text-muted-foreground">Volume:</span>
          <span className="font-mono text-foreground">{(data.volume / 1000000).toFixed(2)}M</span>
        </div>
      </div>
    );
  };

  // Calculate chart data for candlestick visualization
  const chartData = useMemo(() => {
    const visibleCandles = Math.floor(60 / zoomLevel);
    const startIdx = Math.max(0, candleData.length - visibleCandles);
    
    return candleData.slice(startIdx).map((candle) => ({
      ...candle,
      // For bar chart - height of body
      bodyHeight: Math.abs(candle.close - candle.open),
      // Base for the body
      bodyBase: Math.min(candle.open, candle.close),
      // Wick data
      wickHigh: candle.high,
      wickLow: candle.low,
      // Color indicator
      isGreen: candle.close >= candle.open,
    }));
  }, [candleData, zoomLevel]);

  const minPrice = useMemo(() => {
    if (chartData.length === 0) return currentPrice * 0.95;
    return Math.min(...chartData.map((d) => d.low)) * 0.999;
  }, [chartData, currentPrice]);

  const maxPrice = useMemo(() => {
    if (chartData.length === 0) return currentPrice * 1.05;
    return Math.max(...chartData.map((d) => d.high)) * 1.001;
  }, [chartData, currentPrice]);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.5, 3));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.5, 0.5));
  const handleReset = () => setZoomLevel(1);

  return (
    <Card className="border-border bg-card overflow-hidden">
      {/* Chart Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/30 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-foreground">Interactive Chart</h3>
          </div>
          <Badge variant="outline" className="font-mono">
            {instrument} • {timeframe}
          </Badge>
          {isLive && (
            <Badge className="bg-success/10 text-success border-success/20">
              <span className="mr-1.5 h-2 w-2 animate-pulse rounded-full bg-success" />
              Live
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom Controls */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-background p-1">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="w-12 text-center text-xs text-muted-foreground">
              {(zoomLevel * 100).toFixed(0)}%
            </span>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleReset}>
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>

          {/* Toggle Controls */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch
                checked={showPatternOverlay}
                onCheckedChange={setShowPatternOverlay}
                id="pattern-overlay"
              />
              <label htmlFor="pattern-overlay" className="text-xs text-muted-foreground cursor-pointer">
                <Layers className="inline h-3 w-3 mr-1" />
                Patterns
              </label>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={showVolume}
                onCheckedChange={setShowVolume}
                id="volume-overlay"
              />
              <label htmlFor="volume-overlay" className="text-xs text-muted-foreground cursor-pointer">
                Volume
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chart */}
      <div className="p-4">
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 60, left: 10, bottom: showVolume ? 60 : 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
            
            <XAxis
              dataKey="time"
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
              tickFormatter={(val) => {
                const candle = chartData.find((d) => d.time === val);
                return candle ? candle.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
              }}
            />
            
            <YAxis
              domain={[minPrice, maxPrice]}
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
              tickFormatter={(val) => `$${val.toLocaleString()}`}
              orientation="right"
            />
            
            <Tooltip content={<CustomTooltip />} />

            {/* Pattern Overlay Areas */}
            {showPatternOverlay && patternOverlays.map((overlay, idx) => (
              <ReferenceArea
                key={overlay.pattern.id}
                x1={overlay.startIndex}
                x2={overlay.endIndex}
                y1={overlay.priceLevel * 0.998}
                y2={overlay.priceLevel * 1.002}
                fill={overlay.pattern.signal === "Bullish" ? "hsl(var(--success))" : 
                      overlay.pattern.signal === "Bearish" ? "hsl(var(--destructive))" : 
                      "hsl(var(--muted))"}
                fillOpacity={0.15}
                stroke={overlay.pattern.signal === "Bullish" ? "hsl(var(--success))" : 
                        overlay.pattern.signal === "Bearish" ? "hsl(var(--destructive))" : 
                        "hsl(var(--muted))"}
                strokeOpacity={0.5}
              />
            ))}

            {/* Pattern Price Lines */}
            {showPatternOverlay && patternOverlays.map((overlay) => (
              <ReferenceLine
                key={`line-${overlay.pattern.id}`}
                y={overlay.priceLevel}
                stroke={overlay.pattern.signal === "Bullish" ? "hsl(var(--success))" : 
                        overlay.pattern.signal === "Bearish" ? "hsl(var(--destructive))" : 
                        "hsl(var(--muted-foreground))"}
                strokeDasharray="5 5"
                strokeOpacity={0.7}
                label={{
                  value: overlay.pattern.name.slice(0, 15),
                  position: "left",
                  fill: "hsl(var(--foreground))",
                  fontSize: 9,
                }}
              />
            ))}

            {/* Candlestick Wicks (High-Low) */}
            <Line
              type="linear"
              dataKey="wickHigh"
              stroke="transparent"
              dot={false}
            />
            
            {/* Candlestick Bodies */}
            <Bar
              dataKey="bodyHeight"
              barSize={Math.max(4, 12 / zoomLevel)}
              stackId="candle"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isGreen ? "hsl(var(--success))" : "hsl(var(--destructive))"}
                  stroke={entry.isGreen ? "hsl(var(--success))" : "hsl(var(--destructive))"}
                />
              ))}
            </Bar>

            {/* High Line */}
            <Line
              type="monotone"
              dataKey="high"
              stroke="hsl(var(--success))"
              strokeWidth={1}
              dot={false}
              opacity={0.3}
            />

            {/* Low Line */}
            <Line
              type="monotone"
              dataKey="low"
              stroke="hsl(var(--destructive))"
              strokeWidth={1}
              dot={false}
              opacity={0.3}
            />

            {/* Close Price Line */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Volume Chart */}
        {showVolume && (
          <ResponsiveContainer width="100%" height={80}>
            <ComposedChart data={chartData} margin={{ top: 0, right: 60, left: 10, bottom: 0 }}>
              <XAxis dataKey="time" hide />
              <YAxis hide />
              <Bar dataKey="volume" barSize={Math.max(4, 12 / zoomLevel)}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`vol-${index}`}
                    fill={entry.isGreen ? "hsl(var(--success))" : "hsl(var(--destructive))"}
                    opacity={0.4}
                  />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Pattern Overlay Legend */}
      {showPatternOverlay && patterns.length > 0 && (
        <div className="border-t border-border bg-muted/20 px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Crosshair className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium text-foreground">Pattern Overlays</span>
          </div>
          <ScrollArea className="max-h-24">
            <div className="flex flex-wrap gap-2">
              {patternOverlays.map((overlay) => (
                <Badge
                  key={overlay.pattern.id}
                  variant="outline"
                  className={`cursor-pointer transition-all hover:scale-105 ${
                    selectedPattern?.id === overlay.pattern.id ? "ring-2 ring-primary" : ""
                  } ${
                    overlay.pattern.signal === "Bullish"
                      ? "border-success/50 bg-success/10 text-success"
                      : overlay.pattern.signal === "Bearish"
                      ? "border-destructive/50 bg-destructive/10 text-destructive"
                      : "border-muted-foreground/50"
                  }`}
                  onClick={() => setSelectedPattern(
                    selectedPattern?.id === overlay.pattern.id ? null : overlay.pattern
                  )}
                >
                  {overlay.pattern.signal === "Bullish" ? (
                    <TrendingUp className="mr-1 h-3 w-3" />
                  ) : overlay.pattern.signal === "Bearish" ? (
                    <TrendingDown className="mr-1 h-3 w-3" />
                  ) : null}
                  {overlay.pattern.name}
                  <span className="ml-1 opacity-70">
                    {(overlay.pattern.confidence * 100).toFixed(0)}%
                  </span>
                </Badge>
              ))}
            </div>
          </ScrollArea>

          {/* Selected Pattern Details */}
          {selectedPattern && (
            <div className="mt-3 rounded-lg border border-border bg-background p-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-foreground">{selectedPattern.name}</span>
                    <Badge variant="secondary" className="text-xs">
                      {selectedPattern.type}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {selectedPattern.priceRange} • {selectedPattern.timeWindow}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => setSelectedPattern(null)}
                >
                  <EyeOff className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};
