import {
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
  Bar,
  Line
} from "recharts";
import { calculateGannAngles, calculateGannSquareByType } from "@/lib/gannCalculations";

export interface CandlestickData {
  time: string;
  date?: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
  [key: string]: any;
}

interface CandlestickChartProps {
  data: CandlestickData[];
  showGannAngles?: boolean;
  activeGannAngles?: string[];
  showGannWave?: boolean;
  showElliottWave?: boolean;
  showGannBox?: boolean;
  showGannSquares?: boolean;
  activeGannSquares?: (24.52 | 90 | 360)[];
  showGannAstro?: boolean;
  height?: number;
  indicatorKeys?: string[];
  children?: React.ReactNode;
}

const INDICATOR_COLORS = [
  "hsl(var(--primary))",
  "hsl(var(--accent))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--success))"
];

const GANN_ANGLE_COLORS: Record<string, string> = {
  "1x1": "hsl(var(--primary))",
  "2x1": "hsl(var(--accent))",
  "4x1": "hsl(var(--chart-2))",
  "8x1": "hsl(var(--chart-3))",
  "16x1": "hsl(var(--chart-5))",
  "1x2": "hsl(var(--chart-1))",
  "1x4": "hsl(var(--chart-4))"
};

export const CandlestickChart = ({
  data,
  showGannAngles = false,
  activeGannAngles = [],
  showGannWave = false,
  showElliottWave = false,
  showGannBox = false,
  showGannSquares = false,
  activeGannSquares = [],
  showGannAstro = false,
  height = 400,
  indicatorKeys = [],
  children
}: CandlestickChartProps) => {
  if (!data || data.length === 0) return <div className="flex items-center justify-center p-12 text-muted-foreground">No chart data available</div>;

  const latestPrice = data[data.length - 1]?.close || 0;

  // Base Slope for diagonal angles
  const firstPrice = data[0].open;
  const lastPrice = data[data.length - 1].close;
  const avgSlope = (lastPrice - firstPrice) / data.length;

  const getSlopeMultiplier = (angle: string) => {
    const parts = angle.split('x');
    if (parts.length !== 2) return 1;
    return Number(parts[0]) / Number(parts[1]);
  };

  // Process data for rendering
  const processedData = data.map((d, i) => {
    const item: any = {
      ...d,
      wickLow: d.low,
      wickHigh: d.high,
      isUp: d.close >= d.open,
      range: [d.low, d.high],
      bodyRange: [Math.min(d.open, d.close), Math.max(d.open, d.close)]
    };

    // Calculate Diagonal Gann Angles
    if (showGannAngles && activeGannAngles.length > 0) {
      activeGannAngles.forEach(angle => {
        const mult = getSlopeMultiplier(angle);
        item[`gann_${angle}`] = firstPrice + (i * avgSlope * mult);
      });
    }

    return item;
  });

  // Gann Box Levels (Octaves)
  let gannBoxLevels: number[] = [];
  if (showGannBox) {
    const high = Math.max(...data.map(d => d.high));
    const low = Math.min(...data.map(d => d.low));
    const range = high - low;
    gannBoxLevels = [low, low + range * 0.25, low + range * 0.5, low + range * 0.75, high];
  }

  // Astro Levels (Mock)
  const astroLevels = showGannAstro ? [latestPrice * 1.02, latestPrice * 1.05, latestPrice * 0.98] : [];

  // Elliott Wave Logic (Basic 5-point zigzag)
  let elliottPoints: any[] = [];
  if (showElliottWave && data.length > 10) {
    const step = Math.floor(data.length / 6);
    elliottPoints = [
      { time: data[0].time, value: data[0].low, label: "0" },
      { time: data[step].time, value: data[step].high, label: "(1)" },
      { time: data[step * 2].time, value: data[step * 2].low, label: "(2)" },
      { time: data[step * 4].time, value: data[step * 4].high, label: "(3)" },
      { time: data[step * 5].time, value: data[step * 5].low, label: "(4)" },
      { time: data[data.length - 1].time, value: data[data.length - 1].high, label: "(5)" },
    ];
  }

  // Gann Wave Logic (ZigZag)
  let wavePoints: any[] = [];
  if (showGannWave && data.length > 5) {
    let currentHigh = data[0].high;
    let currentLow = data[0].low;
    let trend: 'up' | 'down' = data[1].close > data[0].close ? 'up' : 'down';

    wavePoints.push({ time: data[0].time, value: data[0].close });
    for (let i = 1; i < data.length; i++) {
      if (trend === 'up') {
        if (data[i].high > currentHigh) currentHigh = data[i].high;
        else if (data[i].low < currentHigh * 0.985) { // 1.5% reversal
          wavePoints.push({ time: data[i - 1].time, value: currentHigh });
          trend = 'down';
          currentLow = data[i].low;
        }
      } else {
        if (data[i].low < currentLow) currentLow = data[i].low;
        else if (data[i].high > currentLow * 1.015) {
          wavePoints.push({ time: data[i - 1].time, value: currentLow });
          trend = 'up';
          currentHigh = data[i].high;
        }
      }
    }
    wavePoints.push({ time: data[data.length - 1].time, value: data[data.length - 1].close });
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-card/95 backdrop-blur-sm border border-border p-3 rounded-lg shadow-xl text-xs space-y-1">
          <p className="font-bold border-b border-border pb-1 mb-1 text-primary">{d.date || d.time}</p>
          <div className="grid grid-cols-2 gap-x-4">
            <span className="text-muted-foreground">Open:</span> <span className="font-mono text-right">{d.open?.toFixed(2)}</span>
            <span className="text-muted-foreground">High:</span> <span className="font-mono text-right text-success">{d.high?.toFixed(2)}</span>
            <span className="text-muted-foreground">Low:</span> <span className="font-mono text-right text-destructive">{d.low?.toFixed(2)}</span>
            <span className="text-muted-foreground">Close:</span> <span className="font-mono text-right font-bold">{d.close?.toFixed(2)}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full min-h-[500px] flex flex-col space-y-4">
      <div className="flex items-center justify-between px-2 overflow-x-auto pb-1">
        <div className="flex gap-4 text-[10px] md:text-sm font-mono whitespace-nowrap mr-4">
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">O</span> <span className={data[data.length - 1]?.close >= data[data.length - 1]?.open ? "text-success" : "text-destructive"}>{data[data.length - 1]?.open?.toFixed(2)}</span></div>
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">H</span> <span className="text-success">{data[data.length - 1]?.high?.toFixed(2)}</span></div>
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">L</span> <span className="text-destructive">{data[data.length - 1]?.low?.toFixed(2)}</span></div>
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">C</span> <span className={data[data.length - 1]?.close >= data[data.length - 1]?.open ? "text-success" : "text-destructive"}>{data[data.length - 1]?.close?.toFixed(2)}</span></div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={processedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="1 1" stroke="hsl(var(--border))" opacity={0.15} vertical={true} />
          <XAxis
            dataKey="time"
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            minTickGap={30}
            axisLine={false}
          />
          <YAxis
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            domain={['auto', 'auto']}
            orientation="right"
            width={60}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} isAnimationActive={false} />

          <ReferenceLine
            y={latestPrice}
            stroke="hsl(var(--primary))"
            strokeDasharray="3 3"
            opacity={0.5}
            label={{ position: 'right', value: latestPrice?.toFixed(2), fill: 'hsl(var(--primary))', fontSize: 10, offset: 5 }}
          />

          {/* Gann Box Levels */}
          {showGannBox && gannBoxLevels.map((y, idx) => (
            <ReferenceLine key={`box-${idx}`} y={y} stroke="hsl(var(--accent))" strokeWidth={0.5} opacity={0.3} />
          ))}

          {/* Astro Levels */}
          {showGannAstro && astroLevels.map((y, idx) => (
            <ReferenceLine key={`astro-${idx}`} y={y} stroke="hsl(var(--chart-5))" strokeDasharray="3 3" opacity={0.6} />
          ))}

          {/* Gann Squares Levels */}
          {showGannSquares && activeGannSquares.map((type) => {
            const levels = calculateGannSquareByType(latestPrice, type);
            return Object.entries(levels).map(([label, y]) => (
              <ReferenceLine
                key={`${type}-${label}`}
                y={y}
                stroke="hsl(var(--chart-4))"
                strokeWidth={0.5}
                opacity={0.2}
                label={{ position: 'left', value: label, fill: 'hsl(var(--chart-4))', fontSize: 8 }}
              />
            ));
          })}

          {/* Wick */}
          <Bar dataKey="range" barSize={1} isAnimationActive={false}>
            {processedData.map((d, idx) => (
              <Cell key={idx} fill={d.isUp ? "#22c55e" : "#ef4444"} />
            ))}
          </Bar>

          {/* Body */}
          <Bar dataKey="bodyRange" barSize={8} isAnimationActive={false}>
            {processedData.map((d, idx) => (
              <Cell key={idx} fill={d.isUp ? "#22c55e" : "#ef4444"} />
            ))}
          </Bar>

          {/* Diagonal Gann Angles */}
          {showGannAngles && activeGannAngles.map(angle => (
            <Line
              key={angle}
              type="linear"
              dataKey={`gann_${angle}`}
              stroke={GANN_ANGLE_COLORS[angle] || "hsl(var(--primary))"}
              strokeWidth={1}
              dot={false}
              isAnimationActive={false}
              opacity={0.5}
            />
          ))}

          {/* Gann Wave (ZigZag) */}
          {showGannWave && (
            <Line
              type="linear"
              data={wavePoints}
              dataKey="value"
              stroke="hsl(var(--accent))"
              strokeWidth={2}
              dot={{ r: 2, fill: "hsl(var(--accent))" }}
              isAnimationActive={false}
              name="GANN WAVE"
            />
          )}

          {/* Elliott Wave */}
          {showElliottWave && (
            <Line
              type="linear"
              data={elliottPoints}
              dataKey="value"
              stroke="hsl(var(--chart-3))"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 4, fill: "hsl(var(--chart-3))" }}
              isAnimationActive={false}
              label={{ position: 'top', fill: "hsl(var(--chart-3))", fontSize: 10, fontWeight: 'bold' }}
              name="ELLIOTT WAVE"
            />
          )}

          {/* Dynamic Indicators Overlay */}
          {indicatorKeys.map((key, idx) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={INDICATOR_COLORS[idx % INDICATOR_COLORS.length]}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
              name={key.toUpperCase()}
            />
          ))}

          {children}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
