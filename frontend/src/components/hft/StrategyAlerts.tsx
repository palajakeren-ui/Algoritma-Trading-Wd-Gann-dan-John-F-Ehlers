import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Bell,
  BellRing,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Trash2,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  Clock,
  Activity,
  Zap,
  Target,
  Filter,
  Settings,
} from "lucide-react";
import { toast } from "sonner";

interface StrategyAlert {
  id: string;
  timestamp: Date;
  strategy: string;
  instrument: string;
  signal: "BUY" | "SELL" | "NEUTRAL" | "CAUTION";
  strength: number;
  price: number;
  message: string;
  acknowledged: boolean;
}

interface AlertSettings {
  enabled: boolean;
  soundEnabled: boolean;
  autoAcknowledge: boolean;
  minStrength: number;
  showBuy: boolean;
  showSell: boolean;
  showCaution: boolean;
}

interface StrategyAlertsProps {
  config: Record<string, any>;
  isRunning: boolean;
}

const MOCK_INSTRUMENTS = ["BTCUSDT", "ETHUSDT", "EURUSD", "XAUUSD", "US500"];

const GANN_STRATEGIES = [
  { name: "Square of 9", key: "useGannSquare9" },
  { name: "Gann Angles", key: "useGannAngles" },
  { name: "Time Cycles", key: "useGannTimeCycles" },
  { name: "Support/Resistance", key: "useGannSR" },
  { name: "Gann Fibonacci", key: "useGannFibo" },
  { name: "Gann Wave", key: "useGannWave" },
  { name: "Gann Hexagon", key: "useGannHexagon" },
];

const EHLERS_STRATEGIES = [
  { name: "MAMA/FAMA", key: "useEhlersMAMAFAMA" },
  { name: "Fisher Transform", key: "useEhlersFisher" },
  { name: "Bandpass Filter", key: "useEhlersBandpass" },
  { name: "Super Smoother", key: "useEhlersSuperSmoother" },
  { name: "Roofing Filter", key: "useEhlersRoofing" },
  { name: "Cyber Cycle", key: "useEhlersCyberCycle" },
  { name: "Decycler", key: "useEhlersDecycler" },
  { name: "Insta Trend", key: "useEhlersInstaTrend" },
  { name: "Dominant Cycle", key: "useEhlersDominantCycle" },
];

