import { Card } from "@/components/ui/card";
import { calculateSquareOf9 } from "@/lib/gannCalculations";

interface GannSquareChartProps {
  centerValue: number;
}

export const GannSquareChart = ({ centerValue }: GannSquareChartProps) => {
  const square = calculateSquareOf9(centerValue);
  
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 text-foreground">
        Gann Square of 9
      </h3>
      
      <div className="relative w-full aspect-square max-w-md mx-auto">
        {/* Center */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 bg-primary rounded-full flex items-center justify-center border-2 border-primary-foreground">
          <span className="text-sm font-bold text-primary-foreground">
            {centerValue.toFixed(2)}
          </span>
        </div>
        
        {/* Rings */}
        {square.map((ring, idx) => (
          <div
            key={ring.ring}
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-border"
            style={{
              width: `${30 + ring.ring * 15}%`,
              height: `${30 + ring.ring * 15}%`,
            }}
          >
            {ring.values.slice(0, 4).map((value, i) => {
              const angle = (i * 90 * Math.PI) / 180;
              const radius = (15 + ring.ring * 7.5);
              const x = 50 + radius * Math.cos(angle);
              const y = 50 + radius * Math.sin(angle);
              
              return (
                <div
                  key={i}
                  className="absolute text-xs font-medium text-muted-foreground"
                  style={{
                    left: `${x}%`,
                    top: `${y}%`,
                    transform: 'translate(-50%, -50%)',
                  }}
                >
                  {value.toFixed(1)}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">Key Levels</p>
          {square.slice(0, 3).map((ring) => (
            <div key={ring.ring} className="text-xs text-muted-foreground">
              Ring {ring.ring}: {ring.values[0].toFixed(2)} - {ring.values[ring.values.length - 1].toFixed(2)}
            </div>
          ))}
        </div>
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">Cardinal Points</p>
          <div className="text-xs text-muted-foreground">
            0°: {square[0]?.values[0]?.toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground">
            90°: {square[0]?.values[Math.floor(square[0].values.length / 4)]?.toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground">
            180°: {square[0]?.values[Math.floor(square[0].values.length / 2)]?.toFixed(2)}
          </div>
        </div>
      </div>
    </Card>
  );
};
