import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  BarChart3, 
  Plus, 
  Trash2, 
  TrendingUp, 
  TrendingDown,
  ChevronDown,
  ChevronUp,
  Target
} from "lucide-react";
import { DetectedPattern, PatternType, SignalType, PATTERN_TYPES, getConfidenceColor } from "@/lib/patternUtils";

interface AddPatternFormProps {
  instrument: string;
  timeframe: string;
  patterns: DetectedPattern[];
  onAddPattern: (pattern: DetectedPattern) => void;
  onDeletePattern: (id: string) => void;
}

export const AddPatternForm = ({
  instrument,
  timeframe,
  patterns,
  onAddPattern,
  onDeletePattern,
}: AddPatternFormProps) => {
  const [newPattern, setNewPattern] = useState({
    name: "",
    type: "Candlestick" as PatternType,
    confidence: 0.75,
    priceRange: "",
    timeWindow: "",
    signal: "Bullish" as SignalType,
  });

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [expandedPattern, setExpandedPattern] = useState<string | null>(null);

  const handleAddPattern = () => {
    if (!newPattern.name || !newPattern.priceRange || !newPattern.timeWindow) return;

    const pattern: DetectedPattern = {
      id: Date.now().toString(),
      ...newPattern,
      instrument,
      timeframe,
      detectedAt: new Date(),
    };

    onAddPattern(pattern);
    setNewPattern({
      name: "",
      type: "Candlestick",
      confidence: 0.75,
      priceRange: "",
      timeWindow: "",
      signal: "Bullish",
    });
    setIsFormOpen(false);
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
      <div className="flex items-center justify-between border-b border-border bg-gradient-to-r from-accent/5 to-primary/5 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-accent to-accent/60 p-3">
            <BarChart3 className="h-6 w-6 text-accent-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground">Detected Patterns</h3>
            <p className="text-sm text-muted-foreground">
              {patterns.length} patterns • {instrument} • {timeframe}
            </p>
          </div>
        </div>
        <Button
          onClick={() => setIsFormOpen(!isFormOpen)}
          variant={isFormOpen ? "secondary" : "default"}
        >
          <Plus className="mr-2 h-4 w-4" />
          {isFormOpen ? "Cancel" : "Add Pattern"}
        </Button>
      </div>

      {/* Add Pattern Form */}
      {isFormOpen && (
        <div className="border-b border-border bg-muted/30 p-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Pattern Name</Label>
              <Input
                placeholder="e.g. Bullish Engulfing"
                value={newPattern.name}
                onChange={(e) => setNewPattern({ ...newPattern, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Type</Label>
              <Select
                value={newPattern.type}
                onValueChange={(v: PatternType) => setNewPattern({ ...newPattern, type: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PATTERN_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Signal</Label>
              <Select
                value={newPattern.signal}
                onValueChange={(v: SignalType) => setNewPattern({ ...newPattern, signal: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Bullish">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-success" />
                      Bullish
                    </div>
                  </SelectItem>
                  <SelectItem value="Bearish">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="h-4 w-4 text-destructive" />
                      Bearish
                    </div>
                  </SelectItem>
                  <SelectItem value="Neutral">Neutral</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Confidence (0-1)</Label>
              <Input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={newPattern.confidence}
                onChange={(e) => setNewPattern({ ...newPattern, confidence: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Price Range</Label>
              <Input
                placeholder="e.g. Target: 102,200"
                value={newPattern.priceRange}
                onChange={(e) => setNewPattern({ ...newPattern, priceRange: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Time Window</Label>
              <Input
                placeholder="e.g. next 7-14 days"
                value={newPattern.timeWindow}
                onChange={(e) => setNewPattern({ ...newPattern, timeWindow: e.target.value })}
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={handleAddPattern} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Pattern
            </Button>
          </div>
        </div>
      )}

      {/* Patterns List */}
      {patterns.length > 0 ? (
        <ScrollArea className="h-[400px]">
          <div className="divide-y divide-border">
            {patterns.map((pattern) => {
              const signalStyles = getSignalStyles(pattern.signal);
              const SignalIcon = signalStyles.icon;
              const isExpanded = expandedPattern === pattern.id;

              return (
                <div
                  key={pattern.id}
                  className="transition-colors hover:bg-muted/30"
                >
                  <div 
                    className="flex cursor-pointer items-center justify-between p-4"
                    onClick={() => setExpandedPattern(isExpanded ? null : pattern.id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`rounded-lg p-2 ${signalStyles.bg}`}>
                        <SignalIcon className={`h-5 w-5 ${signalStyles.text}`} />
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">{pattern.name}</h4>
                        <div className="mt-1 flex items-center gap-2">
                          <Badge variant="outline" className={`text-xs ${getTypeColor(pattern.type)}`}>
                            {pattern.type}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {pattern.timeframe}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
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

                  {isExpanded && (
                    <div className="border-t border-border/50 bg-muted/20 p-4">
                      <div className="grid gap-3 text-sm md:grid-cols-3">
                        <div>
                          <span className="text-muted-foreground">Price Range</span>
                          <p className="mt-1 font-mono text-foreground">{pattern.priceRange}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Time Window</span>
                          <p className="mt-1 text-foreground">{pattern.timeWindow}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Signal</span>
                          <div className="mt-1">
                            <Badge className={`${signalStyles.bg} ${signalStyles.text} border ${signalStyles.border}`}>
                              <SignalIcon className="mr-1 h-3 w-3" />
                              {pattern.signal}
                            </Badge>
                          </div>
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
                </div>
              );
            })}
          </div>
        </ScrollArea>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4">
            <BarChart3 className="h-8 w-8 text-muted-foreground" />
          </div>
          <h4 className="mt-4 text-lg font-semibold text-foreground">No Patterns Added</h4>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Click "Add Pattern" to manually record detected patterns.
          </p>
        </div>
      )}
    </Card>
  );
};
