import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Calculator, TrendingUp, TrendingDown, AlertCircle } from "lucide-react";
import { calculateMAMAFAMA, detectMAMACrossovers } from "@/lib/ehlersCalculations";
import { toast } from "sonner";

const MAMAFAMACalculator = () => {
  const [priceData, setPriceData] = useState<string>("");
  const [fastLimit, setFastLimit] = useState<number>(0.5);
  const [slowLimit, setSlowLimit] = useState<number>(0.05);
  const [results, setResults] = useState<any>(null);

  const handleCalculate = () => {
    try {
      // Parse price data
      const prices = priceData
        .split(',')
        .map(p => parseFloat(p.trim()))
        .filter(p => !isNaN(p));

      if (prices.length < 6) {
        toast.error("Please enter at least 6 price values separated by commas");
        return;
      }

      if (fastLimit <= slowLimit) {
        toast.error("Fast limit must be greater than slow limit");
        return;
      }

      // Calculate MAMA/FAMA
      const mamaFamaResults = calculateMAMAFAMA(prices, fastLimit, slowLimit);
      const crossovers = detectMAMACrossovers(mamaFamaResults);

      const latestResult = mamaFamaResults[mamaFamaResults.length - 1];
      const previousResult = mamaFamaResults[mamaFamaResults.length - 2];

      setResults({
        mama: latestResult.mama,
        fama: latestResult.fama,
        phase: latestResult.phase,
        period: latestResult.period,
        trend: latestResult.mama > latestResult.fama ? 'bullish' : 'bearish',
        crossovers: crossovers.length,
        lastCrossover: crossovers.length > 0 ? crossovers[crossovers.length - 1] : null,
        momentum: latestResult.mama - previousResult.mama
      });

      toast.success("MAMA/FAMA calculated successfully!");
    } catch (error) {
      toast.error("Calculation error. Please check your input.");
    }
  };

  return (
    <Card className="p-6 border-border bg-card">
      <div className="flex items-center gap-2 mb-6">
        <Calculator className="w-5 h-5 text-accent" />
        <h3 className="text-lg font-semibold text-foreground">MAMA/FAMA Calculator</h3>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="priceData" className="text-foreground">
            Price Data (comma-separated)
          </Label>
          <Input
            id="priceData"
            placeholder="104.2, 104.5, 104.3, 104.7, 104.9, 105.1, 105.0..."
            value={priceData}
            onChange={(e) => setPriceData(e.target.value)}
            className="font-mono"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Enter at least 6 price values separated by commas
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="fastLimit" className="text-foreground flex justify-between">
              <span>Fast Limit</span>
              <span className="font-mono text-accent">{fastLimit.toFixed(2)}</span>
            </Label>
            <Slider
              id="fastLimit"
              min={0.1}
              max={1.0}
              step={0.01}
              value={[fastLimit]}
              onValueChange={(value) => setFastLimit(value[0])}
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Higher = More responsive (0.1 - 1.0)
            </p>
          </div>

          <div>
            <Label htmlFor="slowLimit" className="text-foreground flex justify-between">
              <span>Slow Limit</span>
              <span className="font-mono text-accent">{slowLimit.toFixed(3)}</span>
            </Label>
            <Slider
              id="slowLimit"
              min={0.01}
              max={0.2}
              step={0.001}
              value={[slowLimit]}
              onValueChange={(value) => setSlowLimit(value[0])}
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Lower = More stable (0.01 - 0.2)
            </p>
          </div>
        </div>

        <Button onClick={handleCalculate} className="w-full">
          <Calculator className="w-4 h-4 mr-2" />
          Calculate MAMA/FAMA
        </Button>
      </div>

      {results && (
        <div className="mt-6 space-y-4">
          <div className="p-4 rounded-lg border-2 border-accent bg-accent/5">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-foreground">Results</h4>
              <Badge
                variant={results.trend === 'bullish' ? 'default' : 'destructive'}
                className="flex items-center gap-1"
              >
                {results.trend === 'bullish' ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                {results.trend.toUpperCase()}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded bg-card border border-border">
                <p className="text-xs text-muted-foreground">MAMA</p>
                <p className="text-xl font-bold text-primary font-mono">
                  {results.mama.toFixed(4)}
                </p>
              </div>
              <div className="p-3 rounded bg-card border border-border">
                <p className="text-xs text-muted-foreground">FAMA</p>
                <p className="text-xl font-bold text-accent font-mono">
                  {results.fama.toFixed(4)}
                </p>
              </div>
              <div className="p-3 rounded bg-card border border-border">
                <p className="text-xs text-muted-foreground">Period</p>
                <p className="text-lg font-semibold text-foreground font-mono">
                  {results.period.toFixed(2)}
                </p>
              </div>
              <div className="p-3 rounded bg-card border border-border">
                <p className="text-xs text-muted-foreground">Phase</p>
                <p className="text-lg font-semibold text-foreground font-mono">
                  {results.phase.toFixed(2)}°
                </p>
              </div>
            </div>

            <div className="mt-3 p-3 rounded bg-muted/50">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-foreground">
                    <strong>Signal:</strong> MAMA is {results.mama > results.fama ? 'above' : 'below'} FAMA
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Total crossovers detected: {results.crossovers}
                  </p>
                  {results.lastCrossover && (
                    <p className="text-xs text-muted-foreground">
                      Last crossover: {results.lastCrossover.type} at index {results.lastCrossover.index}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Momentum: {results.momentum > 0 ? '+' : ''}{results.momentum.toFixed(4)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-secondary/30 border border-border">
            <h5 className="text-sm font-semibold text-foreground mb-2">Interpretation</h5>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• MAMA above FAMA = Bullish trend (Consider long positions)</li>
              <li>• MAMA below FAMA = Bearish trend (Consider short positions)</li>
              <li>• Crossovers indicate potential trend reversals</li>
              <li>• Adaptive period adjusts to market volatility</li>
            </ul>
          </div>
        </div>
      )}
    </Card>
  );
};

export default MAMAFAMACalculator;
