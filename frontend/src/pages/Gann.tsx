import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sparkles, TrendingUp, TrendingDown, Activity, Target, Shield, Zap, Moon, Clock, Brain, LineChart, DollarSign, Layers } from "lucide-react";
import { PageSection } from "@/components/PageSection";

const Gann = () => {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div>
        <h1 className="text-3xl font-black tracking-tighter text-foreground mb-2 flex items-center gap-2 uppercase">
          Cenayang <span className="text-primary text-glow-primary">Market</span> Intelligence
        </h1>
        <p className="text-sm text-muted-foreground">Institutional Output • 2025-11-05 15:25:00 UTC</p>
      </div>

      {/* Account Summary */}
      <PageSection
        title="Institutional Account Summary"
        icon={<DollarSign className="w-5 h-5" />}
      >
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Symbol</p>
            <p className="text-lg font-bold text-foreground">BTCUSD</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Account</p>
            <p className="text-lg font-bold text-foreground">$100,000</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Risk/Trade</p>
            <p className="text-lg font-bold text-foreground">2%</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Leverage</p>
            <p className="text-lg font-bold text-primary">5x</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Lot Size</p>
            <p className="text-lg font-bold text-foreground">0.19</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Broker</p>
            <p className="text-sm font-semibold text-foreground">Binance/MT5</p>
          </div>
        </div>
      </PageSection>

      {/* Main Trading Signal */}
      <PageSection
        title="Main Trading Signal"
        icon={<TrendingUp className="w-5 h-5 text-success" />}
        className="border-success/20"
        headerAction={<Badge className="bg-success">STRONG BUY</Badge>}
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-background/50 rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Entry</p>
            <p className="text-xl font-bold text-foreground">104,525</p>
          </div>
          <div className="bg-background/50 rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Stop Loss</p>
            <p className="text-xl font-bold text-destructive">103,700</p>
          </div>
          <div className="bg-background/50 rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Take Profit</p>
            <p className="text-xl font-bold text-success">105,000</p>
          </div>
          <div className="bg-background/50 rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Risk/Reward</p>
            <p className="text-xl font-bold text-primary">1:2.3</p>
          </div>
        </div>
      </PageSection>

      {/* Tabs for Different Sections */}
      <Tabs defaultValue="gann" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="gann">Gann Analysis</TabsTrigger>
          <TabsTrigger value="astro">Planetary</TabsTrigger>
          <TabsTrigger value="ehlers">Ehlers DSP</TabsTrigger>
          <TabsTrigger value="forecast">Forecasting</TabsTrigger>
          <TabsTrigger value="ml">ML Engine</TabsTrigger>
        </TabsList>

        {/* Gann Analysis Tab */}
        <TabsContent value="gann" className="space-y-6">
          {/* Square of Nine */}
          <PageSection title="Gann Analysis Matrix" icon={<Target className="w-5 h-5 text-primary" />}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Supports</p>
                <div className="flex flex-wrap gap-2">
                  {[103500, 103800, 104100].map((level) => (
                    <Badge key={level} variant="outline" className="text-success border-success">
                      {level.toLocaleString()}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Resistances</p>
                <div className="flex flex-wrap gap-2">
                  {[104500, 104800, 105100].map((level) => (
                    <Badge key={level} variant="outline" className="text-destructive border-destructive">
                      {level.toLocaleString()}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Position</p>
                <div className="flex items-center gap-2">
                  <Progress value={68} className="flex-1" />
                  <span className="text-sm font-mono">0.68</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">Near resistance</p>
              </div>
            </div>
          </PageSection>

          {/* Gann Fan Analysis Table */}
          <PageSection title="Gann Fan Analysis Table" icon={<TrendingUp className="w-5 h-5" />}>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Angle</TableHead>
                  <TableHead>Level</TableHead>
                  <TableHead>Strength</TableHead>
                  <TableHead>Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  { angle: "1x3", level: 104000, strength: 0.87, confidence: 87 },
                  { angle: "1x2", level: 104700, strength: 0.91, confidence: 91 },
                  { angle: "1x1", level: 104200, strength: 0.93, confidence: 93 },
                  { angle: "2x1", level: 104300, strength: 0.89, confidence: 89 },
                  { angle: "3x1", level: 105200, strength: 0.85, confidence: 85 },
                ].map((item) => (
                  <TableRow key={item.angle}>
                    <TableCell className="font-mono font-bold">{item.angle}</TableCell>
                    <TableCell className="font-mono">{item.level.toLocaleString()}</TableCell>
                    <TableCell>
                      <Progress value={item.strength * 100} className="w-20" />
                    </TableCell>
                    <TableCell>
                      <Badge variant={item.confidence > 90 ? "default" : "secondary"}>
                        {item.confidence}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <p className="text-xs text-muted-foreground mt-4 italic">
              Harga berada di antara 1x1 & 1x2 angle → zona vibrasi bullish potensial
            </p>
          </PageSection>

          {/* Gann Geometry */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { name: "Square of 52", value: "104,600", label: "Weekly Cycle", status: "Equilibrium" },
              { name: "Square of 144", value: "105,100", label: "Daily Spiral", status: "Resistance" },
              { name: "Square of 360", value: "105,500", label: "Year Vibration", status: "Completion" },
              { name: "Square of 90", value: "104,500", label: "Quarter Grid", status: "180° Harmonic" },
            ].map((square) => (
              <Card key={square.name}>
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground mb-1">{square.name}</p>
                  <p className="text-2xl font-bold text-foreground mb-1">{square.value}</p>
                  <p className="text-xs text-muted-foreground">{square.label}</p>
                  <Badge variant="outline" className="mt-2 text-xs">{square.status}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Supply & Demand Zones */}
          <PageSection title="Supply & Demand Zones" icon={<Shield className="w-5 h-5" />}>
            <div className="space-y-3">
              {[
                { zone: "Demand", range: "103,500 – 103,800", type: "Accumulation", strength: "Strong", color: "success" },
                { zone: "Mid-Range", range: "104,525", type: "Equilibrium", strength: "Neutral", color: "muted" },
                { zone: "Supply", range: "104,500 – 105,100", type: "Distribution", strength: "Strong", color: "destructive" },
              ].map((item) => (
                <div key={item.zone} className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
                  <div className="flex-1">
                    <p className="font-semibold text-foreground">{item.zone}</p>
                    <p className="text-sm text-muted-foreground">{item.type}</p>
                  </div>
                  <div className="flex-1 text-center">
                    <p className="font-mono text-sm">{item.range}</p>
                  </div>
                  <div className="flex-1 text-right">
                    <Badge variant="outline" className={`text-${item.color} border-${item.color}`}>
                      {item.strength}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </PageSection>
        </TabsContent>

        {/* Planetary Tab */}
        <TabsContent value="astro" className="space-y-6">
          <PageSection title="Planetary Influences & Astrology" icon={<Moon className="w-5 h-5 text-primary" />}>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Total Planetary Score</span>
                <Badge variant="outline" className="text-success border-success">+0.36 Bullish</Badge>
              </div>
              <Progress value={68} className="mb-4" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-success/10 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground mb-1">Bullish Aspects</p>
                  <p className="text-sm font-semibold text-success">Jupiter-Venus Trine: +0.42</p>
                  <p className="text-sm font-semibold text-success">Mercury-Neptune Sextile: +0.32</p>
                </div>
                <div className="bg-destructive/10 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground mb-1">Bearish Aspects</p>
                  <p className="text-sm font-semibold text-destructive">Saturn-Mars Square: -0.38</p>
                </div>
              </div>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Planet</TableHead>
                  <TableHead>Sign</TableHead>
                  <TableHead>Degree</TableHead>
                  <TableHead>Note</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  { planet: "Jupiter", sign: "Leo", degree: "128°", note: "Vibrasi positif" },
                  { planet: "Venus", sign: "Cancer", degree: "98°", note: "Harmonik" },
                  { planet: "Saturn", sign: "Libra", degree: "188°", note: "Tekanan reversal" },
                ].map((item) => (
                  <TableRow key={item.planet}>
                    <TableCell className="font-semibold">{item.planet}</TableCell>
                    <TableCell>{item.sign}</TableCell>
                    <TableCell className="font-mono">{item.degree}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{item.note}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <div className="mt-6 p-4 bg-warning/10 rounded-lg border border-warning/20">
              <p className="text-sm font-semibold mb-2">⚠️ Retrograde Phases</p>
              <p className="text-xs text-muted-foreground">Mercury Retrograde: 2025-11-01 → 2025-11-25 (volatilitas tinggi)</p>
              <p className="text-xs text-muted-foreground">Saturn Retrograde: 2025-06-30 → 2025-11-15 (drag tren makro)</p>
            </div>
          </PageSection>

          {/* Time Cycles */}
          <PageSection title="Time Cycles & Vibrations" icon={<Clock className="w-5 h-5 text-primary" />}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-secondary/30 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Dominant Period</p>
                <p className="text-3xl font-bold text-foreground">24.0</p>
                <p className="text-xs text-muted-foreground">days</p>
              </div>
              <div className="text-center p-4 bg-secondary/30 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Amplitude</p>
                <p className="text-3xl font-bold text-primary">High</p>
              </div>
              <div className="text-center p-4 bg-secondary/30 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Phase</p>
                <p className="text-3xl font-bold text-foreground">0.85</p>
                <p className="text-xs text-warning">Near peak</p>
              </div>
            </div>

            <div className="space-y-2">
              {[
                { cycle: "7 days", confidence: 0.88, percent: 90 },
                { cycle: "21 days", confidence: 0.96, percent: 98 },
                { cycle: "90 days", confidence: 0.92, percent: 95 },
              ].map((item) => (
                <div key={item.cycle} className="flex items-center justify-between p-3 rounded-lg bg-secondary/20">
                  <span className="font-semibold text-foreground">{item.cycle}</span>
                  <div className="flex items-center gap-3">
                    <Progress value={item.percent} className="w-32" />
                    <Badge variant="default">{item.percent}%</Badge>
                  </div>
                </div>
              ))}
            </div>
          </PageSection>
        </TabsContent>

        {/* Ehlers DSP Tab */}
        <TabsContent value="ehlers" className="space-y-6">
          <PageSection title="John F. Ehlers' Digital Filters" icon={<Activity className="w-5 h-5 text-primary" />}>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Indicator</TableHead>
                  <TableHead>Signal</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  { indicator: "Fisher Transform", signal: "Bullish Cross", value: "1.33", confidence: 93 },
                  { indicator: "Smoothed RSI", signal: "Bullish", value: "67.2", confidence: 87 },
                  { indicator: "Super Smoother", signal: "Trend Up", value: "+0.024", confidence: 85 },
                  { indicator: "MAMA", signal: "Bullish", value: "104,400", confidence: 90 },
                  { indicator: "Dominant Cycle", signal: "24.0 days", value: "Strong", confidence: 96 },
                  { indicator: "Cyber Cycle", signal: "Rising", value: "+0.026", confidence: 86 },
                ].map((item) => (
                  <TableRow key={item.indicator}>
                    <TableCell className="font-semibold">{item.indicator}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-success border-success text-xs">
                        {item.signal}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{item.value}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Progress value={item.confidence} className="w-16" />
                        <span className="text-xs">{item.confidence}%</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </PageSection>
        </TabsContent>

        {/* Forecasting Tab */}
        <TabsContent value="forecast" className="space-y-6">
          {/* Short-Term Forecast */}
          <PageSection title="Daily Short-Term Forecast (7 Days)" icon={<LineChart className="w-5 h-5" />}>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Forecast Price</TableHead>
                  <TableHead>Prob ↑</TableHead>
                  <TableHead>Gann Note</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  { date: "2025-11-05", price: 104652, prob: 62, note: "1x1 angle support" },
                  { date: "2025-11-06", price: 104976, prob: 67, note: "Square of 9 confluence" },
                  { date: "2025-11-07", price: 104679, prob: 60, note: "2x1 angle test" },
                  { date: "2025-11-08", price: 104998, prob: 65, note: "Square of 90 harmonic" },
                  { date: "2025-11-09", price: 105322, prob: 70, note: "1x2 angle confluence" },
                  { date: "2025-11-12", price: 105105, prob: 75, note: "ATH window" },
                ].map((item) => (
                  <TableRow key={item.date}>
                    <TableCell className="font-mono text-sm">{item.date}</TableCell>
                    <TableCell className="font-mono font-bold">{item.price.toLocaleString()}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Progress value={item.prob} className="w-16" />
                        <span className="text-xs">{item.prob}%</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{item.note}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </PageSection>

          {/* ATH/ATL Projections */}
          <Card>
            <CardHeader>
              <CardTitle>Time Projections — ATH / ATL</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="short">
                <TabsList>
                  <TabsTrigger value="short">Short-Term</TabsTrigger>
                  <TabsTrigger value="long">Long-Term (2030)</TabsTrigger>
                </TabsList>
                <TabsContent value="short" className="mt-4">
                  <div className="space-y-4">
                    <div className="p-4 border border-success/30 rounded-lg bg-success/5">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="w-5 h-5 text-success" />
                          <span className="font-semibold">Next ATH (Short-Term)</span>
                        </div>
                        <Badge variant="outline" className="text-success border-success">86% Confidence</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">2025-11-12 10:00 UTC</p>
                      <p className="text-2xl font-bold text-success mt-2">$105,105</p>
                      <p className="text-xs text-muted-foreground mt-2">Reversal: 2025-11-16 13:40 UTC, $105,505</p>
                      <p className="text-xs italic mt-2">Quarter harmonic (Square of 90) + 1x2 angle confluence</p>
                    </div>
                    <div className="p-4 border border-destructive/30 rounded-lg bg-destructive/5">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <TrendingDown className="w-5 h-5 text-destructive" />
                          <span className="font-semibold">Short-Term ATL Risk</span>
                        </div>
                        <Badge variant="outline" className="text-destructive border-destructive">71% Confidence</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">2025-11-16 13:40 UTC</p>
                      <p className="text-2xl font-bold text-destructive mt-2">$104,304</p>
                      <p className="text-xs italic mt-2">300° cycle rotation with 1x3 angle support</p>
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="long" className="mt-4">
                  <div className="space-y-4">
                    {[
                      { event: "Next ATH (Mid-Term)", date: "2026-03-15", price: "$150,000", confidence: 87, type: "success" },
                      { event: "Major Reversal", date: "2028-05-01", price: "$250,000", confidence: 76, type: "primary" },
                      { event: "Long-Term ATL Risk", date: "2029-10-01", price: "$220,000", confidence: 73, type: "destructive" },
                    ].map((item) => (
                      <div key={item.event} className={`p-4 border border-${item.type}/30 rounded-lg bg-${item.type}/5`}>
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{item.event}</span>
                          <Badge variant="outline">{item.confidence}%</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{item.date}</p>
                        <p className="text-2xl font-bold mt-2">{item.price}</p>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ML Engine Tab */}
        <TabsContent value="ml" className="space-y-6">
          <PageSection title="Machine Learning Prediction Engine" icon={<Brain className="w-5 h-5" />}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-primary/10 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">24h Forecast</p>
                <p className="text-3xl font-bold text-foreground">104,700</p>
                <Badge variant="outline" className="mt-2 text-success border-success">+0.2% Bullish</Badge>
              </div>
              <div className="text-center p-4 bg-primary/10 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Confidence</p>
                <p className="text-3xl font-bold text-primary">88%</p>
                <Progress value={88} className="mt-2" />
              </div>
              <div className="text-center p-4 bg-primary/10 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Direction</p>
                <div className="flex items-center justify-center gap-2 mt-2">
                  <TrendingUp className="w-8 h-8 text-success" />
                  <span className="text-xl font-bold text-success">Bullish</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-sm font-semibold mb-3">Model Contributions:</p>
              {[
                { model: "XGBoost", weight: 14, feature: "Gann confluence & cycle amplitude" },
                { model: "Random Forest", weight: 14, feature: "Ehlers momentum robustness" },
                { model: "LSTM", weight: 14, feature: "Sequence momentum persistence" },
                { model: "Neural ODE", weight: 10, feature: "Curvature fit of price path" },
                { model: "Gradient Boosting", weight: 18, feature: "Hybrid vibration scoring" },
                { model: "LightGBM", weight: 14, feature: "Fast vol-adjusted prediction" },
                { model: "Hybrid Meta-Model", weight: 100, feature: "Ensemble avg (Gann 30% + Ehlers 70%)" },
              ].map((item) => (
                <div key={item.model} className="p-3 rounded-lg bg-secondary/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">{item.model}</span>
                    <Badge variant="secondary">{item.weight}%</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{item.feature}</p>
                </div>
              ))}
            </div>
          </PageSection>

          {/* Pattern Recognition */}
          <Card>
            <CardHeader>
              <CardTitle>Pattern Recognition</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { name: "Bullish Engulfing", type: "Candlestick", confidence: 88, price: "104,100", time: "2025-11-04 15:25 UTC" },
                  { name: "Morning Star", type: "Candlestick", confidence: 80, price: "104,325", time: "2025-11-03 → 2025-11-04" },
                  { name: "Elliott Wave 3", type: "Wave Structure", confidence: 85, price: "104,700", time: "Peak ~2025-11-11" },
                  { name: "Gann Wave Cycle 3", type: "Time-Price Wave", confidence: 83, price: "105,500", time: "~2025-11-16" },
                  { name: "Harmonic AB=CD", type: "Harmonic", confidence: 76, price: "103,800→104,700", time: "5-8 days" },
                ].map((pattern) => (
                  <div key={pattern.name} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <p className="font-semibold">{pattern.name}</p>
                        <Badge variant="outline" className="text-xs mt-1">{pattern.type}</Badge>
                      </div>
                      <div className="text-right">
                        <Progress value={pattern.confidence} className="w-20 mb-1" />
                        <p className="text-xs text-muted-foreground">{pattern.confidence}%</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                      <div>
                        <p className="text-muted-foreground">Price Target</p>
                        <p className="font-mono font-semibold">{pattern.price}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Time Window</p>
                        <p className="font-semibold">{pattern.time}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Options & Market Sentiment */}
      <PageSection title="Options & Market Sentiment" icon={<Zap className="w-5 h-5" />}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-muted-foreground mb-2">Bias</p>
            <Badge variant="outline" className="text-success border-success text-lg px-4 py-2">CALL (Bullish)</Badge>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Recommendation</p>
            <p className="font-semibold">BTCUSD-Call Strike 105,000</p>
            <p className="text-sm text-muted-foreground">Mid: $145.30 • Expiry: ~14d</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Risk/Reward</p>
            <p className="text-3xl font-bold text-primary">2.2</p>
          </div>
        </div>
      </PageSection>

      {/* Position Sizing */}
      <PageSection title="Position Size Calculation" icon={<Shield className="w-5 h-5 text-primary" />}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-secondary/20 rounded-lg">
            <p className="text-xs text-muted-foreground">Risk Amount</p>
            <p className="text-lg font-bold text-foreground">$2,000</p>
            <p className="text-xs text-muted-foreground">2% of equity</p>
          </div>
          <div className="p-3 bg-secondary/20 rounded-lg">
            <p className="text-xs text-muted-foreground">Stop Distance</p>
            <p className="text-lg font-bold text-foreground">825 pts</p>
            <p className="text-xs text-muted-foreground">$1 per point</p>
          </div>
          <div className="p-3 bg-secondary/20 rounded-lg">
            <p className="text-xs text-muted-foreground">Risk per Lot</p>
            <p className="text-lg font-bold text-foreground">$825</p>
          </div>
          <div className="p-3 bg-primary/20 rounded-lg border border-primary/30">
            <p className="text-xs text-muted-foreground">Final Lot Size</p>
            <p className="text-2xl font-bold text-primary">0.19</p>
            <p className="text-xs text-muted-foreground">with 5x leverage</p>
          </div>
        </div>
      </PageSection>
    </div>
  );
};

export default Gann;
