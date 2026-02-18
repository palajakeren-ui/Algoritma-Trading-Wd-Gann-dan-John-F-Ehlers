import { useState, useEffect, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Activity,
  Wifi,
  WifiOff,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Zap,
  BarChart3,
  Clock,
  Target,
  FileText,
  Layers,
  LineChart,
  Crosshair,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  Timer,
  CandlestickChart as CandlestickIcon,
} from "lucide-react";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import TradingInstrumentSelector from "@/components/TradingInstrumentSelector";
import useWebSocketPrice from "@/hooks/useWebSocketPrice";

// Pattern Components
import { PatternDetectionPanel } from "@/components/pattern/PatternDetectionPanel";
import { ManualAnalysisPanel } from "@/components/pattern/ManualAnalysisPanel";
import { MultiAssetPanel } from "@/components/pattern/MultiAssetPanel";
import { PatternNarrationPanel } from "@/components/pattern/PatternNarrationPanel";
import { AddPatternForm } from "@/components/pattern/AddPatternForm";
import { WaveAnalysisTabs } from "@/components/pattern/WaveAnalysisTabs";
import { PatternExport } from "@/components/pattern/PatternExport";
import { PatternAlerts } from "@/components/pattern/PatternAlerts";
import { RealtimeMultiTimeframe } from "@/components/pattern/RealtimeMultiTimeframe";
import { PatternAccuracyTracker } from "@/components/pattern/PatternAccuracyTracker";
import { GannSupplyDemandPanel } from "@/components/pattern/GannSupplyDemandPanel";

// Types and Utils
import {
  DetectedPattern,
  ManualAnalysis,
  AssetAnalysis,
  TIMEFRAMES,
  getInitialPatterns,
} from "@/lib/patternUtils";

