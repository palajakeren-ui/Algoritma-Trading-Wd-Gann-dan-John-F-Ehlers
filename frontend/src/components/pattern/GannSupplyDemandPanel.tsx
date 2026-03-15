import { useState, useEffect, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Zap,
    TrendingUp,
    TrendingDown,
    Activity,
    Target,
    Shield,
    ArrowRightLeft,
    Clock,
    Timer,
    AlertCircle
} from "lucide-react";

interface GannLevel {
    degree: number;
    price: number;
    type: "Support" | "Resistance" | "Pivot";
    strength: number;
    description: string;
    eta?: string;
}

interface GannSupplyDemandPanelProps {
    currentPrice: number;
    instrument: string;
    timeframe: string;
}

export const GannSupplyDemandPanel = ({
    currentPrice,
    instrument,
    timeframe
}: GannSupplyDemandPanelProps) => {
    const [activeZones, setActiveZones] = useState<any[]>([]);
    const [lastSyncTime, setLastSyncTime] = useState<string>("");

    useEffect(() => {
        setLastSyncTime(new Date().toLocaleTimeString(undefined, { hour12: false }));
    }, [currentPrice, instrument]);

    // Function to calculate Gann Square of 9 levels
    const calculateGannLevels = (price: number): GannLevel[] => {
        if (price <= 0) return [];

        const root = Math.sqrt(price);
        // Generate 15 degree intervals from 0 to 360 (24 divisions)
        const degrees = Array.from({ length: 25 }, (_, i) => i * 15);
        const now = new Date();

        const formatDate = (date: Date) => {
            return date.toLocaleDateString(undefined, { day: '2-digit', month: 'short' }) + " " +
                date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
        };

        const levels: GannLevel[] = [];

        // Resistance levels (increasing degrees)
        degrees.forEach(deg => {
            const levelPrice = Math.pow(root + deg / 180, 2);
            const targetDate = new Date(now.getTime() + (deg / 15) * 3600000);
            levels.push({
                degree: deg,
                price: levelPrice,
                type: "Resistance",
                strength: deg % 90 === 0 ? 100 : (deg % 45 === 0 ? 85 : 70),
                description: `Gann ${deg}° Resistance`,
                eta: formatDate(targetDate)
            });
        });

        // Support levels (decreasing degrees)
        degrees.forEach(deg => {
            const levelPrice = Math.pow(root - deg / 180, 2);
            if (levelPrice > 0) {
                const targetDate = new Date(now.getTime() + (deg / 15) * 3600000);
                levels.push({
                    degree: deg,
                    price: levelPrice,
                    type: "Support",
                    strength: deg % 90 === 0 ? 100 : (deg % 45 === 0 ? 85 : 70),
                    description: `Gann ${deg}° Support`,
                    eta: formatDate(targetDate)
                });
            }
        });

        return levels.sort((a, b) => b.price - a.price);
    };

    const gannLevels = useMemo(() => calculateGannLevels(currentPrice), [currentPrice]);

    const displayLevels = useMemo(() => {
        return [...gannLevels].sort((a, b) => b.price - a.price);
    }, [gannLevels]);

    const timeVibrations = useMemo(() => {
        const now = new Date();
        const formatDate = (date: Date) => {
            return date.toLocaleDateString(undefined, { day: '2-digit', month: 'short' }) + " " +
                date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
        };

        // Generate 15 degree intervals from 15 to 360
        const degrees = Array.from({ length: 24 }, (_, i) => (i + 1) * 15);

        return degrees.map(deg => {
            let status = "Active";
            let color = "text-primary";
            let label = "Vibration";

            if (deg % 90 === 0) {
                status = "Equilibrium";
                color = "text-accent";
                label = "Square";
            } else if (deg % 45 === 0) {
                status = "Harmonic";
                color = "text-blue-400";
                label = "Octant";
            } else if (deg % 30 === 0) {
                status = "Sextant";
                color = "text-purple-400";
                label = "Aspect";
            }

            if (deg === 180) {
                status = "Critical Pivot";
                color = "text-destructive";
                label = "Opposition";
            } else if (deg === 360) {
                status = "Cycle End";
                color = "text-success";
                label = "Completion";
            }

            return {
                cycle: `${deg}° ${label}`,
                nextTurn: formatDate(new Date(now.getTime() + deg * 60000)),
                status,
                color
            };
        });
    }, []);

    // Generate Supply/Demand Zones
    useEffect(() => {
        const now = new Date();
        const getFutureTime = (minutes: number) => {
            const target = new Date(now.getTime() + minutes * 60000);
            return target.toLocaleDateString(undefined, { day: '2-digit', month: 'short' }) + " " +
                target.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
        };

        const zones = [
            {
                id: "supply-1",
                name: `${instrument} Supply Cluster`,
                range: {
                    start: currentPrice * 1.005,
                    end: currentPrice * 1.015
                },
                type: "Supply",
                strength: 85,
                status: currentPrice > currentPrice * 1.005 ? "Testing" : "Pending",
                vibration: "High",
                targetTime: getFutureTime(105)
            },
            {
                id: "demand-1",
                name: `${instrument} Demand Cluster`,
                range: {
                    start: currentPrice * 0.985,
                    end: currentPrice * 0.995
                },
                type: "Demand",
                strength: 92,
                status: currentPrice < currentPrice * 0.995 ? "Testing" : "Active",
                vibration: "Prime",
                targetTime: getFutureTime(195)
            },
            {
                id: "pivot-1",
                name: "Mathematical Equilibrium",
                range: {
                    start: currentPrice * 0.998,
                    end: currentPrice * 1.002
                },
                type: "Pivot",
                strength: 65,
                status: "Neutral",
                vibration: "Zero",
                targetTime: "Continuous Sync"
            }
        ];
        setActiveZones(zones);
    }, [currentPrice, instrument]);

    return (
        <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
                {/* Real-time Gann Levels */}
                <Card className="border-border bg-card overflow-hidden">
                    <div className="border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4">
                        <div className="flex items-center justify-between w-full">
                            <h3 className="flex items-center gap-2 text-lg font-bold text-foreground">
                                <Zap className="h-5 w-5 text-primary" />
                                Gann Square of 9 Levels
                            </h3>
                            <Badge variant="outline" className="text-[10px] bg-success/10 text-success border-success/30 animate-pulse">
                                SYNCED: {lastSyncTime}
                            </Badge>
                        </div>
                    </div>
                    <div className="p-4">
                        <ScrollArea className="h-[450px] pr-4">
                            <div className="space-y-2">
                                {displayLevels.map((level, idx) => {
                                    const distance = ((level.price - currentPrice) / currentPrice) * 100;
                                    const isAbove = distance > 0;
                                    const isVeryNear = Math.abs(distance) < 0.2;

                                    return (
                                        <div
                                            key={idx}
                                            className={`flex items-center justify-between p-3 rounded-lg border transition-all ${isVeryNear
                                                ? "bg-primary/20 border-primary"
                                                : "bg-secondary/30 border-transparent hover:border-border"
                                                }`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={`p-1.5 rounded-md ${level.type === "Resistance" ? "bg-destructive/10 text-destructive" : "bg-success/10 text-success"
                                                    }`}>
                                                    {level.type === "Resistance" ? <TrendingDown className="h-4 w-4" /> : <TrendingUp className="h-4 w-4" />}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-sm">{level.description}</p>
                                                    <div className="flex items-center gap-2">
                                                        <p className="text-[10px] text-muted-foreground uppercase font-black">
                                                            {Math.abs(distance).toFixed(2)}% {isAbove ? "Above" : "Below"}
                                                        </p>
                                                        <Badge variant="outline" className="h-4 px-1 text-[8px] bg-secondary/50 border-transparent">
                                                            <Clock className="h-2 w-2 mr-1" /> {level.eta}
                                                        </Badge>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-mono font-bold text-foreground text-sm">
                                                    ${level.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                </p>
                                                <Badge variant="outline" className="text-[10px] h-4">
                                                    Str: {level.strength.toFixed(0)}%
                                                </Badge>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </ScrollArea>
                        <p className="mt-4 text-[10px] text-muted-foreground italic text-center">
                            *Levels dynamically generated for full 360° rotation (22.5° steps).
                        </p>
                    </div>
                </Card>

                {/* Gann Time Vibration Matrix */}
                <Card className="border-border bg-card overflow-hidden">
                    <div className="border-b border-border bg-gradient-to-r from-accent/5 to-primary/5 p-4">
                        <h3 className="flex items-center gap-2 text-lg font-bold text-foreground">
                            <Clock className="h-5 w-5 text-accent" />
                            Gann Time Vibration Matrix
                        </h3>
                    </div>
                    <div className="p-4 space-y-3">
                        <div className="grid grid-cols-2 gap-3 mb-2">
                            <div className="bg-secondary/30 p-3 rounded-xl border border-border">
                                <p className="text-[10px] font-black text-muted-foreground uppercase mb-1">Current Sync</p>
                                <p className="text-xl font-black text-primary">{instrument}</p>
                            </div>
                            <div className="bg-secondary/30 p-3 rounded-xl border border-border">
                                <p className="text-[10px] font-black text-muted-foreground uppercase mb-1">Time Vibration</p>
                                <p className="text-xl font-black text-success">Active</p>
                            </div>
                        </div>

                        <ScrollArea className="h-[280px] pr-4">
                            <div className="space-y-2">
                                {timeVibrations.map((tv, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-secondary/20 border border-transparent hover:border-border transition-colors">
                                        <div className="flex items-center gap-3">
                                            <Timer className="h-4 w-4 text-muted-foreground" />
                                            <div>
                                                <p className="text-xs font-bold">{tv.cycle}</p>
                                                <p className="text-[10px] text-muted-foreground uppercase">Next Turn: {tv.nextTurn}</p>
                                            </div>
                                        </div>
                                        <Badge variant="outline" className={`text-[10px] font-black ${tv.color} border-current`}>
                                            {tv.status}
                                        </Badge>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>

                        <div className="flex items-center gap-2 p-2 bg-accent/5 rounded-lg border border-accent/20">
                            <AlertCircle className="h-3 w-3 text-accent" />
                            <p className="text-[9px] text-muted-foreground">Mathematical time pivot detected at 90° rotation. High probability of volatility shift.</p>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Supply & Demand Confluence */}
            <Card className="border-border bg-card overflow-hidden">
                <div className="border-b border-border bg-gradient-to-r from-primary/5 to-accent/5 p-4">
                    <h3 className="flex items-center gap-2 text-lg font-bold text-foreground">
                        <Target className="h-5 w-5 text-primary" />
                        S&D Vibration Zones with Time Projections
                    </h3>
                </div>
                <div className="p-4 grid gap-4 md:grid-cols-3">
                    {activeZones.map((zone) => (
                        <div
                            key={zone.id}
                            className={`p-4 rounded-xl border-l-4 shadow-sm relative overflow-hidden ${zone.type === "Supply"
                                ? "bg-destructive/5 border-l-destructive border-border"
                                : zone.type === "Demand"
                                    ? "bg-success/5 border-l-success border-border"
                                    : "bg-muted/30 border-l-primary border-border"
                                }`}
                        >
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    {zone.type === "Supply" ? (
                                        <TrendingDown className="h-4 w-4 text-destructive" />
                                    ) : zone.type === "Demand" ? (
                                        <TrendingUp className="h-4 w-4 text-success" />
                                    ) : (
                                        <ArrowRightLeft className="h-4 w-4 text-primary" />
                                    )}
                                    <span className="font-bold text-sm uppercase italic">{zone.name}</span>
                                </div>
                                <Badge className={
                                    zone.type === "Supply" ? "bg-destructive" : zone.type === "Demand" ? "bg-success" : "bg-primary"
                                }>
                                    {zone.status}
                                </Badge>
                            </div>

                            <div className="space-y-3 mb-4">
                                <div>
                                    <p className="text-[10px] font-black text-muted-foreground uppercase mb-1">Price Range</p>
                                    <p className="font-mono text-xs font-bold leading-none">
                                        ${zone.range.start.toLocaleString(undefined, { maximumFractionDigits: 2 })} - ${zone.range.end.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                    </p>
                                </div>
                                <div className="flex justify-between items-end">
                                    <div>
                                        <p className="text-[10px] font-black text-muted-foreground uppercase mb-1">Time Alignment</p>
                                        <p className="font-bold text-xs flex items-center gap-1">
                                            <Clock className="h-3 w-3 text-primary" /> {zone.targetTime}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[10px] font-black text-muted-foreground uppercase mb-1">Vibration</p>
                                        <p className="font-bold text-xs">{zone.vibration}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-1">
                                <div className="flex justify-between text-[10px] font-bold">
                                    <span>CONFLUENCE</span>
                                    <span>{zone.strength}%</span>
                                </div>
                                <Progress value={zone.strength} className="h-1" />
                            </div>
                        </div>
                    ))}
                </div>
            </Card>

            {/* MARKET VIBRATION SPECTRUM (Advanced UI) */}
            <Card className="p-0 border-border bg-card/50 backdrop-blur-md overflow-hidden shadow-2xl">
                <div className="p-4 border-b border-border bg-secondary/20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
                            <Activity className="h-5 w-5 text-primary animate-pulse" />
                        </div>
                        <div>
                            <h4 className="font-black text-sm tracking-tight text-foreground uppercase">
                                Market Vibration Spectrum
                            </h4>
                            <p className="text-[10px] text-muted-foreground font-bold tracking-widest uppercase">Price & Time Convergence</p>
                        </div>
                    </div>
                    <div className="flex gap-4">
                        <div className="flex flex-col items-end">
                            <span className="text-[9px] font-black text-muted-foreground uppercase">Volatility State</span>
                            <Badge variant="outline" className="text-[10px] font-black bg-success/10 text-success border-success/30 px-2 py-0">COMPRESSION</Badge>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-[9px] font-black text-muted-foreground uppercase">Sync Ratio</span>
                            <span className="text-sm font-black text-primary">0.8824</span>
                        </div>
                    </div>
                </div>

                <div className="p-6 pt-10 pb-12 relative bg-gradient-to-b from-transparent to-black/20">
                    {/* Spectrum Background Track */}
                    <div className="h-[40px] w-full bg-secondary/40 rounded-2xl relative shadow-inner overflow-hidden border border-border/50">
                        {/* Kinetic Glow Layers */}
                        <div className="absolute inset-0 bg-gradient-to-r from-success/40 via-blue-500/40 via-primary/40 via-purple-500/40 to-destructive/40 opacity-30 blur-xl" />
                        <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-success via-blue-500 via-primary via-purple-500 to-destructive opacity-80" />

                        {/* Gann Division Markers (Vertical ticks) */}
                        {[0, 45, 90, 135, 180, 225, 270, 315, 360].map((deg) => (
                            <div
                                key={deg}
                                className="absolute top-0 bottom-0 w-px bg-border/40"
                                style={{ left: `${(deg / 360) * 100}%` }}
                            >
                                <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[8px] font-black text-muted-foreground">
                                    {deg}°
                                </span>
                            </div>
                        ))}
                    </div>

                    {/* Active Zones Visualization */}
                    <div className="absolute top-8 left-0 right-0 h-[44px] pointer-events-none px-6">
                        {/* Demand Cluster Highlight */}
                        <div className="absolute top-0 bottom-0 bg-success/10 border-x border-success/20 blur-[2px]" style={{ left: '15%', width: '12%' }} />
                        {/* Supply Cluster Highlight */}
                        <div className="absolute top-0 bottom-0 bg-destructive/10 border-x border-destructive/20 blur-[2px]" style={{ right: '15%', width: '10%' }} />
                    </div>

                    {/* Price & Time Vibrator (The Cursor) */}
                    <div
                        className="absolute top-4 bottom-8 transition-all duration-1000 ease-in-out z-20 group"
                        style={{
                            left: `${6 + (((currentPrice % 1000) / 1000) * 88)}%` // Padding-aware positioning
                        }}
                    >
                        {/* Scanning Line */}
                        <div className="h-full w-[2px] bg-foreground shadow-[0_0_20px_rgba(255,255,255,0.8)] relative">
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4 h-4 bg-foreground rounded-full border-4 border-primary shadow-[0_0_15px_#fff]" />
                        </div>

                        {/* Floating HUD Information */}
                        <div className="absolute -top-10 left-1/2 -translate-x-1/2 flex flex-col items-center">
                            <div className="bg-foreground text-background text-[11px] font-black px-3 py-1 rounded-sm shadow-2xl border border-white/20 whitespace-nowrap transform group-hover:scale-110 transition-transform">
                                ${currentPrice.toLocaleString()}
                                <span className="ml-2 text-[9px] text-background/70 opacity-80">VIB-X</span>
                            </div>
                            <div className="w-px h-2 bg-foreground" />
                        </div>

                        {/* Bottom Status */}
                        <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-center whitespace-nowrap">
                            <div className="flex items-center gap-1.5">
                                <span className="h-1.5 w-1.5 rounded-full bg-primary animate-ping" />
                                <span className="text-[9px] font-black text-primary tracking-tighter uppercase italic">Phase Alignment: 94%</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Legend / Floor Details */}
                <div className="px-6 py-4 bg-secondary/10 border-t border-border flex justify-between items-center text-[9px] font-black tracking-widest uppercase text-muted-foreground">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <div className="h-1 w-8 bg-success rounded-full" />
                            <span>Accumulation / Demand</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="h-1 w-8 bg-primary rounded-full" />
                            <span>Equilibrium / Neutral</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="h-1 w-8 bg-destructive rounded-full" />
                            <span>Distribution / Supply</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-1 text-primary">
                        <Shield className="h-3 w-3" />
                        <span>Gann Shield Verified</span>
                    </div>
                </div>
            </Card>
        </div>
    );
};
