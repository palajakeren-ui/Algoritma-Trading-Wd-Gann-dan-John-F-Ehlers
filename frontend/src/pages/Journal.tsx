import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  BookOpen, 
  Plus, 
  TrendingUp, 
  TrendingDown, 
  Calendar,
  DollarSign,
  Target,
  AlertCircle,
  CheckCircle,
  XCircle,
  Edit,
  Trash2,
  Filter,
  Download,
  FileText,
  FileSpreadsheet
} from "lucide-react";
import { toast } from "sonner";

interface JournalEntry {
  id: string;
  date: string;
  symbol: string;
  direction: "long" | "short";
  entryPrice: number;
  exitPrice: number;
  stopLoss: number;
  takeProfit: number;
  lotSize: number;
  pnl: number;
  pnlPercent: number;
  status: "win" | "loss" | "breakeven";
  strategy: string;
  gannSignals: string;
  ehlersConfirmation: string;
  emotionalState: string;
  notes: string;
  lessons: string;
  screenshots?: string[];
}

const mockJournalEntries: JournalEntry[] = [
  {
    id: "1",
    date: "2024-12-12",
    symbol: "BTCUSD",
    direction: "long",
    entryPrice: 47250,
    exitPrice: 48500,
    stopLoss: 46800,
    takeProfit: 49000,
    lotSize: 0.15,
    pnl: 187.50,
    pnlPercent: 2.65,
    status: "win",
    strategy: "Gann Square of 9 + MAMA/FAMA Confluence",
    gannSignals: "Square of 9 support at 47200, Fan angle 1x1 confirmed",
    ehlersConfirmation: "Fisher Transform bullish, MAMA above FAMA",
    emotionalState: "Confident, followed plan",
    notes: "Entry triggered at Gann support level with Ehlers confirmation",
    lessons: "Wait for multiple confirmations before entry"
  },
  {
    id: "2",
    date: "2024-12-11",
    symbol: "ETHUSD",
    direction: "short",
    entryPrice: 2680,
    exitPrice: 2720,
    stopLoss: 2750,
    takeProfit: 2550,
    lotSize: 0.5,
    pnl: -20.00,
    pnlPercent: -1.49,
    status: "loss",
    strategy: "Hexagon Resistance + Cycle Peak",
    gannSignals: "Hexagon 180° resistance, time cycle peak",
    ehlersConfirmation: "Dominant cycle showing bearish divergence",
    emotionalState: "Rushed entry, FOMO",
    notes: "Entered too early before confirmation",
    lessons: "Don't rush entries, wait for price action confirmation"
  },
  {
    id: "3",
    date: "2024-12-10",
    symbol: "XAUUSD",
    direction: "long",
    entryPrice: 2045.50,
    exitPrice: 2078.25,
    stopLoss: 2030.00,
    takeProfit: 2085.00,
    lotSize: 0.08,
    pnl: 262.00,
    pnlPercent: 1.60,
    status: "win",
    strategy: "Gann Box 90° + Fibonacci Confluence",
    gannSignals: "Gann Box 90° support, 61.8% Fib retracement",
    ehlersConfirmation: "Super Smoother trend up, Cyber Cycle bullish",
    emotionalState: "Patient, disciplined",
    notes: "Perfect setup with multiple confirmations",
    lessons: "Patience pays off, stick to the system"
  }
];

