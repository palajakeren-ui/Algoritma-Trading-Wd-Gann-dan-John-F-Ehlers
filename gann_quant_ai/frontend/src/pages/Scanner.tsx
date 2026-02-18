import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Search, Filter, Download, RefreshCw, Plus, Wifi, Target, TrendingUp, TrendingDown, Activity, Save, Settings } from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import useWebSocketPrice from "@/hooks/useWebSocketPrice";
import { PageSection } from "@/components/PageSection";
import apiService from "@/services/apiService";

const TIMEFRAMES = [
  "1m", "2m", "3m", "5m", "15m", "30m", "1h", "2h", "3h", "4h", "6h", "8h", "12h", "1d", "1w", "1M", "1Y"
];

const ASSET_TYPES = ["Forex", "Crypto", "Indices", "Commodity", "Stocks"];

interface SignalResult {
  id: string;
  symbol: string;
  asset: string;
  timeframe: string;
  signal: "BUY" | "SELL";
  strength: "STRONG" | "MEDIUM" | "WEAK";
  price: number;
  entryPrice: number;
  takeProfit1: number;
  takeProfit2: number;
  takeProfit3: number;
  stopLoss: number;
  riskReward: number;
  gann: number;
  astro: number;
  ehlers: number;
  ml: number;
  confluence: number;
}

const generateSignals = (basePrice: number): SignalResult[] => [
  {
    id: "1", symbol: "EURUSD", asset: "Forex", timeframe: "15m", signal: "BUY", strength: "STRONG",
    price: 1.0875, entryPrice: 1.0875, takeProfit1: 1.0895, takeProfit2: 1.0920, takeProfit3: 1.0950,
    stopLoss: 1.0850, riskReward: 2.8, gann: 85, astro: 72, ehlers: 78, ml: 82, confluence: 4,
  },
  {
    id: "2", symbol: "BTCUSDT", asset: "Crypto", timeframe: "1h", signal: "BUY", strength: "STRONG",
    price: basePrice, entryPrice: basePrice, takeProfit1: basePrice * 1.02, takeProfit2: basePrice * 1.04, takeProfit3: basePrice * 1.06,
    stopLoss: basePrice * 0.98, riskReward: 3.0, gann: 88, astro: 90, ehlers: 75, ml: 85, confluence: 4,
  },
  {
    id: "3", symbol: "XAUUSD", asset: "Commodity", timeframe: "4h", signal: "SELL", strength: "MEDIUM",
    price: 2045.30, entryPrice: 2045.30, takeProfit1: 2030, takeProfit2: 2015, takeProfit3: 2000,
    stopLoss: 2060, riskReward: 2.1, gann: 45, astro: 38, ehlers: 62, ml: 55, confluence: 2,
  },
  {
    id: "4", symbol: "GBPJPY", asset: "Forex", timeframe: "5m", signal: "BUY", strength: "MEDIUM",
    price: 184.52, entryPrice: 184.52, takeProfit1: 185.00, takeProfit2: 185.50, takeProfit3: 186.00,
    stopLoss: 184.00, riskReward: 2.85, gann: 68, astro: 72, ehlers: 65, ml: 70, confluence: 3,
  },
  {
    id: "5", symbol: "US500", asset: "Indices", timeframe: "1d", signal: "BUY", strength: "WEAK",
    price: 4782.50, entryPrice: 4782.50, takeProfit1: 4820, takeProfit2: 4860, takeProfit3: 4900,
    stopLoss: 4740, riskReward: 2.76, gann: 55, astro: 48, ehlers: 58, ml: 62, confluence: 2,
  },
  {
    id: "6", symbol: "ETHUSDT", asset: "Crypto", timeframe: "30m", signal: "BUY", strength: "STRONG",
    price: 2450.75, entryPrice: 2450.75, takeProfit1: 2500, takeProfit2: 2550, takeProfit3: 2600,
    stopLoss: 2400, riskReward: 2.94, gann: 78, astro: 82, ehlers: 75, ml: 80, confluence: 4,
  },
  {
    id: "7", symbol: "USDJPY", asset: "Forex", timeframe: "1h", signal: "SELL", strength: "MEDIUM",
    price: 149.85, entryPrice: 149.85, takeProfit1: 149.30, takeProfit2: 148.80, takeProfit3: 148.30,
    stopLoss: 150.40, riskReward: 2.82, gann: 42, astro: 55, ehlers: 48, ml: 52, confluence: 2,
  },
];

