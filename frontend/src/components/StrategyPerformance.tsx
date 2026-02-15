import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface Strategy {
  name: string;
  accuracy: number;
  signals: number;
  winRate: number;
  enabled: boolean;
}

const strategies: Strategy[] = [
  { name: "Gann Geometry", accuracy: 75, signals: 145, winRate: 68.5, enabled: true },
  { name: "Ehlers DSP", accuracy: 72, signals: 203, winRate: 71.2, enabled: true },
  { name: "ML Ensemble", accuracy: 78, signals: 187, winRate: 73.8, enabled: true },
  { name: "Astro Cycles", accuracy: 65, signals: 89, winRate: 64.3, enabled: true },
  { name: "Pattern Recognition", accuracy: 70, signals: 156, winRate: 67.9, enabled: true },
];

export const StrategyPerformance = () => {
  return (
    <Card className="p-6 border-border bg-card">
      <h2 className="text-lg font-semibold text-foreground mb-4">Strategy Performance</h2>

      <div className="space-y-4">
        {strategies.map((strategy, idx) => (
          <div key={idx} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    strategy.enabled ? "bg-success" : "bg-muted-foreground"
                  }`}
                />
                <span className="text-sm font-medium text-foreground">{strategy.name}</span>
              </div>
              <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                <span>{strategy.signals} signals</span>
                <span className="text-foreground font-semibold">{strategy.winRate}%</span>
              </div>
            </div>
            <Progress value={strategy.accuracy} className="h-2" />
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-border">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-success">68.7%</p>
            <p className="text-xs text-muted-foreground">Avg Win Rate</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">780</p>
            <p className="text-xs text-muted-foreground">Total Signals</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-accent">2.4</p>
            <p className="text-xs text-muted-foreground">Avg R:R</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
