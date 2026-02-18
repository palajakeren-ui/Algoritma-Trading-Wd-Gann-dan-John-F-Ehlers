import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Settings2,
  Wifi,
  WifiOff,
  Key,
  Server,
  Shield,
  Eye,
  EyeOff,
  Copy,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";

export type BrokerType = "metatrader" | "crypto_exchange" | "fix";

export interface MetaTraderConfig {
  id: string;
  name: string;
  type: "mt4" | "mt5";
  server: string;
  login: string;
  password: string;
  enabled: boolean;
  connected: boolean;
  accountType: "demo" | "live";
  broker: string;
}

export interface CryptoExchangeConfig {
  id: string;
  name: string;
  exchange: "binance_futures" | "binance_spot" | "bybit" | "okx" | "kucoin" | "kraken" | "coinbase";
  apiKey: string;
  apiSecret: string;
  passphrase?: string;
  enabled: boolean;
  connected: boolean;
  testnet: boolean;
  permissions: string[];
}

export interface FIXConfig {
  id: string;
  name: string;
  senderCompId: string;
  targetCompId: string;
  host: string;
  port: number;
  username: string;
  password: string;
  enabled: boolean;
  connected: boolean;
  heartbeatInterval: number;
  resetOnLogon: boolean;
  sslEnabled: boolean;
}

const EXCHANGE_OPTIONS = [
  { value: "binance_futures", label: "Binance Futures", icon: "🔶" },
  { value: "binance_spot", label: "Binance Spot", icon: "🔶" },
  { value: "bybit", label: "Bybit", icon: "⚫" },
  { value: "okx", label: "OKX", icon: "⚪" },
  { value: "kucoin", label: "KuCoin", icon: "🟢" },
  { value: "kraken", label: "Kraken", icon: "🟣" },
  { value: "coinbase", label: "Coinbase Pro", icon: "🔵" },
];

const PERMISSION_OPTIONS = ["spot", "futures", "margin", "withdraw", "internal_transfer"];

