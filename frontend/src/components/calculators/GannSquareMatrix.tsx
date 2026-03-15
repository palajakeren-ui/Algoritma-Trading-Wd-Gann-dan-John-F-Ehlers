import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import { calculateGannSquareByConstant } from "@/lib/gannCalculations";
import { cn } from "@/lib/utils";
import { Activity, Layers, Target, TrendingUp, Zap, HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface GannSquareMatrixProps {
    currentPrice: number;
}

export const GannSquareMatrix = ({ currentPrice }: GannSquareMatrixProps) => {
    const constants = [24.52, 90, 144, 360];

    const matrixData = useMemo(() => {
        return constants.map(c => ({
            constant: c,
            levels: calculateGannSquareByConstant(currentPrice, c)
        }));
    }, [currentPrice]);

    // Find confluences (levels from different squares that are close)
    const confluences = useMemo(() => {
        const allLevels: Array<{ price: number, label: string, constant: number }> = [];
        matrixData.forEach(data => {
            Object.entries(data.levels).forEach(([label, price]) => {
                // Only consider major angles for confluence to avoid clutter
                const angle = parseInt(label);
                if (angle % 45 === 0) {
                    allLevels.push({ price, label: `${data.constant}:${label}`, constant: data.constant });
                }
            });
        });

        const results: Array<{ price: number, matches: string[] }> = [];
        const sorted = [...allLevels].sort((a, b) => a.price - b.price);

        for (let i = 0; i < sorted.length - 1; i++) {
            const matches = [sorted[i].label];
            let j = i + 1;
            while (j < sorted.length && Math.abs(sorted[j].price - sorted[i].price) < currentPrice * 0.001) {
                matches.push(sorted[j].label);
                j++;
            }
            if (matches.length > 1) {
                results.push({
                    price: matches.reduce((acc, m) => acc + allLevels.find(l => l.label === m)!.price, 0) / matches.length,
                    matches
                });
                i = j - 1;
            }
        }
        return results.sort((a, b) => Math.abs(a.price - currentPrice) - Math.abs(b.price - currentPrice)).slice(0, 5);
    }, [matrixData, currentPrice]);

    return (
        <Card className="p-6 border-border bg-card/50 backdrop-blur-sm overflow-hidden relative">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] pointer-events-none">
                <Layers className="w-64 h-64" />
            </div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
                        <Zap className="w-6 h-6 text-primary animate-pulse" />
                        WD Gann Vibration Matrix
                    </h2>
                    <p className="text-sm text-muted-foreground italic">Multi-Constant Geometric Frequency Analysis</p>
                </div>
                <div className="flex items-center gap-2">
                    <Badge className="bg-primary/20 text-primary border-primary/30">
                        STRATEGY: CONFLUENCE
                    </Badge>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {matrixData.map((data) => (
                    <div key={data.constant} className="space-y-4">
                        <div className="flex items-center justify-between pb-2 border-b border-border/50">
                            <span className="text-sm font-bold text-foreground uppercase tracking-wider">Square of {data.constant}</span>
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="text-xs">Based on {data.constant} unit vibration per cycle.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>

                        <div className="space-y-2">
                            {[0, 90, 180, 270, 360].map(angle => {
                                const label = `${angle}°`;
                                const price = data.levels[label];
                                return (
                                    <div key={angle} className="flex justify-between items-center group/item p-1.5 rounded hover:bg-white/5 transition-colors">
                                        <span className="text-[10px] font-mono font-bold text-muted-foreground group-hover/item:text-primary">{label}</span>
                                        <span className="text-xs font-mono font-bold text-foreground">${price?.toFixed(2)}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6 border-t border-border/50">
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-accent" />
                        <h3 className="text-sm font-bold uppercase tracking-widest text-accent">High-Vibration Confluences</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {confluences.map((conf, idx) => (
                            <div key={idx} className="p-3 rounded-lg bg-accent/5 border border-accent/20 relative group hover:bg-accent/10 transition-all">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-lg font-mono font-bold text-accent">${conf.price.toFixed(2)}</span>
                                    <Badge className="bg-accent/20 text-accent border-none text-[8px] h-4">STRENGTH: {conf.matches.length}X</Badge>
                                </div>
                                <div className="flex flex-wrap gap-1">
                                    {conf.matches.map(m => (
                                        <span key={m} className="text-[8px] bg-background/50 px-1 py-0.5 rounded border border-border/50 text-muted-foreground">
                                            {m}
                                        </span>
                                    ))}
                                </div>
                                <div className="mt-2 h-0.5 w-full bg-accent/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-accent transition-all duration-1000" style={{ width: `${(conf.matches.length / 4) * 100}%` }} />
                                </div>
                            </div>
                        ))}
                        {confluences.length === 0 && (
                            <div className="col-span-full py-8 text-center border-2 border-dashed border-border rounded-lg">
                                <p className="text-xs text-muted-foreground italic">No immediate geometric confluences detected.</p>
                            </div>
                        )}
                    </div>
                </div>

                <Card className="p-4 bg-primary/5 border-primary/20 flex flex-col justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-3">
                            <Activity className="w-4 h-4 text-primary" />
                            <h4 className="text-xs font-bold uppercase">Matrix Intelligence</h4>
                        </div>
                        <p className="text-[10px] text-muted-foreground leading-relaxed">
                            The Vibration Matrix synchronizes four distinct Gann geometric models. When multiple squares project the same price level, it indicates a **Strong Geometric Resonance** where a major trend reversal or breakout is mathematically probable.
                        </p>
                    </div>
                    <div className="mt-4 pt-4 border-t border-primary/10">
                        <div className="flex justify-between text-[10px] font-bold">
                            <span className="text-muted-foreground uppercase">Current Bias</span>
                            <span className="text-success uppercase">Resonant Bullish</span>
                        </div>
                    </div>
                </Card>
            </div>
        </Card>
    );
};
