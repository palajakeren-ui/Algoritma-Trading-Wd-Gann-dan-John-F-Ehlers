import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Activity, TrendingUp, TrendingDown, RefreshCw, BarChart3, Plus, X, Trash2 } from "lucide-react";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { CandlestickChart } from "@/components/charts/CandlestickChart";

interface InstrumentData {
  symbol: string;
  name: string;
  price: number;
  mama: number;
  fama: number;
  fisher: number;
  cyberCycle: number;
  bandpass: number;
  signal: "Bullish" | "Bearish" | "Neutral";
  confidence: number;
}

interface TimeframeData {
  timeframe: string;
  signal: "Bullish" | "Bearish" | "Neutral";
  strength: number;
  mama: number;
  fama: number;
}

const TIMEFRAMES = ["1m", "2m", "3m", "5m", "15m", "30m", "45m", "1h", "2h", "3h", "4h", "1d", "3d", "1w", "1mo", "3mo", "6mo", "1y"].map(t => t.toUpperCase());

const DEFAULT_INSTRUMENTS = [
  { symbol: "BTCUSDT", name: "Bitcoin" },
  { symbol: "ETHUSDT", name: "Ethereum" },
  { symbol: "BNBUSDT", name: "BNB" },
  { symbol: "XRPUSDT", name: "XRP" },
  { symbol: "SOLUSDT", name: "Solana" },
  { symbol: "ADAUSDT", name: "Cardano" },
];

const generateInstrumentData = (symbol: string, name: string): InstrumentData => {
  const basePrice = Math.random() * 50000 + 100;
  const signal = Math.random() > 0.6 ? "Bullish" : Math.random() > 0.5 ? "Bearish" : "Neutral";
  return {
    symbol,
    name,
    price: basePrice,
    mama: basePrice * (0.995 + Math.random() * 0.01),
    fama: basePrice * (0.99 + Math.random() * 0.01),
    fisher: (Math.random() * 4 - 2).toFixed(2) as unknown as number,
    cyberCycle: (Math.random() * 0.1 - 0.05).toFixed(3) as unknown as number,
    bandpass: (Math.random() * 0.06 - 0.03).toFixed(3) as unknown as number,
    signal,
    confidence: Math.floor(Math.random() * 40) + 55,
  };
};

const generateTimeframeData = (): TimeframeData[] => TIMEFRAMES.map(tf => ({
  timeframe: tf,
  signal: Math.random() > 0.5 ? "Bullish" : Math.random() > 0.5 ? "Bearish" : "Neutral",
  strength: Math.floor(Math.random() * 40) + 60,
  mama: 97400 + Math.random() * 200,
  fama: 97200 + Math.random() * 200,
}));

const generateCorrelationMatrix = (instruments: InstrumentData[]) => {
  const matrix: { pair: string; correlation: number }[] = [];
  for (let i = 0; i < instruments.length; i++) {
    for (let j = i + 1; j < instruments.length; j++) {
      matrix.push({
        pair: `${instruments[i].symbol}/${instruments[j].symbol}`,
        correlation: (Math.random() * 2 - 1).toFixed(2) as unknown as number,
      });
    }
  }
  return matrix;
};

const generateChartData = () => {
  let prevClose = 97500;
  return Array.from({ length: 30 }, (_, i) => {
    const open = prevClose + (Math.random() - 0.5) * 50;
    const close = open + (Math.random() - 0.5) * 100;
    const high = Math.max(open, close) + Math.random() * 20;
    const low = Math.min(open, close) - Math.random() * 20;
    prevClose = close;
    return {
      time: i,
      date: `T-${30 - i}`,
      open, high, low, close,
      price: close,
      mama: close * (0.999 + Math.random() * 0.002),
      fama: close * (0.998 + Math.random() * 0.002),
      fisher: Math.sin(i / 4) * 1.5,
      bandpass: Math.sin(i / 3) * 0.03,
    };
  });
};

interface EhlersPanelProps {
  currentSymbol?: string;
  currentPrice?: number;
  currentTimeframe?: string;
}

