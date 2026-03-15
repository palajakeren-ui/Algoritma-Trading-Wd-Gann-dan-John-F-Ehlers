import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Clock,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Target,
  Zap,
  Activity,
  CheckCircle,
  AlertTriangle,
  Layers,
} from "lucide-react";
import { DetectedPattern, TIMEFRAMES, generateAutoPatterns } from "@/lib/patternUtils";

interface TimeframeAnalysis {
  timeframe: string;
  label: string;
  patterns: DetectedPattern[];
  dominantSignal: "Bullish" | "Bearish" | "Neutral";
  avgConfidence: number;
  lastUpdated: Date;
  isLoading: boolean;
}

interface RealtimeMultiTimeframeProps {
  currentPrice: number;
  instrument: string;
  onPatternsUpdated: (patterns: DetectedPattern[]) => void;
}

export const RealtimeMultiTimeframe = ({
  currentPrice,
  instrument,
  onPatternsUpdated,
}: RealtimeMultiTimeframeProps) => {
  const [timeframeAnalyses, setTimeframeAnalyses] = useState<TimeframeAnalysis[]>([]);
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>([
    "M1", "M5", "M15", "H1", "H4", "D1", "Y1"
  ]);

  // Initialize timeframe analyses
  useEffect(() => {
    const initialAnalyses: TimeframeAnalysis[] = TIMEFRAMES.map((tf) => ({
      timeframe: tf.value,
      label: tf.label,
      patterns: [],
      dominantSignal: "Neutral" as const,
      avgConfidence: 0,
      lastUpdated: new Date(),
      isLoading: false,
    }));
    setTimeframeAnalyses(initialAnalyses);
  }, []);

  // Calculate dominant signal and average confidence
  const calculateStats = (patterns: DetectedPattern[]) => {
    if (patterns.length === 0) {
      return { dominantSignal: "Neutral" as const, avgConfidence: 0 };
    }

    const bullish = patterns.filter((p) => p.signal === "Bullish").length;
    const bearish = patterns.filter((p) => p.signal === "Bearish").length;
    const avgConfidence =
      patterns.reduce((sum, p) => sum + p.confidence, 0) / patterns.length;

    let dominantSignal: "Bullish" | "Bearish" | "Neutral" = "Neutral";
    if (bullish > bearish && bullish > patterns.length * 0.4) {
      dominantSignal = "Bullish";
    } else if (bearish > bullish && bearish > patterns.length * 0.4) {
      dominantSignal = "Bearish";
    }

    return { dominantSignal, avgConfidence };
  };

  // Scan single timeframe
  const scanTimeframe = useCallback(
    async (timeframe: string) => {
      setTimeframeAnalyses((prev) =>
        prev.map((ta) =>
          ta.timeframe === timeframe ? { ...ta, isLoading: true } : ta
        )
      );

      // Simulate async detection
      await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1000));

      const patterns = generateAutoPatterns(currentPrice, instrument, timeframe);
      const { dominantSignal, avgConfidence } = calculateStats(patterns);

      setTimeframeAnalyses((prev) =>
        prev.map((ta) =>
          ta.timeframe === timeframe
            ? {
              ...ta,
              patterns,
              dominantSignal,
              avgConfidence,
              lastUpdated: new Date(),
              isLoading: false,
            }
            : ta
        )
      );

      return patterns;
    },
    [currentPrice, instrument]
  );

  // Scan all selected timeframes
  const scanAllTimeframes = useCallback(async () => {
    const allPatterns: DetectedPattern[] = [];

    for (const tf of selectedTimeframes) {
      const patterns = await scanTimeframe(tf);
      allPatterns.push(...patterns);
    }

    onPatternsUpdated(allPatterns);
  }, [selectedTimeframes, scanTimeframe, onPatternsUpdated]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!isAutoRefresh) return;

    const interval = setInterval(() => {
      scanAllTimeframes();
    }, 30000);

    return () => clearInterval(interval);
  }, [isAutoRefresh, scanAllTimeframes]);

  // Initial scan
  useEffect(() => {
    scanAllTimeframes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [instrument]);

  const toggleTimeframe = (tf: string) => {
    setSelectedTimeframes((prev) =>
      prev.includes(tf) ? prev.filter((t) => t !== tf) : [...prev, tf]
    );
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "Bullish":
        return "bg-success/10 text-success border-success/30";
      case "Bearish":
        return "bg-destructive/10 text-destructive border-destructive/30";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case "Bullish":
        return <TrendingUp className="h-4 w-4" />;
      case "Bearish":
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Target className="h-4 w-4" />;
    }
  };

  // Summary stats
  const activeAnalyses = timeframeAnalyses.filter((ta) =>
    selectedTimeframes.includes(ta.timeframe)
  );
  const totalPatterns = activeAnalyses.reduce(
    (sum, ta) => sum + ta.patterns.length,
    0
  );
  const bullishTfs = activeAnalyses.filter(
    (ta) => ta.dominantSignal === "Bullish"
  ).length;
  const bearishTfs = activeAnalyses.filter(
    (ta) => ta.dominantSignal === "Bearish"
  ).length;

  return (
    <Card className="overflow-hidden border-border bg-card">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-gradient-to-br from-primary to-primary/60 p-3 shadow-lg shadow-primary/20">
            <Layers className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground">
              Real-Time Multi-Timeframe Analysis
            </h3>
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-3 w-3" />
              {selectedTimeframes.length} timeframes • {totalPatterns} patterns detected
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={isAutoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setIsAutoRefresh(!isAutoRefresh)}
            className="gap-2"
          >
            {isAutoRefresh ? (
              <>
                <CheckCircle className="h-4 w-4" />
                Auto-Refresh ON
              </>
            ) : (
              <>
                <AlertTriangle className="h-4 w-4" />
                Auto-Refresh OFF
              </>
            )}
          </Button>
          <Button
            onClick={scanAllTimeframes}
            className="gap-2 bg-gradient-to-r from-primary to-primary/80"
          >
            <RefreshCw className="h-4 w-4" />
            Scan All
          </Button>
        </div>
      </div>

      {/* Timeframe Selector */}
      <div className="border-b border-border bg-muted/30 p-4">
        <div className="flex flex-wrap gap-1.5">
          {TIMEFRAMES.map((tf) => {
            const analysis = timeframeAnalyses.find((ta) => ta.timeframe === tf.value);
            const isSelected = selectedTimeframes.includes(tf.value);
            const signalColor = analysis ? getSignalColor(analysis.dominantSignal) : "";

            return (
              <Button
                key={tf.value}
                variant={isSelected ? "default" : "outline"}
                size="sm"
                onClick={() => toggleTimeframe(tf.value)}
                className={`font-mono text-xs ${isSelected ? signalColor : ""}`}
              >
                {tf.value}
                {analysis && analysis.patterns.length > 0 && (
                  <Badge
                    variant="secondary"
                    className="ml-1 h-4 w-4 rounded-full p-0 text-[10px]"
                  >
                    {analysis.patterns.length}
                  </Badge>
                )}
              </Button>
            );
          })}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3 border-b border-border p-4">
        <Card className="flex items-center gap-3 bg-success/10 border-success/30 p-3">
          <TrendingUp className="h-5 w-5 text-success" />
          <div>
            <div className="text-xl font-bold text-success">{bullishTfs}</div>
            <div className="text-xs text-muted-foreground">Bullish TFs</div>
          </div>
        </Card>
        <Card className="flex items-center gap-3 bg-destructive/10 border-destructive/30 p-3">
          <TrendingDown className="h-5 w-5 text-destructive" />
          <div>
            <div className="text-xl font-bold text-destructive">{bearishTfs}</div>
            <div className="text-xs text-muted-foreground">Bearish TFs</div>
          </div>
        </Card>
        <Card className="flex items-center gap-3 bg-muted/50 border-border p-3">
          <Zap className="h-5 w-5 text-primary" />
          <div>
            <div className="text-xl font-bold text-foreground">{totalPatterns}</div>
            <div className="text-xs text-muted-foreground">Total Patterns</div>
          </div>
        </Card>
      </div>

      {/* Timeframe Grid */}
      <ScrollArea className="h-[400px]">
        <div className="grid gap-3 p-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {timeframeAnalyses
            .filter((ta) => selectedTimeframes.includes(ta.timeframe))
            .map((ta) => (
              <Card
                key={ta.timeframe}
                className={`relative overflow-hidden border transition-all ${getSignalColor(ta.dominantSignal)} hover:shadow-md`}
              >
                {ta.isLoading && (
                  <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-10">
                    <RefreshCw className="h-5 w-5 animate-spin text-primary" />
                  </div>
                )}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="font-mono font-bold">
                        {ta.timeframe}
                      </Badge>
                      {getSignalIcon(ta.dominantSignal)}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => scanTimeframe(ta.timeframe)}
                    >
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Patterns</span>
                      <span className="font-bold text-foreground">{ta.patterns.length}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Signal</span>
                      <Badge className={getSignalColor(ta.dominantSignal)}>
                        {ta.dominantSignal}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Confidence</span>
                      <span className="font-mono font-semibold">
                        {(ta.avgConfidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Progress
                      value={ta.avgConfidence * 100}
                      className="h-1.5"
                    />
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {ta.lastUpdated.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
        </div>
      </ScrollArea>
    </Card>
  );
};
