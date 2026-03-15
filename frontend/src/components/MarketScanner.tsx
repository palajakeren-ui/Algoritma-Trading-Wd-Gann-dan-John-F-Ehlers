import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, TrendingDown, Search, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface ScannerSignal {
  symbol: string;
  timeframe: string;
  signal: "BUY" | "SELL";
  strength: "STRONG" | "MEDIUM" | "WEAK";
  price: number;
  change: number;
  strategies: string[];
}

const TIMEFRAMES = ["1M", "2M", "3M", "5M", "10M", "15M", "30M", "45M", "1H", "2H", "3H", "4H", "1D", "1W", "1MO"];

const mockSignals: ScannerSignal[] = [
  { symbol: "EURUSD", timeframe: "1H", signal: "BUY", strength: "STRONG", price: 1.0875, change: 0.42, strategies: ["Gann", "Ehlers", "ML"] },
  { symbol: "BTCUSDT", timeframe: "1D", signal: "BUY", strength: "STRONG", price: 43250.50, change: 2.15, strategies: ["Gann", "Astro", "ML"] },
  { symbol: "XAUUSD", timeframe: "15M", signal: "SELL", strength: "MEDIUM", price: 2045.30, change: -0.65, strategies: ["Ehlers", "Pattern"] },
  { symbol: "US500", timeframe: "4H", signal: "BUY", strength: "MEDIUM", price: 4782.50, change: 0.88, strategies: ["ML", "Options"] },
  { symbol: "GBPUSD", timeframe: "30M", signal: "BUY", strength: "WEAK", price: 1.2650, change: 0.25, strategies: ["Gann", "Ehlers"] },
  { symbol: "ETHUSD", timeframe: "2H", signal: "SELL", strength: "STRONG", price: 2450.75, change: -1.85, strategies: ["ML", "Astro"] },
  { symbol: "USDJPY", timeframe: "45M", signal: "BUY", strength: "MEDIUM", price: 149.85, change: 0.32, strategies: ["Gann", "Ehlers"] },
  { symbol: "AUDUSD", timeframe: "3M", signal: "SELL", strength: "WEAK", price: 0.6525, change: -0.18, strategies: ["Pattern"] },
  { symbol: "BNBUSD", timeframe: "10M", signal: "BUY", strength: "STRONG", price: 312.45, change: 1.45, strategies: ["ML", "Gann"] },
  { symbol: "XRPUSD", timeframe: "5M", signal: "BUY", strength: "MEDIUM", price: 0.6234, change: 0.95, strategies: ["Astro", "Ehlers"] },
];

export const MarketScanner = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredSignals = mockSignals.filter(signal => {
    const matchesTimeframe = selectedTimeframe === "ALL" || signal.timeframe === selectedTimeframe;
    const matchesSearch = signal.symbol.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTimeframe && matchesSearch;
  });

  return (
    <Card className="p-4 md:p-6 border-border bg-card">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-foreground">Market Scanner</h2>
          <Badge variant="outline" className="bg-success/10 text-success border-success/20">
            Live
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-2 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
            <Input 
              placeholder="Search symbol..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 w-40 h-8 text-sm"
            />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-1" />
            Filter
          </Button>
        </div>
      </div>

      {/* Timeframe selector */}
      <div className="mb-4 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          <Badge 
            variant={selectedTimeframe === "ALL" ? "default" : "outline"}
            className="cursor-pointer text-xs px-2 py-1"
            onClick={() => setSelectedTimeframe("ALL")}
          >
            ALL
          </Badge>
          {TIMEFRAMES.map((tf) => (
            <Badge
              key={tf}
              variant={selectedTimeframe === tf ? "default" : "outline"}
              className="cursor-pointer text-xs px-2 py-1"
              onClick={() => setSelectedTimeframe(tf)}
            >
              {tf}
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {filteredSignals.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">No signals found for selected filters</p>
        ) : (
          filteredSignals.map((signal, idx) => (
            <div
              key={idx}
              className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-secondary/50 border border-border hover:bg-secondary transition-colors gap-2"
            >
              <div className="flex items-center space-x-3">
                <div className="flex flex-col">
                  <span className="font-semibold text-foreground">{signal.symbol}</span>
                  <span className="text-xs text-muted-foreground">{signal.timeframe}</span>
                </div>
                
                <Badge
                  variant={signal.signal === "BUY" ? "default" : "destructive"}
                  className={signal.signal === "BUY" ? "bg-success" : ""}
                >
                  {signal.signal}
                </Badge>
                
                <Badge
                  variant="outline"
                  className={
                    signal.strength === "STRONG"
                      ? "border-success text-success"
                      : signal.strength === "MEDIUM"
                      ? "border-accent text-accent"
                      : "border-muted-foreground text-muted-foreground"
                  }
                >
                  {signal.strength}
                </Badge>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex flex-wrap gap-1">
                  {signal.strategies.map((strategy, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {strategy}
                    </Badge>
                  ))}
                </div>

                <div className="text-right">
                  <div className="font-mono text-sm text-foreground">{signal.price}</div>
                  <div
                    className={`text-xs flex items-center ${
                      signal.change > 0 ? "text-success" : "text-destructive"
                    }`}
                  >
                    {signal.change > 0 ? (
                      <TrendingUp className="w-3 h-3 mr-1" />
                    ) : (
                      <TrendingDown className="w-3 h-3 mr-1" />
                    )}
                    {Math.abs(signal.change)}%
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Timeframe legend */}
      <div className="mt-4 p-3 bg-secondary/30 rounded-lg">
        <p className="text-xs text-muted-foreground">
          <strong>Timeframes:</strong> 1M (1 min), 2M, 3M, 5M, 10M, 15M, 30M, 45M, 1H (1 hour), 2H, 3H, 4H, 1D (daily), 1W (weekly), 1MO (monthly)
        </p>
      </div>
    </Card>
  );
};
