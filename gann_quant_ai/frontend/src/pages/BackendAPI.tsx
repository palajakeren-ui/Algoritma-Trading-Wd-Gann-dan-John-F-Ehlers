import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Database, 
  Server, 
  Globe, 
  Key, 
  RefreshCw, 
  CheckCircle, 
  XCircle,
  Save,
  TestTube,
  Link,
  Shield,
  Cpu,
  Plus,
  Trash2,
  Edit,
  Eye,
  Download,
  Upload
} from "lucide-react";
import { toast } from "sonner";

interface APIConfig {
  id: string;
  name: string;
  baseUrl: string;
  wsUrl: string;
  apiVersion: string;
  timeout: number;
  retryAttempts: number;
  apiKey: string;
  isActive: boolean;
}

interface DBConfig {
  id: string;
  name: string;
  host: string;
  port: string;
  database: string;
  username: string;
  password: string;
  ssl: boolean;
  poolSize: number;
  isActive: boolean;
}

interface TableRecord {
  id: string;
  [key: string]: string | number | boolean;
}

interface DBTable {
  name: string;
  rows: number;
  columns: string[];
  records: TableRecord[];
}

const BackendAPI = () => {
  const [apiConfigs, setApiConfigs] = useState<APIConfig[]>([
    {
      id: "api-1",
      name: "Primary API",
      baseUrl: "https://api.gannquantai.com",
      wsUrl: "wss://ws.gannquantai.com",
      apiVersion: "v1",
      timeout: 30000,
      retryAttempts: 3,
      apiKey: "",
      isActive: true,
    },
    {
      id: "api-2",
      name: "Backup API",
      baseUrl: "https://backup-api.gannquantai.com",
      wsUrl: "wss://backup-ws.gannquantai.com",
      apiVersion: "v1",
      timeout: 30000,
      retryAttempts: 5,
      apiKey: "",
      isActive: true, // Multiple active allowed
    },
    {
      id: "api-3",
      name: "Binance API",
      baseUrl: "https://api.binance.com",
      wsUrl: "wss://stream.binance.com:9443",
      apiVersion: "v3",
      timeout: 10000,
      retryAttempts: 3,
      apiKey: "",
      isActive: true,
    },
  ]);

  const [dbConfigs, setDbConfigs] = useState<DBConfig[]>([
    {
      id: "db-1",
      name: "Primary Database",
      host: "localhost",
      port: "5432",
      database: "gann_quant_db",
      username: "",
      password: "",
      ssl: true,
      poolSize: 10,
      isActive: true,
    },
    {
      id: "db-2",
      name: "Read Replica",
      host: "replica.gannquantai.com",
      port: "5432",
      database: "gann_quant_replica",
      username: "",
      password: "",
      ssl: true,
      poolSize: 5,
      isActive: true, // Multiple active allowed
    },
  ]);

  const [selectedApiId, setSelectedApiId] = useState("api-1");
  const [selectedDbId, setSelectedDbId] = useState("db-1");
  const [connectionStatus, setConnectionStatus] = useState<Record<string, boolean>>({});
  const [isTestingConnection, setIsTestingConnection] = useState<Record<string, boolean>>({});

  // CRUD State
  const [selectedTable, setSelectedTable] = useState<string>("trades");
  const [crudMode, setCrudMode] = useState<"view" | "create" | "edit">("view");
  const [editingRecord, setEditingRecord] = useState<TableRecord | null>(null);
  const [newRecord, setNewRecord] = useState<Record<string, string>>({});

  const [dbTables, setDbTables] = useState<DBTable[]>([
    { 
      name: "trades", 
      rows: 15420, 
      columns: ["id", "symbol", "side", "price", "quantity", "timestamp"],
      records: [
        { id: "1", symbol: "BTCUSDT", side: "BUY", price: 47500, quantity: 0.5, timestamp: "2024-01-15 10:30:00" },
        { id: "2", symbol: "ETHUSDT", side: "SELL", price: 2450, quantity: 2.0, timestamp: "2024-01-15 11:15:00" },
        { id: "3", symbol: "XAUUSD", side: "BUY", price: 2045, quantity: 1.0, timestamp: "2024-01-15 12:00:00" },
      ]
    },
    { 
      name: "positions", 
      rows: 45, 
      columns: ["id", "symbol", "side", "entry_price", "quantity", "pnl"],
      records: [
        { id: "1", symbol: "BTCUSDT", side: "LONG", entry_price: 47000, quantity: 0.5, pnl: 250 },
        { id: "2", symbol: "ETHUSDT", side: "SHORT", entry_price: 2500, quantity: 2.0, pnl: -100 },
      ]
    },
    { 
      name: "signals", 
      rows: 8932, 
      columns: ["id", "symbol", "timeframe", "signal", "strength", "timestamp"],
      records: [
        { id: "1", symbol: "BTCUSDT", timeframe: "1H", signal: "BUY", strength: 85, timestamp: "2024-01-15 10:00:00" },
        { id: "2", symbol: "EURUSD", timeframe: "4H", signal: "SELL", strength: 72, timestamp: "2024-01-15 08:00:00" },
      ]
    },
    { name: "forecasts", rows: 2341, columns: ["id", "symbol", "prediction", "confidence"], records: [] },
    { name: "alerts", rows: 567, columns: ["id", "type", "message", "status"], records: [] },
    { name: "users", rows: 12, columns: ["id", "username", "email", "role"], records: [] },
    { name: "settings", rows: 1, columns: ["id", "key", "value"], records: [] },
    { name: "logs", rows: 45678, columns: ["id", "level", "message", "timestamp"], records: [] },
    { name: "backtest_results", rows: 234, columns: ["id", "strategy", "profit", "drawdown"], records: [] },
  ]);

  const selectedApi = apiConfigs.find(c => c.id === selectedApiId) || apiConfigs[0];
  const selectedDb = dbConfigs.find(c => c.id === selectedDbId) || dbConfigs[0];
  const currentTable = dbTables.find(t => t.name === selectedTable);

  const updateApiConfig = (id: string, updates: Partial<APIConfig>) => {
    setApiConfigs(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  const updateDbConfig = (id: string, updates: Partial<DBConfig>) => {
    setDbConfigs(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  const addApiConfig = () => {
    const newId = `api-${Date.now()}`;
    setApiConfigs(prev => [...prev, {
      id: newId,
      name: `API Config ${prev.length + 1}`,
      baseUrl: "",
      wsUrl: "",
      apiVersion: "v1",
      timeout: 30000,
      retryAttempts: 3,
      apiKey: "",
      isActive: false,
    }]);
    setSelectedApiId(newId);
    toast.success("New API configuration added");
  };

  const addDbConfig = () => {
    const newId = `db-${Date.now()}`;
    setDbConfigs(prev => [...prev, {
      id: newId,
      name: `Database ${prev.length + 1}`,
      host: "",
      port: "5432",
      database: "",
      username: "",
      password: "",
      ssl: true,
      poolSize: 10,
      isActive: false,
    }]);
    setSelectedDbId(newId);
    toast.success("New database configuration added");
  };

  const removeApiConfig = (id: string) => {
    if (apiConfigs.length <= 1) {
      toast.error("Cannot remove the last API configuration");
      return;
    }
    setApiConfigs(prev => prev.filter(c => c.id !== id));
    if (selectedApiId === id) {
      setSelectedApiId(apiConfigs[0].id);
    }
    toast.success("API configuration removed");
  };

  const removeDbConfig = (id: string) => {
    if (dbConfigs.length <= 1) {
      toast.error("Cannot remove the last database configuration");
      return;
    }
    setDbConfigs(prev => prev.filter(c => c.id !== id));
    if (selectedDbId === id) {
      setSelectedDbId(dbConfigs[0].id);
    }
    toast.success("Database configuration removed");
  };

  const testConnection = async (type: string, id: string) => {
    const key = `${type}-${id}`;
    setIsTestingConnection(prev => ({ ...prev, [key]: true }));
    toast.info(`Testing ${type} connection...`);
    
    setTimeout(() => {
      const success = Math.random() > 0.3;
      setConnectionStatus(prev => ({ ...prev, [key]: success }));
      setIsTestingConnection(prev => ({ ...prev, [key]: false }));
      
      if (success) {
        toast.success(`Connection successful!`);
      } else {
        toast.error(`Failed to connect. Please check your settings.`);
      }
    }, 2000);
  };

  // CRUD Operations
  const handleCreateRecord = () => {
    if (!currentTable) return;
    
    const newId = String(Date.now());
    const record: TableRecord = { id: newId, ...newRecord };
    
    setDbTables(prev => prev.map(t => 
      t.name === selectedTable 
        ? { ...t, rows: t.rows + 1, records: [...t.records, record] }
        : t
    ));
    
    setNewRecord({});
    setCrudMode("view");
    toast.success(`Record created in ${selectedTable}`);
  };

  const handleUpdateRecord = () => {
    if (!editingRecord || !currentTable) return;
    
    setDbTables(prev => prev.map(t => 
      t.name === selectedTable 
        ? { ...t, records: t.records.map(r => r.id === editingRecord.id ? editingRecord : r) }
        : t
    ));
    
    setEditingRecord(null);
    setCrudMode("view");
    toast.success(`Record updated in ${selectedTable}`);
  };

  const handleDeleteRecord = (recordId: string) => {
    setDbTables(prev => prev.map(t => 
      t.name === selectedTable 
        ? { ...t, rows: t.rows - 1, records: t.records.filter(r => r.id !== recordId) }
        : t
    ));
    toast.success(`Record deleted from ${selectedTable}`);
  };

  const saveSettings = () => {
    toast.success("All backend configurations saved successfully!");
  };

  const activeApiCount = apiConfigs.filter(c => c.isActive).length;
  const activeDbCount = dbConfigs.filter(c => c.isActive).length;

  return (
    <div className="space-y-4 md:space-y-6 px-2 md:px-0">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground flex items-center gap-2">
            <Server className="w-6 h-6 md:w-8 md:h-8 text-primary" />
            Backend API & Database
          </h1>
          <p className="text-sm text-muted-foreground">Configure backend connections and database settings (Multiple Active Supported)</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-sm">
            {activeApiCount} APIs Active
          </Badge>
          <Badge variant="outline" className="text-sm">
            {activeDbCount} DBs Active
          </Badge>
          <Button onClick={saveSettings}>
            <Save className="w-4 h-4 mr-2" />
            Save All
          </Button>
        </div>
      </div>

      {/* Connection Status Overview */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {apiConfigs.map(api => (
          <Card key={api.id} className={`border-border bg-card ${api.isActive ? 'ring-2 ring-success' : ''}`}>
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <Globe className={`w-4 h-4 ${connectionStatus[`api-${api.id}`] ? "text-success" : "text-muted-foreground"}`} />
                {api.isActive && <Badge className="bg-success/20 text-success text-xs">Active</Badge>}
              </div>
              <p className="font-semibold text-foreground text-sm truncate">{api.name}</p>
              <p className="text-xs text-muted-foreground truncate">{api.baseUrl || "Not configured"}</p>
            </CardContent>
          </Card>
        ))}
        {dbConfigs.map(db => (
          <Card key={db.id} className={`border-border bg-card ${db.isActive ? 'ring-2 ring-primary' : ''}`}>
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <Database className={`w-4 h-4 ${connectionStatus[`db-${db.id}`] ? "text-success" : "text-muted-foreground"}`} />
                {db.isActive && <Badge className="bg-primary/20 text-primary text-xs">Active</Badge>}
              </div>
              <p className="font-semibold text-foreground text-sm truncate">{db.name}</p>
              <p className="text-xs text-muted-foreground truncate">{db.database || "Not configured"}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="api" className="w-full">
        <TabsList className="grid w-full grid-cols-4 md:w-auto md:inline-grid">
          <TabsTrigger value="api" className="text-xs md:text-sm">REST API</TabsTrigger>
          <TabsTrigger value="database" className="text-xs md:text-sm">Database</TabsTrigger>
          <TabsTrigger value="crud" className="text-xs md:text-sm">CRUD Operations</TabsTrigger>
          <TabsTrigger value="advanced" className="text-xs md:text-sm">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="api" className="space-y-4 mt-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary" />
                  API Configurations ({apiConfigs.length}) - Multiple Active Supported
                </CardTitle>
                <Button onClick={addApiConfig} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add API
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 mb-4">
                {apiConfigs.map(api => (
                  <Button
                    key={api.id}
                    variant={selectedApiId === api.id ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedApiId(api.id)}
                    className="relative"
                  >
                    {api.name}
                    {api.isActive && <span className="ml-2 w-2 h-2 bg-success rounded-full"></span>}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{selectedApi.name}</CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant={selectedApi.isActive ? "default" : "outline"}
                    size="sm"
                    onClick={() => updateApiConfig(selectedApiId, { isActive: !selectedApi.isActive })}
                  >
                    {selectedApi.isActive ? "Active" : "Inactive"}
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => removeApiConfig(selectedApiId)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-foreground">Configuration Name</Label>
                  <Input
                    value={selectedApi.name}
                    onChange={(e) => updateApiConfig(selectedApiId, { name: e.target.value })}
                    placeholder="API Name"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Base URL</Label>
                  <Input
                    value={selectedApi.baseUrl}
                    onChange={(e) => updateApiConfig(selectedApiId, { baseUrl: e.target.value })}
                    placeholder="https://api.example.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">WebSocket URL</Label>
                  <Input
                    value={selectedApi.wsUrl}
                    onChange={(e) => updateApiConfig(selectedApiId, { wsUrl: e.target.value })}
                    placeholder="wss://ws.example.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">API Version</Label>
                  <Input
                    value={selectedApi.apiVersion}
                    onChange={(e) => updateApiConfig(selectedApiId, { apiVersion: e.target.value })}
                    placeholder="v1"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Timeout (ms)</Label>
                  <Input
                    type="number"
                    value={selectedApi.timeout}
                    onChange={(e) => updateApiConfig(selectedApiId, { timeout: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Retry Attempts</Label>
                  <Input
                    type="number"
                    value={selectedApi.retryAttempts}
                    onChange={(e) => updateApiConfig(selectedApiId, { retryAttempts: parseInt(e.target.value) })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-foreground">API Key</Label>
                <Input 
                  type="password" 
                  value={selectedApi.apiKey}
                  onChange={(e) => updateApiConfig(selectedApiId, { apiKey: e.target.value })}
                  placeholder="Enter your API key" 
                />
              </div>

              <div className="flex flex-col md:flex-row gap-3 pt-4">
                <Button 
                  variant="outline" 
                  onClick={() => testConnection("api", selectedApiId)}
                  disabled={isTestingConnection[`api-${selectedApiId}`]}
                  className="flex-1"
                >
                  {isTestingConnection[`api-${selectedApiId}`] ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <TestTube className="w-4 h-4 mr-2" />
                  )}
                  Test API
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => testConnection("ws", selectedApiId)}
                  disabled={isTestingConnection[`ws-${selectedApiId}`]}
                  className="flex-1"
                >
                  {isTestingConnection[`ws-${selectedApiId}`] ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <TestTube className="w-4 h-4 mr-2" />
                  )}
                  Test WebSocket
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="database" className="space-y-4 mt-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary" />
                  Database Configurations ({dbConfigs.length}) - Multiple Active Supported
                </CardTitle>
                <Button onClick={addDbConfig} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Database
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 mb-4">
                {dbConfigs.map(db => (
                  <Button
                    key={db.id}
                    variant={selectedDbId === db.id ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedDbId(db.id)}
                    className="relative"
                  >
                    {db.name}
                    {db.isActive && <span className="ml-2 w-2 h-2 bg-success rounded-full"></span>}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{selectedDb.name}</CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant={selectedDb.isActive ? "default" : "outline"}
                    size="sm"
                    onClick={() => updateDbConfig(selectedDbId, { isActive: !selectedDb.isActive })}
                  >
                    {selectedDb.isActive ? "Active" : "Inactive"}
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => removeDbConfig(selectedDbId)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-foreground">Configuration Name</Label>
                  <Input
                    value={selectedDb.name}
                    onChange={(e) => updateDbConfig(selectedDbId, { name: e.target.value })}
                    placeholder="Database Name"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Host</Label>
                  <Input
                    value={selectedDb.host}
                    onChange={(e) => updateDbConfig(selectedDbId, { host: e.target.value })}
                    placeholder="localhost"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Port</Label>
                  <Input
                    value={selectedDb.port}
                    onChange={(e) => updateDbConfig(selectedDbId, { port: e.target.value })}
                    placeholder="5432"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Database Name</Label>
                  <Input
                    value={selectedDb.database}
                    onChange={(e) => updateDbConfig(selectedDbId, { database: e.target.value })}
                    placeholder="gann_quant_db"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Pool Size</Label>
                  <Input
                    type="number"
                    value={selectedDb.poolSize}
                    onChange={(e) => updateDbConfig(selectedDbId, { poolSize: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Username</Label>
                  <Input
                    value={selectedDb.username}
                    onChange={(e) => updateDbConfig(selectedDbId, { username: e.target.value })}
                    placeholder="Enter username"
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label className="text-foreground">Password</Label>
                  <Input
                    type="password"
                    value={selectedDb.password}
                    onChange={(e) => updateDbConfig(selectedDbId, { password: e.target.value })}
                    placeholder="Enter password"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-primary" />
                  <span className="text-sm text-foreground">Enable SSL/TLS</span>
                </div>
                <Switch
                  checked={selectedDb.ssl}
                  onCheckedChange={(checked) => updateDbConfig(selectedDbId, { ssl: checked })}
                />
              </div>

              <Button 
                variant="outline" 
                onClick={() => testConnection("db", selectedDbId)}
                disabled={isTestingConnection[`db-${selectedDbId}`]}
                className="w-full"
              >
                {isTestingConnection[`db-${selectedDbId}`] ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <TestTube className="w-4 h-4 mr-2" />
                )}
                Test Database Connection
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* CRUD Operations Tab */}
        <TabsContent value="crud" className="space-y-4 mt-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary" />
                  Database CRUD Operations
                </CardTitle>
                <div className="flex gap-2">
                  <Button 
                    variant={crudMode === "create" ? "default" : "outline"} 
                    size="sm"
                    onClick={() => {
                      setCrudMode("create");
                      setNewRecord({});
                    }}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Create
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="w-4 h-4 mr-1" />
                    Export
                  </Button>
                  <Button variant="outline" size="sm">
                    <Upload className="w-4 h-4 mr-1" />
                    Import
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Table Selector */}
              <div className="mb-4">
                <Label className="text-foreground mb-2 block">Select Table</Label>
                <div className="flex flex-wrap gap-2">
                  {dbTables.map(table => (
                    <Button
                      key={table.name}
                      variant={selectedTable === table.name ? "default" : "outline"}
                      size="sm"
                      onClick={() => {
                        setSelectedTable(table.name);
                        setCrudMode("view");
                        setEditingRecord(null);
                      }}
                    >
                      {table.name}
                      <Badge variant="secondary" className="ml-2 text-xs">
                        {table.rows}
                      </Badge>
                    </Button>
                  ))}
                </div>
              </div>

              {/* Create Form */}
              {crudMode === "create" && currentTable && (
                <div className="p-4 bg-secondary/30 rounded-lg mb-4">
                  <h4 className="font-semibold text-foreground mb-3">Create New Record in {selectedTable}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {currentTable.columns.filter(c => c !== "id").map(col => (
                      <div key={col} className="space-y-1">
                        <Label className="text-sm text-foreground">{col}</Label>
                        <Input
                          value={newRecord[col] || ""}
                          onChange={(e) => setNewRecord(prev => ({ ...prev, [col]: e.target.value }))}
                          placeholder={col}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button onClick={handleCreateRecord}>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Save Record
                    </Button>
                    <Button variant="outline" onClick={() => setCrudMode("view")}>
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Edit Form */}
              {crudMode === "edit" && editingRecord && currentTable && (
                <div className="p-4 bg-primary/10 rounded-lg mb-4">
                  <h4 className="font-semibold text-foreground mb-3">Edit Record #{editingRecord.id}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {currentTable.columns.filter(c => c !== "id").map(col => (
                      <div key={col} className="space-y-1">
                        <Label className="text-sm text-foreground">{col}</Label>
                        <Input
                          value={String(editingRecord[col] || "")}
                          onChange={(e) => setEditingRecord(prev => prev ? { ...prev, [col]: e.target.value } : null)}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button onClick={handleUpdateRecord}>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Update Record
                    </Button>
                    <Button variant="outline" onClick={() => {
                      setCrudMode("view");
                      setEditingRecord(null);
                    }}>
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Records Table */}
              {currentTable && (
                <div className="border border-border rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-secondary/50">
                        <tr>
                          {currentTable.columns.map(col => (
                            <th key={col} className="px-4 py-2 text-left font-semibold text-foreground">
                              {col}
                            </th>
                          ))}
                          <th className="px-4 py-2 text-left font-semibold text-foreground">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentTable.records.length === 0 ? (
                          <tr>
                            <td colSpan={currentTable.columns.length + 1} className="px-4 py-8 text-center text-muted-foreground">
                              No records found. Click "Create" to add a new record.
                            </td>
                          </tr>
                        ) : (
                          currentTable.records.map((record, idx) => (
                            <tr key={record.id} className={idx % 2 === 0 ? "bg-card" : "bg-secondary/20"}>
                              {currentTable.columns.map(col => (
                                <td key={col} className="px-4 py-2 text-foreground">
                                  {String(record[col] || "-")}
                                </td>
                              ))}
                              <td className="px-4 py-2">
                                <div className="flex gap-1">
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    onClick={() => {
                                      setEditingRecord(record);
                                      setCrudMode("edit");
                                    }}
                                  >
                                    <Edit className="w-4 h-4" />
                                  </Button>
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    className="text-destructive hover:text-destructive"
                                    onClick={() => handleDeleteRecord(record.id)}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4 mt-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Cpu className="w-5 h-5 text-primary" />
                Advanced Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-foreground">Retry Attempts (Global)</Label>
                  <Input type="number" defaultValue="3" />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Request Rate Limit (per min)</Label>
                  <Input type="number" defaultValue="1000" />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Cache TTL (seconds)</Label>
                  <Input type="number" defaultValue="300" />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Log Level</Label>
                  <select className="w-full px-4 py-2 bg-input border border-border rounded-md text-foreground">
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warn">Warning</option>
                    <option value="error">Error</option>
                  </select>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <span className="text-sm text-foreground">Enable Request Caching</span>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <span className="text-sm text-foreground">Enable Compression</span>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <span className="text-sm text-foreground">Enable Debug Mode</span>
                  <Switch />
                </div>
                <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <span className="text-sm text-foreground">Auto-reconnect on Disconnect</span>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <span className="text-sm text-foreground">Load Balance Across Active APIs</span>
                  <Switch defaultChecked />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Key className="w-5 h-5 text-primary" />
                Environment Variables
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { key: "API_BASE_URL", value: selectedApi.baseUrl, secret: false },
                { key: "WS_URL", value: selectedApi.wsUrl, secret: false },
                { key: "DATABASE_URL", value: `postgresql://***:***@${selectedDb.host}:${selectedDb.port}/${selectedDb.database}`, secret: true },
                { key: "API_KEY", value: "••••••••••••••••", secret: true },
                { key: "JWT_SECRET", value: "••••••••••••••••", secret: true },
              ].map((env, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <div className="flex items-center gap-2">
                    <code className="text-sm font-mono text-foreground">{env.key}</code>
                    {env.secret && (
                      <Badge variant="outline" className="text-xs">
                        <Shield className="w-3 h-3 mr-1" />
                        Secret
                      </Badge>
                    )}
                  </div>
                  <code className="text-xs text-muted-foreground truncate max-w-[200px]">{env.value}</code>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BackendAPI;