const Scanner = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>(["1h"]);
  const [selectedAssets, setSelectedAssets] = useState<string[]>(["Forex", "Crypto"]);
  const [customSymbol, setCustomSymbol] = useState("");
  const [customTimeframe, setCustomTimeframe] = useState("");
  const [riskRewardMode, setRiskRewardMode] = useState<"dynamic" | "fixed">("dynamic");
  const [fixedRR, setFixedRR] = useState(2.0);
  const [tpMultiplier, setTpMultiplier] = useState(1.5);
  const [isScanning, setIsScanning] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const { priceData, isConnected, isLive, toggleConnection } = useWebSocketPrice({
    symbol: "BTCUSDT",
    enabled: true,
    updateInterval: 2000,
  });

  const [results, setResults] = useState<SignalResult[]>(() => generateSignals(47500));

  // Load scanner config from backend on mount
  useEffect(() => {
    const loadScannerConfig = async () => {
      try {
        const config = await apiService.getScannerConfig();
        if (config) {
          if (config.timeframes) setSelectedTimeframes(config.timeframes);
          if (config.assetTypes) setSelectedAssets(config.assetTypes);
          if (config.riskRewardMode) setRiskRewardMode(config.riskRewardMode);
          if (config.fixedRR) setFixedRR(config.fixedRR);
          if (config.tpMultiplier) setTpMultiplier(config.tpMultiplier);
          toast.success("Scanner config loaded from backend");
        }
      } catch (error) {
        console.error("Failed to load scanner config:", error);
        // Use default values
      }
    };
    loadScannerConfig();
  }, []);

  // Save scanner config to backend
  const saveScannerConfig = async () => {
    setIsSaving(true);
    try {
      await apiService.updateScannerConfig({
        timeframes: selectedTimeframes,
        assetTypes: selectedAssets,
        riskRewardMode,
        fixedRR,
        tpMultiplier,
        minConfluence: 3,
        signalStrength: "all"
      });
      toast.success("Scanner config saved to backend!");
    } catch (error) {
      console.error("Failed to save scanner config:", error);
      toast.error("Failed to save config. Saved locally.");
      // Save locally as fallback
      localStorage.setItem("scannerConfig", JSON.stringify({
        timeframes: selectedTimeframes,
        assetTypes: selectedAssets,
        riskRewardMode,
        fixedRR,
        tpMultiplier
      }));
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    if (isLive) {
      setResults(generateSignals(priceData.price));
    }
  }, [priceData.price, isLive]);

  const filteredResults = results.filter(result => {
    const matchesSearch = result.symbol.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTimeframe = selectedTimeframes.length === 0 || selectedTimeframes.includes(result.timeframe);
    const matchesAsset = selectedAssets.length === 0 || selectedAssets.includes(result.asset);
    return matchesSearch && matchesTimeframe && matchesAsset;
  });

  const handleTimeframeToggle = (tf: string) => {
    setIsScanning(true);
    setSelectedTimeframes(prev => {
      const isSelected = prev.includes(tf);
      if (isSelected) {
        return prev.filter(t => t !== tf);
      } else {
        return [...prev, tf];
      }
    });

    // Simulate scan update
    setTimeout(() => {
      setIsScanning(false);
      toast.success(`Scanner updated for ${tf}`);
    }, 800);
  };

  const handleAllTimeframes = () => {
    setIsScanning(true);
    if (selectedTimeframes.length === TIMEFRAMES.length) {
      setSelectedTimeframes([]);
    } else {
      setSelectedTimeframes([...TIMEFRAMES]);
    }

    setTimeout(() => {
      setIsScanning(false);
      toast.success(selectedTimeframes.length === TIMEFRAMES.length ? "Filters cleared" : "All timeframes selected");
    }, 1000);
  };

  const toggleAsset = (asset: string) => {
    setSelectedAssets(prev =>
      prev.includes(asset)
        ? prev.filter(a => a !== asset)
        : [...prev, asset]
    );
  };

  const handleAddCustomSymbol = () => {
    if (!customSymbol.trim()) return;
    const newSignal: SignalResult = {
      id: Date.now().toString(),
      symbol: customSymbol.toUpperCase(),
      asset: "Custom",
      timeframe: customTimeframe || "1H",
      signal: Math.random() > 0.5 ? "BUY" : "SELL",
      strength: "MEDIUM",
      price: 100,
      entryPrice: 100,
      takeProfit1: 102,
      takeProfit2: 104,
      takeProfit3: 106,
      stopLoss: 98,
      riskReward: 2.0,
      gann: Math.round(Math.random() * 30 + 50),
      astro: Math.round(Math.random() * 30 + 50),
      ehlers: Math.round(Math.random() * 30 + 50),
      ml: Math.round(Math.random() * 30 + 50),
      confluence: Math.round(Math.random() * 3 + 2),
    };
    setResults([newSignal, ...results]);
    setCustomSymbol("");
    setCustomTimeframe("");
    toast.success(`Added ${customSymbol.toUpperCase()} to scanner`);
  };

  const handleDownloadSignals = () => {
    const csvContent = [
      ["Symbol", "Asset", "Timeframe", "Signal", "Strength", "Entry", "TP1", "TP2", "TP3", "SL", "R:R", "Gann", "Astro", "Ehlers", "ML", "Confluence"].join(","),
      ...filteredResults.map(r =>
        [r.symbol, r.asset, r.timeframe, r.signal, r.strength, r.entryPrice, r.takeProfit1, r.takeProfit2, r.takeProfit3, r.stopLoss, r.riskReward.toFixed(2), r.gann, r.astro, r.ehlers, r.ml, r.confluence].join(",")
      )
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gann-signals-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Signals exported successfully!");
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Market Scanner</h1>
          <p className="text-muted-foreground">Multi-asset opportunity detector with TP/SL calculations</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={isConnected ? "border-success text-success" : "border-destructive text-destructive"}>
            <Wifi className="w-3 h-3 mr-1" />
            {isConnected ? "Live" : "Offline"}
          </Badge>
          <Button variant="outline" size="sm" onClick={toggleConnection}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isLive ? 'animate-spin' : ''}`} />
            {isLive ? "Pause" : "Resume"}
          </Button>
          <Button variant="outline" size="sm" onClick={saveScannerConfig} disabled={isSaving}>
            <Save className={`w-4 h-4 mr-2 ${isSaving ? 'animate-pulse' : ''}`} />
            {isSaving ? "Saving..." : "Save Config"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadSignals}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters & Manual Input */}
      <PageSection
        title="Scanner Filters & Manual Input"
        icon={<Filter className="w-5 h-5" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search symbols..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="lg:col-span-2">
            <Label className="text-sm font-medium mb-2 block">Multi-Asset Selection</Label>
            <div className="flex flex-wrap gap-2">
              <Badge
                variant={selectedAssets.length === 0 ? "default" : "outline"}
                className="cursor-pointer px-4 py-1.5"
                onClick={() => setSelectedAssets([])}
              >
                All Assets
              </Badge>
              {ASSET_TYPES.map(asset => (
                <Badge
                  key={asset}
                  variant={selectedAssets.includes(asset) ? "default" : "outline"}
                  className="cursor-pointer px-4 py-1.5"
                  onClick={() => toggleAsset(asset)}
                >
                  {asset}
                </Badge>
              ))}
            </div>
          </div>
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <Label className="text-xs text-muted-foreground mb-1 block">Quick Add Symbol</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g. BTCUSDT"
                  value={customSymbol}
                  onChange={(e) => setCustomSymbol(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={handleAddCustomSymbol} size="icon">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Timeframe scanner buttons */}
        <div className="mb-4">
          <Label className="text-sm font-medium mb-3 block flex items-center gap-2">
            <Target className="w-4 h-4 text-primary" />
            Scanner by Timeframe (1m - 1Y)
          </Label>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={selectedTimeframes.length === TIMEFRAMES.length ? "default" : "outline"}
              size="sm"
              className="min-w-[64px] h-9 font-bold"
              onClick={handleAllTimeframes}
              disabled={isScanning}
            >
              ALL
            </Button>
            {TIMEFRAMES.map(tf => (
              <Button
                key={tf}
                variant={selectedTimeframes.includes(tf) ? "default" : "outline"}
                size="sm"
                className={`min-w-[64px] h-9 font-mono transition-all ${selectedTimeframes.includes(tf) ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''}`}
                onClick={() => handleTimeframeToggle(tf)}
                disabled={isScanning}
              >
                {tf}
              </Button>
            ))}
          </div>
        </div>

        {/* Risk/Reward Settings */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-secondary/30 rounded-lg">
          <div className="flex items-center gap-2">
            <Label className="text-sm text-foreground">R:R Mode:</Label>
            <select
              className="px-3 py-1 bg-input border border-border rounded text-foreground text-sm"
              value={riskRewardMode}
              onChange={(e) => setRiskRewardMode(e.target.value as "dynamic" | "fixed")}
            >
              <option value="dynamic">Dynamic</option>
              <option value="fixed">Fixed</option>
            </select>
          </div>
          {riskRewardMode === "fixed" && (
            <div className="flex items-center gap-2">
              <Label className="text-sm text-foreground">Fixed R:R:</Label>
              <Input
                type="number"
                value={fixedRR}
                onChange={(e) => setFixedRR(parseFloat(e.target.value))}
                className="w-20"
                step="0.1"
              />
            </div>
          )}
          <div className="flex items-center gap-2">
            <Label className="text-sm text-foreground">TP Multiplier:</Label>
            <Input
              type="number"
              value={tpMultiplier}
              onChange={(e) => setTpMultiplier(parseFloat(e.target.value))}
              className="w-20"
              step="0.1"
            />
          </div>
        </div>
      </PageSection>

      <PageSection
        title={`Scan Results (${filteredResults.length})`}
        icon={<Activity className="w-5 h-5" />}
        headerAction={
          isScanning && (
            <Badge variant="outline" className="animate-pulse bg-primary/10 text-primary border-primary/20">
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
              Scanning...
            </Badge>
          )
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1200px]">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-2 text-sm font-semibold text-muted-foreground">Symbol</th>
                <th className="text-left py-3 px-2 text-sm font-semibold text-muted-foreground">TF</th>
                <th className="text-left py-3 px-2 text-sm font-semibold text-muted-foreground">Signal</th>
                <th className="text-right py-3 px-2 text-sm font-semibold text-muted-foreground">Entry</th>
                <th className="text-right py-3 px-2 text-sm font-semibold text-muted-foreground">
                  <Target className="w-4 h-4 inline mr-1" />TP1
                </th>
                <th className="text-right py-3 px-2 text-sm font-semibold text-muted-foreground">TP2</th>
                <th className="text-right py-3 px-2 text-sm font-semibold text-muted-foreground">TP3</th>
                <th className="text-right py-3 px-2 text-sm font-semibold text-muted-foreground">SL</th>
                <th className="text-center py-3 px-2 text-sm font-semibold text-muted-foreground">R:R</th>
                <th className="text-center py-3 px-2 text-sm font-semibold text-muted-foreground">Gann</th>
                <th className="text-center py-3 px-2 text-sm font-semibold text-muted-foreground">Ehlers</th>
                <th className="text-center py-3 px-2 text-sm font-semibold text-muted-foreground">ML</th>
                <th className="text-center py-3 px-2 text-sm font-semibold text-muted-foreground">Confluence</th>
              </tr>
            </thead>
            <tbody>
              {filteredResults.map((result) => (
                <tr key={result.id} className="border-b border-border hover:bg-secondary/50 transition-colors">
                  <td className="py-4 px-2">
                    <div>
                      <span className="font-semibold text-foreground">{result.symbol}</span>
                      <Badge variant="outline" className="ml-2 text-xs">{result.asset}</Badge>
                    </div>
                  </td>
                  <td className="py-4 px-2">
                    <Badge variant="secondary" className="font-mono text-xs">{result.timeframe}</Badge>
                  </td>
                  <td className="py-4 px-2">
                    <div className="flex items-center gap-2">
                      <Badge variant={result.signal === "BUY" ? "default" : "destructive"} className={result.signal === "BUY" ? "bg-success" : ""}>
                        {result.signal === "BUY" ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {result.signal}
                      </Badge>
                      <Badge variant="outline" className={
                        result.strength === "STRONG" ? "border-success text-success" :
                          result.strength === "MEDIUM" ? "border-accent text-accent" : "border-muted-foreground text-muted-foreground"
                      }>
                        {result.strength}
                      </Badge>
                    </div>
                  </td>
                  <td className="py-4 px-2 text-right font-mono text-foreground">{result.entryPrice.toFixed(result.entryPrice > 100 ? 2 : 4)}</td>
                  <td className="py-4 px-2 text-right font-mono text-success">{result.takeProfit1.toFixed(result.takeProfit1 > 100 ? 2 : 4)}</td>
                  <td className="py-4 px-2 text-right font-mono text-success">{result.takeProfit2.toFixed(result.takeProfit2 > 100 ? 2 : 4)}</td>
                  <td className="py-4 px-2 text-right font-mono text-success">{result.takeProfit3.toFixed(result.takeProfit3 > 100 ? 2 : 4)}</td>
                  <td className="py-4 px-2 text-right font-mono text-destructive">{result.stopLoss.toFixed(result.stopLoss > 100 ? 2 : 4)}</td>
                  <td className="py-4 px-2 text-center">
                    <Badge variant="outline" className="border-primary text-primary font-mono">
                      1:{(riskRewardMode === "fixed" ? fixedRR : result.riskReward).toFixed(1)}
                    </Badge>
                  </td>
                  <td className="py-4 px-2 text-center">
                    <span className={`font-semibold ${result.gann > 70 ? "text-success" : "text-muted-foreground"}`}>{result.gann}%</span>
                  </td>
                  <td className="py-4 px-2 text-center">
                    <span className={`font-semibold ${result.ehlers > 70 ? "text-success" : "text-muted-foreground"}`}>{result.ehlers}%</span>
                  </td>
                  <td className="py-4 px-2 text-center">
                    <span className={`font-semibold ${result.ml > 70 ? "text-success" : "text-muted-foreground"}`}>{result.ml}%</span>
                  </td>
                  <td className="py-4 px-2 text-center">
                    <Badge variant="outline" className={
                      result.confluence >= 4 ? "border-success text-success" :
                        result.confluence >= 3 ? "border-accent text-accent" : "border-muted text-muted-foreground"
                    }>
                      {result.confluence}/5
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PageSection>
    </div>
  );
};

export default Scanner;
