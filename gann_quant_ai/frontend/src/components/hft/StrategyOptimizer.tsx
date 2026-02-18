import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Cpu,
  Play,
  Pause,
  RotateCcw,
  Zap,
  Target,
  TrendingUp,
  Settings,
  Search,
  Sparkles,
  BarChart3,
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Save,
  Download,
} from "lucide-react";
import { toast } from "sonner";

interface StrategyConfig {
  name: string;
  category: "gann" | "ehlers";
  enabled: boolean;
  weight: number;
  parameters: Record<string, number | boolean>;
}

interface OptimizationResult {
  id: string;
  strategyCombo: string[];
  parameters: Record<string, number>;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  totalTrades: number;
  netProfit: number;
  score: number;
}

interface StrategyOptimizerProps {
  config: Record<string, any>;
  updateConfig: (key: string, value: any) => void;
}

const GANN_STRATEGIES = [
  { id: "gannSquare9", name: "Square of 9", key: "useGannSquare9" },
  { id: "gannAngles", name: "Gann Angles/Fan", key: "useGannAngles" },
  { id: "gannTimeCycles", name: "Time Cycles", key: "useGannTimeCycles" },
  { id: "gannSR", name: "Support/Resistance", key: "useGannSR" },
  { id: "gannFibo", name: "Fibonacci", key: "useGannFibo" },
  { id: "gannWave", name: "Wave", key: "useGannWave" },
  { id: "gannHexagon", name: "Hexagon", key: "useGannHexagon" },
];

const EHLERS_STRATEGIES = [
  { id: "ehlersMAMAFAMA", name: "MAMA/FAMA", key: "useEhlersMAMAFAMA" },
  { id: "ehlersFisher", name: "Fisher Transform", key: "useEhlersFisher" },
  { id: "ehlersBandpass", name: "Bandpass Filter", key: "useEhlersBandpass" },
  { id: "ehlersSuperSmoother", name: "Super Smoother", key: "useEhlersSuperSmoother" },
  { id: "ehlersRoofing", name: "Roofing Filter", key: "useEhlersRoofing" },
  { id: "ehlersCyberCycle", name: "Cyber Cycle", key: "useEhlersCyberCycle" },
  { id: "ehlersDecycler", name: "Decycler", key: "useEhlersDecycler" },
  { id: "ehlersInstaTrend", name: "Instantaneous Trend", key: "useEhlersInstaTrend" },
  { id: "ehlersDominantCycle", name: "Dominant Cycle", key: "useEhlersDominantCycle" },
];

