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
import { calculateGannAngles } from "@/lib/gannCalculations";

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

export const CandlestickChart = ({
  data,
  showGannAngles = true,
  height = 400,
  indicatorKeys = [],
  children
}: CandlestickChartProps) => {
  if (!data || data.length === 0) return <div className="flex items-center justify-center p-12 text-muted-foreground">No chart data available</div>;

  const latestPrice = data[data.length - 1]?.close || 0;
  const gannAngles = calculateGannAngles(latestPrice, 1);

  // Prepare data for the multi-bar trick
  const processedData = data.map(d => ({
    ...d,
    wickLow: d.low,
    wickHigh: d.high,
    isUp: d.close >= d.open,
    range: [d.low, d.high],
    bodyRange: [Math.min(d.open, d.close), Math.max(d.open, d.close)]
  }));

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
          {indicatorKeys.map((key, idx) => d[key] !== undefined && (
            <div key={key} className="flex justify-between border-t border-border/50 pt-1 mt-1 font-semibold" style={{ color: INDICATOR_COLORS[idx % INDICATOR_COLORS.length] }}>
              <span className="uppercase">{key}:</span>
              <span>{typeof d[key] === 'number' ? d[key].toFixed(2) : d[key]}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between px-2 overflow-x-auto pb-1">
        <div className="flex gap-4 text-[10px] md:text-sm font-mono whitespace-nowrap mr-4">
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">O</span> <span className={data[data.length - 1]?.close >= data[data.length - 1]?.open ? "text-success" : "text-destructive"}>{data[data.length - 1]?.open?.toFixed(2)}</span></div>
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">H</span> <span className="text-success">{data[data.length - 1]?.high?.toFixed(2)}</span></div>
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">L</span> <span className="text-destructive">{data[data.length - 1]?.low?.toFixed(2)}</span></div>
          <div className="flex gap-1.5"><span className="text-muted-foreground font-bold">C</span> <span className={data[data.length - 1]?.close >= data[data.length - 1]?.open ? "text-success" : "text-destructive"}>{data[data.length - 1]?.close?.toFixed(2)}</span></div>
        </div>

        {indicatorKeys.length > 0 && (
          <div className="hidden sm:flex flex-wrap gap-2 text-[9px] md:text-xs font-semibold">
            {indicatorKeys.map((key, idx) => (
              <span key={key} className="flex items-center gap-1 border border-border/50 px-1.5 py-0.5 rounded-sm bg-secondary/20" style={{ color: INDICATOR_COLORS[idx % INDICATOR_COLORS.length] }}>
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: INDICATOR_COLORS[idx % INDICATOR_COLORS.length] }} />
                <span className="uppercase">{key}</span>
              </span>
            ))}
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={processedData}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} vertical={false} />
          <XAxis
            dataKey="time"
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 10 }}
            minTickGap={30}
          />
          <YAxis
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 10 }}
            domain={['auto', 'auto']}
            orientation="right"
            width={50}
          />
          <Tooltip content={<CustomTooltip />} />

          <ReferenceLine
            y={latestPrice}
            stroke="currentColor"
            strokeDasharray="3 3"
            opacity={0.3}
            label={{ position: 'right', value: latestPrice?.toFixed(2), fill: 'currentColor', fontSize: 10, offset: 5 }}
          />

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

          {/* Dynamic Indicators Overlay */}
          {indicatorKeys.map((key, idx) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={INDICATOR_COLORS[idx % INDICATOR_COLORS.length]}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
              name={key.toUpperCase()}
            />
          ))}

          {/* Gann Angles */}
          {showGannAngles && (
            <>
              <ReferenceLine y={gannAngles["1x1"]} stroke="hsl(var(--primary))" strokeWidth={1} opacity={0.4} />
              <ReferenceLine y={gannAngles["2x1"]} stroke="hsl(var(--chart-2))" strokeDasharray="3 3" opacity={0.4} />
              <ReferenceLine y={gannAngles["1x2"]} stroke="hsl(var(--chart-3))" strokeDasharray="3 3" opacity={0.4} />
            </>
          )}

          {/* External Overlays */}
          {children}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