const PatternRecognition = () => {
  // State Management
  const [selectedInstrument, setSelectedInstrument] = useState("BTCUSDT");
  const [selectedTimeframe, setSelectedTimeframe] = useState("H1");
  const [activeTab, setActiveTab] = useState("detection");

  // Pattern States
  const [autoPatterns, setAutoPatterns] = useState<DetectedPattern[]>([]);
  const [manualPatterns, setManualPatterns] = useState<DetectedPattern[]>(() =>
    getInitialPatterns("BTCUSDT")
  );

  // Manual Analysis State
  const [manualAnalyses, setManualAnalyses] = useState<ManualAnalysis[]>([]);

  // Multi-Asset State
  const [assetAnalyses, setAssetAnalyses] = useState<AssetAnalysis[]>([
    {
      id: "1",
      symbol: "BTCUSDT",
      name: "Bitcoin",
      timeframes: ["H1", "H4", "D1", "Y1"],
      lastUpdated: new Date(),
      patternCount: 5,
    },
  ]);

  // WebSocket Price Hook
  const { priceData, isConnected, isLive, toggleConnection } = useWebSocketPrice({
    symbol: selectedInstrument,
    enabled: true,
    updateInterval: 2000,
  });

  const [candleData, setCandleData] = useState<any[]>([]);

  // Helpers for Timeframe Synchronization
  const getTimeframeInMs = (tf: string) => {
    if (tf.startsWith('M')) {
      const mins = parseInt(tf.substring(1)) || 1;
      return mins * 60 * 1000;
    }
    if (tf.startsWith('H')) {
      const hours = parseInt(tf.substring(1)) || 1;
      return hours * 60 * 60 * 1000;
    }
    if (tf.startsWith('D')) return 24 * 60 * 60 * 1000;
    if (tf.startsWith('W')) return 7 * 24 * 60 * 60 * 1000;
    if (tf === 'MN1') return 30 * 24 * 60 * 60 * 1000;
    if (tf === 'Y1') return 365 * 24 * 60 * 60 * 1000;
    return 60 * 1000;
  };

  const timeframeLabel = TIMEFRAMES.find(tf => tf.value === selectedTimeframe)?.label || selectedTimeframe;

  // Reset candle data when instrument or timeframe changes
  useEffect(() => {
    setCandleData([]);
  }, [selectedInstrument, selectedTimeframe]);

  // Initialize and Update Candlestick Data
  useEffect(() => {
    if (priceData.price <= 0) return;

    const interval = getTimeframeInMs(selectedTimeframe);

    const generateInitialCandles = (basePrice: number) => {
      const now = Date.now();
      const tfFactor = Math.sqrt(interval / 60000);
      const volatility = 0.005 * tfFactor;

      return Array.from({ length: 60 }, (_, i) => {
        const timestamp = now - (60 - i) * interval;
        const base = basePrice + Math.sin(i / 10) * (basePrice * volatility * 2);

        const open = base + (Math.random() - 0.5) * (basePrice * volatility * 0.5);
        const close = base + (Math.random() - 0.5) * (basePrice * volatility * 0.5);
        const high = Math.max(open, close) + Math.random() * (basePrice * volatility * 0.2);
        const low = Math.min(open, close) - Math.random() * (basePrice * volatility * 0.2);

        return {
          time: new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            ...(interval >= 24 * 60 * 60 * 1000 ? { day: '2-digit', month: 'short', year: 'numeric' } : {})
          }),
          date: new Date(timestamp).toLocaleDateString(),
          open,
          high,
          low,
          close,
          volume: 1000000 * tfFactor * (0.5 + Math.random())
        };
      });
    };

    if (candleData.length === 0) {
      setCandleData(generateInitialCandles(priceData.price));
    } else {
      setCandleData(prev => {
        const newData = [...prev];
        const lastCandle = { ...newData[newData.length - 1] };
        lastCandle.close = priceData.price;
        if (priceData.price > lastCandle.high) lastCandle.high = priceData.price;
        if (priceData.price < lastCandle.low) lastCandle.low = priceData.price;
        newData[newData.length - 1] = lastCandle;
        return newData;
      });
    }
  }, [priceData.price, selectedTimeframe, selectedInstrument]);

  // Calculate technical indicators for the chart
  const candleDataWithIndicators = useMemo(() => {
    return candleData.map((d, i, arr) => {
      const sma7 = i >= 6 ? arr.slice(i - 6, i + 1).reduce((acc, curr) => acc + curr.close, 0) / 7 : d.close;
      const sma25 = i >= 24 ? arr.slice(i - 24, i + 1).reduce((acc, curr) => acc + curr.close, 0) / 25 : d.close;
      return { ...d, sma7, sma25 };
    });
  }, [candleData]);

  const currentPrice = priceData.price;
  const priceChange = priceData.change || 0;
  const priceChangePercent = priceData.changePercent || 0;

  // Combine all patterns for narration
  const allPatterns = [...autoPatterns, ...manualPatterns];

  // Statistics
  const bullishCount = allPatterns.filter(p => p.signal === "Bullish").length;
  const bearishCount = allPatterns.filter(p => p.signal === "Bearish").length;
  const highConfCount = allPatterns.filter(p => p.confidence >= 0.8).length;

  // Handlers
  const handleAutoPatternsDetected = (patterns: DetectedPattern[]) => {
    setAutoPatterns(patterns);
  };

  const handleDeleteAutoPattern = (id: string) => {
    setAutoPatterns((prev) => prev.filter((p) => p.id !== id));
  };

  const handleAddManualPattern = (pattern: DetectedPattern) => {
    setManualPatterns((prev) => [...prev, pattern]);
  };

  const handleDeleteManualPattern = (id: string) => {
    setManualPatterns((prev) => prev.filter((p) => p.id !== id));
  };

  const handleAddManualAnalysis = (analysis: ManualAnalysis) => {
    setManualAnalyses((prev) => [...prev, analysis]);
  };

  const handleDeleteManualAnalysis = (id: string) => {
    setManualAnalyses((prev) => prev.filter((a) => a.id !== id));
  };

  const handleAddAsset = (asset: AssetAnalysis) => {
    setAssetAnalyses((prev) => [...prev, asset]);
  };

  const handleUpdateAsset = (id: string) => {
    setAssetAnalyses((prev) =>
      prev.map((a) => (a.id === id ? { ...a, lastUpdated: new Date() } : a))
    );
  };

  const handleDeleteAsset = (id: string) => {
    setAssetAnalyses((prev) => prev.filter((a) => a.id !== id));
  };

  const handleMultiTimeframeUpdate = (patterns: DetectedPattern[]) => {
    setAutoPatterns(patterns);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Header */}
      <div className="relative overflow-hidden border-b border-border bg-gradient-to-br from-primary/5 via-background to-accent/5">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="relative px-4 py-6 md:px-6 md:py-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            {/* Title Section */}
            <div className="flex items-start gap-4">
              <div className="rounded-2xl bg-gradient-to-br from-primary to-primary/60 p-3 shadow-lg shadow-primary/20">
                <Activity className="h-8 w-8 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
                  Pattern Recognition
                </h1>
                <p className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                  <Sparkles className="h-4 w-4" />
                  Price & Time Analysis • Gann • Elliott • Harmonic
                </p>
              </div>
            </div>

            {/* Price & Connection Panel */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Export & Alerts */}
              <PatternExport
                patterns={allPatterns}
                manualAnalyses={manualAnalyses}
                assets={assetAnalyses}
                instrument={selectedInstrument}
                timeframe={selectedTimeframe}
              />
              <PatternAlerts
                patterns={allPatterns}
                instrument={selectedInstrument}
              />

              {/* Connection Status */}
              <div className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium ${isConnected
                ? "bg-success/10 text-success border border-success/20"
                : "bg-destructive/10 text-destructive border border-destructive/20"
                }`}>
                {isConnected ? (
                  <Wifi className="h-4 w-4" />
                ) : (
                  <WifiOff className="h-4 w-4" />
                )}
                {isConnected ? "Live" : "Offline"}
              </div>

              {/* Price Display */}
              <div className="flex items-center gap-3 rounded-xl bg-card border border-border px-4 py-2 shadow-sm">
                <div>
                  <div className="text-xs text-muted-foreground">{selectedInstrument}</div>
                  <div className="text-xl font-bold font-mono text-foreground">
                    ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className={`flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-medium ${priceChange >= 0
                  ? "bg-success/10 text-success"
                  : "bg-destructive/10 text-destructive"
                  }`}>
                  {priceChange >= 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {priceChangePercent >= 0 ? "+" : ""}{priceChangePercent.toFixed(2)}%
                </div>
              </div>

              {/* Refresh Button */}
              <Button
                variant="outline"
                size="icon"
                onClick={toggleConnection}
                className="rounded-xl"
              >
                <RefreshCw className={`h-4 w-4 ${isLive ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
            <Card className="flex items-center gap-3 border-border bg-card/50 backdrop-blur p-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <div>
                <div className="text-2xl font-bold text-foreground">{allPatterns.length}</div>
                <div className="text-xs text-muted-foreground">Total Patterns</div>
              </div>
            </Card>
            <Card className="flex items-center gap-3 border-border bg-card/50 backdrop-blur p-3">
              <div className="rounded-lg bg-success/10 p-2">
                <TrendingUp className="h-5 w-5 text-success" />
              </div>
              <div>
                <div className="text-2xl font-bold text-success">{bullishCount}</div>
                <div className="text-xs text-muted-foreground">Bullish</div>
              </div>
            </Card>
            <Card className="flex items-center gap-3 border-border bg-card/50 backdrop-blur p-3">
              <div className="rounded-lg bg-destructive/10 p-2">
                <TrendingDown className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <div className="text-2xl font-bold text-destructive">{bearishCount}</div>
                <div className="text-xs text-muted-foreground">Bearish</div>
              </div>
            </Card>
            <Card className="flex items-center gap-3 border-border bg-card/50 backdrop-blur p-3">
              <div className="rounded-lg bg-accent/10 p-2">
                <Target className="h-5 w-5 text-accent" />
              </div>
              <div>
                <div className="text-2xl font-bold text-accent">{highConfCount}</div>
                <div className="text-xs text-muted-foreground">High Conf.</div>
              </div>
            </Card>
            <Card className="flex items-center gap-3 border-border bg-card/50 backdrop-blur p-3">
              <div className="rounded-lg bg-muted p-2">
                <Layers className="h-5 w-5 text-foreground" />
              </div>
              <div>
                <div className="text-2xl font-bold text-foreground">{assetAnalyses.length}</div>
                <div className="text-xs text-muted-foreground">Assets</div>
              </div>
            </Card>
            <Card className="flex items-center gap-3 border-border bg-card/50 backdrop-blur p-3">
              <div className="rounded-lg bg-muted p-2">
                <FileText className="h-5 w-5 text-foreground" />
              </div>
              <div>
                <div className="text-2xl font-bold text-foreground">{manualAnalyses.length}</div>
                <div className="text-xs text-muted-foreground">Analyses</div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-4 md:p-6">
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          {/* Left Sidebar - Controls */}
          <div className="space-y-4">
            {/* Instrument Selector */}
            <Card className="border-border bg-card p-4">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
                <Crosshair className="h-4 w-4 text-primary" />
                Instrument
              </h3>
              <TradingInstrumentSelector
                onInstrumentChange={(symbol) => setSelectedInstrument(symbol)}
                compact
              />
            </Card>

            {/* Timeframe Selector */}
            <Card className="border-border bg-card p-4">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
                <Clock className="h-4 w-4 text-primary" />
                Timeframe
              </h3>
              <ScrollArea className="h-[200px] pr-3">
                <div className="grid grid-cols-3 gap-1.5">
                  {TIMEFRAMES.map((tf) => (
                    <Button
                      key={tf.value}
                      variant={selectedTimeframe === tf.value ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setSelectedTimeframe(tf.value)}
                      className={`text-xs font-mono ${selectedTimeframe === tf.value
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                        }`}
                    >
                      {tf.value}
                    </Button>
                  ))}
                </div>
              </ScrollArea>
            </Card>

            {/* Quick Navigation */}
            <Card className="border-border bg-card p-4">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
                <BarChart3 className="h-4 w-4 text-primary" />
                Quick Nav
              </h3>
              <div className="space-y-1">
                {[
                  { id: "chart", label: "Live Chart", icon: CandlestickIcon },
                  { id: "detection", label: "Auto Detection", icon: Zap },
                  { id: "realtime-mtf", label: "Real-Time MTF", icon: Timer },
                  { id: "accuracy", label: "Accuracy Track", icon: Target },
                  { id: "manual", label: "Manual Entry", icon: FileText },
                  { id: "multi-asset", label: "Multi-Asset", icon: Layers },
                  { id: "gann-sd", label: "Gann S&D", icon: Target },
                  { id: "waves", label: "Wave Analysis", icon: LineChart },
                ].map((item) => (
                  <Button
                    key={item.id}
                    variant={activeTab === item.id ? "secondary" : "ghost"}
                    size="sm"
                    className="w-full justify-start gap-2"
                    onClick={() => setActiveTab(item.id)}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                    <ChevronRight className="ml-auto h-4 w-4 opacity-50" />
                  </Button>
                ))}
              </div>
            </Card>

            {/* Pattern Summary Mini */}
            <Card className="border-border bg-gradient-to-br from-primary/5 to-accent/5 p-4">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
                <AlertTriangle className="h-4 w-4 text-primary" />
                Summary
              </h3>
              <div className="space-y-2 text-xs">
                {allPatterns.slice(0, 3).map((p) => (
                  <div
                    key={p.id}
                    className={`flex items-center gap-2 rounded-lg p-2 ${p.signal === "Bullish"
                      ? "bg-success/10 text-success"
                      : p.signal === "Bearish"
                        ? "bg-destructive/10 text-destructive"
                        : "bg-muted text-muted-foreground"
                      }`}
                  >
                    {p.signal === "Bullish" ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : p.signal === "Bearish" ? (
                      <TrendingDown className="h-3 w-3" />
                    ) : null}
                    <span className="truncate font-medium">{p.name}</span>
                  </div>
                ))}
                {allPatterns.length > 3 && (
                  <div className="text-center text-muted-foreground">
                    +{allPatterns.length - 3} more patterns
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Right Content Area */}
          <div className="space-y-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="flex w-full flex-wrap bg-muted/50 p-1 h-auto gap-1">
                <TabsTrigger value="chart" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <CandlestickIcon className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Live Chart</span>
                  <span className="sm:hidden">Chart</span>
                </TabsTrigger>
                <TabsTrigger value="detection" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <Zap className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Detection</span>
                  <span className="sm:hidden">Auto</span>
                </TabsTrigger>
                <TabsTrigger value="realtime-mtf" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <Timer className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">MTF</span>
                  <span className="sm:hidden">MTF</span>
                </TabsTrigger>
                <TabsTrigger value="accuracy" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <Target className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Accuracy</span>
                  <span className="sm:hidden">Track</span>
                </TabsTrigger>
                <TabsTrigger value="manual" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <FileText className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Manual</span>
                  <span className="sm:hidden">Manual</span>
                </TabsTrigger>
                <TabsTrigger value="multi-asset" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <Layers className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Assets</span>
                  <span className="sm:hidden">Assets</span>
                </TabsTrigger>
                <TabsTrigger value="waves" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <LineChart className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Waves</span>
                  <span className="sm:hidden">Waves</span>
                </TabsTrigger>
                <TabsTrigger value="gann-sd" className="gap-1.5 text-xs flex-1 min-w-[80px]">
                  <Target className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Gann S&D</span>
                  <span className="sm:hidden">S&D</span>
                </TabsTrigger>
              </TabsList>

              {/* Live Chart Tab */}
              <TabsContent value="chart" className="mt-6 space-y-6">
                <div className="space-y-4">
                  <Card className="p-6 border-border bg-card overflow-hidden">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-4">
                        <div className="rounded-xl bg-primary/10 p-2">
                          <CandlestickIcon className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold flex items-center gap-2">
                            {selectedInstrument} <span className="text-muted-foreground font-normal">/ {timeframeLabel}</span>
                          </h3>
                          <p className="text-xs text-muted-foreground">Real-time OHLC Feed • Technical Overlays</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-success text-success bg-success/5 animate-pulse">
                          <Wifi className="h-3 w-3 mr-1" /> LIVE
                        </Badge>
                        <Badge variant="secondary" className="font-mono">{selectedTimeframe}</Badge>
                      </div>
                    </div>

                    <div className="relative group">
                      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
                      <CandlestickChart
                        data={candleDataWithIndicators}
                        height={480}
                        indicatorKeys={['sma7', 'sma25']}
                      />
                    </div>
                  </Card>

                  {/* Market Stats Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: "O", value: candleData[candleData.length - 1]?.open, color: "text-foreground" },
                      { label: "H", value: candleData[candleData.length - 1]?.high, color: "text-success" },
                      { label: "L", value: candleData[candleData.length - 1]?.low, color: "text-destructive" },
                      { label: "C", value: candleData[candleData.length - 1]?.close, color: "text-primary" },
                    ].map((stat, i) => (
                      <Card key={i} className="bg-card/50 border-border p-3 flex items-center justify-between">
                        <span className="text-xs font-bold text-muted-foreground">{stat.label}</span>
                        <span className={`font-mono text-sm font-bold ${stat.color}`}>
                          ${stat.value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </Card>
                    ))}
                  </div>
                </div>
              </TabsContent>

              {/* Auto Detection Tab */}
              <TabsContent value="detection" className="mt-6 space-y-6">
                <PatternDetectionPanel
                  currentPrice={currentPrice}
                  instrument={selectedInstrument}
                  timeframe={selectedTimeframe}
                  patterns={autoPatterns}
                  onPatternsDetected={handleAutoPatternsDetected}
                  onDeletePattern={handleDeleteAutoPattern}
                />

                {/* Pattern Narration */}
                <PatternNarrationPanel patterns={allPatterns} />
              </TabsContent>

              {/* Real-Time Multi-Timeframe Tab */}
              <TabsContent value="realtime-mtf" className="mt-6">
                <RealtimeMultiTimeframe
                  currentPrice={currentPrice}
                  instrument={selectedInstrument}
                  onPatternsUpdated={handleMultiTimeframeUpdate}
                />
              </TabsContent>

              {/* Accuracy Tracking Tab */}
              <TabsContent value="accuracy" className="mt-6">
                <PatternAccuracyTracker
                  patterns={allPatterns}
                  currentPrice={currentPrice}
                  instrument={selectedInstrument}
                />
              </TabsContent>

              {/* Manual Entry Tab */}
              <TabsContent value="manual" className="mt-6 space-y-6">
                <ManualAnalysisPanel
                  instrument={selectedInstrument}
                  currentPrice={currentPrice}
                  analyses={manualAnalyses}
                  onAddAnalysis={handleAddManualAnalysis}
                  onDeleteAnalysis={handleDeleteManualAnalysis}
                />

                <AddPatternForm
                  instrument={selectedInstrument}
                  timeframe={selectedTimeframe}
                  patterns={manualPatterns}
                  onAddPattern={handleAddManualPattern}
                  onDeletePattern={handleDeleteManualPattern}
                />
              </TabsContent>

              {/* Multi-Asset Tab */}
              <TabsContent value="multi-asset" className="mt-6">
                <MultiAssetPanel
                  assets={assetAnalyses}
                  onAddAsset={handleAddAsset}
                  onUpdateAsset={handleUpdateAsset}
                  onDeleteAsset={handleDeleteAsset}
                />
              </TabsContent>

              {/* Wave Analysis Tab */}
              <TabsContent value="waves" className="mt-6">
                <WaveAnalysisTabs currentPrice={currentPrice} candleData={candleDataWithIndicators} />
              </TabsContent>

              {/* Gann Supply & Demand Tab */}
              <TabsContent value="gann-sd" className="mt-6">
                <GannSupplyDemandPanel
                  currentPrice={currentPrice}
                  instrument={selectedInstrument}
                  timeframe={selectedTimeframe}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatternRecognition;