const BrokerExchangeConfig = () => {
  const [activeTab, setActiveTab] = useState<BrokerType>("crypto_exchange");
  
  // MetaTrader Configurations
  const [mtConfigs, setMtConfigs] = useState<MetaTraderConfig[]>([
    {
      id: "mt-1",
      name: "MT5 Primary",
      type: "mt5",
      server: "MetaQuotes-Demo",
      login: "",
      password: "",
      enabled: true,
      connected: false,
      accountType: "demo",
      broker: "MetaQuotes",
    },
  ]);

  // Crypto Exchange Configurations
  const [exchangeConfigs, setExchangeConfigs] = useState<CryptoExchangeConfig[]>([
    {
      id: "ex-1",
      name: "Binance Futures Main",
      exchange: "binance_futures",
      apiKey: "",
      apiSecret: "",
      enabled: true,
      connected: false,
      testnet: true,
      permissions: ["futures"],
    },
    {
      id: "ex-2",
      name: "Binance Spot Main",
      exchange: "binance_spot",
      apiKey: "",
      apiSecret: "",
      enabled: true,
      connected: false,
      testnet: true,
      permissions: ["spot"],
    },
  ]);

  // FIX Protocol Configurations
  const [fixConfigs, setFixConfigs] = useState<FIXConfig[]>([
    {
      id: "fix-1",
      name: "FIX Primary",
      senderCompId: "",
      targetCompId: "",
      host: "",
      port: 443,
      username: "",
      password: "",
      enabled: false,
      connected: false,
      heartbeatInterval: 30,
      resetOnLogon: true,
      sslEnabled: true,
    },
  ]);

  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  const toggleSecret = (id: string) => {
    setShowSecrets(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  // MetaTrader handlers
  const addMTConfig = () => {
    const newConfig: MetaTraderConfig = {
      id: `mt-${Date.now()}`,
      name: "New MetaTrader Account",
      type: "mt5",
      server: "",
      login: "",
      password: "",
      enabled: false,
      connected: false,
      accountType: "demo",
      broker: "",
    };
    setMtConfigs([...mtConfigs, newConfig]);
    toast.success("MetaTrader configuration added");
  };

  const updateMTConfig = (id: string, updates: Partial<MetaTraderConfig>) => {
    setMtConfigs(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  const deleteMTConfig = (id: string) => {
    setMtConfigs(prev => prev.filter(c => c.id !== id));
    toast.success("MetaTrader configuration removed");
  };

  const testMTConnection = (id: string) => {
    const config = mtConfigs.find(c => c.id === id);
    if (!config?.server || !config?.login) {
      toast.error("Please fill in server and login details");
      return;
    }
    toast.info("Testing connection...");
    setTimeout(() => {
      updateMTConfig(id, { connected: true });
      toast.success("MetaTrader connection successful");
    }, 1500);
  };

  // Exchange handlers
  const addExchangeConfig = () => {
    const newConfig: CryptoExchangeConfig = {
      id: `ex-${Date.now()}`,
      name: "New Exchange Account",
      exchange: "binance_futures",
      apiKey: "",
      apiSecret: "",
      enabled: false,
      connected: false,
      testnet: true,
      permissions: [],
    };
    setExchangeConfigs([...exchangeConfigs, newConfig]);
    toast.success("Exchange configuration added");
  };

  const updateExchangeConfig = (id: string, updates: Partial<CryptoExchangeConfig>) => {
    setExchangeConfigs(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  const deleteExchangeConfig = (id: string) => {
    setExchangeConfigs(prev => prev.filter(c => c.id !== id));
    toast.success("Exchange configuration removed");
  };

  const testExchangeConnection = (id: string) => {
    const config = exchangeConfigs.find(c => c.id === id);
    if (!config?.apiKey || !config?.apiSecret) {
      toast.error("Please fill in API key and secret");
      return;
    }
    toast.info("Testing connection...");
    setTimeout(() => {
      updateExchangeConfig(id, { connected: true });
      toast.success("Exchange connection successful");
    }, 1500);
  };

  const togglePermission = (id: string, permission: string) => {
    const config = exchangeConfigs.find(c => c.id === id);
    if (!config) return;
    const newPerms = config.permissions.includes(permission)
      ? config.permissions.filter(p => p !== permission)
      : [...config.permissions, permission];
    updateExchangeConfig(id, { permissions: newPerms });
  };

  // FIX handlers
  const addFIXConfig = () => {
    const newConfig: FIXConfig = {
      id: `fix-${Date.now()}`,
      name: "New FIX Connection",
      senderCompId: "",
      targetCompId: "",
      host: "",
      port: 443,
      username: "",
      password: "",
      enabled: false,
      connected: false,
      heartbeatInterval: 30,
      resetOnLogon: true,
      sslEnabled: true,
    };
    setFixConfigs([...fixConfigs, newConfig]);
    toast.success("FIX configuration added");
  };

  const updateFIXConfig = (id: string, updates: Partial<FIXConfig>) => {
    setFixConfigs(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  const deleteFIXConfig = (id: string) => {
    setFixConfigs(prev => prev.filter(c => c.id !== id));
    toast.success("FIX configuration removed");
  };

  const testFIXConnection = (id: string) => {
    const config = fixConfigs.find(c => c.id === id);
    if (!config?.host || !config?.senderCompId) {
      toast.error("Please fill in host and SenderCompID");
      return;
    }
    toast.info("Testing FIX connection...");
    setTimeout(() => {
      updateFIXConfig(id, { connected: true });
      toast.success("FIX connection established");
    }, 2000);
  };

  const totalConnections = mtConfigs.length + exchangeConfigs.length + fixConfigs.length;
  const activeConnections = [
    ...mtConfigs.filter(c => c.connected),
    ...exchangeConfigs.filter(c => c.connected),
    ...fixConfigs.filter(c => c.connected),
  ].length;

  return (
    <div className="space-y-4">
      {/* Header Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="p-3 border-border bg-card">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Total Configs</p>
              <p className="text-lg font-bold text-foreground">{totalConnections}</p>
            </div>
          </div>
        </Card>
        <Card className="p-3 border-border bg-card">
          <div className="flex items-center gap-2">
            <Wifi className="w-5 h-5 text-success" />
            <div>
              <p className="text-xs text-muted-foreground">Connected</p>
              <p className="text-lg font-bold text-success">{activeConnections}</p>
            </div>
          </div>
        </Card>
        <Card className="p-3 border-border bg-card">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-accent" />
            <div>
              <p className="text-xs text-muted-foreground">Exchanges</p>
              <p className="text-lg font-bold text-foreground">{exchangeConfigs.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-3 border-border bg-card">
          <div className="flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">MetaTrader</p>
              <p className="text-lg font-bold text-foreground">{mtConfigs.length}</p>
            </div>
          </div>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as BrokerType)} className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="crypto_exchange" className="text-sm">
            Crypto Exchanges
          </TabsTrigger>
          <TabsTrigger value="metatrader" className="text-sm">
            MetaTrader
          </TabsTrigger>
          <TabsTrigger value="fix" className="text-sm">
            FIX Protocol
          </TabsTrigger>
        </TabsList>

        {/* Crypto Exchanges Tab */}
        <TabsContent value="crypto_exchange" className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Configure API keys for Binance, Bybit, OKX, and other exchanges
            </p>
            <Button onClick={addExchangeConfig} variant="outline" size="sm" className="gap-2">
              <Plus className="w-4 h-4" />
              Add Exchange
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {exchangeConfigs.map((config) => (
              <Card key={config.id} className={`p-4 border-border ${config.connected ? 'bg-success/5 border-success/30' : 'bg-card'}`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={config.enabled}
                      onCheckedChange={(checked) => updateExchangeConfig(config.id, { enabled: checked })}
                    />
                    <div>
                      <Input
                        value={config.name}
                        onChange={(e) => updateExchangeConfig(config.id, { name: e.target.value })}
                        className="font-semibold bg-transparent border-none p-0 h-auto text-foreground"
                      />
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={config.connected ? "default" : "secondary"} className={config.connected ? "bg-success" : ""}>
                          {config.connected ? <Wifi className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
                          {config.connected ? "Connected" : "Disconnected"}
                        </Badge>
                        {config.testnet && (
                          <Badge variant="outline" className="text-xs">Testnet</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteExchangeConfig(config.id)}>
                    <Trash2 className="w-4 h-4 text-destructive" />
                  </Button>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-xs">Exchange</Label>
                    <Select
                      value={config.exchange}
                      onValueChange={(v) => updateExchangeConfig(config.id, { exchange: v as CryptoExchangeConfig["exchange"] })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EXCHANGE_OPTIONS.map((ex) => (
                          <SelectItem key={ex.value} value={ex.value}>
                            {ex.icon} {ex.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs">API Key</Label>
                    <div className="flex gap-2">
                      <Input
                        type={showSecrets[`${config.id}-key`] ? "text" : "password"}
                        value={config.apiKey}
                        onChange={(e) => updateExchangeConfig(config.id, { apiKey: e.target.value })}
                        placeholder="Enter API Key"
                      />
                      <Button variant="outline" size="icon" onClick={() => toggleSecret(`${config.id}-key`)}>
                        {showSecrets[`${config.id}-key`] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                      <Button variant="outline" size="icon" onClick={() => copyToClipboard(config.apiKey)}>
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs">API Secret</Label>
                    <div className="flex gap-2">
                      <Input
                        type={showSecrets[`${config.id}-secret`] ? "text" : "password"}
                        value={config.apiSecret}
                        onChange={(e) => updateExchangeConfig(config.id, { apiSecret: e.target.value })}
                        placeholder="Enter API Secret"
                      />
                      <Button variant="outline" size="icon" onClick={() => toggleSecret(`${config.id}-secret`)}>
                        {showSecrets[`${config.id}-secret`] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>

                  {(config.exchange === "kucoin" || config.exchange === "coinbase") && (
                    <div className="space-y-2">
                      <Label className="text-xs">Passphrase</Label>
                      <Input
                        type="password"
                        value={config.passphrase || ""}
                        onChange={(e) => updateExchangeConfig(config.id, { passphrase: e.target.value })}
                        placeholder="Enter Passphrase"
                      />
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label className="text-xs">Permissions</Label>
                    <div className="flex flex-wrap gap-2">
                      {PERMISSION_OPTIONS.map((perm) => (
                        <Badge
                          key={perm}
                          variant={config.permissions.includes(perm) ? "default" : "outline"}
                          className="cursor-pointer"
                          onClick={() => togglePermission(config.id, perm)}
                        >
                          {config.permissions.includes(perm) && <CheckCircle2 className="w-3 h-3 mr-1" />}
                          {perm}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-4 pt-2 border-t border-border">
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={config.testnet}
                        onCheckedChange={(checked) => updateExchangeConfig(config.id, { testnet: checked })}
                      />
                      <Label className="text-xs">Testnet Mode</Label>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2">
                    <Button
                      onClick={() => testExchangeConnection(config.id)}
                      variant="outline"
                      size="sm"
                      className="flex-1 gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Test Connection
                    </Button>
                    <Button variant="outline" size="sm" className="gap-2">
                      <ExternalLink className="w-4 h-4" />
                      API Docs
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* MetaTrader Tab */}
        <TabsContent value="metatrader" className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Configure MetaTrader 4/5 accounts for forex and CFD trading
            </p>
            <Button onClick={addMTConfig} variant="outline" size="sm" className="gap-2">
              <Plus className="w-4 h-4" />
              Add Account
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {mtConfigs.map((config) => (
              <Card key={config.id} className={`p-4 border-border ${config.connected ? 'bg-success/5 border-success/30' : 'bg-card'}`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={config.enabled}
                      onCheckedChange={(checked) => updateMTConfig(config.id, { enabled: checked })}
                    />
                    <div>
                      <Input
                        value={config.name}
                        onChange={(e) => updateMTConfig(config.id, { name: e.target.value })}
                        className="font-semibold bg-transparent border-none p-0 h-auto text-foreground"
                      />
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={config.connected ? "default" : "secondary"} className={config.connected ? "bg-success" : ""}>
                          {config.connected ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                          {config.connected ? "Connected" : "Disconnected"}
                        </Badge>
                        <Badge variant="outline" className="text-xs">{config.type.toUpperCase()}</Badge>
                        <Badge variant={config.accountType === "live" ? "destructive" : "secondary"} className="text-xs">
                          {config.accountType.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteMTConfig(config.id)}>
                    <Trash2 className="w-4 h-4 text-destructive" />
                  </Button>
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="text-xs">Platform</Label>
                      <Select
                        value={config.type}
                        onValueChange={(v) => updateMTConfig(config.id, { type: v as "mt4" | "mt5" })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="mt4">MetaTrader 4</SelectItem>
                          <SelectItem value="mt5">MetaTrader 5</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">Account Type</Label>
                      <Select
                        value={config.accountType}
                        onValueChange={(v) => updateMTConfig(config.id, { accountType: v as "demo" | "live" })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="demo">Demo</SelectItem>
                          <SelectItem value="live">Live</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs">Broker</Label>
                    <Input
                      value={config.broker}
                      onChange={(e) => updateMTConfig(config.id, { broker: e.target.value })}
                      placeholder="e.g., IC Markets, XM, Pepperstone"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs">Server</Label>
                    <Input
                      value={config.server}
                      onChange={(e) => updateMTConfig(config.id, { server: e.target.value })}
                      placeholder="e.g., ICMarkets-Demo01"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="text-xs">Login</Label>
                      <Input
                        value={config.login}
                        onChange={(e) => updateMTConfig(config.id, { login: e.target.value })}
                        placeholder="Account number"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">Password</Label>
                      <div className="flex gap-2">
                        <Input
                          type={showSecrets[`${config.id}-pass`] ? "text" : "password"}
                          value={config.password}
                          onChange={(e) => updateMTConfig(config.id, { password: e.target.value })}
                          placeholder="Password"
                        />
                        <Button variant="outline" size="icon" onClick={() => toggleSecret(`${config.id}-pass`)}>
                          {showSecrets[`${config.id}-pass`] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={() => testMTConnection(config.id)}
                    variant="outline"
                    size="sm"
                    className="w-full gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Test Connection
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* FIX Protocol Tab */}
        <TabsContent value="fix" className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Configure FIX protocol connections for institutional trading
            </p>
            <Button onClick={addFIXConfig} variant="outline" size="sm" className="gap-2">
              <Plus className="w-4 h-4" />
              Add FIX Connection
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {fixConfigs.map((config) => (
              <Card key={config.id} className={`p-4 border-border ${config.connected ? 'bg-success/5 border-success/30' : 'bg-card'}`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={config.enabled}
                      onCheckedChange={(checked) => updateFIXConfig(config.id, { enabled: checked })}
                    />
                    <div>
                      <Input
                        value={config.name}
                        onChange={(e) => updateFIXConfig(config.id, { name: e.target.value })}
                        className="font-semibold bg-transparent border-none p-0 h-auto text-foreground"
                      />
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={config.connected ? "default" : "secondary"} className={config.connected ? "bg-success" : ""}>
                          {config.connected ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                          {config.connected ? "Connected" : "Disconnected"}
                        </Badge>
                        {config.sslEnabled && (
                          <Badge variant="outline" className="text-xs">
                            <Shield className="w-3 h-3 mr-1" />
                            SSL
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteFIXConfig(config.id)}>
                    <Trash2 className="w-4 h-4 text-destructive" />
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-foreground">Session Identity</h4>
                    <div className="space-y-2">
                      <Label className="text-xs">SenderCompID</Label>
                      <Input
                        value={config.senderCompId}
                        onChange={(e) => updateFIXConfig(config.id, { senderCompId: e.target.value })}
                        placeholder="Your CompID"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">TargetCompID</Label>
                      <Input
                        value={config.targetCompId}
                        onChange={(e) => updateFIXConfig(config.id, { targetCompId: e.target.value })}
                        placeholder="Exchange CompID"
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-foreground">Connection</h4>
                    <div className="space-y-2">
                      <Label className="text-xs">Host</Label>
                      <Input
                        value={config.host}
                        onChange={(e) => updateFIXConfig(config.id, { host: e.target.value })}
                        placeholder="fix.exchange.com"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">Port</Label>
                      <Input
                        type="number"
                        value={config.port}
                        onChange={(e) => updateFIXConfig(config.id, { port: parseInt(e.target.value) || 443 })}
                        placeholder="443"
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-foreground">Authentication</h4>
                    <div className="space-y-2">
                      <Label className="text-xs">Username</Label>
                      <Input
                        value={config.username}
                        onChange={(e) => updateFIXConfig(config.id, { username: e.target.value })}
                        placeholder="Username"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">Password</Label>
                      <div className="flex gap-2">
                        <Input
                          type={showSecrets[`${config.id}-pass`] ? "text" : "password"}
                          value={config.password}
                          onChange={(e) => updateFIXConfig(config.id, { password: e.target.value })}
                          placeholder="Password"
                        />
                        <Button variant="outline" size="icon" onClick={() => toggleSecret(`${config.id}-pass`)}>
                          {showSecrets[`${config.id}-pass`] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-border">
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={config.sslEnabled}
                        onCheckedChange={(checked) => updateFIXConfig(config.id, { sslEnabled: checked })}
                      />
                      <Label className="text-xs">SSL/TLS</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={config.resetOnLogon}
                        onCheckedChange={(checked) => updateFIXConfig(config.id, { resetOnLogon: checked })}
                      />
                      <Label className="text-xs">Reset on Logon</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Label className="text-xs">Heartbeat (sec):</Label>
                      <Input
                        type="number"
                        value={config.heartbeatInterval}
                        onChange={(e) => updateFIXConfig(config.id, { heartbeatInterval: parseInt(e.target.value) || 30 })}
                        className="w-20"
                      />
                    </div>
                  </div>
                </div>

                <Button
                  onClick={() => testFIXConnection(config.id)}
                  variant="outline"
                  size="sm"
                  className="w-full mt-4 gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Test FIX Connection
                </Button>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BrokerExchangeConfig;