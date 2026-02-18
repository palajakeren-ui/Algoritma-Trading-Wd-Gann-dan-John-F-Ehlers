import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";

interface GannFanFullModuleProps {
  currentPrice: number;
}

// Full Gann Fan angles: 16x1, 8x1, 4x1, 3x1, 2x1, 1x1, 1x2, 1x3, 1x4, 1x8, 1x16
const GANN_FAN_ANGLES = [
  { ratio: "16x1", slope: 86.42, multiplier: 0.970, type: "extreme support" },
  { ratio: "8x1", slope: 82.87, multiplier: 0.978, type: "strong support" },
  { ratio: "4x1", slope: 75.96, multiplier: 0.985, type: "support" },
  { ratio: "3x1", slope: 71.57, multiplier: 0.990, type: "support" },
  { ratio: "2x1", slope: 63.43, multiplier: 0.995, type: "minor support" },
  { ratio: "1x1", slope: 45.00, multiplier: 1.000, type: "balance" },
  { ratio: "1x2", slope: 26.57, multiplier: 1.005, type: "minor resistance" },
  { ratio: "1x3", slope: 18.43, multiplier: 1.010, type: "resistance" },
  { ratio: "1x4", slope: 14.04, multiplier: 1.015, type: "resistance" },
  { ratio: "1x8", slope: 7.13, multiplier: 1.022, type: "strong resistance" },
  { ratio: "1x16", slope: 3.58, multiplier: 1.030, type: "extreme resistance" },
];

const GannFanFullModule = ({ currentPrice }: GannFanFullModuleProps) => {
  const getTypeColor = (type: string) => {
    if (type.includes("support")) return "border-success text-success";
    if (type.includes("resistance")) return "border-destructive text-destructive";
    return "border-primary text-primary";
  };

  const levels = GANN_FAN_ANGLES.map(item => ({
    ...item,
    price: Number((currentPrice * item.multiplier).toFixed(2)),
  }));

  // SVG Fan visualization
  const width = 350;
  const height = 250;
  const startX = 30;
  const startY = height - 30;

  return (
    <Card className="p-4 md:p-6 border-border bg-card">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-primary" />
        <h4 className="text-lg font-semibold text-foreground">Gann Fan Full Module</h4>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* SVG Visualization */}
        <div className="flex justify-center overflow-hidden">
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="w-full max-w-[350px]">
            {/* Grid lines */}
            {[0.25, 0.5, 0.75, 1].map((scale, idx) => (
              <line
                key={`h-${idx}`}
                x1={startX}
                y1={startY - (height - 60) * scale}
                x2={width - 20}
                y2={startY - (height - 60) * scale}
                stroke="hsl(var(--border))"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
            ))}

            {/* Fan lines */}
            {GANN_FAN_ANGLES.map((item, idx) => {
              const radians = item.slope * (Math.PI / 180);
              const endX = width - 20;
              const lineLength = endX - startX;
              const endY = startY - lineLength * Math.tan(radians);
              
              const isBalance = item.ratio === "1x1";
              const isSupport = item.type.includes("support");
              const isResistance = item.type.includes("resistance");
              
              return (
                <g key={idx}>
                  <line
                    x1={startX}
                    y1={startY}
                    x2={endX}
                    y2={Math.max(10, endY)}
                    stroke={isBalance ? "hsl(var(--primary))" : isSupport ? "hsl(var(--success))" : "hsl(var(--destructive))"}
                    strokeWidth={isBalance ? 2.5 : 1.5}
                    opacity={0.8}
                  />
                  <text
                    x={endX + 5}
                    y={Math.max(15, endY)}
                    fill={isBalance ? "hsl(var(--primary))" : isSupport ? "hsl(var(--success))" : "hsl(var(--destructive))"}
                    fontSize="9"
                    fontWeight={isBalance ? "bold" : "normal"}
                  >
                    {item.ratio}
                  </text>
                </g>
              );
            })}

            {/* Origin point */}
            <circle cx={startX} cy={startY} r={6} fill="hsl(var(--primary))" />
            
            {/* Labels */}
            <text x={startX} y={height - 5} fill="hsl(var(--muted-foreground))" fontSize="10" textAnchor="middle">
              Time
            </text>
            <text x={10} y={startY / 2} fill="hsl(var(--muted-foreground))" fontSize="10" textAnchor="middle" transform={`rotate(-90, 10, ${startY / 2})`}>
              Price
            </text>
          </svg>
        </div>

        {/* Price levels list */}
        <div className="space-y-2 max-h-[220px] overflow-y-auto">
          {levels.map((item, idx) => (
            <div key={idx} className="p-2 bg-secondary/50 rounded">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-bold text-foreground">{item.ratio}</span>
                <Badge variant="outline" className={`text-xs ${getTypeColor(item.type)}`}>
                  {item.type.split(' ').pop()}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-mono text-foreground">${item.price.toLocaleString()}</span>
                <span className="text-xs text-muted-foreground">{item.slope.toFixed(2)}° slope</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 p-3 bg-secondary/30 rounded-lg">
        <p className="text-xs text-muted-foreground">
          <strong>1x1 Balance Line:</strong> The 45° angle represents perfect time-price equilibrium. 
          Prices above = bullish, below = bearish.
        </p>
      </div>
    </Card>
  );
};

export default GannFanFullModule;
