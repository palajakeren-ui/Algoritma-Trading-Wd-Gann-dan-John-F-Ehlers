import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrendingUp, Layers, ZoomIn, ZoomOut, BarChart3, Clock, Zap, Wifi, Smartphone, Monitor, Activity } from "lucide-react";
import { PageSection } from "@/components/PageSection";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { useDataFeed } from "@/context/DataFeedContext";
import { useIsMobile } from "@/hooks/use-mobile";

const Charts = () => {
  const isMobile = useIsMobile();
  const { marketData, candles, isConnected, subscribe } = useDataFeed();
  const [activeSymbol, setActiveSymbol] = useState("BTC-USD");

  const [activeOverlays, setActiveOverlays] = useState<Set<string>>(new Set([
    "Gann Square 360", "Gann Angles 1x1", "MAMA (MESA Adaptive)"
  ]));

  useEffect(() => {
    subscribe(activeSymbol);
  }, [activeSymbol, subscribe]);

  const currentMarketData = marketData[activeSymbol] || {
    price: 47500,
    change: 0,
    changePercent: 0,
    timestamp: new Date(),
    source: 'Simulation'
  };

  const currentPrice = currentMarketData.price;
  const currentCandles = candles[activeSymbol] || [];

  const toggleOverlay = (name: string) => {
    const next = new Set(activeOverlays);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setActiveOverlays(next);
  };

  const gannAngles = [
    "16x1", "8x1", "4x1", "3x1", "2x1", "1x1", "1x2", "1x3", "1x4", "1x8", "1x16"
  ];

  const ehlersOverlays = [
    "MAMA (MESA Adaptive)",
    "FAMA (Following Adaptive)",
    "Fisher Transform",
    "Super Smoother",
    "Instantaneous Trendline",
    "Cyber Cycle",
    "SineWave Indicator",
    "Roofing Filter",
    "Bandpass Filter",
    "Smoothed RSI",
    "Decycler",
    "Dominant Cycle"
  ];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-card/30 p-4 rounded-2xl border border-border/50 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-foreground">Advanced Financial Charts</h1>
            <Badge variant="outline" className="hidden md:flex gap-1 border-primary/50 text-primary">
              <Zap className="w-3 h-3" /> Professional
            </Badge>
          </div>
          <p className="text-muted-foreground">Synchronized Data Feed: {activeSymbol} via {currentMarketData.source}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className={isConnected ? "bg-success/10 text-success border-success/20 px-3 py-1" : "bg-destructive/10 text-destructive border-destructive/20 px-3 py-1"}>
            <Wifi className="w-3.5 h-3.5 mr-2 animate-pulse" />
            {isConnected ? "Live Feed" : "Disconnected"}
          </Badge>
          <div className="flex items-center space-x-1 border rounded-lg p-1 bg-background/50">
            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-secondary"><ZoomOut className="w-4 h-4" /></Button>
            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-secondary"><ZoomIn className="w-4 h-4" /></Button>
          </div>
        </div>
      </div>

      {/* Main Layout: Chart + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chart Area */}
        <div className="lg:col-span-3 space-y-4">
          <PageSection
            title={`Market Execution — ${activeSymbol}`}
            icon={<Layers className="w-5 h-5 text-primary" />}
            headerAction={
              <div className="flex items-center gap-4">
                <div className="text-2xl font-bold text-foreground font-mono">
                  ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <Badge variant="outline" className={`${currentMarketData.change >= 0 ? "bg-success/10 text-success border-success/20" : "bg-destructive/10 text-destructive border-destructive/20"}`}>
                  {currentMarketData.change >= 0 ? '+' : ''}{currentMarketData.changePercent.toFixed(2)}%
                </Badge>
              </div>
            }
          >
            <div className="bg-card rounded-xl border border-border p-1 h-[650px] shadow-2xl relative overflow-hidden group">
              <CandlestickChart
                data={currentCandles}
                height={650}
                showGannAngles={Array.from(activeOverlays).some(o => o.startsWith("Gann Angles"))}
                activeGannAngles={Array.from(activeOverlays).filter(o => o.startsWith("Gann Angles")).map(o => o.replace("Gann Angles ", ""))}
                showGannWave={activeOverlays.has("Gann Wave")}
                showElliottWave={activeOverlays.has("Elliott Wave")}
                showGannBox={activeOverlays.has("Gann Box")}
                showGannAstro={activeOverlays.has("Gann Astrology")}
                showGannSquares={Array.from(activeOverlays).some(o => o.startsWith("Gann Square") && o !== "Gann Square of 9")}
                activeGannSquares={Array.from(activeOverlays)
                  .filter(o => o.startsWith("Gann Square ") && o !== "Gann Square of 9")
                  .map(o => parseFloat(o.replace("Gann Square ", ""))) as (24.52 | 90 | 360)[]}
                indicatorKeys={Array.from(activeOverlays).filter(o => ehlersOverlays.includes(o))}
              />
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2 p-2 bg-secondary/20 rounded-lg border border-border/50">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest mr-2 px-2">Active:</span>
              {Array.from(activeOverlays).map(ov => (
                <Badge key={ov} variant="secondary" className="bg-primary/10 text-primary border-primary/20 text-[10px] px-2 py-0.5 whitespace-nowrap">
                  {ov}
                </Badge>
              ))}
            </div>
          </PageSection>
        </div>

        {/* Sidebar: Real-time Analysis */}
        <div className="space-y-6">
          <PageSection title="Vibration Levels" icon={<BarChart3 className="w-5 h-5 text-blue-500" />}>
            <div className="space-y-3">
              <div className="flex justify-between text-sm py-2 px-3 border border-destructive/20 bg-destructive/5 rounded-lg">
                <span className="text-muted-foreground">180° Major</span>
                <span className="text-destructive font-mono font-bold">${(currentPrice * 1.05).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm py-2 px-3 border border-border/50 bg-secondary/20 rounded-lg">
                <span className="text-muted-foreground">90° Cardinal</span>
                <span className="text-foreground font-mono font-bold">${(currentPrice * 1.025).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm py-3 px-3 bg-primary/10 border border-primary/30 rounded-lg font-bold shadow-[0_0_15px_rgba(0,120,255,0.1)]">
                <span className="text-primary">Current Price</span>
                <span className="text-primary font-mono">${currentPrice.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm py-2 px-3 border border-success/20 bg-success/5 rounded-lg">
                <span className="text-muted-foreground">45° Minor</span>
                <span className="text-success font-mono font-bold">${(currentPrice * 0.985).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm py-2 px-3 border border-success/20 bg-success/5 rounded-lg">
                <span className="text-muted-foreground">0° Origin</span>
                <span className="text-success font-mono font-bold">${(currentPrice * 0.95).toFixed(2)}</span>
              </div>
            </div>
          </PageSection>

          <PageSection title="Time Confluences" icon={<Clock className="w-5 h-5 text-orange-500" />}>
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-gradient-to-br from-orange-500/10 to-transparent border border-orange-500/20 relative overflow-hidden group">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] text-orange-400 uppercase font-black tracking-tighter">Reversal Window</span>
                  <Badge variant="outline" className="text-[9px] bg-orange-500/20 text-orange-400 border-orange-500/30">94.2% Conf.</Badge>
                </div>
                <p className="text-2xl font-black text-foreground tracking-tight">FEB 18, 2026</p>
                <p className="text-[10px] text-muted-foreground mt-1 font-medium">360-Year + Astro Jupiter</p>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2.5 rounded-lg bg-secondary/40 border border-border/50 hover:border-primary/30 transition-colors">
                  <span className="text-xs text-muted-foreground">Mars Retrograde Peak</span>
                  <span className="text-xs text-foreground font-bold">14d Remaining</span>
                </div>
                <div className="flex justify-between items-center p-2.5 rounded-lg bg-secondary/40 border border-border/50 hover:border-primary/30 transition-colors">
                  <span className="text-xs text-muted-foreground">Lunar Node Vibration</span>
                  <span className="text-xs text-foreground font-bold">3d Match</span>
                </div>
              </div>
            </div>
          </PageSection>
        </div>
      </div>

      {/* Bottom Controls: Gann & Ehlers */}
      <div className="space-y-6">
        <PageSection title="WD Gann Core Modules" icon={<Zap className="w-5 h-5 text-accent" />}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 p-4 bg-secondary/10 rounded-2xl border border-border/30 shadow-inner">
            {/* Waves Selection */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 border-b border-border pb-2">
                <TrendingUp className="w-4 h-4 text-accent" />
                <p className="text-xs font-black text-accent uppercase tracking-widest pl-1">Wave Patterns</p>
              </div>
              <div className="space-y-1.5">
                {["Gann Wave", "Elliott Wave"].map((name) => (
                  <div
                    key={name}
                    onClick={() => toggleOverlay(name)}
                    className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${activeOverlays.has(name) ? "bg-accent/20 border-accent/40 border-2 shadow-[0_0_10px_rgba(255,170,0,0.1)]" : "bg-card border border-border/50 hover:bg-secondary/50"}`}
                  >
                    <span className={`text-sm ${activeOverlays.has(name) ? "text-foreground font-bold" : "text-muted-foreground"}`}>{name}</span>
                    <div className={`w-2.5 h-2.5 rounded-full ${activeOverlays.has(name) ? "bg-accent animate-pulse shadow-[0_0_8px_rgba(255,170,0,1)]" : "bg-muted"}`} />
                  </div>
                ))}
              </div>
            </div>

            {/* Angles Grid */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 border-b border-border pb-2">
                <Activity className="w-4 h-4 text-primary" />
                <p className="text-xs font-black text-primary uppercase tracking-widest pl-1">Gann Angles Grid</p>
              </div>
              <div className="grid grid-cols-4 gap-1.5">
                {gannAngles.map(angle => (
                  <div
                    key={angle}
                    onClick={() => toggleOverlay(`Gann Angles ${angle}`)}
                    className={`p-2 rounded-lg text-xs font-mono font-bold text-center cursor-pointer border transition-all ${activeOverlays.has(`Gann Angles ${angle}`) ? "bg-primary border-primary text-primary-foreground shadow-[0_0_10px_rgba(0,120,255,0.3)]" : "bg-card border-border/50 hover:border-primary/50 text-muted-foreground hover:text-foreground"}`}
                  >
                    {angle}
                  </div>
                ))}
              </div>
            </div>

            {/* Gann Squares */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 border-b border-border pb-2">
                <Monitor className="w-4 h-4 text-blue-400" />
                <p className="text-xs font-black text-blue-400 uppercase tracking-widest pl-1">Gann Squares</p>
              </div>
              <div className="space-y-1.5">
                {["Gann Square 24.52", "Gann Square 90", "Gann Square 360", "Gann Square of 9"].map((name) => (
                  <div
                    key={name}
                    onClick={() => toggleOverlay(name)}
                    className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${activeOverlays.has(name) ? "bg-blue-500/20 border-blue-500/40 border-2 shadow-[0_0_10px_rgba(59,130,246,0.1)]" : "bg-card border border-border/50 hover:bg-secondary/50"}`}
                  >
                    <span className={`text-sm ${activeOverlays.has(name) ? "text-foreground font-bold" : "text-muted-foreground"}`}>{name}</span>
                    <div className={`w-2.5 h-2.5 rounded-full ${activeOverlays.has(name) ? "bg-blue-500 animate-pulse shadow-[0_0_8px_rgba(59,130,246,1)]" : "bg-muted"}`} />
                  </div>
                ))}
              </div>
            </div>

            {/* Specialized Tools */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 border-b border-border pb-2">
                <Smartphone className="w-4 h-4 text-purple-400" />
                <p className="text-xs font-black text-purple-400 uppercase tracking-widest pl-1">Specialized & Astro</p>
              </div>
              <div className="space-y-1.5">
                {["Gann Box", "Gann Fan", "Gann Astrology"].map((name) => (
                  <div
                    key={name}
                    onClick={() => toggleOverlay(name)}
                    className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${activeOverlays.has(name) ? "bg-purple-500/20 border-purple-500/40 border-2 shadow-[0_0_10px_rgba(168,85,247,0.1)]" : "bg-card border border-border/50 hover:bg-secondary/50"}`}
                  >
                    <span className={`text-sm ${activeOverlays.has(name) ? "text-foreground font-bold" : "text-muted-foreground"}`}>{name}</span>
                    <div className={`w-2.5 h-2.5 rounded-full ${activeOverlays.has(name) ? "bg-purple-500 animate-pulse shadow-[0_0_8px_rgba(168,85,247,1)]" : "bg-muted"}`} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </PageSection>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PageSection title="John F. Ehlers DSP Indicator Set" icon={<Activity className="w-5 h-5 text-primary" />}>
            <div className="grid grid-cols-2 gap-3 p-4 bg-secondary/10 rounded-2xl border border-border/30 max-h-[300px] overflow-y-auto custom-scrollbar">
              {ehlersOverlays.map((name) => (
                <div
                  key={name}
                  onClick={() => toggleOverlay(name)}
                  className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${activeOverlays.has(name) ? "bg-primary/20 border-primary/40 border-2 shadow-[0_0_10px_rgba(0,120,255,0.1)]" : "bg-card border border-border/50 hover:bg-secondary/50"}`}
                >
                  <span className={`text-xs ${activeOverlays.has(name) ? "text-foreground font-bold" : "text-muted-foreground"}`}>{name}</span>
                  <div className={`w-2 h-2 rounded-full ${activeOverlays.has(name) ? "bg-primary animate-pulse shadow-[0_0_8px_rgba(0,120,255,1)]" : "bg-muted"}`} />
                </div>
              ))}
            </div>
          </PageSection>

          <PageSection title="DSP Signal Matrix" icon={<Zap className="w-5 h-5 text-primary" />}>
            <div className="space-y-6 p-4 bg-secondary/10 rounded-2xl border border-border/30 h-full flex flex-col justify-center">
              <div>
                <div className="flex justify-between mb-2 items-end">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Signal Smoothing</span>
                  <span className="text-sm font-black text-primary">92% Fidelity</span>
                </div>
                <div className="h-2 bg-background rounded-full overflow-hidden border border-border/50">
                  <div className="h-full bg-primary w-[92%] shadow-[0_0_12px_rgba(10,120,255,0.6)]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2 items-end">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Cycle Amplitude</span>
                  <span className="text-sm font-black text-accent">Strong</span>
                </div>
                <div className="h-2 bg-background rounded-full overflow-hidden border border-border/50">
                  <div className="h-full bg-accent w-[78%] shadow-[0_0_12px_rgba(255,170,0,0.6)]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2 items-end">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Geometric Convergence</span>
                  <span className="text-sm font-black text-success">Equilibrium</span>
                </div>
                <div className="h-2 bg-background rounded-full overflow-hidden border border-border/50">
                  <div className="h-full bg-success w-[85%] shadow-[0_0_12px_rgba(34,197,94,0.6)]" />
                </div>
              </div>
            </div>
          </PageSection>
        </div>
      </div>
    </div>
  );
};

export default Charts;
