import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Box, RefreshCw } from "lucide-react";
import { calculateGannBoxLevels } from "@/lib/gannCalculations";

const TIMEFRAMES = [
  { value: "1m", label: "1 Minute" },
  { value: "2m", label: "2 Minutes" },
  { value: "3m", label: "3 Minutes" },
  { value: "5m", label: "5 Minutes" },
  { value: "10m", label: "10 Minutes" },
  { value: "15m", label: "15 Minutes" },
  { value: "30m", label: "30 Minutes" },
  { value: "45m", label: "45 Minutes" },
  { value: "1h", label: "1 Hour" },
  { value: "2h", label: "2 Hours" },
  { value: "3h", label: "3 Hours" },
  { value: "4h", label: "4 Hours" },
  { value: "1d", label: "1 Day" },
  { value: "1w", label: "1 Week" },
  { value: "1mo", label: "1 Month" },
  { value: "1y", label: "1 Year" },
];

const GANN_ANGLES = [
  { degree: 0, label: "0°", type: "cardinal" },
  { degree: 15, label: "15°", type: "minor" },
  { degree: 30, label: "30°", type: "minor" },
  { degree: 45, label: "45°", type: "diagonal" },
  { degree: 60, label: "60°", type: "minor" },
  { degree: 75, label: "75°", type: "minor" },
  { degree: 90, label: "90°", type: "cardinal" },
  { degree: 105, label: "105°", type: "minor" },
  { degree: 120, label: "120°", type: "minor" },
  { degree: 135, label: "135°", type: "diagonal" },
  { degree: 150, label: "150°", type: "minor" },
  { degree: 165, label: "165°", type: "minor" },
  { degree: 180, label: "180°", type: "cardinal" },
  { degree: 195, label: "195°", type: "minor" },
  { degree: 210, label: "210°", type: "minor" },
  { degree: 225, label: "225°", type: "diagonal" },
  { degree: 240, label: "240°", type: "minor" },
  { degree: 255, label: "255°", type: "minor" },
  { degree: 270, label: "270°", type: "cardinal" },
  { degree: 285, label: "285°", type: "minor" },
  { degree: 300, label: "300°", type: "minor" },
  { degree: 315, label: "315°", type: "diagonal" },
  { degree: 330, label: "330°", type: "minor" },
  { degree: 345, label: "345°", type: "minor" },
  { degree: 360, label: "360°", type: "cardinal" },
];

interface GannBoxChartProps {
  basePrice?: number;
  periodHigh?: number;
  periodLow?: number;
}

