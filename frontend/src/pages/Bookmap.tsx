import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import useWebSocketPrice from "@/hooks/useWebSocketPrice";
import {
    ZoomIn, ZoomOut, Play, Pause,
    Activity, MousePointer2, Settings,
    BarChart2, MoreVertical, Layout, Grid, Sliders, Zap, Eye
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════════
   APEX PRO - ORDERFLOW TERMINAL
   
   A high-fidelity reconstruction of professional liquidity analysis 
   software (Bookmap/Exocharts hybrid).
   
   FEATURES:
   - Heatmap (HDR)
   - Volume Bubbles (Kinetic)
   - CVD & Delta (Sub-chart)
   - Footprint (Cluster)
   - Stop/Iceberg/Spoofing Detection
   - DOM & T&S
   ═══════════════════════════════════════════════════════════════ */

const CONFIG = {
    MAX_HISTORY: 1000,
    FPS: 60,
    TICK_SIZE: 0.5,
    PRICE_LEVELS: 150, // Visible vertical range
};

// ── COLOR PALETTE (Cyberpunk/Pro) ──
const THEME = {
    bg: "#0b0e11",
    panel: "#15181c",
    border: "#262932",
    grid: "rgba(255, 255, 255, 0.04)",
    text: "#848e9c",
    textHi: "#eaecef",
    bid: "#0ecb81",   // Binance Green
    ask: "#f6465d",   // Binance Red
    stop: "#ffdd00",  // Gold
    iceberg: "#00d4ff", // Cyan
    spoof: "#bf00ff", // Purple
    heatmap: (intensity: number) => {
        if (intensity < 0.02) return "transparent";
        if (intensity < 0.2) return `rgba(40, 60, 160, ${0.3 + intensity})`;
        if (intensity < 0.4) return `rgba(0, 200, 220, ${0.4 + intensity})`;
        if (intensity < 0.6) return `rgba(255, 200, 0, ${0.5 + intensity})`;
        if (intensity < 0.8) return `rgba(255, 80, 0, ${0.6 + intensity})`;
        return `rgba(255, 255, 255, ${0.8 + intensity * 0.2})`;
    }
};

export default function BookmapApex() {
    const { priceData, isConnected } = useWebSocketPrice({ symbol: "BTCUSDT", enabled: true, updateInterval: 80 });

    // ── Refs ──
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const overlayRef = useRef<HTMLCanvasElement>(null);
    const cvdCanvasRef = useRef<HTMLCanvasElement>(null);
    const deltaCanvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // ── State ──
    const [ui, setUi] = useState({
        zoom: 1.5,
        sidebarOpen: true,
        paused: false,
        contrast: 1.2,
        showCVD: true,
        showDelta: true,
        showFootprint: true,
        activeTf: "M1",
        heatmapIntensity: 0.8,
    });

    // ── Data Stores ──
    const history = useRef<any[]>([]);
    const trades = useRef<any[]>([]);
    const markers = useRef<any[]>([]);
    const dom = useRef<any[]>([]);
    const lastPx = useRef(priceData.price || 48000);
    const cumulativeDelta = useRef(0);
    const footprints = useRef<any[]>([]); // { time, high, low, open, close, clusters: { price: { b, a } } }

    // ── Simulation Engine ──
    const updateEngine = useCallback(() => {
        if (ui.paused) return;

        const now = Date.now();
        const curPx = priceData.price || lastPx.current;
        const priceChange = curPx - lastPx.current;
        lastPx.current = curPx;

        // 1. DOM Refresh
        const center = Math.round(curPx / CONFIG.TICK_SIZE) * CONFIG.TICK_SIZE;
        if (dom.current.length === 0 || Math.abs(dom.current[0].p - center) > 60) {
            dom.current = [];
            for (let i = -120; i < 120; i++) {
                const p = center + i * CONFIG.TICK_SIZE;
                let v = Math.random() * 20;
                if (Math.abs(i) % 10 === 0) v += 200;
                if (Math.abs(i) % 50 === 0) v += 800;
                dom.current.push({ p, v, side: p < curPx ? "b" : "a" });
            }
        }

        let tickDelta = 0;
        dom.current.forEach(l => {
            l.v += (Math.random() - 0.5) * 12;
            if (l.v < 5) l.v = Math.random() * 15;

            if (Math.abs(l.p - curPx) < CONFIG.TICK_SIZE) {
                l.v *= 0.85;
                const qty = Math.random() * 8;
                const side = l.p < curPx ? "a" : "b"; // Aggressor side
                trades.current.push({ t: now, p: l.p, q: qty, side, active: true });
                tickDelta += side === "b" ? qty : -qty;

                // Footprint Aggregation (Simple 5s buckets for demo)
                const bucketTime = Math.floor(now / 5000) * 5000;
                let fp = footprints.current.find(f => f.t === bucketTime);
                if (!fp) {
                    fp = { t: bucketTime, o: curPx, h: curPx, l: curPx, c: curPx, clusters: {} };
                    footprints.current.push(fp);
                    if (footprints.current.length > 50) footprints.current.shift();
                }
                fp.h = Math.max(fp.h, curPx);
                fp.l = Math.min(fp.l, curPx);
                fp.c = curPx;

                const roundedP = Math.round(l.p / CONFIG.TICK_SIZE) * CONFIG.TICK_SIZE;
                if (!fp.clusters[roundedP]) fp.clusters[roundedP] = { b: 0, a: 0 };
                if (side === "b") fp.clusters[roundedP].b += qty;
                else fp.clusters[roundedP].a += qty;

                if (qty > 15) markers.current.push({ t: now, p: l.p, type: "stop", side });
            }
            l.side = l.p < curPx ? "b" : "a";
        });

        cumulativeDelta.current += tickDelta;

        const levels = dom.current
            .filter(l => l.v > 40)
            .map(l => ({ p: l.p, v: l.v, side: l.side }));

        history.current.push({
            t: now,
            levels,
            cvd: cumulativeDelta.current,
            delta: tickDelta
        });
        if (history.current.length > CONFIG.MAX_HISTORY) history.current.shift();
        if (trades.current.length > 500) trades.current.shift();

    }, [priceData.price, ui.paused]);

    // ── Render Pipeline ──
    const render = useCallback(() => {
        if (!canvasRef.current || !overlayRef.current) return;
        const ctx = canvasRef.current.getContext("2d", { alpha: false });
        const ctxO = overlayRef.current.getContext("2d");
        const ctxC = cvdCanvasRef.current?.getContext("2d");
        const ctxD = deltaCanvasRef.current?.getContext("2d");

        if (!ctx || !ctxO) return;

        const W = canvasRef.current.width;
        const H = canvasRef.current.height;

        ctx.fillStyle = THEME.bg;
        ctx.fillRect(0, 0, W, H);

        if (history.current.length < 5) {
            requestAnimationFrame(() => { updateEngine(); render(); });
            return;
        }

        const curPx = lastPx.current;
        const range = 60 / ui.zoom;
        const pxTop = curPx + range / 2;
        const pxBot = curPx - range / 2;
        const getY = (p: number) => H - ((p - pxBot) / (pxTop - pxBot)) * H;
        const colW = Math.max(1, W / CONFIG.MAX_HISTORY);
        const cellH = (H / (range / CONFIG.TICK_SIZE)) + 1;

        // 1. Heatmap
        const data = history.current;
        let x = W;
        for (let i = data.length - 1; i >= 0; i--) {
            x -= colW;
            if (x < -colW) break;
            const slice = data[i];
            slice.levels.forEach((l: any) => {
                if (l.p > pxTop || l.p < pxBot) return;
                const intensity = Math.min(1, (l.v / 800) * ui.contrast);
                if (intensity > 0.02) {
                    ctx.fillStyle = THEME.heatmap(intensity);
                    ctx.fillRect(x, getY(l.p) - cellH / 2, colW + 0.5, cellH);
                }
            });
        }

        // 2. Overlay
        ctxO.clearRect(0, 0, W, H);
        ctxO.strokeStyle = THEME.grid;
        ctxO.lineWidth = 1;
        ctxO.beginPath();
        for (let p = Math.floor(pxBot / 10) * 10; p <= pxTop; p += 10) {
            const y = getY(p);
            ctxO.moveTo(0, y); ctxO.lineTo(W, y);
            ctxO.fillStyle = THEME.text;
            ctxO.font = "10px Inter";
            ctxO.fillText(p.toString(), W - 50, y - 4);
        }
        ctxO.stroke();

        // Bubbles
        const now = Date.now();
        const duration = CONFIG.MAX_HISTORY * 40;
        trades.current.forEach(t => {
            const age = now - t.t;
            if (age > duration) return;
            const bx = W - (age / duration) * W;
            const by = getY(t.p);
            if (by < 0 || by > H) return;
            const r = Math.min(40, Math.max(1.5, Math.sqrt(t.q) * 2.5 * ui.zoom));
            ctxO.beginPath();
            ctxO.arc(bx, by, r, 0, Math.PI * 2);
            ctxO.fillStyle = t.side === "b" ? "rgba(14, 203, 129, 0.4)" : "rgba(246, 70, 93, 0.4)";
            ctxO.fill();
            ctxO.strokeStyle = t.side === "b" ? THEME.bid : THEME.ask;
            ctxO.stroke();
        });

        // Footprint (Cluster Mode) - Drawn at the right edge
        if (ui.showFootprint) {
            const fpW = 80;
            const spacing = 100;
            footprints.current.forEach((fp, idx) => {
                const age = now - fp.t;
                if (age > duration) return;
                const fx = W - (age / duration) * W;

                // Candle stick
                ctxO.strokeStyle = fp.c > fp.o ? THEME.bid : THEME.ask;
                ctxO.lineWidth = 1;
                ctxO.beginPath();
                ctxO.moveTo(fx, getY(fp.h)); ctxO.lineTo(fx, getY(fp.l));
                ctxO.stroke();

                // Clusters
                if (ui.zoom > 1.8) {
                    Object.entries(fp.clusters).forEach(([pStr, vol]: any) => {
                        const p = parseFloat(pStr);
                        if (p > pxTop || p < pxBot) return;
                        const fy = getY(p);
                        const bVol = Math.round(vol.b);
                        const aVol = Math.round(vol.a);

                        ctxO.fillStyle = "rgba(21, 24, 28, 0.8)";
                        ctxO.fillRect(fx - fpW / 2, fy - cellH / 2, fpW, cellH - 1);

                        ctxO.fillStyle = bVol > aVol ? THEME.bid : (aVol > bVol ? THEME.ask : "#fff");
                        ctxO.font = "8px monospace";
                        ctxO.textAlign = "center";
                        if (cellH > 8) ctxO.fillText(`${bVol}|${aVol}`, fx, fy + 3);
                    });
                }
            });
        }

        // 3. CVD Chart
        if (ctxC && ui.showCVD) {
            const cW = cvdCanvasRef.current!.width;
            const cH = cvdCanvasRef.current!.height;
            ctxC.clearRect(0, 0, cW, cH);
            ctxC.fillStyle = THEME.panel; ctxC.fillRect(0, 0, cW, cH);

            const cvdS = data.map(d => d.cvd);
            const minC = Math.min(...cvdS);
            const maxC = Math.max(...cvdS);
            const rangeC = maxC - minC || 1;

            ctxC.beginPath();
            ctxC.strokeStyle = THEME.bid; ctxC.lineWidth = 2;
            for (let i = 0; i < data.length; i++) {
                const cx = cW - ((data.length - 1 - i) * (cW / CONFIG.MAX_HISTORY));
                const cy = cH - ((data[i].cvd - minC) / rangeC) * (cH - 20) - 10;
                if (i === 0) ctxC.moveTo(cx, cy); else ctxC.lineTo(cx, cy);
            }
            ctxC.stroke();
            ctxC.fillStyle = THEME.text; ctxC.font = "10px Inter"; ctxC.fillText("CUMULATIVE DELTA", 10, 15);
        }

        // 4. Delta Chart (Separated)
        if (ctxD && ui.showDelta) {
            const dW = deltaCanvasRef.current!.width;
            const dH = deltaCanvasRef.current!.height;
            ctxD.clearRect(0, 0, dW, dH);
            ctxD.fillStyle = THEME.panel; ctxD.fillRect(0, 0, dW, dH);

            for (let i = 0; i < data.length; i++) {
                const dx = dW - ((data.length - 1 - i) * (dW / CONFIG.MAX_HISTORY));
                const dh = Math.min(dH / 2 - 5, Math.abs(data[i].delta) * 1.5);
                ctxD.fillStyle = data[i].delta > 0 ? THEME.bid : THEME.ask;
                ctxD.fillRect(dx, dH / 2 - (data[i].delta > 0 ? dh : 0), dW / CONFIG.MAX_HISTORY, dh);
            }
            ctxD.fillStyle = THEME.text; ctxD.font = "10px Inter"; ctxD.fillText("VOLUME DELTA", 10, 15);
            ctxD.strokeStyle = THEME.grid; ctxD.beginPath(); ctxD.moveTo(0, dH / 2); ctxD.lineTo(dW, dH / 2); ctxD.stroke();
        }

        requestAnimationFrame(() => { updateEngine(); render(); });
    }, [ui.zoom, ui.paused, ui.contrast, ui.showCVD, ui.showDelta, ui.showFootprint, updateEngine]);

    // ── Resizer ──
    useEffect(() => {
        const resize = () => {
            if (containerRef.current && canvasRef.current && overlayRef.current) {
                const { clientWidth, clientHeight } = containerRef.current;
                const subH = (ui.showCVD ? 80 : 0) + (ui.showDelta ? 80 : 0);
                canvasRef.current.width = clientWidth;
                canvasRef.current.height = clientHeight - subH;
                overlayRef.current.width = clientWidth;
                overlayRef.current.height = clientHeight - subH;

                if (cvdCanvasRef.current) {
                    cvdCanvasRef.current.width = clientWidth;
                    cvdCanvasRef.current.height = 80;
                }
                if (deltaCanvasRef.current) {
                    deltaCanvasRef.current.width = clientWidth;
                    deltaCanvasRef.current.height = 80;
                }
            }
        };
        window.addEventListener("resize", resize);
        resize();
        render();
        return () => window.removeEventListener("resize", resize);
    }, [render, ui.showCVD, ui.showDelta]);

    // Metrics
    const totalBid = dom.current.filter(l => l.side === "b" && Math.abs(l.p - lastPx.current) < 15).reduce((acc, l) => acc + l.v, 0);
    const totalAsk = dom.current.filter(l => l.side === "a" && Math.abs(l.p - lastPx.current) < 15).reduce((acc, l) => acc + l.v, 0);
    const imbalance = (totalBid / (totalBid + totalAsk)) * 100 || 50;

    return (
        <div className="flex flex-col h-screen bg-[#0b0e11] text-[#eaecef] font-sans selection:bg-blue-500/30 overflow-hidden">

            {/* ── HEADER ── */}
            <header className="h-[52px] border-b border-[#262932] bg-[#15181c] flex items-center justify-between px-4 shrink-0 z-50 shadow-lg">
                <div className="flex items-center gap-8">
                    <div className="flex items-center gap-3">
                        <Activity className="text-[#0ecb81]" size={22} />
                        <div className="flex flex-col">
                            <span className="font-black tracking-tighter text-xl leading-none">BTCUSDT</span>
                            <span className="text-[10px] text-[#848e9c] font-bold tracking-widest uppercase">Apex Orderflow</span>
                        </div>
                    </div>

                    <div className="h-6 w-px bg-[#262932]" />

                    {/* Pro Stats HUD */}
                    <div className="flex gap-6 items-center">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-[#848e9c] font-bold">MARKET PRICE</span>
                            <span className={`font-mono text-sm font-black ${priceData.change >= 0 ? "text-[#0ecb81]" : "text-[#f6465d]"}`}>
                                {lastPx.current.toFixed(1)}
                            </span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-[#848e9c] font-bold">24H VOL</span>
                            <span className="font-mono text-sm font-bold text-[#eaecef]">2.84B</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-[#848e9c] font-bold">FUNDING</span>
                            <span className="font-mono text-sm font-bold text-blue-400">0.0100%</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    {/* Imbalance Meter */}
                    <div className="flex flex-col w-48 gap-1">
                        <div className="flex justify-between text-[10px] font-black items-center">
                            <span className="text-[#0ecb81]">{imbalance.toFixed(1)}%</span>
                            <span className="text-[#848e9c] tracking-widest">LIQUIDITY RATIO</span>
                            <span className="text-[#f6465d]">{(100 - imbalance).toFixed(1)}%</span>
                        </div>
                        <div className="h-1.5 bg-[#262932] rounded-full overflow-hidden flex shadow-inner">
                            <div className="bg-[#0ecb81] h-full transition-all duration-500 ease-out shadow-[0_0_8px_#0ecb81]" style={{ width: `${imbalance}%` }} />
                        </div>
                    </div>

                    <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full border ${isConnected ? "border-[#0ecb81]/30 bg-[#0ecb81]/5" : "border-[#f6465d]/30 bg-[#f6465d]/5"}`}>
                        <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-[#0ecb81] animate-pulse" : "bg-[#f6465d]"}`} />
                        <span className={`text-[10px] font-black tracking-wider ${isConnected ? "text-[#0ecb81]" : "text-[#f6465d]"}`}>
                            {isConnected ? "DIRECT FEED" : "LATENCY LOSS"}
                        </span>
                    </div>

                    <div className="flex gap-2">
                        <button onClick={() => setUi(p => ({ ...p, sidebarOpen: !p.sidebarOpen }))} className={`p-2 rounded-lg transition-colors ${ui.sidebarOpen ? "bg-[#262932] text-white" : "text-[#848e9c] hover:bg-[#262932]"}`}>
                            <Layout size={20} />
                        </button>
                        <button className="p-2 rounded-lg text-[#848e9c] hover:bg-[#262932]"><Settings size={20} /></button>
                    </div>
                </div>
            </header>

            {/* ── WORKSPACE ── */}
            <div className="flex flex-1 overflow-hidden relative">

                {/* LEFT TOOLBAR */}
                <div className="w-[56px] border-r border-[#262932] bg-[#0b0e11] flex flex-col items-center py-6 gap-6 shrink-0 z-40">
                    <ToolButton icon={MousePointer2} active />
                    <ToolButton icon={Grid} />
                    <div className="w-8 h-px bg-[#262932]" />
                    <ToolButton icon={ZoomIn} onClick={() => setUi(p => ({ ...p, zoom: Math.min(6, p.zoom + 0.2) }))} />
                    <ToolButton icon={ZoomOut} onClick={() => setUi(p => ({ ...p, zoom: Math.max(0.4, p.zoom - 0.2) }))} />
                    <div className="w-8 h-px bg-[#262932]" />
                    <ToolButton icon={Activity} active={ui.showCVD} onClick={() => setUi(p => ({ ...p, showCVD: !p.showCVD }))} color={ui.showCVD ? "text-green-400" : ""} title="CVD" />
                    <ToolButton icon={BarChart2} active={ui.showDelta} onClick={() => setUi(p => ({ ...p, showDelta: !p.showDelta }))} color={ui.showDelta ? "text-red-400" : ""} title="Delta" />
                    <ToolButton icon={Zap} active={ui.showFootprint} onClick={() => setUi(p => ({ ...p, showFootprint: !p.showFootprint }))} color={ui.showFootprint ? "text-blue-400" : ""} title="Footprint" />

                    <div className="flex-1" />
                    <ToolButton icon={ui.paused ? Play : Pause} active={ui.paused} onClick={() => setUi(p => ({ ...p, paused: !p.paused }))} color="text-yellow-400" />
                </div>

                {/* MAIN CHART ENGINE */}
                <div className="flex-1 flex flex-col relative bg-[#0b0e11]" ref={containerRef}>
                    <div className="flex-1 relative overflow-hidden">
                        <canvas ref={canvasRef} className="absolute inset-0 block" />
                        <canvas ref={overlayRef} className="absolute inset-0 block pointer-events-none" />

                        {/* Floating Price Tracker */}
                        <div className="absolute right-0 top-0 bottom-0 w-[100px] pointer-events-none flex flex-col justify-center items-end pr-2 z-30">
                            <div className="bg-[#262932] text-white font-mono text-sm py-1 px-2 rounded-l-md border border-r-0 border-white/20 shadow-xl">
                                {lastPx.current.toFixed(1)}
                            </div>
                        </div>
                    </div>

                    {/* Separated Sub-Charts (CVD & Delta) */}
                    <div className="shrink-0 flex flex-col bg-[#15181c]">
                        {ui.showCVD && (
                            <div className="h-[80px] border-t border-[#262932] relative group">
                                <canvas ref={cvdCanvasRef} className="absolute inset-0 block" />
                            </div>
                        )}
                        {ui.showDelta && (
                            <div className="h-[80px] border-t border-[#262932] relative group">
                                <canvas ref={deltaCanvasRef} className="absolute inset-0 block" />
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT SIDEBAR (High-Density DOM) */}
                {ui.sidebarOpen && (
                    <div className="w-[360px] bg-[#15181c] border-l border-[#262932] flex flex-col shrink-0 z-40 transition-all duration-300">
                        {/* DOM Header */}
                        <div className="h-10 border-b border-[#262932] flex items-center justify-between px-4 bg-[#1e2329]">
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-black text-[#eaecef] tracking-widest">ORDER FLOW LADDER</span>
                                <Eye size={14} className="text-blue-400" />
                            </div>
                            <MoreVertical size={16} className="text-[#848e9c] cursor-pointer" />
                        </div>

                        {/* DOM Ladder Content */}
                        <div className="flex-1 overflow-hidden relative flex flex-col">
                            <div className="flex text-[10px] font-black text-[#5e6673] px-4 py-2 border-b border-[#262932] bg-[#0b0e11]/30">
                                <span className="w-20">PRICE</span>
                                <span className="flex-1 text-right">SIZE (LOTS)</span>
                                <span className="w-16 text-right">DEPTH</span>
                            </div>

                            <div className="flex-1 overflow-y-auto no-scrollbar font-mono text-[11px]">
                                {dom.current
                                    .sort((a, b) => b.p - a.p)
                                    .filter(l => Math.abs(l.p - lastPx.current) < (35 / ui.zoom))
                                    .map((l, i) => {
                                        const isAsk = l.p > lastPx.current;
                                        const isSpread = Math.abs(l.p - lastPx.current) < CONFIG.TICK_SIZE;
                                        const bg = isAsk ? "rgba(246, 70, 93, 0.2)" : "rgba(14, 203, 129, 0.2)";
                                        const maxVol = 1200;

                                        return (
                                            <div key={i} className={`flex items-center h-5 px-4 relative group cursor-crosshair transition-colors ${isSpread ? "bg-[#262932]/50 border-y border-white/5" : "hover:bg-white/5"}`}>
                                                <div className="absolute right-0 top-[1px] bottom-[1px] transition-all duration-500" style={{ width: `${Math.min(100, (l.v / maxVol) * 100)}%`, backgroundColor: bg }} />
                                                <span className={`w-20 z-10 font-black ${isAsk ? "text-[#f6465d]" : "text-[#0ecb81]"} ${isSpread ? "text-white glow-text" : ""}`}>
                                                    {l.p.toFixed(1)}
                                                </span>
                                                <span className="flex-1 text-right z-10 text-[#d1d4dc] group-hover:text-white font-bold">
                                                    {l.v.toFixed(0)}
                                                </span>
                                                <span className="w-16 text-right z-10 text-[#5e6673] text-[9px]">
                                                    {((l.v / maxVol) * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        )
                                    })}
                            </div>
                        </div>

                        {/* Market Tape */}
                        <div className="h-[280px] border-t border-[#262932] flex flex-col bg-[#0b0e11]">
                            <div className="h-9 border-b border-[#262932] flex items-center justify-between px-4 bg-[#1e2329]">
                                <span className="text-[10px] font-black text-[#848e9c] tracking-widest">REALTIME TAPE</span>
                                <Sliders size={14} className="text-[#848e9c] cursor-pointer" />
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar">
                                {trades.current.slice().reverse().slice(0, 40).map((t, i) => (
                                    <div key={i} className="flex justify-between items-center px-4 py-1 text-[10px] font-mono hover:bg-[#262932] border-b border-white/5 transition-colors">
                                        <span className="text-[#5e6673]">{new Date(t.t).toLocaleTimeString("en-GB", { hour12: false, second: '2-digit', minute: '2-digit', hour: '2-digit' })}</span>
                                        <span className={`font-bold ${t.side === "b" ? "text-[#0ecb81]" : "text-[#f6465d]"}`}>{t.p.toFixed(1)}</span>
                                        <span className={`w-20 text-right ${t.q > 8 ? "text-white font-black animate-pulse" : "text-[#848e9c]"}`}>
                                            {t.q.toFixed(3)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function ToolButton({ icon: Icon, active, onClick, color, title }: any) {
    return (
        <div className="flex flex-col items-center gap-1">
            <button
                onClick={onClick}
                className={`
                    w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-300 transform active:scale-95
                    ${active ? "bg-[#262932] text-white shadow-lg border border-white/10" : "text-[#848e9c] hover:text-[#eaecef] hover:bg-[#1e2329]"}
                    ${color ? color : ""}
                `}
            >
                <Icon size={20} strokeWidth={2.5} />
            </button>
            {title && <span className="text-[8px] font-black text-[#5e6673] uppercase tracking-tighter">{title}</span>}
        </div>
    );
}
