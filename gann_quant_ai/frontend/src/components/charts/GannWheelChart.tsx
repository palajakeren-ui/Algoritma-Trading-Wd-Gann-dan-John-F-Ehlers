import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface GannWheelChartProps {
  currentPrice: number;
}

export const GannWheelChart = ({ currentPrice }: GannWheelChartProps) => {
  const degrees = Array.from({ length: 12 }, (_, i) => i * 30);
  const zodiacSigns = [
    "♈", "♉", "♊", "♋", "♌", "♍",
    "♎", "♏", "♐", "♑", "♒", "♓"
  ];
  
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 text-foreground">
        Gann Wheel - Astro Cycles
      </h3>
      
      <div className="relative w-full aspect-square max-w-md mx-auto">
        {/* Outer circle with degrees */}
        <svg viewBox="0 0 400 400" className="w-full h-full">
          {/* Background circle */}
          <circle
            cx="200"
            cy="200"
            r="180"
            fill="hsl(var(--card))"
            stroke="hsl(var(--border))"
            strokeWidth="2"
          />
          
          {/* Inner circles */}
          <circle
            cx="200"
            cy="200"
            r="120"
            fill="none"
            stroke="hsl(var(--border))"
            strokeWidth="1"
          />
          <circle
            cx="200"
            cy="200"
            r="60"
            fill="hsl(var(--primary))"
            fillOpacity="0.1"
            stroke="hsl(var(--primary))"
            strokeWidth="2"
          />
          
          {/* Degree lines */}
          {degrees.map((degree, i) => {
            const angle = (degree - 90) * (Math.PI / 180);
            const x1 = 200 + 60 * Math.cos(angle);
            const y1 = 200 + 60 * Math.sin(angle);
            const x2 = 200 + 180 * Math.cos(angle);
            const y2 = 200 + 180 * Math.sin(angle);
            
            return (
              <g key={degree}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="hsl(var(--border))"
                  strokeWidth="1"
                />
                <text
                  x={200 + 155 * Math.cos(angle)}
                  y={200 + 155 * Math.sin(angle)}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="text-xs fill-muted-foreground"
                >
                  {degree}°
                </text>
                <text
                  x={200 + 140 * Math.cos(angle)}
                  y={200 + 140 * Math.sin(angle)}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="text-lg fill-primary"
                >
                  {zodiacSigns[i]}
                </text>
              </g>
            );
          })}
          
          {/* Center price */}
          <text
            x="200"
            y="200"
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-2xl font-bold fill-foreground"
          >
            {currentPrice.toFixed(2)}
          </text>
        </svg>
      </div>
      
      <div className="mt-6 flex flex-wrap gap-2">
        <Badge variant="outline">Cardinal: 0° 90° 180° 270°</Badge>
        <Badge variant="outline">Fixed: 45° 135° 225° 315°</Badge>
      </div>
    </Card>
  );
};
