import { useState, useEffect } from "react";
import { GannSquareChart } from "@/components/charts/GannSquareChart";
import { GannWheelChart } from "@/components/charts/GannWheelChart";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { GannCalculator } from "@/components/calculators/GannCalculator";
import { GannFanChart } from "@/components/charts/GannFanChart";
import { GannBoxChart } from "@/components/charts/GannBoxChart";
import { GannForecastingCalculator } from "@/components/calculators/GannForecastingCalculator";
import HexagonGeometryChart from "@/components/charts/HexagonGeometryChart";
import GannFanFullModule from "@/components/charts/GannFanFullModule";
import { GannSquareMatrix } from "@/components/calculators/GannSquareMatrix";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Wifi } from "lucide-react";
import useWebSocketPrice from "@/hooks/useWebSocketPrice";

// Mock data for candlestick chart
const generateMockCandleData = (basePrice: number) => Array.from({ length: 30 }, (_, i) => {
  const base = basePrice + Math.sin(i / 5) * (basePrice * 0.02);
  const dateStr = new Date(2024, 0, i + 1).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return {
    time: dateStr,
    date: dateStr,
    open: base + Math.random() * (basePrice * 0.005),
    high: base + Math.random() * (basePrice * 0.015),
    low: base - Math.random() * (basePrice * 0.01),
    close: base + Math.random() * (basePrice * 0.005),
  };
});

const GannTools = () => {
  const { priceData, isConnected, isLive, toggleConnection } = useWebSocketPrice({
    symbol: 'BTCUSDT',
    enabled: true,
    updateInterval: 2000,
  });

  const currentPrice = priceData.price;
  const [mockCandleData, setMockCandleData] = useState(() => generateMockCandleData(currentPrice));

  useEffect(() => {
    setMockCandleData(generateMockCandleData(currentPrice));
  }, [currentPrice]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Gann Analysis Tools</h1>
          <p className="text-muted-foreground">Advanced Gann calculation engines and visualization (Live: ${currentPrice.toLocaleString()})</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={isConnected ? "border-success text-success" : "border-destructive text-destructive"}>
            <Wifi className="w-3 h-3 mr-1" />
            {isConnected ? "WebSocket" : "Disconnected"}
          </Badge>
          <Badge variant={isLive ? "default" : "outline"} className={isLive ? "bg-success" : ""}>
            {isLive ? "Live" : "Paused"}
          </Badge>
          <Button variant="outline" size="sm" onClick={toggleConnection}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isLive ? 'animate-spin' : ''}`} />
            {isLive ? "Pause" : "Resume"}
          </Button>
        </div>
      </div>

      {/* NEW Gann Vibration Matrix - Comparison of 24.52, 90, 144, 360 */}
      <GannSquareMatrix currentPrice={currentPrice} />

      {/* Hexagon Geometry Full (0-360°) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <HexagonGeometryChart currentPrice={currentPrice} />
        <GannFanFullModule currentPrice={currentPrice} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <CandlestickChart data={mockCandleData} />

          {/* Gann Box 0-360° Multi-Timeframe */}
          <GannBoxChart basePrice={currentPrice} />

          {/* Gann Forecasting up to 365 Years */}
          <GannForecastingCalculator currentPrice={currentPrice} autoCalculate={isLive} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <GannSquareChart centerValue={currentPrice} />
            <GannWheelChart currentPrice={currentPrice} />
          </div>

          <GannFanChart />
        </div>

        <div>
          <GannCalculator />
        </div>
      </div>
    </div>
  );
};

export default GannTools;
