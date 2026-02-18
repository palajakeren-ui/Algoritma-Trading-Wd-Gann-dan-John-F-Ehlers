import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from "@/components/ui/slider";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Bell,
  BellRing,
  Volume2,
  VolumeX,
  Trash2,
  Settings,
  TrendingUp,
  TrendingDown,
  Target,
  Clock,
  CheckCircle,
  AlertTriangle,
  Zap,
  X,
} from "lucide-react";
import { DetectedPattern, TIMEFRAMES } from "@/lib/patternUtils";
import { toast } from "@/hooks/use-toast";

interface PatternAlert {
  id: string;
  pattern: DetectedPattern;
  triggeredAt: Date;
  acknowledged: boolean;
}

interface AlertSettings {
  enabled: boolean;
  soundEnabled: boolean;
  minConfidence: number;
  signalTypes: {
    bullish: boolean;
    bearish: boolean;
    neutral: boolean;
  };
  patternTypes: {
    candlestick: boolean;
    waveStructure: boolean;
    timePriceWave: boolean;
    harmonicPattern: boolean;
    chartPattern: boolean;
  };
  timeframes: string[];
}

interface PatternAlertsProps {
  patterns: DetectedPattern[];
  instrument: string;
}

export const PatternAlerts = ({ patterns, instrument }: PatternAlertsProps) => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [alerts, setAlerts] = useState<PatternAlert[]>([]);
  const [settings, setSettings] = useState<AlertSettings>(() => {
    const saved = localStorage.getItem("patternAlertSettings");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // Fall through to default
      }
    }
    return {
      enabled: true,
      soundEnabled: true,
      minConfidence: 75,
      signalTypes: { bullish: true, bearish: true, neutral: false },
      patternTypes: {
        candlestick: true,
        waveStructure: true,
        timePriceWave: true,
        harmonicPattern: true,
        chartPattern: true,
      },
      timeframes: ["M15", "H1", "H4", "D1"],
    };
  });

  const [processedPatternIds, setProcessedPatternIds] = useState<Set<string>>(new Set());

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem("patternAlertSettings", JSON.stringify(settings));
  }, [settings]);

  // Play alert sound
  const playAlertSound = useCallback(() => {
    if (settings.soundEnabled) {
      const audioContext = new (window.AudioContext || (window as typeof window & { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 800;
      oscillator.type = "sine";
      gainNode.gain.value = 0.1;
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.15);
      
      setTimeout(() => {
        const osc2 = audioContext.createOscillator();
        osc2.connect(gainNode);
        osc2.frequency.value = 1000;
        osc2.type = "sine";
        osc2.start(audioContext.currentTime);
        osc2.stop(audioContext.currentTime + 0.15);
      }, 150);
    }
  }, [settings.soundEnabled]);

  // Check patterns for alerts
  useEffect(() => {
    if (!settings.enabled) return;

    patterns.forEach((pattern) => {
      // Skip already processed patterns
      if (processedPatternIds.has(pattern.id)) return;

      // Check confidence threshold
      if (pattern.confidence * 100 < settings.minConfidence) return;

      // Check signal type
      const signalType = pattern.signal.toLowerCase() as keyof typeof settings.signalTypes;
      if (!settings.signalTypes[signalType]) return;

      // Check pattern type
      const patternTypeMap: Record<string, keyof typeof settings.patternTypes> = {
        Candlestick: "candlestick",
        "Wave Structure": "waveStructure",
        "Time–Price Wave": "timePriceWave",
        "Harmonic Pattern": "harmonicPattern",
        "Chart Pattern": "chartPattern",
      };
      const patternTypeKey = patternTypeMap[pattern.type];
      if (patternTypeKey && !settings.patternTypes[patternTypeKey]) return;

      // Check timeframe
      if (settings.timeframes.length > 0 && !settings.timeframes.includes(pattern.timeframe)) return;

      // Create alert
      const newAlert: PatternAlert = {
        id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        pattern,
        triggeredAt: new Date(),
        acknowledged: false,
      };

      setAlerts((prev) => [newAlert, ...prev].slice(0, 50)); // Keep last 50 alerts
      setProcessedPatternIds((prev) => new Set([...prev, pattern.id]));
      playAlertSound();

      toast({
        title: `🎯 Pattern Alert: ${pattern.name}`,
        description: `${pattern.signal} signal detected on ${pattern.instrument} (${pattern.timeframe}) - ${(pattern.confidence * 100).toFixed(0)}% confidence`,
      });
    });
  }, [patterns, settings, processedPatternIds, playAlertSound]);

  const acknowledgeAlert = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
    );
  };

  const dismissAlert = (alertId: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
  };

  const clearAllAlerts = () => {
    setAlerts([]);
    toast({
      title: "Alerts Cleared",
      description: "All pattern alerts have been dismissed.",
    });
  };

  const unacknowledgedCount = alerts.filter((a) => !a.acknowledged).length;

  const toggleTimeframe = (tf: string) => {
    setSettings((prev) => ({
      ...prev,
      timeframes: prev.timeframes.includes(tf)
        ? prev.timeframes.filter((t) => t !== tf)
        : [...prev.timeframes, tf],
    }));
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case "Bullish":
        return <TrendingUp className="h-4 w-4 text-success" />;
      case "Bearish":
        return <TrendingDown className="h-4 w-4 text-destructive" />;
      default:
        return <Target className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Alert Bell Button */}
      <Dialog>
        <DialogTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className="relative"
          >
            {unacknowledgedCount > 0 ? (
              <BellRing className="h-4 w-4 animate-pulse text-primary" />
            ) : (
              <Bell className="h-4 w-4" />
            )}
            {unacknowledgedCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs font-bold text-destructive-foreground">
                {unacknowledgedCount > 9 ? "9+" : unacknowledgedCount}
              </span>
            )}
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BellRing className="h-5 w-5 text-primary" />
                Pattern Alerts
              </div>
              {alerts.length > 0 && (
                <Button variant="ghost" size="sm" onClick={clearAllAlerts} className="text-destructive">
                  <Trash2 className="mr-1 h-4 w-4" />
                  Clear All
                </Button>
              )}
            </DialogTitle>
            <DialogDescription>
              {settings.enabled ? "Real-time alerts for detected patterns" : "Alerts are currently disabled"}
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="h-[400px] pr-3">
            {alerts.length > 0 ? (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <Card
                    key={alert.id}
                    className={`p-4 transition-all ${
                      alert.acknowledged
                        ? "bg-muted/30 border-border opacity-60"
                        : "bg-gradient-to-r from-primary/5 to-accent/5 border-primary/30"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        {getSignalIcon(alert.pattern.signal)}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-foreground truncate">
                              {alert.pattern.name}
                            </span>
                            <Badge
                              variant="outline"
                              className={`text-xs ${
                                alert.pattern.signal === "Bullish"
                                  ? "border-success/30 text-success"
                                  : alert.pattern.signal === "Bearish"
                                  ? "border-destructive/30 text-destructive"
                                  : "border-muted text-muted-foreground"
                              }`}
                            >
                              {alert.pattern.signal}
                            </Badge>
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                            <span className="font-mono">{alert.pattern.timeframe}</span>
                            <span>•</span>
                            <span className="font-semibold">
                              {(alert.pattern.confidence * 100).toFixed(0)}%
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {alert.triggeredAt.toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground truncate">
                            {alert.pattern.priceRange}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {!alert.acknowledged && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-success hover:bg-success/10"
                            onClick={() => acknowledgeAlert(alert.id)}
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground hover:text-destructive"
                          onClick={() => dismissAlert(alert.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="rounded-full bg-muted p-4">
                  <Bell className="h-8 w-8 text-muted-foreground" />
                </div>
                <h4 className="mt-4 font-semibold text-foreground">No Alerts</h4>
                <p className="mt-2 text-sm text-muted-foreground max-w-xs">
                  Pattern alerts will appear here when high-confidence patterns are detected.
                </p>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Settings Button */}
      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              Alert Settings
            </DialogTitle>
            <DialogDescription>
              Configure when and how you receive pattern alerts.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Master Toggle */}
            <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 p-4">
              <div className="flex items-center gap-3">
                <Zap className={`h-5 w-5 ${settings.enabled ? "text-success" : "text-muted-foreground"}`} />
                <div>
                  <Label className="text-sm font-semibold">Enable Alerts</Label>
                  <p className="text-xs text-muted-foreground">Receive pattern notifications</p>
                </div>
              </div>
              <Switch
                checked={settings.enabled}
                onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, enabled: checked }))}
              />
            </div>

            {/* Sound Toggle */}
            <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 p-4">
              <div className="flex items-center gap-3">
                {settings.soundEnabled ? (
                  <Volume2 className="h-5 w-5 text-primary" />
                ) : (
                  <VolumeX className="h-5 w-5 text-muted-foreground" />
                )}
                <div>
                  <Label className="text-sm font-semibold">Sound Alerts</Label>
                  <p className="text-xs text-muted-foreground">Play sound on new alerts</p>
                </div>
              </div>
              <Switch
                checked={settings.soundEnabled}
                onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, soundEnabled: checked }))}
              />
            </div>

            {/* Confidence Threshold */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-semibold">Minimum Confidence</Label>
                <span className="font-mono text-sm font-bold text-primary">{settings.minConfidence}%</span>
              </div>
              <Slider
                value={[settings.minConfidence]}
                onValueChange={([value]) => setSettings((prev) => ({ ...prev, minConfidence: value }))}
                min={50}
                max={95}
                step={5}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Only alert for patterns with confidence ≥ {settings.minConfidence}%
              </p>
            </div>

            {/* Signal Types */}
            <div className="space-y-3">
              <Label className="text-sm font-semibold">Signal Types</Label>
              <div className="flex flex-wrap gap-2">
                {[
                  { key: "bullish" as const, label: "Bullish", color: "bg-success/10 text-success border-success/30" },
                  { key: "bearish" as const, label: "Bearish", color: "bg-destructive/10 text-destructive border-destructive/30" },
                  { key: "neutral" as const, label: "Neutral", color: "bg-muted text-muted-foreground border-border" },
                ].map(({ key, label, color }) => (
                  <Button
                    key={key}
                    variant="outline"
                    size="sm"
                    className={`${settings.signalTypes[key] ? color : "opacity-50"}`}
                    onClick={() =>
                      setSettings((prev) => ({
                        ...prev,
                        signalTypes: { ...prev.signalTypes, [key]: !prev.signalTypes[key] },
                      }))
                    }
                  >
                    {settings.signalTypes[key] && <CheckCircle className="mr-1 h-3 w-3" />}
                    {label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Timeframes */}
            <div className="space-y-3">
              <Label className="text-sm font-semibold">Timeframes</Label>
              <div className="flex flex-wrap gap-1.5">
                {TIMEFRAMES.map((tf) => (
                  <Button
                    key={tf.value}
                    variant={settings.timeframes.includes(tf.value) ? "default" : "outline"}
                    size="sm"
                    className="text-xs font-mono h-7 px-2"
                    onClick={() => toggleTimeframe(tf.value)}
                  >
                    {tf.value}
                  </Button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                {settings.timeframes.length === 0
                  ? "All timeframes selected"
                  : `Alert on: ${settings.timeframes.join(", ")}`}
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
