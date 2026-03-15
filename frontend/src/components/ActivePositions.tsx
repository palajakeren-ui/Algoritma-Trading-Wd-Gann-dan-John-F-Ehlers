import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown } from "lucide-react";

interface Position {
  symbol: string;
  type: "LONG" | "SHORT";
  entry: number;
  current: number;
  pnl: number;
  pnlPercent: number;
  size: string;
  sl: number;
  tp: number;
}

const positions: Position[] = [
  {
    symbol: "EURUSD",
    type: "LONG",
    entry: 1.0850,
    current: 1.0875,
    pnl: 125.50,
    pnlPercent: 2.3,
    size: "0.5 lot",
    sl: 1.0820,
    tp: 1.0920,
  },
  {
    symbol: "BTCUSDT",
    type: "LONG",
    entry: 42800,
    current: 43250,
    pnl: 450.00,
    pnlPercent: 1.05,
    size: "0.1 BTC",
    sl: 42200,
    tp: 44500,
  },
  {
    symbol: "XAUUSD",
    type: "SHORT",
    entry: 2050.20,
    current: 2045.30,
    pnl: 49.00,
    pnlPercent: 0.24,
    size: "0.02 oz",
    sl: 2060.00,
    tp: 2030.00,
  },
];

export const ActivePositions = () => {
  return (
    <Card className="p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">Active Positions</h2>
        <Badge variant="outline" className="bg-accent/10 text-accent border-accent/20">
          {positions.length} Open
        </Badge>
      </div>

      <div className="space-y-3">
        {positions.map((position, idx) => (
          <div
            key={idx}
            className="p-4 rounded-lg bg-secondary/50 border border-border hover:bg-secondary transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div>
                  <h3 className="font-semibold text-foreground">{position.symbol}</h3>
                  <p className="text-xs text-muted-foreground">{position.size}</p>
                </div>
                <Badge
                  variant={position.type === "LONG" ? "default" : "destructive"}
                  className={position.type === "LONG" ? "bg-success" : ""}
                >
                  {position.type}
                </Badge>
              </div>

              <div className="text-right">
                <div
                  className={`text-lg font-bold ${
                    position.pnl > 0 ? "text-success" : "text-destructive"
                  }`}
                >
                  ${position.pnl.toFixed(2)}
                </div>
                <div
                  className={`text-xs flex items-center justify-end ${
                    position.pnl > 0 ? "text-success" : "text-destructive"
                  }`}
                >
                  {position.pnl > 0 ? (
                    <TrendingUp className="w-3 h-3 mr-1" />
                  ) : (
                    <TrendingDown className="w-3 h-3 mr-1" />
                  )}
                  {position.pnlPercent.toFixed(2)}%
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 text-xs">
              <div>
                <p className="text-muted-foreground">Entry</p>
                <p className="font-mono text-foreground">{position.entry}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Current</p>
                <p className="font-mono text-foreground">{position.current}</p>
              </div>
              <div>
                <p className="text-muted-foreground">SL</p>
                <p className="font-mono text-destructive">{position.sl}</p>
              </div>
              <div>
                <p className="text-muted-foreground">TP</p>
                <p className="font-mono text-success">{position.tp}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-border">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Total P&L</p>
            <p className="text-xl font-bold text-success">+$624.50</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">ROI</p>
            <p className="text-xl font-bold text-success">+1.19%</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
