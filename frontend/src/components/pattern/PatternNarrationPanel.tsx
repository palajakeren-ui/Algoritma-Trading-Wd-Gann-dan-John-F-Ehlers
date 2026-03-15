import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Lightbulb,
  ChevronRight
} from "lucide-react";
import { DetectedPattern, generatePatternNarration } from "@/lib/patternUtils";

interface PatternNarrationPanelProps {
  patterns: DetectedPattern[];
}

export const PatternNarrationPanel = ({ patterns }: PatternNarrationPanelProps) => {
  const narrations = generatePatternNarration(patterns);

  const getNarrationStyle = (narration: string) => {
    if (narration.includes("⚠️")) {
      return {
        bg: "bg-destructive/5",
        border: "border-destructive/30",
        icon: AlertTriangle,
        iconColor: "text-destructive",
      };
    }
    return {
      bg: "bg-success/5",
      border: "border-success/30",
      icon: TrendingUp,
      iconColor: "text-success",
    };
  };

  const defaultNarrations = [
    {
      text: "**Bullish Engulfing** pada 101,700 (konfirmasi intraday 2025-11-04 15:25:00 UTC) memberikan sinyal masuk awal.",
      type: "bullish",
    },
    {
      text: "**Morning Star** pada area 101,800 memperkuat setup bagi Wave 3 impulsif — target terukur 102,200 dalam 7–14 days.",
      type: "bullish",
    },
    {
      text: "**Gann Wave** menunjuk reversal window kuat sekitar 2025-11-16 (target 103,000) — gunakan untuk manajemen TP bagian/scale-out.",
      type: "neutral",
    },
  ];

  const displayNarrations = narrations.length > 0 ? narrations : null;

  return (
    <Card className="overflow-hidden border-border bg-card">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-border bg-gradient-to-r from-amber-500/5 to-primary/5 p-4">
        <div className="rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 p-3 shadow-lg shadow-amber-500/20">
          <Lightbulb className="h-6 w-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-foreground">Pattern Summary</h3>
          <p className="text-sm text-muted-foreground">
            AI-generated insights from detected patterns
          </p>
        </div>
        <Badge variant="outline" className="ml-auto">
          {patterns.length} patterns analyzed
        </Badge>
      </div>

      {/* Narrations */}
      <ScrollArea className="h-[250px]">
        <div className="space-y-3 p-4">
          {displayNarrations ? (
            displayNarrations.map((narration, idx) => {
              const styles = getNarrationStyle(narration);
              const NarrationIcon = styles.icon;

              return (
                <div
                  key={idx}
                  className={`flex items-start gap-3 rounded-xl border p-4 transition-all hover:shadow-sm ${styles.bg} ${styles.border}`}
                >
                  <div className={`mt-0.5 rounded-lg p-1.5 ${styles.bg}`}>
                    <NarrationIcon className={`h-4 w-4 ${styles.iconColor}`} />
                  </div>
                  <p
                    className="flex-1 text-sm leading-relaxed text-foreground"
                    dangerouslySetInnerHTML={{
                      __html: narration.replace(/\*\*(.*?)\*\*/g, "<strong class='font-semibold'>$1</strong>"),
                    }}
                  />
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
              );
            })
          ) : (
            <>
              {defaultNarrations.map((item, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 rounded-xl border p-4 transition-all hover:shadow-sm ${
                    item.type === "bullish"
                      ? "bg-success/5 border-success/30"
                      : "bg-accent/5 border-accent/30"
                  }`}
                >
                  <div className={`mt-0.5 rounded-lg p-1.5 ${
                    item.type === "bullish" ? "bg-success/10" : "bg-accent/10"
                  }`}>
                    {item.type === "bullish" ? (
                      <TrendingUp className="h-4 w-4 text-success" />
                    ) : (
                      <Lightbulb className="h-4 w-4 text-accent" />
                    )}
                  </div>
                  <p
                    className="flex-1 text-sm leading-relaxed text-foreground"
                    dangerouslySetInnerHTML={{
                      __html: item.text.replace(/\*\*(.*?)\*\*/g, "<strong class='font-semibold'>$1</strong>"),
                    }}
                  />
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
              ))}
            </>
          )}
        </div>
      </ScrollArea>
    </Card>
  );
};
