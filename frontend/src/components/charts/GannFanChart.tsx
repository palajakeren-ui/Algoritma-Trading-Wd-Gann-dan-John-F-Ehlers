import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";

export const GannFanChart = () => {
  const hexagonAngles = [
    { angle: "60°", price: "103.800", type: "support harmonic" },
    { angle: "120°", price: "104.500", type: "resistance harmonic" },
    { angle: "180°", price: "105.100", type: "full hexagon pivot" },
  ];

  const gannFanAngles = [
    { ratio: "8x1", price: "104.000", slope: "82° slope", type: "support" },
    { ratio: "4x1", price: "104.100", slope: "76° slope", type: "support" },
    { ratio: "1x1", price: "104.200", slope: "45° slope", type: "support" },
    { ratio: "2x1", price: "104.300", slope: "26.5° slope", type: "support" },
    { ratio: "1x2", price: "104.700", slope: "63.5° slope", type: "resistance" },
    { ratio: "3x1", price: "105.200", slope: "18° slope", type: "resistance" },
    { ratio: "1x3", price: "104.000", slope: "18.4° slope", type: "support" },
    { ratio: "1x4", price: "104.150", slope: "14° slope", type: "resistance" },
    { ratio: "1x8", price: "104.050", slope: "7° slope", type: "resistance" },
  ];

  return (
    <div className="space-y-6">
      <Card className="p-6 border-border bg-card">
        <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center">
          <Activity className="w-6 h-6 mr-2 text-accent" />
          Hexagon Geometry
        </h3>
        <div className="space-y-3">
          {hexagonAngles.map((item, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 border border-border hover:bg-secondary/70 transition-colors"
            >
              <div className="flex items-center gap-4">
                <span className="text-2xl font-bold text-accent">{item.angle}</span>
                <span className="text-xl font-mono text-foreground">{item.price}</span>
              </div>
              <Badge 
                variant="outline" 
                className={item.type.includes("support") ? "border-success text-success" : "border-destructive text-destructive"}
              >
                {item.type}
              </Badge>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-6 border-border bg-card">
        <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center">
          <Activity className="w-6 h-6 mr-2 text-success" />
          Gann Fan Angles (Full Module)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {gannFanAngles.map((item, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg bg-secondary/50 border border-border hover:bg-secondary/70 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg font-bold text-foreground">{item.ratio}</span>
                <Badge 
                  variant="outline"
                  className={item.type === "support" ? "border-success text-success bg-success/10" : "border-destructive text-destructive bg-destructive/10"}
                >
                  {item.type}
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-xl font-mono text-foreground">{item.price}</p>
                <p className="text-sm text-muted-foreground">{item.slope}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-6 border-border bg-card bg-gradient-to-br from-card to-secondary/30">
        <h3 className="text-lg font-semibold text-foreground mb-4">Visual Representation</h3>
        <div className="bg-secondary/30 rounded-lg h-[300px] flex items-center justify-center border border-border">
          <div className="text-center">
            <Activity className="w-16 h-16 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Gann Fan Angle Visualization</p>
            <p className="text-xs text-muted-foreground mt-2">Interactive chart coming soon</p>
          </div>
        </div>
      </Card>
    </div>
  );
};
