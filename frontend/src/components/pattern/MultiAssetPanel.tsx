import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Layers, 
  Plus, 
  RefreshCw, 
  Trash2, 
  Clock,
  TrendingUp,
  ChevronRight
} from "lucide-react";
import { AssetAnalysis, TIMEFRAMES } from "@/lib/patternUtils";

interface MultiAssetPanelProps {
  assets: AssetAnalysis[];
  onAddAsset: (asset: AssetAnalysis) => void;
  onUpdateAsset: (id: string) => void;
  onDeleteAsset: (id: string) => void;
}

export const MultiAssetPanel = ({
  assets,
  onAddAsset,
  onUpdateAsset,
  onDeleteAsset,
}: MultiAssetPanelProps) => {
  const [newSymbol, setNewSymbol] = useState("");
  const [newTimeframes, setNewTimeframes] = useState<string[]>(["H1"]);
  const [isFormOpen, setIsFormOpen] = useState(false);

  const handleAddAsset = () => {
    if (!newSymbol) return;

    const asset: AssetAnalysis = {
      id: Date.now().toString(),
      symbol: newSymbol.toUpperCase(),
      name: newSymbol.toUpperCase(),
      timeframes: newTimeframes,
      lastUpdated: new Date(),
      patternCount: 0,
    };

    onAddAsset(asset);
    setNewSymbol("");
    setNewTimeframes(["H1"]);
    setIsFormOpen(false);
  };

  const toggleTimeframe = (tf: string) => {
    if (newTimeframes.includes(tf)) {
      setNewTimeframes(newTimeframes.filter((t) => t !== tf));
    } else {
      setNewTimeframes([...newTimeframes, tf]);
    }
  };

  const allTimeframes = [
    "M1", "M2", "M3", "M5", "M10", "M15", "M30", "M45",
    "H1", "H2", "H3", "H4", "D1", "W1", "MN1", "Y1"
  ];

  return (
    <Card className="overflow-hidden border-border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-primary to-primary/60 p-3">
            <Layers className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground">Multi-Asset Analysis</h3>
            <p className="text-sm text-muted-foreground">
              Track patterns across {assets.length} assets
            </p>
          </div>
        </div>
        <Button
          onClick={() => setIsFormOpen(!isFormOpen)}
          variant={isFormOpen ? "secondary" : "default"}
        >
          <Plus className="mr-2 h-4 w-4" />
          {isFormOpen ? "Cancel" : "Add Asset"}
        </Button>
      </div>

      {/* Add Asset Form */}
      {isFormOpen && (
        <div className="border-b border-border bg-muted/30 p-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Asset Symbol</Label>
              <Input
                placeholder="e.g. ETHUSDT, XAUUSD, EURUSD"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Select Timeframes</Label>
              <ScrollArea className="h-[80px]">
                <div className="flex flex-wrap gap-1">
                  {allTimeframes.map((tf) => (
                    <Button
                      key={tf}
                      variant={newTimeframes.includes(tf) ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleTimeframe(tf)}
                      className="text-xs font-mono h-7 px-2"
                    >
                      {tf}
                    </Button>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={handleAddAsset} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Asset
            </Button>
          </div>
        </div>
      )}

      {/* Assets Grid */}
      {assets.length > 0 ? (
        <ScrollArea className="h-[400px]">
          <div className="grid gap-3 p-4 md:grid-cols-2 lg:grid-cols-3">
            {assets.map((asset) => (
              <Card
                key={asset.id}
                className="group relative overflow-hidden border-border bg-gradient-to-br from-card to-muted/30 p-4 transition-all hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 font-bold text-primary">
                      {asset.symbol.slice(0, 2)}
                    </div>
                    <div>
                      <h4 className="font-bold text-foreground">{asset.symbol}</h4>
                      <p className="text-xs text-muted-foreground">{asset.name}</p>
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => onUpdateAsset(asset.id)}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:bg-destructive/10"
                      onClick={() => onDeleteAsset(asset.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-1">
                  {asset.timeframes.map((tf) => (
                    <Badge key={tf} variant="secondary" className="text-xs font-mono">
                      {tf}
                    </Badge>
                  ))}
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
                  <div className="flex items-center gap-2 text-sm">
                    <TrendingUp className="h-4 w-4 text-success" />
                    <span className="font-semibold text-foreground">{asset.patternCount}</span>
                    <span className="text-muted-foreground">patterns</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {asset.lastUpdated.toLocaleTimeString()}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </ScrollArea>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4">
            <Layers className="h-8 w-8 text-muted-foreground" />
          </div>
          <h4 className="mt-4 text-lg font-semibold text-foreground">No Assets Tracked</h4>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Click "Add Asset" to start tracking patterns across multiple instruments.
          </p>
        </div>
      )}
    </Card>
  );
};
