import { useState, useEffect, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Zap,
  Activity,
  Settings,
  Play,
  Pause,
  BarChart3,
  Clock,
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Server,
  Network,
  TestTube,
  Plus,
  Sparkles,
  Bell,
  RefreshCw,
  Layers,
  Shield,
  History,
  Terminal,
  Target,
  Cpu,
  Cpu as CpuIcon,
  Save
} from "lucide-react";
import { toast } from "sonner";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { BacktestSimulator } from "@/components/hft/BacktestSimulator";
import { StrategyOptimizer } from "@/components/hft/StrategyOptimizer";
import { StrategyAlerts } from "@/components/hft/StrategyAlerts";

// --- Mock Data Generators ---
const generateLatencyData = () => {
  return Array.from({ length: 30 }, (_, i) => ({
    time: i,
    latency: 0.5 + Math.random() * 1.5,
    network: 0.2 + Math.random() * 0.5,
  }));
};

const generatePnLData = () => {
  let pnl = 0;
  return Array.from({ length: 50 }, (_, i) => {
    pnl += (Math.random() - 0.45) * 100;
    return { step: i, pnl };
  });
};

const HFT = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedStrategy, setSelectedStrategy] = useState("market-making");
  const [viewedInstrument, setViewedInstrument] = useState("BTCUSDT");

  // HFT Configuration State (Preserving Logic)
  const [config, setConfig] = useState({
    enabled: false,
    maxOrdersPerSecond: 100,
    maxPositionSize: 10,
    riskLimitPerTrade: 0.1,
    targetLatency: 1.0,
    maxLatency: 5.0,
    coLocation: true,
    directMarketAccess: true,
    autoSpread: false,
    spreadBps: 2.0,
    inventoryLimit: 5,
    quoteSize: 0.1,
    refreshRate: 100,
    minSpreadArb: 0.05,
    maxSlippage: 0.02,
    signalThreshold: 0.8,
    holdPeriod: 500,
    riskMode: "dynamic" as "dynamic" | "fixed",
    kellyFraction: 0.25,
    volatilityAdjusted: true,
    maxDailyDrawdown: 5.0,
    dynamicPositionScaling: true,
    timeframe: "1ms",
    customTimeframe: "",
    fixedRiskPercent: 1.0,
    fixedLotSize: 0.1,
    fixedStopLoss: 50,
    fixedTakeProfit: 100,
    instrumentMode: "single" as "single" | "multi",
    selectedInstruments: ["BTCUSDT"] as string[],
    manualInstruments: [] as string[],
    useGannSquare9: false,
    gannSquare9BasePrice: 100,
    gannSquare9Divisions: 8,
    useGannAngles: false,
    gannAngle: 45,
    gannTimeUnit: 1,
    useGannTimeCycles: false,
    gannCycleBase: 30,
    useGannSR: false,
    gannSRDivisions: 8,
    useGannFibo: false,
    useGannWave: false,
    useGannHexagon: false,
    useGannAstro: false,
    useEhlersMAMAFAMA: false,
    mamaFastLimit: 0.5,
    mamaSlowLimit: 0.05,
    useEhlersFisher: false,
    useEhlersBandpass: false,
    useEhlersSuperSmoother: false,
    useEhlersRoofing: false,
    useEhlersCyberCycle: false,
    useEhlersDecycler: false,
    useEhlersInstaTrend: false,
    useEhlersDominantCycle: false,
    // New Strategies
    useMarketMaking: true,
    useStatisticalArbitrage: false,
    useMomentumScalping: false,
    useMeanReversion: false,
    // Trading Mode
    tradingMode: "spot" as "spot" | "futures",
    // Exit Mode
    exitMode: "ticks" as "ticks" | "rr",
    riskRewardRatio: 2.0,
  });

  useEffect(() => {
    if (config.selectedInstruments.length > 0 && !config.selectedInstruments.includes(viewedInstrument)) {
      setViewedInstrument(config.selectedInstruments[0]);
    }
  }, [config.selectedInstruments, viewedInstrument]);

  // --- Real-time Generation ---
  const [latencyData, setLatencyData] = useState(generateLatencyData());
  const [pnlData, setPnLData] = useState(generatePnLData());
  const [executionLogs, setExecutionLogs] = useState<{ id: string, time: string, action: string, symbol: string, price: string, status: string }[]>([]);

  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => {
      setLatencyData(prev => [...prev.slice(1), {
        time: prev[prev.length - 1].time + 1,
        latency: 0.5 + Math.random() * 1.5,
        network: 0.2 + Math.random() * 0.5
      }]);

      if (Math.random() > 0.3) {
        const actions = ["BUY", "SELL", "LIMIT", "CANCEL"];
        const symbols = config.selectedInstruments.length > 0 ? config.selectedInstruments : ["BTCUSDT"];
        const newLog = {
          id: Math.random().toString(36).substr(2, 9),
          time: new Date().toLocaleTimeString(),
          action: actions[Math.floor(Math.random() * actions.length)],
          symbol: symbols[Math.floor(Math.random() * symbols.length)],
          price: (40000 + Math.random() * 5000).toFixed(2),
          status: "FILLED"
        };
        setExecutionLogs(prev => [newLog, ...prev.slice(0, 15)]);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [isRunning, config.selectedInstruments]);

  // Dynamic Instrument State
  const [instrumentSource, setInstrumentSource] = useState("crypto");

  const instrumentLists: Record<string, { spot: string[], futures: string[] }> = {
    crypto: {
      spot: ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT", "MATICUSDT"],
      futures: ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "BNBUSDT.P", "XRPUSDT.P", "ADAUSDT.P", "DOTUSDT.P", "MATICUSDT.P"]
    },
    mt5: {
      spot: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "XAUUSD"],
      futures: ["USTEC", "US500", "US30", "GER40", "UK100", "JP225", "HK50", "XAUUSD_F"]
    },
    mt4: {
      spot: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "XAUUSD"],
      futures: ["DE30", "US500", "US30", "UK100", "JP225", "HK50", "XAUUSD", "WTI"]
    },
    fix: {
      spot: ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"], // Less common for HFT FIX but supported
      futures: ["ES_F", "NQ_F", "CL_F", "GC_F", "SI_F", "ZB_F", "ZN_F", "YM_F"]
    }
  };

  const [availableInstruments, setAvailableInstruments] = useState<string[]>(instrumentLists.crypto.spot || []);
  const [newInstrumentInput, setNewInstrumentInput] = useState("");

  useEffect(() => {
    const sourceData = instrumentLists[instrumentSource];
    if (sourceData) {
      setAvailableInstruments(config.tradingMode === 'futures' ? sourceData.futures : sourceData.spot);
    }
  }, [instrumentSource, config.tradingMode]);

  const addInstrument = () => {
    if (newInstrumentInput && !availableInstruments.includes(newInstrumentInput)) {
      setAvailableInstruments([...availableInstruments, newInstrumentInput.toUpperCase()]);
      setNewInstrumentInput("");
      toast.success(`[${instrumentSource.toUpperCase()}] Added ${newInstrumentInput.toUpperCase()}`);
    }
  };

  const removeInstrument = (inst: string) => {
    setAvailableInstruments(availableInstruments.filter(i => i !== inst));
    if (config.selectedInstruments.includes(inst)) {
      updateConfig("selectedInstruments", config.selectedInstruments.filter(i => i !== inst));
    }
    toast.info(`Removed ${inst}`);
  };

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const toggleHFT = () => {
    setIsRunning(!isRunning);
    if (!isRunning) toast.success("HFT Node Activated • Low Latency Mode");
    else toast.info("HFT Node Suspended");
  };

  const handleSaveConfig = () => {
    toast.success("Configuration Saved Successfully", {
      description: "All trading parameters and safety limits have been updated."
    });
  };

  return (
    <div className="min-h-screen space-y-8 bg-background pb-12">
      {/* Dynamic Command Header */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-primary/10 via-background to-accent/10 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 p-8 opacity-20">
          <Zap className="h-48 w-48 text-primary blur-2xl" />
        </div>

        <div className="relative z-10 flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-primary p-3 shadow-lg shadow-primary/20">
                <CpuIcon className="h-8 w-8 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tight text-foreground">HFT COMMAND</h1>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-primary/30 bg-primary/5 text-primary">v4.2.0-PRO</Badge>
                  <span className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                    <Server className="h-3 w-3" /> NYC-DATA-CENTER-1
                  </span>
                </div>
              </div>
            </div>
            <p className="max-w-xl text-lg text-muted-foreground/80">
              Ultra-low latency execution engine powered by <span className="text-primary font-bold">Gann-Astro AI</span> and <span className="text-accent font-bold">Ehlers DSP</span> logic.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-4 rounded-2xl border border-border bg-card/50 px-6 py-4 backdrop-blur-xl">
              <div className="text-right">
                <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">System Latency</p>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-black font-mono text-success">
                    {latencyData[latencyData.length - 1].latency.toFixed(2)}ms
                  </span>
                  <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                </div>
              </div>
            </div>

            <Button
              size="lg"
              onClick={toggleHFT}
              className={`h-16 rounded-2xl px-10 text-xl font-bold transition-all duration-500 hover:scale-105 active:scale-95 ${isRunning
                ? "bg-destructive shadow-lg shadow-destructive/20"
                : "bg-primary shadow-lg shadow-primary/20"
                }`}
            >
              {isRunning ? (
                <>
                  <Pause className="mr-3 h-6 w-6 fill-current" /> STOP NODE
                </>
              ) : (
                <>
                  <Play className="mr-3 h-6 w-6 fill-current" /> START NODE
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Real-time Ticker */}
        <div className="mt-8 flex gap-6 overflow-hidden border-t border-border/50 pt-6">
          <div className="flex animate-marquee gap-8 whitespace-nowrap">
            {config.selectedInstruments.map((sym, i) => (
              <div key={sym} className="flex gap-8">
                <span className="flex items-center gap-2 text-sm font-bold text-success">
                  <TrendingUp className="h-4 w-4" /> {sym}: +{(2.4 - i * 0.2).toFixed(1)}%
                </span>
                <span className="flex items-center gap-2 text-sm font-bold text-primary">
                  <Activity className="h-4 w-4" /> VOL: ${(4.2 - i * 0.5).toFixed(1)}B
                </span>
                <span className="flex items-center gap-2 text-sm font-bold text-accent">
                  {config.tradingMode === 'futures' ? 'FR: 0.01%' : 'SPOT'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Control Center */}
      <div className="grid gap-8 lg:grid-cols-[1fr_380px]">
        <div className="space-y-8">
          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {[
              { label: "Executions today", value: "85,420", icon: Layers, color: "text-primary", bg: "bg-primary/10" },
              { label: "Profit realized", value: "+$12,845", icon: DollarSign, color: "text-success", bg: "bg-success/10" },
              { label: "Success Rate", value: "52.3%", icon: TrendingUp, color: "text-accent", bg: "bg-accent/10" },
              { label: "Risk Exposure", value: "0.15%", icon: Shield, color: "text-warning", bg: "bg-warning/10" },
            ].map((stat, i) => (
              <Card key={i} className="group overflow-hidden border-border bg-card p-6 transition-all hover:border-primary/50">
                <div className="flex items-center justify-between">
                  <div className={`rounded-xl ${stat.bg} p-2`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="h-12 w-16 opacity-30 grayscale group-hover:grayscale-0 transition-all">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={latencyData.slice(0, 5)}>
                        <Area type="monotone" dataKey="latency" stroke="currentColor" fill="currentColor" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-2xl font-black text-foreground">{stat.value}</p>
                  <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">{stat.label}</p>
                </div>
              </Card>
            ))}
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="h-16 w-full items-center justify-start gap-2 bg-transparent p-0 flex-wrap mb-4">
              {["overview", "strategies", "optimizer", "alerts", "orderbook", "config", "backtest"].map((tab) => (
                <TabsTrigger
                  key={tab}
                  value={tab}
                  className="h-12 rounded-xl border border-border px-8 font-bold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-lg"
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value="overview" className="mt-6 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-border bg-card p-6 shadow-xl shadow-success/5">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-black">Performance Analytics</h3>
                    <Badge variant="secondary" className="bg-success/10 text-success">Live P&L</Badge>
                  </div>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={pnlData}>
                        <defs>
                          <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="hsl(var(--success))" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="hsl(var(--success))" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <XAxis hide />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} axisLine={false} tickLine={false} />
                        <Tooltip />
                        <Area
                          type="monotone"
                          dataKey="pnl"
                          stroke="hsl(var(--success))"
                          strokeWidth={3}
                          fill="url(#pnlGradient)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </Card>

                <Card className="border-border bg-card p-6 shadow-xl shadow-primary/5">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-black">Latency Stability</h3>
                    <Badge variant="secondary" className="bg-primary/10 text-primary">0.1ms precision</Badge>
                  </div>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={latencyData}>
                        <XAxis hide />
                        <YAxis domain={[0, 5]} stroke="hsl(var(--muted-foreground))" fontSize={10} axisLine={false} tickLine={false} />
                        <Tooltip />
                        <Line type="stepAfter" dataKey="latency" stroke="hsl(var(--primary))" strokeWidth={3} dot={false} />
                        <Line type="stepAfter" dataKey="network" stroke="hsl(var(--accent))" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>

              <Card className="border-border bg-card p-6 overflow-hidden">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-black flex items-center gap-2">
                    <History className="h-5 w-5 text-primary" /> Active Position Nodes
                  </h3>
                  <Button variant="ghost" size="sm" className="text-primary hover:bg-primary/10 font-bold">EXHAUSTIVE VIEW</Button>
                </div>
                <div className="space-y-4">
                  {[
                    ...config.selectedInstruments.map((sym, i) => ({
                      symbol: sym,
                      side: i % 2 === 0 ? "LONG" : "SHORT",
                      qty: (0.5 + i * 0.2).toFixed(2),
                      entry: (40000 + i * 500).toLocaleString(),
                      pnl: i % 2 === 0 ? `+${(120 + i * 20).toFixed(2)}` : `-${(30 + i * 5).toFixed(2)}`,
                      progress: 50 + (i * 10) % 40
                    }))
                  ].map((pos, i) => (
                    <div key={i} className="group flex items-center justify-between rounded-2xl bg-secondary/30 p-4 border border-border/50 hover:bg-secondary/50 hover:border-border transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-12 w-1 rounded-full ${pos.side === 'LONG' ? 'bg-success' : 'bg-destructive'}`} />
                        <div>
                          <p className="font-black text-lg">{pos.symbol}</p>
                          <p className={`text-xs font-black uppercase ${pos.side === 'LONG' ? 'text-success' : 'text-destructive'}`}>
                            {pos.side} • {pos.qty} {config.tradingMode === 'futures' ? 'CONT' : 'UNITS'}
                          </p>
                        </div>
                      </div>
                      <div className="hidden md:block w-32">
                        <div className="h-1.5 w-full bg-border rounded-full overflow-hidden">
                          <div className={`h-full ${pos.pnl.startsWith('+') ? 'bg-success' : 'bg-destructive'}`} style={{ width: `${pos.progress}%` }} />
                        </div>
                        <p className="text-[10px] font-bold text-muted-foreground mt-1 uppercase tracking-wider">Fill Confidence</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-xl font-black font-mono ${pos.pnl.startsWith('+') ? 'text-success' : 'text-destructive'}`}>
                          {pos.pnl}
                        </p>
                        <p className="text-xs font-bold text-muted-foreground">${pos.entry}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </TabsContent>

            <TabsContent value="strategies" className="mt-6 space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">

              {/* Core HFT Strategies */}
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-border/50 pb-4">
                  <div>
                    <h3 className="text-2xl font-black text-foreground flex items-center gap-2">
                      <Cpu className="h-6 w-6 text-primary" /> Core Execution Strategies
                    </h3>
                    <p className="text-sm text-muted-foreground">High-frequency algorithmic execution models.</p>
                  </div>
                  <Badge variant="outline" className="border-primary/30 text-primary font-black uppercase text-[10px] tracking-widest">Active Engine</Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { id: "useMarketMaking", name: "Market Making", desc: "Bid-Ask spread capture", icon: Layers },
                    { id: "useStatisticalArbitrage", name: "Stat Arbitrage", desc: "Pair correlation reversion", icon: Network },
                    { id: "useMomentumScalping", name: "Momentum Scalping", desc: "Micro-trend acceleration", icon: Zap },
                    { id: "useMeanReversion", name: "Mean Reversion", desc: "Overbought/Oversold return", icon: RefreshCw }
                  ].map((strat) => (
                    <Card
                      key={strat.id}
                      onClick={() => updateConfig(strat.id, !config[strat.id as keyof typeof config])}
                      className={`group cursor-pointer border-2 p-4 transition-all duration-300 ${config[strat.id as keyof typeof config]
                        ? "border-primary bg-primary/5 shadow-lg shadow-primary/5"
                        : "border-border bg-card hover:border-primary/30"
                        }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className={`rounded-lg p-2 ${config[strat.id as keyof typeof config] ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <strat.icon className="h-5 w-5" />
                        </div>
                        <Switch checked={!!config[strat.id as keyof typeof config]} />
                      </div>
                      <h4 className="font-black text-sm mb-1">{strat.name}</h4>
                      <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-tight">{strat.desc}</p>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Gann Strategy Suite */}
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-border/50 pb-4">
                  <div>
                    <h3 className="text-2xl font-black text-foreground flex items-center gap-2">
                      <TrendingUp className="h-6 w-6 text-accent" /> W.D. Gann Algorithm Suite
                    </h3>
                    <p className="text-sm text-muted-foreground">Geometric and cyclical price-time projection models.</p>
                  </div>
                  <Badge variant="outline" className="border-accent/30 text-accent font-black uppercase text-[10px] tracking-widest">Master Node</Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { id: "useGannSquare9", name: "Square of 9", desc: "Spiral numerical price mapping", icon: Layers },
                    { id: "useGannAngles", name: "Gann Angles", desc: "Dynamic time-price 1x1 vectors", icon: TrendingUp },
                    { id: "useGannTimeCycles", name: "Time Cycles", desc: "Historical anniversary cycles", icon: Clock },
                    { id: "useGannSR", name: "Gann S/R", desc: "Octave-based support/resistance", icon: BarChart3 },
                    { id: "useGannFibo", name: "Gann Fibonacci", desc: "Combined spiral-fibo levels", icon: Target },
                    { id: "useGannWave", name: "Gann Wave", desc: "Complex wave structure detection", icon: Activity },
                    { id: "useGannHexagon", name: "Hexagon", desc: "Geometric pattern projection", icon: Shield },
                    { id: "useGannAstro", name: "Astro Sync", desc: "Planetary time synchronization", icon: Sparkles }
                  ].map((strat) => (
                    <Card
                      key={strat.id}
                      onClick={() => updateConfig(strat.id, !config[strat.id as keyof typeof config])}
                      className={`group cursor-pointer border-2 p-4 transition-all duration-300 ${config[strat.id as keyof typeof config]
                        ? "border-accent bg-accent/5 shadow-lg shadow-accent/5"
                        : "border-border bg-card hover:border-accent/30"
                        }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className={`rounded-lg p-2 ${config[strat.id as keyof typeof config] ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <strat.icon className="h-5 w-5" />
                        </div>
                        <Switch checked={!!config[strat.id as keyof typeof config]} />
                      </div>
                      <h4 className="font-black text-sm mb-1">{strat.name}</h4>
                      <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-tight">{strat.desc}</p>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Ehlers DSP Suite */}
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-border/50 pb-4">
                  <div>
                    <h3 className="text-2xl font-black text-foreground flex items-center gap-2">
                      <Activity className="h-6 w-6 text-primary" /> John Ehlers DSP Suite
                    </h3>
                    <p className="text-sm text-muted-foreground">Digital Signal Processing for high-fidelity market data.</p>
                  </div>
                  <Badge variant="outline" className="border-primary/30 text-primary font-black uppercase text-[10px] tracking-widest">Signal Processing</Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { id: "useEhlersMAMAFAMA", name: "MAMA/FAMA", desc: "Adaptive moving average sync", icon: Activity },
                    { id: "useEhlersFisher", name: "Fisher Transform", desc: "Price distribution normalization", icon: BarChart3 },
                    { id: "useEhlersBandpass", name: "Bandpass Filter", desc: "Isolate cyclical components", icon: RefreshCw },
                    { id: "useEhlersSuperSmoother", name: "Super Smoother", desc: "Lag-minimized smoothing", icon: Zap },
                    { id: "useEhlersRoofing", name: "Roofing Filter", desc: "Broadband noise elimination", icon: Shield },
                    { id: "useEhlersCyberCycle", name: "Cyber Cycle", desc: "Spectral cycle identification", icon: RefreshCw },
                    { id: "useEhlersDecycler", name: "Decycler", desc: "Instantaneous trend extraction", icon: TrendingUp },
                    { id: "useEhlersInstaTrend", name: "Insta Trend", desc: "Real-time market direction", icon: Activity },
                    { id: "useEhlersDominantCycle", name: "Dominant Cycle", desc: "Period measurement model", icon: Clock }
                  ].map((strat) => (
                    <Card
                      key={strat.id}
                      onClick={() => updateConfig(strat.id, !config[strat.id as keyof typeof config])}
                      className={`group cursor-pointer border-2 p-4 transition-all duration-300 ${config[strat.id as keyof typeof config]
                        ? "border-primary bg-primary/5 shadow-lg shadow-primary/5"
                        : "border-border bg-card hover:border-primary/30"
                        }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className={`rounded-lg p-2 ${config[strat.id as keyof typeof config] ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <strat.icon className="h-5 w-5" />
                        </div>
                        <Switch checked={!!config[strat.id as keyof typeof config]} />
                      </div>
                      <h4 className="font-black text-sm mb-1">{strat.name}</h4>
                      <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-tight">{strat.desc}</p>
                    </Card>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="optimizer" className="mt-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <Card className="border-border bg-card p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="rounded-xl bg-accent/20 p-2">
                    <Sparkles className="h-6 w-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-xl font-black">Strategy Optimizer</h3>
                    <p className="text-sm text-muted-foreground">AI-driven parameter calibration for HFT nodes.</p>
                  </div>
                </div>
                <StrategyOptimizer config={config} updateConfig={updateConfig} />
              </Card>
            </TabsContent>

            <TabsContent value="alerts" className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <StrategyAlerts config={config} isRunning={isRunning} />
            </TabsContent>

            <TabsContent value="backtest" className="mt-6 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Strategy Calibration for Backtest */}
              <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-border bg-card p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-black flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-accent" /> W.D. Gann Calibration
                    </h3>
                    <Badge variant="outline" className="border-accent/30 text-accent uppercase text-[10px] font-black">Backtest Mode</Badge>
                  </div>

                  <div className="space-y-4">
                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannSquare9 ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <Layers className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Square of 9</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Spiral Price Cycles</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannSquare9} onCheckedChange={(v) => updateConfig("useGannSquare9", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannAngles ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <TrendingUp className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Gann Angles</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Time-Price 1x1, 2x1</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannAngles} onCheckedChange={(v) => updateConfig("useGannAngles", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannTimeCycles ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <Clock className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Time Cycles</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Anniversary Master Cycles</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannTimeCycles} onCheckedChange={(v) => updateConfig("useGannTimeCycles", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannSR ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <BarChart3 className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Gann S/R</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Octave-based Support/Res</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannSR} onCheckedChange={(v) => updateConfig("useGannSR", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannFibo ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <Target className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Gann Fibonacci</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Combined Spiral-Fibo</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannFibo} onCheckedChange={(v) => updateConfig("useGannFibo", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannWave ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <Activity className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Gann Wave</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Complex Wave Structure</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannWave} onCheckedChange={(v) => updateConfig("useGannWave", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannHexagon ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <Shield className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Hexagon</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Geometric Pattern Proj</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannHexagon} onCheckedChange={(v) => updateConfig("useGannHexagon", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useGannAstro ? 'bg-accent text-accent-foreground' : 'bg-secondary'}`}>
                          <Sparkles className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Astro Sync</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Planetary Time Sync</p>
                        </div>
                      </div>
                      <Switch checked={config.useGannAstro} onCheckedChange={(v) => updateConfig("useGannAstro", v)} />
                    </div>
                  </div>
                </Card>

                <Card className="border-border bg-card p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-black flex items-center gap-2">
                      <Activity className="h-5 w-5 text-primary" /> Ehlers DSP Calibration
                    </h3>
                    <Badge variant="outline" className="border-primary/30 text-primary uppercase text-[10px] font-black">Backtest Mode</Badge>
                  </div>

                  <div className="space-y-4">
                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersMAMAFAMA ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <Activity className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">MAMA/FAMA</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Mesa Adaptive Moving Avg</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersMAMAFAMA} onCheckedChange={(v) => updateConfig("useEhlersMAMAFAMA", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersFisher ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <BarChart3 className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Fisher Transform</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Gaussian PDF Normalization</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersFisher} onCheckedChange={(v) => updateConfig("useEhlersFisher", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersBandpass ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <RefreshCw className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Bandpass Filter</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Cycle Component Isolation</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersBandpass} onCheckedChange={(v) => updateConfig("useEhlersBandpass", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersSuperSmoother ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <Zap className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Super Smoother</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Lag-minimized Smoothing</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersSuperSmoother} onCheckedChange={(v) => updateConfig("useEhlersSuperSmoother", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersRoofing ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <Shield className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Roofing Filter</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Broadband Noise Elimination</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersRoofing} onCheckedChange={(v) => updateConfig("useEhlersRoofing", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersCyberCycle ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <RefreshCw className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Cyber Cycle</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Spectral Cycle ID</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersCyberCycle} onCheckedChange={(v) => updateConfig("useEhlersCyberCycle", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersDecycler ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <TrendingUp className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Decycler</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Trend Extraction</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersDecycler} onCheckedChange={(v) => updateConfig("useEhlersDecycler", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersInstaTrend ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <Activity className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Insta Trend</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Real-time Direction</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersInstaTrend} onCheckedChange={(v) => updateConfig("useEhlersInstaTrend", v)} />
                    </div>

                    <div className="group flex items-center justify-between p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-all">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${config.useEhlersDominantCycle ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                          <Clock className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold">Dominant Cycle</p>
                          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Period Measurement</p>
                        </div>
                      </div>
                      <Switch checked={config.useEhlersDominantCycle} onCheckedChange={(v) => updateConfig("useEhlersDominantCycle", v)} />
                    </div>
                  </div>
                </Card>
              </div>

              <Card className="border-border bg-card p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="rounded-xl bg-primary/20 p-2">
                    <TestTube className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xl font-black">Backtest Laboratory</h3>
                    <p className="text-sm text-muted-foreground">Stress-test your configuration against historical tick data.</p>
                  </div>
                </div>
                <BacktestSimulator hftConfig={config} />
              </Card>
            </TabsContent>

            <TabsContent value="orderbook" className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <Card className="border-border bg-card p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                  <h3 className="text-xl font-black flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-primary" /> Level 2 Order Book • {viewedInstrument}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {config.selectedInstruments.map(sym => (
                      <Badge
                        key={sym}
                        variant={viewedInstrument === sym ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => setViewedInstrument(sym)}
                      >
                        {sym}
                      </Badge>
                    ))}
                  </div>
                </div>

                {config.tradingMode === 'futures' && (
                  <div className="flex items-center gap-4 mb-4 p-3 bg-accent/5 rounded-xl border border-accent/20">
                    <span className="text-xs font-bold text-accent uppercase flex items-center gap-1">
                      <Clock className="h-3 w-3" /> Funding: 0.01%
                    </span>
                    <span className="text-xs font-bold text-muted-foreground uppercase">
                      Next: 04:20:15
                    </span>
                    <span className="text-xs font-bold text-muted-foreground uppercase border-l border-border pl-4">
                      Mark: $47,250.50
                    </span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-black uppercase text-muted-foreground pb-2 border-b border-border mb-2">
                      <span>Price</span>
                      <span>Size ({config.tradingMode === 'futures' ? 'Cont' : 'Qty'})</span>
                    </div>
                    {[0, 1, 2, 3, 4].map((i) => {
                      const basePrice = viewedInstrument === 'BTCUSDT' ? 47500 : viewedInstrument === 'ETHUSDT' ? 2400 : 100;
                      return (
                        <div key={i} className="flex justify-between items-center p-2 bg-success/5 rounded-lg relative overflow-hidden group">
                          <div className="absolute left-0 top-0 bottom-0 bg-success/10 transition-all duration-1000" style={{ width: `${80 - i * 10}%` }} />
                          <span className="font-mono text-sm text-success font-bold z-10">${(basePrice - i * (basePrice * 0.0001)).toFixed(2)}</span>
                          <span className="font-mono text-sm text-foreground font-bold z-10">{(2.5 - i * 0.3).toFixed(2)}</span>
                        </div>
                      )
                    })}
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-black uppercase text-muted-foreground pb-2 border-b border-border mb-2">
                      <span>Price</span>
                      <span>Size ({config.tradingMode === 'futures' ? 'Cont' : 'Qty'})</span>
                    </div>
                    {[0, 1, 2, 3, 4].map((i) => {
                      const basePrice = viewedInstrument === 'BTCUSDT' ? 47500 : viewedInstrument === 'ETHUSDT' ? 2400 : 100;
                      return (
                        <div key={i} className="flex justify-between items-center p-2 bg-destructive/5 rounded-lg relative overflow-hidden group">
                          <div className="absolute right-0 top-0 bottom-0 bg-destructive/10 transition-all duration-1000" style={{ width: `${60 - i * 8}%` }} />
                          <span className="font-mono text-sm text-destructive font-bold z-10">${(basePrice + (i + 1) * (basePrice * 0.0001)).toFixed(2)}</span>
                          <span className="font-mono text-sm text-foreground font-bold z-10">{(1.8 + i * 0.4).toFixed(2)}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </Card>
            </TabsContent>

            <TabsContent value="config" className="mt-6">
              <Tabs defaultValue="general" className="w-full">
                <TabsList className="h-12 w-full bg-secondary/30 p-1 rounded-xl mb-6">
                  {["general", "instruments", "latency"].map(sub => (
                    <TabsTrigger key={sub} value={sub} className="flex-1 rounded-lg font-bold text-xs uppercase tracking-widest">
                      {sub}
                    </TabsTrigger>
                  ))}
                </TabsList>

                <TabsContent value="general" className="space-y-8">
                  <div className="grid gap-6 md:grid-cols-2">
                    <Card className="border-border bg-card p-6">
                      <h4 className="font-black text-lg mb-6">Engine Settings</h4>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label className="text-xs font-bold text-muted-foreground">MAX POSITION / SEC</Label>
                          <Input type="number" value={config.maxOrdersPerSecond} onChange={(e) => updateConfig("maxOrdersPerSecond", e.target.value)} className="bg-secondary/30" />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs font-bold text-muted-foreground">MAX POSITION SIZE LOT</Label>
                          <Input type="number" value={config.maxPositionSize} onChange={(e) => updateConfig("maxPositionSize", e.target.value)} className="bg-secondary/30" />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs font-bold text-muted-foreground">EXECUTION TIMEFRAME</Label>
                          <div className="flex gap-2">
                            <Select
                              value={config.timeframe}
                              onValueChange={(val) => updateConfig("timeframe", val)}
                            >
                              <SelectTrigger className="w-[180px] bg-secondary/30">
                                <SelectValue placeholder="Select Timeframe" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="1us">1 Microsecond (1us)</SelectItem>
                                <SelectItem value="10us">10 Microseconds (10us)</SelectItem>
                                <SelectItem value="100us">100 Microseconds (100us)</SelectItem>
                                <SelectItem value="1ms">1 Millisecond (1ms)</SelectItem>
                                <SelectItem value="10ms">10 Milliseconds (10ms)</SelectItem>
                                <SelectItem value="100ms">100 Milliseconds (100ms)</SelectItem>
                                <SelectItem value="1s">1 Second (1s)</SelectItem>
                                <SelectItem value="10s">10 Seconds (10s)</SelectItem>
                                <SelectItem value="1m">1 Minute (1m)</SelectItem>
                                <SelectItem value="custom">Manual Input</SelectItem>
                              </SelectContent>
                            </Select>
                            {config.timeframe === "custom" && (
                              <Input
                                placeholder="e.g. 500us"
                                value={config.customTimeframe || ""}
                                onChange={(e) => updateConfig("customTimeframe", e.target.value)}
                                className="bg-secondary/30 flex-1"
                              />
                            )}
                          </div>
                        </div>
                      </div>
                    </Card>
                    <Card className="border-border bg-card p-6">
                      <h4 className="font-black text-lg mb-6">Market Making Parameters</h4>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label className="text-xs font-bold text-muted-foreground">SPREAD (BPS)</Label>
                            <div className="flex items-center gap-2">
                              <Label className="text-[10px] font-bold text-muted-foreground uppercase cursor-pointer" onClick={() => updateConfig("autoSpread", !config.autoSpread)}>Auto Calc</Label>
                              <Switch
                                checked={config.autoSpread}
                                onCheckedChange={(v) => updateConfig("autoSpread", v)}
                                className="scale-75 origin-right"
                              />
                            </div>
                          </div>
                          <Input
                            type="number"
                            value={config.spreadBps}
                            onChange={(e) => updateConfig("spreadBps", e.target.value)}
                            className={`bg-secondary/30 ${config.autoSpread ? 'opacity-50 cursor-not-allowed' : ''}`}
                            disabled={config.autoSpread}
                          />
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-xl bg-secondary/30 border border-border">
                          <Label className="font-bold">Co-Location Mode</Label>
                          <Switch checked={config.coLocation} onCheckedChange={(v) => updateConfig("coLocation", v)} />
                        </div>
                      </div>
                    </Card>
                  </div>

                  <div className="space-y-6 pt-6 border-t border-border">
                    <div className="flex items-center gap-4 mb-2">
                      <Button
                        variant={config.riskMode === "dynamic" ? "default" : "outline"}
                        onClick={() => updateConfig("riskMode", "dynamic")}
                        className="flex-1 font-black h-12 rounded-xl"
                      >
                        <Zap className="mr-2 h-4 w-4 text-accent" /> DYNAMIC RISK
                      </Button>
                      <Button
                        variant={config.riskMode === "fixed" ? "default" : "outline"}
                        onClick={() => updateConfig("riskMode", "fixed")}
                        className="flex-1 font-black h-12 rounded-xl"
                      >
                        <Shield className="mr-2 h-4 w-4 text-primary" /> FIXED RISK
                      </Button>
                    </div>

                    {config.riskMode === "dynamic" ? (
                      <div className="grid gap-6 md:grid-cols-2">
                        <Card className="border-border bg-card p-6 shadow-lg">
                          <h4 className="font-black text-lg mb-6 flex items-center gap-2">
                            <Activity className="h-5 w-5 text-accent" /> Alpha Scaling
                          </h4>
                          <div className="space-y-6">
                            <div className="space-y-2">
                              <div className="flex justify-between items-center">
                                <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Kelly Fraction</Label>
                                <span className="text-xs font-black text-accent">{config.kellyFraction}x</span>
                              </div>
                              <Input
                                type="number"
                                step="0.01"
                                value={config.kellyFraction}
                                onChange={(e) => updateConfig("kellyFraction", parseFloat(e.target.value))}
                                className="bg-secondary/30 h-10 font-mono"
                              />
                              <p className="text-[10px] text-muted-foreground leading-relaxed italic">Optimization factor for position sizing based on probabilistic edge.</p>
                            </div>

                            <div className="flex items-center justify-between p-4 rounded-xl bg-secondary/30 border border-border">
                              <div>
                                <p className="font-bold text-sm">Volatility Adjusted</p>
                                <p className="text-[10px] text-muted-foreground">Auto-scale by ATR/VIX data</p>
                              </div>
                              <Switch checked={config.volatilityAdjusted} onCheckedChange={(v) => updateConfig("volatilityAdjusted", v)} />
                            </div>

                            <div className="flex items-center justify-between p-4 rounded-xl bg-secondary/30 border border-border">
                              <div>
                                <p className="font-bold text-sm">Dynamic Scaling</p>
                                <p className="text-[10px] text-muted-foreground">Modify size during trend strength</p>
                              </div>
                              <Switch checked={config.dynamicPositionScaling} onCheckedChange={(v) => updateConfig("dynamicPositionScaling", v)} />
                            </div>
                          </div>
                        </Card>

                        <Card className="border-border bg-card p-6 shadow-lg border-l-4 border-l-destructive/50">
                          <h4 className="font-black text-lg mb-6 flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-destructive" /> Safety Limits
                          </h4>
                          <div className="space-y-6">
                            <div className="space-y-2">
                              <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Max Daily Drawdown (%)</Label>
                              <Input
                                type="number"
                                value={config.maxDailyDrawdown}
                                onChange={(e) => updateConfig("maxDailyDrawdown", parseFloat(e.target.value))}
                                className="bg-secondary/30 h-10 font-mono text-destructive font-black"
                              />
                              <div className="h-1 w-full bg-secondary rounded-full overflow-hidden mt-2">
                                <div className="h-full bg-destructive" style={{ width: `${config.maxDailyDrawdown * 5}%` }} />
                              </div>
                            </div>

                            <div className="space-y-2">
                              <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Risk Limit Per Trade (%)</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={config.riskLimitPerTrade}
                                onChange={(e) => updateConfig("riskLimitPerTrade", parseFloat(e.target.value))}
                                className="bg-secondary/30 h-10 font-mono"
                              />
                            </div>
                          </div>
                        </Card>
                      </div>
                    ) : (
                      <div className="grid gap-6 md:grid-cols-2">
                        <Card className="border-border bg-card p-6 shadow-lg border-l-4 border-l-primary/50">
                          <h4 className="font-black text-lg mb-6 flex items-center gap-2">
                            <Layers className="h-5 w-5 text-primary" /> Static Allocation
                          </h4>
                          <div className="space-y-6">
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Fixed Lot Size</Label>
                                <Input
                                  type="number"
                                  step="0.01"
                                  value={config.fixedLotSize}
                                  onChange={(e) => updateConfig("fixedLotSize", parseFloat(e.target.value))}
                                  className="bg-secondary/30 h-10 font-mono"
                                />
                              </div>
                            </div>
                          </div>
                        </Card>

                        <Card className="border-border bg-card p-6 shadow-lg">
                          <div className="flex items-center gap-2 mb-6">
                            <Target className="h-5 w-5 text-success" />
                            <h4 className="font-black text-lg">Exit Parameters</h4>
                          </div>

                          <Tabs defaultValue="ticks" className="w-full" onValueChange={(val) => updateConfig('exitMode', val)}>
                            <TabsList className="grid w-full grid-cols-2 mb-6 h-10 bg-secondary/30">
                              <TabsTrigger value="ticks" className="text-xs font-bold">TICKS MODE</TabsTrigger>
                              <TabsTrigger value="rr" className="text-xs font-bold">RISK : REWARD</TabsTrigger>
                            </TabsList>

                            <TabsContent value="ticks" className="space-y-4 animate-in slide-in-from-left-2 duration-300">
                              <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                  <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Stop Loss (Ticks)</Label>
                                  <Input
                                    type="number"
                                    value={config.fixedStopLoss}
                                    onChange={(e) => updateConfig("fixedStopLoss", parseInt(e.target.value))}
                                    className="bg-secondary/30 h-10 font-mono text-destructive"
                                  />
                                </div>
                                <div className="space-y-2">
                                  <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Take Profit (Ticks)</Label>
                                  <Input
                                    type="number"
                                    value={config.fixedTakeProfit}
                                    onChange={(e) => updateConfig("fixedTakeProfit", parseInt(e.target.value))}
                                    className="bg-secondary/30 h-10 font-mono text-success"
                                  />
                                </div>
                              </div>
                              <p className="text-[10px] text-muted-foreground leading-relaxed">
                                Static exits execute at precise price tick levels relative to entry.
                              </p>
                            </TabsContent>

                            <TabsContent value="rr" className="space-y-6 animate-in slide-in-from-right-2 duration-300">
                              <div className="space-y-4">
                                <div className="space-y-2">
                                  <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Reward Ratio (1 : X)</Label>
                                  <Input
                                    type="number"
                                    step="0.1"
                                    min="0.1"
                                    value={config.riskRewardRatio}
                                    onChange={(e) => updateConfig("riskRewardRatio", parseFloat(e.target.value))}
                                    className="bg-secondary/30 h-10 font-mono text-success font-bold"
                                  />
                                </div>
                              </div>

                              <div className="rounded-xl bg-secondary/20 p-4 border border-border/50 space-y-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-bold text-muted-foreground">PROJECTED TARGET</span>
                                  <Badge variant="outline" className="bg-success/10 text-success border-0 font-mono">
                                    +{Math.floor(config.fixedStopLoss * config.riskRewardRatio)} TICKS
                                  </Badge>
                                </div>
                                <div className="h-2 w-full flex rounded-full overflow-hidden">
                                  <div className="h-full bg-destructive" style={{ width: `${100 / (1 + config.riskRewardRatio)}%` }} />
                                  <div className="h-full bg-success" style={{ width: `${100 * config.riskRewardRatio / (1 + config.riskRewardRatio)}%` }} />
                                </div>
                                <div className="flex justify-between text-[10px] font-black uppercase text-muted-foreground">
                                  <span>Risk {((1 / (1 + config.riskRewardRatio)) * 100).toFixed(0)}%</span>
                                  <span>Reward {((config.riskRewardRatio / (1 + config.riskRewardRatio)) * 100).toFixed(0)}%</span>
                                </div>
                              </div>
                            </TabsContent>
                          </Tabs>
                        </Card>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="instruments" className="space-y-6">
                  <Card className="border-border bg-card p-6">
                    <div className="flex flex-col space-y-6 md:flex-row md:items-center md:justify-between md:space-y-0 mb-6">
                      <div className="space-y-1">
                        <h4 className="font-black text-lg">Active Trading Nodes</h4>
                        <p className="text-xs text-muted-foreground">Multi-asset execution pool.</p>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-2 bg-secondary/30 p-1 rounded-lg">
                            <Button
                              size="sm"
                              variant={instrumentSource === 'crypto' ? 'default' : 'ghost'}
                              onClick={() => setInstrumentSource('crypto')}
                              className="text-xs font-bold h-8 flex-1"
                            >
                              CRYPTO
                            </Button>
                            <Button
                              size="sm"
                              variant={instrumentSource === 'mt4' ? 'default' : 'ghost'}
                              onClick={() => setInstrumentSource('mt4')}
                              className="text-xs font-bold h-8 flex-1"
                            >
                              MT4
                            </Button>
                            <Button
                              size="sm"
                              variant={instrumentSource === 'mt5' ? 'default' : 'ghost'}
                              onClick={() => setInstrumentSource('mt5')}
                              className="text-xs font-bold h-8 flex-1"
                            >
                              MT5
                            </Button>
                            <Button
                              size="sm"
                              variant={instrumentSource === 'fix' ? 'default' : 'ghost'}
                              onClick={() => setInstrumentSource('fix')}
                              className="text-xs font-bold h-8 flex-1"
                            >
                              FIX API
                            </Button>
                          </div>
                          <div className="flex items-center gap-2 bg-secondary/30 p-1 rounded-lg">
                            <Button
                              size="sm"
                              variant={config.tradingMode === 'spot' ? 'default' : 'ghost'}
                              onClick={() => updateConfig('tradingMode', 'spot')}
                              className="text-xs font-bold h-7 flex-1"
                            >
                              SPOT
                            </Button>
                            <Button
                              size="sm"
                              variant={config.tradingMode === 'futures' ? 'default' : 'ghost'}
                              onClick={() => updateConfig('tradingMode', 'futures')}
                              className="text-xs font-bold h-7 flex-1"
                            >
                              FUTURES
                            </Button>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Input
                            placeholder="SYM..."
                            className="h-9 w-24 bg-secondary/30 text-xs font-bold uppercase"
                            value={newInstrumentInput}
                            onChange={(e) => setNewInstrumentInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addInstrument()}
                          />
                          <Button size="sm" className="font-bold h-9 bg-primary" onClick={addInstrument}>
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-h-[400px] overflow-y-auto pr-2">
                      {availableInstruments.map(sym => (
                        <div
                          key={sym}
                          className={`group relative p-4 rounded-2xl border transition-all cursor-pointer ${config.selectedInstruments.includes(sym)
                            ? 'border-primary bg-primary/5'
                            : 'border-border bg-secondary/30 hover:border-border/80'
                            }`}
                          onClick={() => {
                            const newSelected = config.selectedInstruments.includes(sym)
                              ? config.selectedInstruments.filter(i => i !== sym)
                              : [...config.selectedInstruments, sym];
                            updateConfig("selectedInstruments", newSelected);
                          }}
                        >
                          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span
                              className="flex h-5 w-5 items-center justify-center rounded-full bg-destructive/20 text-destructive hover:bg-destructive hover:text-white"
                              onClick={(e) => {
                                e.stopPropagation();
                                removeInstrument(sym);
                              }}
                            >
                              <Plus className="h-3 w-3 rotate-45" />
                            </span>
                          </div>
                          <p className="font-black text-center">{sym}</p>
                          <p className="text-[10px] text-center text-muted-foreground font-bold mt-1 uppercase">
                            {instrumentSource}
                          </p>
                        </div>
                      ))}
                    </div>
                  </Card>
                </TabsContent>
                <TabsContent value="latency" className="space-y-6">
                  <Card className="border-border bg-card p-6">
                    <h4 className="font-black text-lg mb-6 flex items-center gap-2">
                      <Clock className="h-5 w-5 text-accent" /> Infrastructure Latency Tuning
                    </h4>
                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label className="text-xs font-bold text-muted-foreground">TARGET LATENCY (MS)</Label>
                          <Input type="number" step="0.1" value={config.targetLatency} onChange={(e) => updateConfig("targetLatency", e.target.value)} className="bg-secondary/30" />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs font-bold text-muted-foreground">MAX LATENCY CUTOFF (MS)</Label>
                          <Input type="number" step="0.1" value={config.maxLatency} onChange={(e) => updateConfig("maxLatency", e.target.value)} className="bg-secondary/30" />
                        </div>
                      </div>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 rounded-xl bg-secondary/30 border border-border">
                          <Label className="font-bold">Hardware Co-Location</Label>
                          <Badge className="bg-success text-success-foreground">ACTIVE</Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-xl bg-secondary/30 border border-border">
                          <Label className="font-bold">Fiber-Optic Direct Path</Label>
                          <Badge className="bg-success text-success-foreground">LINKED</Badge>
                        </div>
                      </div>
                    </div>
                  </Card>
                </TabsContent>
              </Tabs>
              <div className="flex justify-end pt-4 border-t border-border mt-6">
                <Button
                  onClick={handleSaveConfig}
                  className="font-black gap-2 h-11 px-8 rounded-xl shadow-lg shadow-primary/20 bg-primary hover:bg-primary/90 transition-all active:scale-95"
                >
                  <Save className="h-4 w-4" />
                  SAVE CONFIGURATION
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Sidebar - Real-time Execution Feed */}
        <div className="space-y-8">
          <Card className="border-border bg-card p-6 shadow-2xl overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-5">
              <Terminal className="h-20 w-20" />
            </div>
            <h3 className="text-xl font-black mb-6 flex items-center gap-2">
              <Terminal className="h-5 w-5 text-accent" /> Execution Feed
            </h3>
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-3">
                {executionLogs.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin opacity-20" />
                    <p className="font-bold">Waiting for node activation...</p>
                  </div>
                ) : (
                  executionLogs.map((log) => (
                    <div key={log.id} className="group relative overflow-hidden rounded-xl border border-border/50 bg-secondary/20 p-3 text-xs transition-all hover:bg-secondary/40 animate-in slide-in-from-right-4">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-black text-muted-foreground/60">{log.time}</span>
                        <Badge className={`${log.action === 'BUY' ? 'bg-success/20 text-success' :
                          log.action === 'SELL' ? 'bg-destructive/20 text-destructive' : 'bg-primary/20 text-primary'
                          } border-0 text-[10px] h-4 px-1.5`}>
                          {log.action}
                        </Badge>
                      </div>
                      <div className="flex justify-between items-end">
                        <div>
                          <p className="font-black text-foreground">{log.symbol}</p>
                          <p className="font-mono text-muted-foreground">${log.price}</p>
                        </div>
                        <span className="text-success font-black tracking-tighter opacity-0 group-hover:opacity-100 transition-opacity">
                          FILLED ⚡
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </Card>

          <Card className="border-border bg-gradient-to-br from-primary/20 to-accent/20 p-6">
            <h4 className="text-lg font-black mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" /> Node Health
            </h4>
            <div className="space-y-4">
              {[
                { label: "CPU CORE X-8", value: 45, color: "bg-primary" },
                { label: "RAM CL-16", value: 72, color: "bg-accent" },
                { label: "NET-BANDWIDTH", value: 28, color: "bg-success" },
              ].map((stat, i) => (
                <div key={i} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-black uppercase">
                    <span>{stat.label}</span>
                    <span>{stat.value}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-background rounded-full overflow-hidden">
                    <div className={`h-full ${stat.color} transition-all duration-1000`} style={{ width: `${stat.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 rounded-xl bg-background/50 p-4 border border-white/5 backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="h-3 w-3 rounded-full bg-success animate-ping" />
                <p className="text-xs font-bold text-foreground">SYSTEM ARMED & SYNCED</p>
              </div>
            </div>
          </Card>
        </div>
      </div >
    </div >
  );
};

export default HFT;
