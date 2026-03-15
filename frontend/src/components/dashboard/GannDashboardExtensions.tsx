import { useState, useMemo, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Activity,
    TrendingUp,
    Layers,
    Zap,
    Compass,
    Maximize2,
    Target,
    ArrowUpRight,
    ArrowDownRight,
    RefreshCw,
    Clock,
    Waves,
    Calendar,
    ChevronRight
} from "lucide-react";
import {
    calculateGannSquareByConstant,
    calculateGannWaveLevels,
    calculateGannAngles,
    calculateFibonacciLevels
} from "@/lib/gannCalculations";
import { cn } from "@/lib/utils";

interface GannDashboardExtensionsProps {
    currentPrice: number;
}

export const GannDashboardExtensions = ({ currentPrice }: GannDashboardExtensionsProps) => {
    const [activeSquare, setActiveSquare] = useState<string>("144");
    const [rotationAngle, setRotationAngle] = useState(0);

    // Rotate based on price heartbeat
    useEffect(() => {
        setRotationAngle(prev => (prev + 5) % 360);
    }, [currentPrice]);

    const getTimeRemaining = (targetDate: string) => {
        const total = Date.parse(targetDate) - Date.now();
        if (total <= 0) return "Active Now";
        const minutes = Math.floor((total / 1000 / 60) % 60);
        const hours = Math.floor((total / (1000 * 60 * 60)) % 24);
        const days = Math.floor(total / (1000 * 60 * 60 * 24));
        return `${days}h ${hours}j ${minutes}m`; // Using Indonesian labels as requested or context suggests
    };

    const constants = [
        { id: "24.52", label: "Vibration 24.52", value: 24.52, type: "Frequency" },
        { id: "90", label: "Cardinal 90", value: 90, type: "Angle" },
        { id: "144", label: "Square of 144", value: 144, type: "Time/Price" },
        { id: "360", label: "Full Cycle 360", value: 360, type: "Circle" },
    ];

    const activeConstant = useMemo(() =>
        constants.find(c => c.id === activeSquare) || constants[2],
        [activeSquare]);

    const squareLevels = useMemo(() =>
        calculateGannSquareByConstant(currentPrice, activeConstant.value),
        [currentPrice, activeConstant]);

    const waveHigh = currentPrice * 1.05;
    const waveLow = currentPrice * 0.95;

    const waveLevels = useMemo(() =>
        calculateGannWaveLevels(waveHigh, waveLow, currentPrice),
        [currentPrice, waveHigh, waveLow]);

    const gannAngles = useMemo(() =>
        calculateGannAngles(currentPrice),
        [currentPrice]);

    const fibLevels = useMemo(() =>
        calculateFibonacciLevels(waveHigh, waveLow),
        [waveHigh, waveLow]);

    const trendState = useMemo(() => {
        // Simple logic for trend based on Fibonacci and price position
        const midPoint = (waveHigh + waveLow) / 2;
        const volatility = (waveHigh - waveLow) / midPoint;

        if (currentPrice > fibLevels.level_618) return "UPTREND";
        if (currentPrice < fibLevels.level_382) return "DOWNTREND";
        return "SIDEWAYS";
    }, [currentPrice, fibLevels, waveHigh, waveLow]);

    return (
        <div className="space-y-6">
            {/* HUD HEADER */}
            <div className="flex flex-col md:flex-row gap-4 items-stretch">
                <Card className="flex-1 p-4 bg-card/40 backdrop-blur-md border-primary/20 relative overflow-hidden flex items-center justify-between group">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent pointer-events-none" />
                    <div className="flex items-center gap-4 relative z-10">
                        <div className="p-3 bg-primary/10 rounded-full animate-pulse">
                            <Compass className="w-6 h-6 text-primary" style={{ transform: `rotate(${rotationAngle}deg)` }} />
                        </div>
                        <div>
                            <Label className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Price Vibration Matrix</Label>
                            <h3 className="text-2xl font-mono font-bold text-foreground">
                                ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </h3>
                        </div>
                    </div>
                    <div className="text-right relative z-10">
                        <Badge className="bg-success/20 text-success border-success/30 animate-in fade-in zoom-in duration-300">
                            <Activity className="w-3 h-3 mr-1" /> ACTIVE STREAM
                        </Badge>
                        <p className="text-[9px] text-muted-foreground mt-2 font-mono uppercase">Synchronization Latency: 42ms</p>
                    </div>
                </Card>

                <Card className="p-2 bg-secondary/20 border-border/50 flex items-center gap-1">
                    {constants.map((sq) => (
                        <Button
                            key={sq.id}
                            variant={activeSquare === sq.id ? "default" : "ghost"}
                            size="sm"
                            onClick={() => setActiveSquare(sq.id)}
                            className={cn(
                                "h-full px-4 flex flex-col items-center justify-center gap-1 transition-all",
                                activeSquare === sq.id ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "hover:bg-primary/10"
                            )}
                        >
                            <span className="text-[10px] font-bold uppercase">{sq.id}</span>
                            <span className="text-[8px] opacity-60 uppercase tracking-tighter">{sq.type}</span>
                        </Button>
                    ))}
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* MAIN RADAR VIEW */}
                <Card className="lg:col-span-8 p-6 bg-card/30 border-border/50 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                        <Layers className="w-64 h-64 text-foreground" />
                    </div>

                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-1.5 h-6 bg-primary rounded-full" />
                            <h4 className="text-lg font-bold uppercase tracking-wide">Geometric Projections</h4>
                            <Badge variant="outline" className="text-[10px] uppercase font-mono border-primary/30 text-primary">Constant: {activeConstant.value}</Badge>
                        </div>
                        <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-muted-foreground" />
                            <span className="text-xs font-mono text-muted-foreground">{new Date().toLocaleTimeString()}</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* VIBRATION LEVELS GRID */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <Label className="text-xs text-muted-foreground uppercase font-bold tracking-widest flex items-center gap-2">
                                    <Zap className="w-3 h-3 text-accent" /> Resonance Points (15° Step)
                                </Label>
                                <Badge variant="outline" className="text-[8px] h-4">0° - 360°</Badge>
                            </div>

                            <div className="h-[280px] overflow-y-auto pr-2 custom-scrollbar space-y-1.5 bg-background/20 rounded-lg p-2 border border-border/30">
                                {Object.entries(squareLevels).map(([label, price], idx) => {
                                    const angle = parseInt(label);
                                    const isCardinal = angle % 90 === 0;
                                    const isDiagonal = angle % 45 === 0 && !isCardinal;

                                    return (
                                        <div key={label} className={cn(
                                            "relative group/line cursor-default p-2 rounded transition-colors",
                                            isCardinal ? "bg-primary/10 border border-primary/20" : "hover:bg-white/5"
                                        )}>
                                            <div className="flex justify-between items-center">
                                                <div className="flex items-center gap-2">
                                                    <span className={cn(
                                                        "text-[10px] font-mono font-bold",
                                                        isCardinal ? "text-primary" : "text-muted-foreground"
                                                    )}>{label}</span>
                                                    {isCardinal && <Badge className="h-3 px-1 text-[7px] bg-primary/20 text-primary border-none">CARDINAL</Badge>}
                                                </div>
                                                <span className={cn(
                                                    "text-xs font-mono font-bold",
                                                    isCardinal ? "text-primary" : "text-foreground/90"
                                                )}>${price.toFixed(2)}</span>
                                            </div>
                                            <div className="mt-1 flex gap-1">
                                                <div className={cn(
                                                    "h-0.5 rounded-full transition-all",
                                                    isCardinal ? "bg-primary w-full" : "bg-muted/30 w-1/4 group-hover/line:w-1/2"
                                                )} />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            <div className="mt-4 p-3 rounded-xl bg-primary/5 border border-primary/10 flex items-center gap-3">
                                <div className="shrink-0 w-10 h-10 rounded-lg bg-background flex items-center justify-center border border-border">
                                    <Target className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                    <p className="text-[10px] font-bold text-foreground">Geometric Intersection</p>
                                    <p className="text-[9px] text-muted-foreground">High accuracy expected at {activeSquare}° cardinal junctions.</p>
                                </div>
                            </div>
                        </div>

                        {/* RADAR VISUALIZATION (Simplified SVG) */}
                        <div className="relative aspect-square flex items-center justify-center p-4">
                            <svg viewBox="0 0 200 200" className="w-full h-full animate-in zoom-in duration-700">
                                {/* Outer Rings */}
                                <circle cx="100" cy="100" r="95" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-border/30" />
                                <circle cx="100" cy="100" r="70" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-border/30" />
                                <circle cx="100" cy="100" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-border/30" />

                                {/* Cardinal Lines */}
                                <line x1="100" y1="5" x2="100" y2="195" stroke="currentColor" strokeWidth="0.5" className="text-primary/20" />
                                <line x1="5" y1="100" x2="195" y2="100" stroke="currentColor" strokeWidth="0.5" className="text-primary/20" />
                                <line x1="30" y1="30" x2="170" y2="170" stroke="currentColor" strokeWidth="0.5" className="text-border/10" />
                                <line x1="170" y1="30" x2="30" y2="170" stroke="currentColor" strokeWidth="0.5" className="text-border/10" />

                                {/* Dynamic Indicators */}
                                <g style={{ transform: `rotate(${rotationAngle}deg)`, transformOrigin: 'center' }}>
                                    <line x1="100" y1="100" x2="100" y2="5" stroke="currentColor" strokeWidth="1.5" className="text-primary" />
                                    <circle cx="100" cy="5" r="3" className="fill-primary" />
                                </g>

                                {/* Price Points */}
                                {Object.values(squareLevels).map((p, i) => {
                                    const angle = (i * 90 * Math.PI) / 180;
                                    const r = 45 + (i * 15);
                                    const x = 100 + r * Math.cos(angle - Math.PI / 2);
                                    const y = 100 + r * Math.sin(angle - Math.PI / 2);
                                    return (
                                        <g key={i}>
                                            <circle cx={x} cy={y} r="4" className="fill-background stroke-primary" strokeWidth="1" />
                                            <text x={x + 6} y={y + 3} className="text-[5px] fill-muted-foreground font-mono font-bold">${p.toFixed(0)}</text>
                                        </g>
                                    );
                                })}
                            </svg>
                            {/* Center Badge */}
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="w-16 h-16 rounded-full bg-background border-2 border-primary/50 flex flex-col items-center justify-center shadow-2xl shadow-primary/20">
                                    <span className="text-[8px] uppercase tracking-tighter text-muted-foreground">Base</span>
                                    <span className="text-[10px] font-bold text-primary">${currentPrice.toFixed(0)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </Card>

                {/* SIDE PANELS GRID */}
                <div className="lg:col-span-4 space-y-6">
                    {/* GANN WAVE REAL-TIME */}
                    <Card className="p-5 bg-accent/5 border-accent/20 relative overflow-hidden group">
                        <div className="absolute -right-4 -bottom-4 p-8 opacity-5 pointer-events-none group-hover:scale-110 transition-transform">
                            <Waves className="w-24 h-24 text-accent" />
                        </div>

                        <div className="flex items-center justify-between mb-4 relative z-10">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-accent/20 rounded-lg">
                                    <TrendingUp className="w-4 h-4 text-accent" />
                                </div>
                                <div>
                                    <h5 className="text-sm font-bold uppercase tracking-tight">Wave Intelligence</h5>
                                    <p className="text-[9px] text-muted-foreground uppercase font-mono">Gann & Fibonacci Fusion</p>
                                </div>
                            </div>
                            <Badge className={cn(
                                "text-[10px] px-2 py-0.5 font-bold border-none",
                                trendState === "UPTREND" ? "bg-success/20 text-success" :
                                    trendState === "DOWNTREND" ? "bg-destructive/20 text-destructive" :
                                        "bg-amber-500/20 text-amber-500"
                            )}>
                                {trendState}
                            </Badge>
                        </div>

                        <Tabs defaultValue="wave" className="relative z-10">
                            <TabsList className="bg-background/40 w-full mb-3 h-8 p-1">
                                <TabsTrigger value="wave" className="flex-1 text-[9px] uppercase font-bold py-1">Wave</TabsTrigger>
                                <TabsTrigger value="angles" className="flex-1 text-[9px] uppercase font-bold py-1">Angles</TabsTrigger>
                                <TabsTrigger value="fib" className="flex-1 text-[9px] uppercase font-bold py-1">Fib</TabsTrigger>
                            </TabsList>
                            <TabsContent value="wave" className="space-y-4 m-0">
                                <div className="space-y-2">
                                    {Object.entries(waveLevels).map(([label, price], idx) => (
                                        <div key={label} className="p-2 rounded bg-background/30 border border-border/30 hover:bg-background/50 transition-colors flex justify-between items-center">
                                            <span className="text-[9px] text-muted-foreground font-bold uppercase">{label.split(' ').pop()}</span>
                                            <span className="text-xs font-bold text-foreground font-mono">${price.toFixed(2)}</span>
                                        </div>
                                    ))}
                                </div>
                            </TabsContent>
                            <TabsContent value="angles" className="space-y-4 m-0">
                                <div className="grid grid-cols-2 gap-2">
                                    {Object.entries(gannAngles).map(([label, price], idx) => (
                                        <div key={label} className="p-2 rounded bg-primary/5 border border-primary/10 flex flex-col">
                                            <span className="text-[8px] text-primary font-bold">{label} Angle</span>
                                            <span className="text-[11px] font-bold text-foreground font-mono">${(price as number).toFixed(2)}</span>
                                        </div>
                                    ))}
                                </div>
                            </TabsContent>
                            <TabsContent value="fib" className="space-y-4 m-0">
                                <div className="space-y-1.5">
                                    {Object.entries(fibLevels).map(([label, price], idx) => (
                                        <div key={label} className="flex justify-between items-center group/fib">
                                            <span className="text-[10px] font-medium text-muted-foreground">{label.replace('level_', '')}%</span>
                                            <div className="flex-1 mx-3 h-[1px] bg-border/20 group-hover/fib:bg-accent/30 transition-all" />
                                            <span className="text-[10px] font-mono font-bold">${price.toFixed(2)}</span>
                                        </div>
                                    ))}
                                </div>
                            </TabsContent>
                        </Tabs>

                        <div className="mt-4 p-3 rounded-lg bg-background/50 border border-border/50 flex items-center justify-between">
                            <div className="flex flex-col">
                                <span className="text-[8px] uppercase text-muted-foreground font-bold">Resonance Score</span>
                                <span className="text-xs font-bold text-primary">89.4% Synchronized</span>
                            </div>
                            <Button size="icon" variant="ghost" className="h-8 w-8 text-accent hover:text-accent hover:bg-accent/10">
                                <RefreshCw className="w-3.5 h-3.5" />
                            </Button>
                        </div>
                    </Card>

                    {/* CYCLE TIME INFO */}
                    <Card className="p-5 bg-card/50 border-border/50">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="p-2 bg-secondary/30 rounded-lg">
                                <Calendar className="w-4 h-4 text-muted-foreground" />
                            </div>
                            <h5 className="text-sm font-bold uppercase">Time Cycle Projection</h5>
                        </div>

                        <div className="space-y-3">
                            {[
                                { label: "Cycle Bottom", date: "Apr 12, 2026", progress: 75, status: "Critical" },
                                { label: "Vibration Shift", date: "May 19, 2026", progress: 42, status: "Moderate" },
                            ].map((cycle, i) => (
                                <div key={i} className="space-y-1.5">
                                    <div className="flex justify-between items-end">
                                        <span className="text-xs font-semibold">{cycle.label}</span>
                                        <span className="text-[10px] font-mono text-muted-foreground">{cycle.date}</span>
                                    </div>
                                    <Progress value={cycle.progress} className="h-1 bg-secondary/30" />
                                    <div className="flex justify-between items-center text-[9px] text-muted-foreground">
                                        <span>Countdown: {getTimeRemaining(cycle.date)}</span>
                                        <Badge variant="outline" className="h-4 text-[8px] border-warning/30 text-warning">{cycle.status}</Badge>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>
            </div >
        </div >
    );
};