const EhlersDSPPanel = ({ currentSymbol, currentPrice, currentTimeframe }: EhlersPanelProps = {}) => {
  const [instrumentsList, setInstrumentsList] = useState(DEFAULT_INSTRUMENTS);
  const [instruments, setInstruments] = useState<InstrumentData[]>(() =>
    instrumentsList.map(i => generateInstrumentData(i.symbol, i.name))
  );
  const [timeframeData, setTimeframeData] = useState<TimeframeData[]>(generateTimeframeData());
  const [correlationMatrix, setCorrelationMatrix] = useState(generateCorrelationMatrix(instruments));
  const [chartData, setChartData] = useState(generateChartData());
  const [selectedInstrument, setSelectedInstrument] = useState("BTCUSDT");
  const [isLive, setIsLive] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSymbol, setNewSymbol] = useState("");
  const [newName, setNewName] = useState("");

  // Sync with Props
  useEffect(() => {
    if (currentSymbol) {
      const upperSymbol = currentSymbol.toUpperCase();
      setSelectedInstrument(upperSymbol);

      setInstrumentsList(prev => {
        if (prev.some(i => i.symbol === upperSymbol)) return prev;
        return [{ symbol: upperSymbol, name: upperSymbol }, ...prev];
      });

      // Update specific instrument price if provided
      if (currentPrice) {
        setInstruments(prev => prev.map(i => i.symbol === upperSymbol ? { ...i, price: currentPrice } : i));
      }
    }
  }, [currentSymbol, currentPrice]);

  useEffect(() => {
    if (currentTimeframe) {
      // Logic to highlight timeframe (could filter or sort, but for now just console or visual cue if needed)
      // Since timeframeData is generated randomly, we might want to ensure the prop timeframe exists
      // For now, let's just make sure we re-generate or focus.
    }
  }, [currentTimeframe]);

  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(() => {
      setInstruments(instrumentsList.map(i => generateInstrumentData(i.symbol, i.name)));
      setTimeframeData(generateTimeframeData());
      setChartData(generateChartData());
    }, 3000);
    return () => clearInterval(interval);
  }, [isLive, instrumentsList]);

  useEffect(() => {
    setCorrelationMatrix(generateCorrelationMatrix(instruments));
  }, [instruments]);

  const handleAddInstrument = () => {
    if (!newSymbol.trim()) return;
    const newInst = {
      symbol: newSymbol.toUpperCase(),
      name: newName.trim() || newSymbol.toUpperCase(),
    };
    setInstrumentsList([...instrumentsList, newInst]);
    setNewSymbol("");
    setNewName("");
    setShowAddForm(false);
  };

  const handleDeleteInstrument = (symbol: string) => {
    if (instrumentsList.length <= 1) return;
    const newList = instrumentsList.filter(i => i.symbol !== symbol);
    setInstrumentsList(newList);
    if (selectedInstrument === symbol) {
      setSelectedInstrument(newList[0].symbol);
    }
  };

  const getSignalBadge = (signal: string, confidence: number) => {
    const colorClass = signal === "Bullish" ? "bg-success text-success-foreground" :
      signal === "Bearish" ? "bg-destructive text-destructive-foreground" :
        "bg-muted text-muted-foreground";
    return <Badge className={colorClass}>{signal} ({confidence}%)</Badge>;
  };

  const getCorrelationColor = (corr: number) => {
    if (corr > 0.7) return "text-success";
    if (corr < -0.7) return "text-destructive";
    if (Math.abs(corr) < 0.3) return "text-muted-foreground";
    return corr > 0 ? "text-accent" : "text-warning";
  };

  return (
    <Card className="p-4 md:p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-6 h-6 text-accent" />
          <h2 className="text-lg md:text-xl font-semibold text-foreground">Ehlers DSP Analysis</h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={isLive ? "border-success text-success" : ""}>
            {isLive ? "Live" : "Paused"}
          </Badge>
          <Button variant="outline" size="sm" onClick={() => setIsLive(!isLive)}>
            <RefreshCw className={`w-4 h-4 ${isLive ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowAddForm(!showAddForm)}>
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Add Instrument Form */}
      {showAddForm && (
        <div className="p-4 mb-4 bg-secondary/30 rounded-lg border border-border">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-foreground">Add Instrument to DSP Analysis</h4>
            <Button variant="ghost" size="sm" onClick={() => setShowAddForm(false)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Input
              placeholder="Symbol (e.g., DOGEUSDT)"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
            />
            <Input
              placeholder="Name (e.g., Dogecoin)"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
            <Button onClick={handleAddInstrument} disabled={!newSymbol.trim()}>
              <Plus className="w-4 h-4 mr-2" />
              Add to Analysis
            </Button>
          </div>
        </div>
      )}

      <Tabs defaultValue="multi-instrument" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="multi-instrument" className="text-xs md:text-sm">Multi-Instrument</TabsTrigger>
          <TabsTrigger value="multi-timeframe" className="text-xs md:text-sm">Multi-Timeframe</TabsTrigger>
          <TabsTrigger value="correlation" className="text-xs md:text-sm">Correlation Matrix</TabsTrigger>
        </TabsList>

        {/* Multi-Instrument Analysis */}
        <TabsContent value="multi-instrument" className="space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-2 text-muted-foreground">Instrument</th>
                  <th className="text-right p-2 text-muted-foreground">Price</th>
                  <th className="text-right p-2 text-muted-foreground">MAMA</th>
                  <th className="text-right p-2 text-muted-foreground">FAMA</th>
                  <th className="text-right p-2 text-muted-foreground">Fisher</th>
                  <th className="text-right p-2 text-muted-foreground">Cyber Cycle</th>
                  <th className="text-center p-2 text-muted-foreground">Signal</th>
                  <th className="text-center p-2 text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody>
                {instruments.map((inst, idx) => (
                  <tr key={idx} className="border-b border-border/50 hover:bg-secondary/30 group">
                    <td className="p-2">
                      <div className="font-semibold text-foreground">{inst.symbol}</div>
                      <div className="text-xs text-muted-foreground">{inst.name}</div>
                    </td>
                    <td className="text-right p-2 font-mono text-foreground">${inst.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                    <td className="text-right p-2 font-mono text-primary">{Number(inst.mama).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                    <td className="text-right p-2 font-mono text-accent">{Number(inst.fama).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                    <td className={`text-right p-2 font-mono ${Number(inst.fisher) > 0 ? 'text-success' : 'text-destructive'}`}>
                      {Number(inst.fisher) > 0 ? '+' : ''}{Number(inst.fisher).toFixed(2)}
                    </td>
                    <td className={`text-right p-2 font-mono ${Number(inst.cyberCycle) > 0 ? 'text-success' : 'text-destructive'}`}>
                      {Number(inst.cyberCycle) > 0 ? '+' : ''}{Number(inst.cyberCycle).toFixed(3)}
                    </td>
                    <td className="text-center p-2">{getSignalBadge(inst.signal, inst.confidence)}</td>
                    <td className="text-center p-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/20 hover:text-destructive"
                        onClick={() => handleDeleteInstrument(inst.symbol)}
                        disabled={instrumentsList.length <= 1}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* Multi-Timeframe Analysis */}
        <TabsContent value="multi-timeframe" className="space-y-4">
          <div className="flex items-center gap-4 mb-4">
            <Select value={selectedInstrument} onValueChange={setSelectedInstrument}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {instruments.map(inst => (
                  <SelectItem key={inst.symbol} value={inst.symbol}>{inst.symbol}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-9 gap-2">
            {timeframeData.map((tf, idx) => (
              <div key={idx} className="p-3 bg-secondary/50 rounded-lg text-center border border-border">
                <div className="text-xs text-muted-foreground mb-1">{tf.timeframe}</div>
                <Badge className={
                  tf.signal === "Bullish" ? "bg-success text-success-foreground" :
                    tf.signal === "Bearish" ? "bg-destructive text-destructive-foreground" :
                      "bg-muted text-muted-foreground"
                } variant="outline">
                  {tf.signal === "Bullish" ? <TrendingUp className="w-3 h-3" /> :
                    tf.signal === "Bearish" ? <TrendingDown className="w-3 h-3" /> :
                      <BarChart3 className="w-3 h-3" />}
                </Badge>
                <div className="text-sm font-bold text-foreground mt-1">{tf.strength}%</div>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <CandlestickChart data={chartData} height={300} indicatorKeys={['mama', 'fama']} showGannAngles={false} />
          </div>
        </TabsContent>

        {/* Correlation Matrix */}
        <TabsContent value="correlation" className="space-y-4">
          <div className="p-4 bg-secondary/30 rounded-lg">
            <h3 className="text-sm font-semibold text-foreground mb-3">DSP Signal Correlation Matrix</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {correlationMatrix.slice(0, 15).map((item, idx) => (
                <div key={idx} className="p-2 bg-secondary/50 rounded border border-border text-center">
                  <div className="text-xs text-muted-foreground truncate">{item.pair}</div>
                  <div className={`text-lg font-bold ${getCorrelationColor(Number(item.correlation))}`}>
                    {Number(item.correlation).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-success/10 border border-success/30 rounded-lg">
              <div className="text-sm text-muted-foreground">Strong Positive</div>
              <div className="text-2xl font-bold text-success">
                {correlationMatrix.filter(c => Number(c.correlation) > 0.7).length}
              </div>
              <div className="text-xs text-muted-foreground">pairs correlated &gt; 0.7</div>
            </div>
            <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg">
              <div className="text-sm text-muted-foreground">Strong Negative</div>
              <div className="text-2xl font-bold text-destructive">
                {correlationMatrix.filter(c => Number(c.correlation) < -0.7).length}
              </div>
              <div className="text-xs text-muted-foreground">pairs correlated &lt; -0.7</div>
            </div>
            <div className="p-4 bg-muted border border-border rounded-lg">
              <div className="text-sm text-muted-foreground">Uncorrelated</div>
              <div className="text-2xl font-bold text-foreground">
                {correlationMatrix.filter(c => Math.abs(Number(c.correlation)) < 0.3).length}
              </div>
              <div className="text-xs text-muted-foreground">pairs |corr| &lt; 0.3</div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
};

export default EhlersDSPPanel;
