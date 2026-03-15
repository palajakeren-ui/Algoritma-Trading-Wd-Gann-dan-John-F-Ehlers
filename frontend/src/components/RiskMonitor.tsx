import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Shield, TrendingUp } from "lucide-react";
import { Progress } from "@/components/ui/progress";

export const RiskMonitor = () => {
  return (
    <Card className="p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">Risk Monitor</h2>
        <Badge variant="outline" className="bg-success/10 text-success border-success/20">
          <Shield className="w-3 h-3 mr-1" />
          Healthy
        </Badge>
      </div>

      <div className="space-y-6">
        {/* Portfolio Exposure */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Portfolio Exposure</span>
            <span className="text-sm font-semibold text-foreground">2.1%</span>
          </div>
          <Progress value={21} className="h-2" />
          <p className="text-xs text-muted-foreground mt-1">Max allowed: 10%</p>
        </div>

        {/* Drawdown */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Current Drawdown</span>
            <span className="text-sm font-semibold text-warning">3.2%</span>
          </div>
          <Progress value={16} className="h-2" />
          <p className="text-xs text-muted-foreground mt-1">Max allowed: 20%</p>
        </div>

        {/* Win Rate */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Win Rate (90d)</span>
            <span className="text-sm font-semibold text-success">67.8%</span>
          </div>
          <Progress value={67.8} className="h-2" />
        </div>

        {/* Kelly Criterion */}
        <div className="pt-4 border-t border-border">
          <h3 className="text-sm font-semibold text-foreground mb-3">Position Sizing</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-secondary/50">
              <p className="text-xs text-muted-foreground">Kelly Fraction</p>
              <p className="text-lg font-bold text-foreground">0.5x</p>
            </div>
            <div className="p-3 rounded-lg bg-secondary/50">
              <p className="text-xs text-muted-foreground">Risk/Trade</p>
              <p className="text-lg font-bold text-foreground">2.0%</p>
            </div>
          </div>
        </div>

        {/* Risk Alerts */}
        <div className="pt-4 border-t border-border">
          <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2 text-warning" />
            Active Alerts
          </h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 rounded bg-warning/5 border border-warning/20">
              <span className="text-xs text-foreground">EURUSD exposure near limit</span>
              <Badge variant="outline" className="text-xs border-warning text-warning">
                Watch
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