export const StrategyOptimizer = ({ config, updateConfig }: StrategyOptimizerProps) => {
  const [optimizationMode, setOptimizationMode] = useState<"manual" | "auto">("manual");
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationProgress, setOptimizationProgress] = useState(0);
  const [optimizationResults, setOptimizationResults] = useState<OptimizationResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<OptimizationResult | null>(null);
  const [expandedStrategies, setExpandedStrategies] = useState(true);

  // Manual combination settings
  const [manualWeights, setManualWeights] = useState<Record<string, number>>({});
  const [combineMode, setCombineMode] = useState<"and" | "or" | "weighted">("weighted");

  // Auto optimization settings
  const [autoSettings, setAutoSettings] = useState({
    populationSize: 50,
    generations: 100,
    mutationRate: 0.1,
    crossoverRate: 0.8,
    eliteCount: 5,
    objectiveFunction: "sharpe" as "sharpe" | "profit" | "winrate" | "combined",
    minStrategies: 2,
    maxStrategies: 5,
  });

  const getActiveStrategies = () => {
    const active: string[] = [];
    [...GANN_STRATEGIES, ...EHLERS_STRATEGIES].forEach((s) => {
      if (config[s.key]) active.push(s.name);
    });
    return active;
  };

  const startOptimization = () => {
    setIsOptimizing(true);
    setOptimizationProgress(0);
    setOptimizationResults([]);

    const activeStrategies = getActiveStrategies();
    if (activeStrategies.length < 2) {
      toast.error("Enable at least 2 strategies to optimize combinations");
      setIsOptimizing(false);
      return;
    }

    toast.info(`Starting ${optimizationMode} optimization...`);

    // Simulate optimization process
    const totalIterations = optimizationMode === "auto" ? autoSettings.generations : 20;
    let iteration = 0;

    const interval = setInterval(() => {
      iteration++;
      setOptimizationProgress((iteration / totalIterations) * 100);

      if (iteration >= totalIterations) {
        clearInterval(interval);
        generateResults(activeStrategies);
        setIsOptimizing(false);
        toast.success("Optimization complete!");
      }
    }, 100);
  };

  const generateResults = (strategies: string[]) => {
    const results: OptimizationResult[] = [];
    const numResults = 10;

    for (let i = 0; i < numResults; i++) {
      // Generate random combinations
      const numStrategies = Math.floor(Math.random() * 3) + 2;
      const shuffled = [...strategies].sort(() => Math.random() - 0.5);
      const combo = shuffled.slice(0, Math.min(numStrategies, shuffled.length));

      const winRate = 45 + Math.random() * 25;
      const profitFactor = 1 + Math.random() * 2;
      const sharpeRatio = 0.5 + Math.random() * 3;
      const maxDrawdown = 5 + Math.random() * 20;
      const totalTrades = Math.floor(500 + Math.random() * 1500);
      const netProfit = Math.floor(-5000 + Math.random() * 25000);

      const score =
        autoSettings.objectiveFunction === "sharpe"
          ? sharpeRatio
          : autoSettings.objectiveFunction === "profit"
          ? netProfit / 1000
          : autoSettings.objectiveFunction === "winrate"
          ? winRate
          : sharpeRatio * 0.4 + winRate * 0.3 + profitFactor * 0.3;

      results.push({
        id: `result-${i}`,
        strategyCombo: combo,
        parameters: {
          weight1: Math.random().toFixed(2) as unknown as number,
          weight2: Math.random().toFixed(2) as unknown as number,
        },
        winRate: parseFloat(winRate.toFixed(2)),
        profitFactor: parseFloat(profitFactor.toFixed(2)),
        sharpeRatio: parseFloat(sharpeRatio.toFixed(2)),
        maxDrawdown: parseFloat(maxDrawdown.toFixed(2)),
        totalTrades,
        netProfit,
        score: parseFloat(score.toFixed(2)),
      });
    }

    results.sort((a, b) => b.score - a.score);
    setOptimizationResults(results);
  };

  const applyResult = (result: OptimizationResult) => {
    // Disable all strategies first
    [...GANN_STRATEGIES, ...EHLERS_STRATEGIES].forEach((s) => {
      updateConfig(s.key, false);
    });

    // Enable strategies in the selected combination
    result.strategyCombo.forEach((strategyName) => {
      const strategy = [...GANN_STRATEGIES, ...EHLERS_STRATEGIES].find(
        (s) => s.name === strategyName
      );
      if (strategy) {
        updateConfig(strategy.key, true);
      }
    });

    toast.success(`Applied ${result.strategyCombo.length} strategies`);
  };

  const enableAllGann = () => {
    GANN_STRATEGIES.forEach((s) => updateConfig(s.key, true));
    toast.success("All Gann strategies enabled");
  };

  const enableAllEhlers = () => {
    EHLERS_STRATEGIES.forEach((s) => updateConfig(s.key, true));
    toast.success("All Ehlers strategies enabled");
  };

  const disableAll = () => {
    [...GANN_STRATEGIES, ...EHLERS_STRATEGIES].forEach((s) => updateConfig(s.key, false));
    toast.info("All strategies disabled");
  };

  return (
    <div className="space-y-4">
      {/* Mode Selection */}
      <div className="flex gap-2 mb-4">
        <Button
          variant={optimizationMode === "manual" ? "default" : "outline"}
          onClick={() => setOptimizationMode("manual")}
          className="flex-1"
        >
          <Settings className="w-4 h-4 mr-2" />
          Manual Combination
        </Button>
        <Button
          variant={optimizationMode === "auto" ? "default" : "outline"}
          onClick={() => setOptimizationMode("auto")}
          className="flex-1"
        >
          <Sparkles className="w-4 h-4 mr-2" />
          Auto Optimizer
        </Button>
      </div>

      {/* Quick Actions */}
      <Card className="p-4 border-border bg-card">
        <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-accent" />
          Quick Strategy Selection
        </h4>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={enableAllGann}>
            Enable All Gann
          </Button>
          <Button size="sm" variant="outline" onClick={enableAllEhlers}>
            Enable All Ehlers
          </Button>
          <Button size="sm" variant="destructive" onClick={disableAll}>
            Disable All
          </Button>
        </div>
      </Card>

      {/* Strategy Selection with Auto/Manual Toggle */}
      <Card className="p-4 border-border bg-card">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setExpandedStrategies(!expandedStrategies)}
        >
          <h4 className="font-semibold text-foreground flex items-center gap-2">
            <Target className="w-4 h-4 text-primary" />
            Strategy Selection
          </h4>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{getActiveStrategies().length} Active</Badge>
            {expandedStrategies ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </div>
        </div>

        {expandedStrategies && (
          <div className="mt-4 space-y-4">
            {/* Gann Strategies */}
            <div>
              <Label className="text-sm font-medium text-accent mb-2 block">W.D. Gann Strategies</Label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {GANN_STRATEGIES.map((strategy) => (
                  <div
                    key={strategy.id}
                    className={`p-2 rounded-lg border cursor-pointer transition-all ${
                      config[strategy.key]
                        ? "border-accent bg-accent/10"
                        : "border-border bg-secondary/30 hover:border-accent/50"
                    }`}
                    onClick={() => updateConfig(strategy.key, !config[strategy.key])}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{strategy.name}</span>
                      {config[strategy.key] ? (
                        <CheckCircle2 className="w-4 h-4 text-accent" />
                      ) : (
                        <XCircle className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Ehlers Strategies */}
            <div>
              <Label className="text-sm font-medium text-primary mb-2 block">Ehlers DSP Strategies</Label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {EHLERS_STRATEGIES.map((strategy) => (
                  <div
                    key={strategy.id}
                    className={`p-2 rounded-lg border cursor-pointer transition-all ${
                      config[strategy.key]
                        ? "border-primary bg-primary/10"
                        : "border-border bg-secondary/30 hover:border-primary/50"
                    }`}
                    onClick={() => updateConfig(strategy.key, !config[strategy.key])}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{strategy.name}</span>
                      {config[strategy.key] ? (
                        <CheckCircle2 className="w-4 h-4 text-primary" />
                      ) : (
                        <XCircle className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Manual Combination Settings */}
      {optimizationMode === "manual" && (
        <Card className="p-4 border-border bg-card">
          <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Settings className="w-4 h-4 text-primary" />
            Manual Combination Settings
          </h4>
          <div className="space-y-4">
            <div>
              <Label className="text-sm mb-2 block">Combine Mode</Label>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={combineMode === "and" ? "default" : "outline"}
                  onClick={() => setCombineMode("and")}
                >
                  AND (All signals)
                </Button>
                <Button
                  size="sm"
                  variant={combineMode === "or" ? "default" : "outline"}
                  onClick={() => setCombineMode("or")}
                >
                  OR (Any signal)
                </Button>
                <Button
                  size="sm"
                  variant={combineMode === "weighted" ? "default" : "outline"}
                  onClick={() => setCombineMode("weighted")}
                >
                  Weighted Average
                </Button>
              </div>
            </div>

            {combineMode === "weighted" && (
              <div>
                <Label className="text-sm mb-2 block">Strategy Weights</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {getActiveStrategies().map((strategy) => (
                    <div key={strategy} className="flex items-center gap-2">
                      <span className="text-xs flex-1">{strategy}</span>
                      <Input
                        type="number"
                        min={0}
                        max={1}
                        step={0.1}
                        value={manualWeights[strategy] || 1}
                        onChange={(e) =>
                          setManualWeights((prev) => ({
                            ...prev,
                            [strategy]: parseFloat(e.target.value),
                          }))
                        }
                        className="w-16 h-8 text-xs"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Auto Optimizer Settings */}
      {optimizationMode === "auto" && (
        <Card className="p-4 border-border bg-card">
          <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-accent" />
            Auto Optimizer Settings (Genetic Algorithm)
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label className="text-xs">Population Size</Label>
              <Input
                type="number"
                value={autoSettings.populationSize}
                onChange={(e) =>
                  setAutoSettings((prev) => ({ ...prev, populationSize: parseInt(e.target.value) }))
                }
                className="h-8"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Generations</Label>
              <Input
                type="number"
                value={autoSettings.generations}
                onChange={(e) =>
                  setAutoSettings((prev) => ({ ...prev, generations: parseInt(e.target.value) }))
                }
                className="h-8"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Mutation Rate</Label>
              <Input
                type="number"
                step={0.01}
                value={autoSettings.mutationRate}
                onChange={(e) =>
                  setAutoSettings((prev) => ({ ...prev, mutationRate: parseFloat(e.target.value) }))
                }
                className="h-8"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Crossover Rate</Label>
              <Input
                type="number"
                step={0.1}
                value={autoSettings.crossoverRate}
                onChange={(e) =>
                  setAutoSettings((prev) => ({ ...prev, crossoverRate: parseFloat(e.target.value) }))
                }
                className="h-8"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Min Strategies</Label>
              <Input
                type="number"
                min={1}
                max={10}
                value={autoSettings.minStrategies}
                onChange={(e) =>
                  setAutoSettings((prev) => ({ ...prev, minStrategies: parseInt(e.target.value) }))
                }
                className="h-8"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Max Strategies</Label>
              <Input
                type="number"
                min={2}
                max={16}
                value={autoSettings.maxStrategies}
                onChange={(e) =>
                  setAutoSettings((prev) => ({ ...prev, maxStrategies: parseInt(e.target.value) }))
                }
                className="h-8"
              />
            </div>
            <div className="space-y-2 col-span-2">
              <Label className="text-xs">Objective Function</Label>
              <div className="flex gap-2 flex-wrap">
                {(["sharpe", "profit", "winrate", "combined"] as const).map((obj) => (
                  <Button
                    key={obj}
                    size="sm"
                    variant={autoSettings.objectiveFunction === obj ? "default" : "outline"}
                    onClick={() => setAutoSettings((prev) => ({ ...prev, objectiveFunction: obj }))}
                    className="text-xs"
                  >
                    {obj === "sharpe"
                      ? "Sharpe Ratio"
                      : obj === "profit"
                      ? "Net Profit"
                      : obj === "winrate"
                      ? "Win Rate"
                      : "Combined"}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Optimization Control */}
      <Card className="p-4 border-border bg-card">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-foreground flex items-center gap-2">
            <Activity className="w-4 h-4 text-success" />
            Optimization Control
          </h4>
          <Badge variant="outline">
            {isOptimizing ? "Running..." : optimizationResults.length > 0 ? "Complete" : "Ready"}
          </Badge>
        </div>

        {isOptimizing && (
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span>Progress</span>
              <span>{optimizationProgress.toFixed(0)}%</span>
            </div>
            <Progress value={optimizationProgress} className="h-2" />
          </div>
        )}

        <div className="flex gap-2">
          <Button
            onClick={startOptimization}
            disabled={isOptimizing}
            className="flex-1"
          >
            {isOptimizing ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Start Optimization
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              setOptimizationResults([]);
              setOptimizationProgress(0);
            }}
            disabled={isOptimizing}
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>
      </Card>

      {/* Optimization Results */}
      {optimizationResults.length > 0 && (
        <Card className="p-4 border-border bg-card">
          <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-primary" />
            Optimization Results (Top 10)
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-secondary/50">
                <tr>
                  <th className="px-3 py-2 text-left">Rank</th>
                  <th className="px-3 py-2 text-left">Strategy Combination</th>
                  <th className="px-3 py-2 text-right">Win Rate</th>
                  <th className="px-3 py-2 text-right">Profit Factor</th>
                  <th className="px-3 py-2 text-right">Sharpe</th>
                  <th className="px-3 py-2 text-right">Max DD</th>
                  <th className="px-3 py-2 text-right">Score</th>
                  <th className="px-3 py-2 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {optimizationResults.map((result, idx) => (
                  <tr
                    key={result.id}
                    className={`${
                      idx % 2 === 0 ? "bg-card" : "bg-secondary/20"
                    } hover:bg-secondary/40 cursor-pointer`}
                    onClick={() => setSelectedResult(result)}
                  >
                    <td className="px-3 py-2 font-bold text-foreground">#{idx + 1}</td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap gap-1">
                        {result.strategyCombo.map((s) => (
                          <Badge key={s} variant="outline" className="text-xs">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="px-3 py-2 text-right font-mono">{result.winRate}%</td>
                    <td className="px-3 py-2 text-right font-mono">{result.profitFactor}</td>
                    <td className="px-3 py-2 text-right font-mono">{result.sharpeRatio}</td>
                    <td className="px-3 py-2 text-right font-mono text-destructive">
                      {result.maxDrawdown}%
                    </td>
                    <td className="px-3 py-2 text-right font-bold text-success">{result.score}</td>
                    <td className="px-3 py-2 text-center">
                      <Button size="sm" variant="outline" onClick={() => applyResult(result)}>
                        Apply
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
