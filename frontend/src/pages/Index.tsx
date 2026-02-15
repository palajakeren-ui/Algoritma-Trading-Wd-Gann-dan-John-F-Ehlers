import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, Activity, DollarSign, Percent, Layers, RefreshCw, Wifi, Shield, Zap, Smartphone, Monitor } from "lucide-react";
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart } from "recharts";
import { GannSquareChart } from "@/components/charts/GannSquareChart";
import { GannWheelChart } from "@/components/charts/GannWheelChart";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { GannCalculator } from "@/components/calculators/GannCalculator";
import { GannFanChart } from "@/components/charts/GannFanChart";
import { GannBoxChart } from "@/components/charts/GannBoxChart";
import { GannForecastingCalculator } from "@/components/calculators/GannForecastingCalculator";
import AstroCyclePanel from "@/components/dashboard/AstroCyclePanel";
import EhlersDSPPanel from "@/components/dashboard/EhlersDSPPanel";
import AIForecastPanel from "@/components/dashboard/AIForecastPanel";
import HexagonGeometryChart from "@/components/charts/HexagonGeometryChart";
import GannFanFullModule from "@/components/charts/GannFanFullModule";
import { Button } from "@/components/ui/button";
import TradingInstrumentSelector from "@/components/TradingInstrumentSelector";
import { PageSection } from "@/components/PageSection";
import { GannDashboardExtensions } from "@/components/dashboard/GannDashboardExtensions";
import { useIsMobile } from "@/hooks/use-mobile";
import { ActiveTradingPanel } from "@/components/trading/ActiveTradingPanel";
import Scanner from "./Scanner";


const generateMockPriceData = (basePrice: number) => Array.from({ length: 30 }, (_, i) => {
  const base = basePrice + Math.sin(i / 5) * (basePrice * 0.04);
  const date = new Date(2024, 9, 21 + i);
  return {
    date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    price: base + Math.random() * (basePrice * 0.02),
    volume: 800000 + Math.random() * 800000,
  };
});

const generateMockCandleData = (basePrice: number) => Array.from({ length: 30 }, (_, i) => {
  const base = basePrice + Math.sin(i / 5) * (basePrice * 0.04);
  const dateStr = new Date(2024, 0, i + 1).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return {
    time: dateStr,
    date: dateStr,
    open: base + Math.random() * (basePrice * 0.01),
    high: base + Math.random() * (basePrice * 0.03),
    low: base - Math.random() * (basePrice * 0.015),
    close: base + Math.random() * (basePrice * 0.01),
  };
});

import { useDataFeed } from "@/context/DataFeedContext";

