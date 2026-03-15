import { useState, useEffect, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Target,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  Award,
  AlertTriangle,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { DetectedPattern, PATTERN_TYPES } from "@/lib/patternUtils";

interface TrackedPattern {
  id: string;
  pattern: DetectedPattern;
  entryPrice: number;
  currentPrice: number;
  targetPrice: number;
  stopLoss: number;
  result: "pending" | "success" | "failure";
  pnlPercent: number;
  trackedAt: Date;
  resolvedAt?: Date;
}

interface PatternAccuracyTrackerProps {
  patterns: DetectedPattern[];
  currentPrice: number;
  instrument: string;
}

export const PatternAccuracyTracker = ({
  patterns,
  currentPrice,
  instrument,
}: PatternAccuracyTrackerProps) => {
  const [trackedPatterns, setTrackedPatterns] = useState<TrackedPattern[]>([]);
  const [activeTab, setActiveTab] = useState("overview");

  // Auto-track new high-confidence patterns
  useEffect(() => {
    const highConfPatterns = patterns.filter(
      (p) => p.confidence >= 0.75 && !trackedPatterns.some((tp) => tp.pattern.id === p.id)
    );

    if (highConfPatterns.length > 0) {
      const newTracked = highConfPatterns.map((pattern) => {
        const isBullish = pattern.signal === "Bullish";
        const targetMultiplier = isBullish ? 1.02 + pattern.confidence * 0.03 : 0.98 - pattern.confidence * 0.03;
        const stopMultiplier = isBullish ? 0.985 : 1.015;

        return {
          id: `track-${pattern.id}`,
          pattern,
          entryPrice: currentPrice,
          currentPrice,
          targetPrice: Number((currentPrice * targetMultiplier).toFixed(2)),
          stopLoss: Number((currentPrice * stopMultiplier).toFixed(2)),
          result: "pending" as const,
          pnlPercent: 0,
          trackedAt: new Date(),
        };
      });

      setTrackedPatterns((prev) => [...prev, ...newTracked]);
    }
  }, [patterns, currentPrice, trackedPatterns]);

  // Update tracked patterns with current price
  useEffect(() => {
    setTrackedPatterns((prev) =>
      prev.map((tp) => {
        if (tp.result !== "pending") return tp;

        const isBullish = tp.pattern.signal === "Bullish";
        const pnlPercent = ((currentPrice - tp.entryPrice) / tp.entryPrice) * 100;
        
        let result: "pending" | "success" | "failure" = "pending";
        
        if (isBullish) {
          if (currentPrice >= tp.targetPrice) result = "success";
          else if (currentPrice <= tp.stopLoss) result = "failure";
        } else {
          if (currentPrice <= tp.targetPrice) result = "success";
          else if (currentPrice >= tp.stopLoss) result = "failure";
        }

        return {
          ...tp,
          currentPrice,
          pnlPercent: Number(pnlPercent.toFixed(2)),
          result,
          resolvedAt: result !== "pending" ? new Date() : undefined,
        };
      })
    );
  }, [currentPrice]);

  // Statistics
  const stats = useMemo(() => {
    const total = trackedPatterns.length;
    const pending = trackedPatterns.filter((tp) => tp.result === "pending").length;
    const success = trackedPatterns.filter((tp) => tp.result === "success").length;
    const failure = trackedPatterns.filter((tp) => tp.result === "failure").length;
    const resolved = success + failure;
    const winRate = resolved > 0 ? (success / resolved) * 100 : 0;
    
    const avgPnL = resolved > 0
      ? trackedPatterns
          .filter((tp) => tp.result !== "pending")
          .reduce((sum, tp) => sum + tp.pnlPercent, 0) / resolved
      : 0;

    return { total, pending, success, failure, resolved, winRate, avgPnL };
  }, [trackedPatterns]);

  // Stats by pattern type
  const statsByType = useMemo(() => {
    return PATTERN_TYPES.map((type) => {
      const typePatterns = trackedPatterns.filter((tp) => tp.pattern.type === type);
      const resolved = typePatterns.filter((tp) => tp.result !== "pending");
      const success = resolved.filter((tp) => tp.result === "success").length;
      const winRate = resolved.length > 0 ? (success / resolved.length) * 100 : 0;

      return {
        type,
        total: typePatterns.length,
        resolved: resolved.length,
        success,
        winRate: Number(winRate.toFixed(1)),
      };
    }).filter((s) => s.total > 0);
  }, [trackedPatterns]);

  // Stats by signal type
  const statsBySignal = useMemo(() => {
    const signals = ["Bullish", "Bearish", "Neutral"] as const;
    return signals.map((signal) => {
      const signalPatterns = trackedPatterns.filter((tp) => tp.pattern.signal === signal);
      const resolved = signalPatterns.filter((tp) => tp.result !== "pending");
      const success = resolved.filter((tp) => tp.result === "success").length;
      const winRate = resolved.length > 0 ? (success / resolved.length) * 100 : 0;

      return {
        signal,
        total: signalPatterns.length,
        resolved: resolved.length,
        success,
        failure: resolved.length - success,
        winRate: Number(winRate.toFixed(1)),
      };
    }).filter((s) => s.total > 0);
  }, [trackedPatterns]);

  // Chart data for pie chart
  const pieData = [
    { name: "Success", value: stats.success, color: "hsl(var(--success))" },
    { name: "Failure", value: stats.failure, color: "hsl(var(--destructive))" },
    { name: "Pending", value: stats.pending, color: "hsl(var(--muted))" },
  ].filter((d) => d.value > 0);

  const handleClearResolved = () => {
    setTrackedPatterns((prev) => prev.filter((tp) => tp.result === "pending"));
  };

  const handleRemovePattern = (id: string) => {
    setTrackedPatterns((prev) => prev.filter((tp) => tp.id !== id));
  };

  return (
    <Card className="border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/30 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-2">
            <Target className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Pattern Accuracy Tracker</h3>
            <p className="text-xs text-muted-foreground">
              Real-time tracking of pattern performance
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono">
            {instrument}
          </Badge>
          <Button variant="outline" size="sm" onClick={handleClearResolved}>
            <Trash2 className="mr-1 h-3 w-3" />
            Clear Resolved
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-3 p-4 md:grid-cols-4 lg:grid-cols-6">
        <Card className="flex items-center gap-3 border-border bg-muted/30 p-3">
          <div className="rounded-lg bg-primary/10 p-2">
            <BarChart3 className="h-4 w-4 text-primary" />
          </div>
          <div>
            <div className="text-lg font-bold text-foreground">{stats.total}</div>
            <div className="text-xs text-muted-foreground">Total Tracked</div>
          </div>
        </Card>
        
        <Card className="flex items-center gap-3 border-border bg-muted/30 p-3">
          <div className="rounded-lg bg-accent/10 p-2">
            <Clock className="h-4 w-4 text-accent" />
          </div>
          <div>
            <div className="text-lg font-bold text-accent">{stats.pending}</div>
            <div className="text-xs text-muted-foreground">Pending</div>
          </div>
        </Card>
        
        <Card className="flex items-center gap-3 border-border bg-muted/30 p-3">
          <div className="rounded-lg bg-success/10 p-2">
            <CheckCircle className="h-4 w-4 text-success" />
          </div>
          <div>
            <div className="text-lg font-bold text-success">{stats.success}</div>
            <div className="text-xs text-muted-foreground">Success</div>
          </div>
        </Card>
        
        <Card className="flex items-center gap-3 border-border bg-muted/30 p-3">
          <div className="rounded-lg bg-destructive/10 p-2">
            <XCircle className="h-4 w-4 text-destructive" />
          </div>
          <div>
            <div className="text-lg font-bold text-destructive">{stats.failure}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
        </Card>
        
        <Card className="flex items-center gap-3 border-border bg-muted/30 p-3">
          <div className="rounded-lg bg-success/10 p-2">
            <Award className="h-4 w-4 text-success" />
          </div>
          <div>
            <div className="text-lg font-bold text-success">{stats.winRate.toFixed(1)}%</div>
            <div className="text-xs text-muted-foreground">Win Rate</div>
          </div>
        </Card>
        
        <Card className="flex items-center gap-3 border-border bg-muted/30 p-3">
          <div className={`rounded-lg p-2 ${stats.avgPnL >= 0 ? "bg-success/10" : "bg-destructive/10"}`}>
            {stats.avgPnL >= 0 ? (
              <TrendingUp className="h-4 w-4 text-success" />
            ) : (
              <TrendingDown className="h-4 w-4 text-destructive" />
            )}
          </div>
          <div>
            <div className={`text-lg font-bold ${stats.avgPnL >= 0 ? "text-success" : "text-destructive"}`}>
              {stats.avgPnL >= 0 ? "+" : ""}{stats.avgPnL.toFixed(2)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg P&L</div>
          </div>
        </Card>
      </div>

      {/* Tabs Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="px-4 pb-4">
        <TabsList className="grid w-full grid-cols-3 bg-muted/50">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="patterns">Tracked Patterns</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-4 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Pie Chart */}
            <Card className="border-border bg-muted/20 p-4">
              <h4 className="mb-3 text-sm font-medium text-foreground">Result Distribution</h4>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            {/* Win Rate by Signal */}
            <Card className="border-border bg-muted/20 p-4">
              <h4 className="mb-3 text-sm font-medium text-foreground">Win Rate by Signal</h4>
              <div className="space-y-3">
                {statsBySignal.map((stat) => (
                  <div key={stat.signal}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        {stat.signal === "Bullish" ? (
                          <TrendingUp className="h-4 w-4 text-success" />
                        ) : stat.signal === "Bearish" ? (
                          <TrendingDown className="h-4 w-4 text-destructive" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="text-sm text-foreground">{stat.signal}</span>
                      </div>
                      <span className="text-sm font-medium text-foreground">
                        {stat.winRate}% ({stat.success}/{stat.resolved})
                      </span>
                    </div>
                    <Progress value={stat.winRate} className="h-2" />
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Win Rate by Pattern Type */}
          <Card className="border-border bg-muted/20 p-4">
            <h4 className="mb-3 text-sm font-medium text-foreground">Performance by Pattern Type</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={statsByType}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="type" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="winRate" name="Win Rate %" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        {/* Tracked Patterns Tab */}
        <TabsContent value="patterns" className="mt-4">
          <ScrollArea className="h-[400px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pattern</TableHead>
                  <TableHead>Signal</TableHead>
                  <TableHead>Entry</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Current</TableHead>
                  <TableHead>P&L</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trackedPatterns.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                      No patterns being tracked yet. High-confidence patterns will be auto-tracked.
                    </TableCell>
                  </TableRow>
                ) : (
                  trackedPatterns.map((tp) => (
                    <TableRow key={tp.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium text-foreground">{tp.pattern.name}</div>
                          <div className="text-xs text-muted-foreground">{tp.pattern.type}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            tp.pattern.signal === "Bullish"
                              ? "border-success/50 text-success"
                              : tp.pattern.signal === "Bearish"
                              ? "border-destructive/50 text-destructive"
                              : ""
                          }
                        >
                          {tp.pattern.signal}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-foreground">
                        ${tp.entryPrice.toLocaleString()}
                      </TableCell>
                      <TableCell className="font-mono text-foreground">
                        ${tp.targetPrice.toLocaleString()}
                      </TableCell>
                      <TableCell className="font-mono text-foreground">
                        ${tp.currentPrice.toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`font-mono font-medium ${
                            tp.pnlPercent >= 0 ? "text-success" : "text-destructive"
                          }`}
                        >
                          {tp.pnlPercent >= 0 ? "+" : ""}{tp.pnlPercent}%
                        </span>
                      </TableCell>
                      <TableCell>
                        {tp.result === "pending" ? (
                          <Badge variant="secondary" className="bg-accent/10 text-accent">
                            <Clock className="mr-1 h-3 w-3" />
                            Pending
                          </Badge>
                        ) : tp.result === "success" ? (
                          <Badge className="bg-success/10 text-success border-success/20">
                            <CheckCircle className="mr-1 h-3 w-3" />
                            Success
                          </Badge>
                        ) : (
                          <Badge className="bg-destructive/10 text-destructive border-destructive/20">
                            <XCircle className="mr-1 h-3 w-3" />
                            Failed
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => handleRemovePattern(tp.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </ScrollArea>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Confidence vs Win Rate Analysis */}
            <Card className="border-border bg-muted/20 p-4">
              <h4 className="mb-3 text-sm font-medium text-foreground">Confidence Correlation</h4>
              <div className="space-y-3">
                {[
                  { range: "90-100%", min: 0.9, max: 1 },
                  { range: "80-90%", min: 0.8, max: 0.9 },
                  { range: "75-80%", min: 0.75, max: 0.8 },
                ].map((conf) => {
                  const confPatterns = trackedPatterns.filter(
                    (tp) => tp.pattern.confidence >= conf.min && tp.pattern.confidence < conf.max
                  );
                  const resolved = confPatterns.filter((tp) => tp.result !== "pending");
                  const success = resolved.filter((tp) => tp.result === "success").length;
                  const winRate = resolved.length > 0 ? (success / resolved.length) * 100 : 0;

                  return (
                    <div key={conf.range}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-foreground">{conf.range} Confidence</span>
                        <span className="text-sm font-medium text-foreground">
                          {winRate.toFixed(1)}% win rate
                        </span>
                      </div>
                      <Progress value={winRate} className="h-2" />
                      <div className="text-xs text-muted-foreground mt-1">
                        {success}/{resolved.length} trades (of {confPatterns.length} total)
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            {/* Recent Performance */}
            <Card className="border-border bg-muted/20 p-4">
              <h4 className="mb-3 text-sm font-medium text-foreground">Recent Performance</h4>
              <ScrollArea className="h-[200px]">
                <div className="space-y-2">
                  {trackedPatterns
                    .filter((tp) => tp.result !== "pending")
                    .slice(-10)
                    .reverse()
                    .map((tp) => (
                      <div
                        key={tp.id}
                        className={`flex items-center justify-between rounded-lg border p-2 ${
                          tp.result === "success"
                            ? "border-success/30 bg-success/5"
                            : "border-destructive/30 bg-destructive/5"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {tp.result === "success" ? (
                            <CheckCircle className="h-4 w-4 text-success" />
                          ) : (
                            <XCircle className="h-4 w-4 text-destructive" />
                          )}
                          <span className="text-sm text-foreground">{tp.pattern.name}</span>
                        </div>
                        <span
                          className={`font-mono text-sm ${
                            tp.pnlPercent >= 0 ? "text-success" : "text-destructive"
                          }`}
                        >
                          {tp.pnlPercent >= 0 ? "+" : ""}{tp.pnlPercent}%
                        </span>
                      </div>
                    ))}
                </div>
              </ScrollArea>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
};
