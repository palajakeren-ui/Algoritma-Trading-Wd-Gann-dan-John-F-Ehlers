import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Target, TrendingUp, TrendingDown, ArrowRightLeft, Layers, Activity, Search, RefreshCw } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import apiService from "@/services/apiService";

interface OptionChainData {
  strike: number;
  callBid: number;
  callAsk: number;
  callIV: string;
  callVol: number;
  putBid: number;
  putAsk: number;
  putIV: string;
  putVol: number;
}

interface OptionsAnalysis {
  symbol: string;
  spotPrice: number;
  expiryDays: number;
  call: {
    price: number;
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
    iv: number;
    moneyness: string;
  };
  put: {
    price: number;
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
    iv: number;
    moneyness: string;
  };
  volatility: {
    current: number;
    percentile: number;
  };
}

const defaultOptionChainData: OptionChainData[] = [
  { strike: 1.0700, callBid: 0.1250, callAsk: 0.1265, callIV: "24.5%", callVol: 450, putBid: 0.0010, putAsk: 0.0015, putIV: "32.1%", putVol: 12 },
  { strike: 1.0750, callBid: 0.0820, callAsk: 0.0835, callIV: "23.8%", callVol: 890, putBid: 0.0025, putAsk: 0.0035, putIV: "30.5%", putVol: 45 },
  { strike: 1.0800, callBid: 0.0450, callAsk: 0.0465, callIV: "22.1%", callVol: 1240, putBid: 0.0080, putAsk: 0.0095, putIV: "28.4%", putVol: 156 },
  { strike: 1.0850, callBid: 0.0210, callAsk: 0.0225, callIV: "21.5%", callVol: 3400, putBid: 0.0240, putAsk: 0.0255, putIV: "27.2%", putVol: 870 },
  { strike: 1.0900, callBid: 0.0085, callAsk: 0.0095, callIV: "20.8%", callVol: 1800, putBid: 0.0520, putAsk: 0.0535, putIV: "26.5%", putVol: 1100 },
  { strike: 1.0950, callBid: 0.0035, callAsk: 0.0045, callIV: "21.2%", callVol: 720, putBid: 0.0910, putAsk: 0.0925, putIV: "27.8%", putVol: 650 },
  { strike: 1.1000, callBid: 0.0015, callAsk: 0.0020, callIV: "22.4%", callVol: 240, putBid: 0.1350, putAsk: 0.1365, putIV: "29.1%", putVol: 140 },
];

