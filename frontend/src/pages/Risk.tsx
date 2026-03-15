import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, AlertTriangle, TrendingDown, TrendingUp, RefreshCw, Calculator, Target } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import apiService from "@/services/apiService";

interface RiskMetrics {
  status: string;
  config: any;
  metrics: {
    riskStatus: string;
    totalExposure: number;
    maxDrawdown: number;
    sharpeRatio: number;
    kellyFraction: number;
    riskPerTrade: number;
    maxPositionSize: number;
    winRate: number;
    avgRiskReward: number;
    dailyLossLimit: number;
    maxOpenPositions: number;
    leverageLimit: number;
  };
  timestamp: string;
}

interface RRCalculation {
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  riskAmount: number;
  rewardAmount: number;
  riskRewardRatio: number;
  riskPercent: number;
  rewardPercent: number;
  breakevenWinrate: number;
  expectedValue: number;
  rating: string;
  notes: string[];
}

const Risk = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);

  // R:R Calculator state
  const [rrInput, setRrInput] = useState({
    entryPrice: 50000,
    stopLoss: 48500,
    takeProfit: 54000,
    accountBalance: 100000,
    riskPercent: 2.0,
    direction: "LONG"
  });
  const [rrResult, setRrResult] = useState<RRCalculation | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // Risk alerts state
  const [alerts, setAlerts] = useState([
    { severity: "warning", message: "EURUSD position near max size", action: "Watch" },
    { severity: "info", message: "Volatility increased 15%", action: "Monitor" },
    { severity: "success", message: "All stop losses in place", action: "OK" },
  ]);

  const fetchRiskMetrics = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.getRiskConfig();
      setRiskMetrics(result);
      toast.success("Risk metrics loaded from backend");
    } catch (error) {
      console.error("Failed to fetch risk metrics:", error);
      toast.error("Failed to load risk metrics. Using default values.");
      // Set default values
      setRiskMetrics({
        status: "active",
        config: {},
        metrics: {
          riskStatus: "Low",
          totalExposure: 2.1,
          maxDrawdown: -3.2,
          sharpeRatio: 2.4,
          kellyFraction: 0.5,
          riskPerTrade: 2.0,
          maxPositionSize: 5.0,
          winRate: 67.8,
          avgRiskReward: 2.4,
          dailyLossLimit: 5.0,
          maxOpenPositions: 5,
          leverageLimit: 3
        },
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const calculateRR = async () => {
    setIsCalculating(true);
    try {
      const result = await apiService.calculateRiskReward({
        entryPrice: rrInput.entryPrice,
        stopLoss: rrInput.stopLoss,
        takeProfit: rrInput.takeProfit,
        accountBalance: rrInput.accountBalance,
        riskPercent: rrInput.riskPercent
      });

      if (result.analysis) {
        setRrResult(result.analysis);
        toast.success(`R:R Ratio: 1:${result.analysis.riskRewardRatio?.toFixed(2) || "N/A"}`);
      }
    } catch (error) {
      console.error("R:R calculation error:", error);
      toast.error("Failed to calculate R:R. Using local calculation.");

      // Fallback local calculation
      const risk = Math.abs(rrInput.entryPrice - rrInput.stopLoss);
      const reward = Math.abs(rrInput.takeProfit - rrInput.entryPrice);
      const ratio = reward / risk;

      setRrResult({
        entryPrice: rrInput.entryPrice,
        stopLoss: rrInput.stopLoss,
        takeProfit: rrInput.takeProfit,
        riskAmount: risk,
        rewardAmount: reward,
        riskRewardRatio: ratio,
        riskPercent: (risk / rrInput.entryPrice) * 100,
        rewardPercent: (reward / rrInput.entryPrice) * 100,
        breakevenWinrate: 100 / (1 + ratio),
        expectedValue: (ratio * 0.5) - 0.5,
        rating: ratio >= 3 ? "excellent" : ratio >= 2 ? "good" : ratio >= 1.5 ? "acceptable" : "poor",
        notes: []
      });
    } finally {
      setIsCalculating(false);
    }
  };

  useEffect(() => {
    fetchRiskMetrics();
  }, []);

  const metrics = riskMetrics?.metrics || {
    riskStatus: "Low",
    totalExposure: 2.1,
    maxDrawdown: -3.2,
    sharpeRatio: 2.4,
    kellyFraction: 0.5,
    riskPerTrade: 2.0,
    maxPositionSize: 5.0,
    winRate: 67.8,
    avgRiskReward: 2.4,
    dailyLossLimit: 5.0,
    maxOpenPositions: 5,
    leverageLimit: 3
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center">
            <Shield className="w-8 h-8 mr-3 text-success" />
            Risk Management
          </h1>
          <p className="text-muted-foreground">Portfolio risk & position monitoring</p>
        </div>
        <Button onClick={fetchRiskMetrics} disabled={isLoading} variant="outline">
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 border-border bg-card">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">Risk Status</h3>
          <p className={`text-2xl font-bold ${metrics.riskStatus === "Low" ? "text-success" :
              metrics.riskStatus === "Medium" ? "text-warning" : "text-destructive"
            }`}>{metrics.riskStatus}</p>
          <Badge variant="outline" className={`mt-2 ${metrics.riskStatus === "Low" ? "bg-success/10 text-success border-success/20" :
              metrics.riskStatus === "Medium" ? "bg-warning/10 text-warning border-warning/20" :
                "bg-destructive/10 text-destructive border-destructive/20"
            }`}>
            <Shield className="w-3 h-3 mr-1" />
            {metrics.riskStatus === "Low" ? "Healthy" : metrics.riskStatus === "Medium" ? "Caution" : "Alert"}
          </Badge>
        </Card>

        <Card className="p-6 border-border bg-card">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">Total Exposure</h3>
          <p className="text-2xl font-bold text-foreground">{metrics.totalExposure}%</p>
          <Badge variant="outline" className="mt-2">of equity</Badge>
        </Card>

        <Card className="p-6 border-border bg-card">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">Max Drawdown</h3>
          <p className="text-2xl font-bold text-warning">{metrics.maxDrawdown}%</p>
          <Badge variant="outline" className="mt-2 bg-warning/10 text-warning border-warning/20">
            Within limits
          </Badge>
        </Card>

        <Card className="p-6 border-border bg-card">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">Sharpe Ratio</h3>
          <p className="text-2xl font-bold text-foreground">{metrics.sharpeRatio}</p>
          <Badge variant="outline" className={`mt-2 ${metrics.sharpeRatio >= 2 ? "bg-success/10 text-success border-success/20" :
              "bg-warning/10 text-warning border-warning/20"
            }`}>
            {metrics.sharpeRatio >= 2 ? "Excellent" : "Good"}
          </Badge>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 border-border bg-card">
          <h2 className="text-xl font-semibold text-foreground mb-4">Position Sizing</h2>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Kelly Fraction</span>
                <span className="text-sm font-semibold text-foreground">{metrics.kellyFraction}x (Half Kelly)</span>
              </div>
              <Progress value={metrics.kellyFraction * 100} className="h-2" />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Risk Per Trade</span>
                <span className="text-sm font-semibold text-foreground">{metrics.riskPerTrade}%</span>
              </div>
              <Progress value={metrics.riskPerTrade * 10} className="h-2" />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Max Position Size</span>
                <span className="text-sm font-semibold text-foreground">{metrics.maxPositionSize}%</span>
              </div>
              <Progress value={metrics.maxPositionSize * 10} className="h-2" />
            </div>

            <div className="pt-4 border-t border-border">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-secondary/50">
                  <p className="text-xs text-muted-foreground mb-1">Win Rate</p>
                  <p className="text-xl font-bold text-success">{metrics.winRate}%</p>
                </div>
                <div className="p-3 rounded-lg bg-secondary/50">
                  <p className="text-xs text-muted-foreground mb-1">Avg R:R</p>
                  <p className="text-xl font-bold text-foreground">{metrics.avgRiskReward}</p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-border bg-card">
          <h2 className="text-xl font-semibold text-foreground mb-4">Risk Alerts</h2>
          <div className="space-y-3">
            {alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border ${alert.severity === "warning"
                    ? "bg-warning/5 border-warning/20"
                    : alert.severity === "info"
                      ? "bg-accent/5 border-accent/20"
                      : "bg-success/5 border-success/20"
                  }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {alert.severity === "warning" && (
                      <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                    )}
                    {alert.severity === "info" && (
                      <TrendingDown className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
                    )}
                    {alert.severity === "success" && (
                      <Shield className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
                    )}
                    <p className="text-sm text-foreground">{alert.message}</p>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      alert.severity === "warning"
                        ? "border-warning text-warning"
                        : alert.severity === "info"
                          ? "border-accent text-accent"
                          : "border-success text-success"
                    }
                  >
                    {alert.action}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* R:R Calculator Section */}
      <Card className="p-6 border-border bg-card">
        <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
          <Calculator className="w-5 h-5 text-primary" />
          Risk:Reward Calculator
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Section */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs">Entry Price</Label>
                <Input
                  type="number"
                  value={rrInput.entryPrice}
                  onChange={(e) => setRrInput(prev => ({ ...prev, entryPrice: parseFloat(e.target.value) }))}
                />
              </div>
              <div>
                <Label className="text-xs">Account Balance</Label>
                <Input
                  type="number"
                  value={rrInput.accountBalance}
                  onChange={(e) => setRrInput(prev => ({ ...prev, accountBalance: parseFloat(e.target.value) }))}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs text-destructive">Stop Loss</Label>
                <Input
                  type="number"
                  value={rrInput.stopLoss}
                  onChange={(e) => setRrInput(prev => ({ ...prev, stopLoss: parseFloat(e.target.value) }))}
                  className="border-destructive/30"
                />
              </div>
              <div>
                <Label className="text-xs text-success">Take Profit</Label>
                <Input
                  type="number"
                  value={rrInput.takeProfit}
                  onChange={(e) => setRrInput(prev => ({ ...prev, takeProfit: parseFloat(e.target.value) }))}
                  className="border-success/30"
                />
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-1">
                <Label className="text-xs">Risk %</Label>
                <Input
                  type="number"
                  value={rrInput.riskPercent}
                  onChange={(e) => setRrInput(prev => ({ ...prev, riskPercent: parseFloat(e.target.value) }))}
                  step="0.1"
                />
              </div>
              <div className="flex-1">
                <Label className="text-xs">Direction</Label>
                <select
                  value={rrInput.direction}
                  onChange={(e) => setRrInput(prev => ({ ...prev, direction: e.target.value }))}
                  className="w-full h-10 px-3 border border-border rounded-md bg-background"
                >
                  <option value="LONG">LONG</option>
                  <option value="SHORT">SHORT</option>
                </select>
              </div>
            </div>

            <Button onClick={calculateRR} disabled={isCalculating} className="w-full">
              <Target className="w-4 h-4 mr-2" />
              {isCalculating ? "Calculating..." : "Calculate R:R"}
            </Button>
          </div>

          {/* Result Section */}
          <div className="p-4 bg-secondary/30 rounded-lg">
            {rrResult ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-lg font-semibold">Risk:Reward Ratio</span>
                  <Badge className={`text-lg px-4 py-1 ${rrResult.riskRewardRatio >= 3 ? "bg-success" :
                      rrResult.riskRewardRatio >= 2 ? "bg-primary" :
                        rrResult.riskRewardRatio >= 1.5 ? "bg-warning" : "bg-destructive"
                    }`}>
                    1:{rrResult.riskRewardRatio?.toFixed(2)}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-destructive/10 rounded">
                    <p className="text-xs text-muted-foreground">Risk Amount</p>
                    <p className="text-lg font-bold text-destructive">${rrResult.riskAmount?.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">{rrResult.riskPercent?.toFixed(2)}%</p>
                  </div>
                  <div className="p-3 bg-success/10 rounded">
                    <p className="text-xs text-muted-foreground">Reward Amount</p>
                    <p className="text-lg font-bold text-success">${rrResult.rewardAmount?.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">{rrResult.rewardPercent?.toFixed(2)}%</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Breakeven Win Rate</p>
                    <p className="text-lg font-bold">{rrResult.breakevenWinrate?.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded">
                    <p className="text-xs text-muted-foreground">Rating</p>
                    <Badge variant="outline" className={`mt-1 ${rrResult.rating === "excellent" ? "border-success text-success" :
                        rrResult.rating === "good" ? "border-primary text-primary" :
                          rrResult.rating === "acceptable" ? "border-warning text-warning" :
                            "border-destructive text-destructive"
                      }`}>
                      {rrResult.rating?.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calculator className="w-12 h-12 mx-auto mb-4 opacity-20" />
                <p>Enter trade parameters and click Calculate</p>
              </div>
            )}
          </div>
        </div>
      </Card>

      <Card className="p-6 border-border bg-card">
        <h2 className="text-xl font-semibold text-foreground mb-4">Equity Curve</h2>
        <div className="bg-secondary/30 rounded-lg h-[300px] flex items-center justify-center border border-border">
          <div className="text-center space-y-4">
            <TrendingUp className="w-16 h-16 text-muted-foreground mx-auto" />
            <div>
              <p className="text-lg font-semibold text-foreground">Performance Chart</p>
              <p className="text-sm text-muted-foreground">
                Historical equity and drawdown visualization
              </p>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-4">Stop Loss Settings</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">ATR Multiplier</span>
              <span className="font-semibold text-foreground">2.0x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max SL %</span>
              <span className="font-semibold text-foreground">3.0%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Trailing Stop</span>
              <span className="font-semibold text-success">Active</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-4">Correlation Matrix</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">EURUSD-GBPUSD</span>
              <span className="font-semibold text-foreground">0.85</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">BTC-ETH</span>
              <span className="font-semibold text-foreground">0.92</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">GOLD-USD</span>
              <span className="font-semibold text-foreground">-0.65</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-4">Risk Limits</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Daily Loss Limit</span>
              <span className="font-semibold text-foreground">{metrics.dailyLossLimit}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Open Positions</span>
              <span className="font-semibold text-foreground">{metrics.maxOpenPositions}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Leverage</span>
              <span className="font-semibold text-foreground">1:{metrics.leverageLimit}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Risk;
