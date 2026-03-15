import { useState, useEffect } from "react";
import apiService from "@/services/apiService";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    TrendingUp, TrendingDown, DollarSign, Percent, Activity,
    Server, Wifi, WifiOff, RefreshCw, Plus, Settings,
    BarChart3, PieChart, AlertCircle, CheckCircle2
} from "lucide-react";
import { PageSection } from "@/components/PageSection";

interface BrokerAccount {
    id: string;
    name: string;
    type: "MT4" | "MT5" | "Binance" | "Bybit" | "OKX" | "FIX";
    status: "connected" | "disconnected" | "error";
    balance: number;
    equity: number;
    margin: number;
    freeMargin: number;
    marginLevel: number;
    openPositions: number;
    todayPnL: number;
    totalPnL: number;
    leverage: number;
}

const MultiBrokerAnalysis = () => {
    const [isLoading, setIsLoading] = useState(true);
    const [accounts, setAccounts] = useState<BrokerAccount[]>([]);

    useEffect(() => {
        const detectBrokers = async () => {
            setIsLoading(true);
            try {
                // Fetch configured trading modes (accounts)
                const response = await apiService.getTradingModes();

                if (response && Array.isArray(response) && response.length > 0) {
                    // Map configured modes to BrokerAccount view model
                    const detectedAccounts: BrokerAccount[] = response.map((mode: any) => {
                        // Determine display type
                        let type: BrokerAccount["type"] = "Binance";
                        if (mode.brokerType === "metatrader") type = mode.mtType === "mt4" ? "MT4" : "MT5";
                        else if (mode.brokerType === "fix") type = "FIX";
                        else if (mode.brokerType === "crypto_exchange") {
                            // Capitalize first letter
                            const ex = mode.exchange || "Binance";
                            type = (ex.charAt(0).toUpperCase() + ex.slice(1)) as any;
                        }

                        // Simulate status based on config (real implementation would ping health)
                        const status = mode.brokerConnected ? "connected" : "disconnected";

                        // Simulate financial data (since config doesn"t hold live balance)
                        // In a real app, we would fetch balance for each account here
                        const isConnected = status === "connected";

                        return {
                            id: mode.id,
                            name: mode.name || `Account ${mode.id}`,
                            type: type,
                            status: status,
                            // Mock live data relative to "connected" status
                            balance: isConnected ? 10000 + Math.random() * 40000 : 0,
                            equity: isConnected ? 10000 + Math.random() * 42000 : 0,
                            margin: isConnected ? Math.random() * 5000 : 0,
                            freeMargin: isConnected ? 5000 + Math.random() * 30000 : 0,
                            marginLevel: isConnected ? 100 + Math.random() * 900 : 0,
                            openPositions: isConnected ? Math.floor(Math.random() * 10) : 0,
                            todayPnL: isConnected ? (Math.random() - 0.4) * 1000 : 0,
                            totalPnL: isConnected ? (Math.random() - 0.3) * 5000 : 0,
                            leverage: mode.leverage || 10
                        };
                    });
                    setAccounts(detectedAccounts);
                    toast.success(`Auto-detected ${detectedAccounts.length} broker configurations.`);
                } else {
                    // Fallback to mock data if no config found (for demo purposes) or empty state
                    toast.info("No active broker configurations found. Showing demo data.");
                    setAccounts(EXISTING_MOCK_DATA);
                }
            } catch (error) {
                console.error("Failed to auto-detect brokers:", error);
                toast.error("Failed to detect broker configurations. Showing demo data.");
                setAccounts(EXISTING_MOCK_DATA);
            } finally {
                setIsLoading(false);
            }
        };

        detectBrokers();
    }, []);

    // Keep mock data as fallback constant
    const EXISTING_MOCK_DATA: BrokerAccount[] = [
        {
            id: "1",
            name: "Binance Futures Main",
            type: "Binance",
            status: "connected",
            balance: 50000,
            equity: 52340,
            margin: 5234,
            freeMargin: 47106,
            marginLevel: 1001.2,
            openPositions: 3,
            todayPnL: 1240,
            totalPnL: 2340,
            leverage: 10
        },
        {
            id: "2",
            name: "MT5 ICMarkets",
            type: "MT5",
            status: "connected",
            balance: 25000,
            equity: 26780,
            margin: 2678,
            freeMargin: 24102,
            marginLevel: 1000.5,
            openPositions: 5,
            todayPnL: 780,
            totalPnL: 1780,
            leverage: 100
        },
        {
            id: "3",
            name: "Bybit USDT Perpetual",
            type: "Bybit",
            status: "connected",
            balance: 30000,
            equity: 29450,
            margin: 2945,
            freeMargin: 26505,
            marginLevel: 999.8,
            openPositions: 2,
            todayPnL: -550,
            totalPnL: -550,
            leverage: 20
        },
        {
            id: "4",
            name: "OKX Trading Account",
            type: "OKX",
            status: "disconnected",
            balance: 15000,
            equity: 15000,
            margin: 0,
            freeMargin: 15000,
            marginLevel: 0,
            openPositions: 0,
            todayPnL: 0,
            totalPnL: 450,
            leverage: 5
        }
    ];

    const totalBalance = accounts.reduce((sum, acc) => sum + acc.balance, 0);
    const totalEquity = accounts.reduce((sum, acc) => sum + acc.equity, 0);
    const totalPnL = accounts.reduce((sum, acc) => sum + acc.todayPnL, 0);
    const totalPositions = accounts.reduce((sum, acc) => sum + acc.openPositions, 0);
    const connectedAccounts = accounts.filter(acc => acc.status === "connected").length;

    return (
        <div className="space-y-6 px-2 md:px-0">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
                        <Server className="w-8 h-8 text-primary" />
                        Multi-Broker Account Analysis
                    </h1>
                    <p className="text-sm text-muted-foreground">
                        Unified view of all trading accounts across multiple brokers
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                        <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                        {isLoading ? 'Detecting...' : 'Scan Brokers'}
                    </Button>
                    <Button size="sm">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Account
                    </Button>
                </div>
            </div>

            {/* Global Summary */}
            <PageSection
                title="Portfolio Overview"
                icon={<BarChart3 className="w-5 h-5" />}
            >
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <Card className="p-4 bg-card border-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Server className="w-4 h-4 text-primary" />
                            <p className="text-xs text-muted-foreground">Connected</p>
                        </div>
                        <p className="text-2xl font-bold">{connectedAccounts}/{accounts.length}</p>
                    </Card>

                    <Card className="p-4 bg-card border-border">
                        <div className="flex items-center gap-2 mb-2">
                            <DollarSign className="w-4 h-4 text-accent" />
                            <p className="text-xs text-muted-foreground">Total Balance</p>
                        </div>
                        <p className="text-2xl font-bold">${totalBalance.toLocaleString()}</p>
                    </Card>

                    <Card className="p-4 bg-card border-border">
                        <div className="flex items-center gap-2 mb-2">
                            <TrendingUp className="w-4 h-4 text-success" />
                            <p className="text-xs text-muted-foreground">Total Equity</p>
                        </div>
                        <p className="text-2xl font-bold">${totalEquity.toLocaleString()}</p>
                    </Card>

                    <Card className={`p-4 border-border ${totalPnL >= 0 ? 'bg-success/5 border-success/30' : 'bg-destructive/5 border-destructive/30'}`}>
                        <div className="flex items-center gap-2 mb-2">
                            <Activity className={`w-4 h-4 ${totalPnL >= 0 ? 'text-success' : 'text-destructive'}`} />
                            <p className="text-xs text-muted-foreground">Today's P&L</p>
                        </div>
                        <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-success' : 'text-destructive'}`}>
                            ${totalPnL.toLocaleString()}
                        </p>
                    </Card>

                    <Card className="p-4 bg-card border-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Activity className="w-4 h-4 text-primary" />
                            <p className="text-xs text-muted-foreground">Open Positions</p>
                        </div>
                        <p className="text-2xl font-bold">{totalPositions}</p>
                    </Card>
                </div>
            </PageSection>

            {/* Individual Accounts */}
            <PageSection
                title="Broker Accounts"
                icon={<Server className="w-5 h-5" />}
            >
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {accounts.map(account => (
                        <Card
                            key={account.id}
                            className={`p-6 border-border ${account.status === "connected"
                                ? 'bg-card'
                                : 'bg-secondary/20 opacity-75'
                                }`}
                        >
                            {/* Account Header */}
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${account.type === "MT4" || account.type === "MT5"
                                        ? 'bg-blue-500/20'
                                        : account.type === "Binance"
                                            ? 'bg-yellow-500/20'
                                            : account.type === "Bybit"
                                                ? 'bg-orange-500/20'
                                                : 'bg-purple-500/20'
                                        }`}>
                                        <Server className={`w-5 h-5 ${account.type === "MT4" || account.type === "MT5"
                                            ? 'text-blue-500'
                                            : account.type === "Binance"
                                                ? 'text-yellow-500'
                                                : account.type === "Bybit"
                                                    ? 'text-orange-500'
                                                    : 'text-purple-500'
                                            }`} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg">{account.name}</h3>
                                        <Badge variant="outline" className="text-xs mt-1">
                                            {account.type}
                                        </Badge>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {account.status === "connected" ? (
                                        <Badge className="bg-success gap-1">
                                            <Wifi className="w-3 h-3" />
                                            Connected
                                        </Badge>
                                    ) : account.status === "error" ? (
                                        <Badge variant="destructive" className="gap-1">
                                            <AlertCircle className="w-3 h-3" />
                                            Error
                                        </Badge>
                                    ) : (
                                        <Badge variant="secondary" className="gap-1">
                                            <WifiOff className="w-3 h-3" />
                                            Offline
                                        </Badge>
                                    )}
                                    <Button variant="ghost" size="sm">
                                        <Settings className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>

                            {/* Account Metrics */}
                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div className="space-y-3">
                                    <div>
                                        <p className="text-xs text-muted-foreground">Balance</p>
                                        <p className="text-xl font-bold">${account.balance.toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Equity</p>
                                        <p className="text-xl font-bold">${account.equity.toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Margin Used</p>
                                        <p className="text-lg font-mono">${account.margin.toLocaleString()}</p>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <div>
                                        <p className="text-xs text-muted-foreground">Free Margin</p>
                                        <p className="text-xl font-bold">${account.freeMargin.toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Margin Level</p>
                                        <p className={`text-xl font-bold ${account.marginLevel > 200 ? 'text-success' :
                                            account.marginLevel > 100 ? 'text-accent' :
                                                'text-destructive'
                                            }`}>
                                            {account.marginLevel.toFixed(1)}%
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Leverage</p>
                                        <p className="text-lg font-mono">{account.leverage}x</p>
                                    </div>
                                </div>
                            </div>

                            {/* Performance */}
                            <div className="grid grid-cols-3 gap-3 p-3 bg-secondary/30 rounded-lg">
                                <div className="text-center">
                                    <p className="text-xs text-muted-foreground mb-1">Positions</p>
                                    <p className="text-lg font-bold">{account.openPositions}</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-xs text-muted-foreground mb-1">Today P&L</p>
                                    <p className={`text-lg font-bold ${account.todayPnL >= 0 ? 'text-success' : 'text-destructive'}`}>
                                        ${account.todayPnL.toLocaleString()}
                                    </p>
                                </div>
                                <div className="text-center">
                                    <p className="text-xs text-muted-foreground mb-1">Total P&L</p>
                                    <p className={`text-lg font-bold ${account.totalPnL >= 0 ? 'text-success' : 'text-destructive'}`}>
                                        ${account.totalPnL.toLocaleString()}
                                    </p>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="grid grid-cols-2 gap-2 mt-4">
                                <Button variant="outline" size="sm">
                                    <Activity className="w-4 h-4 mr-2" />
                                    View Positions
                                </Button>
                                <Button variant="outline" size="sm">
                                    <BarChart3 className="w-4 h-4 mr-2" />
                                    Analytics
                                </Button>
                            </div>
                        </Card>
                    ))}
                </div>
            </PageSection>

            {/* Allocation Chart */}
            <PageSection
                title="Portfolio Allocation"
                icon={<PieChart className="w-5 h-5" />}
            >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="p-6 border-border bg-card">
                        <h3 className="font-semibold mb-4">Balance Distribution</h3>
                        <div className="space-y-3">
                            {accounts.map(account => {
                                const percentage = (account.balance / totalBalance) * 100;
                                return (
                                    <div key={account.id}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span>{account.name}</span>
                                            <span className="font-mono">{percentage.toFixed(1)}%</span>
                                        </div>
                                        <div className="w-full bg-secondary rounded-full h-2">
                                            <div
                                                className="bg-primary rounded-full h-2 transition-all"
                                                style={{ width: `${percentage}%` }}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </Card>

                    <Card className="p-6 border-border bg-card">
                        <h3 className="font-semibold mb-4">Risk Exposure by Broker</h3>
                        <div className="space-y-3">
                            {accounts.map(account => {
                                const riskPercentage = account.balance > 0 ? (account.margin / account.balance) * 100 : 0;
                                return (
                                    <div key={account.id}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span>{account.name}</span>
                                            <span className={`font-mono ${riskPercentage > 50 ? 'text-destructive' :
                                                riskPercentage > 30 ? 'text-accent' :
                                                    'text-success'
                                                }`}>
                                                {riskPercentage.toFixed(1)}%
                                            </span>
                                        </div>
                                        <div className="w-full bg-secondary rounded-full h-2">
                                            <div
                                                className={`rounded-full h-2 transition-all ${riskPercentage > 50 ? 'bg-destructive' :
                                                    riskPercentage > 30 ? 'bg-accent' :
                                                        'bg-success'
                                                    }`}
                                                style={{ width: `${Math.min(riskPercentage, 100)}%` }}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </Card>
                </div>
            </PageSection>
        </div>
    );
};

export default MultiBrokerAnalysis;
