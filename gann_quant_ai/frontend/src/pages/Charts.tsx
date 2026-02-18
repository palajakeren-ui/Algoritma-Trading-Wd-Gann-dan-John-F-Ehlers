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
    "Gann Square of 9", "Gann Angles 1x1", "MAMA (John F. Ehlers)"
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

  const gannOverlays = [
    "Gann Square of 9",
    "Gann Angles 1x1",
    "Gann Angles 2x1",
    "Gann Angles 3x1",
    "Gann Box (Geometric)",
    "Gann Wheel (Hexagon)",
    "Square of 144 Spiral",
    "Square of 90 Harmonic",
    "Planetary Vibration Lines"
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
    "Smoothed RSI"
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-foreground">Advanced Financial Charts</h1>
            <Badge variant="outline" className="hidden md:flex gap-1 border-primary/50 text-primary">
              <Zap className="w-3 h-3" /> Professional
            </Badge>
          </div>
          <p className="text-muted-foreground">Synchronized Data Feed: {activeSymbol} via {currentMarketData.source}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={isConnected ? "border-success text-success" : "border-destructive text-destructive"}>
            <Wifi className="w-3 h-3 mr-1" />
            {isConnected ? "Live Feed Active" : "Wait for Connection..."}
          </Badge>
          <div className="flex items-center space-x-1 border rounded-lg p-1 bg-background/50">
            <Button variant="ghost" size="icon" className="h-8 w-8"><ZoomOut className="w-4 h-4" /></Button>
            <Button variant="ghost" size="icon" className="h-8 w-8"><ZoomIn className="h-8 w-8" /></Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
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
            <div className="bg-card rounded-xl border border-border p-1">
              <CandlestickChart data={currentCandles} height={isMobile ? 350 : 550} showGannAngles={activeOverlays.has("Gann Angles 1x1")} />
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground mr-2">Active Analysis:</span>
              {Array.from(activeOverlays).slice(0, 5).map(ov => (
                <Badge key={ov} variant="secondary" className="bg-primary/10 text-primary border-primary/20 text-[10px]">
                  {ov}
                </Badge>
              ))}
              {activeOverlays.size > 5 && <span className="text-[10px] text-muted-foreground">+{activeOverlays.size - 5} more</span>}
            </div>
          </PageSection>
        </div>

        <div className="space-y-4">
          <PageSection title="WD Gann Modules" icon={<Zap className="w-5 h-5 text-accent" />}>
            <div className="space-y-1.5 max-h-[250px] overflow-y-auto pr-2 scrollbar-hide">
              {gannOverlays.map((name) => (
                <div
                  key={name}
                  onClick={() => toggleOverlay(name)}
                  className={`flex items-center justify-between p-2 rounded cursor-pointer transition-all ${activeOverlays.has(name) ? "bg-accent/20 border-accent/30 border" : "bg-secondary/30 border border-transparent hover:bg-secondary/50"}`}
                >
                  <span className={`text-xs ${activeOverlays.has(name) ? "text-foreground font-semibold" : "text-muted-foreground"}`}>{name}</span>
                  <div className={`w-1.5 h-1.5 rounded-full ${activeOverlays.has(name) ? "bg-accent animate-pulse shadow-[0_0_8px_rgba(255,170,0,0.8)]" : "bg-muted"}`} />
                </div>
              ))}
            </div>
          </PageSection>

          <PageSection title="John F. Ehlers DSP" icon={<Activity className="w-5 h-5 text-primary" />}>
            <div className="space-y-1.5 max-h-[250px] overflow-y-auto pr-2 scrollbar-hide">
              {ehlersOverlays.map((name) => (
                <div
                  key={name}
                  onClick={() => toggleOverlay(name)}
                  className={`flex items-center justify-between p-2 rounded cursor-pointer transition-all ${activeOverlays.has(name) ? "bg-primary/20 border-primary/30 border" : "bg-secondary/30 border border-transparent hover:bg-secondary/50"}`}
                >
                  <span className={`text-xs ${activeOverlays.has(name) ? "text-foreground font-semibold" : "text-muted-foreground"}`}>{name}</span>
                  <div className={`w-1.5 h-1.5 rounded-full ${activeOverlays.has(name) ? "bg-primary animate-pulse shadow-[0_0_8px_rgba(0,120,255,0.8)]" : "bg-muted"}`} />
                </div>
              ))}
            </div>
          </PageSection>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <PageSection title="Vibration Levels" icon={<BarChart3 className="w-5 h-5" />}>
          <div className="space-y-2">
            <div className="flex justify-between text-sm py-1 border-b border-border/30">
              <span className="text-muted-foreground">180° Major Resistance</span>
              <span className="text-destructive font-mono font-bold">${(currentPrice * 1.05).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm py-1 border-b border-border/30">
              <span className="text-muted-foreground">90° Cardinal Level</span>
              <span className="text-foreground font-mono font-bold">${(currentPrice * 1.025).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm py-2 bg-primary/5 px-2 rounded font-bold">
              <span className="text-primary">Current Price</span>
              <span className="text-primary font-mono">${currentPrice.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm py-1 border-b border-border/30">
              <span className="text-muted-foreground">45° Minor Support</span>
              <span className="text-success font-mono font-bold">${(currentPrice * 0.985).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm py-1 border-b border-border/30">
              <span className="text-muted-foreground">0° Cycle Origin</span>
              <span className="text-success font-mono font-bold">${(currentPrice * 0.95).toFixed(2)}</span>
            </div>
          </div>
        </PageSection>

        <PageSection title="Time Confluences" icon={<Clock className="w-5 h-5" />}>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-accent/10 border border-accent/20 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-100 transition-opacity">
                <Zap className="w-4 h-4 text-accent" />
              </div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-muted-foreground uppercase font-semibold">Critical Reversal Window</span>
                <Badge variant="outline" className="text-[10px] bg-accent/20 text-accent border-accent/30">94% Confidence</Badge>
              </div>
              <p className="text-xl font-black text-foreground">FEB 18, 2026</p>
              <p className="text-[10px] text-muted-foreground mt-1">Gann 360-Year Cycle + Astro Jupiter Confluence</p>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-secondary/30">
                <span className="text-muted-foreground">Mars Retrograde Peak</span>
                <span className="text-foreground font-semibold">14 Days Remaining</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-secondary/30">
                <span className="text-muted-foreground">Lunar Node Vibration</span>
                <span className="text-foreground font-semibold">Match in 3 Days</span>
              </div>
            </div>
          </div>
        </PageSection>

        <PageSection title="DSP Signal Matrix" icon={<Zap className="w-5 h-5 text-primary" />}>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1.5 items-end">
                <span className="text-xs text-muted-foreground">Signal Smoothing (Ehlers)</span>
                <span className="text-sm font-bold text-primary">High Fidelity</span>
              </div>
              <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-primary w-[92%] shadow-[0_0_8px_rgba(0,120,255,0.5)]" />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1.5 items-end">
                <span className="text-xs text-muted-foreground">Cycle Amplitude</span>
                <span className="text-sm font-bold text-accent">Strong</span>
              </div>
              <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-accent w-[78%] shadow-[0_0_8px_rgba(255,170,0,0.5)]" />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1.5 items-end">
                <span className="text-xs text-muted-foreground">Gann Geometric Convergence</span>
                <span className="text-sm font-bold text-success">Equilibrium</span>
              </div>
              <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-success w-[85%] shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
              </div>
            </div>
          </div>
        </PageSection>
      </div>
    </div>
  );
};

export default Charts;
