import { useState, useRef, useCallback, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Settings as SettingsIcon, Save, Download, Upload, Search, Plus, Trash2,
  TrendingUp, DollarSign, Settings2, Shield, Zap, Activity, AlertTriangle,
  CheckCircle2, Play, Pause, Layers, Server, Wifi, WifiOff, Key, Eye, EyeOff,
  RefreshCw, Clock, Sparkles, Target, Telescope, Waves, Grid, Brain, Cpu,
  Globe, ShieldCheck
} from "lucide-react";
import { toast } from "sonner";
import { tradingInstruments as instrumentsData, InstrumentCategory, Instrument } from "@/data/tradingInstruments";
import AlertAPISettings from "@/components/settings/AlertAPISettings";
import apiService from "@/services/apiService";

// --- Timeframes & Strategies (From Settings) ---
const timeframes = [
  { label: "1M", value: "M1", name: "1 Minute" },
  { label: "2M", value: "M2", name: "2 Minutes" },
  { label: "3M", value: "M3", name: "3 Minutes" },
  { label: "5M", value: "M5", name: "5 Minutes" },
  { label: "10M", value: "M10", name: "10 Minutes" },
  { label: "15M", value: "M15", name: "15 Minutes" },
  { label: "30M", value: "M30", name: "30 Minutes" },
  { label: "45M", value: "M45", name: "45 Minutes" },
  { label: "1H", value: "H1", name: "1 Hour" },
  { label: "2H", value: "H2", name: "2 Hours" },
  { label: "3H", value: "H3", name: "3 Hours" },
  { label: "4H", value: "H4", name: "4 Hours" },
  { label: "1D", value: "D1", name: "1 Day" },
  { label: "1W", value: "W1", name: "1 Week" },
  { label: "1MO", value: "MN", name: "1 Month" },
  { label: "3MO", value: "QMN", name: "3 Months" },
  { label: "6MO", value: "SMN", name: "6 Months" },
  { label: "1Y", value: "Y1", name: "1 Year" },
];

const defaultStrategies = [
  { name: "WD Gann Modul", weight: 0.25 },
  { name: "Astro Cycles", weight: 0.15 },
  { name: "Ehlers DSP", weight: 0.20 },
  { name: "ML Models", weight: 0.25 },
  { name: "Pattern Recognition", weight: 0.10 },
  { name: "Options Flow", weight: 0.05 },
];

type TimeframeWeights = {
  [key: string]: { name: string; weight: number }[];
};

const createInitialWeights = (): TimeframeWeights => {
  return timeframes.reduce((acc, tf) => {
    acc[tf.value] = defaultStrategies.map(s => ({ ...s }));
    return acc;
  }, {} as TimeframeWeights);
};

// --- TradingMode Types & Helpers ---

const parseNumericInput = (value: string): number | null => {
  if (value === "" || value === "-") return null;
  const normalized = value.replace(",", ".");
  const parsed = parseFloat(normalized);
  return isNaN(parsed) ? null : parsed;
};

const formatNumericValue = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "";
  return String(value);
};

type RiskManagementType = "dynamic" | "fixed";

interface TradingModeConfig {
  id: string;
  name: string;
  mode: "spot" | "futures";
  enabled: boolean;
  leverage: number;
  marginMode: "cross" | "isolated";
  openLotSize: number;
  autoLotSize: boolean;
  trailingStop: boolean;
  trailingStopDistance: number;
  autoDeleverage: boolean;
  hedgingEnabled: boolean;
  selectedInstrument: string;
  riskType: RiskManagementType;
  riskPerTrade: number;
  kellyFraction: number;
  adaptiveSizing: boolean;
  volatilityAdjustment: boolean;
  drawdownProtection: boolean;
  maxDrawdown: number;
  dailyLossLimit: number;
  weeklyLossLimit: number;
  breakEvenOnProfit: boolean;
  liquidationAlert: number;
  fixedRiskPerTrade: number;
  fixedMaxDrawdown: number;
  riskRewardRatio: number;
  fixedLotSize: number;
  maxOpenPositions: number;
  brokerType: "crypto_exchange" | "metatrader" | "fix" | "dex" | "none";
  exchange: string;
  endpoint: string;
  apiKey: string;
  apiSecret: string;
  passphrase: string;
  testnet: boolean;
  brokerConnected: boolean;
  mtType: "mt4" | "mt5" | "";
  mtServer: string;
  mtLogin: string;
  mtPassword: string;
  mtAccountType: "demo" | "live";
  mtBroker: string;
  fixSenderCompId: string;
  fixTargetCompId: string;
  fixHost: string;
  fixPort: number;
  fixUsername: string;
  fixPassword: string;
  fixHeartbeatInterval: number;
  fixResetOnLogon: boolean;
  fixSslEnabled: boolean;
  dexChain: string;
  dexExchange: string;
  dexWalletAddress: string;
  dexPrivateKey: string;
  dexSlippage: number;
  dexPriorityFee: number;
  dexAutoSlippage: boolean;
  dexAutoPriorityFee: boolean;
  timeEntryEnabled: boolean;
  entryStartTime: string;
  entryEndTime: string;
  useMultiTf: boolean;
  confirmationTimeframes: string[];
}

