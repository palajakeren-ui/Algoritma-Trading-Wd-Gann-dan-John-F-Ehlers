import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  FileText, Download, Printer, Calendar, TrendingUp, TrendingDown, Activity, Target,
  BarChart3, PieChart, ArrowUpRight, ArrowDownRight, Filter, RefreshCw, Brain, Star, Waves
} from "lucide-react";
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPie, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ComposedChart } from "recharts";
import { toast } from "sonner";

const COLORS = ['hsl(var(--success))', 'hsl(var(--destructive))', 'hsl(var(--accent))', 'hsl(var(--primary))', 'hsl(var(--chart-3))'];

const tradingInstruments = [
  { symbol: "BTCUSD", name: "Bitcoin", trades: 45, winRate: 72.5, pnl: 8540.25, category: "Crypto", avgHoldTime: "4.2h", maxDD: 5.2 },
  { symbol: "ETHUSD", name: "Ethereum", trades: 32, winRate: 68.2, pnl: 3210.50, category: "Crypto", avgHoldTime: "3.8h", maxDD: 6.1 },
  { symbol: "XAUUSD", name: "Gold", trades: 28, winRate: 75.0, pnl: 4520.00, category: "Commodities", avgHoldTime: "6.5h", maxDD: 3.8 },
  { symbol: "EURUSD", name: "Euro/USD", trades: 15, winRate: 60.0, pnl: -850.25, category: "Forex", avgHoldTime: "2.1h", maxDD: 8.5 },
  { symbol: "SPX500", name: "S&P 500", trades: 7, winRate: 85.7, pnl: 2100.00, category: "Indices", avgHoldTime: "12.3h", maxDD: 2.1 },
];

const performanceByPeriod = [
  { period: "Week 1", pnl: 2500, trades: 28, winRate: 71, gannAccuracy: 78, ehlersScore: 82 },
  { period: "Week 2", pnl: 3200, trades: 32, winRate: 75, gannAccuracy: 82, ehlersScore: 85 },
  { period: "Week 3", pnl: -800, trades: 25, winRate: 52, gannAccuracy: 58, ehlersScore: 62 },
  { period: "Week 4", pnl: 4520, trades: 42, winRate: 78, gannAccuracy: 85, ehlersScore: 88 },
];

const gannPerformanceData = [
  { name: "Square of 9", accuracy: 78.5, signals: 45, profitable: 35, avgRR: 2.3 },
  { name: "Gann Fan", accuracy: 72.3, signals: 42, profitable: 30, avgRR: 2.1 },
  { name: "Hexagon 0-360°", accuracy: 74.8, signals: 38, profitable: 28, avgRR: 2.4 },
  { name: "Time Cycles", accuracy: 65.4, signals: 35, profitable: 23, avgRR: 1.9 },
  { name: "Gann Box", accuracy: 76.2, signals: 28, profitable: 21, avgRR: 2.2 },
  { name: "Elliott Wave", accuracy: 68.9, signals: 22, profitable: 15, avgRR: 2.5 },
];

const ehlersPerformanceData = [
  { name: "Fisher Transform", accuracy: 82.5, signals: 52, profitable: 43 },
  { name: "MAMA/FAMA", accuracy: 78.3, signals: 48, profitable: 38 },
  { name: "Bandpass Filter", accuracy: 75.8, signals: 35, profitable: 27 },
  { name: "Super Smoother", accuracy: 71.2, signals: 42, profitable: 30 },
  { name: "Cyber Cycle", accuracy: 69.5, signals: 38, profitable: 26 },
  { name: "Roofing Filter", accuracy: 73.4, signals: 31, profitable: 23 },
];

const radarData = [
  { subject: "Gann", A: 85, fullMark: 100 },
  { subject: "Ehlers", A: 82, fullMark: 100 },
  { subject: "ML", A: 78, fullMark: 100 },
  { subject: "Astro", A: 72, fullMark: 100 },
  { subject: "Pattern", A: 68, fullMark: 100 },
  { subject: "Options", A: 65, fullMark: 100 },
];

const monthlyBreakdown = [
  { month: "Jan", profit: 3200, loss: 800, net: 2400, trades: 45 },
  { month: "Feb", profit: 4100, loss: 1200, net: 2900, trades: 52 },
  { month: "Mar", profit: 2800, loss: 1500, net: 1300, trades: 38 },
  { month: "Apr", profit: 5200, loss: 900, net: 4300, trades: 61 },
  { month: "May", profit: 3800, loss: 2100, net: 1700, trades: 48 },
  { month: "Jun", profit: 4500, loss: 1100, net: 3400, trades: 55 },
];

