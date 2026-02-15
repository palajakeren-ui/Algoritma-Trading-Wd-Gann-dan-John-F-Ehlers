import { useState, useMemo, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Play,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Zap,
  Shield,
  Activity,
  Layers,
  Upload,
  Download
} from "lucide-react";
import { toast } from "sonner";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, ComposedChart } from "recharts";

// Gann Strategies
const GANN_STRATEGIES = [
  { id: "gann-square-9", name: "Gann Square of 9", description: "Spiral price levels from center value" },
  { id: "gann-angles", name: "Gann Angles (1x1, 2x1, etc.)", description: "Time-price relationship angles" },
  { id: "gann-fan", name: "Gann Fan", description: "Multiple angle lines from pivot point" },
  { id: "gann-time-cycles", name: "Gann Time Cycles", description: "Cyclical time-based projections" },
  { id: "gann-support-resistance", name: "Gann Support/Resistance", description: "Pivot-based S/R levels" },
  { id: "gann-fibonacci", name: "Gann Fibonacci Levels", description: "Combined Gann-Fibonacci analysis" },
  { id: "gann-wave", name: "Gann Wave Analysis", description: "Wave structure identification" },
  { id: "gann-hexagon", name: "Gann Hexagon", description: "Geometric hexagon price patterns" },
  { id: "gann-astro-sync", name: "Astro Sync", description: "Planetary time synchronization" },
];

// Ehlers Strategies
const EHLERS_STRATEGIES = [
  { id: "ehlers-mama-fama", name: "MAMA/FAMA", description: "Mesa Adaptive Moving Average" },
  { id: "ehlers-fisher", name: "Fisher Transform", description: "Gaussian price normalization" },
  { id: "ehlers-bandpass", name: "Bandpass Filter", description: "Cyclical component extraction" },
  { id: "ehlers-super-smoother", name: "Super Smoother", description: "Lag-reduced price smoothing" },
  { id: "ehlers-roofing", name: "Roofing Filter", description: "HP + LP filtering combination" },
  { id: "ehlers-cyber-cycle", name: "Cyber Cycle", description: "Market cycle identification" },
  { id: "ehlers-decycler", name: "Decycler", description: "Trend extraction filter" },
  { id: "ehlers-instantaneous-trend", name: "Instantaneous Trend", description: "Real-time trend following" },
  { id: "ehlers-dominant-cycle", name: "Dominant Cycle", description: "Period measurement model" },
];

interface ManualInstrument {
  id: string;
  symbol: string;
  name: string;
  type: string;
  exchange: string;
}

interface BacktestConfig {
  // General
  startDate: string;
  endDate: string;
  initialCapital: number;

  // Risk Management
  riskMode: "dynamic" | "fixed";
  kellyFraction: number;
  volatilityAdjusted: boolean;
  maxDailyDrawdown: number;
  dynamicPositionScaling: boolean;
  fixedRiskPercent: number;
  fixedLotSize: number;
  fixedStopLoss: number;
  fixedTakeProfit: number;
  riskLimitPerTrade: number;
  exitMode: "ticks" | "rr";
  riskRewardRatio: number;

  // Strategies
  selectedGannStrategies: string[];
  selectedEhlersStrategies: string[];

  // Strategy Parameters
  gannAngle: number;
  gannTimeUnit: number;
  gannCycleLength: number;
  ehlersFilterPeriod: number;
  ehlersBandwidth: number;
  ehlersFastLimit: number;
  ehlersSlowLimit: number;
}

interface BacktestResult {
  trades: TradeResult[];
  metrics: BacktestMetrics;
  equityCurve: { date: string; equity: number; drawdown: number }[];
  monthlyReturns: { month: string; return: number }[];
}

interface TradeResult {
  id: number;
  instrument: string;
  strategy: string;
  direction: "LONG" | "SHORT";
  entryDate: string;
  exitDate: string;
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  pnlPercent: number;
  holdingPeriod: string;
}

interface BacktestMetrics {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnL: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  calmarRatio: number;
  avgHoldingPeriod: string;
  expectancy: number;
}

