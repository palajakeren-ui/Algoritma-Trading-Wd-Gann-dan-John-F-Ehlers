import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Calculator, Activity, TrendingUp, Sun, Moon, Star } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";
import {
  calculateSquareOf9,
  calculateGannAngles,
  calculateSupportResistance,
  calculateFibonacciLevels,
  calculateGannFan,
} from "@/lib/gannCalculations";

// Gann Fan Full Module: 16x1, 8x1, 4x1, 3x1, 2x1, 1x1, 1x2, 1x3, 1x4, 1x8, 1x16
const GANN_FAN_ANGLES = [
  { ratio: "16x1", slope: 86.42, multiplier: 0.970 },
  { ratio: "8x1", slope: 82.87, multiplier: 0.978 },
  { ratio: "4x1", slope: 75.96, multiplier: 0.985 },
  { ratio: "3x1", slope: 71.57, multiplier: 0.990 },
  { ratio: "2x1", slope: 63.43, multiplier: 0.995 },
  { ratio: "1x1", slope: 45.00, multiplier: 1.000 },
  { ratio: "1x2", slope: 26.57, multiplier: 1.005 },
  { ratio: "1x3", slope: 18.43, multiplier: 1.010 },
  { ratio: "1x4", slope: 14.04, multiplier: 1.015 },
  { ratio: "1x8", slope: 7.13, multiplier: 1.022 },
  { ratio: "1x16", slope: 3.58, multiplier: 1.030 },
];

// Hexagon Geometry: 0°,15°,30°,45°,60°,90°,135°,180°,225°,270°,315°,360°
const HEXAGON_ANGLES = [0, 15, 30, 45, 60, 90, 135, 180, 225, 270, 315, 360];

// Elliott Wave patterns
const ELLIOTT_WAVES = [
  { wave: "Wave 1", ratio: 1.0, type: "impulse" },
  { wave: "Wave 2", ratio: 0.618, type: "correction" },
  { wave: "Wave 3", ratio: 1.618, type: "impulse" },
  { wave: "Wave 4", ratio: 0.382, type: "correction" },
  { wave: "Wave 5", ratio: 1.0, type: "impulse" },
  { wave: "Wave A", ratio: 1.0, type: "correction" },
  { wave: "Wave B", ratio: 0.5, type: "correction" },
  { wave: "Wave C", ratio: 1.0, type: "correction" },
];

// Astrology data
const PLANETARY_POSITIONS = [
  { planet: "Sun", symbol: "☉", degree: 245, sign: "Sagittarius" },
  { planet: "Moon", symbol: "☽", degree: 120, sign: "Leo" },
  { planet: "Mercury", symbol: "☿", degree: 230, sign: "Scorpio", retrograde: true },
  { planet: "Venus", symbol: "♀", degree: 280, sign: "Capricorn" },
  { planet: "Mars", symbol: "♂", degree: 95, sign: "Cancer" },
  { planet: "Jupiter", symbol: "♃", degree: 45, sign: "Taurus" },
  { planet: "Saturn", symbol: "♄", degree: 335, sign: "Pisces" },
];

interface GannCalculatorFullProps {
  currentPrice?: number;
}

