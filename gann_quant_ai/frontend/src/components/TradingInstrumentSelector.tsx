import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Plus, RefreshCw, Wifi, X, Trash2 } from "lucide-react";
import useWebSocketPrice from "@/hooks/useWebSocketPrice";

const defaultInstruments = [
  { symbol: "BTCUSDT", name: "Bitcoin", category: "Crypto", basePrice: 47500 },
  { symbol: "ETHUSDT", name: "Ethereum", category: "Crypto", basePrice: 2450 },
  { symbol: "EURUSD", name: "Euro/USD", category: "Forex", basePrice: 1.0875 },
  { symbol: "XAUUSD", name: "Gold", category: "Commodities", basePrice: 2045 },
  { symbol: "US500", name: "S&P 500", category: "Indices", basePrice: 4780 },
  { symbol: "GBPUSD", name: "GBP/USD", category: "Forex", basePrice: 1.2650 },
  { symbol: "USDJPY", name: "USD/JPY", category: "Forex", basePrice: 149.85 },
  { symbol: "BNBUSDT", name: "BNB", category: "Crypto", basePrice: 312 },
];

interface TradingInstrumentSelectorProps {
  onInstrumentChange?: (symbol: string, price: number) => void;
  compact?: boolean;
}

const TradingInstrumentSelector = ({ onInstrumentChange, compact = false }: TradingInstrumentSelectorProps) => {
  const [selectedInstrument, setSelectedInstrument] = useState(defaultInstruments[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [customSymbol, setCustomSymbol] = useState("");
  const [customName, setCustomName] = useState("");
  const [customCategory, setCustomCategory] = useState("Custom");
  const [instruments, setInstruments] = useState(defaultInstruments);
  const [showAddForm, setShowAddForm] = useState(false);
  
  const { priceData, isConnected, isLive, toggleConnection } = useWebSocketPrice({
    symbol: selectedInstrument.symbol,
    enabled: true,
    updateInterval: 1500,
  });

  const filteredInstruments = instruments.filter(i => 
    i.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    i.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectInstrument = (symbol: string) => {
    const inst = instruments.find(i => i.symbol === symbol);
    if (inst) {
      setSelectedInstrument(inst);
      onInstrumentChange?.(inst.symbol, priceData.price);
    }
  };

  const handleAddCustom = () => {
    if (!customSymbol.trim()) return;
    const newInst = {
      symbol: customSymbol.toUpperCase(),
      name: customName.trim() || customSymbol.toUpperCase(),
      category: customCategory || "Custom",
      basePrice: 100,
    };
    setInstruments([...instruments, newInst]);
    setCustomSymbol("");
    setCustomName("");
    setCustomCategory("Custom");
    setShowAddForm(false);
  };

  const handleDeleteInstrument = (symbol: string) => {
    if (instruments.length <= 1) return;
    const newInstruments = instruments.filter(i => i.symbol !== symbol);
    setInstruments(newInstruments);
    if (selectedInstrument.symbol === symbol) {
      setSelectedInstrument(newInstruments[0]);
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <Select value={selectedInstrument.symbol} onValueChange={handleSelectInstrument}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select instrument" />
          </SelectTrigger>
          <SelectContent>
            {instruments.map(i => (
              <SelectItem key={i.symbol} value={i.symbol}>
                {i.symbol} - {i.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Badge variant="outline" className={isConnected ? "border-success text-success" : "border-destructive text-destructive"}>
          <Wifi className="w-3 h-3 mr-1" />
          ${priceData.price.toLocaleString()}
        </Badge>
      </div>
    );
  }

  return (
    <Card className="p-4 border-border bg-card">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <h3 className="text-base font-semibold text-foreground">Trading Instruments</h3>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={isConnected ? "border-success text-success" : "border-destructive text-destructive"}>
            <Wifi className="w-3 h-3 mr-1" />
            {isConnected ? "Live" : "Offline"}
          </Badge>
          <Button variant="outline" size="sm" onClick={toggleConnection}>
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
            <h4 className="text-sm font-semibold text-foreground">Add New Instrument</h4>
            <Button variant="ghost" size="sm" onClick={() => setShowAddForm(false)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <Input
              placeholder="Symbol (e.g., AAPL)"
              value={customSymbol}
              onChange={(e) => setCustomSymbol(e.target.value)}
            />
            <Input
              placeholder="Name (e.g., Apple)"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
            />
            <Select value={customCategory} onValueChange={setCustomCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Crypto">Crypto</SelectItem>
                <SelectItem value="Forex">Forex</SelectItem>
                <SelectItem value="Commodities">Commodities</SelectItem>
                <SelectItem value="Indices">Indices</SelectItem>
                <SelectItem value="Stocks">Stocks</SelectItem>
                <SelectItem value="Custom">Custom</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleAddCustom} disabled={!customSymbol.trim()}>
              <Plus className="w-4 h-4 mr-2" />
              Add
            </Button>
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search instruments..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
        {filteredInstruments.map(inst => (
          <div key={inst.symbol} className="relative group">
            <Button
              variant={selectedInstrument.symbol === inst.symbol ? "default" : "outline"}
              size="sm"
              className="w-full justify-start pr-8"
              onClick={() => handleSelectInstrument(inst.symbol)}
            >
              <div className="text-left">
                <p className="text-xs font-semibold">{inst.symbol}</p>
                <p className="text-[10px] text-muted-foreground">{inst.category}</p>
              </div>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-2 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/20 hover:text-destructive"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteInstrument(inst.symbol);
              }}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-secondary/30 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-foreground">{selectedInstrument.symbol}</p>
            <p className="text-xs text-muted-foreground">{selectedInstrument.name}</p>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold text-foreground">${priceData.price.toLocaleString()}</p>
            <p className={`text-xs ${priceData.changePercent >= 0 ? 'text-success' : 'text-destructive'}`}>
              {priceData.changePercent >= 0 ? '+' : ''}{priceData.changePercent.toFixed(2)}%
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default TradingInstrumentSelector;