const Index = () => {
  const isMobile = useIsMobile();
  const { marketData, candles, isConnected, subscribe } = useDataFeed();

  // Synchronization State
  const [activeSymbol, setActiveSymbol] = useState("BTC-USD");
  const [activeTimeframe, setActiveTimeframe] = useState("1d");

  // Subscribe to symbol on mount or change
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
  const priceChange = currentMarketData.change;
  const priceChangePercent = currentMarketData.changePercent;
  const lastUpdate = currentMarketData.timestamp;
  const dataSource = currentMarketData.source;

  const currentCandles = candles[activeSymbol] || [];

  return (
    <div className={`space-y-4 md:space-y-6 px-2 md:px-0 transition-all duration-300 ${isMobile ? 'pb-20' : ''}`}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6 rounded-2xl bg-gradient-to-br from-card via-card to-primary/5 border border-border/50 shadow-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-32 -mt-32 transition-colors group-hover:bg-primary/10" />

        <div className="flex items-center gap-6 relative z-10">
          <div className="w-24 h-24 md:w-32 md:h-32 rounded-2xl bg-black/40 p-3 border border-primary/20 shadow-[0_0_40px_rgba(var(--primary),0.2)] flex items-center justify-center">
            <img
              src="/Tanpa Judul.ico"
              alt="Cenayang Market Logo"
              className="w-full h-full object-contain"
              onError={(e) => { e.currentTarget.src = "/placeholder.svg"; }}
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl md:text-4xl font-black tracking-tighter text-foreground uppercase">
                Cenayang <span className="text-primary text-glow-primary">Market</span>
              </h1>
              <Badge variant="outline" className={`hidden md:flex gap-1 ml-2 border-primary/30 text-primary bg-primary/5`}>
                <Zap className="w-3 h-3 text-accent animate-pulse" />
                QUANTUM PRO
              </Badge>
            </div>
            <p className="text-sm md:text-lg text-muted-foreground font-medium flex items-center gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
              {activeSymbol} Neural-Gann Intelligence System
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap relative z-10">
          <Badge variant="outline" className={`border-border/50 bg-black/20 backdrop-blur-sm px-3 py-1`}>
            {isMobile ? <Smartphone className="w-3 h-3 mr-2" /> : <Monitor className="w-3 h-3 mr-2" />}
            {isMobile ? "Mobile Lite" : "Desktop High-Performance"}
          </Badge>
          <Badge variant="outline" className={isConnected ? "border-success/50 text-success bg-success/5" : "border-destructive/50 text-destructive bg-destructive/5"}>
            <Wifi className="w-3 h-3 mr-1" />
            {isConnected ? `Synced: ${dataSource}` : "Offline Mode"}
          </Badge>
          <Badge className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold shadow-lg shadow-primary/20 px-4">
            LIVE TRADING
          </Badge>
        </div>
      </div>


      <PageSection
        title="Live Market Status"
        icon={<Activity className="w-5 h-5" />}
      >
        <div className={`grid ${isMobile ? 'grid-cols-2 gap-2' : 'grid-cols-4 gap-4'}`}>
          <div className="space-y-1 p-2 md:p-0 rounded-lg md:rounded-none bg-accent/5 md:bg-transparent">
            <p className="text-xs md:text-sm text-muted-foreground">Account Balance</p>
            <p className="text-lg md:text-2xl font-bold text-foreground flex items-center">
              <DollarSign className="w-4 h-4 md:w-5 md:h-5 mr-1" />
              100,000
            </p>
          </div>
          <div className="space-y-1 p-2 md:p-0 rounded-lg md:rounded-none bg-accent/5 md:bg-transparent">
            <p className="text-xs md:text-sm text-muted-foreground">Risk/Trade</p>
            <p className="text-lg md:text-2xl font-bold text-foreground flex items-center">
              <Percent className="w-4 h-4 md:w-5 md:h-5 mr-1" />
              2%
            </p>
          </div>
          <div className="space-y-1 p-2 md:p-0 rounded-lg md:rounded-none bg-accent/5 md:bg-transparent">
            <p className="text-xs md:text-sm text-muted-foreground">Leverage</p>
            <p className="text-lg md:text-2xl font-bold text-foreground flex items-center">
              <Layers className="w-4 h-4 md:w-5 md:h-5 mr-1" />
              5x
            </p>
          </div>
          <div className="space-y-1 p-2 md:p-0 rounded-lg md:rounded-none bg-accent/5 md:bg-transparent">
            <p className="text-xs md:text-sm text-muted-foreground">Lot Size</p>
            <p className="text-lg md:text-2xl font-bold text-foreground">0.19</p>
          </div>
        </div>
        <p className="text-[10px] md:text-xs text-muted-foreground mt-3 md:mt-4">
          Last Update: {lastUpdate.toISOString().replace('T', ' ').split('.')[0]} UTC
        </p>
      </PageSection>

      <PageSection
        title="Gann Geometric Intelligence"
        icon={<Zap className="w-5 h-5 text-accent animate-pulse" />}
        headerAction={
          <Badge className="bg-primary/20 text-primary border-primary/30 flex items-center gap-1">
            <Activity className="w-3 h-3" />
            {!isMobile && "SYNCHRONIZED"}
          </Badge>
        }
      >
        <GannDashboardExtensions currentPrice={currentPrice} />
      </PageSection>

      <PageSection
        title="Active Trading - Buy/Sell Instruments"
        icon={<Activity className="w-5 h-5 text-success animate-pulse" />}
        headerAction={
          <Badge className="bg-success/20 text-success border-success/30 flex items-center gap-1">
            <Activity className="w-3 h-3" />
            {!isMobile && "TRADING ACTIVE"}
          </Badge>
        }
      >
        <ActiveTradingPanel currentPrice={currentPrice} />
      </PageSection>

      <PageSection
        title="Advanced Trading Charts"
        icon={<TrendingUp className="w-6 h-6" />}
        headerAction={
          <div className="text-right">
            <p className="text-xl md:text-2xl font-bold text-foreground">${currentPrice.toLocaleString()}</p>
            <p className={`text-xs md:text-sm flex items-center justify-end ${priceChange >= 0 ? 'text-success' : 'text-destructive'}`}>
              {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
            </p>
          </div>
        }
      >
        <Tabs value={activeTimeframe} onValueChange={setActiveTimeframe} className="w-full">
          <div className="mb-3 md:mb-4 overflow-x-auto scrollbar-hide">
            <TabsList className={`inline-flex ${isMobile ? 'h-9' : 'h-auto'} p-1 md:p-2 min-w-max`}>
              {["m1", "m2", "m3", "m5", "m10", "m15", "m30", "m45", "1h", "2h", "3h", "4h", "1d", "1w", "1mo", "1y"].map((tf) => (
                <TabsTrigger key={tf} value={tf} className="text-xs md:text-sm px-2 md:px-3 py-1 md:py-2">
                  {tf.toUpperCase()}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <div className="bg-card/50 rounded-xl border border-border/50 p-2 md:p-4">
            {["m1", "m2", "m3", "m5", "m10", "m15", "m30", "m45", "1h", "2h", "3h", "4h", "1d", "1w", "1mo", "1y"].map((tf) => (
              <TabsContent key={tf} value={tf} className="mt-0 focus-visible:outline-none">
                <CandlestickChart data={currentCandles} showGannAngles={true} height={isMobile ? 300 : 400} />
              </TabsContent>
            ))}
          </div>
        </Tabs>
      </PageSection>

      {/* Trading Instrument Selector */}
      <TradingInstrumentSelector onInstrumentChange={(sym) => { setActiveSymbol(sym); }} />

      {/* Astro Cycle Panel */}
      <AstroCyclePanel />

      {/* Ehlers DSP Multi-Timeframe & Multi-Instrument Analysis */}
      <EhlersDSPPanel currentSymbol={activeSymbol} currentPrice={currentPrice} currentTimeframe={activeTimeframe} />


      <Tabs defaultValue="overview" className="w-full">
        <div className="overflow-x-auto scrollbar-hide pb-2">
          <TabsList className={`inline-flex w-auto min-w-full md:grid md:w-full md:grid-cols-6 gap-1 ${isMobile ? 'justify-start' : ''}`}>
            <TabsTrigger value="overview" className="text-xs md:text-sm whitespace-nowrap px-4 md:px-3">Overview</TabsTrigger>
            <TabsTrigger value="calculations" className="text-xs md:text-sm whitespace-nowrap px-4 md:px-3">Calculations</TabsTrigger>
            <TabsTrigger value="analysis" className="text-xs md:text-sm whitespace-nowrap px-4 md:px-3">Analysis</TabsTrigger>
            <TabsTrigger value="forecasting" className="text-xs md:text-sm whitespace-nowrap px-4 md:px-3">Forecast</TabsTrigger>
            <TabsTrigger value="risk" className="text-xs md:text-sm whitespace-nowrap px-4 md:px-3">Risk</TabsTrigger>
            <TabsTrigger value="scanner" className="text-xs md:text-sm whitespace-nowrap px-4 md:px-3">Scanner</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="overview" className="mt-4">
          <PageSection title="Real-Time Market Overview" icon={<Activity className="w-5 h-5" />}>
            <div className={`grid ${isMobile ? 'grid-cols-2 gap-3' : 'grid-cols-4 gap-4'}`}>
              <div className="p-3 bg-secondary/50 rounded-lg border border-border/50">
                <p className="text-xs text-muted-foreground">Current Price</p>
                <p className="text-lg md:text-xl font-bold text-foreground">${currentPrice.toLocaleString()}</p>
              </div>
              <div className="p-3 bg-secondary/50 rounded-lg border border-border/50">
                <p className="text-xs text-muted-foreground">24h Change</p>
                <p className={`text-lg md:text-xl font-bold ${priceChange >= 0 ? 'text-success' : 'text-destructive'}`}>
                  {priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%
                </p>
              </div>
              <div className="p-3 bg-secondary/50 rounded-lg border border-border/50">
                <p className="text-xs text-muted-foreground">Gann Level</p>
                <p className="text-lg md:text-xl font-bold text-primary">90°</p>
              </div>
              <div className="p-3 bg-secondary/50 rounded-lg border border-border/50 flex flex-col justify-between">
                <p className="text-xs text-muted-foreground mb-1">Signal</p>
                <Badge className="bg-success w-fit">BULLISH</Badge>
              </div>
            </div>
          </PageSection>
        </TabsContent>

        <TabsContent value="calculations" className="space-y-4 mt-4">
          <h3 className="text-lg md:text-xl font-semibold text-foreground mb-3 md:mb-4">Live Calculation Engines (WebSocket: ${currentPrice.toLocaleString()})</h3>

          {/* Hexagon Geometry and Gann Fan Full Module */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
            <HexagonGeometryChart currentPrice={currentPrice} />
            <GannFanFullModule currentPrice={currentPrice} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
            <Card className="p-4 md:p-6 border-border bg-card">
              <h4 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-success" />
                WD Gann Angles Summary
              </h4>
              <div className="space-y-2 max-h-[350px] overflow-y-auto">
                {[
                  { angle: "0°", price: (currentPrice * 1.000).toFixed(2), type: "origin" },
                  { angle: "15°", price: (currentPrice * 0.996).toFixed(2), type: "minor" },
                  { angle: "30°", price: (currentPrice * 0.992).toFixed(2), type: "support" },
                  { angle: "45°", price: (currentPrice * 0.988).toFixed(2), type: "cardinal" },
                  { angle: "60°", price: (currentPrice * 0.982).toFixed(2), type: "support" },
                  { angle: "90°", price: (currentPrice * 0.975).toFixed(2), type: "major" },
                  { angle: "135°", price: (currentPrice * 1.012).toFixed(2), type: "resistance" },
                  { angle: "180°", price: (currentPrice * 1.025).toFixed(2), type: "pivot" },
                  { angle: "225°", price: (currentPrice * 1.038).toFixed(2), type: "resistance" },
                  { angle: "270°", price: (currentPrice * 1.050).toFixed(2), type: "major" },
                  { angle: "315°", price: (currentPrice * 0.962).toFixed(2), type: "support" },
                  { angle: "360°", price: (currentPrice * 0.950).toFixed(2), type: "cycle" },
                ].map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center p-2 bg-secondary/50 rounded">
                    <span className="text-sm font-bold text-accent">{item.angle}</span>
                    <span className="text-sm font-mono text-foreground">${item.price}</span>
                    <Badge variant="outline" className={item.type.includes("support") || item.type === "cardinal" ? "text-xs border-success text-success" : item.type === "origin" || item.type.includes("pivot") || item.type === "cycle" ? "text-xs border-primary text-primary" : item.type === "major" ? "text-xs border-accent text-accent" : "text-xs border-destructive text-destructive"}>
                      {item.type}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-4 md:p-6 border-border bg-card">
              <h4 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-accent" />
                Planetary
              </h4>
              <div className="space-y-4">
                <div>
                  <h5 className="text-sm font-semibold text-muted-foreground mb-2">Fibonacci Levels</h5>
                  <div className="space-y-2">
                    {[
                      { level: "0.0%", price: `$${(currentPrice * 0.95).toFixed(2)}` },
                      { level: "23.6%", price: `$${(currentPrice * 0.976).toFixed(2)}` },
                      { level: "38.2%", price: `$${(currentPrice * 0.982).toFixed(2)}` },
                      { level: "50.0%", price: `$${(currentPrice * 1.00).toFixed(2)}` },
                      { level: "61.8%", price: `$${(currentPrice * 1.018).toFixed(2)}` },
                      { level: "78.6%", price: `$${(currentPrice * 1.036).toFixed(2)}` },
                      { level: "100.0%", price: `$${(currentPrice * 1.05).toFixed(2)}` },
                    ].map((item, idx) => (
                      <div key={idx} className="flex justify-between items-center p-2 bg-secondary/50 rounded">
                        <span className="text-sm font-mono text-foreground">{item.level}</span>
                        <span className="text-sm font-bold text-accent">{item.price}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-4 md:p-6 border-border bg-card">
              <h4 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-chart-3" />
                Technical
              </h4>
              <div className="space-y-4">
                <div>
                  <h5 className="text-sm font-semibold text-muted-foreground mb-2">Time Cycles</h5>
                  <div className="space-y-2">
                    {[
                      { name: "Weekly", date: "27/11/2025", type: "Minor" },
                      { name: "Monthly", date: "20/12/2025", type: "Moderate" },
                      { name: "Quarterly", date: "18/2/2026", type: "Major" },
                      { name: "Fibonacci 144", date: "13/4/2026", type: "Major" },
                      { name: "Semi-Annual", date: "19/5/2026", type: "Major" },
                      { name: "Annual", date: "20/11/2026", type: "Critical" },
                    ].map((item, idx) => (
                      <div key={idx} className="p-2 bg-secondary/50 rounded space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-semibold text-foreground">{item.name}</span>
                          <Badge variant="outline" className="text-xs">{item.type}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{item.date}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4 mt-4">
          <h3 className="text-lg font-semibold text-foreground mb-4">WD Gann Analysis Tools (Real-Time: ${currentPrice.toLocaleString()})</h3>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
            <div className="lg:col-span-2 space-y-4 md:space-y-6">
              <CandlestickChart data={currentCandles} height={isMobile ? 300 : 500} />
              <GannBoxChart basePrice={currentPrice} />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                <GannSquareChart centerValue={currentPrice} />
                <GannWheelChart currentPrice={currentPrice} />
              </div>
              <GannFanChart />
            </div>
            <div>
              <GannCalculator />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="forecasting" className="space-y-4 mt-4">
          <h3 className="text-lg font-semibold text-foreground mb-4">AI-Powered WD Gann Forecasting (Real-Time)</h3>
          <AIForecastPanel currentPrice={currentPrice} />
          <div className="mt-6">
            <h4 className="text-lg font-semibold text-foreground mb-4">WD Gann Cycle Forecasting (Up to 365 Years)</h4>
            <GannForecastingCalculator />
          </div>
        </TabsContent>

        <TabsContent value="risk" className="mt-4">
          <PageSection title="Risk & Position Management" icon={<Shield className="w-5 h-5" />}>
            <div className={`grid ${isMobile ? 'grid-cols-1 gap-3' : 'grid-cols-4 gap-4'}`}>
              <div className="p-4 bg-secondary/50 rounded-lg border border-border/50 flex justify-between items-center md:block">
                <p className="text-xs text-muted-foreground md:mb-1">Position Size</p>
                <p className="text-xl md:text-2xl font-bold text-foreground">0.19 BTC</p>
              </div>
              <div className="p-4 bg-secondary/50 rounded-lg border border-border/50 flex justify-between items-center md:block">
                <p className="text-xs text-muted-foreground md:mb-1">Risk Amount</p>
                <p className="text-xl md:text-2xl font-bold text-destructive">$2,000</p>
              </div>
              <div className="p-4 bg-secondary/50 rounded-lg border border-border/50 flex justify-between items-center md:block">
                <p className="text-xs text-muted-foreground md:mb-1">Stop Loss</p>
                <p className="text-xl md:text-2xl font-bold text-destructive">${(currentPrice * 0.98).toFixed(2)}</p>
              </div>
              <div className="p-4 bg-secondary/50 rounded-lg border border-border/50 flex justify-between items-center md:block">
                <p className="text-xs text-muted-foreground md:mb-1">Take Profit</p>
                <p className="text-xl md:text-2xl font-bold text-success">${(currentPrice * 1.04).toFixed(2)}</p>
              </div>
            </div>
          </PageSection>
        </TabsContent>

        <TabsContent value="scanner" className="mt-4">
          <Scanner />
        </TabsContent>
      </Tabs>
    </div >
  );
};

export default Index;
