import { Activity, TrendingUp, AlertCircle, Zap } from "lucide-react";
import { Card } from "@/components/ui/card";

export const DashboardHeader = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card className="p-4 border-border bg-card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Portfolio Value</p>
            <h3 className="text-2xl font-bold text-foreground">$127,543.21</h3>
            <p className="text-xs text-success flex items-center mt-1">
              <TrendingUp className="w-3 h-3 mr-1" />
              +12.45% (24h)
            </p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-success/10 flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-success" />
          </div>
        </div>
      </Card>

      <Card className="p-4 border-border bg-card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Active Signals</p>
            <h3 className="text-2xl font-bold text-foreground">23</h3>
            <p className="text-xs text-accent flex items-center mt-1">
              <Activity className="w-3 h-3 mr-1" />
              8 Strong • 15 Medium
            </p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
            <Activity className="w-6 h-6 text-accent" />
          </div>
        </div>
      </Card>

      <Card className="p-4 border-border bg-card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Win Rate</p>
            <h3 className="text-2xl font-bold text-foreground">67.8%</h3>
            <p className="text-xs text-success flex items-center mt-1">
              <Zap className="w-3 h-3 mr-1" />
              Last 90 days
            </p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-success/10 flex items-center justify-center">
            <Zap className="w-6 h-6 text-success" />
          </div>
        </div>
      </Card>

      <Card className="p-4 border-border bg-card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Risk Level</p>
            <h3 className="text-2xl font-bold text-foreground">Low</h3>
            <p className="text-xs text-muted-foreground flex items-center mt-1">
              <AlertCircle className="w-3 h-3 mr-1" />
              2.1% exposure
            </p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
            <AlertCircle className="w-6 h-6 text-primary" />
          </div>
        </div>
      </Card>
    </div>
  );
};
