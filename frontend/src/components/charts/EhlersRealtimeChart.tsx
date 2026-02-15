import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ComposedChart, Area
} from "recharts";
import { generateRealtimeFilterData } from "@/lib/ehlersFilters";
import { CandlestickChart } from "@/components/charts/CandlestickChart";

interface EhlersRealtimeChartProps {
  currentPrice?: number;
}

const EhlersRealtimeChart = ({ currentPrice = 47509 }: EhlersRealtimeChartProps) => {
  const [data, setData] = useState(() => generateRealtimeFilterData(currentPrice));
  const [isLive, setIsLive] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState("all");

  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      setData(prev => {
        const newData = [...prev.slice(1)];
        const lastCandle = prev[prev.length - 1];

        // Simulating a new candle from the previous close
        const open = lastCandle.close;
        const close = open + (Math.random() - 0.5) * 60;
        const high = Math.max(open, close) + Math.random() * 20;
        const low = Math.min(open, close) - Math.random() * 20;

        const time = new Date();
        const timeStr = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        newData.push({
          time: timeStr,
          date: time.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          open: Number(open.toFixed(2)),
          high: Number(high.toFixed(2)),
          low: Number(low.toFixed(2)),
          close: Number(close.toFixed(2)),
          price: Number(close.toFixed(2)),
          fisher: Number((Math.sin(Date.now() / 10000) * 1.5).toFixed(3)),
          bandpass: Number((Math.sin(Date.now() / 15000) * 0.02).toFixed(4)),
          superSmoother: Number((close * 0.998).toFixed(2)),
          roofing: Number((Math.sin(Date.now() / 20000) * 0.015).toFixed(4)),
          cyberCycle: Number((Math.sin(Date.now() / 12000) * 0.025).toFixed(4)),
          decycler: Number((close * 0.995).toFixed(2)),
        });

        return newData;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isLive]);

  return (
    <Card className="p-4 md:p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">Real-Time Digital Filters</h3>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isLive ? "default" : "outline"} className={isLive ? "bg-success" : ""}>
            {isLive ? "Live" : "Paused"}
          </Badge>
          <Button variant="outline" size="sm" onClick={() => setIsLive(!isLive)}>
            <RefreshCw className={`w-4 h-4 ${isLive ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      <Tabs value={selectedFilter} onValueChange={setSelectedFilter} className="w-full">
        <div className="overflow-x-auto mb-4">
          <TabsList className="inline-flex gap-1 h-auto p-1">
            <TabsTrigger value="all" className="text-xs">All Filters</TabsTrigger>
            <TabsTrigger value="bandpass" className="text-xs">Bandpass</TabsTrigger>
            <TabsTrigger value="fisher" className="text-xs">Fisher</TabsTrigger>
            <TabsTrigger value="superSmoother" className="text-xs">Super Smoother</TabsTrigger>
            <TabsTrigger value="roofing" className="text-xs">Roofing</TabsTrigger>
            <TabsTrigger value="cyberCycle" className="text-xs">Cyber Cycle</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="all" className="mt-0">
          <CandlestickChart data={data} height={350} indicatorKeys={['superSmoother', 'decycler']} showGannAngles={false} />
        </TabsContent>

        <TabsContent value="bandpass" className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
              <Legend />
              <Area type="monotone" dataKey="bandpass" fill="hsl(var(--primary))" fillOpacity={0.2} stroke="hsl(var(--primary))" strokeWidth={2} name="Bandpass Filter" />
            </ComposedChart>
          </ResponsiveContainer>
        </TabsContent>

        <TabsContent value="fisher" className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
              <Legend />
              <Line type="monotone" dataKey="fisher" stroke="hsl(var(--accent))" strokeWidth={2} dot={false} name="Fisher Transform" />
            </LineChart>
          </ResponsiveContainer>
        </TabsContent>

        <TabsContent value="superSmoother" className="mt-0">
          <CandlestickChart data={data} height={350} indicatorKeys={['superSmoother']} showGannAngles={false} />
        </TabsContent>

        <TabsContent value="roofing" className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
              <Legend />
              <Area type="monotone" dataKey="roofing" fill="hsl(var(--chart-3))" fillOpacity={0.3} stroke="hsl(var(--chart-3))" strokeWidth={2} name="Roofing Filter" />
            </ComposedChart>
          </ResponsiveContainer>
        </TabsContent>

        <TabsContent value="cyberCycle" className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
              <Legend />
              <Line type="monotone" dataKey="cyberCycle" stroke="hsl(var(--chart-4))" strokeWidth={2} dot={false} name="Cyber Cycle" />
            </LineChart>
          </ResponsiveContainer>
        </TabsContent>
      </Tabs>

      <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-2">
        <div className="p-2 bg-secondary/50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Fisher</p>
          <p className="text-sm font-bold text-accent">{data[data.length - 1]?.fisher}</p>
        </div>
        <div className="p-2 bg-secondary/50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Bandpass</p>
          <p className="text-sm font-bold text-primary">{data[data.length - 1]?.bandpass}</p>
        </div>
        <div className="p-2 bg-secondary/50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Roofing</p>
          <p className="text-sm font-bold text-chart-3">{data[data.length - 1]?.roofing}</p>
        </div>
        <div className="p-2 bg-secondary/50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Cyber Cycle</p>
          <p className="text-sm font-bold text-chart-4">{data[data.length - 1]?.cyberCycle}</p>
        </div>
        <div className="p-2 bg-secondary/50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Signal</p>
          <Badge className="bg-success text-xs">Bullish</Badge>
        </div>
      </div>
    </Card>
  );
};

export default EhlersRealtimeChart;
