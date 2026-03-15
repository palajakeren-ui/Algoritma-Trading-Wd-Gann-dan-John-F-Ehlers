import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CalendarClock, TrendingUp, TrendingDown, Target, RefreshCw, Zap, Clock } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";

interface ForecastResult {
  year: number;
  date: Date;
  price: number;
  cycle: string;
  type: "peak" | "trough" | "neutral";
  confidence: number;
}

const CYCLE_TYPES = [
  { value: "major", label: "Major Cycle (20 Years)" },
  { value: "intermediate", label: "Intermediate (10 Years)" },
  { value: "minor", label: "Minor Cycle (5 Years)" },
  { value: "annual", label: "Annual Cycle" },
  { value: "quarterly", label: "Quarterly Cycle" },
  { value: "monthly", label: "Monthly Cycle" },
];

const YEAR_RANGES = [
  { value: "10", label: "10 Years" },
  { value: "25", label: "25 Years" },
  { value: "50", label: "50 Years" },
  { value: "100", label: "100 Years" },
  { value: "200", label: "200 Years" },
  { value: "365", label: "365 Years" },
];

interface GannForecastingCalculatorProps {
  currentPrice?: number;
  autoCalculate?: boolean;
}

export const GannForecastingCalculator = ({ currentPrice, autoCalculate = false }: GannForecastingCalculatorProps) => {
  const [basePrice, setBasePrice] = useState(currentPrice?.toString() || "100");
  const [startYear, setStartYear] = useState(new Date().getFullYear().toString());
  const [forecastRange, setForecastRange] = useState("100");
  const [cycleType, setCycleType] = useState("major");
  const [forecasts, setForecasts] = useState<ForecastResult[]>([]);
  const [isAutoMode, setIsAutoMode] = useState(autoCalculate);
  const [isCalculating, setIsCalculating] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Sync auto mode with prop
  useEffect(() => {
    setIsAutoMode(autoCalculate);
  }, [autoCalculate]);

  // Update base price when current price changes
  useEffect(() => {
    if (currentPrice && isAutoMode) {
      setBasePrice(currentPrice.toString());
    }
  }, [currentPrice, isAutoMode]);

  // Auto-calculate when in auto mode and price changes
  useEffect(() => {
    if (isAutoMode && basePrice) {
      const timer = setTimeout(() => {
        calculateForecasts();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [basePrice, forecastRange, cycleType, isAutoMode]);

  const calculateForecasts = () => {
    setIsCalculating(true);
    const price = parseFloat(basePrice) || 100;
    const start = parseInt(startYear) || new Date().getFullYear();
    const range = parseInt(forecastRange) || 100;

    const results: ForecastResult[] = [];

    // 1. Essential Gann Constants (Squares & Wheels)
    const gannSquares = [9, 24, 52, 72, 90, 120, 144, 360];

    // 2. Astro Vibrational Periods (Planetary Cycles in Years)
    const astroPeriods = [
      { name: "Mercury", cycle: 0.24, weight: 15 },
      { name: "Venus", cycle: 0.615, weight: 18 },
      { name: "Earth/Sun", cycle: 1.0, weight: 10 },
      { name: "Mars", cycle: 1.88, weight: 25 },
      { name: "Jupiter", cycle: 11.86, weight: 45 },
      { name: "Saturn", cycle: 29.46, weight: 55 },
      { name: "Uranus", cycle: 84.0, weight: 65 },
      { name: "Neptune", cycle: 164.8, weight: 75 }
    ];

    for (let i = 1; i <= range; i++) {
      const year = start + i;
      const yearsFromStart = i;

      let resonancePower = 0;
      let cycleName = "Standard Wave";
      let type: "peak" | "trough" | "neutral" = "neutral";
      const reasons: string[] = [];

      // A. Square Resonance (9, 24, 52, 90, 144, 360)
      for (const sq of gannSquares) {
        if (yearsFromStart % sq === 0) {
          resonancePower += (sq === 360 || sq === 144) ? 40 : 25;
          reasons.push(`Sq${sq}`);
          if (sq >= 90) type = yearsFromStart % (sq * 2) === 0 ? "peak" : "trough";
        }
      }

      // B. Astro Synchronicity
      for (const astro of astroPeriods) {
        const progress = (yearsFromStart / astro.cycle) % 1;
        if (progress < 0.05 || progress > 0.95) {
          resonancePower += astro.weight;
          reasons.push(astro.name);
          if (astro.weight > 40) type = "peak";
        } else if (Math.abs(progress - 0.5) < 0.05) {
          resonancePower += astro.weight / 2;
          reasons.push(`${astro.name} Opp`);
          type = "trough";
        }
      }

      // C. Gann Wave & Angle Symmetry
      const sqrtPrice = Math.sqrt(price);
      const angleResonance = (yearsFromStart * 45) % 360; // Gann 45 degree time angle
      if (angleResonance === 0) {
        resonancePower += 30;
        reasons.push("Gann 45°");
      }

      // Square of Nine calculation for projected price
      // Using time-to-price squaring formula: Price = (sqrt(Price) + (Time_Angle / 180))^2
      const timeAngle = (yearsFromStart * 360 / 365) * 8; // Normalized time vibration
      const projectedPrice = Math.pow(sqrtPrice + (timeAngle / 360), 2);

      // E. Precision Intra-Day Timing (Gann Time Vibration)
      // We derive specific Day, Hour, Minute, and Second based on the cycle resonance
      const dayOfYear = Math.floor((resonancePower * 3.6525) % 365);
      const hour = Math.floor((resonancePower * 13) % 24);
      const minute = Math.floor((resonancePower * 47) % 60);
      const second = Math.floor((resonancePower * 19) % 60);

      const forecastDate = new Date(year, 0, 1);
      forecastDate.setDate(forecastDate.getDate() + dayOfYear);
      forecastDate.setHours(hour, minute, second);

      // Determine final results
      const finalConfidence = Math.min(99, Math.max(40, resonancePower));

      if (reasons.length > 0) {
        cycleName = reasons.join(" + ");
      }

      results.push({
        year,
        date: forecastDate,
        price: projectedPrice,
        cycle: cycleName,
        type: type === "neutral" && resonancePower > 60 ? (i % 2 === 0 ? "peak" : "trough") : type,
        confidence: finalConfidence,
      });
    }

    setForecasts(results);
    setIsCalculating(false);
  };

  const significantForecasts = forecasts.filter((f) => f.confidence >= 75);
  const peakForecasts = forecasts.filter((f) => f.type === "peak" && f.confidence >= 70);
  const troughForecasts = forecasts.filter((f) => f.type === "trough" && f.confidence >= 70);

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-base md:text-lg font-black tracking-tight">
              <Zap className="h-5 w-5 text-accent animate-pulse" />
              GANN QUANTUM FORECASTING ENGINE
            </CardTitle>
            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3">
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Precision: SQ9 | SQ144 | Astro-Vibration | Angle-Time</p>
              <Badge variant="outline" className="w-fit text-[10px] h-5 bg-primary/10 text-primary border-primary/20 flex items-center gap-1 font-mono">
                <Clock className="w-3 h-3" />
                {currentTime.toLocaleDateString()} {currentTime.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </Badge>
            </div>
          </div>
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Base Price</Label>
              {isAutoMode && <Badge variant="outline" className="text-[10px] h-4 bg-primary/10 text-primary border-primary/20">LIVE</Badge>}
            </div>
            <div className="relative">
              <Input
                type="number"
                value={basePrice}
                onChange={(e) => !isAutoMode && setBasePrice(e.target.value)}
                placeholder="100"
                readOnly={isAutoMode}
                className={isAutoMode ? "bg-primary/5 border-primary/20 text-primary font-bold" : ""}
              />
              {isAutoMode && (
                <div className="absolute right-2 top-1/2 -translate-y-1/2">
                  <Zap className="w-3 h-3 text-primary animate-pulse" />
                </div>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Label>Start Year</Label>
            <Input
              type="number"
              value={startYear}
              onChange={(e) => setStartYear(e.target.value)}
              placeholder="2024"
            />
          </div>
          <div className="space-y-2">
            <Label>Forecast Range</Label>
            <Select value={forecastRange} onValueChange={setForecastRange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {YEAR_RANGES.map((range) => (
                  <SelectItem key={range.value} value={range.value}>
                    {range.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Cycle Focus</Label>
            <Select value={cycleType} onValueChange={setCycleType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CYCLE_TYPES.map((cycle) => (
                  <SelectItem key={cycle.value} value={cycle.value}>
                    {cycle.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <Button
          onClick={calculateForecasts}
          className="w-full relative overflow-hidden group"
          disabled={isCalculating}
        >
          {isCalculating ? (
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Target className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
          )}
          {isAutoMode ? "Refresh Automatic Forecast" : `Generate ${forecastRange}-Year Forecast`}
          {isAutoMode && isCalculating && <div className="absolute inset-0 bg-primary/20 animate-pulse" />}
        </Button>

        {forecasts.length > 0 && (
          <Tabs defaultValue="significant" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="significant">Significant</TabsTrigger>
              <TabsTrigger value="peaks">Peaks</TabsTrigger>
              <TabsTrigger value="troughs">Troughs</TabsTrigger>
              <TabsTrigger value="all">All</TabsTrigger>
            </TabsList>

            <TabsContent value="significant">
              <ScrollArea className="h-[300px]">
                <div className="space-y-2">
                  {significantForecasts.map((forecast) => (
                    <ForecastItem key={forecast.year} forecast={forecast} />
                  ))}
                  {significantForecasts.length === 0 && (
                    <p className="text-muted-foreground text-center py-4">No significant cycles found</p>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="peaks">
              <ScrollArea className="h-[300px]">
                <div className="space-y-2">
                  {peakForecasts.map((forecast) => (
                    <ForecastItem key={forecast.year} forecast={forecast} />
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="troughs">
              <ScrollArea className="h-[300px]">
                <div className="space-y-2">
                  {troughForecasts.map((forecast) => (
                    <ForecastItem key={forecast.year} forecast={forecast} />
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="all">
              <ScrollArea className="h-[300px]">
                <div className="space-y-2">
                  {forecasts.map((forecast) => (
                    <ForecastItem key={forecast.year} forecast={forecast} />
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        )}

        {/* Summary Stats */}
        {forecasts.length > 0 && (
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30">
              <TrendingUp className="h-5 w-5 mx-auto text-green-500 mb-1" />
              <div className="text-2xl font-bold text-green-500">{peakForecasts.length}</div>
              <div className="text-xs text-muted-foreground">Peak Cycles</div>
            </div>
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <TrendingDown className="h-5 w-5 mx-auto text-red-500 mb-1" />
              <div className="text-2xl font-bold text-red-500">{troughForecasts.length}</div>
              <div className="text-xs text-muted-foreground">Trough Cycles</div>
            </div>
            <div className="p-3 rounded-lg bg-primary/10 border border-primary/30">
              <Target className="h-5 w-5 mx-auto text-primary mb-1" />
              <div className="text-2xl font-bold text-primary">{significantForecasts.length}</div>
              <div className="text-xs text-muted-foreground">High Confidence</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const ForecastItem = ({ forecast }: { forecast: ForecastResult }) => (
  <div
    className={`p-3 rounded-lg border ${forecast.type === "peak"
      ? "bg-green-500/5 border-green-500/20"
      : forecast.type === "trough"
        ? "bg-red-500/5 border-red-500/20"
        : "bg-secondary/50 border-border/50"
      }`}
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {forecast.type === "peak" ? (
          <TrendingUp className="h-4 w-4 text-green-500" />
        ) : forecast.type === "trough" ? (
          <TrendingDown className="h-4 w-4 text-red-500" />
        ) : (
          <Target className="h-4 w-4 text-muted-foreground" />
        )}
        <span className="font-semibold">{forecast.year}</span>
        <Badge variant="outline" className="text-xs">
          {forecast.cycle}
        </Badge>
      </div>
      <div className="text-right">
        <div className="font-mono text-sm font-bold text-foreground">${forecast.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        <div className="text-[9px] text-muted-foreground font-medium uppercase">
          {forecast.date.toLocaleDateString()} {forecast.date.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </div>
        <div className="flex items-center justify-end gap-1 mt-0.5">
          <div className="w-12 h-1 bg-secondary rounded-full overflow-hidden">
            <div
              className={`h-full ${forecast.confidence > 80 ? 'bg-primary' : forecast.confidence > 60 ? 'bg-accent' : 'bg-muted-foreground'}`}
              style={{ width: `${forecast.confidence}%` }}
            />
          </div>
          <span className="text-[9px] font-bold text-primary">{forecast.confidence}%</span>
        </div>
      </div>
    </div>
  </div>
);
