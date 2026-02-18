import { Card } from "@/components/ui/card";
import { ReferenceLine } from "recharts";
import { Activity, TrendingUp, TrendingDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { CandlestickChart } from "./CandlestickChart";

interface MAMAFAMAChartProps {
  data: Array<{
    time: string;
    date?: string;
    open: number;
    high: number;
    low: number;
    close: number;
    mama: number;
    fama: number;
    [key: string]: any;
  }>;
  crossovers: Array<{
    index: number;
    type: 'bullish' | 'bearish';
    mama: number;
    fama: number;
  }>;
}

const MAMAFAMAChart = ({ data, crossovers }: MAMAFAMAChartProps) => {
  const latestCrossover = crossovers.length > 0 ? crossovers[crossovers.length - 1] : null;

  return (
    <Card className="p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">MAMA/FAMA Candlestick Analysis</h3>
        </div>
        {latestCrossover && (
          <Badge
            variant={latestCrossover.type === 'bullish' ? 'default' : 'destructive'}
            className="flex items-center gap-1"
          >
            {latestCrossover.type === 'bullish' ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {latestCrossover.type === 'bullish' ? 'Bullish Cross' : 'Bearish Cross'}
          </Badge>
        )}
      </div>

      <div className="w-full">
        <CandlestickChart data={data} height={400} indicatorKeys={['mama', 'fama']} showGannAngles={false}>
          {/* Crossover markers */}
          {crossovers.map((crossover, idx) => (
            <ReferenceLine
              key={idx}
              x={data[crossover.index]?.time}
              stroke={crossover.type === 'bullish' ? 'hsl(var(--success))' : 'hsl(var(--destructive))'}
              strokeDasharray="3 3"
              opacity={0.6}
              label={{
                value: crossover.type === 'bullish' ? 'BULL' : 'BEAR',
                position: 'top',
                fill: crossover.type === 'bullish' ? 'hsl(var(--success))' : 'hsl(var(--destructive))',
                fontSize: 10
              }}
            />
          ))}
        </CandlestickChart>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-3 rounded-lg bg-secondary/30 border border-border">
          <p className="text-xs text-muted-foreground mb-1">Current Price</p>
          <p className="text-lg font-bold text-foreground font-mono">
            {data[data.length - 1]?.close.toFixed(2)}
          </p>
        </div>
        <div className="p-3 rounded-lg bg-primary/10 border border-primary/30">
          <p className="text-xs text-muted-foreground mb-1">MAMA</p>
          <p className="text-lg font-bold text-primary font-mono">
            {data[data.length - 1]?.mama.toFixed(2)}
          </p>
        </div>
        <div className="p-3 rounded-lg bg-accent/10 border border-accent/30">
          <p className="text-xs text-muted-foreground mb-1">FAMA</p>
          <p className="text-lg font-bold text-accent font-mono">
            {data[data.length - 1]?.fama.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="mt-4 p-3 rounded-lg bg-muted/50">
        <p className="text-xs text-muted-foreground">
          <strong>Signal:</strong> {data[data.length - 1]?.mama > data[data.length - 1]?.fama
            ? 'MAMA above FAMA - Bullish trend'
            : 'MAMA below FAMA - Bearish trend'}
        </p>
      </div>
    </Card>
  );
};

export default MAMAFAMAChart;
