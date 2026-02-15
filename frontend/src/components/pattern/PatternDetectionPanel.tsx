import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Zap, 
  Search, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown, 
  Trash2,
  Clock,
  Target,
  ChevronDown,
  ChevronUp,
  Sparkles
} from "lucide-react";
import { DetectedPattern, generateAutoPatterns, getConfidenceColor } from "@/lib/patternUtils";

interface PatternDetectionPanelProps {
  currentPrice: number;
  instrument: string;
  timeframe: string;
  patterns: DetectedPattern[];
  onPatternsDetected: (patterns: DetectedPattern[]) => void;
  onDeletePattern: (id: string) => void;
}

export const PatternDetectionPanel = ({
  currentPrice,
  instrument,
  timeframe,
  patterns,
  onPatternsDetected,
  onDeletePattern,
}: PatternDetectionPanelProps) => {
  const [isDetecting, setIsDetecting] = useState(false);
  const [lastDetection, setLastDetection] = useState<Date | null>(null);
  const [expandedPattern, setExpandedPattern] = useState<string | null>(null);

  const runAutoDetection = () => {
    setIsDetecting(true);
    setTimeout(() => {
      const detected = generateAutoPatterns(currentPrice, instrument, timeframe);
      onPatternsDetected(detected);
      setLastDetection(new Date());
      setIsDetecting(false);
    }, 1500);
  };

  const getSignalStyles = (signal: string) => {
    switch (signal) {
      case "Bullish":
        return {
          bg: "bg-success/10",
          border: "border-success/30",
          text: "text-success",
          icon: TrendingUp,
        };
      case "Bearish":
        return {
          bg: "bg-destructive/10",
          border: "border-destructive/30",
          text: "text-destructive",
          icon: TrendingDown,
        };
      default:
        return {
          bg: "bg-muted",
          border: "border-border",
          text: "text-muted-foreground",
          icon: Target,
        };
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "Candlestick": return "bg-blue-500/10 text-blue-500 border-blue-500/30";
      case "Wave Structure": return "bg-purple-500/10 text-purple-500 border-purple-500/30";
      case "Time–Price Wave": return "bg-amber-500/10 text-amber-500 border-amber-500/30";
      case "Harmonic Pattern": return "bg-pink-500/10 text-pink-500 border-pink-500/30";
      case "Chart Pattern": return "bg-teal-500/10 text-teal-500 border-teal-500/30";
      default: return "bg-muted text-muted-foreground border-border";
    }
  };

  return (
    <Card className="overflow-hidden border-border bg-card">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-gradient-to-br from-primary to-primary/60 p-3 shadow-lg shadow-primary/20">
            <Zap className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground">Auto Pattern Detection</h3>
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-3 w-3" />
              {lastDetection
                ? `Last scan: ${lastDetection.toLocaleTimeString()}`
                : "Click to run automatic pattern detection"}
            </p>
          </div>
        </div>
        <Button
          onClick={runAutoDetection}
          disabled={isDetecting}
          size="lg"
          className="bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg shadow-primary/20"
        >
          {isDetecting ? (
            <>
              <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
              Scanning...
            </>
          ) : (
            <>
              <Search className="mr-2 h-5 w-5" />
              Run Detection
            </>
          )}
        </Button>
      </div>

      {/* Patterns Grid */}
      {patterns.length > 0 ? (
        <ScrollArea className="h-[500px]">
          <div className="grid gap-3 p-4 md:grid-cols-2">
            {patterns.map((pattern) => {
              const signalStyles = getSignalStyles(pattern.signal);
              const SignalIcon = signalStyles.icon;
              const isExpanded = expandedPattern === pattern.id;

              return (
                <Card
                  key={pattern.id}
                  className={`group relative overflow-hidden border transition-all duration-200 ${signalStyles.border} ${signalStyles.bg} hover:shadow-md`}
                >
                  {/* Pattern Header */}
                  <div 
                    className="cursor-pointer p-4"
                    onClick={() => setExpandedPattern(isExpanded ? null : pattern.id)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className={`rounded-lg p-2 ${signalStyles.bg}`}>
                          <SignalIcon className={`h-5 w-5 ${signalStyles.text}`} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <h4 className="font-semibold text-foreground line-clamp-1">
                            {pattern.name}
                          </h4>
                          <div className="mt-1 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className={`text-xs ${getTypeColor(pattern.type)}`}>
                              {pattern.type}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {pattern.timeframe}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <div className={`text-lg font-bold font-mono ${getConfidenceColor(pattern.confidence)}`}>
                          {(pattern.confidence * 100).toFixed(0)}%
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                    </div>

                    {/* Confidence Bar */}
                    <div className="mt-3">
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            pattern.confidence >= 0.85
                              ? "bg-success"
                              : pattern.confidence >= 0.7
                              ? "bg-accent"
                              : "bg-warning"
                          }`}
                          style={{ width: `${pattern.confidence * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="border-t border-border/50 bg-background/50 p-4">
                      <div className="grid gap-3 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Price Range</span>
                          <span className="font-mono text-foreground">{pattern.priceRange}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Time Window</span>
                          <span className="text-foreground">{pattern.timeWindow}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Signal</span>
                          <Badge className={signalStyles.bg + " " + signalStyles.text}>
                            <SignalIcon className="mr-1 h-3 w-3" />
                            {pattern.signal}
                          </Badge>
                        </div>
                      </div>
                      <div className="mt-4 flex justify-end">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeletePattern(pattern.id);
                          }}
                        >
                          <Trash2 className="mr-2 h-3 w-3" />
                          Remove
                        </Button>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </ScrollArea>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4">
            <Sparkles className="h-8 w-8 text-muted-foreground" />
          </div>
          <h4 className="mt-4 text-lg font-semibold text-foreground">No Patterns Detected</h4>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Click "Run Detection" to scan for candlestick, wave, harmonic, and chart patterns automatically.
          </p>
        </div>
      )}
    </Card>
  );
};
