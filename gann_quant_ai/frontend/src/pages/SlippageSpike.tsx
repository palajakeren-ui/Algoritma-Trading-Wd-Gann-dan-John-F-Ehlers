import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Settings2, Zap, AlertTriangle, TrendingUp, Activity, Shield, BarChart2, RefreshCw } from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";

const SlippageSpike = () => {
  // Slippage Settings
  const [slippageSettings, setSlippageSettings] = useState({
    autoSlippage: true,
    slippageValue: "0.5",
    maxSlippage: "2.0",
    slippageModel: "adaptive",
    marketImpact: true,
    liquidityAdjust: true,
    volatilityFactor: "1.5"
  });

  // Spike Detection Settings
  const [spikeSettings, setSpikeSettings] = useState({
    autoDetect: true,
    sensitivity: "medium",
    threshold: "3.0",
    filterSpikes: true,
    alertOnSpike: true,
    lookbackPeriod: "20",
    zScoreThreshold: "2.5",
    volumeSpike: true,
    priceSpike: true
  });

  // Recent Spike Events State (Real-time)
  const [spikeEvents, setSpikeEvents] = useState([
    { time: "2 hours ago", instrument: "BTC/USDT", type: "Price", magnitude: "+4.2%", action: "Filtered" },
    { time: "5 hours ago", instrument: "ETH/USDT", type: "Volume", magnitude: "3.5x avg", action: "Alert" },
    { time: "8 hours ago", instrument: "EUR/USD", type: "Price", magnitude: "-1.8%", action: "Filtered" },
  ]);

  // Real-time stats
  const [stats, setStats] = useState({
    currentSlippage: "0.35%",
    avgSlippage24h: "0.42%",
    maxSlippage24h: "1.2%",
    spikesDetected: 7,
    lastSpikeTime: "2 hours ago",
    filteredTrades: 12
  });

  // Real-time Spike Generator Simulation
  useEffect(() => {
    if (!spikeSettings.autoDetect) return;

    const intervalId = setInterval(() => {
      // Chance of generating a spike based on sensitivity
      const chance = spikeSettings.sensitivity === "low" ? 0.05 :
        spikeSettings.sensitivity === "medium" ? 0.1 :
          spikeSettings.sensitivity === "high" ? 0.2 : 0.4;

      if (Math.random() < chance) {
        const type = Math.random() > 0.5 ? "Price" : "Volume";
        const isPositive = Math.random() > 0.5;
        const magnitudeVal = (parseFloat(spikeSettings.threshold) + Math.random() * 2).toFixed(1);
        const magnitude = type === "Price"
          ? `${isPositive ? "+" : "-"}${magnitudeVal}%`
          : `${magnitudeVal}x avg`;

        const action = Math.random() > 0.5 ? "Filtered" : "Alert";
        const newEvent = {
          time: "Just now",
          instrument: "BTC/USDT",
          type,
          magnitude,
          action
        };

        setSpikeEvents(prev => [newEvent, ...prev.slice(0, 7)]);

        // Update Stats
        setStats(prev => ({
          ...prev,
          spikesDetected: prev.spikesDetected + 1,
          lastSpikeTime: "Just now",
          filteredTrades: action === "Filtered" ? prev.filteredTrades + 1 : prev.filteredTrades
        }));

        if (spikeSettings.alertOnSpike) {
          toast(type === "Price" ? "🚨 Price Spike Detected!" : "📊 Volume Surge Detected!", {
            description: `${newEvent.instrument}: ${magnitude} magnitude.`,
            action: {
              label: "View",
              onClick: () => console.log("Spike details", newEvent),
            },
          });
        }
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(intervalId);
  }, [spikeSettings, slippageSettings]);

  const runCalibration = () => {
    toast.success("Calibrating slippage model with recent market data...");
  };

  const testSpikeDetection = () => {
    toast.success("Running spike detection test on historical data...");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center">
            <Settings2 className="w-8 h-8 mr-3 text-primary" />
            Slippage & Spike Detection
          </h1>
          <p className="text-muted-foreground">Automatic slippage calculation and price spike detection</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={slippageSettings.autoSlippage || spikeSettings.autoDetect ? "default" : "outline"} className={slippageSettings.autoSlippage || spikeSettings.autoDetect ? "bg-success" : ""}>
            {slippageSettings.autoSlippage || spikeSettings.autoDetect ? "System Active" : "System Paused"}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const newState = !(slippageSettings.autoSlippage && spikeSettings.autoDetect);
              setSlippageSettings(prev => ({ ...prev, autoSlippage: newState }));
              setSpikeSettings(prev => ({ ...prev, autoDetect: newState }));
              toast.success(newState ? "All systems enabled" : "All systems disabled");
            }}
          >
            {slippageSettings.autoSlippage && spikeSettings.autoDetect ? "Disable All" : "Enable All"}
          </Button>
        </div>
      </div>

      {/* Real-time Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Current Slippage</p>
          <p className="text-xl font-bold text-primary">{stats.currentSlippage}</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Avg Slippage (24h)</p>
          <p className="text-xl font-bold text-foreground">{stats.avgSlippage24h}</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Max Slippage (24h)</p>
          <p className="text-xl font-bold text-warning">{stats.maxSlippage24h}</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Spikes Detected</p>
          <p className="text-xl font-bold text-destructive">{stats.spikesDetected}</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Last Spike</p>
          <p className="text-xl font-bold text-foreground">{stats.lastSpikeTime}</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Filtered Trades</p>
          <p className="text-xl font-bold text-success">{stats.filteredTrades}</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Auto Slippage Card */}
        <Card className="p-6 border-border bg-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground flex items-center">
              <Zap className="w-5 h-5 mr-2 text-primary" />
              Automatic Slippage
            </h2>
            <Button variant="outline" size="sm" onClick={runCalibration}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Calibrate
            </Button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground">Auto Slippage Calculation</Label>
                <p className="text-xs text-muted-foreground">Automatically calculate slippage based on market conditions</p>
              </div>
              <Switch
                checked={slippageSettings.autoSlippage}
                onCheckedChange={(checked) => setSlippageSettings(prev => ({ ...prev, autoSlippage: checked }))}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-foreground text-sm">Base Slippage (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={slippageSettings.slippageValue}
                  onChange={(e) => setSlippageSettings(prev => ({ ...prev, slippageValue: e.target.value }))}
                  disabled={slippageSettings.autoSlippage}
                  className="bg-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-foreground text-sm">Max Slippage (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={slippageSettings.maxSlippage}
                  onChange={(e) => setSlippageSettings(prev => ({ ...prev, maxSlippage: e.target.value }))}
                  className="bg-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-foreground text-sm">Slippage Model</Label>
              <select
                value={slippageSettings.slippageModel}
                onChange={(e) => {
                  const val = e.target.value;
                  let updates = { slippageModel: val };

                  if (val === "fixed") {
                    updates = { ...updates, volatilityFactor: "1.0", marketImpact: false, liquidityAdjust: false };
                  } else if (val === "adaptive") {
                    updates = { ...updates, volatilityFactor: "1.5", marketImpact: true, liquidityAdjust: false };
                  } else if (val === "volume") {
                    updates = { ...updates, volatilityFactor: "1.2", marketImpact: false, liquidityAdjust: true };
                  } else if (val === "realistic") {
                    updates = { ...updates, volatilityFactor: "2.0", marketImpact: true, liquidityAdjust: true };
                  } else if (val === "tiered") {
                    updates = { ...updates, volatilityFactor: "1.8", marketImpact: true, liquidityAdjust: true };
                  }

                  setSlippageSettings(prev => ({ ...prev, ...updates }));
                  toast.info(`Slippage profile updated to ${val} model`);
                }}
                className="w-full px-4 py-2 bg-card border border-border rounded-md text-foreground"
              >
                <option value="fixed">Fixed - Constant slippage</option>
                <option value="adaptive">Adaptive - Based on volatility</option>
                <option value="volume">Volume-based - Considers liquidity</option>
                <option value="realistic">Realistic - Market impact model</option>
                <option value="tiered">Tiered - Size-dependent</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label className="text-foreground text-sm">Volatility Factor</Label>
              <Input
                type="number"
                step="0.1"
                value={slippageSettings.volatilityFactor}
                onChange={(e) => setSlippageSettings(prev => ({ ...prev, volatilityFactor: e.target.value }))}
                className="bg-input"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground text-sm">Market Impact Adjustment</Label>
                <p className="text-xs text-muted-foreground">Consider order size impact on price</p>
              </div>
              <Switch
                checked={slippageSettings.marketImpact}
                onCheckedChange={(checked) => setSlippageSettings(prev => ({ ...prev, marketImpact: checked }))}
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground text-sm">Liquidity Adjustment</Label>
                <p className="text-xs text-muted-foreground">Adjust based on order book depth</p>
              </div>
              <Switch
                checked={slippageSettings.liquidityAdjust}
                onCheckedChange={(checked) => setSlippageSettings(prev => ({ ...prev, liquidityAdjust: checked }))}
              />
            </div>

            <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
              <div className="flex items-center gap-2 text-primary mb-2">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm font-medium">Current Estimated Slippage</span>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {slippageSettings.autoSlippage ? stats.currentSlippage : `${slippageSettings.slippageValue}%`}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Model: {slippageSettings.slippageModel} | Factor: {slippageSettings.volatilityFactor}x
              </p>
            </div>
          </div>
        </Card>

        {/* Auto Spike Detection Card */}
        <Card className="p-6 border-border bg-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2 text-warning" />
              Spike Detection
            </h2>
            <Button variant="outline" size="sm" onClick={testSpikeDetection}>
              <Activity className="w-4 h-4 mr-2" />
              Test
            </Button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground">Auto Spike Detection</Label>
                <p className="text-xs text-muted-foreground">Automatically detect price spikes and anomalies</p>
              </div>
              <Switch
                checked={spikeSettings.autoDetect}
                onCheckedChange={(checked) => setSpikeSettings(prev => ({ ...prev, autoDetect: checked }))}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-foreground text-sm">Sensitivity</Label>
                <select
                  value={spikeSettings.sensitivity}
                  onChange={(e) => {
                    const val = e.target.value;
                    let updates = { sensitivity: val };

                    if (val === "low") {
                      updates = { ...updates, threshold: "5.0", lookbackPeriod: "10", zScoreThreshold: "4.0" };
                    } else if (val === "medium") {
                      updates = { ...updates, threshold: "3.0", lookbackPeriod: "20", zScoreThreshold: "2.5" };
                    } else if (val === "high") {
                      updates = { ...updates, threshold: "2.0", lookbackPeriod: "30", zScoreThreshold: "1.8" };
                    } else if (val === "ultra") {
                      updates = { ...updates, threshold: "1.0", lookbackPeriod: "50", zScoreThreshold: "1.2" };
                    }

                    setSpikeSettings(prev => ({ ...prev, ...updates }));
                    toast.info(`Spike detection calibrated to ${val} sensitivity`);
                  }}
                  className="w-full px-4 py-2 bg-card border border-border rounded-md text-foreground"
                  disabled={!spikeSettings.autoDetect}
                >
                  <option value="low">Low - Major spikes only</option>
                  <option value="medium">Medium - Balanced</option>
                  <option value="high">High - All anomalies</option>
                  <option value="ultra">Ultra - Micro movements</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label className="text-foreground text-sm">Threshold (σ)</Label>
                <Input
                  type="number"
                  step="0.5"
                  value={spikeSettings.threshold}
                  onChange={(e) => setSpikeSettings(prev => ({ ...prev, threshold: e.target.value }))}
                  disabled={!spikeSettings.autoDetect}
                  className="bg-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-foreground text-sm">Lookback Period</Label>
                <Input
                  type="number"
                  value={spikeSettings.lookbackPeriod}
                  onChange={(e) => setSpikeSettings(prev => ({ ...prev, lookbackPeriod: e.target.value }))}
                  disabled={!spikeSettings.autoDetect}
                  className="bg-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-foreground text-sm">Z-Score Threshold</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={spikeSettings.zScoreThreshold}
                  onChange={(e) => setSpikeSettings(prev => ({ ...prev, zScoreThreshold: e.target.value }))}
                  disabled={!spikeSettings.autoDetect}
                  className="bg-input"
                />
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground text-sm">Price Spike Detection</Label>
                <p className="text-xs text-muted-foreground">Detect abnormal price movements</p>
              </div>
              <Switch
                checked={spikeSettings.priceSpike}
                onCheckedChange={(checked) => setSpikeSettings(prev => ({ ...prev, priceSpike: checked }))}
                disabled={!spikeSettings.autoDetect}
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground text-sm">Volume Spike Detection</Label>
                <p className="text-xs text-muted-foreground">Detect abnormal volume spikes</p>
              </div>
              <Switch
                checked={spikeSettings.volumeSpike}
                onCheckedChange={(checked) => setSpikeSettings(prev => ({ ...prev, volumeSpike: checked }))}
                disabled={!spikeSettings.autoDetect}
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground text-sm">Filter Spikes from Trading</Label>
                <p className="text-xs text-muted-foreground">Exclude detected spikes from execution</p>
              </div>
              <Switch
                checked={spikeSettings.filterSpikes}
                onCheckedChange={(checked) => setSpikeSettings(prev => ({ ...prev, filterSpikes: checked }))}
                disabled={!spikeSettings.autoDetect}
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div>
                <Label className="text-foreground text-sm">Alert on Spike</Label>
                <p className="text-xs text-muted-foreground">Show notification when spike detected</p>
              </div>
              <Switch
                checked={spikeSettings.alertOnSpike}
                onCheckedChange={(checked) => setSpikeSettings(prev => ({ ...prev, alertOnSpike: checked }))}
                disabled={!spikeSettings.autoDetect}
              />
            </div>

            <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
              <div className="flex items-center gap-2 text-warning mb-2">
                <Shield className="w-4 h-4" />
                <span className="text-sm font-medium">Spike Detection Status</span>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {spikeSettings.autoDetect ? "Active" : "Disabled"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {spikeSettings.autoDetect
                  ? `Sensitivity: ${spikeSettings.sensitivity} | Threshold: ${spikeSettings.threshold}σ | Z-Score: ${spikeSettings.zScoreThreshold}`
                  : "Enable to detect price anomalies"}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Spike Events */}
      <Card className="p-6 border-border bg-card">
        <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center">
          <BarChart2 className="w-5 h-5 mr-2" />
          Recent Spike Events
        </h2>
        <div className="space-y-2">
          {spikeEvents.map((event, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
              <div className="flex items-center gap-4">
                <span className="text-xs text-muted-foreground w-24">{event.time}</span>
                <span className="text-sm font-medium text-foreground w-24">{event.instrument}</span>
                <Badge variant="outline" className={event.type === "Price" ? "bg-primary/10 text-primary" : "bg-warning/10 text-warning"}>
                  {event.type}
                </Badge>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-sm font-semibold ${event.magnitude.includes("-") ? "text-destructive" : "text-success"}`}>
                  {event.magnitude}
                </span>
                <Badge variant={event.action === "Filtered" ? "destructive" : "default"} className="w-20 justify-center">
                  {event.action}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default SlippageSpike;
