import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, TrendingUp, Shield, BarChart2, Bell } from "lucide-react";
import { PageSection } from "@/components/PageSection";
import MAMAFAMAChart from "@/components/charts/MAMAFAMAChart";
import MAMAFAMACalculator from "@/components/calculators/MAMAFAMACalculator";
import MAMAFAMAAlerts from "@/components/alerts/MAMAFAMAAlerts";
import EhlersRealtimeChart from "@/components/charts/EhlersRealtimeChart";

const Ehlers = () => {
  // Mock chart data for MAMA/FAMA visualization with OHLC
  const chartData = [
    { time: "10:00", open: 104.10, high: 104.30, low: 104.05, close: 104.20, price: 104.20, mama: 104.15, fama: 104.10 },
    { time: "10:15", open: 104.20, high: 104.45, low: 104.15, close: 104.35, price: 104.35, mama: 104.22, fama: 104.18 },
    { time: "10:30", open: 104.35, high: 104.40, low: 104.25, close: 104.28, price: 104.28, mama: 104.26, fama: 104.22 },
    { time: "10:45", open: 104.28, high: 104.50, low: 104.20, close: 104.42, price: 104.42, mama: 104.32, fama: 104.28 },
    { time: "11:00", open: 104.42, high: 104.60, low: 104.35, close: 104.55, price: 104.55, mama: 104.40, fama: 104.35 },
    { time: "11:15", open: 104.55, high: 104.65, low: 104.40, close: 104.48, price: 104.48, mama: 104.44, fama: 104.39 },
    { time: "11:30", open: 104.48, high: 104.55, low: 104.30, close: 104.38, price: 104.38, mama: 104.42, fama: 104.41 },
    { time: "11:45", open: 104.38, high: 104.45, low: 104.25, close: 104.32, price: 104.32, mama: 104.38, fama: 104.40 },
    { time: "12:00", open: 104.32, high: 104.50, low: 104.28, close: 104.45, price: 104.45, mama: 104.40, fama: 104.42 },
    { time: "12:15", open: 104.45, high: 104.65, low: 104.40, close: 104.58, price: 104.58, mama: 104.46, fama: 104.44 },
    { time: "12:30", open: 104.58, high: 104.70, low: 104.50, close: 104.65, price: 104.65, mama: 104.52, fama: 104.48 },
    { time: "12:45", open: 104.65, high: 104.80, low: 104.60, close: 104.72, price: 104.72, mama: 104.58, fama: 104.52 },
    { time: "13:00", open: 104.72, high: 104.85, low: 104.68, close: 104.80, price: 104.80, mama: 104.65, fama: 104.58 },
    { time: "13:15", open: 104.80, high: 104.85, low: 104.70, close: 104.75, price: 104.75, mama: 104.70, fama: 104.62 },
    { time: "13:30", open: 104.75, high: 104.80, low: 104.62, close: 104.68, price: 104.68, mama: 104.71, fama: 104.66 },
    { time: "13:45", open: 104.68, high: 104.75, low: 104.58, close: 104.62, price: 104.62, mama: 104.68, fama: 104.67 },
    { time: "14:00", open: 104.62, high: 104.75, low: 104.58, close: 104.70, price: 104.70, mama: 104.68, fama: 104.68 },
    { time: "14:15", open: 104.70, high: 104.85, low: 104.68, close: 104.78, price: 104.78, mama: 104.72, fama: 104.70 },
  ];

  const mockCrossovers = [
    { index: 7, type: 'bearish' as const, mama: 104.38, fama: 104.40 },
    { index: 8, type: 'bullish' as const, mama: 104.40, fama: 104.42 },
  ];

  const indicators = [
    { name: "Fisher Transform", value: "1.33", signal: "Bullish Cross", strength: 93, trend: "bullish" },
    { name: "Smoothed RSI", value: "67.2", signal: "Bullish", strength: 87, trend: "bullish" },
    { name: "Super Smoother", value: "+0.024", signal: "Trend Up", strength: 85, trend: "bullish" },
    { name: "MAMA (MESA Adaptive)", value: "104,400", signal: "Bullish", strength: 90, trend: "bullish" },
    { name: "FAMA (Following Adaptive)", value: "104,350", signal: "Following", strength: 88, trend: "bullish" },
    { name: "Instantaneous Trendline", value: "104,100", signal: "Uptrend", strength: 89, trend: "bullish" },
    { name: "Cyber Cycle", value: "+0.026", signal: "Rising", strength: 86, trend: "bullish" },
    { name: "Dominant Cycle", value: "24.0 days", signal: "Strong", strength: 96, trend: "bullish" },
    { name: "Sinewave Indicator", value: "+0.021", signal: "Bullish phase", strength: 84, trend: "bullish" },
    { name: "Roofing Filter", value: "+0.017", signal: "Uptrend noise", strength: 80, trend: "bullish" },
    { name: "Decycler", value: "+0.028", signal: "Bullish", strength: 82, trend: "bullish" },
    { name: "Bandpass Filter", value: "+0.015", signal: "Cycle Peak", strength: 88, trend: "bullish" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground flex items-center">
          <Activity className="w-8 h-8 mr-3 text-accent" />
          John F. Ehlers' Digital Filters
        </h1>
        <p className="text-muted-foreground">Advanced signal processing for market analysis</p>
      </div>

      <PageSection title="Overall Analysis Score" icon={<Shield className="w-5 h-5" />}>
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Combined confidence across all digital filter indicators (including Bandpass Filter)
          </p>
          <Badge className="bg-success text-success-foreground text-lg px-4 py-2">88%</Badge>
        </div>
      </PageSection>

      {/* Interactive Real-Time Chart */}
      <EhlersRealtimeChart currentPrice={47509} />

      <PageSection title="Digital Filter Indicators" icon={<BarChart2 className="w-5 h-5" />}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {indicators.map((indicator, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 border border-border hover:bg-secondary/70 transition-colors"
            >
              <div className="flex-1">
                <p className="font-semibold text-foreground">{indicator.name}</p>
                <div className="flex items-center gap-3 mt-1">
                  <p className="text-sm text-muted-foreground font-mono">{indicator.value}</p>
                  <Badge
                    variant="outline"
                    className="border-success text-success bg-success/10"
                  >
                    {indicator.signal}
                  </Badge>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-xs text-muted-foreground mb-1">Confidence</p>
                  <p className="text-lg font-bold text-foreground">{indicator.strength}%</p>
                </div>
                <TrendingUp className="w-5 h-5 text-success" />
              </div>
            </div>
          ))}
        </div>
      </PageSection>

      {/* Bandpass Filter Detail */}
      <PageSection title="Bandpass Filter Analysis" icon={<Activity className="w-5 h-5 text-primary" />}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-secondary/50 rounded-lg">
            <p className="text-sm text-muted-foreground">Center Frequency</p>
            <p className="text-2xl font-bold text-foreground">20 Bars</p>
          </div>
          <div className="p-4 bg-secondary/50 rounded-lg">
            <p className="text-sm text-muted-foreground">Bandwidth</p>
            <p className="text-2xl font-bold text-foreground">0.30</p>
          </div>
          <div className="p-4 bg-secondary/50 rounded-lg">
            <p className="text-sm text-muted-foreground">Current Signal</p>
            <p className="text-2xl font-bold text-success">+0.015</p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-4">
          The Bandpass Filter isolates the dominant cycle component, removing both high-frequency noise and low-frequency trend.
          Positive values indicate bullish cycle phase, negative values indicate bearish phase.
        </p>
      </PageSection>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MAMAFAMAChart data={chartData} crossovers={mockCrossovers} />
        <MAMAFAMACalculator />
      </div>

      <MAMAFAMAAlerts />
    </div>
  );
};

export default Ehlers;