export const BacktestSimulator = ({ hftConfig }: { hftConfig?: any }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [hasResults, setHasResults] = useState(false);

  // Sync with HFT Config
  useEffect(() => {
    if (hftConfig) {
      const gannStrats = [];
      if (hftConfig.useGannSquare9) gannStrats.push("gann-square-9");
      if (hftConfig.useGannAngles) gannStrats.push("gann-angles");
      if (hftConfig.useGannTimeCycles) gannStrats.push("gann-time-cycles");
      if (hftConfig.useGannSR) gannStrats.push("gann-support-resistance");
      if (hftConfig.useGannFibo) gannStrats.push("gann-fibonacci");
      if (hftConfig.useGannWave) gannStrats.push("gann-wave");
      if (hftConfig.useGannHexagon) gannStrats.push("gann-hexagon");
      if (hftConfig.useGannAstro) gannStrats.push("gann-astro-sync");

      const ehlersStrats = [];
      if (hftConfig.useEhlersMAMAFAMA) ehlersStrats.push("ehlers-mama-fama");
      if (hftConfig.useEhlersFisher) ehlersStrats.push("ehlers-fisher");
      if (hftConfig.useEhlersBandpass) ehlersStrats.push("ehlers-bandpass");
      if (hftConfig.useEhlersSuperSmoother) ehlersStrats.push("ehlers-super-smoother");
      if (hftConfig.useEhlersRoofing) ehlersStrats.push("ehlers-roofing");
      if (hftConfig.useEhlersCyberCycle) ehlersStrats.push("ehlers-cyber-cycle");
      if (hftConfig.useEhlersDecycler) ehlersStrats.push("ehlers-decycler");
      if (hftConfig.useEhlersInstaTrend) ehlersStrats.push("ehlers-instantaneous-trend");
      if (hftConfig.useEhlersDominantCycle) ehlersStrats.push("ehlers-dominant-cycle");

      setConfig(prev => ({
        ...prev,
        selectedGannStrategies: gannStrats,
        selectedEhlersStrategies: ehlersStrats
      }));
    }
  }, [hftConfig]);

  // Manual instruments
  const [manualInstruments, setManualInstruments] = useState<ManualInstrument[]>([
    { id: "1", symbol: "BTCUSDT", name: "Bitcoin", type: "Crypto", exchange: "Binance" },
  ]);
  const [newInstrument, setNewInstrument] = useState({
    symbol: "",
    name: "",
    type: "Crypto",
    exchange: "Binance",
  });

  // Selected instruments for backtest
  const [selectedInstruments, setSelectedInstruments] = useState<string[]>(["BTCUSDT"]);

  // Backtest configuration
  const [config, setConfig] = useState<BacktestConfig>({
    startDate: "2024-01-01",
    endDate: "2024-12-31",
    initialCapital: 100000,

    riskMode: "dynamic",
    kellyFraction: 0.25,
    volatilityAdjusted: true,
    maxDailyDrawdown: 5.0,
    dynamicPositionScaling: true,
    fixedRiskPercent: 1.0,
    fixedLotSize: 0.1,
    fixedStopLoss: 50,
    fixedTakeProfit: 100,
    riskLimitPerTrade: 0.1,
    exitMode: "ticks",
    riskRewardRatio: 2.0,

    selectedGannStrategies: ["gann-angles", "gann-support-resistance"],
    selectedEhlersStrategies: ["ehlers-mama-fama", "ehlers-super-smoother"],

    gannAngle: 45,
    gannTimeUnit: 1,
    gannCycleLength: 30,
    ehlersFilterPeriod: 20,
    ehlersBandwidth: 0.3,
    ehlersFastLimit: 0.5,
    ehlersSlowLimit: 0.05,
  });

  // Simulated results
  const [results, setResults] = useState<BacktestResult | null>(null);

  const addManualInstrument = () => {
    if (!newInstrument.symbol || !newInstrument.name) {
      toast.error("Please fill in symbol and name");
      return;
    }

    const instrument: ManualInstrument = {
      id: Date.now().toString(),
      ...newInstrument,
    };

    setManualInstruments(prev => [...prev, instrument]);
    setNewInstrument({ symbol: "", name: "", type: "Crypto", exchange: "Binance" });
    toast.success(`Added ${instrument.symbol}`);
  };

  const removeInstrument = (id: string) => {
    setManualInstruments(prev => prev.filter(i => i.id !== id));
  };

  const toggleStrategy = (strategyId: string, type: "gann" | "ehlers") => {
    setConfig(prev => {
      const key = type === "gann" ? "selectedGannStrategies" : "selectedEhlersStrategies";
      const current = prev[key];
      if (current.includes(strategyId)) {
        return { ...prev, [key]: current.filter(s => s !== strategyId) };
      } else {
        return { ...prev, [key]: [...current, strategyId] };
      }
    });
  };

  const toggleInstrument = (symbol: string) => {
    setSelectedInstruments(prev => {
      if (prev.includes(symbol)) {
        return prev.filter(s => s !== symbol);
      } else {
        return [...prev, symbol];
      }
    });
  };

  const runBacktest = () => {
    if (selectedInstruments.length === 0) {
      toast.error("Please select at least one instrument");
      return;
    }

    if (config.selectedGannStrategies.length === 0 && config.selectedEhlersStrategies.length === 0) {
      toast.error("Please select at least one strategy");
      return;
    }

    setIsRunning(true);
    toast.info("Running backtest simulation...");

    // Simulate backtest (in real implementation, this would run actual calculations)
    setTimeout(() => {
      const simulatedResults = generateSimulatedResults();
      setResults(simulatedResults);
      setIsRunning(false);
      setHasResults(true);
      toast.success("Backtest completed!");
    }, 2000);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      toast.success(`Loaded historical data: ${file.name}`);
      // In a real app, parse the file here
    }
  };

  const handleDownloadResults = () => {
    if (!results) {
      toast.error("No results to download");
      return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(results, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "backtest_results.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    toast.success("Results downloaded");
  };

  const generateSimulatedResults = (): BacktestResult => {
    const trades: TradeResult[] = [];
    const strategies = [...config.selectedGannStrategies, ...config.selectedEhlersStrategies];

    let tradeId = 1;
    for (let i = 0; i < 50; i++) {
      const isWin = Math.random() > 0.45;
      const strategy = strategies[Math.floor(Math.random() * strategies.length)];
      const strategyName = [...GANN_STRATEGIES, ...EHLERS_STRATEGIES].find(s => s.id === strategy)?.name || strategy;
      const instrument = selectedInstruments[Math.floor(Math.random() * selectedInstruments.length)];
      const direction = Math.random() > 0.5 ? "LONG" : "SHORT";
      const entryPrice = 40000 + Math.random() * 20000;
      const pnlPercent = isWin ? Math.random() * 5 : -Math.random() * 3;
      const exitPrice = entryPrice * (1 + pnlPercent / 100 * (direction === "LONG" ? 1 : -1));
      const size = config.riskMode === "fixed" ? config.fixedLotSize : 0.1 + Math.random() * 0.4;

      trades.push({
        id: tradeId++,
        instrument,
        strategy: strategyName,
        direction,
        entryDate: `2024-${String(Math.floor(i / 5) + 1).padStart(2, '0')}-${String((i % 28) + 1).padStart(2, '0')}`,
        exitDate: `2024-${String(Math.floor(i / 5) + 1).padStart(2, '0')}-${String(((i % 28) + 2) % 28 + 1).padStart(2, '0')}`,
        entryPrice,
        exitPrice,
        size,
        pnl: (exitPrice - entryPrice) * size * (direction === "LONG" ? 1 : -1),
        pnlPercent,
        holdingPeriod: `${Math.floor(Math.random() * 48) + 1}h`,
      });
    }

    const wins = trades.filter(t => t.pnl > 0);
    const losses = trades.filter(t => t.pnl < 0);
    const totalPnL = trades.reduce((sum, t) => sum + t.pnl, 0);
    const avgWin = wins.length > 0 ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length : 0;
    const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length) : 0;

    const metrics: BacktestMetrics = {
      totalTrades: trades.length,
      winningTrades: wins.length,
      losingTrades: losses.length,
      winRate: (wins.length / trades.length) * 100,
      totalPnL,
      avgWin,
      avgLoss,
      profitFactor: avgLoss > 0 ? (avgWin * wins.length) / (avgLoss * losses.length) : 0,
      maxDrawdown: 5 + Math.random() * 10,
      sharpeRatio: 1.5 + Math.random() * 1.5,
      sortinoRatio: 1.8 + Math.random() * 1.2,
      calmarRatio: 2 + Math.random() * 1,
      avgHoldingPeriod: "12h",
      expectancy: (avgWin * (wins.length / trades.length)) - (avgLoss * (losses.length / trades.length)),
    };

    // Generate equity curve
    let equity = config.initialCapital;
    const equityCurve = [];
    let peak = equity;

    for (let i = 0; i < 252; i++) {
      const dailyReturn = (Math.random() - 0.48) * 0.02;
      equity *= (1 + dailyReturn);
      peak = Math.max(peak, equity);
      const drawdown = ((peak - equity) / peak) * 100;

      equityCurve.push({
        date: `Day ${i + 1}`,
        equity: Math.round(equity),
        drawdown: Number(drawdown.toFixed(2)),
      });
    }

    // Generate monthly returns
    const monthlyReturns = [
      { month: "Jan", return: 2.5 + Math.random() * 3 },
      { month: "Feb", return: -1 + Math.random() * 4 },
      { month: "Mar", return: 1.5 + Math.random() * 2.5 },
      { month: "Apr", return: 3 + Math.random() * 2 },
      { month: "May", return: -0.5 + Math.random() * 3 },
      { month: "Jun", return: 2 + Math.random() * 2 },
      { month: "Jul", return: 1 + Math.random() * 3 },
      { month: "Aug", return: -1.5 + Math.random() * 4 },
      { month: "Sep", return: 2.5 + Math.random() * 2 },
      { month: "Oct", return: 1.8 + Math.random() * 2.5 },
      { month: "Nov", return: 3.2 + Math.random() * 2 },
      { month: "Dec", return: 2 + Math.random() * 3 },
    ];

    return { trades, metrics, equityCurve, monthlyReturns };
  };

  return (
    <div className="space-y-4">
      <Tabs defaultValue="config" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="instruments">Instruments</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
          <TabsTrigger value="results" disabled={!hasResults}>Results</TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-4 mt-4">
          <Card className="p-6 border-border bg-card">
            <div className="flex items-center justify-between mb-6 border-b border-border/40 pb-4">
              <h4 className="font-black text-lg text-foreground flex items-center gap-2">
                <Layers className="w-5 h-5 text-primary" />
                Simulation Configuration
              </h4>
              <div className="flex bg-secondary/30 p-1 rounded-lg border border-border/50">
                <Button
                  variant={config.riskMode === "dynamic" ? "secondary" : "ghost"}
                  size="sm"
                  onClick={() => setConfig(prev => ({ ...prev, riskMode: "dynamic" }))}
                  className={`h-7 text-xs font-bold transition-all ${config.riskMode === "dynamic" ? "bg-accent/10 text-accent shadow-sm" : "text-muted-foreground"}`}
                >
                  <Zap className="w-3 h-3 mr-1" /> Dynamic Risk
                </Button>
                <div className="w-px h-3 bg-border/40 mx-1 self-center" />
                <Button
                  variant={config.riskMode === "fixed" ? "secondary" : "ghost"}
                  size="sm"
                  onClick={() => setConfig(prev => ({ ...prev, riskMode: "fixed" }))}
                  className={`h-7 text-xs font-bold transition-all ${config.riskMode === "fixed" ? "bg-primary/10 text-primary shadow-sm" : "text-muted-foreground"}`}
                >
                  <Shield className="w-3 h-3 mr-1" /> Fixed Risk
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* LEFT COLUMN: General & Data */}
              <div className="lg:col-span-5 space-y-8">
                {/* Time & Capital */}
                <div className="space-y-4">
                  <h5 className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5" /> Period & Capital
                  </h5>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label className="text-[10px] uppercase text-muted-foreground font-bold">Start Date</Label>
                      <Input
                        type="date"
                        value={config.startDate}
                        onChange={(e) => setConfig(prev => ({ ...prev, startDate: e.target.value }))}
                        className="bg-secondary/30 border-border h-9 text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-[10px] uppercase text-muted-foreground font-bold">End Date</Label>
                      <Input
                        type="date"
                        value={config.endDate}
                        onChange={(e) => setConfig(prev => ({ ...prev, endDate: e.target.value }))}
                        className="bg-secondary/30 border-border h-9 text-xs"
                      />
                    </div>
                    <div className="col-span-2 space-y-1.5">
                      <Label className="text-[10px] uppercase text-muted-foreground font-bold">Initial Capital</Label>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                        <Input
                          type="number"
                          value={config.initialCapital}
                          onChange={(e) => setConfig(prev => ({ ...prev, initialCapital: Number(e.target.value) }))}
                          className="bg-secondary/30 border-border h-9 pl-9 font-mono font-bold"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Data Management */}
                <div className="space-y-4 pt-4 border-t border-border/40">
                  <h5 className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                    <Upload className="w-3.5 h-3.5" /> Historical Data
                  </h5>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="relative group">
                      <input
                        type="file"
                        accept=".csv,.json"
                        onChange={handleFileUpload}
                        className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
                      />
                      <Button variant="outline" className="w-full text-xs h-9 border-dashed border-2 group-hover:border-primary/50 transition-colors">
                        Upload File
                      </Button>
                    </div>
                    <Button variant="outline" onClick={handleDownloadResults} disabled={!hasResults} className="w-full text-xs h-9">
                      <Download className="w-3 h-3 mr-2" /> Export
                    </Button>
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN: Risk Parameters (Conditional) */}
              <div className="lg:col-span-7 space-y-6 lg:border-l lg:border-border/40 lg:pl-8">

                {config.riskMode === "dynamic" ? (
                  <div className="space-y-6 animate-in fade-in slide-in-from-right-2 duration-300">
                    <div className="grid grid-cols-2 gap-5">
                      {/* Kelly Fraction */}
                      <div className="space-y-2">
                        <Label className="text-[10px] uppercase font-bold text-muted-foreground">Kelly Fraction</Label>
                        <div className="relative">
                          <Input
                            type="number"
                            step="0.01"
                            value={config.kellyFraction}
                            onChange={(e) => setConfig(prev => ({ ...prev, kellyFraction: parseFloat(e.target.value) }))}
                            className="bg-secondary/30 h-10 font-mono border-accent/30 focus:border-accent"
                          />
                          <span className="absolute right-3 top-3 text-xs font-bold text-accent">x</span>
                        </div>
                        <p className="text-[9px] text-muted-foreground">Optimal f multiplier.</p>
                      </div>

                      {/* Drawdown Limit */}
                      <div className="space-y-2">
                        <Label className="text-[10px] uppercase font-bold text-muted-foreground">Max Daily DD</Label>
                        <div className="relative">
                          <Input
                            type="number"
                            value={config.maxDailyDrawdown}
                            onChange={(e) => setConfig(prev => ({ ...prev, maxDailyDrawdown: parseFloat(e.target.value) }))}
                            className="bg-secondary/30 h-10 font-mono border-destructive/30 focus:border-destructive text-destructive"
                          />
                          <span className="absolute right-3 top-3 text-xs font-bold text-destructive">%</span>
                        </div>
                        <p className="text-[9px] text-muted-foreground">Hard stop threshold.</p>
                      </div>
                    </div>

                    {/* Toggles */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/20 border border-border/50">
                        <div className="space-y-0.5">
                          <p className="text-xs font-bold">Volatility Adjust</p>
                          <p className="text-[9px] text-muted-foreground">Scale by ATR</p>
                        </div>
                        <Switch checked={config.volatilityAdjusted} onCheckedChange={(v) => setConfig(prev => ({ ...prev, volatilityAdjusted: v }))} className="scale-75 origin-right" />
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/20 border border-border/50">
                        <div className="space-y-0.5">
                          <p className="text-xs font-bold">Dynamic Scale</p>
                          <p className="text-[9px] text-muted-foreground">Trend strength sizing</p>
                        </div>
                        <Switch checked={config.dynamicPositionScaling} onCheckedChange={(v) => setConfig(prev => ({ ...prev, dynamicPositionScaling: v }))} className="scale-75 origin-right" />
                      </div>
                    </div>

                    {/* Risk Limit */}
                    <div className="space-y-2 pt-2 border-t border-border/30">
                      <div className="flex justify-between">
                        <Label className="text-[10px] uppercase font-bold text-muted-foreground">Risk Cap Per Trade</Label>
                        <span className="text-xs font-mono font-bold">{config.riskLimitPerTrade}%</span>
                      </div>
                      <Input
                        type="range"
                        min="0.1"
                        max="5"
                        step="0.1"
                        value={config.riskLimitPerTrade}
                        onChange={(e) => setConfig(prev => ({ ...prev, riskLimitPerTrade: parseFloat(e.target.value) }))}
                        className="h-2 bg-secondary"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6 animate-in fade-in slide-in-from-right-2 duration-300">
                    <div className="space-y-2">
                      <Label className="text-[10px] uppercase font-bold text-muted-foreground">Fixed Lot Size</Label>
                      <div className="relative">
                        <Input
                          type="number"
                          step="0.01"
                          value={config.fixedLotSize}
                          onChange={(e) => setConfig(prev => ({ ...prev, fixedLotSize: parseFloat(e.target.value) }))}
                          className="bg-secondary/30 h-10 font-mono border-primary/30 focus:border-primary"
                        />
                        <span className="absolute right-3 top-3 text-xs font-bold text-primary">LOT</span>
                      </div>
                    </div>

                    <Tabs defaultValue="ticks" className="w-full" onValueChange={(val) => setConfig(prev => ({ ...prev, exitMode: val as any }))}>
                      <TabsList className="grid w-full grid-cols-2 mb-4 h-8 bg-secondary/30">
                        <TabsTrigger value="ticks" className="text-[10px] font-bold">TICKS MODE</TabsTrigger>
                        <TabsTrigger value="rr" className="text-[10px] font-bold">RISK : REWARD</TabsTrigger>
                      </TabsList>

                      <TabsContent value="ticks" className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label className="text-[10px] font-bold text-destructive uppercase">Stop Loss</Label>
                            <Input
                              type="number"
                              value={config.fixedStopLoss}
                              onChange={(e) => setConfig(prev => ({ ...prev, fixedStopLoss: parseInt(e.target.value) }))}
                              className="bg-secondary/30 h-9 font-mono text-destructive text-xs"
                              placeholder="Ticks"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label className="text-[10px] font-bold text-success uppercase">Take Profit</Label>
                            <Input
                              type="number"
                              value={config.fixedTakeProfit}
                              onChange={(e) => setConfig(prev => ({ ...prev, fixedTakeProfit: parseInt(e.target.value) }))}
                              className="bg-secondary/30 h-9 font-mono text-success text-xs"
                              placeholder="Ticks"
                            />
                          </div>
                        </div>
                      </TabsContent>

                      <TabsContent value="rr" className="space-y-4">
                        <div className="space-y-2">
                          <Label className="text-[10px] font-bold text-foreground uppercase">Target Ratio (1:R)</Label>
                          <Input
                            type="number"
                            step="0.1"
                            value={config.riskRewardRatio}
                            onChange={(e) => setConfig(prev => ({ ...prev, riskRewardRatio: parseFloat(e.target.value) }))}
                            className="bg-secondary/30 h-9 font-mono text-foreground text-xs"
                          />
                        </div>
                        <div className="rounded bg-secondary/20 p-3 border border-border/50 flex justify-between items-center text-xs">
                          <span className="text-muted-foreground">Implied Reward</span>
                          <span className="font-mono font-bold text-success">
                            +{Math.floor(config.fixedStopLoss * (config.riskRewardRatio || 2))} Ticks
                          </span>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </div>
                )}
              </div>
            </div>

            {/* Action Footer */}
            <div className="mt-8 pt-6 border-t border-border/40 flex justify-center">
              <Button
                size="lg"
                onClick={runBacktest}
                disabled={isRunning}
                className="min-w-[200px] font-bold rounded-xl shadow-lg shadow-primary/10 hover:shadow-primary/20 transition-all"
              >
                {isRunning ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    Running Simulation...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2 fill-current" />
                    Start Backtest
                  </>
                )}
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* Instruments Tab */}
        <TabsContent value="instruments" className="space-y-4 mt-4">
          {/* Add Manual Instrument */}
          <Card className="p-4 border-border bg-card">
            <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <Plus className="w-4 h-4 text-success" />
              Add Manual Instrument
            </h4>
            <div className="grid grid-cols-5 gap-3">
              <div>
                <Label className="text-xs text-muted-foreground">Symbol</Label>
                <Input
                  placeholder="e.g., EURUSD"
                  value={newInstrument.symbol}
                  onChange={(e) => setNewInstrument(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                  className="bg-secondary border-border"
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Name</Label>
                <Input
                  placeholder="e.g., Euro/USD"
                  value={newInstrument.name}
                  onChange={(e) => setNewInstrument(prev => ({ ...prev, name: e.target.value }))}
                  className="bg-secondary border-border"
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Type</Label>
                <Select
                  value={newInstrument.type}
                  onValueChange={(v) => setNewInstrument(prev => ({ ...prev, type: v }))}
                >
                  <SelectTrigger className="bg-secondary border-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Crypto">Crypto</SelectItem>
                    <SelectItem value="Forex">Forex</SelectItem>
                    <SelectItem value="Stock">Stock</SelectItem>
                    <SelectItem value="Index">Index</SelectItem>
                    <SelectItem value="Commodity">Commodity</SelectItem>
                    <SelectItem value="Futures">Futures</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Exchange</Label>
                <Input
                  placeholder="e.g., NYSE"
                  value={newInstrument.exchange}
                  onChange={(e) => setNewInstrument(prev => ({ ...prev, exchange: e.target.value }))}
                  className="bg-secondary border-border"
                />
              </div>
              <div className="flex items-end">
                <Button onClick={addManualInstrument} className="w-full">
                  <Plus className="w-4 h-4 mr-1" />
                  Add
                </Button>
              </div>
            </div>
          </Card>

          {/* Instrument List */}
          <Card className="p-4 border-border bg-card">
            <h4 className="font-semibold text-foreground mb-4">Available Instruments (Click to Select)</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {manualInstruments.map((instrument) => (
                <div
                  key={instrument.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedInstruments.includes(instrument.symbol)
                    ? "bg-primary/20 border-primary"
                    : "bg-secondary/50 border-border hover:border-primary/50"
                    }`}
                  onClick={() => toggleInstrument(instrument.symbol)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-foreground">{instrument.symbol}</p>
                      <p className="text-xs text-muted-foreground">{instrument.name}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {instrument.type}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeInstrument(instrument.id);
                        }}
                      >
                        <Trash2 className="w-3 h-3 text-destructive" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{instrument.exchange}</p>
                  {selectedInstruments.includes(instrument.symbol) && (
                    <CheckCircle className="w-4 h-4 text-success mt-2" />
                  )}
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Strategies Tab */}
        <TabsContent value="strategies" className="space-y-4 mt-4">
          {/* Gann Strategies */}
          <Card className="p-4 border-border bg-card">
            <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <Target className="w-4 h-4 text-accent" />
              W.D. Gann Strategies
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {GANN_STRATEGIES.map((strategy) => (
                <div
                  key={strategy.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${config.selectedGannStrategies.includes(strategy.id)
                    ? "bg-accent/20 border-accent"
                    : "bg-secondary/50 border-border hover:border-accent/50"
                    }`}
                  onClick={() => toggleStrategy(strategy.id, "gann")}
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-semibold text-foreground text-sm">{strategy.name}</p>
                    {config.selectedGannStrategies.includes(strategy.id) && (
                      <CheckCircle className="w-4 h-4 text-success" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{strategy.description}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Ehlers Strategies */}
          <Card className="p-4 border-border bg-card">
            <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              John F. Ehlers DSP Strategies
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {EHLERS_STRATEGIES.map((strategy) => (
                <div
                  key={strategy.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${config.selectedEhlersStrategies.includes(strategy.id)
                    ? "bg-primary/20 border-primary"
                    : "bg-secondary/50 border-border hover:border-primary/50"
                    }`}
                  onClick={() => toggleStrategy(strategy.id, "ehlers")}
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-semibold text-foreground text-sm">{strategy.name}</p>
                    {config.selectedEhlersStrategies.includes(strategy.id) && (
                      <CheckCircle className="w-4 h-4 text-success" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{strategy.description}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Selected Summary */}
          <Card className="p-4 border-border bg-card">
            <h4 className="font-semibold text-foreground mb-2">Selected Strategies</h4>
            <div className="flex flex-wrap gap-2">
              {config.selectedGannStrategies.map(id => {
                const s = GANN_STRATEGIES.find(g => g.id === id);
                return s ? (
                  <Badge key={id} variant="outline" className="border-accent text-accent">
                    {s.name}
                  </Badge>
                ) : null;
              })}
              {config.selectedEhlersStrategies.map(id => {
                const s = EHLERS_STRATEGIES.find(e => e.id === id);
                return s ? (
                  <Badge key={id} variant="outline" className="border-primary text-primary">
                    {s.name}
                  </Badge>
                ) : null;
              })}
            </div>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4 mt-4">
          {results && (
            <>
              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                <Card className="p-3 border-border bg-card">
                  <p className="text-xs text-muted-foreground">Total Trades</p>
                  <p className="text-lg font-bold text-foreground">{results.metrics.totalTrades}</p>
                </Card>
                <Card className="p-3 border-border bg-card">
                  <p className="text-xs text-muted-foreground">Win Rate</p>
                  <p className="text-lg font-bold text-success">{results.metrics.winRate.toFixed(1)}%</p>
                </Card>
                <Card className="p-3 border-border bg-card">
                  <p className="text-xs text-muted-foreground">Total P&L</p>
                  <p className={`text-lg font-bold ${results.metrics.totalPnL >= 0 ? 'text-success' : 'text-destructive'}`}>
                    ${results.metrics.totalPnL.toFixed(2)}
                  </p>
                </Card>
                <Card className="p-3 border-border bg-card">
                  <p className="text-xs text-muted-foreground">Profit Factor</p>
                  <p className="text-lg font-bold text-foreground">{results.metrics.profitFactor.toFixed(2)}</p>
                </Card>
                <Card className="p-3 border-border bg-card">
                  <p className="text-xs text-muted-foreground">Sharpe Ratio</p>
                  <p className="text-lg font-bold text-primary">{results.metrics.sharpeRatio.toFixed(2)}</p>
                </Card>
                <Card className="p-3 border-border bg-card">
                  <p className="text-xs text-muted-foreground">Max Drawdown</p>
                  <p className="text-lg font-bold text-destructive">{results.metrics.maxDrawdown.toFixed(1)}%</p>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Equity Curve */}
                <Card className="p-4 border-border bg-card">
                  <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-success" />
                    Equity Curve
                  </h4>
                  <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={results.equityCurve}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                        <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                        <YAxis yAxisId="left" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                        <YAxis yAxisId="right" orientation="right" stroke="hsl(var(--destructive))" tick={{ fontSize: 10 }} />
                        <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }} />
                        <Area yAxisId="left" type="monotone" dataKey="equity" fill="hsl(var(--success))" fillOpacity={0.2} stroke="hsl(var(--success))" strokeWidth={2} name="Equity" />
                        <Line yAxisId="right" type="monotone" dataKey="drawdown" stroke="hsl(var(--destructive))" strokeWidth={1} dot={false} name="Drawdown %" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </Card>

                {/* Monthly Returns */}
                <Card className="p-4 border-border bg-card">
                  <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-primary" />
                    Monthly Returns (%)
                  </h4>
                  <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={results.monthlyReturns}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                        <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                        <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                        <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }} />
                        <Bar
                          dataKey="return"
                          fill="hsl(var(--primary))"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>

              {/* Trade List */}
              <Card className="p-4 border-border bg-card">
                <h4 className="font-semibold text-foreground mb-4">Recent Trades</h4>
                <div className="overflow-x-auto max-h-[300px]">
                  <table className="w-full text-sm">
                    <thead className="bg-secondary/50 sticky top-0">
                      <tr>
                        <th className="px-3 py-2 text-left text-foreground">ID</th>
                        <th className="px-3 py-2 text-left text-foreground">Instrument</th>
                        <th className="px-3 py-2 text-left text-foreground">Strategy</th>
                        <th className="px-3 py-2 text-left text-foreground">Direction</th>
                        <th className="px-3 py-2 text-right text-foreground">Entry</th>
                        <th className="px-3 py-2 text-right text-foreground">Exit</th>
                        <th className="px-3 py-2 text-right text-foreground">Size</th>
                        <th className="px-3 py-2 text-right text-foreground">P&L</th>
                        <th className="px-3 py-2 text-right text-foreground">Duration</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.trades.slice(0, 20).map((trade, idx) => (
                        <tr key={trade.id} className={idx % 2 === 0 ? "bg-card" : "bg-secondary/20"}>
                          <td className="px-3 py-2 font-mono text-foreground">{trade.id}</td>
                          <td className="px-3 py-2 font-semibold text-foreground">{trade.instrument}</td>
                          <td className="px-3 py-2 text-muted-foreground text-xs">{trade.strategy}</td>
                          <td className="px-3 py-2">
                            <Badge className={trade.direction === "LONG" ? "bg-success" : "bg-destructive"}>
                              {trade.direction}
                            </Badge>
                          </td>
                          <td className="px-3 py-2 text-right font-mono text-foreground">${trade.entryPrice.toFixed(2)}</td>
                          <td className="px-3 py-2 text-right font-mono text-foreground">${trade.exitPrice.toFixed(2)}</td>
                          <td className="px-3 py-2 text-right font-mono text-foreground">{trade.size.toFixed(3)}</td>
                          <td className={`px-3 py-2 text-right font-mono ${trade.pnl >= 0 ? 'text-success' : 'text-destructive'}`}>
                            {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right text-muted-foreground">{trade.holdingPeriod}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>

              {/* Detailed Metrics */}
              <Card className="p-4 border-border bg-card">
                <h4 className="font-semibold text-foreground mb-4">Detailed Performance Metrics</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Winning Trades</p>
                    <p className="font-bold text-success">{results.metrics.winningTrades}</p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Losing Trades</p>
                    <p className="font-bold text-destructive">{results.metrics.losingTrades}</p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Avg Win</p>
                    <p className="font-bold text-success">${results.metrics.avgWin.toFixed(2)}</p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Avg Loss</p>
                    <p className="font-bold text-destructive">${results.metrics.avgLoss.toFixed(2)}</p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Sortino Ratio</p>
                    <p className="font-bold text-foreground">{results.metrics.sortinoRatio.toFixed(2)}</p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Calmar Ratio</p>
                    <p className="font-bold text-foreground">{results.metrics.calmarRatio.toFixed(2)}</p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Expectancy</p>
                    <p className={`font-bold ${results.metrics.expectancy >= 0 ? 'text-success' : 'text-destructive'}`}>
                      ${results.metrics.expectancy.toFixed(2)}
                    </p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Avg Holding</p>
                    <p className="font-bold text-foreground">{results.metrics.avgHoldingPeriod}</p>
                  </div>
                </div>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div >
  );
};
