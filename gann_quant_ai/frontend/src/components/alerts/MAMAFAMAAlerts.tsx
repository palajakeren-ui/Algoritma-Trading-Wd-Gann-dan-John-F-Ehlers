import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bell, BellOff, TrendingUp, TrendingDown, Clock } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface Alert {
  id: string;
  time: string;
  type: 'bullish' | 'bearish';
  mama: number;
  fama: number;
  symbol: string;
  timeframe: string;
}

const MAMAFAMAAlerts = () => {
  const [alertsEnabled, setAlertsEnabled] = useState(true);

  // Mock alert data
  const recentAlerts: Alert[] = [
    {
      id: "1",
      time: "2024-01-20 14:35:22",
      type: "bullish",
      mama: 104.450,
      fama: 104.350,
      symbol: "EURUSD",
      timeframe: "H1"
    },
    {
      id: "2",
      time: "2024-01-20 13:15:08",
      type: "bearish",
      mama: 43100.25,
      fama: 43250.50,
      symbol: "BTCUSDT",
      timeframe: "M15"
    },
    {
      id: "3",
      time: "2024-01-20 11:42:51",
      type: "bullish",
      mama: 2048.80,
      fama: 2045.30,
      symbol: "XAUUSD",
      timeframe: "H4"
    }
  ];

  const toggleAlerts = () => {
    setAlertsEnabled(!alertsEnabled);
    if (!alertsEnabled) {
      toast.success("MAMA/FAMA crossover alerts enabled");
    } else {
      toast.info("MAMA/FAMA crossover alerts disabled");
    }
  };

  return (
    <Card className="p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">MAMA/FAMA Crossover Alerts</h3>
        </div>
        <Button
          variant={alertsEnabled ? "default" : "outline"}
          size="sm"
          onClick={toggleAlerts}
          className="gap-2"
        >
          {alertsEnabled ? (
            <>
              <Bell className="w-4 h-4" />
              Enabled
            </>
          ) : (
            <>
              <BellOff className="w-4 h-4" />
              Disabled
            </>
          )}
        </Button>
      </div>

      <div className="space-y-3">
        {recentAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-4 rounded-lg border-l-4 ${
              alert.type === 'bullish'
                ? 'border-l-success bg-success/5 border border-success/20'
                : 'border-l-destructive bg-destructive/5 border border-destructive/20'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Badge
                    variant={alert.type === 'bullish' ? 'default' : 'destructive'}
                    className="flex items-center gap-1"
                  >
                    {alert.type === 'bullish' ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {alert.type.toUpperCase()} CROSSOVER
                  </Badge>
                  <span className="text-sm font-semibold text-foreground">
                    {alert.symbol}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {alert.timeframe}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div>
                    <p className="text-xs text-muted-foreground">MAMA</p>
                    <p className="text-sm font-mono font-semibold text-primary">
                      {alert.mama.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">FAMA</p>
                    <p className="text-sm font-mono font-semibold text-accent">
                      {alert.fama.toFixed(2)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  {alert.time}
                </div>
              </div>

              <div className="text-right">
                <p className="text-xs text-muted-foreground mb-1">Action</p>
                <Badge
                  variant="outline"
                  className={alert.type === 'bullish' ? 'text-success' : 'text-destructive'}
                >
                  {alert.type === 'bullish' ? 'LONG' : 'SHORT'}
                </Badge>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-border/50">
              <p className="text-xs text-muted-foreground">
                {alert.type === 'bullish' 
                  ? '📈 MAMA crossed above FAMA - Potential uptrend beginning'
                  : '📉 MAMA crossed below FAMA - Potential downtrend beginning'}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-4 rounded-lg bg-muted/50 border border-border">
        <h5 className="text-sm font-semibold text-foreground mb-2">Alert Settings</h5>
        <div className="space-y-2 text-xs text-muted-foreground">
          <p>✓ Real-time crossover detection</p>
          <p>✓ Multi-timeframe monitoring (M1 - MN)</p>
          <p>✓ Push notifications on crossovers</p>
          <p>✓ Historical alert log (last 50 alerts)</p>
        </div>
      </div>
    </Card>
  );
};

export default MAMAFAMAAlerts;