const EXCHANGE_OPTIONS = [
  { value: "binance", label: "Binance", icon: "🔶", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.binance.com" },
  { value: "bybit", label: "Bybit", icon: "⚫", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.bybit.com" },
  { value: "okx", label: "OKX", icon: "⚪", type: "both", hasPassphrase: true, defaultEndpoint: "https://www.okx.com" },
  { value: "kucoin", label: "KuCoin", icon: "🟢", type: "both", hasPassphrase: true, defaultEndpoint: "https://api.kucoin.com" },
  { value: "gateio", label: "Gate.io", icon: "GATE", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.gateio.ws" },
  { value: "bitget", label: "Bitget", icon: "🔵", type: "both", hasPassphrase: true, defaultEndpoint: "https://api.bitget.com" },
  { value: "mexc", label: "MEXC", icon: "Ⓜ️", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.mexc.com" },
  { value: "kraken", label: "Kraken", icon: "🐙", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.kraken.com" },
  { value: "coinbase", label: "Coinbase", icon: "🔵", type: "spot", hasPassphrase: false, defaultEndpoint: "https://api.coinbase.com" },
  { value: "htx", label: "HTX", icon: "HTX", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.huobi.pro" },
  { value: "crypto_com", label: "Crypto.com", icon: "🦁", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.crypto.com" },
  { value: "bingx", label: "BingX", icon: "🟦", type: "both", hasPassphrase: false, defaultEndpoint: "https://open-api.bingx.com" },
  { value: "deribit", label: "Deribit", icon: "DRBT", type: "futures", hasPassphrase: false, defaultEndpoint: "https://www.deribit.com" },
  { value: "phemex", label: "Phemex", icon: "🦅", type: "both", hasPassphrase: false, defaultEndpoint: "https://api.phemex.com" },
];

const DEX_CHAINS = [
  { value: "solana", label: "Solana", icon: "◎" },
  { value: "ethereum", label: "Ethereum", icon: "Ξ" },
  { value: "base", label: "Base", icon: "🔵" },
  { value: "bsc", label: "BSC", icon: "🔶" },
  { value: "arbitrum", label: "Arbitrum", icon: "🟦" },
  { value: "polygon", label: "Polygon", icon: "🟣" },
  { value: "hyperliquid", label: "Hyperliquid", icon: "HL" },
];

const DEX_EXCHANGES: Record<string, { value: string, label: string, icon: string }[]> = {
  solana: [
    { value: "jupiter", label: "Jupiter", icon: "🪐" },
    { value: "raydium", label: "Raydium", icon: "☀️" },
    { value: "orca", label: "Orca", icon: "🐳" },
  ],
  ethereum: [
    { value: "uniswap_v3", label: "Uniswap V3", icon: "🦄" },
    { value: "sushiswap", label: "SushiSwap", icon: "🍣" },
    { value: "curve", label: "Curve", icon: "🧮" },
  ],
  base: [
    { value: "aerodrome", label: "Aerodrome", icon: "✈️" },
    { value: "base_swap", label: "BaseSwap", icon: "🔵" },
    { value: "uniswap_v3", label: "Uniswap V3", icon: "🦄" },
  ],
  bsc: [
    { value: "pancakeswap", label: "PancakeSwap", icon: "🥞" },
    { value: "biswap", label: "BiSwap", icon: "🅱️" },
  ],
  arbitrum: [
    { value: "uniswap_v3", label: "Uniswap V3", icon: "🦄" },
    { value: "camelot", label: "Camelot", icon: "🏰" },
  ]
};

const DEX_PERP_EXCHANGES: Record<string, { value: string, label: string, icon: string }[]> = {
  solana: [
    { value: "drift", label: "Drift Protocol", icon: "🌀" },
    { value: "jupiter_perps", label: "Jupiter Perps", icon: "🪐" },
    { value: "zeta", label: "Zeta Markets", icon: "Ζ" },
  ],
  arbitrum: [
    { value: "gmx_v2", label: "GMX V2", icon: "🫐" },
    { value: "vertex", label: "Vertex", icon: "📐" },
    { value: "gm_perp", label: "Gains Network", icon: "🍏" },
  ],
  hyperliquid: [
    { value: "hyperliquid", label: "Hyperliquid L1", icon: "HL" },
  ],
  base: [
    { value: "dydx", label: "dYdX Chain", icon: "🟣" },
    { value: "intentx", label: "IntentX", icon: "IX" },
    { value: "synthetix", label: "Synthetix V3", icon: "⚔️" },
  ],
};

interface ManualLeverageConfig {
  instrument: string;
  leverage: number;
  marginMode: "cross" | "isolated";
}

const NumericInput = ({
  value, onChange, step = "1", className = "", placeholder = "", disabled = false
}: {
  value: number; onChange: (value: number) => void; step?: string; className?: string; placeholder?: string; disabled?: boolean;
}) => {
  const [localValue, setLocalValue] = useState<string>(formatNumericValue(value));
  useEffect(() => { setLocalValue(formatNumericValue(value)); }, [value]);
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val === "" || /^-?[\d.,]*$/.test(val)) setLocalValue(val);
  };
  const handleBlur = () => {
    const parsed = parseNumericInput(localValue);
    if (parsed !== null) { onChange(parsed); setLocalValue(formatNumericValue(parsed)); }
    else if (localValue === "" || localValue === "-") { onChange(0); setLocalValue("0"); }
  };
  return <Input type="text" inputMode="decimal" value={localValue} onChange={handleChange} onBlur={handleBlur} className={className} placeholder={placeholder} disabled={disabled} />;
};

const RiskSettingsPanel = ({ mode, onUpdate }: { mode: TradingModeConfig; onUpdate: (u: Partial<TradingModeConfig>) => void }) => {
  const isFutures = mode.mode === "futures";

  return (
    <div className="mt-6 space-y-6 animate-in slide-in-from-bottom-2 duration-500">

      {/* 1. Allocation Strategy Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Label className="text-sm font-black flex items-center gap-2">
            <Shield className={`w-4 h-4 ${isFutures ? 'text-accent' : 'text-primary'}`} />
            RISK ALLOCATION MODEL
          </Label>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">
            Current Logic: <span className={mode.riskType === 'dynamic' ? 'text-primary' : 'text-foreground'}>{mode.riskType} Sizing</span>
          </p>
        </div>
        <div className="bg-secondary/30 p-1 rounded-xl flex gap-1 border border-border/50">
          <Button
            variant={mode.riskType === "dynamic" ? "default" : "ghost"}
            size="sm"
            onClick={() => onUpdate({ riskType: "dynamic" })}
            className={`h-8 px-4 text-xs font-bold rounded-lg transition-all ${mode.riskType === 'dynamic' ? (isFutures ? 'bg-accent hover:bg-accent/90' : '') : 'hover:bg-background/50'}`}
          >
            DYNAMIC %
          </Button>
          <Button
            variant={mode.riskType === "fixed" ? "default" : "ghost"}
            size="sm"
            onClick={() => onUpdate({ riskType: "fixed" })}
            className={`h-8 px-4 text-xs font-bold rounded-lg transition-all ${mode.riskType === 'fixed' ? (isFutures ? 'bg-accent hover:bg-accent/90' : '') : 'hover:bg-background/50'}`}
          >
            FIXED AMT
          </Button>
        </div>
      </div>

      {/* 2. Position Sizing Card */}
      <div className="rounded-xl border border-border/40 bg-gradient-to-b from-card to-secondary/5 shadow-sm overflow-hidden">
        <div className="bg-secondary/10 px-4 py-3 border-b border-border/30 flex items-center justify-between">
          <h5 className="text-xs font-bold uppercase tracking-widest flex items-center gap-2 text-foreground/80">
            <Activity className="w-3.5 h-3.5" />
            {mode.riskType === 'dynamic' ? 'Dynamic Sizing Engine' : 'Fixed Allocation Logic'}
          </h5>
          {mode.riskType === 'dynamic' && (
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-success shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse" />
              <span className="text-[9px] font-bold text-success uppercase tracking-wider">Kelly Active</span>
            </div>
          )}
        </div>

        <div className="p-5">
          {mode.riskType === "dynamic" ? (
            <div className="grid grid-cols-2 gap-x-6 gap-y-5">
              <div className="space-y-2">
                <Label className="text-[10px] font-bold text-muted-foreground uppercase">Risk Exposure</Label>
                <div className="relative group">
                  <NumericInput
                    value={mode.riskPerTrade}
                    onChange={(v) => onUpdate({ riskPerTrade: v })}
                    className="h-10 text-right font-mono text-sm bg-background/50 border-input/60 focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all pl-4 pr-8 rounded-lg"
                    placeholder="1.0"
                  />
                  <span className="absolute right-3 top-3 text-xs font-bold text-muted-foreground">%</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-[10px] font-bold text-muted-foreground uppercase">Kelly Multiplier</Label>
                <div className="relative group">
                  <NumericInput
                    value={mode.kellyFraction}
                    step="0.1"
                    onChange={(v) => onUpdate({ kellyFraction: v })}
                    className="h-10 text-right font-mono text-sm bg-background/50 border-input/60 focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all pl-4 pr-8 rounded-lg"
                    placeholder="0.5"
                  />
                  <span className="absolute right-3 top-3 text-xs font-bold text-muted-foreground">x</span>
                </div>
              </div>

              <div className="col-span-2 mt-1 pt-4 border-t border-border/30 flex items-center justify-between">
                <div>
                  <Label className="text-xs font-bold text-foreground/90">Volatility Scaling</Label>
                  <p className="text-[10px] text-muted-foreground">Automatically reduce size during high ATR regimes.</p>
                </div>
                <Switch
                  checked={mode.adaptiveSizing}
                  onCheckedChange={(v) => onUpdate({ adaptiveSizing: v })}
                  className={isFutures ? "data-[state=checked]:bg-accent" : "data-[state=checked]:bg-primary"}
                />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-[10px] font-bold text-muted-foreground uppercase">Lot Size</Label>
                  <div className="flex items-center gap-1">
                    <Switch
                      checked={mode.autoLotSize}
                      onCheckedChange={(v) => onUpdate({ autoLotSize: v })}
                      className="scale-50 origin-right"
                    />
                    <span className="text-[8px] font-bold uppercase text-accent">Auto</span>
                  </div>
                </div>
                <div className="relative group">
                  <NumericInput
                    value={mode.fixedLotSize}
                    step="0.01"
                    onChange={(v) => onUpdate({ fixedLotSize: v })}
                    className={`h-10 text-right font-mono text-sm border-input/60 focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all pl-4 pr-10 rounded-lg ${mode.autoLotSize ? 'bg-secondary/20 opacity-50 cursor-not-allowed' : 'bg-background/50'}`}
                    placeholder={mode.autoLotSize ? "AUTO" : "0.01"}
                  />
                  <span className="absolute right-3 top-3 text-xs font-bold text-muted-foreground">LOT</span>
                  {mode.autoLotSize && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <Badge variant="outline" className="h-5 text-[8px] bg-accent/10 border-accent/20 text-accent">AI CALIBRATED</Badge>
                    </div>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-[10px] font-bold text-muted-foreground uppercase">Risk : Reward</Label>
                <div className="relative group">
                  <NumericInput
                    value={mode.riskRewardRatio}
                    step="0.1"
                    onChange={(v) => onUpdate({ riskRewardRatio: v })}
                    className="h-10 text-right font-mono text-sm bg-background/50 border-input/60 focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all pl-4 pr-8 rounded-lg"
                  />
                  <span className="absolute right-3 top-3 text-xs font-bold text-muted-foreground">RR</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Safety Limits Card */}
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 shadow-sm overflow-hidden">
        <div className="bg-destructive/10 px-4 py-3 border-b border-destructive/20 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-destructive" />
          <h5 className="text-xs font-bold uppercase text-destructive tracking-widest">Circuit Breakers</h5>
        </div>
        <div className="p-5 grid grid-cols-2 md:grid-cols-3 gap-5">
          <div className="space-y-2">
            <Label className="text-[10px] font-bold text-destructive/80 uppercase">Max Drawdown</Label>
            <div className="relative group">
              <NumericInput
                value={mode.maxDrawdown}
                onChange={(v) => onUpdate({ maxDrawdown: v })}
                className="h-10 text-right font-mono text-destructive border-destructive/20 bg-background/50 focus:border-destructive focus:ring-1 focus:ring-destructive/20 transition-all pl-4 pr-8 rounded-lg"
              />
              <span className="absolute right-3 top-3 text-xs font-bold text-destructive">%</span>
            </div>
          </div>
          <div className="space-y-2">
            <Label className="text-[10px] font-bold text-destructive/80 uppercase">Daily Loss Limit</Label>
            <div className="relative group">
              <NumericInput
                value={mode.dailyLossLimit}
                onChange={(v) => onUpdate({ dailyLossLimit: v })}
                className="h-10 text-right font-mono text-destructive border-destructive/20 bg-background/50 focus:border-destructive focus:ring-1 focus:ring-destructive/20 transition-all pl-4 pr-8 rounded-lg"
              />
              <span className="absolute right-3 top-3 text-xs font-bold text-destructive">%</span>
            </div>
          </div>
          <div className="space-y-2">
            <Label className="text-[10px] font-bold text-destructive/80 uppercase">Weekly Limit</Label>
            <div className="relative group">
              <NumericInput
                value={mode.weeklyLossLimit}
                onChange={(v) => onUpdate({ weeklyLossLimit: v })}
                className="h-10 text-right font-mono text-destructive border-destructive/20 bg-background/50 focus:border-destructive focus:ring-1 focus:ring-destructive/20 transition-all pl-4 pr-8 rounded-lg"
              />
              <span className="absolute right-3 top-3 text-xs font-bold text-destructive">%</span>
            </div>
          </div>
        </div>
      </div>



    </div>
  );
};

const BrokerConfigPanel = ({ mode, onUpdate }: { mode: TradingModeConfig; onUpdate: (u: Partial<TradingModeConfig>) => void }) => {
  const [testing, setTesting] = useState(false);

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      let connectionData: any = { brokerType: mode.brokerType };

      if (mode.brokerType === "crypto_exchange") {
        connectionData = {
          ...connectionData,
          exchange: mode.exchange,
          apiKey: mode.apiKey,
          apiSecret: mode.apiSecret,
          testnet: mode.testnet,
        };
      } else if (mode.brokerType === "metatrader") {
        connectionData = {
          ...connectionData,
          mtType: mode.mtType,
          mtLogin: mode.mtLogin,
          mtPassword: mode.mtPassword,
          mtServer: mode.mtServer,
        };
      } else if (mode.brokerType === "fix") {
        connectionData = {
          ...connectionData,
          fixHost: mode.fixHost,
          fixPort: mode.fixPort,
          fixSenderCompId: mode.fixSenderCompId,
          fixTargetCompId: mode.fixTargetCompId,
          fixUsername: mode.fixUsername,
          fixPassword: mode.fixPassword,
          fixSslEnabled: mode.fixSslEnabled,
        };
      } else if (mode.brokerType === "dex") {
        connectionData = {
          ...connectionData,
          dexChain: mode.dexChain,
          dexExchange: mode.dexExchange,
          dexWalletAddress: mode.dexWalletAddress,
          dexPrivateKey: mode.dexPrivateKey,
          dexSlippage: mode.dexSlippage,
          dexPriorityFee: mode.dexPriorityFee,
        };
      }

      const result = await apiService.testBrokerConnection(connectionData);

      if (result.connected) {
        toast.success(result.message || "Connection successful!");
        onUpdate({ brokerConnected: true });
      } else {
        toast.error(result.message || "Connection failed");
        onUpdate({ brokerConnected: false });
      }
    } catch (error: any) {
      toast.error(error.message || "Connection test failed");
      onUpdate({ brokerConnected: false });
    } finally {
      setTesting(false);
    }
  };

  if (mode.brokerType === "none") return null;

  if (mode.brokerType === "crypto_exchange") {
    return (
      <div className="p-3 bg-secondary/30 rounded space-y-2">
        <div className="flex gap-2">
          <Select value={mode.exchange} onValueChange={(v) => {
            const sel = EXCHANGE_OPTIONS.find(ex => ex.value === v);
            onUpdate({ exchange: v, endpoint: sel?.defaultEndpoint || "", passphrase: "", brokerConnected: false });
          }}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{EXCHANGE_OPTIONS.filter(ex => ex.type === "both" || ex.type === mode.mode).map(ex => <SelectItem key={ex.value} value={ex.value}>{ex.icon} {ex.label}</SelectItem>)}</SelectContent>
          </Select>
          <Input value={mode.endpoint} onChange={(e) => onUpdate({ endpoint: e.target.value })} placeholder="API Endpoint" />
        </div>
        <Input type="password" value={mode.apiKey} onChange={(e) => onUpdate({ apiKey: e.target.value })} placeholder="API Key" />
        <Input type="password" value={mode.apiSecret} onChange={(e) => onUpdate({ apiSecret: e.target.value })} placeholder="API Secret" />
        {EXCHANGE_OPTIONS.find(ex => ex.value === mode.exchange)?.hasPassphrase && (
          <Input type="password" value={mode.passphrase} onChange={(e) => onUpdate({ passphrase: e.target.value })} placeholder="Passphrase" />
        )}
        <div className="flex items-center gap-2">
          <Switch checked={mode.testnet} onCheckedChange={(v) => onUpdate({ testnet: v })} className="scale-75" />
          <Label className="text-xs">Testnet Mode</Label>
        </div>
        <Button
          size="sm"
          variant={mode.brokerConnected ? "default" : "outline"}
          className={`w-full ${mode.brokerConnected ? 'bg-success hover:bg-success/90' : ''}`}
          onClick={handleTestConnection}
          disabled={testing || !mode.apiKey || !mode.apiSecret}
        >
          {testing ? (
            <><RefreshCw className="w-3 h-3 mr-2 animate-spin" /> Testing...</>
          ) : mode.brokerConnected ? (
            <><CheckCircle2 className="w-3 h-3 mr-2" /> Connected</>
          ) : (
            <>Test Connection</>
          )}
        </Button>
      </div>
    );
  }

  if (mode.brokerType === "metatrader") {
    return (
      <div className="p-3 bg-secondary/30 rounded space-y-3 border border-border">
        <h5 className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1"><Server className="w-3 h-3" /> MetaTrader Config</h5>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <Label className="text-xs">Platform:</Label>
            <div className="flex gap-1">
              <Button size="sm" className="h-6 px-2 text-xs" variant={mode.mtType === "mt4" ? "default" : "outline"} onClick={() => onUpdate({ mtType: "mt4", brokerConnected: false })}>MT4</Button>
              <Button size="sm" className="h-6 px-2 text-xs" variant={mode.mtType === "mt5" ? "default" : "outline"} onClick={() => onUpdate({ mtType: "mt5", brokerConnected: false })}>MT5</Button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Label className="text-xs">Account:</Label>
            <div className="flex gap-1">
              <Button size="sm" className="h-6 px-2 text-xs" variant={mode.mtAccountType === "demo" ? "secondary" : "ghost"} onClick={() => onUpdate({ mtAccountType: "demo" })}>Demo</Button>
              <Button size="sm" className="h-6 px-2 text-xs" variant={mode.mtAccountType === "live" ? "secondary" : "ghost"} onClick={() => onUpdate({ mtAccountType: "live" })}>Live</Button>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1"><Label className="text-[10px]">Broker Name</Label><Input className="h-8 text-xs" value={mode.mtBroker} onChange={e => onUpdate({ mtBroker: e.target.value })} placeholder="e.g. ICMarkets" /></div>
          <div className="space-y-1"><Label className="text-[10px]">Server Address</Label><Input className="h-8 text-xs" value={mode.mtServer} onChange={e => onUpdate({ mtServer: e.target.value })} placeholder="MetaQuotes-Demo" /></div>
          <div className="space-y-1"><Label className="text-[10px]">Login ID</Label><Input className="h-8 text-xs" value={mode.mtLogin} onChange={e => onUpdate({ mtLogin: e.target.value })} placeholder={mode.mtType === "mt5" ? "${MT5_LOGIN}" : "${MT4_LOGIN}"} /></div>
          <div className="space-y-1"><Label className="text-[10px]">Password</Label><Input className="h-8 text-xs" type="password" value={mode.mtPassword} onChange={e => onUpdate({ mtPassword: e.target.value })} placeholder={mode.mtType === "mt5" ? "${MT5_PASSWORD}" : "${MT4_PASSWORD}"} /></div>
        </div>
        <Button
          size="sm"
          variant={mode.brokerConnected ? "default" : "outline"}
          className={`w-full h-8 text-xs ${mode.brokerConnected ? 'bg-success hover:bg-success/90' : ''}`}
          onClick={handleTestConnection}
          disabled={testing || !mode.mtLogin || !mode.mtPassword}
        >
          {testing ? (
            <><RefreshCw className="w-3 h-3 mr-2 animate-spin" /> Testing {mode.mtType?.toUpperCase()}...</>
          ) : mode.brokerConnected ? (
            <><CheckCircle2 className="w-3 h-3 mr-2" /> Connected to {mode.mtType?.toUpperCase()}</>
          ) : (
            <>Test MT Connection</>
          )}
        </Button>
      </div>
    );
  }

  if (mode.brokerType === "fix") {
    return (
      <div className="p-3 bg-secondary/30 rounded space-y-3 border border-border">
        <h5 className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1"><Activity className="w-3 h-3" /> FIX Protocol Config</h5>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1"><Label className="text-[10px]">Host</Label><Input className="h-8 text-xs" value={mode.fixHost} onChange={e => onUpdate({ fixHost: e.target.value })} placeholder="fix.broker.com" /></div>
          <div className="space-y-1"><Label className="text-[10px]">Port</Label><Input className="h-8 text-xs" type="number" value={mode.fixPort} onChange={e => onUpdate({ fixPort: parseInt(e.target.value) })} /></div>
          <div className="space-y-1"><Label className="text-[10px]">Sender Comp ID</Label><Input className="h-8 text-xs" value={mode.fixSenderCompId} onChange={e => onUpdate({ fixSenderCompId: e.target.value })} /></div>
          <div className="space-y-1"><Label className="text-[10px]">Target Comp ID</Label><Input className="h-8 text-xs" value={mode.fixTargetCompId} onChange={e => onUpdate({ fixTargetCompId: e.target.value })} /></div>
          <div className="space-y-1"><Label className="text-[10px]">Username</Label><Input className="h-8 text-xs" value={mode.fixUsername} onChange={e => onUpdate({ fixUsername: e.target.value })} /></div>
          <div className="space-y-1"><Label className="text-[10px]">Password</Label><Input className="h-8 text-xs" type="password" value={mode.fixPassword} onChange={e => onUpdate({ fixPassword: e.target.value })} /></div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch checked={mode.fixSslEnabled} onCheckedChange={v => onUpdate({ fixSslEnabled: v })} className="scale-75" /> <Label className="text-xs">SSL</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch checked={mode.fixResetOnLogon} onCheckedChange={v => onUpdate({ fixResetOnLogon: v })} className="scale-75" /> <Label className="text-xs">Reset SeqNum</Label>
          </div>
        </div>
        <Button
          size="sm"
          variant={mode.brokerConnected ? "default" : "outline"}
          className={`w-full h-8 text-xs ${mode.brokerConnected ? 'bg-success hover:bg-success/90' : ''}`}
          onClick={handleTestConnection}
          disabled={testing || !mode.fixHost || !mode.fixSenderCompId}
        >
          {testing ? (
            <><RefreshCw className="w-3 h-3 mr-2 animate-spin" /> Sending FIX Logon...</>
          ) : mode.brokerConnected ? (
            <><CheckCircle2 className="w-3 h-3 mr-2" /> FIX Connected</>
          ) : (
            <>Test FIX Connection</>
          )}
        </Button>
      </div>
    );
  }

  if (mode.brokerType === "dex") {
    return (
      <div className="p-3 bg-secondary/30 rounded space-y-3 border border-border">
        <h5 className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1">
          <Globe className="w-3 h-3 text-primary" /> DEX (Decentralized Exchange) Config
        </h5>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="text-[10px]">Blockchain Network</Label>
            <Select value={mode.dexChain} onValueChange={(v) => {
              const options = mode.mode === "futures" ? (DEX_PERP_EXCHANGES[v] || []) : (DEX_EXCHANGES[v] || []);
              onUpdate({ dexChain: v, dexExchange: options[0]?.value || "" });
            }}>
              <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Select Chain" /></SelectTrigger>
              <SelectContent>
                {DEX_CHAINS.filter(chain => {
                  if (mode.mode === "futures") return !!DEX_PERP_EXCHANGES[chain.value];
                  return !!DEX_EXCHANGES[chain.value];
                }).map(chain => (
                  <SelectItem key={chain.value} value={chain.value}>{chain.icon} {chain.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label className="text-[10px]">{mode.mode === "futures" ? "Perpetual DEX" : "DEX Protocol"}</Label>
            <Select value={mode.dexExchange} onValueChange={(v) => onUpdate({ dexExchange: v })}>
              <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Select Protocol" /></SelectTrigger>
              <SelectContent>
                {(mode.mode === "futures" ? (DEX_PERP_EXCHANGES[mode.dexChain] || []) : (DEX_EXCHANGES[mode.dexChain] || [])).map(dex => (
                  <SelectItem key={dex.value} value={dex.value}>{dex.icon} {dex.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-1">
          <Label className="text-[10px]">Wallet Public Address</Label>
          <Input
            className="h-8 text-xs font-mono"
            value={mode.dexWalletAddress}
            onChange={e => onUpdate({ dexWalletAddress: e.target.value })}
            placeholder="0x... or Solana Address"
          />
        </div>

        <div className="space-y-1">
          <Label className="text-[10px]">Encrypted Private Key / Seed</Label>
          <div className="relative">
            <Input
              type="password"
              className="h-8 text-xs font-mono pr-10"
              value={mode.dexPrivateKey}
              onChange={e => onUpdate({ dexPrivateKey: e.target.value })}
              placeholder="Private Key (Keep safe!)"
            />
            <ShieldCheck className="absolute right-3 top-2 w-4 h-4 text-muted-foreground opacity-50" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label className="text-[10px]">Max Slippage (%)</Label>
              <div className="flex items-center gap-1">
                <Switch
                  checked={mode.dexAutoSlippage}
                  onCheckedChange={v => onUpdate({ dexAutoSlippage: v })}
                  className="scale-50 origin-right"
                />
                <span className="text-[8px] font-bold uppercase text-accent">Auto</span>
              </div>
            </div>
            <div className="relative group">
              <NumericInput
                value={mode.dexSlippage}
                onChange={v => onUpdate({ dexSlippage: v })}
                className={`h-8 text-right font-mono text-xs pr-8 ${mode.dexAutoSlippage ? 'bg-secondary/20 opacity-50 cursor-not-allowed' : ''}`}
                disabled={mode.dexAutoSlippage}
              />
              <span className="absolute right-2 top-2 text-[9px] font-bold text-muted-foreground">%</span>
              {mode.dexAutoSlippage && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <Badge variant="outline" className="h-4 text-[7px] bg-accent/10 border-accent/20 text-accent">DYNAMIC</Badge>
                </div>
              )}
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label className="text-[10px]">Priority Fee (Tip)</Label>
              <div className="flex items-center gap-1">
                <Switch
                  checked={mode.dexAutoPriorityFee}
                  onCheckedChange={v => onUpdate({ dexAutoPriorityFee: v })}
                  className="scale-50 origin-right"
                />
                <span className="text-[8px] font-bold uppercase text-accent">Auto</span>
              </div>
            </div>
            <div className="relative group">
              <NumericInput
                value={mode.dexPriorityFee}
                onChange={v => onUpdate({ dexPriorityFee: v })}
                className={`h-8 text-right font-mono text-xs pr-10 ${mode.dexAutoPriorityFee ? 'bg-secondary/20 opacity-50 cursor-not-allowed' : ''}`}
                disabled={mode.dexAutoPriorityFee}
              />
              <span className="absolute right-2 top-2 text-[8px] font-bold text-muted-foreground">Native</span>
              {mode.dexAutoPriorityFee && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <Badge variant="outline" className="h-4 text-[7px] bg-accent/10 border-accent/20 text-accent">OPTIMIZED</Badge>
                </div>
              )}
            </div>
          </div>
        </div>

        <Button
          size="sm"
          variant={mode.brokerConnected ? "default" : "outline"}
          className={`w-full h-8 text-xs ${mode.brokerConnected ? 'bg-success hover:bg-success/90' : ''}`}
          onClick={handleTestConnection}
          disabled={testing || !mode.dexWalletAddress || !mode.dexPrivateKey}
        >
          {testing ? (
            <><RefreshCw className="w-3 h-3 mr-2 animate-spin" /> Verifying Wallet...</>
          ) : mode.brokerConnected ? (
            <><CheckCircle2 className="w-3 h-3 mr-2" /> Wallet Connected</>
          ) : (
            <>Sync Wallet & Test Connection</>
          )}
        </Button>
      </div>
    );
  }

  return null;
};

const TimeSettingsPanel = ({ mode, onUpdate }: { mode: TradingModeConfig; onUpdate: (u: Partial<TradingModeConfig>) => void }) => {
  return (
    <div className="mt-4 p-3 bg-secondary/20 rounded-lg border border-border">
      <div className="flex items-center justify-between mb-3">
        <Label className="font-semibold text-xs flex items-center gap-1">
          <Clock className="w-3 h-3 text-primary" /> Entry Time Window
        </Label>
        <Switch
          checked={mode.timeEntryEnabled}
          onCheckedChange={(v) => onUpdate({ timeEntryEnabled: v })}
          className="scale-75 origin-right"
        />
      </div>

      {mode.timeEntryEnabled && (
        <div className="grid grid-cols-2 gap-3 animate-in fade-in slide-in-from-top-1 duration-200">
          <div className="space-y-1">
            <Label className="text-[10px]">Start Time</Label>
            <Input
              type="time"
              value={mode.entryStartTime || "00:00"}
              onChange={(e) => onUpdate({ entryStartTime: e.target.value })}
              className="h-8 text-xs bg-background"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[10px]">End Time</Label>
            <Input
              type="time"
              value={mode.entryEndTime || "23:59"}
              onChange={(e) => onUpdate({ entryEndTime: e.target.value })}
              className="h-8 text-xs bg-background"
            />
          </div>
          <p className="col-span-2 text-[9px] text-muted-foreground italic">
            Trades will only be entered within this time window.
          </p>
        </div>
      )}
      {!mode.timeEntryEnabled && (
        <p className="text-[10px] text-muted-foreground flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-success" /> 24/7 trading enabled.
        </p>
      )}
    </div>
  );
};

const MultiTfConfirmationPanel = ({ mode, onUpdate }: { mode: TradingModeConfig; onUpdate: (u: Partial<TradingModeConfig>) => void }) => {
  const toggleTf = (tfValue: string) => {
    const current = mode.confirmationTimeframes || [];
    const updated = current.includes(tfValue)
      ? current.filter(t => t !== tfValue)
      : [...current, tfValue];
    onUpdate({ confirmationTimeframes: updated });
  };

  return (
    <div className="mt-4 p-3 bg-secondary/20 rounded-lg border border-border">
      <div className="flex items-center justify-between mb-3">
        <Label className="font-semibold text-xs flex items-center gap-1">
          <Layers className="w-3 h-3 text-primary" /> Multi-Timeframe Confirmation
        </Label>
        <Switch
          checked={mode.useMultiTf}
          onCheckedChange={(v) => onUpdate({ useMultiTf: v })}
          className="scale-75 origin-right"
        />
      </div>

      {mode.useMultiTf && (
        <div className="space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
          <p className="text-[10px] text-muted-foreground">Select timeframes to confirm trend/signals before entry:</p>
          <div className="flex flex-wrap gap-1">
            {timeframes.map((tf) => (
              <Badge
                key={tf.value}
                variant={mode.confirmationTimeframes?.includes(tf.value) ? "default" : "outline"}
                className="cursor-pointer text-[9px] px-1.5 h-5"
                onClick={() => toggleTf(tf.value)}
              >
                {tf.label}
              </Badge>
            ))}
          </div>
          {mode.confirmationTimeframes?.length === 0 && (
            <p className="text-[9px] text-destructive italic">Please select at least one timeframe.</p>
          )}
        </div>
      )}
      {!mode.useMultiTf && (
        <p className="text-[10px] text-muted-foreground flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-success" /> Single timeframe entry.
        </p>
      )}
    </div>
  );
};

interface FeatureConfig {
  technical: {
    enabled: boolean;
    features: string[];
  };
  gann: {
    enabled: boolean;
    features: string[];
  };
  ehlers: {
    enabled: boolean;
    features: string[];
  };
  astro: {
    enabled: boolean;
    features: string[];
  };
  microstructure: {
    enabled: boolean;
    features: string[];
  };
  time: {
    enabled: boolean;
    features: string[];
  };
  transformations: {
    lags: boolean;
    rolling: boolean;
    differences: boolean;
    ratios: boolean;
  };
  selection: {
    enabled: boolean;
    method: string;
    topK: number;
    correlationThreshold: number;
  };
}

const Settings = () => {
  // --- States ---
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Enhanced System States ---
  const [autoDetectTimezone, setAutoDetectTimezone] = useState(true);
  const [marketBirthAuto, setMarketBirthAuto] = useState(true);
  const [syncWithDashboard, setSyncWithDashboard] = useState(true);
  const [activeEpochs, setActiveEpochs] = useState<string[]>(["btc", "sp500"]);

  // --- Planetary Vibration Automation States ---
  const [autoPlanetaryVibration, setAutoPlanetaryVibration] = useState(true);
  const [planetaryFactors, setPlanetaryFactors] = useState<Record<string, number>>({
    sun: 1.0, moon: 1.0, merc: 1.0, venus: 1.0, mars: 1.0, jup: 1.0, sat: 1.0, ura: 1.0
  });

  // --- AI Feature Engineering States ---
  const [featureConfig, setFeatureConfig] = useState<FeatureConfig>({
    technical: {
      enabled: true,
      features: ["rsi", "macd", "bollinger_bands", "stochastic", "adx", "atr"]
    },
    gann: {
      enabled: true,
      features: ["square_of_9", "gann_fan", "time_cycles", "vibration"]
    },
    ehlers: {
      enabled: true,
      features: ["mama_fama", "fisher_transform", "cyber_cycle", "super_smoother"]
    },
    astro: {
      enabled: true,
      features: ["aspects", "lunar_phase", "retrograde", "bradley"]
    },
    microstructure: {
      enabled: false,
      features: ["order_flow", "imbalance", "volume_profile"]
    },
    time: {
      enabled: true,
      features: ["hour", "day_of_week", "month", "session"]
    },
    transformations: {
      lags: true,
      rolling: true,
      differences: true,
      ratios: false
    },
    selection: {
      enabled: true,
      method: "correlation",
      topK: 50,
      correlationThreshold: 0.95
    }
  });

  const updateFeatureConfig = <K extends keyof FeatureConfig>(section: K, update: Partial<FeatureConfig[K]>) => {
    setFeatureConfig(prev => ({
      ...prev,
      [section]: { ...prev[section], ...update }
    }));
  };

  const toggleFeature = (section: keyof FeatureConfig, feature: string) => {
    setFeatureConfig(prev => {
      const sectionData = prev[section];
      if (!('features' in sectionData)) return prev;

      const currentFeatures = sectionData.features as string[];
      const newFeatures = currentFeatures.includes(feature)
        ? currentFeatures.filter(f => f !== feature)
        : [...currentFeatures, feature];

      return {
        ...prev,
        [section]: { ...sectionData, features: newFeatures }
      };
    });
  };

  // Comprehensive Market Birth Database
  const MARKET_EPOCHS: Record<string, { date: string, time: string, lat: number, lon: number, name: string }> = {
    btc: { name: "Bitcoin Genesis", date: "2009-01-03", time: "18:15", lat: 51.5074, lon: -0.1278 },
    eth: { name: "Ethereum Genesis", date: "2015-07-30", time: "15:26", lat: 47.3769, lon: 8.5417 },
    sol: { name: "Solana Genesis", date: "2020-03-16", time: "12:00", lat: 37.7749, lon: -122.4194 },
    sp500: { name: "S&P 500 Modern Era", date: "1957-03-04", time: "09:30", lat: 40.7128, lon: -74.0060 },
    nasdaq: { name: "NASDAQ Launch", date: "1971-02-08", time: "09:30", lat: 40.7128, lon: -74.0060 },
    dji: { name: "Dow Jones Ind", date: "1896-05-26", time: "09:30", lat: 40.7128, lon: -74.0110 },
    gold: { name: "Gold Standard Fix", date: "1919-09-12", time: "11:00", lat: 51.5074, lon: -0.1278 },
    idx: { name: "IDX Composite (Modern)", date: "1982-08-10", time: "09:00", lat: -6.2233, lon: 106.8114 },
    idx_1912: { name: "Jakarta Stock Exchange (1792 History/1912)", date: "1912-12-14", time: "09:00", lat: -6.2233, lon: 106.8114 },
    idx_1977: { name: "IDX Modern Re-Opening", date: "1977-06-16", time: "09:00", lat: -6.2233, lon: 106.8114 },
    lq45: { name: "LQ45 Index Inception", date: "1997-02-01", time: "09:00", lat: -6.2233, lon: 106.8114 },
    nikkei: { name: "Nikkei 225", date: "1950-09-07", time: "09:00", lat: 35.6762, lon: 139.6503 },
    hsi: { name: "Hang Seng", date: "1969-11-24", time: "10:00", lat: 22.2855, lon: 114.1577 },
    ftse: { name: "FTSE 100", date: "1984-01-03", time: "08:00", lat: 51.5151, lon: -0.0917 },
    dax: { name: "DAX Index", date: "1988-07-01", time: "09:00", lat: 50.1109, lon: 8.6821 },
    nifty: { name: "Nifty 50", date: "1994-04-22", time: "09:15", lat: 18.9220, lon: 72.8347 },
    cac: { name: "CAC 40", date: "1987-12-31", time: "09:30", lat: 48.8686, lon: 2.3411 },
    asx: { name: "ASX 200 (Australia)", date: "2000-03-31", time: "10:00", lat: -33.8688, lon: 151.2093 },
    ibex: { name: "IBEX 35 (Spain)", date: "1992-01-14", time: "09:00", lat: 40.4168, lon: -3.7038 },
    ftsemib: { name: "FTSE MIB (Italy)", date: "2004-12-31", time: "09:00", lat: 45.4642, lon: 9.1900 },
    kospi: { name: "KOSPI (S.Korea)", date: "1980-01-04", time: "09:00", lat: 37.5665, lon: 126.9780 },
    sti: { name: "STI (Singapore)", date: "1999-08-31", time: "09:00", lat: 1.3521, lon: 103.8198 },
    klci: { name: "KLCI (Malaysia)", date: "1977-01-01", time: "09:00", lat: 3.1390, lon: 101.6869 },
    set: { name: "SET (Thailand)", date: "1975-04-30", time: "09:00", lat: 13.7563, lon: 100.5018 },
    bovespa: { name: "B3 IBOVESPA (Brazil)", date: "1968-01-02", time: "10:00", lat: -23.5505, lon: -46.6333 },
    tsx: { name: "TSX Composite (Canada)", date: "1977-01-01", time: "09:30", lat: 43.6532, lon: -79.3832 },
    sse: { name: "Shanghai Composite (China)", date: "1990-12-19", time: "09:30", lat: 31.2304, lon: 121.4737 },
    szse: { name: "Shenzhen Component (China)", date: "1991-04-03", time: "09:30", lat: 22.5431, lon: 114.0579 },
    merval: { name: "MERVAL (Argentina)", date: "1986-06-30", time: "11:00", lat: -34.6037, lon: -58.3816 },
    moex: { name: "MOEX Russia", date: "1997-09-22", time: "10:00", lat: 55.7558, lon: 37.6173 },
    tasi: { name: "TASI (Saudi Arabia)", date: "1985-01-01", time: "10:00", lat: 24.7136, lon: 46.6753 },
    jse: { name: "JSE All Share (S.Africa)", date: "1960-01-02", time: "09:00", lat: -26.2041, lon: 28.0473 },
    bist: { name: "BIST 100 (Turkey)", date: "1986-01-02", time: "10:00", lat: 41.0082, lon: 28.9784 },
    ipc: { name: "IPC Mexico", date: "1978-10-30", time: "08:30", lat: 19.4326, lon: -99.1332 },
    smi: { name: "SMI (Switzerland)", date: "1988-06-30", time: "09:00", lat: 47.3769, lon: 8.5417 },
    stoxx50: { name: "Euro Stoxx 50", date: "1991-12-31", time: "09:00", lat: 50.1109, lon: 8.6821 },
    buttonwood: { name: "NYSE Buttonwood (1792)", date: "1792-05-17", time: "08:00", lat: 40.7069, lon: -74.0110 },
  };

  const WORLD_EXCHANGES = [
    { value: "America/New_York", label: "NYSE/NASDAQ (New York)" },
    { value: "America/Chicago", label: "CME/CBOT (Chicago)" },
    { value: "America/Toronto", label: "TSX (Toronto)" },
    { value: "America/Mexico_City", label: "BMV (Mexico)" },
    { value: "America/Argentina/Buenos_Aires", label: "BCBA (Argentina)" },
    { value: "America/Sao_Paulo", label: "B3 (Brazil)" },
    { value: "Europe/London", label: "LSE (London)" },
    { value: "Europe/Paris", label: "Euronext Paris" },
    { value: "Europe/Frankfurt", label: "Xetra (Germany)" },
    { value: "Europe/Zurich", label: "SIX (Switzerland)" },
    { value: "Europe/Moscow", label: "MOEX (Russia)" },
    { value: "Europe/Istanbul", label: "BIST (Turkey)" },
    { value: "Asia/Jakarta", label: "IDX (Jakarta)" },
    { value: "Asia/Singapore", label: "SGX (Singapore)" },
    { value: "Asia/Hong_Kong", label: "HKEX (Hong Kong)" },
    { value: "Asia/Tokyo", label: "TSE (Tokyo)" },
    { value: "Asia/Shanghai", label: "SSE (China)" },
    { value: "Asia/Seoul", label: "KRX (S.Korea)" },
    { value: "Asia/Kolkata", label: "NSE/BSE (India)" },
    { value: "Asia/Riyadh", label: "Tadawul (Saudi Arabia)" },
    { value: "Africa/Johannesburg", label: "JSE (S.Africa)" },
    { value: "Australia/Sydney", label: "ASX (Sydney)" },
  ];


  // Trading Config State
  const [activeModes, setActiveModes] = useState<TradingModeConfig[]>(() => {
    const saved = localStorage.getItem("tradingModes");
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error(e); }
    }
    return [
      {
        id: "spot-1", name: "Spot Trading - Primary", mode: "spot", enabled: true, leverage: 1, marginMode: "cross",
        openLotSize: 0.01, autoLotSize: false, trailingStop: false, trailingStopDistance: 1, autoDeleverage: false, hedgingEnabled: false,
        selectedInstrument: "", riskType: "dynamic", riskPerTrade: 2.0, kellyFraction: 0.5, adaptiveSizing: true,
        volatilityAdjustment: true, drawdownProtection: true, maxDrawdown: 15, dailyLossLimit: 5, weeklyLossLimit: 15,
        breakEvenOnProfit: true, liquidationAlert: 0, fixedRiskPerTrade: 2.0, fixedMaxDrawdown: 20, riskRewardRatio: 2.0,
        fixedLotSize: 0.01, maxOpenPositions: 5, brokerType: "crypto_exchange", exchange: "binance", endpoint: "https://api.binance.com",
        apiKey: "", apiSecret: "", passphrase: "", testnet: true, brokerConnected: false, mtType: "", mtServer: "", mtLogin: "",
        mtPassword: "", mtAccountType: "demo", mtBroker: "", fixSenderCompId: "", fixTargetCompId: "", fixHost: "", fixPort: 443,
        fixUsername: "", fixPassword: "", fixHeartbeatInterval: 30, fixResetOnLogon: true, fixSslEnabled: true,
        dexChain: "solana", dexExchange: "jupiter", dexWalletAddress: "", dexPrivateKey: "", dexSlippage: 0.5, dexPriorityFee: 0.0001,
        dexAutoSlippage: true, dexAutoPriorityFee: true,
        timeEntryEnabled: false, entryStartTime: "00:00", entryEndTime: "23:59",
        useMultiTf: false, confirmationTimeframes: ["H1", "H4", "D1"],
      },
      {
        id: "futures-1", name: "Futures Trading - Primary", mode: "futures", enabled: true, leverage: 10, marginMode: "isolated",
        openLotSize: 0.1, autoLotSize: true, trailingStop: true, trailingStopDistance: 0.5, autoDeleverage: true, hedgingEnabled: true,
        selectedInstrument: "BTC/USDT", riskType: "dynamic", riskPerTrade: 1.5, kellyFraction: 0.5, adaptiveSizing: true,
        volatilityAdjustment: true, drawdownProtection: true, maxDrawdown: 10, dailyLossLimit: 3, weeklyLossLimit: 10,
        breakEvenOnProfit: true, liquidationAlert: 80, fixedRiskPerTrade: 2.0, fixedMaxDrawdown: 20, riskRewardRatio: 2.0,
        fixedLotSize: 0.1, maxOpenPositions: 3, brokerType: "crypto_exchange", exchange: "binance", endpoint: "https://fapi.binance.com",
        apiKey: "", apiSecret: "", passphrase: "", testnet: true, brokerConnected: false, mtType: "", mtServer: "", mtLogin: "",
        mtPassword: "", mtAccountType: "demo", mtBroker: "", fixSenderCompId: "", fixTargetCompId: "", fixHost: "", fixPort: 443,
        fixUsername: "", fixPassword: "", fixHeartbeatInterval: 30, fixResetOnLogon: true, fixSslEnabled: true,
        timeEntryEnabled: false, entryStartTime: "00:00", entryEndTime: "23:59",
        useMultiTf: false, confirmationTimeframes: ["M15", "H1", "H4"],
      },
    ]
  });
  const [manualLeverages, setManualLeverages] = useState<ManualLeverageConfig[]>(() => {
    const saved = localStorage.getItem("manualLeverages");
    if (saved) { try { return JSON.parse(saved); } catch (e) { console.error(e); } }
    return [
      { instrument: "BTC/USDT", leverage: 25, marginMode: "isolated" },
      { instrument: "ETH/USDT", leverage: 20, marginMode: "isolated" },
      { instrument: "EUR/USD", leverage: 100, marginMode: "cross" },
      { instrument: "XAU/USD", leverage: 20, marginMode: "cross" },
    ];
  });
  const [newLeverageInput, setNewLeverageInput] = useState({ instrument: "", leverage: 10, marginMode: "isolated" as "cross" | "isolated" });
  const [isRunning, setIsRunning] = useState(false);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  // Settings State
  const [tfWeights, setTfWeights] = useState<TimeframeWeights>(() => {
    const saved = localStorage.getItem("strategyWeights");
    return saved ? JSON.parse(saved) : createInitialWeights();
  });

  // Save weights to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("strategyWeights", JSON.stringify(tfWeights));
  }, [tfWeights]);

  // Load all settings from backend on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await apiService.loadSettingsFromBackend();
        if (response.success && response.settings) {
          const s = response.settings;

          if (s.tradingModes && s.tradingModes.length > 0) setActiveModes(s.tradingModes);
          if (s.manualLeverages && s.manualLeverages.length > 0) setManualLeverages(s.manualLeverages);
          if (s.strategyWeights && Object.keys(s.strategyWeights).length > 0) setTfWeights(s.strategyWeights);

          if (s.mlConfig) {
            setFeatureConfig(prev => ({
              ...prev,
              ...s.mlConfig
            }));
          }

          // Note: syncing instruments from backend is complex due to object structure mismatch
          // We rely on local/default list and only sync ENABLED status if we implemented full mapping

          toast.success("Settings loaded from backend configuration");
        }
      } catch (error) {
        console.error("Failed to load settings", error);
        // Silent fail or toast error? Silent for now to avoid annoyance if offline
      }
    };
    loadSettings();
  }, []);
  const [activeTf, setActiveTf] = useState("H1");
  const [instruments, setInstruments] = useState(() => {
    const saved = localStorage.getItem("tradingInstruments");
    if (saved) { try { return JSON.parse(saved); } catch { /* ignore parse error */ } }
    return instrumentsData;
  });
  const [instrumentSearch, setInstrumentSearch] = useState("");
  const [activeInstrumentTab, setActiveInstrumentTab] = useState<InstrumentCategory>("forex");
  const [newInstrument, setNewInstrument] = useState({ symbol: "", name: "", category: "" });
  const [customInstrumentCategory, setCustomInstrumentCategory] = useState<InstrumentCategory>("forex");

  // --- Handlers ---
  const toggleSecret = (key: string) => setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }));
  const handleUpdateMode = useCallback((id: string, updates: Partial<TradingModeConfig>) => {
    setActiveModes(prev => prev.map(m => m.id === id ? { ...m, ...updates } : m));
  }, []);
  const handleModeToggle = (id: string) => {
    const updated = activeModes.map(m => m.id === id ? { ...m, enabled: !m.enabled } : m);
    setActiveModes(updated);
    const mode = updated.find(m => m.id === id);
    toast.success(`${mode?.name} ${mode?.enabled ? 'enabled' : 'disabled'}`);
  };
  const addNewMode = (type: "spot" | "futures") => {
    const newMode: TradingModeConfig = {
      id: `${type}-${Date.now()}`, name: `${type === 'spot' ? 'Spot' : 'Futures'} Trading - New`, mode: type, enabled: false,
      leverage: type === "spot" ? 1 : 5, marginMode: "isolated", openLotSize: type === "spot" ? 0.01 : 0.1, autoLotSize: type === "futures", trailingStop: false,
      trailingStopDistance: 1, autoDeleverage: type === "futures", hedgingEnabled: type === "futures", selectedInstrument: type === "futures" ? "BTC/USDT" : "",
      riskType: "dynamic", riskPerTrade: type === "spot" ? 2.0 : 1.5, kellyFraction: 0.5, adaptiveSizing: true, volatilityAdjustment: true,
      drawdownProtection: true, maxDrawdown: type === "spot" ? 15 : 10, dailyLossLimit: type === "spot" ? 5 : 3, weeklyLossLimit: type === "spot" ? 15 : 10,
      breakEvenOnProfit: true, liquidationAlert: type === "futures" ? 80 : 0, fixedRiskPerTrade: 2.0, fixedMaxDrawdown: 20, riskRewardRatio: 2.0,
      fixedLotSize: type === "spot" ? 0.01 : 0.1, maxOpenPositions: type === "spot" ? 5 : 3, brokerType: "crypto_exchange", exchange: "binance",
      endpoint: type === "spot" ? "https://api.binance.com" : "https://fapi.binance.com", apiKey: "", apiSecret: "", passphrase: "", testnet: true,
      brokerConnected: false, mtType: "", mtServer: "", mtLogin: "",
      mtPassword: "", mtAccountType: "demo", mtBroker: "", fixSenderCompId: "",
      fixTargetCompId: "", fixHost: "", fixPort: 443, fixUsername: "", fixPassword: "", fixHeartbeatInterval: 30, fixResetOnLogon: true, fixSslEnabled: true,
      dexChain: "solana", dexExchange: "jupiter", dexWalletAddress: "", dexPrivateKey: "", dexSlippage: 0.5, dexPriorityFee: 0.0001,
      dexAutoSlippage: true, dexAutoPriorityFee: true,
      timeEntryEnabled: false, entryStartTime: "00:00", entryEndTime: "23:59",
      useMultiTf: false, confirmationTimeframes: ["H1", "H4"],
    };
    setActiveModes(prev => [...prev, newMode]);
    toast.success(`New ${type} configuration added`);
  };
  const removeMode = (id: string) => {
    setActiveModes(prev => prev.filter(m => m.id !== id));
    toast.success("Configuration removed");
  };

  const testBrokerConnection = (id: string) => {
    const mode = activeModes.find(m => m.id === id);
    if (!mode) return;
    toast.info(`Testing connection for ${mode.name}...`);
    setTimeout(() => {
      handleUpdateMode(id, { brokerConnected: true });
      toast.success("Connection successful!");
    }, 1500);
  };

  // Leverage Handlers
  const addManualLeverage = () => {
    if (!newLeverageInput.instrument.trim()) return toast.error("Enter instrument name");
    if (manualLeverages.some(l => l.instrument.toLowerCase() === newLeverageInput.instrument.toLowerCase())) return toast.error("Exists");
    setManualLeverages(prev => [...prev, { ...newLeverageInput, instrument: newLeverageInput.instrument.toUpperCase() }]);
    setNewLeverageInput({ instrument: "", leverage: 10, marginMode: "isolated" });
    toast.success("Leverage added");
  };
  const removeManualLeverage = (inst: string) => setManualLeverages(prev => prev.filter(l => l.instrument !== inst));
  const updateManualLeverage = (inst: string, up: Partial<ManualLeverageConfig>) => setManualLeverages(prev => prev.map(l => l.instrument === inst ? { ...l, ...up } : l));
  const handleInstrumentChange = (modeId: string, inst: string) => {
    const lev = manualLeverages.find(l => l.instrument === inst);
    if (lev) { handleUpdateMode(modeId, { selectedInstrument: inst, leverage: lev.leverage, marginMode: lev.marginMode }); toast.success("Leverage synced"); }
    else handleUpdateMode(modeId, { selectedInstrument: inst });
  };

  // Instrument Handlers
  const addCustomInstrument = () => {
    if (!newInstrument.symbol.trim() || !newInstrument.name.trim()) return toast.error("Fill symbol and name");
    const inst: Instrument = { symbol: newInstrument.symbol.toUpperCase().trim(), name: newInstrument.name.trim(), enabled: true, category: newInstrument.category.trim() || "Custom" };
    if (instruments[customInstrumentCategory].some(i => i.symbol === inst.symbol)) return toast.error("Exists");
    setInstruments(prev => ({ ...prev, [customInstrumentCategory]: [...prev[customInstrumentCategory], inst] }));
    setNewInstrument({ symbol: "", name: "", category: "" });
    toast.success("Instrument added");
  };
  const removeInstrument = (cat: InstrumentCategory, sym: string) => {
    setInstruments(prev => ({ ...prev, [cat]: prev[cat].filter(i => i.symbol !== sym) }));
    toast.success(`${sym} removed`);
  };
  const toggleInstrument = (cat: InstrumentCategory, sym: string) => {
    setInstruments(prev => ({ ...prev, [cat]: prev[cat].map(i => i.symbol === sym ? { ...i, enabled: !i.enabled } : i) }));
  };
  const handleWeightChange = (tf: string, idx: number, w: number) => {
    setTfWeights(prev => ({ ...prev, [tf]: prev[tf].map((s, i) => i === idx ? { ...s, weight: w } : s) }));
  };

  // Global Actions
  const handleSaveAllSettings = async () => {
    try {
      // Save to localStorage first
      localStorage.setItem("tradingModes", JSON.stringify(activeModes));
      localStorage.setItem("manualLeverages", JSON.stringify(manualLeverages));
      localStorage.setItem("strategyWeights", JSON.stringify(tfWeights));
      localStorage.setItem("tradingInstruments", JSON.stringify(instruments));

      // Build comprehensive risk settings from active modes
      const primaryMode = activeModes.find(m => m.enabled) || activeModes[0];
      const riskSettings = primaryMode ? {
        // Risk type (dynamic vs fixed)
        riskType: primaryMode.riskType,

        // === DYNAMIC RISK SETTINGS ===
        riskPerTrade: primaryMode.riskPerTrade,
        kellyFraction: primaryMode.kellyFraction,
        adaptiveSizing: primaryMode.adaptiveSizing,
        volatilityAdjustment: primaryMode.volatilityAdjustment,
        maxDrawdown: primaryMode.maxDrawdown,
        dailyLossLimit: primaryMode.dailyLossLimit,
        weeklyLossLimit: primaryMode.weeklyLossLimit,
        drawdownProtection: primaryMode.drawdownProtection,

        // === FIXED RISK SETTINGS ===
        fixedRiskPerTrade: primaryMode.fixedRiskPerTrade,
        fixedLotSize: primaryMode.fixedLotSize,
        riskRewardRatio: primaryMode.riskRewardRatio,
        fixedMaxDrawdown: primaryMode.fixedMaxDrawdown,

        // === COMMON SETTINGS ===
        maxOpenPositions: primaryMode.maxOpenPositions,
        trailingStop: primaryMode.trailingStop,
        trailingStopDistance: primaryMode.trailingStopDistance,
        breakEvenOnProfit: primaryMode.breakEvenOnProfit,
        liquidationAlert: primaryMode.liquidationAlert,

        // Trading mode specific
        leverage: primaryMode.leverage,
        marginMode: primaryMode.marginMode,
      } : {};

      // Sync to backend YAML config files
      try {
        // Try new config sync API first
        await apiService.syncAllConfigsToBackend({
          tradingModes: activeModes,
          strategyWeights: tfWeights,
          instruments: instruments, // Backend will extract enabled symbols
          manualLeverages: manualLeverages,
          riskSettings: riskSettings,
          notificationSettings: {}, // Add if available
          mlConfig: featureConfig,  // Add ML Config
        } as any);

        toast.success("All configurations saved and synced to YAML config files");
      } catch (syncError) {
        // Fallback to old API
        try {
          await apiService.syncAllSettings({
            tradingModes: activeModes,
            instruments: instruments,
            strategyWeights: tfWeights,
            manualLeverages: manualLeverages
          });
          toast.success("All configurations saved and synced to backend");
        } catch (fallbackError) {
          console.warn("Backend sync failed, saved to localStorage only:", fallbackError);
          toast.success("Configurations saved locally (backend sync unavailable)");
        }
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to save configurations");
    }
  };

  const handleExportSettings = () => {
    const settings = { version: "2.0", exportDate: new Date().toISOString(), activeModes, manualLeverages, tfWeights, instruments };
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `full-trading-config-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Settings exported");
  };

  const handleImportSettings = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        if (data.activeModes) setActiveModes(data.activeModes);
        if (data.manualLeverages) setManualLeverages(data.manualLeverages);
        if (data.tfWeights) setTfWeights(data.tfWeights);
        if (data.instruments) setInstruments(data.instruments);
        toast.success("Settings imported successfully");
      } catch { toast.error("Invalid file"); }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const spotModes = activeModes.filter(m => m.mode === "spot");
  const futuresModes = activeModes.filter(m => m.mode === "futures");
  const activeCount = activeModes.filter(m => m.enabled).length;

  return (
    <div className="space-y-6 px-2 md:px-0">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tighter text-foreground flex items-center gap-4 uppercase">
            <div className="w-20 h-20 rounded-2xl bg-black/40 p-2 border border-primary/20 shadow-[0_0_30px_rgba(var(--primary),0.15)] flex items-center justify-center">
              <img
                src="/Tanpa Judul.ico"
                alt="Logo"
                className="w-full h-full object-contain"
                onError={(e) => { e.currentTarget.src = "/placeholder.svg"; }}
              />
            </div>
            Cenayang <span className="text-primary">Settings</span>
          </h1>
          <p className="text-sm text-muted-foreground">Manage trading modes, strategies, and system configuration</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleSaveAllSettings} variant="outline" className="gap-2 border-primary/50 text-foreground hover:bg-primary/10">
            <Save className="w-4 h-4" /> Save All
          </Button>
          <Button onClick={() => setIsRunning(!isRunning)} variant={isRunning ? "destructive" : "default"} className="gap-2">
            {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />} {isRunning ? "Pause System" : "Start System"}
          </Button>
          <Button onClick={handleExportSettings} variant="outline" className="gap-2"><Download className="w-4 h-4" /> Export</Button>
          <Button onClick={() => fileInputRef.current?.click()} variant="outline" className="gap-2"><Upload className="w-4 h-4" /> Import</Button>
          <input ref={fileInputRef} type="file" accept=".json" className="hidden" onChange={handleImportSettings} />
        </div>
      </div>

      <Tabs defaultValue="modes" className="w-full">
        <TabsList className="grid w-full grid-cols-5 lg:w-[1000px] mb-6">
          <TabsTrigger value="modes">Trading Modes</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
          <TabsTrigger value="instruments">Instruments</TabsTrigger>
          <TabsTrigger value="ai-engineering">
            <Cpu className="w-4 h-4 mr-2" />
            AI Engineering
          </TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="modes" className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Card className="p-4 border-border bg-card flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-success/20 flex items-center justify-center"><TrendingUp className="w-5 h-5 text-success" /></div>
              <div><p className="text-xs text-muted-foreground">Spot Configs</p><p className="text-xl font-bold">{spotModes.length}</p></div>
            </Card>
            <Card className="p-4 border-border bg-card flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center"><Zap className="w-5 h-5 text-primary" /></div>
              <div><p className="text-xs text-muted-foreground">Futures Configs</p><p className="text-xl font-bold">{futuresModes.length}</p></div>
            </Card>
            <Card className="p-4 border-border bg-card flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center"><Activity className="w-5 h-5 text-accent" /></div>
              <div><p className="text-xs text-muted-foreground">Active Modes</p><p className="text-xl font-bold">{activeCount}</p></div>
            </Card>
            <Card className="p-4 border-border bg-card flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-destructive/20 flex items-center justify-center"><Shield className="w-5 h-5 text-destructive" /></div>
              <div><p className="text-xs text-muted-foreground">Max Leverage</p><p className="text-xl font-bold">{Math.max(...manualLeverages.map(l => l.leverage), 1)}x</p></div>
            </Card>
          </div>

          <Tabs defaultValue="config" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="config">Configurations</TabsTrigger>
              <TabsTrigger value="leverage">Manual Leverage</TabsTrigger>
            </TabsList>

            <TabsContent value="config" className="space-y-8">
              {/* Spot Section */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold flex items-center gap-2"><TrendingUp className="text-success" /> Spot Trading</h3>
                  <Button onClick={() => addNewMode("spot")} variant="outline" size="sm"><Plus className="w-4 h-4 mr-1" /> Add Spot</Button>
                </div>
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                  {spotModes.map(mode => (
                    <Card key={mode.id} className={`p-4 border-border ${mode.enabled ? 'bg-success/5 border-success/30' : 'bg-card'}`}>
                      {/* Header */}
                      <div className="flex justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <Switch checked={mode.enabled} onCheckedChange={() => handleModeToggle(mode.id)} />
                          <Input value={mode.name} onChange={(e) => handleUpdateMode(mode.id, { name: e.target.value })} className="font-semibold bg-transparent border-none p-0 h-auto" />
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => removeMode(mode.id)}><AlertTriangle className="w-4 h-4 text-destructive" /></Button>
                      </div>
                      {/* Broker Type */}
                      <div className="mb-4 space-y-2">
                        <Label className="text-xs">Broker Configuration</Label>
                        <Select value={mode.brokerType} onValueChange={(v) => handleUpdateMode(mode.id, { brokerType: v as any, brokerConnected: false })}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="crypto_exchange">Crypto Exchange</SelectItem>
                            <SelectItem value="metatrader">MetaTrader</SelectItem>
                            <SelectItem value="fix">FIX Protocol</SelectItem>
                            <SelectItem value="dex">DEX (Wallet Connect)</SelectItem>
                            <SelectItem value="none">None</SelectItem>
                          </SelectContent>
                        </Select>
                        {/* Inline Broker Configs - Simplification for single file logic */}
                        <BrokerConfigPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                      </div>
                      {/* Risk Settings */}
                      <RiskSettingsPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                      {/* Entry Time Settings */}
                      <TimeSettingsPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                      {/* Multi-Timeframe Confirmation */}
                      <MultiTfConfirmationPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                    </Card>
                  ))}
                </div>
              </div>

              {/* Futures Section */}
              <div className="space-y-4 pt-4 border-t border-border">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold flex items-center gap-2"><Zap className="text-primary" /> Futures Trading</h3>
                  <Button onClick={() => addNewMode("futures")} variant="outline" size="sm"><Plus className="w-4 h-4 mr-1" /> Add Futures</Button>
                </div>
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                  {futuresModes.map(mode => (
                    <Card key={mode.id} className={`p-4 border-border ${mode.enabled ? 'bg-primary/5 border-primary/30' : 'bg-card'}`}>
                      <div className="flex justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <Switch checked={mode.enabled} onCheckedChange={() => handleModeToggle(mode.id)} />
                          <Input value={mode.name} onChange={(e) => handleUpdateMode(mode.id, { name: e.target.value })} className="font-semibold bg-transparent border-none p-0 h-auto" />
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => removeMode(mode.id)}><AlertTriangle className="w-4 h-4 text-destructive" /></Button>
                      </div>

                      {/* Broker Type Selection for Futures */}
                      <div className="mb-4 space-y-2">
                        <Label className="text-xs">Broker Configuration</Label>
                        <Select value={mode.brokerType} onValueChange={(v) => {
                          const isDex = v === "dex";
                          handleUpdateMode(mode.id, {
                            brokerType: v as any,
                            brokerConnected: false,
                            dexChain: isDex ? "solana" : mode.dexChain,
                            dexExchange: isDex ? "drift" : mode.dexExchange
                          });
                        }}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="crypto_exchange">Crypto Exchange</SelectItem>
                            <SelectItem value="fix">FIX Protocol</SelectItem>
                            <SelectItem value="dex">Perp DEX (Hyperliquid/Drift/GMX)</SelectItem>
                            <SelectItem value="none">None</SelectItem>
                          </SelectContent>
                        </Select>
                        <BrokerConfigPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                      </div>

                      <div className="mb-4 grid grid-cols-2 gap-2">
                        <div className="col-span-2">
                          <Label className="text-xs">Instrument</Label>
                          <select className="w-full bg-input border rounded px-2 py-1 text-sm" value={mode.selectedInstrument} onChange={(e) => handleInstrumentChange(mode.id, e.target.value)}>
                            <option value="">Select...</option>
                            {manualLeverages.map(l => <option key={l.instrument} value={l.instrument}>{l.instrument} ({l.leverage}x)</option>)}
                          </select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Leverage</Label>
                          <NumericInput value={mode.leverage} onChange={(v) => handleUpdateMode(mode.id, { leverage: v })} />
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between items-center">
                            <Label className="text-xs">Lot Size</Label>
                            <div className="flex items-center gap-1">
                              <Switch
                                checked={mode.autoLotSize}
                                onCheckedChange={(v) => handleUpdateMode(mode.id, { autoLotSize: v })}
                                className="scale-75 origin-right"
                              />
                              <span className="text-[9px] font-bold uppercase text-accent">Auto</span>
                            </div>
                          </div>
                          <div className="relative">
                            <NumericInput
                              value={mode.openLotSize}
                              onChange={(v) => handleUpdateMode(mode.id, { openLotSize: v })}
                              className={`h-8 ${mode.autoLotSize ? "bg-secondary/20 opacity-50 cursor-not-allowed" : ""}`}
                              placeholder={mode.autoLotSize ? "AUTO" : "0.1"}
                            />
                            {mode.autoLotSize && (
                              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                <span className="text-[8px] font-bold text-accent animate-pulse uppercase">AI Sizing Active</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="p-3 bg-secondary/30 rounded space-y-2">
                        <Label className="text-xs">Broker (Futures)</Label>
                        <Select value={mode.brokerType} onValueChange={(v) => handleUpdateMode(mode.id, { brokerType: v as any })}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="crypto_exchange">Crypto Exchange</SelectItem>
                            <SelectItem value="metatrader">MetaTrader</SelectItem>
                            <SelectItem value="fix">FIX Protocol</SelectItem>
                          </SelectContent>
                        </Select>
                        <BrokerConfigPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                      </div>
                      <RiskSettingsPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                      <TimeSettingsPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                      <MultiTfConfirmationPanel mode={mode} onUpdate={(u) => handleUpdateMode(mode.id, u)} />
                    </Card>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="leverage" className="space-y-4">
              {/* Manual Leverage Card */}
              <Card className="p-4 border-border bg-card">
                <h3 className="text-lg font-semibold mb-4">Manual Leverage Config</h3>
                <div className="flex gap-2 items-end">
                  <div className="flex-1"><Label>Instrument</Label><Input value={newLeverageInput.instrument} onChange={(e) => setNewLeverageInput(p => ({ ...p, instrument: e.target.value }))} placeholder="BTC/USDT" /></div>
                  <div className="w-24"><Label>Lev</Label><Input type="number" value={newLeverageInput.leverage} onChange={(e) => setNewLeverageInput(p => ({ ...p, leverage: +e.target.value }))} /></div>
                  <Button onClick={addManualLeverage}>Add</Button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-4">
                  {manualLeverages.map(l => (
                    <div key={l.instrument} className="p-2 border rounded flex justify-between items-center bg-secondary/20">
                      <span className="font-bold">{l.instrument}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-primary/20 px-1 rounded">{l.leverage}x</span>
                        <Trash2 className="w-3 h-3 cursor-pointer text-destructive" onClick={() => removeManualLeverage(l.instrument)} />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </TabsContent>
          </Tabs>
        </TabsContent>

        <TabsContent value="strategies">
          <Card className="p-6 border-border bg-card">
            <h2 className="text-xl font-semibold mb-4">Strategy Weights</h2>
            <Tabs value={activeTf} onValueChange={setActiveTf}>
              <TabsList className="flex flex-wrap h-auto p-2 mb-4">
                {timeframes.map(tf => <TabsTrigger key={tf.value} value={tf.value} className="text-xs px-2 py-1">{tf.label}</TabsTrigger>)}
              </TabsList>
              {timeframes.map(tf => (
                <TabsContent key={tf.value} value={tf.value} className="space-y-4">
                  {tfWeights[tf.value]?.map((s, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-sm"><Label>{s.name}</Label><span>{s.weight.toFixed(2)}</span></div>
                      <Input type="range" min="0" max="1" step="0.05" value={s.weight} onChange={(e) => handleWeightChange(tf.value, idx, parseFloat(e.target.value))} />
                    </div>
                  ))}
                  <div className="text-right text-sm font-bold pt-2 border-t">Total: {tfWeights[tf.value]?.reduce((a, b) => a + b.weight, 0).toFixed(2)}</div>
                </TabsContent>
              ))}
            </Tabs>
          </Card>
        </TabsContent>

        <TabsContent value="instruments">
          <div className="grid gap-6">
            <Card className="p-6 border-border bg-card">
              <h2 className="text-xl font-semibold mb-4">Add Custom Instrument</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div className="md:col-span-1 space-y-1"><Label>Symbol</Label><Input value={newInstrument.symbol} onChange={(e) => setNewInstrument(p => ({ ...p, symbol: e.target.value }))} placeholder="BTCUSDT" /></div>
                <div className="md:col-span-2 space-y-1"><Label>Name</Label><Input value={newInstrument.name} onChange={(e) => setNewInstrument(p => ({ ...p, name: e.target.value }))} placeholder="Bitcoin" /></div>
                <Button onClick={addCustomInstrument}><Plus className="w-4 h-4 mr-2" /> Add</Button>
              </div>
            </Card>
            <Card className="p-6 border-border bg-card">
              <h2 className="text-xl font-semibold mb-4">Trading Instruments</h2>
              <div className="relative mb-4"><Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" /><Input className="pl-9" value={instrumentSearch} onChange={(e) => setInstrumentSearch(e.target.value)} placeholder="Search..." /></div>
              <Tabs value={activeInstrumentTab} onValueChange={(v) => setActiveInstrumentTab(v as any)}>
                <TabsList>{Object.keys(instruments).map(k => <TabsTrigger key={k} value={k} className="capitalize">{k}</TabsTrigger>)}</TabsList>
                {Object.keys(instruments).map(k => (
                  <TabsContent key={k} value={k}>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {instruments[k as InstrumentCategory].filter(i => i.symbol.includes(instrumentSearch.toUpperCase())).map(i => (
                        <div key={i.symbol} className="flex justify-between items-center p-3 border rounded">
                          <div className="flex items-center gap-2"><Switch checked={i.enabled} onCheckedChange={() => toggleInstrument(k as any, i.symbol)} /> <span>{i.symbol}</span></div>
                          <Trash2 className="w-4 h-4 text-muted-foreground cursor-pointer" onClick={() => removeInstrument(k as any, i.symbol)} />
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ai-engineering" className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
              <Cpu className="w-5 h-5 text-primary" />
              AI Feature Engineering
            </h2>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => toast.success("Feature config saved")}>
                <Save className="w-4 h-4 mr-1" />
                Save Config
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Technical Indicators */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Activity className="w-4 h-4 text-warning" />
                  Technical Indicators
                </h3>
                <Switch
                  checked={featureConfig.technical.enabled}
                  onCheckedChange={(v) => updateFeatureConfig("technical", { enabled: v })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3 opacity-90">
                {["rsi", "macd", "bollinger_bands", "stochastic", "adx", "cci", "williams_r", "atr", "obv", "mfi"].map(feature => (
                  <div key={feature} className="flex items-center space-x-2">
                    <Checkbox
                      id={`tech-${feature}`}
                      checked={featureConfig.technical.features.includes(feature)}
                      onCheckedChange={() => toggleFeature("technical", feature)}
                      disabled={!featureConfig.technical.enabled}
                    />
                    <Label htmlFor={`tech-${feature}`} className="uppercase text-xs">{feature.replace(/_/g, " ")}</Label>
                  </div>
                ))}
              </div>
            </Card>

            {/* Gann Features */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Target className="w-4 h-4 text-accent" />
                  Gann Features
                </h3>
                <Switch
                  checked={featureConfig.gann.enabled}
                  onCheckedChange={(v) => updateFeatureConfig("gann", { enabled: v })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3 opacity-90">
                {["square_of_9", "square_of_24", "square_of_52", "square_of_90", "square_of_144", "gann_fan", "time_cycles", "vibration", "natural_vibration"].map(feature => (
                  <div key={feature} className="flex items-center space-x-2">
                    <Checkbox
                      id={`gann-${feature}`}
                      checked={featureConfig.gann.features.includes(feature)}
                      onCheckedChange={() => toggleFeature("gann", feature)}
                      disabled={!featureConfig.gann.enabled}
                    />
                    <Label htmlFor={`gann-${feature}`} className="text-xs capitalize">{feature.replace(/_/g, " ")}</Label>
                  </div>
                ))}
              </div>
            </Card>

            {/* Ehlers Features */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-success" />
                  Ehlers Features
                </h3>
                <Switch
                  checked={featureConfig.ehlers.enabled}
                  onCheckedChange={(v) => updateFeatureConfig("ehlers", { enabled: v })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3 opacity-90">
                {["mama_fama", "fisher_transform", "cyber_cycle", "super_smoother", "roofing_filter", "decycler", "sinewave_indicator", "instantaneous_trendline", "bandpass_filter", "smoothed_rsi"].map(feature => (
                  <div key={feature} className="flex items-center space-x-2">
                    <Checkbox
                      id={`ehlers-${feature}`}
                      checked={featureConfig.ehlers.features.includes(feature)}
                      onCheckedChange={() => toggleFeature("ehlers", feature)}
                      disabled={!featureConfig.ehlers.enabled}
                    />
                    <Label htmlFor={`ehlers-${feature}`} className="text-xs capitalize">{feature.replace(/_/g, " ")}</Label>
                  </div>
                ))}
              </div>
            </Card>

            {/* Astro Features */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Zap className="w-4 h-4 text-primary" />
                  Astro Features
                </h3>
                <Switch
                  checked={featureConfig.astro.enabled}
                  onCheckedChange={(v) => updateFeatureConfig("astro", { enabled: v })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3 opacity-90">
                {["major_aspects_score", "retrograde_status", "lunar_phase", "planetary_strength", "bradley_value", "declination", "eclipses"].map(feature => (
                  <div key={feature} className="flex items-center space-x-2">
                    <Checkbox
                      id={`astro-${feature}`}
                      checked={featureConfig.astro.features.includes(feature)}
                      onCheckedChange={() => toggleFeature("astro", feature)}
                      disabled={!featureConfig.astro.enabled}
                    />
                    <Label htmlFor={`astro-${feature}`} className="text-xs capitalize">{feature.replace(/_/g, " ")}</Label>
                  </div>
                ))}
              </div>
            </Card>

            {/* Market Microstructure */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Activity className="w-4 h-4 text-secondary-foreground" />
                  Market Microstructure
                </h3>
                <Switch
                  checked={featureConfig.microstructure.enabled}
                  onCheckedChange={(v) => updateFeatureConfig("microstructure", { enabled: v })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3 opacity-90">
                {["bid_ask_spread", "volume_profile", "order_flow_imbalance", "tape_reading_features", "large_order_detection"].map(feature => (
                  <div key={feature} className="flex items-center space-x-2">
                    <Checkbox
                      id={`micro-${feature}`}
                      checked={featureConfig.microstructure.features.includes(feature)}
                      onCheckedChange={() => toggleFeature("microstructure", feature)}
                      disabled={!featureConfig.microstructure.enabled}
                    />
                    <Label htmlFor={`micro-${feature}`} className="text-xs capitalize">{feature.replace(/_/g, " ")}</Label>
                  </div>
                ))}
              </div>
            </Card>

            {/* Time Features */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" />
                  Time Features
                </h3>
                <Switch
                  checked={featureConfig.time.enabled}
                  onCheckedChange={(v) => updateFeatureConfig("time", { enabled: v })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3 opacity-90">
                {["hour_of_day", "day_of_week", "day_of_month", "month_of_year", "is_month_end", "session_type"].map(feature => (
                  <div key={feature} className="flex items-center space-x-2">
                    <Checkbox
                      id={`time-${feature}`}
                      checked={featureConfig.time.features.includes(feature)}
                      onCheckedChange={() => toggleFeature("time", feature)}
                      disabled={!featureConfig.time.enabled}
                    />
                    <Label htmlFor={`time-${feature}`} className="text-xs capitalize">{feature.replace(/_/g, " ")}</Label>
                  </div>
                ))}
              </div>
            </Card>

            {/* Transformations */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Layers className="w-4 h-4 text-secondary-foreground" />
                  Transformations
                </h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Lag Features</Label>
                  <Switch
                    checked={featureConfig.transformations.lags}
                    onCheckedChange={(v) => updateFeatureConfig("transformations", { lags: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Rolling Statistics</Label>
                  <Switch
                    checked={featureConfig.transformations.rolling}
                    onCheckedChange={(v) => updateFeatureConfig("transformations", { rolling: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Differencing</Label>
                  <Switch
                    checked={featureConfig.transformations.differences}
                    onCheckedChange={(v) => updateFeatureConfig("transformations", { differences: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Ratio Features</Label>
                  <Switch
                    checked={featureConfig.transformations.ratios}
                    onCheckedChange={(v) => updateFeatureConfig("transformations", { ratios: v })}
                  />
                </div>
              </div>
            </Card>

            {/* Feature Selection */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Target className="w-4 h-4 text-secondary-foreground" />
                  Feature Selection
                </h3>
                <Switch
                  checked={featureConfig.selection.enabled}
                  onCheckedChange={(v) => updateFeatureConfig("selection", { enabled: v })}
                />
              </div>
              <div className="space-y-4">
                <div>
                  <Label className="text-xs text-muted-foreground">Selection Method</Label>
                  <Select
                    value={featureConfig.selection.method}
                    onValueChange={(v) => updateFeatureConfig("selection", { method: v })}
                    disabled={!featureConfig.selection.enabled}
                  >
                    <SelectTrigger className="bg-secondary border-border mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="correlation">Correlation Threshold</SelectItem>
                      <SelectItem value="mutual_information">Mutual Information</SelectItem>
                      <SelectItem value="recursive_elimination">RFE (Recursive)</SelectItem>
                      <SelectItem value="importance">Model Importance</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground">Top K Features: {featureConfig.selection.topK}</Label>
                  <Slider
                    value={[featureConfig.selection.topK]}
                    min={10}
                    max={200}
                    step={10}
                    onValueChange={([v]) => updateFeatureConfig("selection", { topK: v })}
                    className="mt-2"
                    disabled={!featureConfig.selection.enabled}
                  />
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground">Correlation Threshold: {featureConfig.selection.correlationThreshold}</Label>
                  <Slider
                    value={[featureConfig.selection.correlationThreshold]}
                    min={0.5}
                    max={0.99}
                    step={0.01}
                    onValueChange={([v]) => updateFeatureConfig("selection", { correlationThreshold: v })}
                    className="mt-2"
                    disabled={!featureConfig.selection.enabled}
                  />
                </div>
              </div>
            </Card>

            <div className="col-span-full flex justify-end mt-4">
              <Button onClick={handleSaveAllSettings} className="bg-primary hover:bg-primary/90">
                <Save className="w-4 h-4 mr-2" />
                Save AI Configuration
              </Button>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="system">
          <AlertAPISettings />

          {/* Timezone Configuration */}
          <Card className="p-6 border-border bg-card mt-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  Global Timezone Configuration
                </h2>
                <p className="text-sm text-muted-foreground">Synchronize analysis with your local time and global trading hubs</p>
              </div>
              <div className="flex items-center gap-2 bg-secondary/50 p-2 rounded-lg border">
                <Switch checked={autoDetectTimezone} onCheckedChange={setAutoDetectTimezone} />
                <Label className="text-xs font-bold">Auto-detect Local</Label>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label className="text-xs uppercase font-bold text-muted-foreground">Primary Local Timezone</Label>
                <Select disabled={autoDetectTimezone} value={autoDetectTimezone ? Intl.DateTimeFormat().resolvedOptions().timeZone : undefined} defaultValue="UTC">
                  <SelectTrigger className="bg-secondary/20">
                    <SelectValue placeholder={autoDetectTimezone ? Intl.DateTimeFormat().resolvedOptions().timeZone : "Select Timezone"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="UTC">UTC (GMT+0)</SelectItem>
                    <SelectItem value="America/New_York">New York (GMT-5)</SelectItem>
                    <SelectItem value="Europe/London">London (GMT+0)</SelectItem>
                    <SelectItem value="Asia/Jakarta">Jakarta (GMT+7)</SelectItem>
                    <SelectItem value="Asia/Singapore">Singapore (GMT+8)</SelectItem>
                    <SelectItem value="Asia/Tokyo">Tokyo (GMT+9)</SelectItem>
                    {/* Add more as needed, or use the WORLD_EXCHANGES values */}
                  </SelectContent>
                </Select>
                {autoDetectTimezone && (
                  <p className="text-[10px] text-primary flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> System detected: {Intl.DateTimeFormat().resolvedOptions().timeZone}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label className="text-xs uppercase font-bold text-muted-foreground">Active Market Session Hub</Label>
                <Select defaultValue="America/New_York">
                  <SelectTrigger className="bg-secondary/20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    {WORLD_EXCHANGES.map(ex => (
                      <SelectItem key={ex.value} value={ex.value}>{ex.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-full p-4 bg-gradient-to-r from-secondary/40 to-transparent rounded-lg border border-border/50">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-0.5">
                    <p className="text-[9px] text-muted-foreground uppercase font-bold">Your Local Time</p>
                    <p className="text-sm font-mono font-bold text-primary">{new Date().toLocaleTimeString()}</p>
                  </div>
                  <div className="space-y-0.5 border-l pl-4">
                    <p className="text-[9px] text-muted-foreground uppercase font-bold">Universal (UTC)</p>
                    <p className="text-sm font-mono font-bold">{new Date().toUTCString().split(' ')[4]}</p>
                  </div>
                  <div className="space-y-0.5 border-l pl-4">
                    <p className="text-[9px] text-muted-foreground uppercase font-bold">Unix Epoch</p>
                    <p className="text-sm font-mono font-bold text-muted-foreground">{Math.floor(Date.now() / 1000)}</p>
                  </div>
                  <div className="space-y-0.5 border-l pl-4">
                    <p className="text-[9px] text-muted-foreground uppercase font-bold">Sidereal Time</p>
                    <p className="text-sm font-mono font-bold text-accent">LST CALC..</p>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* WD Gann Astrology Configuration - RECREATED & ADVANCED */}
          <Card className="p-6 border-border bg-card mt-6 border-l-4 border-l-accent shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-accent animate-pulse" />
                  Gann Master Astro-Vibration Engine
                </h2>
                <p className="text-sm text-muted-foreground">Configure esoteric time cycles and planetary vibrations based on WD Gann's Tunnel Thru The Air</p>
              </div>
              <Badge variant="outline" className="border-accent text-accent animate-pulse">ADVANCED MODE ACTIVE</Badge>
            </div>

            <Tabs defaultValue="planetary" className="w-full">
              <TabsList className="grid w-full grid-cols-5 mb-6 bg-secondary/20 p-1">
                <TabsTrigger value="charts" className="text-xs">Market Horoscopes</TabsTrigger>
                <TabsTrigger value="planetary" className="text-xs">Planetary Vibrations</TabsTrigger>
                <TabsTrigger value="aspects" className="text-xs">Master Aspects</TabsTrigger>
                <TabsTrigger value="cycles" className="text-xs">Time Cycles</TabsTrigger>
                <TabsTrigger value="geometry" className="text-xs">Geometry & Squaring</TabsTrigger>
              </TabsList>

              {/* Market Horoscopes (Birth Charts) */}
              <TabsContent value="charts" className="space-y-4">
                <div className="flex justify-between items-center mb-2 px-1">
                  <div className="flex items-center gap-4 bg-secondary/20 p-2 rounded-lg border">
                    <div className="flex items-center gap-2">
                      <Switch id="auto-dash" checked={syncWithDashboard} onCheckedChange={setSyncWithDashboard} />
                      <Label htmlFor="auto-dash" className="text-[10px] uppercase font-bold text-accent cursor-pointer">Sync Dashboard</Label>
                    </div>
                    <div className="flex items-center gap-2 border-l pl-4">
                      <Switch id="auto-birth" checked={marketBirthAuto} onCheckedChange={setMarketBirthAuto} />
                      <Label htmlFor="auto-birth" className="text-[10px] uppercase font-bold text-muted-foreground cursor-pointer">Auto-Calibrate</Label>
                    </div>
                  </div>
                  <Button size="sm" className="h-8 bg-accent text-accent-foreground font-bold text-xs" onClick={() => setActiveEpochs([...activeEpochs, "custom"])}>
                    <Plus className="w-3.5 h-3.5 mr-1" /> ADD ANALYSIS
                  </Button>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                  {activeEpochs.map((epochId, idx) => {
                    const epoch = MARKET_EPOCHS[epochId] || { name: "Custom Chart", date: "2024-01-01", time: "00:00", lat: 0, lon: 0 };
                    return (
                      <div key={`${epochId}-${idx}`} className="space-y-4 border p-4 rounded-lg bg-secondary/5 relative overflow-hidden">
                        <div className="flex justify-between items-center border-b pb-2 mb-2">
                          <h3 className="text-sm font-bold flex items-center gap-2">
                            <Target className="w-4 h-4 text-primary" />
                            {epochId === "custom" ? "Manual Calibration" : epoch.name}
                          </h3>
                          <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground hover:text-red-500" onClick={() => setActiveEpochs(activeEpochs.filter((_, i) => i !== idx))}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1">
                            <Label className="text-[10px] uppercase text-muted-foreground">Epoch Source</Label>
                            <Select value={epochId} onValueChange={(val) => {
                              const news = [...activeEpochs];
                              news[idx] = val;
                              setActiveEpochs(news);
                            }}>
                              <SelectTrigger className="h-8 text-[11px] border-accent/20">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="max-h-[300px]">
                                {Object.entries(MARKET_EPOCHS).map(([k, v]) => (
                                  <SelectItem key={k} value={k}>{v.name}</SelectItem>
                                ))}
                                <SelectItem value="custom">Manual Coordinates..</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[10px] uppercase text-muted-foreground">Coordinate System</Label>
                            <Select defaultValue="geo">
                              <SelectTrigger className="h-8 text-[11px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="geo">Geocentric</SelectItem>
                                <SelectItem value="helio">Heliocentric</SelectItem>
                                <SelectItem value="topo">Topocentric</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="col-span-full space-y-1">
                            <Label className="text-[10px] uppercase text-muted-foreground">Market Inception (UTC)</Label>
                            <div className="flex gap-2">
                              <Input type="date" className="h-8 text-xs flex-1" disabled={marketBirthAuto && epochId !== "custom"} value={marketBirthAuto && epochId !== "custom" ? epoch.date : undefined} />
                              <Input type="time" className="h-8 text-xs w-32" disabled={marketBirthAuto && epochId !== "custom"} value={marketBirthAuto && epochId !== "custom" ? epoch.time : undefined} />
                            </div>
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[10px] uppercase text-muted-foreground">Latitude</Label>
                            <Input type="number" className="h-8 text-xs" disabled={marketBirthAuto && epochId !== "custom"} value={marketBirthAuto && epochId !== "custom" ? epoch.lat : undefined} />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[10px] uppercase text-muted-foreground">Longitude</Label>
                            <Input type="number" className="h-8 text-xs" disabled={marketBirthAuto && epochId !== "custom"} value={marketBirthAuto && epochId !== "custom" ? epoch.lon : undefined} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </TabsContent>

              {/* Planetary Vibrations */}
              <TabsContent value="planetary" className="space-y-4">
                <div className="flex justify-between items-center mb-2 px-1">
                  <div className="flex items-center gap-2 bg-secondary/20 p-2 rounded-lg border">
                    <Switch id="auto-vibrate" checked={autoPlanetaryVibration} onCheckedChange={setAutoPlanetaryVibration} />
                    <Label htmlFor="auto-vibrate" className="text-[10px] uppercase font-bold text-accent cursor-pointer flex items-center gap-1">
                      <Zap className="w-3 h-3" /> Auto-Vibrate Engine
                    </Label>
                  </div>
                  <Badge variant="outline" className="text-[10px] border-primary/30">Dynamic Scaling Active</Badge>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { node: "Sun", icon: "☀️", color: "text-yellow-500", key: "sun", cycle: "365.25d" },
                    { node: "Moon", icon: "🌙", color: "text-slate-400", key: "moon", cycle: "27.3d" },
                    { node: "Mercury", icon: "☿", color: "text-cyan-400", key: "merc", cycle: "88d" },
                    { node: "Venus", icon: "♀", color: "text-pink-400", key: "venus", cycle: "225d" },
                    { node: "Mars", icon: "♂", color: "text-red-500", key: "mars", cycle: "687d" },
                    { node: "Jupiter", icon: "♃", color: "text-orange-400", key: "jup", cycle: "11.8y" },
                    { node: "Saturn", icon: "♄", color: "text-amber-600", key: "sat", cycle: "29.4y" },
                    { node: "Uranus", icon: "♅", color: "text-blue-400", key: "ura", cycle: "84y" },
                  ].map((p) => (
                    <div key={p.key} className="p-3 border rounded-lg bg-secondary/10 flex flex-col gap-2 relative group hover:border-accent/50 transition-colors">
                      <div className="flex justify-between items-center">
                        <span className={`text-xl ${p.color}`}>{p.icon}</span>
                        <Switch checked={true} />
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] font-bold uppercase truncate">{p.node}</p>
                        <p className="text-[9px] text-muted-foreground">Orbit: {p.cycle}</p>
                      </div>
                      <Input
                        type="number"
                        step="0.01"
                        className="h-6 text-[10px] bg-background/50"
                        value={planetaryFactors[p.key]}
                        onChange={(e) => setPlanetaryFactors(prev => ({ ...prev, [p.key]: parseFloat(e.target.value) }))}
                        disabled={autoPlanetaryVibration}
                      />
                      <Label className="text-[8px] text-center text-muted-foreground">
                        {autoPlanetaryVibration ? "Auto-Optimized Factor" : "Manual Vibration Factor"}
                      </Label>
                      {autoPlanetaryVibration && (
                        <div className="absolute inset-0 bg-accent/5 pointer-events-none flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <Activity className="w-4 h-4 text-accent animate-pulse" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="bg-accent/5 p-3 rounded-lg border border-accent/20 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-accent">Planetary Price Conversion</p>
                    <p className="text-[10px] text-muted-foreground">Convert planetary longitude degrees into price targets (Wheel of 24)</p>
                  </div>
                  <Select defaultValue="24">
                    <SelectTrigger className="w-24 h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="24">Wheel of 24</SelectItem>
                      <SelectItem value="360">Circle of 360</SelectItem>
                      <SelectItem value="gann">Gann 9x9</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              {/* Master Aspects */}
              <TabsContent value="aspects" className="space-y-4">
                <div className="grid grid-cols-1 gap-6">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center bg-secondary/10 p-2 rounded-t-lg border-x border-t">
                      <Label className="text-xs font-bold uppercase text-accent flex items-center gap-2">
                        <Activity className="w-3.5 h-3.5" />
                        Gann Harmonic Master Aspects (15° Increments)
                      </Label>
                      <Badge variant="outline" className="border-accent text-accent">360° COVERAGE</Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 p-4 border rounded-b-lg bg-card">
                      {Array.from({ length: 24 }, (_, i) => (i + 1) * 15).map(deg => {
                        const isHard = deg % 90 === 0 || deg === 360;
                        const isMain = deg % 45 === 0;
                        const label = deg === 0 || deg === 360 ? "Conjunction" :
                          deg === 180 ? "Opposition" :
                            deg === 90 ? "Square" :
                              deg === 270 ? "Square" :
                                deg === 120 ? "Trine" :
                                  deg === 60 ? "Sextile" :
                                    deg === 45 ? "Semi-Square" :
                                      deg === 135 ? "Sesquiquadrate" : `Aspect ${deg}°`;

                        return (
                          <div key={deg} className={`flex flex-col gap-1.5 p-2 border rounded transition-all hover:border-accent/40 ${isHard ? 'bg-accent/5 border-accent/20' : isMain ? 'bg-primary/5 border-primary/20' : 'bg-secondary/5 border-border'}`}>
                            <div className="flex justify-between items-start">
                              <span className={`text-[10px] font-bold ${isHard ? 'text-accent' : isMain ? 'text-primary' : 'text-muted-foreground'}`}>{deg}°</span>
                              <Switch defaultChecked={isMain || deg % 30 === 0} />
                            </div>
                            <div className="space-y-0.5">
                              <p className="text-[9px] font-black leading-tight truncate uppercase">{label}</p>
                              <div className="flex justify-between items-center text-[8px] text-muted-foreground">
                                <span>Orb: ±{isHard ? 8 : isMain ? 5 : 2}°</span>
                                <span className="font-bold">W: {isHard ? 1.0 : isMain ? 0.7 : 0.3}</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="p-4 border rounded-lg bg-accent/5 border-accent/20">
                    <h4 className="text-xs font-bold flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-accent" />
                      Master Cycle Integration
                    </h4>
                    <p className="text-[10px] text-muted-foreground">
                      Enable all 15° harmonic vibrations for deep fractal analysis. In Gann theory, these increments correspond to the 24 hours of the day and the 24 divisions of the circle, creating a perfect synchronization between time and price geometry.
                    </p>
                  </div>
                </div>
              </TabsContent>

              {/* Time Cycles */}
              <TabsContent value="cycles" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <Label className="text-xs font-bold uppercase text-accent">Gann Major Cycles</Label>
                    {[
                      { name: "Law of Vibration (144)", dur: "144 Days", id: "v144" },
                      { name: "Master Year (365)", dur: "1 Year", id: "my" },
                      { name: "Great Cycle (60y)", dur: "60 Years", id: "gc60" },
                      { name: "Square of 90 (90d)", dur: "90 Days", id: "sq90" },
                    ].map(c => (
                      <div key={c.id} className="flex items-center justify-between p-2 border rounded-md bg-secondary/5">
                        <div className="flex items-center gap-3">
                          <Switch defaultChecked />
                          <div className="flex flex-col">
                            <span className="text-xs font-bold">{c.name}</span>
                            <span className="text-[9px] text-muted-foreground">{c.dur}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-3">
                    <Label className="text-xs font-bold uppercase text-accent">Astronomical Cycles</Label>
                    <div className="space-y-2">
                      <div className="p-3 border rounded-lg bg-secondary/5 space-y-3">
                        <div className="flex justify-between items-center">
                          <Label className="text-xs">Lunar Synodic Cycle (29.5d)</Label>
                          <Switch defaultChecked />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex items-center gap-2">
                            <Checkbox id="nm" defaultChecked />
                            <Label htmlFor="nm" className="text-[10px]">New Moon</Label>
                          </div>
                          <div className="flex items-center gap-2">
                            <Checkbox id="fm" defaultChecked />
                            <Label htmlFor="fm" className="text-[10px]">Full Moon</Label>
                          </div>
                        </div>
                      </div>
                      <div className="p-3 border rounded-lg bg-secondary/5 space-y-2">
                        <div className="flex justify-between items-center">
                          <Label className="text-xs">Solstice/Equinox Points</Label>
                          <Switch defaultChecked />
                        </div>
                        <p className="text-[9px] text-muted-foreground italic">Cardinal points (0° Ari, Can, Lib, Cap)</p>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* Geometry & Squaring */}
              <TabsContent value="geometry" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label className="text-xs font-bold uppercase flex items-center gap-2">
                        <Waves className="w-3 h-3 text-accent" />
                        Price-Time Squaring
                      </Label>
                      <div className="p-4 border rounded-lg bg-red-500/5 border-red-500/20 space-y-4">
                        <div className="flex items-center justify-between">
                          <Label className="text-xs">Auto-Square Calculation</Label>
                          <Switch defaultChecked />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-[10px]">Squaring Algorithm</Label>
                          <Select defaultValue="sq9">
                            <SelectTrigger className="h-8 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="sq9">Square of 9 Matrix</SelectItem>
                              <SelectItem value="sq144">Master Square of 144</SelectItem>
                              <SelectItem value="sq52">Financial Year Square (52)</SelectItem>
                              <SelectItem value="hexagon">Hexagon Vibration</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="flex items-center gap-2">
                          <Checkbox id="vol_squaring" />
                          <Label htmlFor="vol_squaring" className="text-[10px]">Include Volume-Time Squaring</Label>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label className="text-xs font-bold uppercase flex items-center gap-2">
                        <Grid className="w-3 h-3 text-accent" />
                        Static Angles & Overlays
                      </Label>
                      <div className="grid grid-cols-1 gap-2">
                        {[
                          { name: "Gann Fan 1x1 (45°)", default: true },
                          { name: "Cardinal Cross (90°)", default: true },
                          { name: "Fixed Harmonics (5/8)", default: false },
                          { name: "Spiral of 360", default: true },
                        ].map(g => (
                          <div key={g.name} className="flex items-center justify-between p-2 border rounded bg-secondary/5">
                            <span className="text-xs">{g.name}</span>
                            <Switch defaultChecked={g.default} />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-accent/5 border border-accent/20 rounded-lg">
                  <div className="flex items-center gap-2 text-accent mb-1 font-bold">
                    <AlertTriangle className="w-3 h-3" />
                    <span className="text-[10px]">MASTER VIBRATION LOCK</span>
                  </div>
                  <p className="text-[9px] text-muted-foreground">Unlock for manual correction of price-coordinate synchronization across multiple planetary dimensions.</p>
                </div>
              </TabsContent>
            </Tabs>

            <div className="mt-8 pt-4 border-t flex justify-end gap-3">
              <Button variant="outline" size="sm" className="h-8 text-xs font-bold">RESET TO GANN DEFAULTS</Button>
              <Button size="sm" className="h-8 text-xs font-bold shadow-accent hover:shadow-accent/50 bg-accent hover:bg-accent/90 text-accent-foreground">SAVE ASTRO CONFIGURATION</Button>
            </div>
          </Card>


          <Card className="p-6 border-border bg-card mt-6">
            <h2 className="text-xl font-semibold mb-2">System Backup</h2>
            <p className="text-sm text-muted-foreground mb-4">Export all configuration including trading modes, weights, and instruments.</p>
            <div className="flex gap-4">
              <Button onClick={handleExportSettings}><Download className="w-4 h-4 mr-2" /> Full Export</Button>
              <Button variant="outline" onClick={() => fileInputRef.current?.click()}><Upload className="w-4 h-4 mr-2" /> Full Import</Button>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div >
  );
};

export default Settings;
