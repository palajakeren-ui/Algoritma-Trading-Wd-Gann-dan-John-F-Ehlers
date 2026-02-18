import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, TrendingUp, Target } from "lucide-react";

const Forecasting = () => {
  const predictions = [
    { date: "Dec 20, 2024", price: 1.0892, confidence: 82, type: "High" },
    { date: "Dec 25, 2024", price: 1.0875, confidence: 78, type: "Turn" },
    { date: "Dec 28, 2024", price: 1.0845, confidence: 85, type: "Low" },
    { date: "Jan 02, 2025", price: 1.0910, confidence: 80, type: "High" },
    { date: "Jan 08, 2025", price: 1.0880, confidence: 75, type: "Turn" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Price Forecasting</h1>
          <p className="text-muted-foreground">Gann Wave & Time Cycle Predictions</p>
        </div>
        <Button>
          <Target className="w-4 h-4 mr-2" />
          Generate Forecast
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6 border-border bg-card">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-success" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Next Major Turn</p>
              <p className="text-xl font-bold text-foreground">Dec 28, 2024</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-success/10 text-success border-success/20">
            85% Confidence
          </Badge>
        </Card>

        <Card className="p-6 border-border bg-card">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
              <Target className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Projected Price</p>
              <p className="text-xl font-bold text-foreground">1.0845</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-accent/10 text-accent border-accent/20">
            Gann Wave Analysis
          </Badge>
        </Card>

        <Card className="p-6 border-border bg-card">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-warning/10 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-warning" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Cycle Phase</p>
              <p className="text-xl font-bold text-foreground">Topping</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-warning/10 text-warning border-warning/20">
            Jupiter-Saturn Aspect
          </Badge>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 border-border bg-card">
          <h2 className="text-xl font-semibold text-foreground mb-4">Daily Predictions</h2>
          <div className="space-y-3">
            {predictions.map((pred, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 border border-border"
              >
                <div className="flex items-center space-x-4">
                  <Calendar className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-semibold text-foreground">{pred.date}</p>
                    <p className="text-xs text-muted-foreground">{pred.type} Point</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-foreground">{pred.price}</p>
                  <p className="text-xs text-success">{pred.confidence}% confidence</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6 border-border bg-card">
          <h2 className="text-xl font-semibold text-foreground mb-4">
            Gann Wave Projection
          </h2>
          <div className="bg-secondary/30 rounded-lg h-[400px] flex items-center justify-center border border-border">
            <div className="text-center space-y-4">
              <Target className="w-16 h-16 text-muted-foreground mx-auto" />
              <div>
                <p className="text-lg font-semibold text-foreground">Wave Chart</p>
                <p className="text-sm text-muted-foreground">
                  Spiral projection of price & time
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6 border-border bg-card">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Long-term Forecast (365 Days)
        </h2>
        <div className="bg-secondary/30 rounded-lg h-[300px] flex items-center justify-center border border-border">
          <div className="text-center space-y-4">
            <TrendingUp className="w-16 h-16 text-muted-foreground mx-auto" />
            <div>
              <p className="text-lg font-semibold text-foreground">Annual Projection</p>
              <p className="text-sm text-muted-foreground">
                Gann Square of 360 cycle analysis
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Forecasting;