export const GannBoxChart = ({ basePrice = 100, periodHigh, periodLow }: GannBoxChartProps) => {
  const [price, setPrice] = useState(basePrice.toString());
  const [high, setHigh] = useState(periodHigh?.toString() || (basePrice * 1.05).toFixed(2));
  const [low, setLow] = useState(periodLow?.toString() || (basePrice * 0.95).toFixed(2));
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>(["1h", "4h", "1d"]);
  const [isAutoMode, setIsAutoMode] = useState(true);
  const [boxLevels, setBoxLevels] = useState<{ degree: number; price: number; type: string }[]>([]);
  const [octaveLevels, setOctaveLevels] = useState<Record<string, number>>({});

  useEffect(() => {
    calculateGannBox();
  }, []);

  useEffect(() => {
    if (isAutoMode) {
      if (basePrice) setPrice(basePrice.toString());
      if (periodHigh) setHigh(periodHigh.toString());
      if (periodLow) setLow(periodLow.toString());
    }
  }, [basePrice, periodHigh, periodLow, isAutoMode]);

  useEffect(() => {
    calculateGannBox();
  }, [price, high, low]);

  const calculateGannBox = () => {
    const priceValue = parseFloat(price) || 100;
    const highValue = parseFloat(high) || priceValue * 1.05;
    const lowValue = parseFloat(low) || priceValue * 0.95;

    const sqrtPrice = Math.sqrt(priceValue);

    const levels = GANN_ANGLES.map((angle) => {
      const radians = (angle.degree * Math.PI) / 180;
      const priceLevel = Math.pow(sqrtPrice + radians / (2 * Math.PI), 2);
      return {
        degree: angle.degree,
        price: priceLevel,
        type: angle.type,
      };
    });

    setBoxLevels(levels);
    setOctaveLevels(calculateGannBoxLevels(highValue, lowValue));
  };

  const toggleTimeframe = (tf: string) => {
    setSelectedTimeframes((prev) =>
      prev.includes(tf) ? prev.filter((t) => t !== tf) : [...prev, tf]
    );
  };

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3 border-b border-border/50 mb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Box className="h-5 w-5 text-primary" />
            Gann Box 0-360° Multi-Timeframe
          </CardTitle>
          <div className="flex items-center bg-secondary/50 p-1 rounded-lg border border-border/50">
            <Button
              variant={!isAutoMode ? "default" : "ghost"}
              size="sm"
              onClick={() => setIsAutoMode(false)}
              className="h-8 text-xs px-3"
            >
              Manual
            </Button>
            <Button
              variant={isAutoMode ? "default" : "ghost"}
              size="sm"
              onClick={() => setIsAutoMode(true)}
              className="h-8 text-xs px-3"
            >
              Automatic
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Base Price</Label>
              {isAutoMode && <Badge variant="outline" className="text-[10px] h-4 bg-primary/10 text-primary border-primary/20">LIVE</Badge>}
            </div>
            <Input
              type="number"
              value={price}
              onChange={(e) => !isAutoMode && setPrice(e.target.value)}
              placeholder="Base"
              readOnly={isAutoMode}
              className={isAutoMode ? "bg-primary/5 border-primary/20 text-primary font-bold" : ""}
            />
          </div>
          <div className="space-y-2">
            <Label>Period High</Label>
            <Input
              type="number"
              value={high}
              onChange={(e) => !isAutoMode && setHigh(e.target.value)}
              placeholder="High"
              readOnly={isAutoMode}
              className={isAutoMode ? "bg-primary/5 border-primary/20 text-primary font-medium" : ""}
            />
          </div>
          <div className="space-y-2">
            <Label>Period Low</Label>
            <Input
              type="number"
              value={low}
              onChange={(e) => !isAutoMode && setLow(e.target.value)}
              placeholder="Low"
              readOnly={isAutoMode}
              className={isAutoMode ? "bg-primary/5 border-primary/20 text-primary font-medium" : ""}
            />
          </div>
        </div>

        <Button onClick={calculateGannBox} className="w-full" variant={isAutoMode ? "outline" : "default"}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isAutoMode ? "animate-spin" : ""}`} />
          {isAutoMode ? "Auto-Updating Calculations..." : "Calculate Box Levels"}
        </Button>

        <div className="space-y-2">
          <Label>Active Timeframes</Label>
          <div className="flex flex-wrap gap-2">
            {TIMEFRAMES.map((tf) => (
              <Badge
                key={tf.value}
                variant={selectedTimeframes.includes(tf.value) ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => toggleTimeframe(tf.value)}
              >
                {tf.label}
              </Badge>
            ))}
          </div>
        </div>

        {/* Gann Box Visualization */}
        <div className="relative aspect-square bg-background/50 rounded-lg border border-border/50 overflow-hidden">
          <svg viewBox="0 0 200 200" className="w-full h-full">
            {/* Background grid */}
            {GANN_ANGLES.slice(0, -1).map((angle) => {
              const radians = (angle.degree * Math.PI) / 180;
              const x2 = 100 + 90 * Math.cos(radians);
              const y2 = 100 + 90 * Math.sin(radians);
              return (
                <line
                  key={angle.degree}
                  x1="100"
                  y1="100"
                  x2={x2}
                  y2={y2}
                  stroke="hsl(var(--border))"
                  strokeWidth={angle.type === "minor" ? "0.2" : "0.5"}
                  strokeDasharray={angle.type === "minor" ? "1,1" : "2,2"}
                />
              );
            })}

            {/* Concentric circles */}
            {[20, 40, 60, 80].map((r) => (
              <circle
                key={r}
                cx="100"
                cy="100"
                r={r}
                fill="none"
                stroke="hsl(var(--border))"
                strokeWidth="0.5"
                strokeDasharray="2,2"
              />
            ))}

            {/* Gann Box */}
            <rect
              x="20"
              y="20"
              width="160"
              height="160"
              fill="none"
              stroke="hsl(var(--primary))"
              strokeWidth="2"
            />

            {/* Diagonal lines */}
            <line x1="20" y1="20" x2="180" y2="180" stroke="hsl(var(--primary))" strokeWidth="1" />
            <line x1="180" y1="20" x2="20" y2="180" stroke="hsl(var(--primary))" strokeWidth="1" />

            {/* Mid lines */}
            <line x1="100" y1="20" x2="100" y2="180" stroke="hsl(var(--accent))" strokeWidth="1" />
            <line x1="20" y1="100" x2="180" y2="100" stroke="hsl(var(--accent))" strokeWidth="1" />

            {/* Degree labels */}
            {GANN_ANGLES.slice(0, -1).map((angle) => {
              const radians = ((angle.degree - 90) * Math.PI) / 180;
              const x = 100 + 95 * Math.cos(radians);
              const y = 100 + 95 * Math.sin(radians);
              return (
                <text
                  key={angle.degree}
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="fill-muted-foreground text-[6px]"
                >
                  {angle.label}
                </text>
              );
            })}

            {/* Center price */}
            <text
              x="100"
              y="100"
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-primary text-[10px] font-bold"
            >
              {parseFloat(price).toFixed(2)}
            </text>
          </svg>
        </div>

        {/* Price Levels Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Degree based levels */}
          {boxLevels.length > 0 && (
            <div className="space-y-2">
              <Label>Gann Degree Levels (Square of 9)</Label>
              <div className="grid grid-cols-3 gap-2 text-sm">
                {boxLevels.map((level) => (
                  <div
                    key={level.degree}
                    className={`p-3 rounded border ${level.type === "cardinal"
                      ? "bg-primary/10 border-primary/30 font-bold"
                      : level.type === "diagonal"
                        ? "bg-accent/10 border-accent/30 font-medium"
                        : "bg-secondary/20 border-border/30 opacity-80"
                      }`}
                  >
                    <div className="flex justify-between items-center gap-1">
                      <span>{level.degree}°</span>
                      <span className="font-mono">{level.price.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Octave based levels */}
          {Object.keys(octaveLevels).length > 0 && (
            <div className="space-y-2">
              <Label>Gann Box Octaves (Price Range)</Label>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                {Object.entries(octaveLevels).map(([label, val]) => (
                  <div
                    key={label}
                    className="p-1.5 rounded border border-border bg-secondary/30"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-semibold">{label}</span>
                      <span className="font-mono">{val.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Timeframe Status */}
        <div className="space-y-2">
          <Label>Timeframe Analysis Status</Label>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {selectedTimeframes.map((tf) => {
              const tfData = TIMEFRAMES.find((t) => t.value === tf);
              const signal = Math.random() > 0.5 ? "bullish" : "bearish";
              return (
                <div key={tf} className="p-2 rounded bg-secondary/50 border border-border/50">
                  <div className="font-medium">{tfData?.label}</div>
                  <Badge variant={signal === "bullish" ? "default" : "destructive"} className="text-[10px]">
                    {signal.toUpperCase()}
                  </Badge>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
