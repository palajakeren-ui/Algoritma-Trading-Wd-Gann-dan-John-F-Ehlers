import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  FileText, 
  Save, 
  Trash2, 
  TrendingUp, 
  TrendingDown, 
  PenLine,
  Clock,
  ChevronRight
} from "lucide-react";
import { ManualAnalysis, TIMEFRAMES, SignalType } from "@/lib/patternUtils";

interface ManualAnalysisPanelProps {
  instrument: string;
  currentPrice: number;
  analyses: ManualAnalysis[];
  onAddAnalysis: (analysis: ManualAnalysis) => void;
  onDeleteAnalysis: (id: string) => void;
}

export const ManualAnalysisPanel = ({
  instrument,
  currentPrice,
  analyses,
  onAddAnalysis,
  onDeleteAnalysis,
}: ManualAnalysisPanelProps) => {
  const [newAnalysis, setNewAnalysis] = useState({
    timeframe: "H1",
    notes: "",
    patterns: "",
    bias: "Neutral" as SignalType,
    support: "",
    resistance: "",
  });

  const [isFormOpen, setIsFormOpen] = useState(false);

  const handleAddAnalysis = () => {
    if (!newAnalysis.notes) return;

    const analysis: ManualAnalysis = {
      id: Date.now().toString(),
      timeframe: newAnalysis.timeframe,
      instrument,
      notes: newAnalysis.notes,
      patterns: newAnalysis.patterns.split(",").map((p) => p.trim()).filter(Boolean),
      bias: newAnalysis.bias,
      keyLevels: {
        support: parseFloat(newAnalysis.support) || currentPrice * 0.95,
        resistance: parseFloat(newAnalysis.resistance) || currentPrice * 1.05,
      },
      createdAt: new Date(),
    };

    onAddAnalysis(analysis);
    setNewAnalysis({
      timeframe: "H1",
      notes: "",
      patterns: "",
      bias: "Neutral",
      support: "",
      resistance: "",
    });
    setIsFormOpen(false);
  };

  const getBiasStyles = (bias: SignalType) => {
    switch (bias) {
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
          icon: ChevronRight,
        };
    }
  };

  return (
    <Card className="overflow-hidden border-border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-gradient-to-r from-accent/5 to-primary/5 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-accent to-accent/60 p-3">
            <FileText className="h-6 w-6 text-accent-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground">Manual Timeframe Analysis</h3>
            <p className="text-sm text-muted-foreground">
              {analyses.length} analysis recorded
            </p>
          </div>
        </div>
        <Button
          onClick={() => setIsFormOpen(!isFormOpen)}
          variant={isFormOpen ? "secondary" : "default"}
        >
          <PenLine className="mr-2 h-4 w-4" />
          {isFormOpen ? "Cancel" : "New Analysis"}
        </Button>
      </div>

      {/* Add New Analysis Form */}
      {isFormOpen && (
        <div className="border-b border-border bg-muted/30 p-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Timeframe</Label>
              <Select
                value={newAnalysis.timeframe}
                onValueChange={(v) => setNewAnalysis({ ...newAnalysis, timeframe: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map((tf) => (
                    <SelectItem key={tf.value} value={tf.value}>
                      {tf.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Bias</Label>
              <Select
                value={newAnalysis.bias}
                onValueChange={(v: SignalType) => setNewAnalysis({ ...newAnalysis, bias: v })}
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
              <Label className="text-sm font-medium">Support Level</Label>
              <Input
                type="number"
                placeholder={`e.g. ${(currentPrice * 0.95).toFixed(0)}`}
                value={newAnalysis.support}
                onChange={(e) => setNewAnalysis({ ...newAnalysis, support: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Resistance Level</Label>
              <Input
                type="number"
                placeholder={`e.g. ${(currentPrice * 1.05).toFixed(0)}`}
                value={newAnalysis.resistance}
                onChange={(e) => setNewAnalysis({ ...newAnalysis, resistance: e.target.value })}
              />
            </div>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Patterns Identified</Label>
              <Input
                placeholder="e.g. Double Bottom, Rising Wedge, MACD Divergence"
                value={newAnalysis.patterns}
                onChange={(e) => setNewAnalysis({ ...newAnalysis, patterns: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Analysis Notes</Label>
              <Textarea
                placeholder="Your detailed analysis notes..."
                value={newAnalysis.notes}
                onChange={(e) => setNewAnalysis({ ...newAnalysis, notes: e.target.value })}
                rows={2}
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={handleAddAnalysis} className="gap-2">
              <Save className="h-4 w-4" />
              Save Analysis
            </Button>
          </div>
        </div>
      )}

      {/* Analyses List */}
      {analyses.length > 0 ? (
        <ScrollArea className="h-[400px]">
          <div className="divide-y divide-border">
            {analyses.map((analysis) => {
              const biasStyles = getBiasStyles(analysis.bias);
              const BiasIcon = biasStyles.icon;

              return (
                <div key={analysis.id} className="p-4 transition-colors hover:bg-muted/30">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className={`rounded-lg p-2 ${biasStyles.bg}`}>
                        <BiasIcon className={`h-5 w-5 ${biasStyles.text}`} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="outline" className="font-mono">
                            {analysis.timeframe}
                          </Badge>
                          <Badge className={`${biasStyles.bg} ${biasStyles.text} border ${biasStyles.border}`}>
                            {analysis.bias}
                          </Badge>
                          <span className="text-sm text-muted-foreground">{analysis.instrument}</span>
                        </div>
                        
                        <div className="mt-2 flex flex-wrap gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Support: </span>
                            <span className="font-mono text-destructive">
                              ${analysis.keyLevels.support.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Resistance: </span>
                            <span className="font-mono text-success">
                              ${analysis.keyLevels.resistance.toLocaleString()}
                            </span>
                          </div>
                        </div>

                        {analysis.patterns.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {analysis.patterns.map((p, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {p}
                              </Badge>
                            ))}
                          </div>
                        )}

                        <p className="mt-2 text-sm text-foreground">{analysis.notes}</p>
                      </div>
                    </div>
                    
                    <div className="flex flex-col items-end gap-2">
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {analysis.createdAt.toLocaleString()}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                        onClick={() => onDeleteAnalysis(analysis.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4">
            <PenLine className="h-8 w-8 text-muted-foreground" />
          </div>
          <h4 className="mt-4 text-lg font-semibold text-foreground">No Analyses Yet</h4>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Click "New Analysis" to record your first manual timeframe analysis.
          </p>
        </div>
      )}
    </Card>
  );
};
