import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    TrendingUp, TrendingDown, DollarSign, Percent,
    Activity, AlertCircle, CheckCircle2, Clock, Zap
} from "lucide-react";
import { toast } from "sonner";

interface Position {
    id: string;
    symbol: string;
    type: "BUY" | "SELL";
    lotSize: number;
    entryPrice: number;
    currentPrice: number;
    stopLoss: number;
    takeProfit: number;
    pnl: number;
    pnlPercent: number;
    openTime: Date;
    status: "OPEN" | "PENDING" | "CLOSED";
}

interface OrderForm {
    symbol: string;
    type: "BUY" | "SELL";
    orderType: "MARKET" | "LIMIT" | "STOP";
    lotSize: number;
    limitPrice?: number;
    stopLoss?: number;
    takeProfit?: number;
}

export const ActiveTradingPanel = ({ currentPrice }: { currentPrice: number }) => {
    const [positions, setPositions] = useState<Position[]>([
        {
            id: "1",
            symbol: "BTCUSDT",
            type: "BUY",
            lotSize: 0.5,
            entryPrice: 95420,
            currentPrice: currentPrice,
            stopLoss: 94000,
            takeProfit: 98000,
            pnl: (currentPrice - 95420) * 0.5,
            pnlPercent: ((currentPrice - 95420) / 95420) * 100,
            openTime: new Date(Date.now() - 3600000),
            status: "OPEN"
        }
    ]);

    const [orderForm, setOrderForm] = useState<OrderForm>({
        symbol: "BTCUSDT",
        type: "BUY",
        orderType: "MARKET",
        lotSize: 0.1,
        stopLoss: currentPrice * 0.98,
        takeProfit: currentPrice * 1.04
    });

    // Update current prices in real-time
    useEffect(() => {
        setPositions(prev => prev.map(pos => ({
            ...pos,
            currentPrice,
            pnl: pos.type === "BUY"
                ? (currentPrice - pos.entryPrice) * pos.lotSize
                : (pos.entryPrice - currentPrice) * pos.lotSize,
            pnlPercent: pos.type === "BUY"
                ? ((currentPrice - pos.entryPrice) / pos.entryPrice) * 100
                : ((pos.entryPrice - currentPrice) / pos.entryPrice) * 100
        })));
    }, [currentPrice]);

    const handlePlaceOrder = () => {
        const newPosition: Position = {
            id: Date.now().toString(),
            symbol: orderForm.symbol,
            type: orderForm.type,
            lotSize: orderForm.lotSize,
            entryPrice: orderForm.orderType === "MARKET" ? currentPrice : (orderForm.limitPrice || currentPrice),
            currentPrice: currentPrice,
            stopLoss: orderForm.stopLoss || currentPrice * 0.98,
            takeProfit: orderForm.takeProfit || currentPrice * 1.04,
            pnl: 0,
            pnlPercent: 0,
            openTime: new Date(),
            status: orderForm.orderType === "MARKET" ? "OPEN" : "PENDING"
        };

        setPositions(prev => [...prev, newPosition]);
        toast.success(`${orderForm.type} order placed for ${orderForm.symbol}`);
    };

    const handleClosePosition = (id: string) => {
        const position = positions.find(p => p.id === id);
        if (position) {
            toast.success(`Position closed. P&L: $${position.pnl.toFixed(2)}`);
            setPositions(prev => prev.filter(p => p.id !== id));
        }
    };

    const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0);
    const openPositions = positions.filter(p => p.status === "OPEN").length;

    return (
        <div className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Card className="p-4 bg-card border-border">
                    <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-primary" />
                        <div>
                            <p className="text-xs text-muted-foreground">Open Positions</p>
                            <p className="text-xl font-bold">{openPositions}</p>
                        </div>
                    </div>
                </Card>
                <Card className={`p-4 border-border ${totalPnL >= 0 ? 'bg-success/5 border-success/30' : 'bg-destructive/5 border-destructive/30'}`}>
                    <div className="flex items-center gap-2">
                        <DollarSign className={`w-4 h-4 ${totalPnL >= 0 ? 'text-success' : 'text-destructive'}`} />
                        <div>
                            <p className="text-xs text-muted-foreground">Total P&L</p>
                            <p className={`text-xl font-bold ${totalPnL >= 0 ? 'text-success' : 'text-destructive'}`}>
                                ${totalPnL.toFixed(2)}
                            </p>
                        </div>
                    </div>
                </Card>
                <Card className="p-4 bg-card border-border">
                    <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-accent" />
                        <div>
                            <p className="text-xs text-muted-foreground">Win Rate</p>
                            <p className="text-xl font-bold">68%</p>
                        </div>
                    </div>
                </Card>
                <Card className="p-4 bg-card border-border">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-primary" />
                        <div>
                            <p className="text-xs text-muted-foreground">Today's Trades</p>
                            <p className="text-xl font-bold">12</p>
                        </div>
                    </div>
                </Card>
            </div>

            <Tabs defaultValue="positions" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="positions">Active Positions</TabsTrigger>
                    <TabsTrigger value="order">Place Order</TabsTrigger>
                </TabsList>

                {/* Active Positions Tab */}
                <TabsContent value="positions" className="space-y-3">
                    {positions.length === 0 ? (
                        <Card className="p-8 text-center border-border bg-card">
                            <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                            <p className="text-muted-foreground">No active positions</p>
                        </Card>
                    ) : (
                        positions.map(position => (
                            <Card key={position.id} className={`p-4 border-border ${position.pnl >= 0 ? 'bg-success/5 border-success/20' : 'bg-destructive/5 border-destructive/20'}`}>
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <Badge variant={position.type === "BUY" ? "default" : "destructive"} className="font-bold">
                                            {position.type}
                                        </Badge>
                                        <div>
                                            <p className="font-bold text-lg">{position.symbol}</p>
                                            <p className="text-xs text-muted-foreground flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {position.openTime.toLocaleTimeString()}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className={`text-xl font-bold ${position.pnl >= 0 ? 'text-success' : 'text-destructive'}`}>
                                            ${position.pnl.toFixed(2)}
                                        </p>
                                        <p className={`text-sm ${position.pnl >= 0 ? 'text-success' : 'text-destructive'}`}>
                                            {position.pnl >= 0 ? '+' : ''}{position.pnlPercent.toFixed(2)}%
                                        </p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3 text-sm">
                                    <div>
                                        <p className="text-xs text-muted-foreground">Lot Size</p>
                                        <p className="font-mono font-bold">{position.lotSize}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Entry</p>
                                        <p className="font-mono font-bold">${position.entryPrice.toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Current</p>
                                        <p className="font-mono font-bold">${position.currentPrice.toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Status</p>
                                        <Badge variant="outline" className="text-xs">
                                            {position.status}
                                        </Badge>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                                    <div className="flex items-center gap-2">
                                        <TrendingDown className="w-3 h-3 text-destructive" />
                                        <div>
                                            <p className="text-xs text-muted-foreground">Stop Loss</p>
                                            <p className="font-mono text-destructive font-bold">${position.stopLoss.toLocaleString()}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <TrendingUp className="w-3 h-3 text-success" />
                                        <div>
                                            <p className="text-xs text-muted-foreground">Take Profit</p>
                                            <p className="font-mono text-success font-bold">${position.takeProfit.toLocaleString()}</p>
                                        </div>
                                    </div>
                                </div>

                                <Button
                                    onClick={() => handleClosePosition(position.id)}
                                    variant="outline"
                                    size="sm"
                                    className="w-full"
                                >
                                    Close Position
                                </Button>
                            </Card>
                        ))
                    )}
                </TabsContent>

                {/* Place Order Tab */}
                <TabsContent value="order">
                    <Card className="p-6 border-border bg-card">
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Symbol</Label>
                                    <Select value={orderForm.symbol} onValueChange={(v) => setOrderForm(prev => ({ ...prev, symbol: v }))}>
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="BTCUSDT">BTC/USDT</SelectItem>
                                            <SelectItem value="ETHUSDT">ETH/USDT</SelectItem>
                                            <SelectItem value="BNBUSDT">BNB/USDT</SelectItem>
                                            <SelectItem value="SOLUSDT">SOL/USDT</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label>Order Type</Label>
                                    <Select value={orderForm.orderType} onValueChange={(v: any) => setOrderForm(prev => ({ ...prev, orderType: v }))}>
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="MARKET">Market</SelectItem>
                                            <SelectItem value="LIMIT">Limit</SelectItem>
                                            <SelectItem value="STOP">Stop</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label>Lot Size</Label>
                                <Input
                                    type="number"
                                    step="0.01"
                                    value={orderForm.lotSize}
                                    onChange={(e) => setOrderForm(prev => ({ ...prev, lotSize: parseFloat(e.target.value) }))}
                                    placeholder="0.1"
                                />
                            </div>

                            {orderForm.orderType !== "MARKET" && (
                                <div className="space-y-2">
                                    <Label>Limit Price</Label>
                                    <Input
                                        type="number"
                                        value={orderForm.limitPrice || ''}
                                        onChange={(e) => setOrderForm(prev => ({ ...prev, limitPrice: parseFloat(e.target.value) }))}
                                        placeholder={currentPrice.toString()}
                                    />
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Stop Loss</Label>
                                    <Input
                                        type="number"
                                        value={orderForm.stopLoss || ''}
                                        onChange={(e) => setOrderForm(prev => ({ ...prev, stopLoss: parseFloat(e.target.value) }))}
                                        placeholder={(currentPrice * 0.98).toFixed(2)}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label>Take Profit</Label>
                                    <Input
                                        type="number"
                                        value={orderForm.takeProfit || ''}
                                        onChange={(e) => setOrderForm(prev => ({ ...prev, takeProfit: parseFloat(e.target.value) }))}
                                        placeholder={(currentPrice * 1.04).toFixed(2)}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3 pt-4">
                                <Button
                                    onClick={() => {
                                        setOrderForm(prev => ({ ...prev, type: "BUY" }));
                                        handlePlaceOrder();
                                    }}
                                    className="bg-success hover:bg-success/90 text-white"
                                >
                                    <TrendingUp className="w-4 h-4 mr-2" />
                                    BUY
                                </Button>
                                <Button
                                    onClick={() => {
                                        setOrderForm(prev => ({ ...prev, type: "SELL" }));
                                        handlePlaceOrder();
                                    }}
                                    className="bg-destructive hover:bg-destructive/90 text-white"
                                >
                                    <TrendingDown className="w-4 h-4 mr-2" />
                                    SELL
                                </Button>
                            </div>
                        </div>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
};