export const StrategyAlerts = ({ config, isRunning }: StrategyAlertsProps) => {
  const [alerts, setAlerts] = useState<StrategyAlert[]>([]);
  const [alertSettings, setAlertSettings] = useState<AlertSettings>({
    enabled: true,
    soundEnabled: true,
    autoAcknowledge: false,
    minStrength: 0.5,
    showBuy: true,
    showSell: true,
    showCaution: true,
  });
  const [filterStrategy, setFilterStrategy] = useState<string>("all");
  const [filterSignal, setFilterSignal] = useState<string>("all");

  const getActiveStrategies = useCallback(() => {
    const active: string[] = [];
    [...GANN_STRATEGIES, ...EHLERS_STRATEGIES].forEach((s) => {
      if (config[s.key]) active.push(s.name);
    });
    return active;
  }, [config]);

  const generateAlert = useCallback(() => {
    const activeStrategies = getActiveStrategies();
    if (activeStrategies.length === 0) return null;

    const strategy = activeStrategies[Math.floor(Math.random() * activeStrategies.length)];
    const instrument = MOCK_INSTRUMENTS[Math.floor(Math.random() * MOCK_INSTRUMENTS.length)];
    const signals: ("BUY" | "SELL" | "NEUTRAL" | "CAUTION")[] = ["BUY", "SELL", "NEUTRAL", "CAUTION"];
    const signal = signals[Math.floor(Math.random() * signals.length)];
    const strength = Math.random();

    const basePrice = {
      BTCUSDT: 47500,
      ETHUSDT: 2480,
      EURUSD: 1.0856,
      XAUUSD: 2045.5,
      US500: 5120,
    }[instrument] || 100;

    const price = basePrice * (1 + (Math.random() - 0.5) * 0.01);

    const messages = {
      BUY: [
        `${strategy} bullish signal detected`,
        `${strategy} indicates upward momentum`,
        `${strategy} buy zone confirmed`,
      ],
      SELL: [
        `${strategy} bearish signal detected`,
        `${strategy} indicates downward pressure`,
        `${strategy} sell zone confirmed`,
      ],
      NEUTRAL: [
        `${strategy} consolidation pattern`,
        `${strategy} waiting for confirmation`,
        `${strategy} no clear direction`,
      ],
      CAUTION: [
        `${strategy} divergence warning`,
        `${strategy} volatility spike detected`,
        `${strategy} risk level elevated`,
      ],
    };

    const message = messages[signal][Math.floor(Math.random() * 3)];

    return {
      id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      strategy,
      instrument,
      signal,
      strength,
      price,
      message,
      acknowledged: false,
    };
  }, [getActiveStrategies]);

  useEffect(() => {
    if (!isRunning || !alertSettings.enabled) return;

    const interval = setInterval(() => {
      const newAlert = generateAlert();
      if (newAlert && newAlert.strength >= alertSettings.minStrength) {
        // Filter based on signal type
        const shouldShow =
          (newAlert.signal === "BUY" && alertSettings.showBuy) ||
          (newAlert.signal === "SELL" && alertSettings.showSell) ||
          (newAlert.signal === "CAUTION" && alertSettings.showCaution) ||
          newAlert.signal === "NEUTRAL";

        if (shouldShow) {
          setAlerts((prev) => [newAlert, ...prev].slice(0, 100));

          if (alertSettings.soundEnabled && newAlert.signal !== "NEUTRAL") {
            // Play sound notification (browser notification)
            if (Notification.permission === "granted") {
              new Notification(`${newAlert.signal} Signal - ${newAlert.instrument}`, {
                body: newAlert.message,
                icon: "/favicon.ico",
              });
            }
            toast[newAlert.signal === "BUY" ? "success" : newAlert.signal === "SELL" ? "error" : "warning"](
              newAlert.message,
              { description: `${newAlert.instrument} @ ${newAlert.price.toFixed(4)}` }
            );
          }
        }
      }
    }, 2000 + Math.random() * 3000);

    return () => clearInterval(interval);
  }, [isRunning, alertSettings, generateAlert]);

  const acknowledgeAlert = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a))
    );
  };

  const clearAlerts = () => {
    setAlerts([]);
    toast.info("All alerts cleared");
  };

  const acknowledgeAll = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, acknowledged: true })));
    toast.success("All alerts acknowledged");
  };

  const requestNotificationPermission = () => {
    if ("Notification" in window) {
      Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          toast.success("Notifications enabled");
        }
      });
    }
  };

  const filteredAlerts = alerts.filter((alert) => {
    const strategyMatch = filterStrategy === "all" || alert.strategy === filterStrategy;
    const signalMatch = filterSignal === "all" || alert.signal === filterSignal;
    return strategyMatch && signalMatch;
  });

  const unacknowledgedCount = alerts.filter((a) => !a.acknowledged).length;

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "BUY":
        return "bg-success text-success-foreground";
      case "SELL":
        return "bg-destructive text-destructive-foreground";
      case "CAUTION":
        return "bg-accent text-accent-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case "BUY":
        return <TrendingUp className="w-4 h-4" />;
      case "SELL":
        return <TrendingDown className="w-4 h-4" />;
      case "CAUTION":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Alert Settings */}
      <Card className="p-4 border-border bg-card">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-foreground flex items-center gap-2">
            <Settings className="w-4 h-4 text-primary" />
            Alert Settings
          </h4>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={alertSettings.enabled ? "border-success text-success" : ""}>
              {alertSettings.enabled ? "Active" : "Disabled"}
            </Badge>
            {unacknowledgedCount > 0 && (
              <Badge className="bg-destructive">{unacknowledgedCount} New</Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center justify-between">
            <Label className="text-sm">Enable Alerts</Label>
            <Switch
              checked={alertSettings.enabled}
              onCheckedChange={(v) => setAlertSettings((prev) => ({ ...prev, enabled: v }))}
            />
          </div>
          <div className="flex items-center justify-between">
            <Label className="text-sm">Sound</Label>
            <Switch
              checked={alertSettings.soundEnabled}
              onCheckedChange={(v) => {
                setAlertSettings((prev) => ({ ...prev, soundEnabled: v }));
                if (v) requestNotificationPermission();
              }}
            />
          </div>
          <div className="flex items-center justify-between">
            <Label className="text-sm">Show Buy</Label>
            <Switch
              checked={alertSettings.showBuy}
              onCheckedChange={(v) => setAlertSettings((prev) => ({ ...prev, showBuy: v }))}
            />
          </div>
          <div className="flex items-center justify-between">
            <Label className="text-sm">Show Sell</Label>
            <Switch
              checked={alertSettings.showSell}
              onCheckedChange={(v) => setAlertSettings((prev) => ({ ...prev, showSell: v }))}
            />
          </div>
        </div>

        <div className="mt-4 flex items-center gap-4">
          <div className="flex-1">
            <Label className="text-xs text-muted-foreground mb-1 block">Min Signal Strength</Label>
            <Input
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={alertSettings.minStrength}
              onChange={(e) =>
                setAlertSettings((prev) => ({ ...prev, minStrength: parseFloat(e.target.value) }))
              }
              className="h-8"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={requestNotificationPermission}
          >
            <Bell className="w-4 h-4 mr-2" />
            Enable Notifications
          </Button>
        </div>
      </Card>

      {/* Alert Filters */}
      <Card className="p-4 border-border bg-card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <Label className="text-sm">Filter:</Label>
          </div>
          <select
            value={filterStrategy}
            onChange={(e) => setFilterStrategy(e.target.value)}
            className="h-8 px-2 rounded border border-border bg-background text-sm"
          >
            <option value="all">All Strategies</option>
            {getActiveStrategies().map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select
            value={filterSignal}
            onChange={(e) => setFilterSignal(e.target.value)}
            className="h-8 px-2 rounded border border-border bg-background text-sm"
          >
            <option value="all">All Signals</option>
            <option value="BUY">Buy</option>
            <option value="SELL">Sell</option>
            <option value="CAUTION">Caution</option>
            <option value="NEUTRAL">Neutral</option>
          </select>
          <div className="flex-1" />
          <Button size="sm" variant="outline" onClick={acknowledgeAll}>
            <CheckCircle2 className="w-4 h-4 mr-1" />
            Ack All
          </Button>
          <Button size="sm" variant="destructive" onClick={clearAlerts}>
            <Trash2 className="w-4 h-4 mr-1" />
            Clear
          </Button>
        </div>
      </Card>

      {/* Real-time Alert Feed */}
      <Card className="p-4 border-border bg-card">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-foreground flex items-center gap-2">
            <BellRing className="w-4 h-4 text-accent animate-pulse" />
            Real-Time Strategy Alerts
          </h4>
          <Badge variant="outline" className="font-mono">
            {filteredAlerts.length} alerts
          </Badge>
        </div>

        {!isRunning && (
          <div className="text-center py-8 text-muted-foreground">
            <Pause className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>HFT Engine is stopped. Start to receive alerts.</p>
          </div>
        )}

        {isRunning && getActiveStrategies().length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No strategies enabled. Enable strategies to receive alerts.</p>
          </div>
        )}

        {isRunning && getActiveStrategies().length > 0 && (
          <ScrollArea className="h-[400px]">
            <div className="space-y-2">
              {filteredAlerts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Activity className="w-12 h-12 mx-auto mb-2 opacity-50 animate-pulse" />
                  <p>Waiting for signals...</p>
                </div>
              ) : (
                filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 rounded-lg border transition-all ${
                      alert.acknowledged
                        ? "border-border bg-secondary/30 opacity-60"
                        : "border-primary/50 bg-primary/5"
                    }`}
                    onClick={() => acknowledgeAlert(alert.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${getSignalColor(alert.signal)}`}>
                        {getSignalIcon(alert.signal)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-foreground">{alert.instrument}</span>
                            <Badge className={getSignalColor(alert.signal)}>{alert.signal}</Badge>
                            <Badge variant="outline" className="text-xs">
                              {(alert.strength * 100).toFixed(0)}%
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            {alert.timestamp.toLocaleTimeString()}
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">{alert.message}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {alert.strategy}
                          </Badge>
                          <span className="text-xs font-mono text-foreground">
                            @ {alert.price.toFixed(alert.price > 100 ? 2 : 4)}
                          </span>
                        </div>
                      </div>
                      {!alert.acknowledged && (
                        <Button size="sm" variant="ghost" onClick={() => acknowledgeAlert(alert.id)}>
                          <CheckCircle2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        )}
      </Card>

      {/* Signal Summary */}
      <Card className="p-4 border-border bg-card">
        <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
          <Target className="w-4 h-4 text-primary" />
          Signal Summary (Last 100)
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-success/10 rounded-lg text-center">
            <TrendingUp className="w-6 h-6 text-success mx-auto mb-1" />
            <p className="text-2xl font-bold text-success">
              {alerts.filter((a) => a.signal === "BUY").length}
            </p>
            <p className="text-xs text-muted-foreground">Buy Signals</p>
          </div>
          <div className="p-3 bg-destructive/10 rounded-lg text-center">
            <TrendingDown className="w-6 h-6 text-destructive mx-auto mb-1" />
            <p className="text-2xl font-bold text-destructive">
              {alerts.filter((a) => a.signal === "SELL").length}
            </p>
            <p className="text-xs text-muted-foreground">Sell Signals</p>
          </div>
          <div className="p-3 bg-accent/10 rounded-lg text-center">
            <AlertCircle className="w-6 h-6 text-accent mx-auto mb-1" />
            <p className="text-2xl font-bold text-accent">
              {alerts.filter((a) => a.signal === "CAUTION").length}
            </p>
            <p className="text-xs text-muted-foreground">Caution</p>
          </div>
          <div className="p-3 bg-muted/30 rounded-lg text-center">
            <Activity className="w-6 h-6 text-muted-foreground mx-auto mb-1" />
            <p className="text-2xl font-bold text-foreground">
              {alerts.filter((a) => a.signal === "NEUTRAL").length}
            </p>
            <p className="text-xs text-muted-foreground">Neutral</p>
          </div>
        </div>
      </Card>
    </div>
  );
};