const Reports = () => {
  const [selectedInstrument, setSelectedInstrument] = useState<string>("all");
  const [selectedPeriod, setSelectedPeriod] = useState<string>("30d");
  const [isLoading, setIsLoading] = useState(false);

  const currentDate = new Date().toLocaleDateString('en-US', { 
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  const mockReportData = {
    summary: {
      totalTrades: 127, winRate: 68.5, profitFactor: 2.34, netProfit: 15420.50,
      maxDrawdown: 8.2, sharpeRatio: 1.87, avgRR: 2.35, expectancy: 121.42,
      avgWin: 385.50, avgLoss: 164.20, largestWin: 2450.00, largestLoss: 680.00,
    },
    gannAnalysis: {
      squareOf9Accuracy: 78.5, fanAngleHits: 42, timeCycleConfirmations: 35, hexagonPivots: 28,
      gannBoxAccuracy: 76.2, elliottWaveAccuracy: 68.9, astrologyCorrelation: 72.3,
    },
    ehlersIndicators: {
      compositeScore: 88, fisherTransformSignals: 23, mamaFamaConfluences: 31,
      cycleIdentifications: 15, bandpassSignals: 18, roofingSignals: 12,
    },
    forecasting: {
      shortTermAccuracy: 72.3, mediumTermAccuracy: 65.8, longTermAccuracy: 58.4,
      totalForecasts: 89, successfulForecasts: 58,
    },
    risk: {
      valueAtRisk: 2450.00, conditionalVaR: 3200.00, beta: 0.85, alpha: 0.12,
    }
  };

  const filteredInstruments = selectedInstrument === "all" 
    ? tradingInstruments 
    : tradingInstruments.filter(i => i.symbol === selectedInstrument);

  const handleExportPDF = () => {
    setIsLoading(true);
    setTimeout(() => {
      toast.success("Comprehensive report exported to PDF (5 pages)!");
      setIsLoading(false);
    }, 1500);
  };

  const handlePrint = () => { window.print(); };

  const refreshData = () => {
    setIsLoading(true);
    setTimeout(() => { toast.success("Report data refreshed!"); setIsLoading(false); }, 1000);
  };

  const pieData = tradingInstruments.map(i => ({ name: i.symbol, value: Math.abs(i.pnl) }));

  return (
    <div className="space-y-4 md:space-y-6 px-2 md:px-0">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-3xl font-bold text-foreground">Comprehensive Analysis Reports</h1>
          <p className="text-sm text-muted-foreground">In-depth trading analysis across all strategies (5+ pages)</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={refreshData} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="w-4 h-4 mr-2" />Print
          </Button>
          <Button size="sm" onClick={handleExportPDF} disabled={isLoading}>
            <Download className="w-4 h-4 mr-2" />Export PDF
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4 border-border bg-card">
        <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Filters:</span>
          </div>
          <div className="flex flex-wrap gap-3">
            <Select value={selectedInstrument} onValueChange={setSelectedInstrument}>
              <SelectTrigger className="w-[180px]"><SelectValue placeholder="Select Instrument" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Instruments</SelectItem>
                {tradingInstruments.map(i => (<SelectItem key={i.symbol} value={i.symbol}>{i.symbol} - {i.name}</SelectItem>))}
              </SelectContent>
            </Select>
            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="Period" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Last 7 Days</SelectItem>
                <SelectItem value="30d">Last 30 Days</SelectItem>
                <SelectItem value="90d">Last 90 Days</SelectItem>
                <SelectItem value="1y">Last Year</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Report Header */}
      <Card className="p-4 md:p-6 border-border bg-card">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 md:w-12 md:h-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileText className="w-5 h-5 md:w-6 md:h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-base md:text-lg font-semibold text-foreground">Gann Quant AI Comprehensive Report</h2>
              <p className="text-xs md:text-sm text-muted-foreground">Generated: {currentDate}</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-primary/10 text-primary">5 Pages Analysis</Badge>
        </div>
      </Card>

      <Tabs defaultValue="summary" className="w-full">
        <div className="overflow-x-auto">
          <TabsList className="inline-flex w-auto min-w-full md:grid md:w-full md:grid-cols-7 gap-1">
            <TabsTrigger value="summary" className="text-xs md:text-sm">Summary</TabsTrigger>
            <TabsTrigger value="instruments" className="text-xs md:text-sm">Instruments</TabsTrigger>
            <TabsTrigger value="gann" className="text-xs md:text-sm">WD Gann</TabsTrigger>
            <TabsTrigger value="ehlers" className="text-xs md:text-sm">Ehlers DSP</TabsTrigger>
            <TabsTrigger value="forecast" className="text-xs md:text-sm">Forecasting</TabsTrigger>
            <TabsTrigger value="risk" className="text-xs md:text-sm">Risk Analysis</TabsTrigger>
            <TabsTrigger value="strategy" className="text-xs md:text-sm">Strategy</TabsTrigger>
          </TabsList>
        </div>

        {/* PAGE 1: Summary */}
        <TabsContent value="summary" className="space-y-4 mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {[
              { label: "Total Trades", value: mockReportData.summary.totalTrades, color: "text-foreground" },
              { label: "Win Rate", value: `${mockReportData.summary.winRate}%`, color: "text-success" },
              { label: "Profit Factor", value: mockReportData.summary.profitFactor, color: "text-foreground" },
              { label: "Net Profit", value: `$${mockReportData.summary.netProfit.toLocaleString()}`, color: "text-success" },
              { label: "Max Drawdown", value: `${mockReportData.summary.maxDrawdown}%`, color: "text-destructive" },
              { label: "Sharpe Ratio", value: mockReportData.summary.sharpeRatio, color: "text-foreground" },
              { label: "Avg R:R", value: mockReportData.summary.avgRR, color: "text-primary" },
              { label: "Expectancy", value: `$${mockReportData.summary.expectancy}`, color: "text-success" },
              { label: "Avg Win", value: `$${mockReportData.summary.avgWin}`, color: "text-success" },
              { label: "Avg Loss", value: `$${mockReportData.summary.avgLoss}`, color: "text-destructive" },
              { label: "Largest Win", value: `$${mockReportData.summary.largestWin}`, color: "text-success" },
              { label: "Largest Loss", value: `$${mockReportData.summary.largestLoss}`, color: "text-destructive" },
            ].map((stat, idx) => (
              <Card key={idx} className="p-3 border-border bg-card">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className={`text-lg md:text-xl font-bold ${stat.color}`}>{stat.value}</p>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="p-4 md:p-6 border-border bg-card">
              <h3 className="text-lg font-semibold text-foreground mb-4">Weekly Performance Trend</h3>
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={performanceByPeriod}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="period" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="pnl" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="accuracy" orientation="right" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                    <Bar yAxisId="pnl" dataKey="pnl" fill="hsl(var(--success))" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="accuracy" type="monotone" dataKey="gannAccuracy" stroke="hsl(var(--primary))" strokeWidth={2} />
                    <Line yAxisId="accuracy" type="monotone" dataKey="ehlersScore" stroke="hsl(var(--accent))" strokeWidth={2} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card className="p-4 md:p-6 border-border bg-card">
              <h3 className="text-lg font-semibold text-foreground mb-4">Strategy Performance Radar</h3>
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis dataKey="subject" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 8 }} />
                    <Radar name="Accuracy" dataKey="A" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.5} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* PAGE 2: Instruments */}
        <TabsContent value="instruments" className="space-y-4 mt-4">
          <Card className="p-4 md:p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4">Detailed Instrument Performance</h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[800px]">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Symbol</th>
                    <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Category</th>
                    <th className="text-center py-3 px-2 text-sm font-medium text-muted-foreground">Trades</th>
                    <th className="text-center py-3 px-2 text-sm font-medium text-muted-foreground">Win Rate</th>
                    <th className="text-center py-3 px-2 text-sm font-medium text-muted-foreground">Avg Hold</th>
                    <th className="text-center py-3 px-2 text-sm font-medium text-muted-foreground">Max DD</th>
                    <th className="text-right py-3 px-2 text-sm font-medium text-muted-foreground">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInstruments.map((inst) => (
                    <tr key={inst.symbol} className="border-b border-border/50 hover:bg-secondary/30">
                      <td className="py-3 px-2"><span className="font-semibold text-foreground">{inst.symbol}</span></td>
                      <td className="py-3 px-2"><Badge variant="outline">{inst.category}</Badge></td>
                      <td className="py-3 px-2 text-center text-foreground">{inst.trades}</td>
                      <td className="py-3 px-2 text-center">
                        <Badge className={inst.winRate >= 65 ? "bg-success" : inst.winRate >= 50 ? "bg-accent" : "bg-destructive"}>{inst.winRate}%</Badge>
                      </td>
                      <td className="py-3 px-2 text-center text-muted-foreground">{inst.avgHoldTime}</td>
                      <td className="py-3 px-2 text-center text-destructive">{inst.maxDD}%</td>
                      <td className="py-3 px-2 text-right">
                        <span className={`font-semibold flex items-center justify-end gap-1 ${inst.pnl >= 0 ? 'text-success' : 'text-destructive'}`}>
                          {inst.pnl >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                          ${Math.abs(inst.pnl).toLocaleString()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="p-4 md:p-6 border-border bg-card">
              <h3 className="text-lg font-semibold text-foreground mb-4">P&L Distribution</h3>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                      {pieData.map((_, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                  </RechartsPie>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card className="p-4 md:p-6 border-border bg-card">
              <h3 className="text-lg font-semibold text-foreground mb-4">Monthly Breakdown</h3>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                    <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                    <Bar dataKey="profit" fill="hsl(var(--success))" stackId="a" />
                    <Bar dataKey="loss" fill="hsl(var(--destructive))" stackId="b" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* PAGE 3: WD Gann Analysis */}
        <TabsContent value="gann" className="space-y-4 mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Square of 9 Accuracy", value: `${mockReportData.gannAnalysis.squareOf9Accuracy}%` },
              { label: "Gann Box Accuracy", value: `${mockReportData.gannAnalysis.gannBoxAccuracy}%` },
              { label: "Elliott Wave Accuracy", value: `${mockReportData.gannAnalysis.elliottWaveAccuracy}%` },
              { label: "Astro Correlation", value: `${mockReportData.gannAnalysis.astrologyCorrelation}%` },
            ].map((stat, idx) => (
              <Card key={idx} className="p-3 border-border bg-card">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className="text-xl font-bold text-success">{stat.value}</p>
              </Card>
            ))}
          </div>

          <Card className="p-4 md:p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
              <Star className="w-5 h-5 mr-2 text-accent" />
              WD Gann Geometry Performance
            </h3>
            <div className="space-y-3">
              {gannPerformanceData.map((item, idx) => (
                <div key={idx} className="p-4 bg-secondary/30 rounded-lg">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold text-foreground">{item.name}</p>
                      <p className="text-xs text-muted-foreground">{item.profitable}/{item.signals} signals profitable</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">Avg R:R</p>
                        <p className="font-semibold text-primary">{item.avgRR}</p>
                      </div>
                      <Badge className={item.accuracy >= 75 ? "bg-success" : item.accuracy >= 65 ? "bg-accent" : "bg-destructive"}>
                        {item.accuracy}%
                      </Badge>
                    </div>
                  </div>
                  <div className="mt-2 h-2 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-primary to-success" style={{ width: `${item.accuracy}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* PAGE 4: Ehlers DSP */}
        <TabsContent value="ehlers" className="space-y-4 mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Composite Score", value: `${mockReportData.ehlersIndicators.compositeScore}%`, icon: Activity },
              { label: "Fisher Signals", value: mockReportData.ehlersIndicators.fisherTransformSignals, icon: Waves },
              { label: "MAMA/FAMA", value: mockReportData.ehlersIndicators.mamaFamaConfluences, icon: TrendingUp },
              { label: "Bandpass Signals", value: mockReportData.ehlersIndicators.bandpassSignals, icon: BarChart3 },
            ].map((stat, idx) => (
              <Card key={idx} className="p-3 border-border bg-card">
                <div className="flex items-center gap-2 mb-1">
                  <stat.icon className="w-4 h-4 text-accent" />
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                </div>
                <p className="text-xl font-bold text-success">{stat.value}</p>
              </Card>
            ))}
          </div>

          <Card className="p-4 md:p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4">Ehlers DSP Indicator Performance</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ehlersPerformanceData.map((item, idx) => (
                <div key={idx} className="p-4 bg-secondary/30 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <p className="font-semibold text-foreground">{item.name}</p>
                    <Badge className={item.accuracy >= 75 ? "bg-success" : "bg-accent"}>{item.accuracy}%</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">{item.profitable}/{item.signals} profitable signals</p>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-accent" style={{ width: `${item.accuracy}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* PAGE 5: Forecasting */}
        <TabsContent value="forecast" className="space-y-4 mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Short-Term", value: `${mockReportData.forecasting.shortTermAccuracy}%`, desc: "1-7 days" },
              { label: "Medium-Term", value: `${mockReportData.forecasting.mediumTermAccuracy}%`, desc: "1-4 weeks" },
              { label: "Long-Term", value: `${mockReportData.forecasting.longTermAccuracy}%`, desc: "1-12 months" },
              { label: "Success Rate", value: `${((mockReportData.forecasting.successfulForecasts / mockReportData.forecasting.totalForecasts) * 100).toFixed(1)}%`, desc: `${mockReportData.forecasting.successfulForecasts}/${mockReportData.forecasting.totalForecasts}` },
            ].map((stat, idx) => (
              <Card key={idx} className="p-3 border-border bg-card">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className="text-xl font-bold text-foreground">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.desc}</p>
              </Card>
            ))}
          </div>

          <Card className="p-4 md:p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
              <Brain className="w-5 h-5 mr-2 text-primary" />
              AI/ML Forecasting Accuracy Trend
            </h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceByPeriod}>
                  <defs>
                    <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="period" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                  <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} domain={[40, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                  <Area type="monotone" dataKey="gannAccuracy" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorAccuracy)" name="Gann Accuracy" />
                  <Line type="monotone" dataKey="ehlersScore" stroke="hsl(var(--accent))" strokeWidth={2} name="Ehlers Score" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </TabsContent>

        {/* PAGE 6: Risk Analysis */}
        <TabsContent value="risk" className="space-y-4 mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Value at Risk (95%)", value: `$${mockReportData.risk.valueAtRisk.toLocaleString()}`, color: "text-destructive" },
              { label: "Conditional VaR", value: `$${mockReportData.risk.conditionalVaR.toLocaleString()}`, color: "text-destructive" },
              { label: "Beta", value: mockReportData.risk.beta, color: "text-foreground" },
              { label: "Alpha", value: mockReportData.risk.alpha, color: "text-success" },
            ].map((stat, idx) => (
              <Card key={idx} className="p-3 border-border bg-card">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
              </Card>
            ))}
          </div>

          <Card className="p-4 md:p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4">Risk-Adjusted Returns by Instrument</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tradingInstruments} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis type="number" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="symbol" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} width={80} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                  <Bar dataKey="winRate" fill="hsl(var(--success))" name="Win Rate %" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </TabsContent>

        {/* PAGE 7: Strategy Breakdown */}
        <TabsContent value="strategy" className="space-y-4 mt-4">
          <Card className="p-4 md:p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4">Strategy Contribution Analysis</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {radarData.map((strategy, idx) => (
                <div key={idx} className="p-4 bg-secondary/30 rounded-lg">
                  <div className="flex justify-between items-center mb-3">
                    <p className="font-semibold text-foreground">{strategy.subject}</p>
                    <Badge className="bg-primary">{strategy.A}%</Badge>
                  </div>
                  <div className="h-3 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-primary to-success transition-all" style={{ width: `${strategy.A}%` }} />
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Contribution to overall signal accuracy</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-4 md:p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4">Report Summary</h3>
            <div className="prose prose-sm text-muted-foreground">
              <p>This comprehensive report covers 7 pages of in-depth analysis including:</p>
              <ul className="list-disc list-inside space-y-1 mt-2">
                <li><strong>Executive Summary</strong> - Key performance metrics and ratios</li>
                <li><strong>Instrument Analysis</strong> - Detailed breakdown by trading instrument</li>
                <li><strong>WD Gann Analysis</strong> - Geometry, Box, Fan, Elliott Wave, Astrology performance</li>
                <li><strong>Ehlers DSP Analysis</strong> - Digital filter indicator accuracy</li>
                <li><strong>Forecasting Analysis</strong> - AI/ML prediction accuracy trends</li>
                <li><strong>Risk Analysis</strong> - VaR, CVaR, Alpha, Beta calculations</li>
                <li><strong>Strategy Breakdown</strong> - Individual strategy contributions</li>
              </ul>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Reports;
