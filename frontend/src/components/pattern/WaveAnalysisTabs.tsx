import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Waves,
  BarChart3,
  Clock,
  TrendingUp,
  TrendingDown,
  Target,
  Calendar,
  Zap,
  RefreshCw,
  Activity,
  Timer,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Area,
  Line,
  ReferenceLine,
} from "recharts";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import {
  generateTimeCycleData,
  enrichWithGannWaves,
  enrichWithElliottWaves,
} from "@/lib/patternUtils";
import { apiService } from "@/services/apiService";

interface WaveAnalysisTabsProps {
  currentPrice: number;
  candleData: any[];
  symbol?: string;
}

// Live countdown component with HH:MM:SS
const LiveCountdown = ({ targetDate, className = "" }: { targetDate: string; className?: string }) => {
  const [remaining, setRemaining] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0, total: 0 });

  useEffect(() => {
    const update = () => {
      const total = Date.parse(targetDate) - Date.now();
      if (total <= 0) {
        setRemaining({ days: 0, hours: 0, minutes: 0, seconds: 0, total: 0 });
        return;
      }
      setRemaining({
        days: Math.floor(total / (1000 * 60 * 60 * 24)),
        hours: Math.floor((total / (1000 * 60 * 60)) % 24),
        minutes: Math.floor((total / (1000 * 60)) % 60),
        seconds: Math.floor((total / 1000) % 60),
        total,
      });
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, [targetDate]);

  if (remaining.total <= 0) {
    return <span className={cn("text-success font-bold animate-pulse", className)}>⚡ ACTIVE NOW</span>;
  }

  const pad = (n: number) => n.toString().padStart(2, "0");

  return (
    <span className={cn("font-mono tabular-nums", className)}>
      {remaining.days > 0 && <span>{remaining.days}<span className="text-muted-foreground text-[9px] mx-0.5">d</span></span>}
      {pad(remaining.hours)}<span className="text-muted-foreground text-[9px]">h</span>
      <span className="text-primary">:</span>
      {pad(remaining.minutes)}<span className="text-muted-foreground text-[9px]">m</span>
      <span className="text-primary">:</span>
      {pad(remaining.seconds)}<span className="text-muted-foreground text-[9px]">s</span>
    </span>
  );
};

export const WaveAnalysisTabs = ({ currentPrice, candleData, symbol = "BTC-USD" }: WaveAnalysisTabsProps) => {
  const [apiData, setApiData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  const timePatterns = generateTimeCycleData();

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchWaveAnalysis = async () => {
      setIsLoading(true);
      try {
        const response = await apiService.getWaveForecast({ symbol });
        if (response.status === "success") {
          setApiData(response);
        }
      } catch (error) {
        console.error("Error fetching wave analysis:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWaveAnalysis();
    const interval = setInterval(fetchWaveAnalysis, 30000);
    return () => clearInterval(interval);
  }, [symbol]);

  const gannAnalysis = apiData?.gannAnalysis;
  const elliottAnalysis = apiData?.elliottAnalysis;

  const gannData = enrichWithGannWaves(candleData);
  const elliottData = enrichWithElliottWaves(candleData);

  const elliottWaveCount = elliottAnalysis ? {
    currentWave: elliottAnalysis.current_wave || "Unknown",
    subWave: elliottAnalysis.sub_wave || "N/A",
    degree: elliottAnalysis.degree || "Unknown",
    trend: elliottAnalysis.trend || "Neutral",
    targets: {
      wave3: elliottAnalysis.targets?.wave3?.toString() || "0",
      wave4: elliottAnalysis.targets?.wave4?.toString() || "0",
      wave5: elliottAnalysis.targets?.wave5?.toString() || "0",
    },
    invalidation: elliottAnalysis.invalidation?.toString() || "0",
    nextPivotDate: elliottAnalysis.next_pivot_date || null,
    estimatedDuration: elliottAnalysis.estimated_duration || null,
  } : {
    currentWave: "Calculating...",
    subWave: "...",
    degree: "...",
    trend: "Wait",
    targets: { wave3: "0", wave4: "0", wave5: "0" },
    invalidation: "0",
    nextPivotDate: null,
    estimatedDuration: null,
  };

  // Generate estimated target times for waves (based on current time + analysis periods)
  const generateEstimatedTargets = () => {
    const now = Date.now();
    const baseInterval = 4 * 60 * 60 * 1000; // 4 hours base

    return {
      gannWaveTargets: [
        { label: "Wave 1 Complete", time: new Date(now + baseInterval * 2.5).toISOString(), price: currentPrice * 1.025, direction: "up" },
        { label: "Wave 2 Retrace", time: new Date(now + baseInterval * 4).toISOString(), price: currentPrice * 0.988, direction: "down" },
        { label: "Wave 3 Impulse", time: new Date(now + baseInterval * 8).toISOString(), price: currentPrice * 1.062, direction: "up" },
        { label: "Wave 4 Correction", time: new Date(now + baseInterval * 11).toISOString(), price: currentPrice * 1.035, direction: "down" },
        { label: "Wave 5 Final", time: new Date(now + baseInterval * 16).toISOString(), price: currentPrice * 1.085, direction: "up" },
      ],
      elliottWaveTargets: [
        { label: "Sub-wave iii", time: new Date(now + baseInterval * 3).toISOString(), price: currentPrice * 1.035, fib: "1.000x" },
        { label: "Wave 3 Target", time: new Date(now + baseInterval * 7).toISOString(), price: currentPrice * 1.058, fib: "1.618x" },
        { label: "Wave 4 Pull", time: new Date(now + baseInterval * 10).toISOString(), price: currentPrice * 1.028, fib: "0.382" },
        { label: "Wave 5 Peak", time: new Date(now + baseInterval * 15).toISOString(), price: currentPrice * 1.092, fib: "2.618x" },
      ],
    };
  };

  const estimatedTargets = generateEstimatedTargets();

  const pricePatterns = [
    { name: "Head & Shoulders", type: "Reversal", confidence: 87, direction: "Bearish", timeframe: "H4" },
    { name: "Ascending Triangle", type: "Continuation", confidence: 82, direction: "Bullish", timeframe: "H1" },
    { name: "Double Bottom", type: "Reversal", confidence: 78, direction: "Bullish", timeframe: "D1" },
    { name: "Cup & Handle", type: "Continuation", confidence: 75, direction: "Bullish", timeframe: "W1" },
    { name: "Falling Wedge", type: "Reversal", confidence: 71, direction: "Bullish", timeframe: "H4" },
    { name: "Bullish Flag", type: "Continuation", confidence: 68, direction: "Bullish", timeframe: "H1" },
  ];

  return (
    <Tabs defaultValue="gann-wave" className="w-full">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <TabsList className="grid grid-cols-4 bg-muted/50 p-1 flex-1">
          <TabsTrigger value="gann-wave" className="gap-2 text-xs md:text-sm">
            <Waves className="h-4 w-4" />
            <span className="hidden md:inline">Gann Wave</span>
            <span className="md:hidden">Gann</span>
          </TabsTrigger>
          <TabsTrigger value="elliott-wave" className="gap-2 text-xs md:text-sm">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden md:inline">Elliott Wave</span>
            <span className="md:hidden">Elliott</span>
          </TabsTrigger>
          <TabsTrigger value="time-cycles" className="gap-2 text-xs md:text-sm">
            <Clock className="h-4 w-4" />
            <span className="hidden md:inline">Time Cycles</span>
            <span className="md:hidden">Cycles</span>
          </TabsTrigger>
          <TabsTrigger value="patterns" className="gap-2 text-xs md:text-sm">
            <Target className="h-4 w-4" />
            <span className="hidden md:inline">Price Patterns</span>
            <span className="md:hidden">Patterns</span>
          </TabsTrigger>
        </TabsList>
        <Badge variant="outline" className="h-9 px-3 bg-muted/30 border-primary/20 flex items-center gap-2 font-mono text-xs md:text-sm">
          <Clock className="h-3.5 w-3.5 text-primary animate-pulse" />
          {currentTime.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })} UTC
        </Badge>
      </div>

      {/* ================================================================ */}
      {/* GANN WAVE TAB — Improved Layout */}
      {/* ================================================================ */}
      <TabsContent value="gann-wave" className="mt-6 space-y-4">
        {/* Chart Section — Full Width */}
        <Card className="overflow-hidden border-border bg-card">
          <div className="border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-bold text-foreground">
              <Waves className="h-5 w-5 text-primary" />
              Gann Wave — Realtime Candlestick Overlay
            </h3>
            <div className="flex items-center gap-2">
              {isLoading && <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />}
              <Badge variant="outline" className="border-success text-success bg-success/5 text-xs animate-pulse">LIVE</Badge>
            </div>
          </div>
          <div className="h-[420px] p-4">
            <CandlestickChart
              data={gannData}
              height={380}
              indicatorKeys={['sma7', 'sma25']}
            >
              <Line type="monotone" dataKey="gann_composite" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Gann Composite" />
              <Line type="monotone" dataKey="gann_fast" stroke="hsl(var(--accent))" strokeWidth={1} dot={false} opacity={0.6} name="Fast Cycle" />
              <Line type="monotone" dataKey="gann_slow" stroke="hsl(var(--muted-foreground))" strokeWidth={1} dot={false} opacity={0.4} name="Slow Cycle" />
            </CandlestickChart>
          </div>
        </Card>

        {/* Two-column: Wave Details + Estimated Target Times */}
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Gann Wave Details */}
          <Card className="overflow-hidden border-border bg-card">
            <div className="border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4">
              <h3 className="font-bold text-foreground flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary" />
                Wave Breakdown
              </h3>
            </div>
            <ScrollArea className="h-[360px]">
              <div className="space-y-3 p-4">
                {gannAnalysis?.waves?.map((wave: any, idx: number) => (
                  <div key={idx} className="rounded-xl bg-muted/30 p-3 border border-border/20 transition-all hover:bg-muted/50">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex flex-col">
                        <span className="font-bold text-xs text-foreground uppercase tracking-tight">Wave {wave.number}</span>
                        <span className="text-[9px] text-muted-foreground font-mono">{wave.gann_angle} ({wave.degrees}°)</span>
                      </div>
                      <Badge variant="outline" className={cn("text-[10px] font-bold border-none px-2 py-0", wave.direction === "up" ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive")}>
                        {wave.direction === "up" ? <ArrowUpRight className="h-3 w-3 mr-0.5" /> : <ArrowDownRight className="h-3 w-3 mr-0.5" />}
                        {wave.direction.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-muted-foreground">Change: <span className="text-foreground font-bold">{wave.change_pct}%</span></span>
                      <span className="text-muted-foreground">Duration: <span className="text-foreground font-bold">{wave.bars} bars</span></span>
                    </div>
                  </div>
                ))}

                {gannAnalysis?.projection && (
                  <div className="rounded-xl bg-primary/5 p-4 border border-primary/30 mt-4 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-2 opacity-10">
                      <Zap className="h-8 w-8 text-primary" />
                    </div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold text-primary uppercase tracking-widest flex items-center gap-1">
                        <Target className="h-3 w-3" /> Next Target
                      </span>
                      <Badge className="bg-primary text-primary-foreground text-[10px] h-4">
                        {gannAnalysis.projection.angle_name}
                      </Badge>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-end">
                        <div className="text-[10px] text-muted-foreground uppercase font-bold">Price Target</div>
                        <div className="text-xl font-mono font-black text-foreground">${gannAnalysis.projection.target_price}</div>
                      </div>
                      <div className="p-2 rounded bg-background/50 border border-border/30 space-y-1">
                        <div className="flex items-center justify-between text-[10px] text-muted-foreground font-bold uppercase">
                          <span className="flex items-center gap-1"><Timer className="h-3 w-3" /> Countdown</span>
                          <LiveCountdown targetDate={gannAnalysis.projection.target_date} className="text-xs text-primary font-bold" />
                        </div>
                        <div className="text-xs font-bold text-foreground font-mono flex items-center gap-2">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          {new Date(gannAnalysis.projection.target_date).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                          {new Date(gannAnalysis.projection.target_date).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-[9px] text-muted-foreground uppercase font-mono">
                        <span>Confidence</span>
                        <span>{(gannAnalysis.projection.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                )}

                {!gannAnalysis && !isLoading && (
                  <p className="text-sm text-center text-muted-foreground p-8">Waiting for backend analysis data...</p>
                )}
              </div>
            </ScrollArea>
          </Card>

          {/* Estimated Target Times — Live Countdown */}
          <Card className="overflow-hidden border-border bg-card">
            <div className="border-b border-border bg-gradient-to-r from-accent/5 to-primary/5 p-4">
              <h3 className="font-bold text-foreground flex items-center gap-2">
                <Timer className="h-4 w-4 text-accent" />
                Gann Wave — Estimated Target Time
              </h3>
            </div>
            <ScrollArea className="h-[360px]">
              <div className="space-y-2 p-4">
                {estimatedTargets.gannWaveTargets.map((target, idx) => (
                  <div key={idx} className={cn(
                    "rounded-xl p-3 border transition-all hover:shadow-sm",
                    target.direction === "up"
                      ? "bg-success/5 border-success/20 hover:bg-success/10"
                      : "bg-destructive/5 border-destructive/20 hover:bg-destructive/10"
                  )}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {target.direction === "up"
                          ? <ArrowUpRight className="h-4 w-4 text-success" />
                          : <ArrowDownRight className="h-4 w-4 text-destructive" />
                        }
                        <span className="text-sm font-bold text-foreground">{target.label}</span>
                      </div>
                      <Badge variant="outline" className={cn(
                        "text-xs font-mono",
                        target.direction === "up" ? "border-success/30 text-success" : "border-destructive/30 text-destructive"
                      )}>
                        ${target.price.toFixed(2)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {new Date(target.time).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                        {new Date(target.time).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Timer className="h-3 w-3 text-primary" />
                        <LiveCountdown targetDate={target.time} className="text-xs font-bold text-primary" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>
        </div>
      </TabsContent>

      {/* ================================================================ */}
      {/* ELLIOTT WAVE TAB — Improved Layout */}
      {/* ================================================================ */}
      <TabsContent value="elliott-wave" className="mt-6 space-y-4">
        {/* Chart Section — Full Width */}
        <Card className="overflow-hidden border-border bg-card">
          <div className="border-b border-border bg-gradient-to-r from-accent/5 to-primary/5 p-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-bold text-foreground">
              <BarChart3 className="h-5 w-5 text-accent" />
              Elliott Wave — Realtime Analysis
            </h3>
            <div className="flex items-center gap-2">
              {isLoading && <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />}
              <Badge variant="outline" className="border-accent text-accent bg-accent/5 text-xs animate-pulse">LIVE</Badge>
            </div>
          </div>
          <div className="h-[420px] p-4">
            <CandlestickChart
              data={elliottData}
              height={380}
              indicatorKeys={['sma7', 'sma25']}
            >
              <Area type="monotone" dataKey="elliott_wave" fill="hsl(var(--primary))" fillOpacity={0.05} stroke="hsl(var(--primary))" strokeWidth={2} name="Wave Projection" />
              <ReferenceLine y={Number(elliottWaveCount.targets.wave3)} stroke="hsl(var(--success))" strokeDasharray="5 5" label={{ value: 'W3', position: 'right', fill: 'hsl(var(--success))', fontSize: 10 }} />
              <ReferenceLine y={Number(elliottWaveCount.invalidation)} stroke="hsl(var(--destructive))" strokeDasharray="5 5" label={{ value: 'Inv.', position: 'right', fill: 'hsl(var(--destructive))', fontSize: 10 }} />
            </CandlestickChart>
          </div>
        </Card>

        {/* Two-column: Wave Count + Estimated Targets */}
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Elliott Wave Count Info */}
          <Card className="overflow-hidden border-border bg-card">
            <div className="border-b border-border bg-gradient-to-r from-accent/5 to-primary/5 p-4">
              <h3 className="font-bold text-foreground flex items-center gap-2">
                <Waves className="h-4 w-4 text-accent" />
                Wave Count & Levels
              </h3>
            </div>
            <ScrollArea className="h-[400px]">
              <div className="space-y-4 p-4">
                {/* Current Wave Info */}
                <div className="rounded-xl bg-primary/5 p-4 border border-primary/30 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-2 opacity-10">
                    <Waves className="h-8 w-8 text-primary" />
                  </div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex flex-col">
                      <span className="text-2xl font-black text-foreground tracking-tighter">{elliottWaveCount.currentWave}</span>
                      <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">{elliottWaveCount.degree} Degree</span>
                    </div>
                    <Badge className={cn("font-bold px-2 py-0.5", elliottWaveCount.trend === "Bullish" ? "bg-success/20 text-success" : "bg-destructive/20 text-destructive")}>
                      {elliottWaveCount.trend}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Activity className="h-3 w-3" /> Sub-wave {elliottWaveCount.subWave}</span>
                  </div>

                  {elliottWaveCount.nextPivotDate && (
                    <div className="mt-4 p-3 rounded-lg bg-background/50 border border-border/30">
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground uppercase font-bold mb-1">
                        <span className="flex items-center gap-1"><Timer className="h-3 w-3" /> Projected Pivot</span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <div className="flex items-center gap-2 text-sm font-bold text-foreground font-mono">
                          <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                          {new Date(elliottWaveCount.nextPivotDate).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                          {new Date(elliottWaveCount.nextPivotDate).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </div>
                        <LiveCountdown targetDate={elliottWaveCount.nextPivotDate} className="text-sm font-bold text-primary" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Fibonacci Target Levels */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-[10px] uppercase text-muted-foreground tracking-widest">Fibo Target Levels</h4>
                    <span className="text-[10px] text-primary font-mono animate-pulse">Est. Active</span>
                  </div>
                  {[
                    { label: "Wave 3 (1.618x)", value: elliottWaveCount.targets.wave3, color: "text-success" },
                    { label: "Wave 4 (0.382)", value: elliottWaveCount.targets.wave4, color: "text-accent" },
                    { label: "Wave 5 (2.618x)", value: elliottWaveCount.targets.wave5, color: "text-success" },
                  ].map((target, idx) => (
                    <div key={idx} className="flex justify-between rounded-lg bg-muted/50 p-3">
                      <span className="text-sm text-muted-foreground">{target.label}</span>
                      <span className={`font-mono font-semibold ${target.color}`}>${target.value}</span>
                    </div>
                  ))}
                  <div className="flex justify-between rounded-lg bg-destructive/10 p-3 border border-destructive/30">
                    <span className="text-sm text-destructive">Invalidation</span>
                    <span className="font-mono font-semibold text-destructive">${elliottWaveCount.invalidation}</span>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </Card>

          {/* Elliott Estimated Target Times — Live Countdown */}
          <Card className="overflow-hidden border-border bg-card">
            <div className="border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4">
              <h3 className="font-bold text-foreground flex items-center gap-2">
                <Timer className="h-4 w-4 text-primary" />
                Elliott Wave — Estimated Target Time
              </h3>
            </div>
            <ScrollArea className="h-[400px]">
              <div className="space-y-2 p-4">
                {estimatedTargets.elliottWaveTargets.map((target, idx) => (
                  <div key={idx} className="rounded-xl bg-muted/30 p-4 border border-border/20 transition-all hover:bg-muted/50 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                          <span className="text-xs font-black text-primary">{idx + 1}</span>
                        </div>
                        <div>
                          <span className="text-sm font-bold text-foreground">{target.label}</span>
                          <div className="text-[10px] text-muted-foreground font-mono">Fib: {target.fib}</div>
                        </div>
                      </div>
                      <Badge variant="outline" className="border-primary/30 text-primary font-mono text-sm">
                        ${target.price.toFixed(2)}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded-lg bg-background/50 border border-border/20">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {new Date(target.time).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                        {new Date(target.time).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Timer className="h-3 w-3 text-accent" />
                        <LiveCountdown targetDate={target.time} className="text-xs font-bold text-accent" />
                      </div>
                    </div>

                    {/* Progress bar */}
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-primary to-accent transition-all"
                        style={{ width: `${Math.max(5, 100 - ((Date.parse(target.time) - Date.now()) / (16 * 4 * 60 * 60 * 1000)) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>
        </div>
      </TabsContent>

      {/* ================================================================ */}
      {/* TIME CYCLES TAB */}
      {/* ================================================================ */}
      <TabsContent value="time-cycles" className="mt-6 space-y-4">
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="overflow-hidden border-border bg-card">
            <div className="border-b border-border bg-gradient-to-r from-accent/5 to-primary/5 p-4">
              <h3 className="flex items-center gap-2 text-lg font-bold text-foreground">
                <Clock className="h-5 w-5 text-accent" />
                Time Cycle Analysis
              </h3>
            </div>
            <ScrollArea className="h-[380px]">
              <div className="space-y-3 p-4">
                {timePatterns.map((pattern, idx) => (
                  <div key={idx} className="rounded-xl bg-muted/50 p-4 border border-border">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-primary" />
                        <span className="font-semibold text-foreground">{pattern.cycle}</span>
                        <Badge variant="outline" className="text-xs">{pattern.type}</Badge>
                      </div>
                      <Badge className={pattern.confidence >= 85 ? "bg-success text-success-foreground" : pattern.confidence >= 70 ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground"}>
                        {pattern.confidence}%
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">Next Turn: {pattern.nextTurn}</span>
                      <LiveCountdown targetDate={pattern.nextTurn} className="text-xs font-bold text-primary" />
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                      <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${100 - (pattern.daysRemaining / 90) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>

          <Card className="overflow-hidden border-border bg-card">
            <div className="border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4">
              <h3 className="flex items-center gap-2 text-lg font-bold text-foreground">
                <Zap className="h-5 w-5 text-primary" />
                Gann Time Squares
              </h3>
            </div>
            <div className="grid grid-cols-3 gap-3 p-4">
              {[
                { period: "7 Days", date: "Jan 31", active: true },
                { period: "15 Days", date: "Feb 5", active: false },
                { period: "30 Days", date: "Feb 15", active: false },
                { period: "45 Days", date: "Feb 28", active: false },
                { period: "60 Days", date: "Mar 15", active: false },
                { period: "90 Days", date: "Apr 1", active: true },
                { period: "120 Days", date: "Apr 30", active: false },
                { period: "180 Days", date: "Jun 1", active: true },
                { period: "360 Days", date: "Dec 1", active: false },
              ].map((item, idx) => (
                <div key={idx} className={`rounded-xl p-4 text-center border transition-all ${item.active ? "bg-primary/10 border-primary shadow-sm" : "bg-muted/30 border-border hover:bg-muted/50"}`}>
                  <div className="text-xs text-muted-foreground">{item.period}</div>
                  <div className={`mt-1 font-bold ${item.active ? "text-primary" : "text-foreground"}`}>
                    {item.date}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </TabsContent>

      {/* ================================================================ */}
      {/* PRICE PATTERNS TAB */}
      {/* ================================================================ */}
      <TabsContent value="patterns" className="mt-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {pricePatterns.map((pattern, idx) => (
            <Card key={idx} className="overflow-hidden border-border bg-card transition-all hover:shadow-md">
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-foreground">{pattern.name}</h4>
                  <Badge variant="outline" className="font-mono">{pattern.timeframe}</Badge>
                </div>
                <div className="flex items-center gap-2 mb-4">
                  <Badge className={pattern.direction === "Bullish" ? "bg-success text-success-foreground" : "bg-destructive text-destructive-foreground"}>
                    {pattern.direction === "Bullish" ? <TrendingUp className="mr-1 h-3 w-3" /> : <TrendingDown className="mr-1 h-3 w-3" />}
                    {pattern.direction}
                  </Badge>
                  <Badge variant="secondary">{pattern.type}</Badge>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Confidence</span>
                  <span className={`font-bold font-mono ${pattern.confidence >= 80 ? "text-success" : pattern.confidence >= 70 ? "text-accent" : "text-muted-foreground"}`}>
                    {pattern.confidence}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div className={`h-full rounded-full transition-all ${pattern.confidence >= 80 ? "bg-success" : pattern.confidence >= 70 ? "bg-accent" : "bg-muted"}`} style={{ width: `${pattern.confidence}%` }} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </TabsContent>
    </Tabs>
  );
};