const Journal = () => {
  const [entries, setEntries] = useState<JournalEntry[]>(mockJournalEntries);
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [newEntry, setNewEntry] = useState<Partial<JournalEntry>>({
    direction: "long",
    status: "win"
  });

  const filteredEntries = entries.filter(entry => 
    filterStatus === "all" ? true : entry.status === filterStatus
  );

  const stats = {
    totalTrades: entries.length,
    wins: entries.filter(e => e.status === "win").length,
    losses: entries.filter(e => e.status === "loss").length,
    winRate: ((entries.filter(e => e.status === "win").length / entries.length) * 100).toFixed(1),
    totalPnl: entries.reduce((sum, e) => sum + e.pnl, 0),
  };

  const handleAddEntry = () => {
    if (newEntry.symbol && newEntry.entryPrice) {
      const entry: JournalEntry = {
        id: Date.now().toString(),
        date: new Date().toISOString().split('T')[0],
        symbol: newEntry.symbol || "",
        direction: newEntry.direction as "long" | "short",
        entryPrice: newEntry.entryPrice || 0,
        exitPrice: newEntry.exitPrice || 0,
        stopLoss: newEntry.stopLoss || 0,
        takeProfit: newEntry.takeProfit || 0,
        lotSize: newEntry.lotSize || 0,
        pnl: newEntry.pnl || 0,
        pnlPercent: newEntry.pnlPercent || 0,
        status: newEntry.status as "win" | "loss" | "breakeven",
        strategy: newEntry.strategy || "",
        gannSignals: newEntry.gannSignals || "",
        ehlersConfirmation: newEntry.ehlersConfirmation || "",
        emotionalState: newEntry.emotionalState || "",
        notes: newEntry.notes || "",
        lessons: newEntry.lessons || ""
      };
      setEntries([entry, ...entries]);
      setNewEntry({ direction: "long", status: "win" });
      setShowNewEntry(false);
      toast.success("Journal entry added successfully!");
    }
  };

  const exportToCSV = () => {
    const headers = ["Date", "Symbol", "Direction", "Entry Price", "Exit Price", "Stop Loss", "Take Profit", "Lot Size", "P&L", "P&L %", "Status", "Strategy", "Gann Signals", "Ehlers Confirmation", "Emotional State", "Notes", "Lessons"];
    const csvContent = [
      headers.join(","),
      ...filteredEntries.map(entry => [
        entry.date,
        entry.symbol,
        entry.direction,
        entry.entryPrice,
        entry.exitPrice,
        entry.stopLoss,
        entry.takeProfit,
        entry.lotSize,
        entry.pnl,
        entry.pnlPercent,
        entry.status,
        `"${entry.strategy}"`,
        `"${entry.gannSignals}"`,
        `"${entry.ehlersConfirmation}"`,
        `"${entry.emotionalState}"`,
        `"${entry.notes}"`,
        `"${entry.lessons}"`
      ].join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trading-journal-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Journal exported to CSV!");
  };

  const exportToJSON = () => {
    const jsonContent = JSON.stringify(filteredEntries, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trading-journal-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Journal exported to JSON!");
  };

  const exportToPDF = () => {
    toast.success("Generating PDF report...");
    setTimeout(() => {
      window.print();
    }, 500);
  };

  const deleteEntry = (id: string) => {
    setEntries(entries.filter(e => e.id !== id));
    toast.success("Entry deleted successfully!");
  };

  return (
    <div className="space-y-4 md:space-y-6 px-2 md:px-0">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-3xl font-bold text-foreground flex items-center gap-2">
            <BookOpen className="w-6 h-6 md:w-8 md:h-8 text-primary" />
            Trading Journal
          </h1>
          <p className="text-sm text-muted-foreground">Track, analyze, and improve your trading performance</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={exportToCSV}>
            <FileSpreadsheet className="w-4 h-4 mr-2" />
            CSV
          </Button>
          <Button variant="outline" size="sm" onClick={exportToJSON}>
            <FileText className="w-4 h-4 mr-2" />
            JSON
          </Button>
          <Button variant="outline" size="sm" onClick={exportToPDF}>
            <Download className="w-4 h-4 mr-2" />
            PDF
          </Button>
          <Button size="sm" onClick={() => setShowNewEntry(!showNewEntry)}>
            <Plus className="w-4 h-4 mr-2" />
            New Entry
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
        <Card className="p-3 md:p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Total Trades</p>
          <p className="text-xl md:text-2xl font-bold text-foreground">{stats.totalTrades}</p>
        </Card>
        <Card className="p-3 md:p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Wins</p>
          <p className="text-xl md:text-2xl font-bold text-success">{stats.wins}</p>
        </Card>
        <Card className="p-3 md:p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Losses</p>
          <p className="text-xl md:text-2xl font-bold text-destructive">{stats.losses}</p>
        </Card>
        <Card className="p-3 md:p-4 border-border bg-card">
          <p className="text-xs text-muted-foreground mb-1">Win Rate</p>
          <p className="text-xl md:text-2xl font-bold text-foreground">{stats.winRate}%</p>
        </Card>
        <Card className="p-3 md:p-4 border-border bg-card col-span-2 md:col-span-1">
          <p className="text-xs text-muted-foreground mb-1">Total P&L</p>
          <p className={`text-xl md:text-2xl font-bold ${stats.totalPnl >= 0 ? 'text-success' : 'text-destructive'}`}>
            ${stats.totalPnl.toFixed(2)}
          </p>
        </Card>
      </div>

      {/* New Entry Form */}
      {showNewEntry && (
        <Card className="p-4 md:p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-4">New Journal Entry</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-4">
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Symbol</label>
              <Input 
                placeholder="BTCUSD" 
                value={newEntry.symbol || ""}
                onChange={(e) => setNewEntry({ ...newEntry, symbol: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Direction</label>
              <Select 
                value={newEntry.direction} 
                onValueChange={(value) => setNewEntry({ ...newEntry, direction: value as "long" | "short" })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="long">Long</SelectItem>
                  <SelectItem value="short">Short</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Entry Price</label>
              <Input 
                type="number" 
                placeholder="0.00"
                value={newEntry.entryPrice || ""}
                onChange={(e) => setNewEntry({ ...newEntry, entryPrice: parseFloat(e.target.value) })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Exit Price</label>
              <Input 
                type="number" 
                placeholder="0.00"
                value={newEntry.exitPrice || ""}
                onChange={(e) => setNewEntry({ ...newEntry, exitPrice: parseFloat(e.target.value) })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Stop Loss</label>
              <Input 
                type="number" 
                placeholder="0.00"
                value={newEntry.stopLoss || ""}
                onChange={(e) => setNewEntry({ ...newEntry, stopLoss: parseFloat(e.target.value) })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Take Profit</label>
              <Input 
                type="number" 
                placeholder="0.00"
                value={newEntry.takeProfit || ""}
                onChange={(e) => setNewEntry({ ...newEntry, takeProfit: parseFloat(e.target.value) })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Lot Size</label>
              <Input 
                type="number" 
                step="0.01"
                placeholder="0.00"
                value={newEntry.lotSize || ""}
                onChange={(e) => setNewEntry({ ...newEntry, lotSize: parseFloat(e.target.value) })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Status</label>
              <Select 
                value={newEntry.status} 
                onValueChange={(value) => setNewEntry({ ...newEntry, status: value as "win" | "loss" | "breakeven" })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="win">Win</SelectItem>
                  <SelectItem value="loss">Loss</SelectItem>
                  <SelectItem value="breakeven">Breakeven</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 mb-4">
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Strategy Used</label>
              <Input 
                placeholder="e.g., Gann Square of 9 + MAMA/FAMA"
                value={newEntry.strategy || ""}
                onChange={(e) => setNewEntry({ ...newEntry, strategy: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Emotional State</label>
              <Input 
                placeholder="e.g., Confident, Patient"
                value={newEntry.emotionalState || ""}
                onChange={(e) => setNewEntry({ ...newEntry, emotionalState: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 mb-4">
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Gann Signals</label>
              <Textarea 
                placeholder="Describe Gann signals..."
                value={newEntry.gannSignals || ""}
                onChange={(e) => setNewEntry({ ...newEntry, gannSignals: e.target.value })}
                className="min-h-[80px]"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Ehlers Confirmation</label>
              <Textarea 
                placeholder="Describe Ehlers DSP confirmations..."
                value={newEntry.ehlersConfirmation || ""}
                onChange={(e) => setNewEntry({ ...newEntry, ehlersConfirmation: e.target.value })}
                className="min-h-[80px]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 mb-4">
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Trade Notes</label>
              <Textarea 
                placeholder="Additional notes..."
                value={newEntry.notes || ""}
                onChange={(e) => setNewEntry({ ...newEntry, notes: e.target.value })}
                className="min-h-[80px]"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Lessons Learned</label>
              <Textarea 
                placeholder="What did you learn?"
                value={newEntry.lessons || ""}
                onChange={(e) => setNewEntry({ ...newEntry, lessons: e.target.value })}
                className="min-h-[80px]"
              />
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={handleAddEntry}>Save Entry</Button>
            <Button variant="outline" onClick={() => setShowNewEntry(false)}>Cancel</Button>
          </div>
        </Card>
      )}

      {/* Filter */}
      <div className="flex items-center gap-4">
        <Filter className="w-4 h-4 text-muted-foreground" />
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Trades</SelectItem>
            <SelectItem value="win">Wins Only</SelectItem>
            <SelectItem value="loss">Losses Only</SelectItem>
            <SelectItem value="breakeven">Breakeven</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-sm text-muted-foreground">
          Showing {filteredEntries.length} of {entries.length} entries
        </span>
      </div>

      {/* Journal Entries */}
      <div className="space-y-4">
        {filteredEntries.map((entry) => (
          <Card key={entry.id} className="p-4 md:p-6 border-border bg-card">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-4">
              <div className="flex items-center gap-3 md:gap-4">
                <div className={`w-10 h-10 md:w-12 md:h-12 rounded-lg flex items-center justify-center ${
                  entry.status === "win" ? "bg-success/10" : 
                  entry.status === "loss" ? "bg-destructive/10" : "bg-muted"
                }`}>
                  {entry.status === "win" ? (
                    <CheckCircle className="w-5 h-5 md:w-6 md:h-6 text-success" />
                  ) : entry.status === "loss" ? (
                    <XCircle className="w-5 h-5 md:w-6 md:h-6 text-destructive" />
                  ) : (
                    <AlertCircle className="w-5 h-5 md:w-6 md:h-6 text-muted-foreground" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-base md:text-lg font-semibold text-foreground">{entry.symbol}</h3>
                    <Badge variant="outline" className={
                      entry.direction === "long" ? "text-success border-success" : "text-destructive border-destructive"
                    }>
                      {entry.direction === "long" ? (
                        <><TrendingUp className="w-3 h-3 mr-1" /> Long</>
                      ) : (
                        <><TrendingDown className="w-3 h-3 mr-1" /> Short</>
                      )}
                    </Badge>
                  </div>
                  <p className="text-xs md:text-sm text-muted-foreground flex items-center gap-1">
                    <Calendar className="w-3 h-3" /> {entry.date}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-4 md:gap-6">
                <div className="text-right">
                  <p className="text-xs md:text-sm text-muted-foreground">P&L</p>
                  <p className={`text-lg md:text-xl font-bold ${entry.pnl >= 0 ? 'text-success' : 'text-destructive'}`}>
                    ${entry.pnl.toFixed(2)} ({entry.pnlPercent > 0 ? '+' : ''}{entry.pnlPercent}%)
                  </p>
                </div>
                <div className="flex gap-1 md:gap-2">
                  <Button variant="ghost" size="icon" className="w-8 h-8 md:w-10 md:h-10">
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="w-8 h-8 md:w-10 md:h-10 text-destructive"
                    onClick={() => deleteEntry(entry.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-4 p-3 md:p-4 bg-secondary/50 rounded-lg">
              <div>
                <p className="text-xs text-muted-foreground">Entry</p>
                <p className="font-mono text-sm md:text-base text-foreground">${entry.entryPrice.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Exit</p>
                <p className="font-mono text-sm md:text-base text-foreground">${entry.exitPrice.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Stop Loss</p>
                <p className="font-mono text-sm md:text-base text-destructive">${entry.stopLoss.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Take Profit</p>
                <p className="font-mono text-sm md:text-base text-success">${entry.takeProfit.toFixed(2)}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Strategy</p>
                <p className="text-foreground">{entry.strategy}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Emotional State</p>
                <p className="text-foreground">{entry.emotionalState}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Gann Signals</p>
                <p className="text-foreground">{entry.gannSignals}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Ehlers Confirmation</p>
                <p className="text-foreground">{entry.ehlersConfirmation}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Notes</p>
                <p className="text-foreground">{entry.notes}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Lessons</p>
                <p className="text-foreground">{entry.lessons}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Journal;
