import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Maximize2, Minimize2, AlertCircle, Zap, Clock } from "lucide-react";

interface GannHighLowPanelProps {
    currentPrice: number;
    symbol: string;
}

export const GannHighLowPanel = ({ currentPrice, symbol }: GannHighLowPanelProps) => {
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    // Mock data calculations based on the symbol and current price
    // In a real app, these would come from an API

    const longTermATH = currentPrice * 1.42;
    const longTermATL = currentPrice * 0.28;
    const shortTermATH = currentPrice * 1.08;
    const shortTermATL = currentPrice * 0.92;

    const calculateGannLevels = (price: number) => {
        const sqrt = Math.sqrt(price);
        return {
            sq9: Math.pow(sqrt + 0.125, 2), // 45 degrees
            sq9Major: Math.pow(sqrt + 0.25, 2), // 90 degrees
            sq9Cycle: Math.pow(sqrt + 2, 2), // 360 degrees
        };
    };

    const calculateVibrationTime = (price: number, seed: number) => {
        const timeOffset = (price % 365) * 24 * 60 * 60 * 1000;
        const resonance = new Date(new Date().getFullYear(), 0, 1).getTime() + timeOffset;
        const finalDate = new Date(resonance);
        // Ensure some variety based on the seed (sq offset)
        finalDate.setHours((finalDate.getHours() + seed) % 24);
        finalDate.setMinutes((finalDate.getMinutes() + seed * 7) % 60);
        finalDate.setSeconds((finalDate.getSeconds() + seed * 13) % 60);
        return finalDate;
    };

    const levels = {
        ltAth: {
            ...calculateGannLevels(longTermATH),
            time90: calculateVibrationTime(longTermATH, 90),
            time360: calculateVibrationTime(longTermATH, 360)
        },
        ltAtl: {
            ...calculateGannLevels(longTermATL),
            time90: calculateVibrationTime(longTermATL, 90),
            timeBase: calculateVibrationTime(longTermATL, 45)
        },
        stAth: {
            ...calculateGannLevels(shortTermATH),
            timeTarget: calculateVibrationTime(shortTermATH, 144)
        },
        stAtl: {
            ...calculateGannLevels(shortTermATL),
            timeFloor: calculateVibrationTime(shortTermATL, 144)
        },
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Long-Term ATH */}
            <Card className="p-4 bg-gradient-to-br from-primary/10 to-transparent border-primary/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                    <TrendingUp className="w-12 h-12 text-primary" />
                </div>
                <div className="relative z-10">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold text-primary flex items-center gap-1 font-mono bg-primary/10 px-2 py-0.5 rounded">
                            <Clock className="w-3.5 h-3.5" />
                            {currentTime.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                        <Badge variant="outline" className="text-xs border-primary/30 text-primary px-2">ATH LONG</Badge>
                    </div>
                    <h4 className="text-2xl font-black text-foreground font-mono mb-4 tracking-tighter">${longTermATH.toLocaleString(undefined, { maximumFractionDigits: 2 })}</h4>
                    <div className="mt-4 space-y-3">
                        <div className="flex justify-between items-center bg-background/40 p-2 rounded border border-primary/10">
                            <div className="flex flex-col">
                                <span className="text-muted-foreground uppercase text-[10px] font-black tracking-wider">90° Resonance</span>
                                <span className="text-sm text-primary font-bold font-mono">
                                    {levels.ltAth.time90.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="text-[9px] text-muted-foreground">{levels.ltAth.time90.toLocaleDateString()}</span>
                            </div>
                            <span className="text-lg font-black text-primary">${levels.ltAth.sq9Major.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex justify-between items-center bg-background/40 p-2 rounded border border-accent/10">
                            <div className="flex flex-col">
                                <span className="text-muted-foreground uppercase text-[10px] font-black tracking-wider">Full Cycle (360°)</span>
                                <span className="text-sm text-accent font-bold font-mono">
                                    {levels.ltAth.time360.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="text-[9px] text-muted-foreground">{levels.ltAth.time360.toLocaleDateString()}</span>
                            </div>
                            <span className="text-lg font-black text-accent">${levels.ltAth.sq9Cycle.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                        </div>
                    </div>
                </div>
            </Card>

            {/* Long-Term ATL */}
            <Card className="p-4 bg-gradient-to-br from-destructive/10 to-transparent border-destructive/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                    <TrendingDown className="w-12 h-12 text-destructive" />
                </div>
                <div className="relative z-10">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold text-destructive flex items-center gap-1 font-mono bg-destructive/10 px-2 py-0.5 rounded">
                            <Clock className="w-3.5 h-3.5" />
                            {currentTime.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                        <Badge variant="outline" className="text-xs border-destructive/30 text-destructive px-2">ATL LONG</Badge>
                    </div>
                    <h4 className="text-2xl font-black text-foreground font-mono mb-4 tracking-tighter">${longTermATL.toLocaleString(undefined, { maximumFractionDigits: 2 })}</h4>
                    <div className="mt-4 space-y-3">
                        <div className="flex justify-between items-center bg-background/40 p-2 rounded border border-destructive/10">
                            <div className="flex flex-col">
                                <span className="text-muted-foreground uppercase text-[10px] font-black tracking-wider">90° Resonance</span>
                                <span className="text-sm text-destructive font-bold font-mono">
                                    {levels.ltAtl.time90.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="text-[9px] text-muted-foreground">{levels.ltAtl.time90.toLocaleDateString()}</span>
                            </div>
                            <span className="text-lg font-black text-destructive">${levels.ltAtl.sq9Major.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex justify-between items-center bg-background/40 p-2 rounded border border-primary/10">
                            <div className="flex flex-col">
                                <span className="text-muted-foreground uppercase text-[10px] font-black tracking-wider">Support Base</span>
                                <span className="text-sm text-primary font-bold font-mono">
                                    {levels.ltAtl.timeBase.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="text-[9px] text-muted-foreground">{levels.ltAtl.timeBase.toLocaleDateString()}</span>
                            </div>
                            <span className="text-lg font-black text-primary">${levels.ltAtl.sq9.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                        </div>
                    </div>
                </div>
            </Card>

            {/* Short-Term ATH */}
            <Card className="p-4 bg-gradient-to-br from-accent/10 to-transparent border-accent/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                    <Maximize2 className="w-12 h-12 text-accent" />
                </div>
                <div className="relative z-10">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold text-accent flex items-center gap-1 font-mono bg-accent/10 px-2 py-0.5 rounded">
                            <Clock className="w-3.5 h-3.5" />
                            {currentTime.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                        <Badge variant="outline" className="text-xs border-accent/30 text-accent px-2">ATH SHORT</Badge>
                    </div>
                    <h4 className="text-2xl font-black text-foreground font-mono mb-4 tracking-tighter">${shortTermATH.toLocaleString(undefined, { maximumFractionDigits: 2 })}</h4>
                    <div className="mt-4 space-y-3">
                        <div className="flex justify-between items-center bg-background/40 p-2 rounded border border-accent/10">
                            <div className="flex flex-col">
                                <span className="text-muted-foreground uppercase text-[10px] font-black tracking-wider">Vibration Target</span>
                                <span className="text-sm text-accent font-bold font-mono">
                                    {levels.stAth.timeTarget.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="text-[9px] text-muted-foreground">{levels.stAth.timeTarget.toLocaleDateString()}</span>
                            </div>
                            <span className="text-lg font-black text-accent">${levels.stAth.sq9Major.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex justify-between items-center p-2">
                            <span className="text-xs font-bold text-muted-foreground uppercase">Price/Time Gap</span>
                            <span className="text-lg font-black text-success">+{((shortTermATH / currentPrice - 1) * 100).toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
            </Card>

            {/* Short-Term ATL */}
            <Card className="p-4 bg-gradient-to-br from-warning/10 to-transparent border-warning/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                    <Minimize2 className="w-12 h-12 text-warning" />
                </div>
                <div className="relative z-10">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold text-warning flex items-center gap-1 font-mono bg-warning/10 px-2 py-0.5 rounded">
                            <Clock className="w-3.5 h-3.5" />
                            {currentTime.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                        <Badge variant="outline" className="text-xs border-warning/30 text-warning px-2">ATL SHORT</Badge>
                    </div>
                    <h4 className="text-2xl font-black text-foreground font-mono mb-4 tracking-tighter">${shortTermATL.toLocaleString(undefined, { maximumFractionDigits: 2 })}</h4>
                    <div className="mt-4 space-y-3">
                        <div className="flex justify-between items-center bg-background/40 p-2 rounded border border-warning/10">
                            <div className="flex flex-col">
                                <span className="text-muted-foreground uppercase text-[10px] font-black tracking-wider">Vibration Floor</span>
                                <span className="text-sm text-warning font-bold font-mono">
                                    {levels.stAtl.timeFloor.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="text-[9px] text-muted-foreground">{levels.stAtl.timeFloor.toLocaleDateString()}</span>
                            </div>
                            <span className="text-lg font-black text-warning">${levels.stAtl.sq9Major.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex justify-between items-center p-2">
                            <span className="text-xs font-bold text-muted-foreground uppercase">Price/Time Gap</span>
                            <span className="text-lg font-black text-destructive">{((shortTermATL / currentPrice - 1) * 100).toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
};
