import { useState, useMemo, useEffect, useRef } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Hexagon,
  Maximize2,
  RefreshCw,
  Target,
  TrendingUp,
  TrendingDown,
  Activity,
  Layers,
  MousePointer2,
  Lock,
  Unlock
} from "lucide-react";
import { cn } from "@/lib/utils";

interface HexagonGeometryChartProps {
  currentPrice: number;
}

const HexagonGeometryChart = ({ currentPrice }: HexagonGeometryChartProps) => {
  const [rotationAngle, setRotationAngle] = useState(0);
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  const [isAutoScanning, setIsAutoScanning] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showAngles, setShowAngles] = useState(true);
  const [athPrice, setAthPrice] = useState<number>(0);
  const [atlPrice, setAtlPrice] = useState<number>(0);
  const [athDate, setAthDate] = useState<string>("");
  const [atlDate, setAtlDate] = useState<string>("");
  const [viewMode, setViewMode] = useState<'live' | 'ath' | 'atl'>('live');
  const [referenceDate, setReferenceDate] = useState<string>(new Date().toISOString().split('T')[0]); // Live/Default

  // Active Reference Date based on mode
  const activeDate = useMemo(() => {
    if (viewMode === 'ath') return athDate || referenceDate;
    if (viewMode === 'atl') return atlDate || referenceDate;
    return referenceDate;
  }, [viewMode, athDate, atlDate, referenceDate]);

  const matrixRef = useRef<HTMLDivElement>(null);



  // Determine calculation base
  const basePrice = useMemo(() => {
    if (viewMode === 'ath') return athPrice || currentPrice; // Fallback if 0 to avoid blank chart initially
    if (viewMode === 'atl') return atlPrice || currentPrice;
    return currentPrice;
  }, [viewMode, athPrice, atlPrice, currentPrice]);

  // Animation Engine
  useEffect(() => {
    let frameId: number;
    const animate = () => {
      if (isAutoScanning) {
        setRotationAngle(prev => (prev + 0.5) % 360);
      }
      frameId = requestAnimationFrame(animate);
    };
    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [isAutoScanning]);

  // Realtime Analysis Stats
  const liveStats = useMemo(() => {
    const angle = rotationAngle % 360;
    const sqrt = Math.sqrt(basePrice);
    const factor = angle / 360;

    // Time Calc (1 deg = 1 day)
    const msPerDay = 24 * 60 * 60 * 1000;
    const targetTime = new Date(activeDate).getTime() + angle * msPerDay;
    const dateObj = new Date(targetTime);

    return {
      date: dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }),
      resistance: Math.pow(sqrt + factor, 2),
      support: Math.pow(sqrt - factor, 2)
    };
  }, [rotationAngle, basePrice, activeDate]);

  // Gann Hexagon Calculations
  const hexagonLevels = useMemo(() => {
    const sqrt = Math.sqrt(basePrice);
    // Full 360 degrees in 15-degree steps as requested
    const steps = [
      0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165,
      180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345, 360
    ];

    return steps.map(angle => {
      const radians = (angle * Math.PI) / 180;
      const factor = angle / 360;
      // Determine node type for visualization hierarchy
      const isHexVertex = angle % 60 === 0;
      const isSquareVertex = angle % 90 === 0;

      // Time Calculation (1 degree = 1 day approx/solar) - Projections
      const date = new Date(activeDate);
      date.setDate(date.getDate() + angle);

      return {
        angle,
        date: date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
        x: 50 + 40 * Math.cos(radians),
        y: 50 + 40 * Math.sin(radians),
        resistance: Math.pow(sqrt + factor, 2),
        support: Math.pow(sqrt - factor, 2),
        label: `${angle}°`,
        isMajor: isHexVertex || isSquareVertex
      };
    });
  }, [basePrice, activeDate]);

  const activeLevel = useMemo(() => {
    if (selectedNode !== null) {
      return hexagonLevels.find(l => l.angle === selectedNode);
    }
    // Find nearest vertex to current rotation
    const normalizedRotation = rotationAngle % 360;
    return hexagonLevels.reduce((prev, curr) => {
      return Math.abs(curr.angle - normalizedRotation) < Math.abs(prev.angle - normalizedRotation) ? curr : prev;
    });
  }, [hexagonLevels, selectedNode, rotationAngle]);

  // Sync scroll with Active Level (Animation)
  useEffect(() => {
    // Only auto-scroll if:
    // 1. Auto-scanning is active (don't fight manual user clicks)
    // 2. We have refs
    if (!isAutoScanning || !activeLevel || !matrixRef.current) return;

    const row = document.getElementById(`matrix-row-${activeLevel.angle}`);
    if (row) {
      const container = matrixRef.current;

      // Use geometric calculation instead of scrollIntoView to prevent 
      // the whole page from jumping (which disturbs user)
      const containerRect = container.getBoundingClientRect();
      const rowRect = row.getBoundingClientRect();
      const relativeTop = rowRect.top - containerRect.top;
      const currentScroll = container.scrollTop;

      // Calculate target to center the element
      const targetScroll = currentScroll + relativeTop - (container.clientHeight / 2) + (row.clientHeight / 2);

      container.scrollTo({
        top: targetScroll,
        behavior: 'smooth'
      });
    }
  }, [activeLevel, isAutoScanning]);

  return (
    <Card className="w-full bg-black/40 border-white/10 backdrop-blur-xl overflow-hidden">
      <CardHeader className="border-b border-white/5 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Hexagon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg font-bold text-white tracking-tight">
                Hexagon Price Geometry
              </CardTitle>
              <p className="text-xs text-muted-foreground font-mono mt-1">
                GANN MASTER CYCLE: {currentPrice.toFixed(2)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 bg-transparent border-white/10 hover:bg-white/5"
              onClick={() => setIsAutoScanning(!isAutoScanning)}
            >
              {isAutoScanning ? <Lock className="w-4 h-4 text-primary" /> : <Unlock className="w-4 h-4 text-muted-foreground" />}
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 bg-transparent border-white/10 hover:bg-white/5"
              onClick={() => setRotationAngle(0)}
            >
              <RefreshCw className="w-4 h-4 text-muted-foreground" />
            </Button>
            <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 font-mono">
              LIVE
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="flex flex-col w-full">

          {/* TOP: VISUALIZATION */}
          <div className="w-full relative p-8 flex items-center justify-center border-b border-white/5 bg-gradient-to-br from-background/50 to-background/20">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent" />

            {/* Main SVG Container */}
            <div className="relative w-full max-w-[700px] aspect-square">
              <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-2xl">
                <defs>
                  <filter id="glow-strong" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                  <linearGradient id="beam-grad" x1="0%" y1="100%" x2="0%" y2="0%">
                    <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0" />
                    <stop offset="50%" stopColor="hsl(var(--primary))" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.1" />
                  </linearGradient>
                  <radialGradient id="center-glow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="transparent" />
                  </radialGradient>
                </defs>

                {/* Background Structure */}
                <circle cx="50" cy="50" r="49" fill="url(#center-glow)" opacity="0.3" />
                <circle cx="50" cy="50" r="48" fill="none" stroke="currentColor" strokeWidth="0.1" className="text-white/20" strokeDasharray="3 1" />
                <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" strokeWidth="0.1" className="text-white/10" />
                <circle cx="50" cy="50" r="28" fill="none" stroke="currentColor" strokeWidth="0.1" className="text-white/5" />

                {/* Geometric Overlays (Vibration Structure) */}
                {/* Triangle (120 vibrations) */}
                <path d="M 50 10 L 84.64 70 L 15.36 70 Z" fill="none" stroke="currentColor" strokeWidth="0.1" className="text-blue-400/30" />
                {/* Square (90 vibrations) */}
                <rect x="21.7" y="21.7" width="56.6" height="56.6" fill="none" stroke="currentColor" strokeWidth="0.1" className="text-yellow-400/30" transform="rotate(45 50 50)" />

                {/* S/R Dynamic Wedges */}
                <g style={{ transform: `rotate(${rotationAngle}deg)`, transformOrigin: 'center' }}>
                  {/* Resistance Wedge (Forward) */}
                  <path d="M 50 50 L 90 30 A 60 60 0 0 1 90 70 Z" fill="hsl(var(--destructive))" fillOpacity="0.1" stroke="none" />
                  {/* Support Wedge (Backward) */}
                  <path d="M 50 50 L 10 70 A 60 60 0 0 1 10 30 Z" fill="hsl(var(--success))" fillOpacity="0.1" stroke="none" />
                </g>

                {/* The Hexagon (Main) */}
                <path
                  d="M 90 50 L 70 84.64 L 30 84.64 L 10 50 L 30 15.36 L 70 15.36 Z"
                  fill="none"
                  stroke="hsl(var(--primary))"
                  strokeWidth="0.5"
                  className="drop-shadow-[0_0_10px_rgba(var(--primary),0.5)]"
                  filter="url(#glow-strong)"
                />

                {/* Scanner Beam */}
                <g style={{ transform: `rotate(${rotationAngle}deg)`, transformOrigin: 'center' }}>
                  <path d="M 50 50 L 50 2" stroke="url(#beam-grad)" strokeWidth="2" strokeLinecap="round" />
                  <circle cx="50" cy="2" r="1" fill="white" filter="url(#glow-strong)" />
                  <line x1="50" y1="50" x2="50" y2="98" stroke="currentColor" strokeWidth="0.1" className="text-white/10" strokeDasharray="1 1" />
                </g>

                {/* Nodes */}
                {hexagonLevels.map((node, i) => {
                  const isActive = activeLevel?.angle === node.angle;
                  return (
                    <g
                      key={i}
                      onClick={() => { setSelectedNode(node.angle); setRotationAngle(node.angle); setIsAutoScanning(false); }}
                      className="cursor-pointer group"
                    >
                      {/* Node Connection Line (Subtle) */}
                      <line x1="50" y1="50" x2={node.x} y2={node.y} stroke="currentColor" strokeWidth="0.05" className={cn("transition-colors", isActive ? "stroke-primary/50" : "stroke-white/5")} />

                      {/* Node Dot */}
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={isActive ? 2 : (node.isMajor ? 1.2 : 0.6)}
                        className={cn(
                          "transition-all duration-300",
                          isActive ? "fill-primary stroke-white stroke-[0.2]" : (node.isMajor ? "fill-white/80" : "fill-white/30 group-hover:fill-white/60")
                        )}
                        filter={isActive ? "url(#glow-strong)" : undefined}
                      />

                      {/* Labels */}
                      {(node.isMajor || isActive) && (
                        <text
                          x={node.x}
                          y={node.y}
                          dx={node.x > 50 ? 3 : -3}
                          dy={node.y > 50 ? 3 : -3}
                          textAnchor={node.x > 50 ? "start" : "end"}
                          className={cn(
                            "text-[2px] font-mono select-none transition-all",
                            isActive ? "fill-primary font-bold text-[3px]" : "fill-white/40"
                          )}
                        >
                          {node.label}
                        </text>
                      )}
                    </g>
                  );
                })}

                {/* Center Hub */}
                <circle cx="50" cy="50" r="6" fill="black" stroke="hsl(var(--primary))" strokeWidth="0.5" />
                <text x="50" y="50" dy="0.5" textAnchor="middle" className="text-[2.5px] font-bold fill-white select-none">
                  {basePrice.toFixed(0)}
                </text>
                <text x="50" y="54" textAnchor="middle" className="text-[1.5px] font-mono fill-muted-foreground uppercase tracking-widest">
                  {viewMode}
                </text>
              </svg>

              {/* Angle Control Overlay */}
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                <Badge
                  variant="secondary"
                  className="bg-black/50 backdrop-blur-md border border-white/10 text-xs font-mono cursor-pointer hover:bg-primary/20"
                  onClick={() => setShowAngles(!showAngles)}
                >
                  {rotationAngle.toFixed(0)}°
                </Badge>
              </div>
            </div>
          </div>

          {/* BOTTOM: DATA ANALYSIS */}
          <div className="w-full bg-black/20 p-8 grid grid-cols-1 lg:grid-cols-[1fr_1.5fr] gap-8 border-t border-white/5">
            {/* Left Col: Active State & Confidence */}
            <div className="flex flex-col h-full gap-6">
              {/* REVERSAL CONFIGURATION */}
              {/* REVERSAL CONFIGURATION */}
              {/* REVERSAL CONFIGURATION - HUD STYLE */}
              <div className={cn(
                "relative overflow-hidden rounded-xl bg-black/40 border shadow-2xl backdrop-blur-md transition-all duration-500",
                viewMode === 'live' ? "border-primary/30 shadow-primary/5" :
                  viewMode === 'ath' ? "border-destructive/30 shadow-destructive/5" :
                    "border-success/30 shadow-success/5"
              )}>
                {/* Decorative Header Bar */}
                <div className={cn(
                  "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r opacity-50 transition-colors duration-500",
                  viewMode === 'live' ? "from-primary/50 via-primary to-primary/50" :
                    viewMode === 'ath' ? "from-destructive/50 via-destructive to-destructive/50" :
                      "from-success/50 via-success to-success/50"
                )} />

                <div className="p-5">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className={cn(
                      "text-[10px] font-bold tracking-[0.2em] uppercase flex items-center gap-2 transition-colors duration-300",
                      viewMode === 'live' ? "text-primary" :
                        viewMode === 'ath' ? "text-destructive" :
                          "text-success"
                    )}>
                      <RefreshCw className="w-3 h-3" /> System Reference
                    </h3>
                    <div className="flex gap-1">
                      {/* Status LEDs Synced with Mode */}
                      <div className={cn("w-1.5 h-1.5 rounded-full transition-all duration-300", viewMode === 'live' ? "bg-primary animate-pulse shadow-[0_0_8px_hsl(var(--primary))]" : "bg-white/5 opacity-20")} />
                      <div className={cn("w-1.5 h-1.5 rounded-full transition-all duration-300", viewMode === 'ath' ? "bg-destructive animate-pulse shadow-[0_0_8px_hsl(var(--destructive))]" : "bg-white/5 opacity-20")} />
                      <div className={cn("w-1.5 h-1.5 rounded-full transition-all duration-300", viewMode === 'atl' ? "bg-success animate-pulse shadow-[0_0_8px_hsl(var(--success))]" : "bg-white/5 opacity-20")} />
                    </div>
                  </div>

                  {/* Mode Tabs */}
                  <div className="grid grid-cols-3 p-1 rounded-lg bg-black/40 border border-white/5 mb-6">
                    {['live', 'ath', 'atl'].map((mode) => (
                      <button
                        key={mode}
                        onClick={() => setViewMode(mode as any)}
                        className={cn(
                          "py-2 text-[10px] font-bold tracking-wider uppercase rounded-md transition-all duration-300",
                          viewMode === mode
                            ? "bg-primary/20 text-primary shadow-[0_0_10px_rgba(var(--primary),0.2)] border border-primary/20"
                            : "text-muted-foreground hover:text-white hover:bg-white/5"
                        )}
                      >
                        {mode}
                      </button>
                    ))}
                  </div>

                  {/* Dynamic Input Area */}
                  <div className="relative min-h-[120px]">
                    {viewMode === 'live' && (
                      <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div className="space-y-1">
                          <label className="text-[9px] text-muted-foreground uppercase tracking-widest pl-1">Start Date</label>
                          <div className="relative group">
                            <input
                              type="date"
                              value={referenceDate}
                              onChange={(e) => setReferenceDate(e.target.value)}
                              className="w-full bg-black/20 border-b border-white/10 px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-primary transition-all group-hover:bg-white/5"
                            />
                            <div className="absolute bottom-0 left-0 h-[1px] w-0 bg-primary transition-all duration-300 group-hover:w-full" />
                          </div>
                        </div>
                        <div className="p-3 rounded border border-dashed border-white/10 bg-white/5 text-[10px] text-muted-foreground leading-relaxed">
                          <span className="text-primary">LIVE MODE:</span> Real-time analysis based on current market cycle.
                        </div>
                      </div>
                    )}

                    {viewMode === 'ath' && (
                      <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1">
                            <label className="text-[9px] text-muted-foreground uppercase tracking-widest pl-1">High Price</label>
                            <input
                              type="number"
                              placeholder={String(currentPrice)}
                              value={athPrice || ''}
                              onChange={(e) => setAthPrice(Number(e.target.value))}
                              className="w-full bg-black/20 border-b border-white/10 px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-primary transition-all"
                            />
                          </div>
                          <div className="space-y-1">
                            <label className="text-[9px] text-muted-foreground uppercase tracking-widest pl-1">High Date</label>
                            <input
                              type="date"
                              value={athDate}
                              onChange={(e) => setAthDate(e.target.value)}
                              className="w-full bg-black/20 border-b border-white/10 px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-primary transition-all"
                            />
                          </div>
                        </div>
                        <div className="p-3 rounded border border-dashed border-white/10 bg-white/5 text-[10px] text-muted-foreground leading-relaxed">
                          <span className="text-destructive">ATH MODE:</span> Bearish reversal projections from Major High.
                        </div>
                      </div>
                    )}

                    {viewMode === 'atl' && (
                      <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1">
                            <label className="text-[9px] text-muted-foreground uppercase tracking-widest pl-1">Low Price</label>
                            <input
                              type="number"
                              placeholder={String(currentPrice)}
                              value={atlPrice || ''}
                              onChange={(e) => setAtlPrice(Number(e.target.value))}
                              className="w-full bg-black/20 border-b border-white/10 px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-primary transition-all"
                            />
                          </div>
                          <div className="space-y-1">
                            <label className="text-[9px] text-muted-foreground uppercase tracking-widest pl-1">Low Date</label>
                            <input
                              type="date"
                              value={atlDate}
                              onChange={(e) => setAtlDate(e.target.value)}
                              className="w-full bg-black/20 border-b border-white/10 px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-primary transition-all"
                            />
                          </div>
                        </div>
                        <div className="p-3 rounded border border-dashed border-white/10 bg-white/5 text-[10px] text-muted-foreground leading-relaxed">
                          <span className="text-success">ATL MODE:</span> Bullish reversal projections from Major Low.
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex-1 flex flex-col justify-center">
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-6 flex items-center justify-between">
                  <span className="flex items-center gap-2"><Target className="w-4 h-4 text-primary" /> Active Coordinates</span>
                  <span className="font-mono text-xs text-white bg-white/10 px-2 py-1 rounded">{liveStats.date}</span>
                </h3>

                <div className="flex flex-col gap-4">
                  {/* Resistance (Top) */}
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-destructive/30 transition-colors group flex flex-col justify-center gap-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground uppercase tracking-widest">Resistance</span>
                      <TrendingUp className="w-4 h-4 text-destructive/70 group-hover:text-destructive transition-colors" />
                    </div>
                    <div className="text-2xl font-mono font-bold text-white tracking-tight flex items-baseline justify-between">
                      <span>{liveStats.resistance.toFixed(2)}</span>
                      <div className="w-[60%] bg-white/5 rounded-full h-1 ml-2 overflow-hidden self-center">
                        <div className="h-full bg-destructive/50 w-[70%]" />
                      </div>
                    </div>
                  </div>

                  {/* Support (Bottom) */}
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-success/30 transition-colors group flex flex-col justify-center gap-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground uppercase tracking-widest">Support</span>
                      <TrendingDown className="w-4 h-4 text-success/70 group-hover:text-success transition-colors" />
                    </div>
                    <div className="text-2xl font-mono font-bold text-white tracking-tight flex items-baseline justify-between">
                      <span>{liveStats.support.toFixed(2)}</span>
                      <div className="w-[60%] bg-white/5 rounded-full h-1 ml-2 overflow-hidden self-center">
                        <div className="h-full bg-success/50 w-[85%]" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/5">
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span className="flex items-center gap-2">
                    <Activity className="w-4 h-4" /> Geometric Confidence
                  </span>
                  <span className="text-primary font-bold font-mono text-lg">94.2%</span>
                </div>
              </div>
            </div>

            {/* Right Col: Vibration Matrix List */}
            <div className="flex flex-col h-[400px] lg:h-auto min-h-[400px]">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                <Layers className="w-4 h-4 text-primary" /> Vibration Matrix
              </h3>
              <div ref={matrixRef} className="flex-1 overflow-y-auto custom-scrollbar border border-white/5 rounded-2xl bg-black/20">
                <div className="divide-y divide-white/5">
                  <div className="sticky top-0 bg-black/60 backdrop-blur-sm z-10 grid grid-cols-[0.8fr_1.2fr_1fr_1fr] p-3 text-[10px] uppercase font-bold text-muted-foreground tracking-wider border-b border-white/10">
                    <div>Angle</div>
                    <div>Time</div>
                    <div className="text-right">Support</div>
                    <div className="text-right">Resistance</div>
                  </div>
                  {hexagonLevels.map((level) => {
                    const isActive = activeLevel?.angle === level.angle;
                    return (
                      <div
                        id={`matrix-row-${level.angle}`}
                        key={level.angle}
                        className={cn(
                          "grid grid-cols-[0.8fr_1.2fr_1fr_1fr] p-3 items-center cursor-pointer transition-all hover:bg-white/5",
                          isActive ? "bg-primary/10" : ""
                        )}
                        onClick={() => {
                          setSelectedNode(level.angle);
                          setRotationAngle(level.angle);
                          setIsAutoScanning(false);
                        }}
                      >
                        <div>
                          <Badge variant="outline" className={cn("font-mono text-[10px] h-5 w-12 justify-center px-0 border-white/10", isActive && "border-primary text-primary bg-primary/10")}>
                            {level.angle}°
                          </Badge>
                        </div>
                        <div className="text-[10px] font-mono text-muted-foreground whitespace-nowrap">
                          {level.date}
                        </div>
                        <div className="text-right font-mono text-xs text-success/90">
                          ${level.support.toFixed(2)}
                        </div>
                        <div className="text-right font-mono text-xs text-destructive/90">
                          ${level.resistance.toFixed(2)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default HexagonGeometryChart;