const Options = () => {
  const [symbol, setSymbol] = useState("BTC");
  const [spotPrice, setSpotPrice] = useState(50000);
  const [expiryDays, setExpiryDays] = useState(30);
  const [isLoading, setIsLoading] = useState(false);
  const [optionChainData, setOptionChainData] = useState<OptionChainData[]>(defaultOptionChainData);
  const [analysis, setAnalysis] = useState<OptionsAnalysis | null>(null);
  
  // Greeks state
  const [greeksData, setGreeksData] = useState([
    { name: "Delta", value: "0.58", desc: "Directional exposure" },
    { name: "Gamma", value: "0.032", desc: "Delta sensitivity" },
    { name: "Theta", value: "-0.015", desc: "Time decay" },
    { name: "Vega", value: "0.125", desc: "Volatility sensitivity" },
  ]);

  // Implied volatility state
  const [impliedVol, setImpliedVol] = useState({ value: 28.5, status: "Elevated" });
  const [putCallRatio, setPutCallRatio] = useState({ value: 0.85, status: "Bullish" });

  const fetchOptionsAnalysis = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.getOptionsAnalysis({
        symbol,
        expiryDays,
      });
      
      setAnalysis(result);
      
      // Update Greeks from API response
      if (result.call) {
        setGreeksData([
          { name: "Delta", value: result.call.delta?.toFixed(4) || "0.58", desc: "Directional exposure" },
          { name: "Gamma", value: result.call.gamma?.toFixed(4) || "0.032", desc: "Delta sensitivity" },
          { name: "Theta", value: result.call.theta?.toFixed(4) || "-0.015", desc: "Time decay" },
          { name: "Vega", value: result.call.vega?.toFixed(4) || "0.125", desc: "Volatility sensitivity" },
        ]);
      }

      // Update IV
      if (result.volatility) {
        const iv = result.volatility.current * 100;
        setImpliedVol({
          value: iv,
          status: iv > 50 ? "High" : iv > 30 ? "Elevated" : "Normal"
        });
      }

      toast.success(`Options analysis loaded for ${symbol}`);
    } catch (error) {
      console.error("Options analysis error:", error);
      toast.error("Failed to fetch options analysis. Using mock data.");
    } finally {
      setIsLoading(false);
    }
  };

  const calculateGreeks = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.calculateOptionsGreeks({
        spotPrice,
        strikePrice: spotPrice, // ATM
        timeToExpiry: expiryDays,
        volatility: impliedVol.value / 100,
        riskFreeRate: 0.05,
        optionType: "call"
      });

      if (result.greeks) {
        setGreeksData([
          { name: "Delta", value: result.greeks.delta?.toFixed(4) || "0.50", desc: "Directional exposure" },
          { name: "Gamma", value: result.greeks.gamma?.toFixed(4) || "0.032", desc: "Delta sensitivity" },
          { name: "Theta", value: result.greeks.theta?.toFixed(4) || "-0.015", desc: "Time decay" },
          { name: "Vega", value: result.greeks.vega?.toFixed(4) || "0.125", desc: "Volatility sensitivity" },
        ]);
        toast.success("Greeks calculated successfully");
      }
    } catch (error) {
      console.error("Greeks calculation error:", error);
      toast.error("Failed to calculate Greeks");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchOptionsAnalysis();
  }, []);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center">
            <Target className="w-8 h-8 mr-3 text-accent" />
            Options Analysis
          </h1>
          <p className="text-muted-foreground">Greeks, volatility surface & flow analysis</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input 
              className="pl-9 w-[200px] h-9" 
              placeholder="Ticker (e.g. BTC)"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            />
          </div>
          <Input
            type="number"
            className="w-[120px] h-9"
            placeholder="Spot Price"
            value={spotPrice}
            onChange={(e) => setSpotPrice(parseFloat(e.target.value))}
          />
          <Button 
            onClick={fetchOptionsAnalysis} 
            disabled={isLoading}
            size="sm"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Analyze
          </Button>
          <Badge variant="outline" className="h-9 px-4 border-accent text-accent">Real-time Feed</Badge>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 border-border bg-card hover:bg-accent/5 transition-colors group cursor-default">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center justify-between">
            Implied Volatility
            <Activity className="w-4 h-4 text-warning opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          <p className="text-2xl font-bold text-foreground">{impliedVol.value.toFixed(1)}%</p>
          <Badge variant="outline" className={`mt-2 ${
            impliedVol.status === "High" ? "bg-destructive/10 text-destructive border-destructive/20" :
            impliedVol.status === "Elevated" ? "bg-warning/10 text-warning border-warning/20" :
            "bg-success/10 text-success border-success/20"
          }`}>
            {impliedVol.status}
          </Badge>
        </Card>

        <Card className="p-6 border-border bg-card hover:bg-accent/5 transition-colors group cursor-default">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">Put/Call Ratio</h3>
          <p className="text-2xl font-bold text-foreground">{putCallRatio.value}</p>
          <Badge variant="outline" className={`mt-2 ${
            putCallRatio.status === "Bullish" ? "bg-success/10 text-success border-success/20" :
            "bg-destructive/10 text-destructive border-destructive/20"
          }`}>
            {putCallRatio.status}
          </Badge>
        </Card>

        <Card className="p-6 border-border bg-card hover:bg-accent/5 transition-colors group cursor-default">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">Options Flow</h3>
          <p className="text-2xl font-bold text-foreground">Positive</p>
          <div className="mt-2 flex items-center text-success">
            <TrendingUp className="w-4 h-4 mr-1" />
            <span className="text-sm">$2.4M calls</span>
          </div>
        </Card>

        <Card className="p-6 border-border bg-card hover:bg-accent/5 transition-colors group cursor-default">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">Max Pain</h3>
          <p className="text-2xl font-bold text-foreground">{analysis?.spotPrice ? (analysis.spotPrice * 0.98).toFixed(0) : "1.0850"}</p>
          <Badge variant="outline" className="mt-2">Near Current</Badge>
        </Card>
      </div>

      {/* Main Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 border-border bg-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
              <Layers className="w-5 h-5 text-accent" /> Greeks Overview
            </h2>
            <Button size="sm" variant="outline" onClick={calculateGreeks} disabled={isLoading}>
              <RefreshCw className={`w-3 h-3 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Calculate
            </Button>
          </div>
          <div className="space-y-4">
            {greeksData.map((greek, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors border border-border/50">
                <div>
                  <p className="font-semibold text-foreground">{greek.name}</p>
                  <p className="text-xs text-muted-foreground">{greek.desc}</p>
                </div>
                <span className="text-lg font-mono font-bold text-foreground">{greek.value}</span>
              </div>
            ))}
          </div>
          
          {/* Call/Put pricing from API */}
          {analysis && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-success/10 rounded-lg">
                  <p className="text-xs text-muted-foreground">Call Price</p>
                  <p className="text-lg font-bold text-success">${analysis.call?.price?.toFixed(2) || "N/A"}</p>
                </div>
                <div className="p-3 bg-destructive/10 rounded-lg">
                  <p className="text-xs text-muted-foreground">Put Price</p>
                  <p className="text-lg font-bold text-destructive">${analysis.put?.price?.toFixed(2) || "N/A"}</p>
                </div>
              </div>
            </div>
          )}
        </Card>

        <Card className="p-6 border-border bg-card">
          <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-success" /> Unusual Activity
          </h2>
          <div className="space-y-3">
            {[
              { symbol: "EURUSD", type: "Call", strike: 1.09, volume: 1250, sentiment: "Bullish" },
              { symbol: "BTCUSDT", type: "Call", strike: 45000, volume: 850, sentiment: "Bullish" },
              { symbol: "XAUUSD", type: "Put", strike: 2000, volume: 680, sentiment: "Bearish" },
            ].map((activity, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-secondary/30 border border-border hover:border-accent/50 transition-all cursor-pointer">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-foreground">{activity.symbol}</span>
                    <Badge variant="outline" className="text-[10px]">{activity.type}</Badge>
                  </div>
                  <Badge
                    variant={activity.sentiment === "Bullish" ? "default" : "destructive"}
                    className={activity.sentiment === "Bullish" ? "bg-success hover:bg-success/90" : ""}
                  >
                    {activity.sentiment}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Strike: {activity.strike}</span>
                  <span className="text-foreground font-mono">{activity.volume} contracts</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Options Orderbook (Option Chain) */}
      <Card className="border-border bg-card overflow-hidden">
        <div className="p-6 border-b border-border flex flex-col md:flex-row md:items-center justify-between gap-4 bg-accent/5">
          <div>
            <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
              <ArrowRightLeft className="w-5 h-5 text-accent" /> Options Orderbook
            </h2>
            <p className="text-xs text-muted-foreground">Real-time liquidity & strike depth</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-success/20 text-success border-success/30">CALLS</Badge>
            <div className="w-8 h-[1px] bg-border" />
            <Badge variant="outline" className="border-border text-muted-foreground">STRIKE</Badge>
            <div className="w-8 h-[1px] bg-border" />
            <Badge className="bg-destructive/20 text-destructive border-destructive/30">PUTS</Badge>
          </div>
        </div>

        <ScrollArea className="h-[500px] w-full">
          <Table>
            <TableHeader className="sticky top-0 bg-card z-10 shadow-sm">
              <TableRow className="border-b border-border hover:bg-transparent">
                <TableHead className="text-center font-bold text-success border-r bg-success/5">Vol</TableHead>
                <TableHead className="text-center font-bold text-success border-r bg-success/5">IV</TableHead>
                <TableHead className="text-center font-bold text-success border-r bg-success/5">Bid</TableHead>
                <TableHead className="text-center font-bold text-success border-r bg-success/5">Ask</TableHead>
                <TableHead className="text-center font-bold text-accent bg-accent/10 min-w-[120px]">STRIKE</TableHead>
                <TableHead className="text-center font-bold text-destructive border-l bg-destructive/5">Bid</TableHead>
                <TableHead className="text-center font-bold text-destructive border-l bg-destructive/5">Ask</TableHead>
                <TableHead className="text-center font-bold text-destructive border-l bg-destructive/5">IV</TableHead>
                <TableHead className="text-center font-bold text-destructive border-l bg-destructive/5">Vol</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {optionChainData.map((row, idx) => (
                <TableRow key={idx} className="hover:bg-accent/5 transition-colors border-b border-border/50 lg:h-12">
                  {/* Calls Side */}
                  <TableCell className="text-center font-mono text-[11px] text-muted-foreground border-r">{row.callVol}</TableCell>
                  <TableCell className="text-center font-mono text-[11px] text-muted-foreground border-r">{row.callIV}</TableCell>
                  <TableCell className="text-center font-mono text-xs text-success font-semibold border-r">{row.callBid}</TableCell>
                  <TableCell className="text-center font-mono text-xs text-success font-semibold border-r">{row.callAsk}</TableCell>

                  {/* Strike Column */}
                  <TableCell className="text-center font-bold bg-secondary/20 text-foreground scale-105 shadow-inner">
                    {row.strike.toFixed(4)}
                  </TableCell>

                  {/* Puts Side */}
                  <TableCell className="text-center font-mono text-xs text-destructive font-semibold border-l">{row.putBid}</TableCell>
                  <TableCell className="text-center font-mono text-xs text-destructive font-semibold border-l">{row.putAsk}</TableCell>
                  <TableCell className="text-center font-mono text-[11px] text-muted-foreground border-l">{row.putIV}</TableCell>
                  <TableCell className="text-center font-mono text-[11px] text-muted-foreground border-l">{row.putVol}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
        <div className="p-4 bg-secondary/20 border-t border-border flex justify-between items-center">
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Data feed: Backend API / Options Engine</p>
          <div className="flex gap-4">
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-success animate-pulse" /> <span className="text-[10px] text-muted-foreground">Connected</span></div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-accent" /> <span className="text-[10px] text-muted-foreground">Latency: 24ms</span></div>
          </div>
        </div>
      </Card>

      <Card className="p-6 border-border bg-card">
        <h2 className="text-xl font-semibold text-foreground mb-4">Volatility Surface</h2>
        <div className="bg-secondary/30 rounded-lg h-[300px] flex items-center justify-center border border-border group relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-accent/10 to-transparent pointer-events-none" />
          <div className="text-center space-y-4 z-10 transition-transform group-hover:scale-105 duration-500">
            <Target className="w-16 h-16 text-muted-foreground mx-auto" />
            <div>
              <p className="text-lg font-semibold text-foreground">IV Surface Chart</p>
              <p className="text-sm text-muted-foreground">
                3D visualization of implied volatility across strikes and maturities
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Options;