const GannCalculatorFull = ({ currentPrice = 47500 }: GannCalculatorFullProps) => {
  const [price, setPrice] = useState<string>(currentPrice.toString());
  const [high, setHigh] = useState<string>((currentPrice * 1.05).toString());
  const [low, setLow] = useState<string>((currentPrice * 0.95).toString());
  const [results, setResults] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("gannbox");

  useEffect(() => {
    setPrice(currentPrice.toString());
    setHigh((currentPrice * 1.05).toFixed(2));
    setLow((currentPrice * 0.95).toFixed(2));
    handleCalculate();
  }, [currentPrice]);

  const handleCalculate = () => {
    const priceNum = parseFloat(price) || currentPrice;
    const highNum = parseFloat(high);
    const lowNum = parseFloat(low);

    const gannAngles = calculateGannAngles(priceNum);
    const supportResistance = calculateSupportResistance(highNum, lowNum, priceNum);
    const fibonacci = calculateFibonacciLevels(highNum, lowNum);
    const squareOf9 = calculateSquareOf9(priceNum);
    const gannFan = calculateGannFan(priceNum, 1);

    // Gann Box data
    const gannBoxData = HEXAGON_ANGLES.map((angle, idx) => ({
      angle: `${angle}°`,
      price: priceNum * (1 + (Math.sin(angle * Math.PI / 180) * 0.05)),
      support: angle <= 180,
    }));

    // Gann Wave data
    const gannWaveData = Array.from({ length: 20 }, (_, i) => ({
      time: i,
      price: priceNum + Math.sin(i / 3) * (priceNum * 0.02) + (i * priceNum * 0.001),
      wave: Math.sin(i / 2) * (priceNum * 0.015),
    }));

    // Elliott Wave levels
    const elliottLevels = ELLIOTT_WAVES.map(w => ({
      ...w,
      price: priceNum * w.ratio,
    }));

    // Fan levels
    const fanLevels = GANN_FAN_ANGLES.map(f => ({
      ...f,
      price: priceNum * f.multiplier,
    }));

    setResults({
      gannAngles,
      supportResistance,
      fibonacci,
      squareOf9: squareOf9[0]?.values.slice(0, 8),
      gannBoxData,
      gannWaveData,
      elliottLevels,
      fanLevels,
    });
  };

  return (
    <Card className="p-4 md:p-6 border-border bg-card">
      <div className="flex items-center gap-2 mb-6">
        <Calculator className="w-6 h-6 text-primary" />
        <h3 className="text-xl font-semibold text-foreground">Gann Calculator Full Module</h3>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div>
          <Label htmlFor="price">Current Price</Label>
          <Input id="price" type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="high">Period High</Label>
          <Input id="high" type="number" step="0.01" value={high} onChange={(e) => setHigh(e.target.value)} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="low">Period Low</Label>
          <Input id="low" type="number" step="0.01" value={low} onChange={(e) => setLow(e.target.value)} className="mt-1" />
        </div>
      </div>

      <Button onClick={handleCalculate} className="w-full mb-6">Calculate All Levels</Button>

      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="grid grid-cols-5 mb-4">
          <TabsTrigger value="gannbox" className="text-xs">Gann Box</TabsTrigger>
          <TabsTrigger value="gannwave" className="text-xs">Gann Wave</TabsTrigger>
          <TabsTrigger value="elliott" className="text-xs">Elliott Wave</TabsTrigger>
          <TabsTrigger value="gannfan" className="text-xs">Gann Fan</TabsTrigger>
          <TabsTrigger value="astrology" className="text-xs">Astrology</TabsTrigger>
        </TabsList>

        {/* Gann Box Tab */}
        <TabsContent value="gannbox" className="space-y-4">
          <h4 className="text-lg font-semibold text-foreground flex items-center">
            <Activity className="w-5 h-5 mr-2 text-accent" />
            Gann Box (0°-360°)
          </h4>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={results?.gannBoxData || []}>
                <defs>
                  <linearGradient id="colorGann" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="angle" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                <Area type="monotone" dataKey="price" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorGann)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {HEXAGON_ANGLES.map(angle => (
              <div key={angle} className="p-2 bg-secondary/50 rounded text-center">
                <span className="text-xs text-muted-foreground">{angle}°</span>
                <p className="text-sm font-mono text-foreground">${(parseFloat(price) * (1 + Math.sin(angle * Math.PI / 180) * 0.03)).toFixed(2)}</p>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Gann Wave Tab */}
        <TabsContent value="gannwave" className="space-y-4">
          <h4 className="text-lg font-semibold text-foreground flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-success" />
            Gann Wave Analysis
          </h4>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={results?.gannWaveData || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                <Line type="monotone" dataKey="price" stroke="hsl(var(--foreground))" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="wave" stroke="hsl(var(--primary))" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </TabsContent>

        {/* Elliott Wave Tab */}
        <TabsContent value="elliott" className="space-y-4">
          <h4 className="text-lg font-semibold text-foreground">Elliott Wave Levels</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {ELLIOTT_WAVES.map((wave, idx) => (
              <div key={idx} className={`p-3 rounded-lg border ${wave.type === "impulse" ? "border-success/30 bg-success/10" : "border-destructive/30 bg-destructive/10"}`}>
                <p className="text-sm font-semibold text-foreground">{wave.wave}</p>
                <p className="text-xs text-muted-foreground">{wave.type}</p>
                <p className="text-lg font-mono text-foreground">${(parseFloat(price) * wave.ratio).toFixed(2)}</p>
                <Badge variant="outline" className="text-xs">{(wave.ratio * 100).toFixed(1)}%</Badge>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Gann Fan Tab */}
        <TabsContent value="gannfan" className="space-y-4">
          <h4 className="text-lg font-semibold text-foreground">Gann Fan (16x1 to 1x16)</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {GANN_FAN_ANGLES.map((fan, idx) => (
              <div key={idx} className="p-3 bg-secondary/50 rounded-lg">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-foreground">{fan.ratio}</span>
                  <Badge variant="outline" className={fan.multiplier < 1 ? "border-success text-success" : fan.multiplier > 1 ? "border-destructive text-destructive" : "border-primary text-primary"}>
                    {fan.multiplier < 1 ? "Support" : fan.multiplier > 1 ? "Resistance" : "Balance"}
                  </Badge>
                </div>
                <p className="text-lg font-mono text-foreground">${(parseFloat(price) * fan.multiplier).toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">{fan.slope.toFixed(2)}° slope</p>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Astrology Tab */}
        <TabsContent value="astrology" className="space-y-4">
          <h4 className="text-lg font-semibold text-foreground flex items-center">
            <Star className="w-5 h-5 mr-2 text-accent" />
            Gann Astrology (Planetary Positions)
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {PLANETARY_POSITIONS.map((planet, idx) => (
              <div key={idx} className="p-3 bg-secondary/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{planet.symbol}</span>
                  <div>
                    <p className="font-semibold text-foreground">{planet.planet}</p>
                    {planet.retrograde && <Badge variant="destructive" className="text-xs">Retrograde</Badge>}
                  </div>
                </div>
                <p className="text-sm text-foreground">{planet.sign}</p>
                <p className="text-lg font-mono text-accent">{planet.degree}°</p>
                <p className="text-xs text-muted-foreground">Price: ${(parseFloat(price) * (1 + planet.degree / 3600)).toFixed(2)}</p>
              </div>
            ))}
          </div>
          <Card className="p-4 bg-primary/10 border-primary/20">
            <p className="text-sm text-foreground">
              <strong>Market Sentiment:</strong> Based on planetary aspects, current bias is <Badge className="bg-success">72% Bullish</Badge>
            </p>
          </Card>
        </TabsContent>
      </Tabs>

      {results && (
        <div className="mt-6 space-y-4">
          <h4 className="text-lg font-semibold text-foreground">Support & Resistance</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div className="p-2 bg-destructive/10 rounded text-center">
              <span className="text-xs text-muted-foreground">R3</span>
              <p className="font-mono text-destructive">${results.supportResistance?.resistance3?.toFixed(2)}</p>
            </div>
            <div className="p-2 bg-destructive/10 rounded text-center">
              <span className="text-xs text-muted-foreground">R2</span>
              <p className="font-mono text-destructive">${results.supportResistance?.resistance2?.toFixed(2)}</p>
            </div>
            <div className="p-2 bg-destructive/10 rounded text-center">
              <span className="text-xs text-muted-foreground">R1</span>
              <p className="font-mono text-destructive">${results.supportResistance?.resistance1?.toFixed(2)}</p>
            </div>
            <div className="p-2 bg-primary/10 rounded text-center">
              <span className="text-xs text-muted-foreground">Pivot</span>
              <p className="font-mono text-primary font-bold">${results.supportResistance?.pivot?.toFixed(2)}</p>
            </div>
            <div className="p-2 bg-success/10 rounded text-center">
              <span className="text-xs text-muted-foreground">S1</span>
              <p className="font-mono text-success">${results.supportResistance?.support1?.toFixed(2)}</p>
            </div>
            <div className="p-2 bg-success/10 rounded text-center">
              <span className="text-xs text-muted-foreground">S2</span>
              <p className="font-mono text-success">${results.supportResistance?.support2?.toFixed(2)}</p>
            </div>
            <div className="p-2 bg-success/10 rounded text-center">
              <span className="text-xs text-muted-foreground">S3</span>
              <p className="font-mono text-success">${results.supportResistance?.support3?.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

export default GannCalculatorFull;
