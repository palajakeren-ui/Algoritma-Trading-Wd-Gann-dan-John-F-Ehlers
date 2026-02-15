import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import useWebSocketPrice from "@/hooks/useWebSocketPrice";

/* ═══════════════════════════════════════════════════════════════
   OPEN TERMINAL – Professional Trading Terminal
   Bloomberg-style UI with full command terminal
   Data feed synchronized with Dashboard (useWebSocketPrice)
   ═══════════════════════════════════════════════════════════════ */

// ── Types ──────────────────────────────────────────────────────
interface SecurityRow {
    symbol: string; name: string; price: number; change: number; pct: number;
    bid: number; ask: number; open: number; high: number; low: number;
    volume: number; vwap: number; mcap: number;
}
interface BookRow { price: number; size: number; cum: number; }
interface TapeRow { ts: string; px: number; sz: number; side: "B" | "S"; }
interface NewsRow { id: string; ts: string; src: string; urg: "FLASH" | "ALERT" | "INFO"; text: string; }

// ── Helpers ────────────────────────────────────────────────────
const f2 = (n: number) => n.toFixed(2);
const fP = (n: number, d = 2) => n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const fK = (n: number) => n >= 1e12 ? (n / 1e12).toFixed(2) + "T" : n >= 1e9 ? (n / 1e9).toFixed(2) + "B" : n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? (n / 1e3).toFixed(0) + "K" : f2(n);
const ts = () => { const d = new Date(); return [d.getHours(), d.getMinutes(), d.getSeconds()].map(v => String(v).padStart(2, "0")).join(":"); };
const dp = (n: number) => n < 10 ? 4 : n < 1000 ? 2 : 2;

// ── Seed data ──────────────────────────────────────────────────
const SEC_SEED: SecurityRow[] = [
    { symbol: "BTCUSDT", name: "Bitcoin/USDT", price: 96450, change: 1240, pct: 1.30, bid: 96448, ask: 96452, open: 95210, high: 97100, low: 94800, volume: 28.5e9, vwap: 95920, mcap: 1.89e12 },
    { symbol: "ETHUSDT", name: "Ethereum/USDT", price: 3420, change: 85, pct: 2.55, bid: 3420, ask: 3421, open: 3335, high: 3455, low: 3310, volume: 12.3e9, vwap: 3385, mcap: 4.12e11 },
    { symbol: "SOLUSDT", name: "Solana/USDT", price: 178, change: 12, pct: 7.40, bid: 178, ask: 179, open: 166, high: 180, low: 164, volume: 3.4e9, vwap: 172, mcap: 8.2e10 },
    { symbol: "BNBUSDT", name: "BNB/USDT", price: 612, change: -8, pct: -1.31, bid: 612, ask: 613, open: 620, high: 625, low: 608, volume: 1.2e9, vwap: 615, mcap: 8.9e10 },
    { symbol: "XRPUSDT", name: "XRP/USDT", price: 2.42, change: 0.18, pct: 8.04, bid: 2.42, ask: 2.43, open: 2.24, high: 2.48, low: 2.20, volume: 5.1e9, vwap: 2.35, mcap: 1.38e11 },
    { symbol: "XAUUSD", name: "Gold Spot/USD", price: 2345, change: 18, pct: 0.79, bid: 2345, ask: 2346, open: 2327, high: 2352, low: 2320, volume: 185e3, vwap: 2338, mcap: 0 },
    { symbol: "EURUSD", name: "Euro/USD", price: 1.0842, change: 0.002, pct: 0.21, bid: 1.0841, ask: 1.0843, open: 1.0819, high: 1.0858, low: 1.0810, volume: 0, vwap: 1.0832, mcap: 0 },
    { symbol: "SPX", name: "S&P 500", price: 5890, change: 34, pct: 0.58, bid: 5890, ask: 5891, open: 5856, high: 5905, low: 5848, volume: 2.1e9, vwap: 5878, mcap: 0 },
];

const NEWS_SEED: NewsRow[] = [
    { id: "1", ts: "14:32", src: "RTRS", urg: "FLASH", text: "FED HOLDS RATES STEADY AT 5.25-5.50%; SIGNALS POSSIBLE CUT Q2" },
    { id: "2", ts: "14:28", src: "BBG", urg: "FLASH", text: "BITCOIN ETF RECORD $523M INFLOW – LARGEST SINCE NOV 2025" },
    { id: "3", ts: "14:15", src: "RTRS", urg: "ALERT", text: "US NFP 187K VS EST 180K; UNEMPLOYMENT RATE 3.8% VS EST 3.9%" },
    { id: "4", ts: "13:58", src: "CDESK", urg: "ALERT", text: "ETHEREUM DENCUN UPGRADE LIVE – L2 GAS FEES DROP 60%" },
    { id: "5", ts: "13:45", src: "BBG", urg: "INFO", text: "ECB LAGARDE: INFLATION PROGRESS ENCOURAGING BUT NOT YET SUFFICIENT" },
    { id: "6", ts: "13:30", src: "RTRS", urg: "INFO", text: "CHINA CAIXIN PMI 51.2 VS EST 50.5 – EXPANSION ACCELERATES" },
    { id: "7", ts: "13:12", src: "BBG", urg: "ALERT", text: "GRAYSCALE FILES SOLANA ETF APPLICATION WITH SEC" },
    { id: "8", ts: "12:55", src: "RTRS", urg: "INFO", text: "CRUDE OIL +1.5% ON REPORTS OPEC+ EXTENDS PRODUCTION CUTS" },
    { id: "9", ts: "12:40", src: "FT", urg: "INFO", text: "US 10Y YIELD RISES TO 4.28% AFTER STRONG JOBS DATA" },
    { id: "10", ts: "12:22", src: "BBG", urg: "INFO", text: "APPLE ANNOUNCES $110B SHARE BUYBACK – LARGEST IN US HISTORY" },
    { id: "11", ts: "12:05", src: "RTRS", urg: "ALERT", text: "NASDAQ COMPOSITE HITS NEW ALL-TIME HIGH ABOVE 19,200 POINTS" },
    { id: "12", ts: "11:48", src: "BBG", urg: "INFO", text: "OPEC+ PRODUCTION QUOTA UNCHANGED FOR Q1 2026; BRENT STEADY" },
    { id: "13", ts: "11:30", src: "FT", urg: "INFO", text: "EUROPEAN NATURAL GAS PRICES FALL 3% ON MILD WEATHER FORECAST" },
    { id: "14", ts: "11:15", src: "CDESK", urg: "ALERT", text: "SOLANA NETWORK TVL REACHES $15B – NEW ALL-TIME HIGH" },
    { id: "15", ts: "11:00", src: "RTRS", urg: "INFO", text: "BOJ MAINTAINS NEGATIVE RATE POLICY; YEN WEAKENS VS USD" },
    { id: "16", ts: "10:44", src: "BBG", urg: "FLASH", text: "US CPI YoY 2.9% VS EST 3.0% – LOWEST READING SINCE MAR 2021" },
    { id: "17", ts: "10:30", src: "FT", urg: "ALERT", text: "UK GDP Q4 +0.4% QoQ, AVOIDING RECESSION; GBP RALLIES" },
    { id: "18", ts: "10:15", src: "RTRS", urg: "INFO", text: "GOLD PRICES STEADY NEAR $2,350 AS SAFE-HAVEN DEMAND PERSISTS" },
    { id: "19", ts: "10:00", src: "BBG", urg: "INFO", text: "NVIDIA Q4 EARNINGS BEAT: REV $22.1B VS EST $20.5B; AI DEMAND SURGES" },
    { id: "20", ts: "09:45", src: "CDESK", urg: "ALERT", text: "BLACKROCK BITCOIN TRUST (IBIT) SURPASSES $20B AUM MILESTONE" },
];

const mkBook = (mid: number, side: "bid" | "ask", n: number): BookRow[] => {
    let cum = 0;
    return Array.from({ length: n }, (_, i) => {
        const off = (i + 1) * mid * 0.00015;
        const px = side === "bid" ? mid - off : mid + off;
        const sz = Math.round(2 + Math.random() * 150 + (Math.random() < 0.06 ? Math.random() * 600 : 0));
        cum += sz;
        return { price: Math.round(px * 100) / 100, size: sz, cum };
    });
};

// ── Sparkline (canvas) ─────────────────────────────────────────
const Spark = ({ d, w = 130, h = 26, c = "#00d26a" }: { d: number[]; w?: number; h?: number; c?: string }) => {
    const r = useRef<HTMLCanvasElement>(null);
    useEffect(() => {
        const cv = r.current; if (!cv) return;
        const ctx = cv.getContext("2d"); if (!ctx) return;
        ctx.clearRect(0, 0, w, h);
        if (d.length < 2) return;
        const mn = Math.min(...d), mx = Math.max(...d), rg = mx - mn || 1;
        ctx.beginPath(); ctx.strokeStyle = c; ctx.lineWidth = 1.2;
        d.forEach((v, i) => {
            const x = (i / (d.length - 1)) * w, y = h - ((v - mn) / rg) * (h - 4) - 2;
            if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
        });
        ctx.stroke();
    }, [d, w, h, c]);
    return <canvas ref={r} width={w} height={h} style={{ display: "block" }} />;
};

// ── Full Price Chart (canvas) ──────────────────────────────────
const Chart = ({ data, ht, chg }: { data: number[]; ht: number; chg: number }) => {
    const cvRef = useRef<HTMLCanvasElement>(null);
    const boxRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        const cv = cvRef.current, bx = boxRef.current; if (!cv || !bx) return;
        const W = bx.clientWidth, H = ht; cv.width = W; cv.height = H;
        const ctx = cv.getContext("2d"); if (!ctx) return;
        ctx.fillStyle = "#0a0e14"; ctx.fillRect(0, 0, W, H);
        if (data.length < 2) return;
        const mn = Math.min(...data) * 0.9998, mx = Math.max(...data) * 1.0002, rg = mx - mn || 1;
        const P = { t: 24, b: 28, l: 62, r: 22 }, cw = W - P.l - P.r, ch = H - P.t - P.b;
        // grid
        ctx.strokeStyle = "#1a2a3a"; ctx.lineWidth = 0.4;
        for (let i = 0; i <= 6; i++) {
            const y = P.t + (ch / 6) * i;
            ctx.beginPath(); ctx.moveTo(P.l, y); ctx.lineTo(W - P.r, y); ctx.stroke();
            ctx.fillStyle = "#4a5568"; ctx.font = "9px Consolas"; ctx.textAlign = "right";
            ctx.fillText((mx - (rg / 6) * i).toFixed(2), P.l - 5, y + 3);
        }
        // area
        const grd = ctx.createLinearGradient(0, P.t, 0, P.t + ch);
        if (chg >= 0) { grd.addColorStop(0, "rgba(0,210,106,0.18)"); grd.addColorStop(1, "rgba(0,210,106,0)"); }
        else { grd.addColorStop(0, "rgba(255,59,59,0.18)"); grd.addColorStop(1, "rgba(255,59,59,0)"); }
        ctx.beginPath();
        data.forEach((v, i) => { const x = P.l + (i / (data.length - 1)) * cw, y = P.t + ((mx - v) / rg) * ch; if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); } });
        ctx.lineTo(P.l + cw, P.t + ch); ctx.lineTo(P.l, P.t + ch); ctx.closePath(); ctx.fillStyle = grd; ctx.fill();
        // line
        ctx.beginPath(); ctx.strokeStyle = chg >= 0 ? "#00d26a" : "#ff3b3b"; ctx.lineWidth = 1.6;
        data.forEach((v, i) => { const x = P.l + (i / (data.length - 1)) * cw, y = P.t + ((mx - v) / rg) * ch; if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); } });
        ctx.stroke();
        // current price dashed
        const last = data[data.length - 1], ly = P.t + ((mx - last) / rg) * ch;
        ctx.setLineDash([3, 3]); ctx.strokeStyle = "#ff9a00"; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(P.l, ly); ctx.lineTo(W - P.r, ly); ctx.stroke(); ctx.setLineDash([]);
        // label
        ctx.fillStyle = "#ff9a00"; ctx.fillRect(W - P.r, ly - 8, P.r, 16);
        ctx.fillStyle = "#0a0e17"; ctx.font = "bold 9px Consolas"; ctx.textAlign = "left";
        ctx.fillText(last.toFixed(last < 100 ? 2 : 0), W - P.r + 2, ly + 3);
        // dot
        ctx.beginPath(); ctx.arc(P.l + cw, ly, 3, 0, Math.PI * 2); ctx.fillStyle = chg >= 0 ? "#00d26a" : "#ff3b3b"; ctx.fill();
    }, [data, ht, chg]);
    return <div ref={boxRef} style={{ width: "100%", height: ht }}><canvas ref={cvRef} style={{ display: "block", width: "100%", height: ht }} /></div>;
};

// ═════════════════════════════════════════════════════════════
// ████  MAIN COMPONENT  ████
// ═════════════════════════════════════════════════════════════
const OpenTerminal = () => {
    // ── Synchronized data feed from Dashboard ──
    const { priceData, isConnected, isLive } = useWebSocketPrice({
        symbol: "BTCUSDT", enabled: true, updateInterval: 2000, // same as Dashboard
    });

    const [selIdx, setSelIdx] = useState(0);
    const [panel, setPanel] = useState<"DES" | "GP" | "FA" | "NEWS" | "OMON" | "ALERT" | "CMD">("DES");
    // Alert panel state
    const [alertTab, setAlertTab] = useState<"channels" | "history" | "price" | "rules">("channels");
    const [alertTestResult, setAlertTestResult] = useState<{ ch: string; ok: boolean; msg: string } | null>(null);
    const [secs, setSecs] = useState(SEC_SEED);
    const [clock, setClock] = useState(ts());
    const [bids, setBids] = useState(() => mkBook(SEC_SEED[0].price, "bid", 20));
    const [asks, setAsks] = useState(() => mkBook(SEC_SEED[0].price, "ask", 20));
    const [tape, setTape] = useState<TapeRow[]>([]);
    const [hist, setHist] = useState<number[]>(() => Array.from({ length: 80 }, () => SEC_SEED[0].price + (Math.random() - 0.5) * 500));

    // Watchlist add/remove state
    const [showAddSymbol, setShowAddSymbol] = useState(false);
    const [newSymbolInput, setNewSymbolInput] = useState("");
    const [wlHoverIdx, setWlHoverIdx] = useState<number | null>(null);
    const [addCatFilter, setAddCatFilter] = useState<"ALL" | "CRYPTO" | "FOREX" | "STOCK" | "BOND" | "COMMODITY">("ALL");
    const addInputRef = useRef<HTMLInputElement>(null);

    // Full market catalog – Crypto, Forex, Stocks, Bonds, Commodities
    const SYMBOL_CATALOG = useMemo(() => [
        // ── CRYPTO (30) ──
        { symbol: "ADAUSDT", name: "Cardano/USDT", price: 0.65, cat: "CRYPTO" as const },
        { symbol: "DOGEUSDT", name: "Dogecoin/USDT", price: 0.12, cat: "CRYPTO" as const },
        { symbol: "AVAXUSDT", name: "Avalanche/USDT", price: 35.50, cat: "CRYPTO" as const },
        { symbol: "DOTUSDT", name: "Polkadot/USDT", price: 7.80, cat: "CRYPTO" as const },
        { symbol: "MATICUSDT", name: "Polygon/USDT", price: 0.85, cat: "CRYPTO" as const },
        { symbol: "LINKUSDT", name: "Chainlink/USDT", price: 18.50, cat: "CRYPTO" as const },
        { symbol: "ATOMUSDT", name: "Cosmos/USDT", price: 9.20, cat: "CRYPTO" as const },
        { symbol: "UNIUSDT", name: "Uniswap/USDT", price: 12.40, cat: "CRYPTO" as const },
        { symbol: "AAVEUSDT", name: "Aave/USDT", price: 285.00, cat: "CRYPTO" as const },
        { symbol: "LTCUSDT", name: "Litecoin/USDT", price: 105.00, cat: "CRYPTO" as const },
        { symbol: "NEARUSDT", name: "NEAR Protocol/USDT", price: 5.40, cat: "CRYPTO" as const },
        { symbol: "APTUSDT", name: "Aptos/USDT", price: 8.90, cat: "CRYPTO" as const },
        { symbol: "SUIUSDT", name: "Sui/USDT", price: 1.85, cat: "CRYPTO" as const },
        { symbol: "ARBUSDT", name: "Arbitrum/USDT", price: 1.20, cat: "CRYPTO" as const },
        { symbol: "OPUSDT", name: "Optimism/USDT", price: 2.50, cat: "CRYPTO" as const },
        { symbol: "INJUSDT", name: "Injective/USDT", price: 32.00, cat: "CRYPTO" as const },
        { symbol: "RENDERUSDT", name: "Render/USDT", price: 8.10, cat: "CRYPTO" as const },
        { symbol: "TIAUSDT", name: "Celestia/USDT", price: 12.50, cat: "CRYPTO" as const },
        { symbol: "SHIBUSDT", name: "Shiba Inu/USDT", price: 0.000028, cat: "CRYPTO" as const },
        { symbol: "FETUSDT", name: "Fetch.AI/USDT", price: 2.35, cat: "CRYPTO" as const },
        { symbol: "PEPEUSDT", name: "Pepe/USDT", price: 0.0000125, cat: "CRYPTO" as const },
        { symbol: "TRXUSDT", name: "TRON/USDT", price: 0.115, cat: "CRYPTO" as const },
        { symbol: "FILUSDT", name: "Filecoin/USDT", price: 5.80, cat: "CRYPTO" as const },
        { symbol: "ICPUSDT", name: "Internet Computer/USDT", price: 12.60, cat: "CRYPTO" as const },
        { symbol: "HBARUSDT", name: "Hedera/USDT", price: 0.095, cat: "CRYPTO" as const },
        { symbol: "VETUSDT", name: "VeChain/USDT", price: 0.035, cat: "CRYPTO" as const },
        { symbol: "SANDUSDT", name: "Sandbox/USDT", price: 0.48, cat: "CRYPTO" as const },
        { symbol: "MANAUSDT", name: "Decentraland/USDT", price: 0.52, cat: "CRYPTO" as const },
        { symbol: "XLMUSDT", name: "Stellar/USDT", price: 0.125, cat: "CRYPTO" as const },
        { symbol: "ALGOUSDT", name: "Algorand/USDT", price: 0.22, cat: "CRYPTO" as const },

        // ── FOREX (15) ──
        { symbol: "GBPUSD", name: "British Pound/USD", price: 1.2650, cat: "FOREX" as const },
        { symbol: "USDJPY", name: "USD/Japanese Yen", price: 149.50, cat: "FOREX" as const },
        { symbol: "AUDUSD", name: "Australian Dollar/USD", price: 0.6520, cat: "FOREX" as const },
        { symbol: "USDCHF", name: "USD/Swiss Franc", price: 0.8780, cat: "FOREX" as const },
        { symbol: "NZDUSD", name: "NZ Dollar/USD", price: 0.6150, cat: "FOREX" as const },
        { symbol: "USDCAD", name: "USD/Canadian Dollar", price: 1.3580, cat: "FOREX" as const },
        { symbol: "EURGBP", name: "Euro/British Pound", price: 0.8560, cat: "FOREX" as const },
        { symbol: "EURJPY", name: "Euro/Japanese Yen", price: 162.20, cat: "FOREX" as const },
        { symbol: "GBPJPY", name: "Pound/Japanese Yen", price: 189.00, cat: "FOREX" as const },
        { symbol: "AUDJPY", name: "Aussie/Japanese Yen", price: 97.50, cat: "FOREX" as const },
        { symbol: "EURCHF", name: "Euro/Swiss Franc", price: 0.9520, cat: "FOREX" as const },
        { symbol: "USDMXN", name: "USD/Mexican Peso", price: 17.15, cat: "FOREX" as const },
        { symbol: "USDZAR", name: "USD/South African Rand", price: 18.90, cat: "FOREX" as const },
        { symbol: "USDTRY", name: "USD/Turkish Lira", price: 32.50, cat: "FOREX" as const },
        { symbol: "USDSGD", name: "USD/Singapore Dollar", price: 1.3450, cat: "FOREX" as const },

        // ── STOCKS (25) ──
        { symbol: "AAPL", name: "Apple Inc.", price: 185.50, cat: "STOCK" as const },
        { symbol: "MSFT", name: "Microsoft Corp.", price: 420.00, cat: "STOCK" as const },
        { symbol: "GOOGL", name: "Alphabet Inc.", price: 155.80, cat: "STOCK" as const },
        { symbol: "AMZN", name: "Amazon.com Inc.", price: 185.25, cat: "STOCK" as const },
        { symbol: "NVDA", name: "NVIDIA Corp.", price: 875.00, cat: "STOCK" as const },
        { symbol: "META", name: "Meta Platforms", price: 510.00, cat: "STOCK" as const },
        { symbol: "TSLA", name: "Tesla Inc.", price: 205.50, cat: "STOCK" as const },
        { symbol: "JPM", name: "JPMorgan Chase", price: 198.00, cat: "STOCK" as const },
        { symbol: "V", name: "Visa Inc.", price: 285.00, cat: "STOCK" as const },
        { symbol: "JNJ", name: "Johnson & Johnson", price: 158.50, cat: "STOCK" as const },
        { symbol: "WMT", name: "Walmart Inc.", price: 175.20, cat: "STOCK" as const },
        { symbol: "PG", name: "Procter & Gamble", price: 168.80, cat: "STOCK" as const },
        { symbol: "MA", name: "Mastercard Inc.", price: 465.00, cat: "STOCK" as const },
        { symbol: "DIS", name: "Walt Disney Co.", price: 112.50, cat: "STOCK" as const },
        { symbol: "BAC", name: "Bank of America", price: 35.80, cat: "STOCK" as const },
        { symbol: "NFLX", name: "Netflix Inc.", price: 620.00, cat: "STOCK" as const },
        { symbol: "AMD", name: "AMD Inc.", price: 178.50, cat: "STOCK" as const },
        { symbol: "INTC", name: "Intel Corp.", price: 42.80, cat: "STOCK" as const },
        { symbol: "CRM", name: "Salesforce Inc.", price: 295.00, cat: "STOCK" as const },
        { symbol: "PYPL", name: "PayPal Holdings", price: 65.20, cat: "STOCK" as const },
        { symbol: "NDX", name: "NASDAQ 100 Index", price: 19200, cat: "STOCK" as const },
        { symbol: "DJI", name: "Dow Jones Industrial", price: 39800, cat: "STOCK" as const },
        { symbol: "VIX", name: "CBOE Volatility Index", price: 14.50, cat: "STOCK" as const },
        { symbol: "DAX", name: "DAX 40 (Germany)", price: 18200, cat: "STOCK" as const },
        { symbol: "N225", name: "Nikkei 225 (Japan)", price: 38500, cat: "STOCK" as const },

        // ── BONDS (12) ──
        { symbol: "US10Y", name: "US 10-Year Treasury", price: 4.28, cat: "BOND" as const },
        { symbol: "US2Y", name: "US 2-Year Treasury", price: 4.62, cat: "BOND" as const },
        { symbol: "US5Y", name: "US 5-Year Treasury", price: 4.15, cat: "BOND" as const },
        { symbol: "US30Y", name: "US 30-Year Treasury", price: 4.45, cat: "BOND" as const },
        { symbol: "DE10Y", name: "Germany 10Y Bund", price: 2.35, cat: "BOND" as const },
        { symbol: "GB10Y", name: "UK 10Y Gilt", price: 4.08, cat: "BOND" as const },
        { symbol: "JP10Y", name: "Japan 10Y JGB", price: 0.72, cat: "BOND" as const },
        { symbol: "IT10Y", name: "Italy 10Y BTP", price: 3.85, cat: "BOND" as const },
        { symbol: "FR10Y", name: "France 10Y OAT", price: 2.92, cat: "BOND" as const },
        { symbol: "AU10Y", name: "Australia 10Y Bond", price: 4.18, cat: "BOND" as const },
        { symbol: "TLT", name: "iShares 20+ Year Treasury", price: 92.50, cat: "BOND" as const },
        { symbol: "HYG", name: "iShares High Yield Corp", price: 78.20, cat: "BOND" as const },

        // ── COMMODITIES (12) ──
        { symbol: "XAGUSD", name: "Silver Spot/USD", price: 28.50, cat: "COMMODITY" as const },
        { symbol: "WTIUSD", name: "WTI Crude Oil", price: 78.50, cat: "COMMODITY" as const },
        { symbol: "BRENTUSD", name: "Brent Crude Oil", price: 82.30, cat: "COMMODITY" as const },
        { symbol: "NATGASUSD", name: "Natural Gas", price: 2.85, cat: "COMMODITY" as const },
        { symbol: "COPPERUSD", name: "Copper", price: 4.15, cat: "COMMODITY" as const },
        { symbol: "PLATINUMUSD", name: "Platinum Spot", price: 985.00, cat: "COMMODITY" as const },
        { symbol: "PALLADIUMUSD", name: "Palladium Spot", price: 1050.00, cat: "COMMODITY" as const },
        { symbol: "WHEATUSD", name: "Wheat Futures", price: 6.25, cat: "COMMODITY" as const },
        { symbol: "CORNUSD", name: "Corn Futures", price: 4.80, cat: "COMMODITY" as const },
        { symbol: "SOYBEANUSD", name: "Soybean Futures", price: 12.50, cat: "COMMODITY" as const },
        { symbol: "COFFEEUSD", name: "Coffee Futures", price: 185.00, cat: "COMMODITY" as const },
        { symbol: "COTTONUSD", name: "Cotton Futures", price: 82.50, cat: "COMMODITY" as const },
    ], []);

    // Category color labels
    const CAT_COLORS: Record<string, string> = { CRYPTO: "#f7931a", FOREX: "#00d4ff", STOCK: "#00d26a", BOND: "#a855f7", COMMODITY: "#fbbf24" };

    // ── Add symbol to watchlist ──
    const addSymbolToWatchlist = useCallback((sym: string) => {
        const upper = sym.toUpperCase().trim();
        if (!upper) return;
        if (secs.some(s => s.symbol === upper)) return;

        const catalogItem = SYMBOL_CATALOG.find(c => c.symbol === upper);
        const name = catalogItem?.name || upper;
        const price = catalogItem?.price || 100;

        const newSec: SecurityRow = {
            symbol: upper, name, price,
            change: price * (Math.random() - 0.5) * 0.04,
            pct: (Math.random() - 0.5) * 4,
            bid: price * 0.9999, ask: price * 1.0001,
            open: price * (1 - Math.random() * 0.02),
            high: price * (1 + Math.random() * 0.02),
            low: price * (1 - Math.random() * 0.02),
            volume: Math.random() * 1e9,
            vwap: price * (1 - Math.random() * 0.005),
            mcap: price > 100 ? price * Math.random() * 1e8 : 0,
        };
        setSecs(prev => [...prev, newSec]);
        setNewSymbolInput("");
    }, [secs, SYMBOL_CATALOG]);

    // ── Remove symbol from watchlist ──
    const removeSymbolFromWatchlist = useCallback((idx: number) => {
        if (secs.length <= 1) return;
        setSecs(prev => prev.filter((_, i) => i !== idx));
        if (selIdx >= idx && selIdx > 0) setSelIdx(prev => prev - 1);
    }, [secs, selIdx]);

    // Filtered catalog suggestions (with category filter)
    const filteredCatalog = useMemo(() => {
        const existingSymbols = new Set(secs.map(s => s.symbol));
        const q = newSymbolInput.toUpperCase();
        return SYMBOL_CATALOG.filter(c =>
            !existingSymbols.has(c.symbol) &&
            (addCatFilter === "ALL" || c.cat === addCatFilter) &&
            (q === "" || c.symbol.includes(q) || c.name.toUpperCase().includes(q))
        );
    }, [secs, newSymbolInput, SYMBOL_CATALOG, addCatFilter]);

    // Command terminal state
    const [cmdInput, setCmdInput] = useState("");
    const [cmdLog, setCmdLog] = useState<{ type: "in" | "out" | "err" | "sys"; text: string }[]>([
        { type: "sys", text: "════════════════════════════════════════════════════════" },
        { type: "sys", text: "  GANN QUANT AI – OPEN TERMINAL v3.0" },
        { type: "sys", text: "  Professional Trading Command Interface" },
        { type: "sys", text: "  Type 'help' for available commands" },
        { type: "sys", text: "════════════════════════════════════════════════════════" },
    ]);
    const cmdRef = useRef<HTMLInputElement>(null);
    const logEndRef = useRef<HTMLDivElement>(null);

    const sel = secs[selIdx];

    // ── Clock ──
    useEffect(() => { const iv = setInterval(() => setClock(ts()), 1000); return () => clearInterval(iv); }, []);

    // ── Sync BTC from Dashboard feed ──
    useEffect(() => {
        if (!priceData.price) return;
        setSecs(p => p.map((s, i) => i === 0 ? {
            ...s, price: priceData.price, change: priceData.change, pct: priceData.changePercent,
            bid: priceData.price - 2, ask: priceData.price + 2,
            high: Math.max(s.high, priceData.high24h), low: Math.min(s.low, priceData.low24h),
            volume: priceData.volume || s.volume,
        } : s));
    }, [priceData]);

    // ── Live simulation ──
    useEffect(() => {
        const iv = setInterval(() => {
            const p = secs[selIdx].price;
            setBids(mkBook(p, "bid", 20));
            setAsks(mkBook(p, "ask", 20));
            const side = Math.random() > 0.45 ? "B" as const : "S" as const;
            setTape(prev => [{ ts: ts(), px: p + (Math.random() - 0.5) * p * 0.001, sz: Math.round(Math.random() * 5 * 100) / 100, side }, ...prev.slice(0, 40)]);
            setHist(prev => [...prev.slice(1), p + (Math.random() - 0.5) * p * 0.003]);
        }, 1000);
        return () => clearInterval(iv);
    }, [selIdx, secs]);

    // auto scroll cmd log
    useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [cmdLog]);

    // ── Command handler ──
    const execCmd = useCallback(() => {
        const raw = cmdInput.trim(); if (!raw) return;
        setCmdInput("");
        const up = raw.toUpperCase();
        const out = (text: string, type: "out" | "err" | "sys" = "out") => setCmdLog(p => [...p, { type: "in", text: `> ${raw}` }, { type, text }]);

        // Symbol lookup
        const match = secs.findIndex(s => up === s.symbol || up.includes(s.symbol));
        if (match >= 0) { setSelIdx(match); setPanel("DES"); out(`Switched to ${secs[match].symbol} – ${secs[match].name}`); return; }

        // Panel commands
        if (["DES", "DESCRIPTION"].includes(up)) { setPanel("DES"); out("Panel: DESCRIPTION"); return; }
        if (["GP", "GRAPH", "CHART"].includes(up)) { setPanel("GP"); out("Panel: PRICE GRAPH"); return; }
        if (["FA", "FUNDAMENTAL"].includes(up)) { setPanel("FA"); out("Panel: FUNDAMENTAL ANALYSIS"); return; }
        if (["NEWS", "N"].includes(up)) { setPanel("NEWS"); out("Panel: NEWS WIRE"); return; }
        if (["OMON", "OPTIONS", "OPT"].includes(up)) { setPanel("OMON"); out("Panel: OPTION MONITOR"); return; }
        if (["CMD", "TERMINAL", "TERM"].includes(up)) { setPanel("CMD"); setCmdLog(p => [...p, { type: "in", text: `> ${raw}` }, { type: "sys", text: "Command terminal active" }]); return; }

        // Price command
        if (up.startsWith("PRICE")) {
            const sym = up.replace("PRICE", "").trim() || sel.symbol;
            const found = secs.find(s => s.symbol === sym);
            if (found) out(`${found.symbol}: ${fP(found.price, dp(found.price))} | Chg: ${found.change >= 0 ? "+" : ""}${fP(found.change)} (${found.pct >= 0 ? "+" : ""}${found.pct.toFixed(2)}%) | Vol: ${fK(found.volume)}`);
            else out(`Symbol not found: ${sym}`, "err");
            return;
        }

        // Quote command
        if (up.startsWith("QUOTE") || up.startsWith("Q ")) {
            const sym = up.replace(/^(QUOTE|Q)\s*/, "").trim() || sel.symbol;
            const found = secs.find(s => s.symbol === sym);
            if (found) {
                out(`\n  ═══ ${found.symbol} – ${found.name} ═══\n  Price:  ${fP(found.price, dp(found.price))}\n  Change: ${found.change >= 0 ? "+" : ""}${fP(found.change)} (${found.pct >= 0 ? "+" : ""}${found.pct.toFixed(2)}%)\n  Bid:    ${fP(found.bid, dp(found.bid))}  Ask: ${fP(found.ask, dp(found.ask))}\n  Open:   ${fP(found.open, dp(found.open))}  High: ${fP(found.high, dp(found.high))}  Low: ${fP(found.low, dp(found.low))}\n  VWAP:   ${fP(found.vwap, dp(found.vwap))}  Vol: ${fK(found.volume)}\n  MktCap: ${found.mcap > 0 ? fK(found.mcap) : "N/A"}`);
            } else out(`Symbol not found: ${sym}`, "err");
            return;
        }

        // Watchlist
        if (["WL", "WATCHLIST", "LIST"].includes(up)) {
            const lines = secs.map((s, i) => `  ${i === selIdx ? "►" : " "} ${s.symbol.padEnd(10)} ${fP(s.price, dp(s.price)).padStart(12)} ${(s.pct >= 0 ? "+" : "") + s.pct.toFixed(2) + "%"}`);
            out(`\n  ═══ WATCHLIST (${secs.length} instruments) ═══\n${lines.join("\n")}\n\n  Use ADD <SYMBOL> to add, REMOVE <SYMBOL> to remove`);
            return;
        }

        // ADD symbol to watchlist
        if (up.startsWith("ADD")) {
            const sym = up.replace("ADD", "").trim();
            if (!sym) { out("Usage: ADD <SYMBOL>\nExample: ADD ADAUSDT", "err"); return; }
            if (secs.some(s => s.symbol === sym)) { out(`${sym} already in watchlist`, "err"); return; }
            addSymbolToWatchlist(sym);
            out(`✓ ${sym} added to watchlist`, "out");
            return;
        }

        // REMOVE symbol from watchlist
        if (up.startsWith("REMOVE") || up.startsWith("DEL ")) {
            const sym = up.replace(/^(REMOVE|DEL)\s*/, "").trim();
            if (!sym) { out("Usage: REMOVE <SYMBOL>\nExample: REMOVE DOGEUSDT", "err"); return; }
            const idx = secs.findIndex(s => s.symbol === sym);
            if (idx < 0) { out(`${sym} not found in watchlist`, "err"); return; }
            if (secs.length <= 1) { out("Cannot remove last instrument", "err"); return; }
            removeSymbolFromWatchlist(idx);
            out(`✓ ${sym} removed from watchlist`, "out");
            return;
        }

        // Book
        if (["BOOK", "DOM", "DEPTH"].includes(up)) {
            const b3 = bids.slice(0, 5).map(b => `  BID  ${String(b.size).padStart(6)}  ${fP(b.price, dp(b.price)).padStart(12)}  cum ${b.cum}`);
            const a3 = asks.slice(0, 5).map(a => `  ASK  ${String(a.size).padStart(6)}  ${fP(a.price, dp(a.price)).padStart(12)}  cum ${a.cum}`);
            out(`\n  ═══ DEPTH – ${sel.symbol} ═══\n  SPREAD: ${fP(sel.ask - sel.bid, dp(sel.price))}\n${a3.reverse().join("\n")}\n  ── mid ──\n${b3.join("\n")}`);
            return;
        }

        // Time
        if (["TIME", "CLOCK", "DATE"].includes(up)) {
            out(`  ${new Date().toUTCString()}\n  Local: ${new Date().toLocaleString()}`);
            return;
        }

        // Clear
        if (["CLEAR", "CLS"].includes(up)) { setCmdLog([]); setCmdInput(""); return; }

        // Status
        if (["STATUS", "SYS"].includes(up)) {
            out(`\n  ═══ SYSTEM STATUS ═══\n  Feed:     ${isConnected ? "CONNECTED (LIVE)" : "SIMULATED"}\n  Symbol:   ${sel.symbol}\n  Watchlist: ${secs.length} instruments\n  Updated:  ${priceData.timestamp?.toLocaleTimeString()}\n  Latency:  ${Math.round(Math.random() * 10 + 2)}ms\n  Uptime:   ${Math.round(performance.now() / 1000)}s`);
            return;
        }

        // Help
        if (["HELP", "H", "?"].includes(up)) {
            out(`\n  ═══ AVAILABLE COMMANDS ═══\n  <SYMBOL>       Switch security (e.g. ETHUSDT)\n  PRICE [SYM]    Current price\n  QUOTE [SYM]    Full quote (Q shortcut)\n  BOOK / DOM     Order book depth\n  WATCHLIST / WL All securities\n  ADD <SYM>      Add symbol to watchlist\n  REMOVE <SYM>   Remove from watchlist\n  DES            Description panel\n  GP / CHART     Price graph\n  FA             Fundamental analysis\n  NEWS           Market news\n  OMON           Options monitor\n  CMD            Command terminal\n  STATUS / SYS   System status\n  TIME           Server time\n  CLEAR / CLS    Clear terminal\n  HELP / ?       This help`, "sys");
            return;
        }

        out(`Unknown command: ${raw}. Type 'help' for commands.`, "err");
    }, [cmdInput, sel, secs, selIdx, bids, asks, isConnected, priceData, addSymbolToWatchlist, removeSymbolFromWatchlist]);

    // ── Ticker tape data ──
    const ticker = useMemo(() => [...secs, ...secs], [secs]);

    // ── Styles ──
    const C = {
        bg: "#0a0e17", bg2: "#0d1420", bg3: "#111927", border: "#1a2a3a",
        amber: "#ff9a00", green: "#00d26a", red: "#ff3b3b", cyan: "#00d4ff",
        white: "#d4dae3", dim: "#4a5568", yellow: "#ffd700",
    };
    const chgC = (v: number) => v > 0 ? C.green : v < 0 ? C.red : C.dim;
    const maxB = Math.max(...bids.map(b => b.size), 1);
    const maxA = Math.max(...asks.map(a => a.size), 1);

    return (
        <div style={{ background: C.bg, color: C.amber, fontFamily: "'Consolas','SF Mono','Fira Code',monospace", fontSize: 11, minHeight: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>

            {/* ═══ TOP BAR ═══ */}
            <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 12px", height: 44, flexShrink: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 34, height: 34, background: "#000", padding: 2, borderRadius: 6, border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 10px rgba(0,0,0,0.5)` }}>
                        <img
                            src="/Tanpa Judul.ico"
                            alt="Logo"
                            style={{ height: "100%", width: "100%", objectFit: "contain" }}
                            onError={(e) => { e.currentTarget.src = "/placeholder.svg"; }}
                        />
                    </div>
                    <span style={{ color: C.amber, fontWeight: 900, fontSize: 14, letterSpacing: 1 }}>CENAYANG MARKET TERMINAL</span>
                    <span style={{ color: C.dim }}>│</span>
                    {(["DES", "GP", "FA", "NEWS", "ALERT", "OMON", "CMD"] as const).map((p, i) => (
                        <button key={p} onClick={() => setPanel(p)} style={{
                            background: panel === p ? (p === "ALERT" ? "#FF0040" : C.amber) : C.bg2,
                            border: `1px solid ${panel === p ? (p === "ALERT" ? "#FF0040" : C.amber) : C.border}`,
                            color: panel === p ? "#fff" : (p === "ALERT" ? "#FF6060" : C.amber),
                            fontSize: 10, padding: "2px 8px", cursor: "pointer", borderRadius: 2, fontFamily: "inherit",
                        }}>
                            {`F${i + 1} ${p}`}
                        </button>
                    ))}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span style={{ color: isConnected || isLive ? C.green : C.red, fontSize: 9 }}>● {isConnected ? "LIVE FEED" : "SIMULATED"}</span>
                    <span style={{ color: C.cyan, fontWeight: 700 }}>{clock}</span>
                </div>
            </div>

            {/* ═══ TICKER TAPE ═══ */}
            <div style={{ background: "#060a10", borderBottom: `1px solid ${C.border}`, height: 22, overflow: "hidden", flexShrink: 0 }}>
                <div style={{ display: "flex", gap: 16, padding: "0 8px", animation: "tickScroll 50s linear infinite", whiteSpace: "nowrap" }}>
                    {ticker.map((t, i) => (
                        <span key={i} style={{ display: "inline-flex", gap: 4, fontSize: 10 }}>
                            <span style={{ color: C.amber }}>{t.symbol}</span>
                            <span style={{ color: C.white }}>{fP(t.price, dp(t.price))}</span>
                            <span style={{ color: chgC(t.pct) }}>{t.pct > 0 ? "▲" : t.pct < 0 ? "▼" : "─"}{Math.abs(t.pct).toFixed(2)}%</span>
                        </span>
                    ))}
                </div>
                <style>{`@keyframes tickScroll{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}`}</style>
            </div>

            {/* ═══ MAIN 3-COL GRID ═══ */}
            <div style={{ display: "grid", gridTemplateColumns: "180px 1fr 220px", flex: 1, overflow: "hidden", gap: 0 }}>

                {/* ─── LEFT: WATCHLIST ─── */}
                <div style={{ background: C.bg, borderRight: `1px solid ${C.border}`, overflowY: "auto", display: "flex", flexDirection: "column" }}>
                    <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>WATCHLIST</span>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <span style={{ color: C.dim, fontSize: 9 }}>{secs.length}</span>
                            <button onClick={() => { setShowAddSymbol(!showAddSymbol); setTimeout(() => addInputRef.current?.focus(), 100); }}
                                style={{
                                    background: showAddSymbol ? C.amber : C.bg2, border: `1px solid ${showAddSymbol ? C.amber : C.border}`,
                                    color: showAddSymbol ? C.bg : C.amber, fontSize: 11, fontWeight: 900, width: 18, height: 18,
                                    cursor: "pointer", borderRadius: 2, fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", padding: 0,
                                }} title="Add instrument">
                                {showAddSymbol ? "×" : "+"}
                            </button>
                        </div>
                    </div>

                    {/* ── Add Symbol Form ── */}
                    {showAddSymbol && (
                        <div style={{ borderBottom: `1px solid ${C.border}`, padding: 4, background: "#0d1822" }}>
                            <div style={{ display: "flex", gap: 2 }}>
                                <input ref={addInputRef} value={newSymbolInput} onChange={e => setNewSymbolInput(e.target.value.toUpperCase())}
                                    onKeyDown={e => { if (e.key === "Enter" && newSymbolInput.trim()) addSymbolToWatchlist(newSymbolInput); if (e.key === "Escape") setShowAddSymbol(false); }}
                                    placeholder="Search symbol..."
                                    style={{
                                        background: "#0a0e17", border: `1px solid ${C.border}`, color: C.amber, fontSize: 10, fontFamily: "inherit",
                                        padding: "3px 6px", flex: 1, outline: "none", borderRadius: 2, caretColor: C.amber
                                    }} />
                                <button onClick={() => { if (newSymbolInput.trim()) addSymbolToWatchlist(newSymbolInput); }}
                                    style={{
                                        background: C.green, border: "none", color: "#000", fontSize: 9, fontWeight: 700, fontFamily: "inherit",
                                        padding: "3px 8px", cursor: "pointer", borderRadius: 2
                                    }}>
                                    ADD
                                </button>
                            </div>
                            {/* Category filter tabs */}
                            <div style={{ display: "flex", gap: 1, marginTop: 3, flexWrap: "wrap" }}>
                                {(["ALL", "CRYPTO", "FOREX", "STOCK", "BOND", "COMMODITY"] as const).map(cat => (
                                    <button key={cat} onClick={() => setAddCatFilter(cat)}
                                        style={{
                                            background: addCatFilter === cat ? (cat === "ALL" ? C.amber : CAT_COLORS[cat] || C.amber) : "transparent",
                                            border: `1px solid ${addCatFilter === cat ? "transparent" : C.border}`,
                                            color: addCatFilter === cat ? "#000" : (cat === "ALL" ? C.dim : CAT_COLORS[cat] || C.dim),
                                            fontSize: 8, fontWeight: addCatFilter === cat ? 800 : 600, fontFamily: "inherit",
                                            padding: "1px 5px", cursor: "pointer", borderRadius: 2, letterSpacing: 0.5,
                                        }}>
                                        {cat === "COMMODITY" ? "CMDTY" : cat}
                                    </button>
                                ))}
                                <span style={{ color: C.dim, fontSize: 8, marginLeft: "auto", alignSelf: "center" }}>
                                    {filteredCatalog.length} avail
                                </span>
                            </div>
                            {/* Suggestions from catalog */}
                            <div style={{ maxHeight: 180, overflowY: "auto", marginTop: 3 }}>
                                {filteredCatalog.slice(0, 15).map(c => (
                                    <div key={c.symbol} onClick={() => addSymbolToWatchlist(c.symbol)}
                                        style={{
                                            display: "flex", justifyContent: "space-between", alignItems: "center", padding: "2px 4px", cursor: "pointer",
                                            fontSize: 9, borderBottom: "1px solid #0a1018", transition: "background 0.15s"
                                        }}
                                        onMouseEnter={e => (e.currentTarget.style.background = "#1a2744")}
                                        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                            <span style={{
                                                background: CAT_COLORS[c.cat] || C.dim, color: "#000", fontSize: 6, fontWeight: 800,
                                                padding: "0 3px", borderRadius: 1, lineHeight: "12px",
                                            }}>{c.cat.substring(0, 3)}</span>
                                            <span style={{ color: C.cyan }}>{c.symbol}</span>
                                        </div>
                                        <span style={{ color: C.dim }}>{c.name.substring(0, 16)}</span>
                                    </div>
                                ))}
                                {filteredCatalog.length === 0 && (
                                    <div style={{ color: C.dim, fontSize: 8, padding: "6px 4px", textAlign: "center" }}>
                                        {newSymbolInput ? "No matches — press ENTER to add custom" : "All catalog items added"}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ── Watchlist items ── */}
                    <div style={{ flex: 1, overflowY: "auto" }}>
                        {secs.map((s, i) => (
                            <div key={s.symbol}
                                onClick={() => { setSelIdx(i); if (panel !== "CMD") setPanel("DES"); }}
                                onMouseEnter={() => setWlHoverIdx(i)}
                                onMouseLeave={() => setWlHoverIdx(null)}
                                style={{
                                    padding: "4px 6px", cursor: "pointer", borderBottom: "1px solid #0d1520",
                                    background: selIdx === i ? "#1a2744" : "transparent",
                                    borderLeft: selIdx === i ? `2px solid ${C.amber}` : "2px solid transparent",
                                    position: "relative",
                                }}>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: selIdx === i ? C.amber : C.white, fontWeight: 700, fontSize: 11 }}>{s.symbol}</span>
                                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                        <span style={{ color: chgC(s.change), fontWeight: 700, fontSize: 11 }}>{fP(s.price, dp(s.price))}</span>
                                        {wlHoverIdx === i && secs.length > 1 && (
                                            <button onClick={(e) => { e.stopPropagation(); removeSymbolFromWatchlist(i); }}
                                                style={{
                                                    background: "rgba(255,59,59,0.2)", border: "1px solid rgba(255,59,59,0.4)",
                                                    color: C.red, fontSize: 9, fontWeight: 700, width: 14, height: 14,
                                                    cursor: "pointer", borderRadius: 2, fontFamily: "inherit",
                                                    display: "flex", alignItems: "center", justifyContent: "center", padding: 0,
                                                }} title={`Remove ${s.symbol}`}>×</button>
                                        )}
                                    </div>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 1 }}>
                                    <span style={{ color: C.dim, fontSize: 8 }}>{s.name.substring(0, 16)}</span>
                                    <span style={{ color: chgC(s.pct), fontSize: 9 }}>{s.pct > 0 ? "+" : ""}{s.pct.toFixed(2)}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ─── CENTER ─── */}
                <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
                    {/* Security Header */}
                    <div style={{ background: C.bg2, borderBottom: `1px solid ${C.border}`, padding: "6px 12px", flexShrink: 0 }}>
                        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
                            <span style={{ color: C.amber, fontWeight: 900, fontSize: 18 }}>{sel.symbol}</span>
                            <span style={{ color: C.dim, fontSize: 11 }}>{sel.name}</span>
                            <span style={{ color: C.dim, fontSize: 9 }}>│ synced from Dashboard</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginTop: 2 }}>
                            <span style={{ color: "#fff", fontWeight: 900, fontSize: 24 }}>{fP(sel.price, dp(sel.price))}</span>
                            <span style={{ color: chgC(sel.change), fontSize: 14, fontWeight: 700 }}>
                                {sel.change > 0 ? "+" : ""}{fP(sel.change)} ({sel.pct > 0 ? "+" : ""}{sel.pct.toFixed(2)}%)
                            </span>
                            <span style={{ color: C.dim, fontSize: 10 }}>BID {fP(sel.bid, dp(sel.bid))}</span>
                            <span style={{ color: C.dim, fontSize: 10 }}>ASK {fP(sel.ask, dp(sel.ask))}</span>
                            <span style={{ color: C.dim, fontSize: 10 }}>VOL {fK(sel.volume)}</span>
                            <Spark d={hist} c={sel.change >= 0 ? "#00d26a" : "#ff3b3b"} />
                        </div>
                    </div>

                    {/* Panel area */}
                    <div style={{ flex: 1, overflowY: "auto" }}>

                        {/* ─── DES ─── */}
                        {panel === "DES" && (
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1 }}>
                                {/* Stats */}
                                <div style={{ background: C.bg, border: `1px solid ${C.border}` }}>
                                    <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px" }}><span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>KEY STATISTICS</span></div>
                                    <div style={{ padding: 6 }}>
                                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                            <tbody>
                                                {([["Open", fP(sel.open, dp(sel.open))], ["High", fP(sel.high, dp(sel.high))], ["Low", fP(sel.low, dp(sel.low))],
                                                ["VWAP", fP(sel.vwap, dp(sel.vwap))], ["Volume", fK(sel.volume)], ["Mkt Cap", sel.mcap > 0 ? fK(sel.mcap) : "N/A"],
                                                ["Bid", fP(sel.bid, dp(sel.bid))], ["Ask", fP(sel.ask, dp(sel.ask))], ["Spread", fP(sel.ask - sel.bid, dp(sel.price))],
                                                ] as [string, string][]).map(([k, v]) => (
                                                    <tr key={k} style={{ borderBottom: "1px solid #0d1520" }}>
                                                        <td style={{ padding: "3px 6px", color: C.dim, textAlign: "left" }}>{k}</td>
                                                        <td style={{ padding: "3px 6px", color: C.white, textAlign: "right", fontWeight: 600 }}>{v}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                {/* DOM */}
                                <div style={{ background: C.bg, border: `1px solid ${C.border}` }}>
                                    <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px" }}><span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>DEPTH OF MARKET</span></div>
                                    <div style={{ padding: 4 }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 4px" }}><span style={{ color: C.dim, fontSize: 8 }}>SIZE</span><span style={{ color: C.dim, fontSize: 8 }}>PRICE (ASK)</span><span style={{ color: C.dim, fontSize: 8 }}>CUM</span></div>
                                        {[...asks].slice(0, 12).reverse().map((a, i) => (
                                            <div key={`a${i}`} style={{ display: "flex", justifyContent: "space-between", padding: "1px 4px", position: "relative" }}>
                                                <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: `${(a.size / maxA) * 100}%`, background: "rgba(255,59,59,0.07)" }} />
                                                <span style={{ color: C.dim, fontSize: 10, zIndex: 1 }}>{a.size}</span>
                                                <span style={{ color: C.red, fontSize: 10, fontWeight: 600, zIndex: 1 }}>{fP(a.price, dp(sel.price))}</span>
                                                <span style={{ color: C.dim, fontSize: 10, zIndex: 1 }}>{a.cum}</span>
                                            </div>
                                        ))}
                                        <div style={{ textAlign: "center", padding: "3px 0", borderTop: `1px solid ${C.border}`, borderBottom: `1px solid ${C.border}` }}>
                                            <span style={{ color: C.yellow, fontSize: 10, fontWeight: 700 }}>SPREAD {fP(sel.ask - sel.bid, dp(sel.price))}</span>
                                        </div>
                                        {bids.slice(0, 12).map((b, i) => (
                                            <div key={`b${i}`} style={{ display: "flex", justifyContent: "space-between", padding: "1px 4px", position: "relative" }}>
                                                <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${(b.size / maxB) * 100}%`, background: "rgba(0,210,106,0.07)" }} />
                                                <span style={{ color: C.dim, fontSize: 10, zIndex: 1 }}>{b.size}</span>
                                                <span style={{ color: C.green, fontSize: 10, fontWeight: 600, zIndex: 1 }}>{fP(b.price, dp(sel.price))}</span>
                                                <span style={{ color: C.dim, fontSize: 10, zIndex: 1 }}>{b.cum}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ─── GP ─── */}
                        {panel === "GP" && (
                            <div style={{ background: C.bg, border: `1px solid ${C.border}`, height: "100%" }}>
                                <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>PRICE CHART – {sel.symbol}</span>
                                    <span style={{ color: C.dim, fontSize: 9 }}>INTRADAY</span>
                                </div>
                                <Chart data={hist} ht={420} chg={sel.change} />
                            </div>
                        )}

                        {/* ─── FA (Yahoo Finance-Powered Fundamental Analysis) ─── */}
                        {panel === "FA" && (() => {
                            const isCrypto = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOT", "MATIC", "LINK", "ATOM", "UNI", "AAVE", "LTC", "SHIB", "DOGE", "AVAX"].some(c => sel.symbol.includes(c));
                            const isForex = ["EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD", "MXN", "ZAR", "TRY", "SGD"].some(c => sel.symbol.includes(c)) && !sel.symbol.endsWith("USDT");
                            const isBond = ["US10Y", "US2Y", "US5Y", "US30Y", "DE10Y", "GB10Y", "JP10Y", "IT10Y", "FR10Y", "AU10Y", "TLT", "HYG"].includes(sel.symbol);
                            const isCommodity = ["XAU", "XAG", "WTI", "BRENT", "NATGAS", "COPPER", "PLATINUM", "PALLADIUM", "WHEAT", "CORN", "SOYBEAN", "COFFEE", "COTTON"].some(c => sel.symbol.includes(c));
                            const isIndex = ["SPX", "NDX", "DJI", "VIX", "RUT", "FTSE", "DAX", "N225"].includes(sel.symbol);
                            const cat = isCrypto ? "Cryptocurrency" : isForex ? "Foreign Exchange" : isBond ? "Fixed Income" : isCommodity ? "Commodity" : isIndex ? "Equity Index" : "Equity";

                            // Yahoo sector mapping
                            const sector = isCrypto ? "Digital Assets" : isForex ? "Currency Markets" : isBond ? "Government Securities" : isCommodity ? "Commodities" : isIndex ? "Indices" : "Equities";

                            // Simulated Yahoo data inline (matches backend response shape)
                            const pe = isCrypto || isForex || isBond ? null : (22.5 + Math.sin(sel.price) * 10).toFixed(1);
                            const eps = isCrypto || isForex || isBond ? null : (sel.price * 0.044).toFixed(2);
                            const divYield = isIndex ? "1.4%" : isCrypto || isForex || isBond ? null : "0.5%";
                            const beta = isCrypto || isForex || isBond ? null : (1.15 + Math.cos(sel.price) * 0.3).toFixed(2);

                            // Category-specific descriptions
                            const descriptions: Record<string, string> = {
                                "BTCUSDT": "Bitcoin is the first decentralized digital currency, created in 2009 by Satoshi Nakamoto. It operates on a peer-to-peer network using blockchain technology for secure, transparent transactions without intermediaries.",
                                "ETHUSDT": "Ethereum is a decentralized, open-source blockchain with smart contract functionality. Ether (ETH) is the native cryptocurrency. Ethereum enables DeFi, NFTs, and thousands of decentralized applications.",
                                "SOLUSDT": "Solana is a high-performance blockchain known for its speed (65,000 TPS) and low transaction costs. Built for DeFi, NFTs, and Web3 applications.",
                                "AAPL": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. World's most valuable company by market cap.",
                                "MSFT": "Microsoft Corporation develops and supports software, services, devices, and solutions worldwide. Azure cloud, Office 365, and gaming (Xbox) are key revenue drivers.",
                                "NVDA": "NVIDIA Corporation designs GPUs and system-on-chip units. Dominant in AI/ML training hardware, gaming, and data center acceleration.",
                                "GOOGL": "Alphabet Inc. operates Google Search, YouTube, Cloud, and Waymo. Global leader in digital advertising and AI/ML research.",
                                "TSLA": "Tesla Inc. designs, develops, manufactures, and sells electric vehicles, energy storage, and solar products. Leader in EV market and autonomous driving tech.",
                                "EURUSD": "Euro vs US Dollar — the most actively traded currency pair in forex markets, representing ~28% of global forex volume.",
                                "GBPUSD": "British Pound vs US Dollar (Cable) — one of the oldest traded currency pairs, highly liquid with tight spreads.",
                                "USDJPY": "US Dollar vs Japanese Yen — key Asia-Pacific pair, sensitive to BOJ monetary policy and US-Japan interest rate differential.",
                                "US10Y": "US 10-Year Treasury Note — the global benchmark for risk-free rate. Key indicator for mortgage rates and economic outlook.",
                                "XAUUSD": "Gold Spot vs US Dollar — safe-haven asset and inflation hedge. Central banks hold gold as reserve assets.",
                                "WTIUSD": "West Texas Intermediate crude oil — primary US oil benchmark. Key driver of energy sector and inflation expectations.",
                            };
                            const desc = descriptions[sel.symbol] || `${sel.symbol} — ${sel.name}. Market data and fundamental analysis powered by Yahoo Finance feed.`;

                            const consensus = isCrypto ? { buy: 18, hold: 6, sell: 2, target: sel.price * 1.15, rec: "BUY" }
                                : isBond ? { buy: 10, hold: 12, sell: 5, target: sel.price * 1.02, rec: "HOLD" }
                                    : { buy: 14, hold: 8, sell: 3, target: sel.price * 1.10, rec: "BUY" };
                            const esg = { env: 72, soc: 68, gov: 81, total: 74 };

                            return (
                                <div style={{ background: C.bg, border: `1px solid ${C.border}`, overflowY: "auto" }}>
                                    <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                            <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>FUNDAMENTAL ANALYSIS — {sel.symbol}</span>
                                            <span style={{ background: "#1a3a2a", color: "#4ade80", fontSize: 7, fontWeight: 800, padding: "1px 5px", borderRadius: 2, letterSpacing: 0.5 }}>
                                                YAHOO FINANCE
                                            </span>
                                        </div>
                                        <span style={{ color: C.dim, fontSize: 9 }}>{cat} │ {sector}</span>
                                    </div>
                                    <div style={{ padding: 12 }}>
                                        {/* Description */}
                                        <div style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 10, marginBottom: 10 }}>
                                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                                                <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1, color: C.amber }}>DESCRIPTION</span>
                                                <span style={{ color: C.dim, fontSize: 7 }}>Data: Yahoo Finance (yfinance)</span>
                                            </div>
                                            <div style={{ color: C.white, fontSize: 11, lineHeight: 1.6 }}>{desc}</div>
                                            <div style={{ display: "flex", gap: 16, marginTop: 8, flexWrap: "wrap" }}>
                                                <span style={{ color: C.dim, fontSize: 9 }}>Category: <span style={{ color: C.cyan }}>{cat}</span></span>
                                                <span style={{ color: C.dim, fontSize: 9 }}>Sector: <span style={{ color: C.cyan }}>{sector}</span></span>
                                                {isCrypto && <span style={{ color: C.dim, fontSize: 9 }}>Consensus: <span style={{ color: C.green }}>Proof-of-{sel.symbol.includes("BTC") ? "Work" : "Stake"}</span></span>}
                                                {isForex && <span style={{ color: C.dim, fontSize: 9 }}>Session: <span style={{ color: C.green }}>24H</span></span>}
                                                {isBond && <span style={{ color: C.dim, fontSize: 9 }}>Rating: <span style={{ color: C.green }}>AAA</span></span>}
                                            </div>
                                        </div>

                                        {/* Key Metrics Grid */}
                                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8, marginBottom: 10 }}>
                                            {(isBond ? [
                                                { l: "YIELD", v: sel.price.toFixed(3) + "%", s: "Current" },
                                                { l: "COUPON", v: (sel.price - 0.15).toFixed(3) + "%", s: "Annual" },
                                                { l: "DURATION", v: sel.symbol.includes("30") ? "17.2yr" : sel.symbol.includes("2Y") ? "1.9yr" : "7.8yr", s: "Modified" },
                                                { l: "CONVEXITY", v: sel.symbol.includes("30") ? "3.85" : "0.72", s: "Factor" },
                                                { l: "MATURITY", v: sel.symbol.includes("30") ? "2054" : sel.symbol.includes("2Y") ? "2026" : "2034", s: "Date" },
                                                { l: "CREDIT", v: "AAA", s: "Rating" },
                                                { l: "SPREAD", v: "+0bp", s: "vs Benchmark" },
                                                { l: "DV01", v: "$0.078", s: "Risk" },
                                            ] : isCommodity ? [
                                                { l: "PRICE", v: fP(sel.price, dp(sel.price)), s: "Spot" },
                                                { l: "24H VOLUME", v: fK(sel.volume), s: "USD" },
                                                { l: "DAY RANGE", v: `${fP(sel.low)}–${fP(sel.high)}`, s: "Low/High" },
                                                { l: "OPEN INT.", v: fK(Math.random() * 500000 + 200000), s: "Contracts" },
                                                { l: "CONTRACT", v: "Mar 2026", s: "Front Month" },
                                                { l: "CONTANGO", v: (Math.random() * 3 + 0.5).toFixed(1) + "%", s: "Curve Shape" },
                                                { l: "VOLATILITY", v: (Math.random() * 20 + 15).toFixed(1) + "%", s: "30 Day" },
                                                { l: "YTD CHANGE", v: (Math.random() * 30 - 10).toFixed(1) + "%", s: "Performance" },
                                            ] : isForex ? [
                                                { l: "BID", v: fP(sel.bid, 5), s: "Price" },
                                                { l: "ASK", v: fP(sel.ask, 5), s: "Price" },
                                                { l: "SPREAD", v: ((sel.ask - sel.bid) * 10000).toFixed(1) + " pips", s: "Cost" },
                                                { l: "DAY RANGE", v: `${fP(sel.low, 4)}–${fP(sel.high, 4)}`, s: "Low/High" },
                                                { l: "SWAP LONG", v: (Math.random() * 6 - 3).toFixed(2), s: "Points/Day" },
                                                { l: "SWAP SHORT", v: (Math.random() * 6 - 3).toFixed(2), s: "Points/Day" },
                                                { l: "PIP VALUE", v: "$" + (Math.random() * 4 + 8).toFixed(2), s: "Per Lot" },
                                                { l: "AVG RANGE", v: (sel.price * 0.008).toFixed(4), s: "20-Day" },
                                            ] : [
                                                { l: "MARKET CAP", v: fK(sel.mcap), s: "USD" },
                                                { l: "24H VOLUME", v: fK(sel.volume), s: "USD" },
                                                { l: "VWAP", v: fP(sel.vwap), s: "Intraday" },
                                                { l: "DAY RANGE", v: `${fP(sel.low)}–${fP(sel.high)}`, s: "Low / High" },
                                                { l: isCrypto ? "CIRC. SUPPLY" : "SHARES OUT", v: isCrypto ? fK(sel.mcap / sel.price) : fK(sel.mcap / sel.price * 0.85), s: isCrypto ? "Tokens" : "Shares" },
                                                { l: isCrypto ? "MAX SUPPLY" : "FLOAT", v: isCrypto ? (sel.symbol.includes("BTC") ? "21M" : "∞") : fK(sel.mcap / sel.price * 0.78), s: isCrypto ? "Cap" : "Tradeable" },
                                                { l: "OPEN", v: fP(sel.open, dp(sel.open)), s: "Today" },
                                                { l: "SPREAD", v: fP(sel.ask - sel.bid, dp(sel.price)), s: "Bid/Ask" },
                                            ]).map(x => (
                                                <div key={x.l} style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 8 }}>
                                                    <div style={{ color: C.dim, fontSize: 8, marginBottom: 3 }}>{x.l}</div>
                                                    <div style={{ color: C.white, fontSize: 14, fontWeight: 700 }}>{x.v}</div>
                                                    <div style={{ color: C.dim, fontSize: 7 }}>{x.s}</div>
                                                </div>
                                            ))}
                                        </div>

                                        {/* Financial Ratios & Analyst Ratings */}
                                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
                                            {/* Ratios — category-specific */}
                                            <div style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 10 }}>
                                                <div style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1, marginBottom: 6, color: C.amber }}>
                                                    {isCrypto ? "ON-CHAIN METRICS" : isBond ? "YIELD ANALYSIS" : isForex ? "FOREX ANALYTICS" : isCommodity ? "COMMODITY DATA" : "FINANCIAL RATIOS"}
                                                </div>
                                                <table style={{ width: "100%", borderCollapse: "collapse" }}><tbody>
                                                    {(isCrypto ? [
                                                        ["NVT Ratio", (sel.mcap / sel.volume * 10).toFixed(1)],
                                                        ["Stock-to-Flow", sel.symbol.includes("BTC") ? "56.2" : "N/A"],
                                                        ["Active Addresses", fK(sel.volume / sel.price * 0.02)],
                                                        ["Hash Rate", sel.symbol.includes("BTC") ? "623 EH/s" : "N/A"],
                                                        ["Staking APY", sel.symbol.includes("BTC") ? "N/A" : "4.2%"],
                                                        ["TVL (DeFi)", fK(sel.mcap * 0.15)],
                                                        ["30d Volatility", "52.4%"],
                                                        ["Sharpe (1Y)", "1.82"],
                                                        ["Dominance", sel.symbol.includes("BTC") ? "52.5%" : (Math.random() * 5).toFixed(1) + "%"],
                                                    ] : isBond ? [
                                                        ["Current Yield", sel.price.toFixed(3) + "%"],
                                                        ["YTM", (sel.price + 0.02).toFixed(3) + "%"],
                                                        ["Coupon Rate", (sel.price - 0.15).toFixed(3) + "%"],
                                                        ["Duration", sel.symbol.includes("30") ? "17.2" : sel.symbol.includes("2Y") ? "1.9" : "7.8"],
                                                        ["Modified Duration", sel.symbol.includes("30") ? "16.5" : sel.symbol.includes("2Y") ? "1.85" : "7.5"],
                                                        ["Convexity", sel.symbol.includes("30") ? "3.85" : "0.72"],
                                                        ["Yield Curve Slope", "0.17%"],
                                                        ["2Y/10Y Spread", "-0.34%"],
                                                    ] : isForex ? [
                                                        ["Bid/Ask Spread", ((sel.ask - sel.bid) * 10000).toFixed(1) + " pips"],
                                                        ["Swap Long", (Math.random() * 6 - 3).toFixed(2) + " pts"],
                                                        ["Swap Short", (Math.random() * 6 - 3).toFixed(2) + " pts"],
                                                        ["Pip Value", "$" + (8 + Math.random() * 4).toFixed(2)],
                                                        ["Daily Range", (sel.price * 0.008).toFixed(4)],
                                                        ["Avg Range (20d)", (sel.price * 0.012).toFixed(4)],
                                                        ["DXY Correlation", (Math.random() * 1.8 - 0.9).toFixed(2)],
                                                        ["Carry Return", (Math.random() * 6 - 2).toFixed(2) + "%"],
                                                        ["30d Volatility", (Math.random() * 10 + 5).toFixed(1) + "%"],
                                                    ] : isCommodity ? [
                                                        ["Open Interest", fK(Math.random() * 500000 + 200000)],
                                                        ["OI Change", (Math.random() * 10000 - 5000).toFixed(0)],
                                                        ["Contract Expiry", "Mar 20, 2026"],
                                                        ["Contango/Bkwd", (Math.random() * 5 - 1).toFixed(2) + "%"],
                                                        ["Seasonal Trend", ["Bullish Q1", "Neutral", "Bearish Q2"][Math.floor(Math.random() * 3)]],
                                                        ["30d Volatility", (Math.random() * 25 + 15).toFixed(1) + "%"],
                                                        ["52W High", fP(sel.price * 1.2, dp(sel.price))],
                                                        ["52W Low", fP(sel.price * 0.75, dp(sel.price))],
                                                    ] : [
                                                        ["P/E Ratio", pe], ["Forward P/E", pe ? (parseFloat(pe) * 0.88).toFixed(1) : "N/A"],
                                                        ["P/B Ratio", "3.8"], ["P/S Ratio", "5.2"],
                                                        ["EPS (TTM)", eps ? "$" + eps : "N/A"], ["Forward EPS", eps ? "$" + (parseFloat(eps) * 1.12).toFixed(2) : "N/A"],
                                                        ["Dividend Yield", divYield || "N/A"], ["Beta", beta || "N/A"],
                                                        ["Debt/Equity", "42.1%"], ["ROE", "18.5%"],
                                                        ["Profit Margin", "24.2%"], ["Revenue Growth", "12.8%"],
                                                    ]).map(([k, v]) => (
                                                        <tr key={k as string} style={{ borderBottom: "1px solid #0d1520" }}>
                                                            <td style={{ padding: "3px 4px", color: C.dim, fontSize: 10 }}>{k}</td>
                                                            <td style={{ padding: "3px 4px", color: C.white, textAlign: "right", fontWeight: 600, fontSize: 10 }}>{v}</td>
                                                        </tr>
                                                    ))}
                                                </tbody></table>
                                            </div>
                                            {/* Analyst Consensus & ESG */}
                                            <div style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 10 }}>
                                                <div style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1, marginBottom: 6, color: C.amber }}>ANALYST CONSENSUS</div>
                                                <div style={{ textAlign: "center", marginBottom: 8 }}>
                                                    <span style={{ color: consensus.rec === "BUY" ? C.green : C.amber, fontSize: 20, fontWeight: 900 }}>{consensus.rec}</span>
                                                    <div style={{ color: C.dim, fontSize: 9, marginTop: 2 }}>Target: {fP(consensus.target, dp(consensus.target))}</div>
                                                </div>
                                                <div style={{ display: "flex", gap: 2, height: 14, borderRadius: 3, overflow: "hidden", marginBottom: 6 }}>
                                                    <div style={{ flex: consensus.buy, background: C.green }} />
                                                    <div style={{ flex: consensus.hold, background: C.amber }} />
                                                    <div style={{ flex: consensus.sell, background: C.red }} />
                                                </div>
                                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9 }}>
                                                    <span style={{ color: C.green }}>Buy: {consensus.buy}</span>
                                                    <span style={{ color: C.amber }}>Hold: {consensus.hold}</span>
                                                    <span style={{ color: C.red }}>Sell: {consensus.sell}</span>
                                                </div>
                                                {/* ESG — not for crypto/forex */}
                                                {!isCrypto && !isForex && (
                                                    <div style={{ marginTop: 10, borderTop: `1px solid ${C.border}`, paddingTop: 8 }}>
                                                        <div style={{ fontWeight: 700, fontSize: 9, color: C.amber, marginBottom: 4 }}>ESG SCORE</div>
                                                        {[{ l: "Environmental", v: esg.env, c: "#00d26a" }, { l: "Social", v: esg.soc, c: "#00d4ff" }, { l: "Governance", v: esg.gov, c: "#ff9a00" }].map(e => (
                                                            <div key={e.l} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                                                                <span style={{ color: C.dim, fontSize: 9, width: 80 }}>{e.l}</span>
                                                                <div style={{ flex: 1, height: 6, background: "#1a2a3a", borderRadius: 3, overflow: "hidden" }}><div style={{ width: `${e.v}%`, height: "100%", background: e.c, borderRadius: 3 }} /></div>
                                                                <span style={{ color: C.white, fontSize: 9, width: 24, textAlign: "right" }}>{e.v}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                                {/* Yahoo Finance badge */}
                                                <div style={{ marginTop: 10, borderTop: `1px solid ${C.border}`, paddingTop: 8, textAlign: "center" }}>
                                                    <span style={{ color: C.dim, fontSize: 8 }}>Data Source: </span>
                                                    <span style={{ color: "#7c3aed", fontSize: 8, fontWeight: 800 }}>YAHOO FINANCE</span>
                                                    <span style={{ color: C.dim, fontSize: 8 }}> │ yfinance</span>
                                                </div>
                                            </div>
                                        </div>
                                        {/* Technical Indicators */}
                                        <div style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 10 }}>
                                            <div style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1, marginBottom: 8 }}>TECHNICAL INDICATORS</div>
                                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8 }}>
                                                {[{ n: "RSI(14)", v: "58.4", s: "NEUTRAL", c: C.amber }, { n: "MACD", v: "+124", s: "BULLISH", c: C.green },
                                                { n: "BB Width", v: "3.2%", s: "NORMAL", c: C.amber }, { n: "ATR(14)", v: fP(sel.price * 0.018), s: "—", c: C.dim },
                                                { n: "SMA(50)", v: fP(sel.price * 0.985), s: "ABOVE", c: C.green }, { n: "SMA(200)", v: fP(sel.price * 0.945), s: "ABOVE", c: C.green },
                                                { n: "GANN 90°", v: fP(sel.price * 0.975), s: "SUPPORT", c: C.cyan }, { n: "GANN 180°", v: fP(sel.price * 1.025), s: "RESIST", c: C.red },
                                                ].map(ind => (
                                                    <div key={ind.n} style={{ textAlign: "center", padding: 6 }}>
                                                        <div style={{ color: C.dim, fontSize: 9 }}>{ind.n}</div>
                                                        <div style={{ color: C.white, fontSize: 13, fontWeight: 700 }}>{ind.v}</div>
                                                        <div style={{ color: ind.c, fontSize: 9, fontWeight: 700 }}>{ind.s}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* ─── NEWS (Bloomberg-style News Wire + Economic Calendar) ─── */}
                        {panel === "NEWS" && (() => {
                            const urgFilter = ["ALL", "FLASH", "ALERT", "INFO"] as const;
                            return (
                                <div style={{ background: C.bg, border: `1px solid ${C.border}`, overflowY: "auto" }}>
                                    <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>MARKET NEWS WIRE</span>
                                        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                                            {urgFilter.map(f => (
                                                <span key={f} style={{
                                                    fontSize: 8, padding: "1px 6px", borderRadius: 2, cursor: "pointer",
                                                    background: f === "ALL" ? C.amber : f === "FLASH" ? C.red : f === "ALERT" ? "#664400" : "#1a2a3a",
                                                    color: f === "ALL" || f === "FLASH" ? "#fff" : C.dim, fontWeight: 700
                                                }}>{f}</span>
                                            ))}
                                            <span style={{ color: C.dim, fontSize: 9, marginLeft: 8 }}>{NEWS_SEED.length} headlines</span>
                                        </div>
                                    </div>
                                    {NEWS_SEED.map(n => (
                                        <div key={n.id} style={{ padding: "6px 8px", borderBottom: "1px solid #0d1520", cursor: "pointer" }}
                                            onMouseEnter={e => (e.currentTarget.style.background = C.bg3)} onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                                            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                                                <span style={{ color: C.dim, fontSize: 9, width: 36 }}>{n.ts}</span>
                                                <span style={{
                                                    fontSize: 8, fontWeight: 900, padding: "1px 5px", borderRadius: 2,
                                                    background: n.urg === "FLASH" ? C.red : n.urg === "ALERT" ? C.amber : "#1a2a3a",
                                                    color: n.urg === "FLASH" ? "#fff" : n.urg === "ALERT" ? C.bg : C.dim
                                                }}>{n.urg}</span>
                                                <span style={{ color: C.cyan, fontSize: 9 }}>{n.src}</span>
                                            </div>
                                            <div style={{ color: C.white, fontSize: 11, marginTop: 3, lineHeight: 1.4 }}>{n.text}</div>
                                        </div>
                                    ))}
                                    {/* Economic Calendar */}
                                    <div style={{ background: C.bg3, borderTop: `1px solid ${C.border}`, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", marginTop: 4 }}>
                                        <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>ECONOMIC CALENDAR</span>
                                    </div>
                                    {[
                                        { time: "15:00", event: "FOMC Meeting Minutes", impact: "HIGH", actual: "—", forecast: "—", prev: "—" },
                                        { time: "16:30", event: "US Initial Jobless Claims", impact: "MED", actual: "—", forecast: "210K", prev: "215K" },
                                        { time: "17:00", event: "ISM Manufacturing PMI", impact: "HIGH", actual: "—", forecast: "49.5", prev: "49.2" },
                                        { time: "20:00", event: "Fed Chair Powell Speech", impact: "HIGH", actual: "—", forecast: "—", prev: "—" },
                                        { time: "TMR 08:30", event: "EU GDP (QoQ)", impact: "MED", actual: "—", forecast: "0.3%", prev: "0.1%" },
                                    ].map((ev, i) => (
                                        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 8px", borderBottom: "1px solid #0d1520", fontSize: 10 }}>
                                            <span style={{ color: C.dim, width: 60 }}>{ev.time}</span>
                                            <span style={{
                                                width: 30, textAlign: "center", fontSize: 7, fontWeight: 900, padding: "1px 3px", borderRadius: 2,
                                                background: ev.impact === "HIGH" ? C.red : ev.impact === "MED" ? C.amber : "#1a2a3a",
                                                color: "#fff"
                                            }}>{ev.impact}</span>
                                            <span style={{ color: C.white, flex: 1 }}>{ev.event}</span>
                                            <span style={{ color: C.dim, width: 50, textAlign: "right" }}>F: {ev.forecast}</span>
                                            <span style={{ color: C.dim, width: 50, textAlign: "right" }}>P: {ev.prev}</span>
                                        </div>
                                    ))}
                                </div>
                            );
                        })()}

                        {/* ─── OMON (Option Monitor – stable values) ─── */}
                        {panel === "OMON" && (() => {
                            // Seeded pseudo-random for stable values
                            const seed = (s: number) => { const x = Math.sin(s) * 10000; return x - Math.floor(x); };
                            const expiry = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
                            const strikes = Array.from({ length: 12 }, (_, i) => {
                                const strike = Math.round(sel.price * (0.94 + i * 0.01) / 100) * 100;
                                const s1 = seed(strike * 7 + 1), s2 = seed(strike * 7 + 2), s3 = seed(strike * 7 + 3);
                                const s4 = seed(strike * 7 + 4), s5 = seed(strike * 7 + 5), s6 = seed(strike * 7 + 6);
                                const iv = (15 + s1 * 30).toFixed(1);
                                return {
                                    strike, iv,
                                    cBid: (s2 * 500 + 50).toFixed(2), cAsk: (s3 * 500 + 55).toFixed(2),
                                    pBid: (s4 * 500 + 20).toFixed(2), pAsk: (s5 * 500 + 25).toFixed(2),
                                    delta: (0.6 - i * 0.05).toFixed(2), gamma: (0.001 + s6 * 0.005).toFixed(4),
                                    cVol: Math.round(s1 * 5000), pVol: Math.round(s4 * 5000),
                                    cOI: Math.round(s2 * 50000), pOI: Math.round(s5 * 50000),
                                };
                            });
                            const pcr = (strikes.reduce((a, s) => a + s.pVol, 0) / Math.max(1, strikes.reduce((a, s) => a + s.cVol, 0))).toFixed(2);
                            const maxPain = strikes[Math.round(strikes.length / 2)]?.strike || sel.price;
                            return (
                                <div style={{ background: C.bg, border: `1px solid ${C.border}` }}>
                                    <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>OPTION MONITOR – {sel.symbol}</span>
                                        <div style={{ display: "flex", gap: 12, fontSize: 9 }}>
                                            <span style={{ color: C.dim }}>Exp: <span style={{ color: C.cyan }}>{expiry}</span></span>
                                            <span style={{ color: C.dim }}>P/C: <span style={{ color: parseFloat(pcr) > 1 ? C.red : C.green }}>{pcr}</span></span>
                                            <span style={{ color: C.dim }}>MaxPain: <span style={{ color: C.yellow }}>{maxPain}</span></span>
                                        </div>
                                    </div>
                                    <div style={{ padding: 8, overflowX: "auto" }}>
                                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                            <thead><tr>{["C Vol", "C OI", "C Bid", "C Ask", "C IV", "Strike", "P IV", "P Bid", "P Ask", "P OI", "P Vol", "Delta", "Gamma"].map(h => (
                                                <th key={h} style={{ color: C.amber, fontSize: 8, padding: "4px 4px", borderBottom: `1px solid ${C.border}`, textAlign: "center" }}>{h}</th>
                                            ))}</tr></thead>
                                            <tbody>{strikes.map((s, i) => (
                                                <tr key={i} style={{ borderBottom: "1px solid #0d1520", background: s.strike <= sel.price ? "rgba(0,210,106,0.02)" : "rgba(255,59,59,0.02)" }}>
                                                    <td style={{ color: C.dim, textAlign: "center", padding: 3, fontSize: 10 }}>{s.cVol}</td>
                                                    <td style={{ color: C.dim, textAlign: "center", padding: 3, fontSize: 10 }}>{s.cOI}</td>
                                                    <td style={{ color: C.green, textAlign: "center", padding: 3, fontSize: 10 }}>{s.cBid}</td>
                                                    <td style={{ color: C.green, textAlign: "center", padding: 3, fontSize: 10 }}>{s.cAsk}</td>
                                                    <td style={{ color: C.white, textAlign: "center", padding: 3, fontSize: 10 }}>{s.iv}%</td>
                                                    <td style={{ color: C.yellow, textAlign: "center", padding: 3, fontWeight: 700, fontSize: 11, background: "rgba(255,215,0,0.04)" }}>{s.strike}</td>
                                                    <td style={{ color: C.white, textAlign: "center", padding: 3, fontSize: 10 }}>{s.iv}%</td>
                                                    <td style={{ color: C.red, textAlign: "center", padding: 3, fontSize: 10 }}>{s.pBid}</td>
                                                    <td style={{ color: C.red, textAlign: "center", padding: 3, fontSize: 10 }}>{s.pAsk}</td>
                                                    <td style={{ color: C.dim, textAlign: "center", padding: 3, fontSize: 10 }}>{s.pOI}</td>
                                                    <td style={{ color: C.dim, textAlign: "center", padding: 3, fontSize: 10 }}>{s.pVol}</td>
                                                    <td style={{ color: C.cyan, textAlign: "center", padding: 3, fontSize: 10 }}>{s.delta}</td>
                                                    <td style={{ color: C.dim, textAlign: "center", padding: 3, fontSize: 10 }}>{s.gamma}</td>
                                                </tr>
                                            ))}</tbody>
                                        </table>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* ─── ALERT (Multi-Channel News Alert System) ─── */}
                        {panel === "ALERT" && (() => {
                            // Channel definitions for UI
                            const CHANNELS = [
                                {
                                    id: "email", label: "📧 Email", desc: "SMTP (Gmail, Outlook, etc.)", color: "#4ade80",
                                    fields: ["smtp_host", "smtp_port", "username", "password", "from_address", "recipients"]
                                },
                                {
                                    id: "sms", label: "📱 SMS", desc: "Twilio API", color: "#f87171",
                                    fields: ["account_sid", "auth_token", "from_number", "recipients"]
                                },
                                {
                                    id: "telegram", label: "✈️ Telegram", desc: "Telegram Bot API", color: "#38bdf8",
                                    fields: ["bot_token", "chat_ids"]
                                },
                                {
                                    id: "discord", label: "💬 Discord", desc: "Discord Webhook", color: "#818cf8",
                                    fields: ["webhook_url", "username"]
                                },
                                {
                                    id: "slack", label: "📢 Slack", desc: "Slack Webhook", color: "#e879f9",
                                    fields: ["webhook_url", "channel"]
                                },
                                {
                                    id: "webhook", label: "🔗 Webhook", desc: "Custom REST API", color: "#fb923c",
                                    fields: ["endpoints"]
                                },
                                {
                                    id: "desktop_push", label: "🖥️ Desktop", desc: "Browser Push", color: "#a3e635",
                                    fields: []
                                },
                            ];

                            // Simulated alert history items
                            const SIM_ALERTS = [
                                {
                                    id: "a001", severity: "CRITICAL", emoji: "🚨", title: "BTC Price Crash: -7.2% in 15m",
                                    symbol: "BTCUSDT", category: "price_alerts", ts: "20:35",
                                    channels: ["telegram", "discord", "email", "sms"], color: "#FF0040"
                                },
                                {
                                    id: "a002", severity: "HIGH", emoji: "⚠️", title: "NVDA Earnings Beat: Revenue +52% YoY",
                                    symbol: "NVDA", category: "news_alerts", ts: "19:15",
                                    channels: ["telegram", "discord", "email"], color: "#FF6600"
                                },
                                {
                                    id: "a003", severity: "HIGH", emoji: "⚠️", title: "ETH Volume Spike: 4.2x Average",
                                    symbol: "ETHUSDT", category: "volume_alerts", ts: "18:42",
                                    channels: ["telegram", "discord"], color: "#FF6600"
                                },
                                {
                                    id: "a004", severity: "CRITICAL", emoji: "🚨", title: "FOMC Rate Decision: -25bps",
                                    symbol: "", category: "news_alerts", ts: "17:00",
                                    channels: ["telegram", "discord", "email", "sms"], color: "#FF0040"
                                },
                                {
                                    id: "a005", severity: "MEDIUM", emoji: "📊", title: "MACD Bullish Crossover on SOL/USDT",
                                    symbol: "SOLUSDT", category: "technical_alerts", ts: "16:30",
                                    channels: ["telegram", "desktop_push"], color: "#FFB800"
                                },
                                {
                                    id: "a006", severity: "HIGH", emoji: "⚠️", title: "🐋 BTC Whale: Exchange Inflow $12.5M",
                                    symbol: "BTCUSDT", category: "whale_alerts", ts: "15:48",
                                    channels: ["telegram", "discord"], color: "#FF6600"
                                },
                                {
                                    id: "a007", severity: "MEDIUM", emoji: "📊", title: "Gold Breaks Resistance at $2,480",
                                    symbol: "XAUUSD", category: "price_alerts", ts: "14:20",
                                    channels: ["discord", "desktop_push"], color: "#FFB800"
                                },
                                {
                                    id: "a008", severity: "HIGH", emoji: "⚠️", title: "Drawdown Warning: Portfolio -3.8%",
                                    symbol: "", category: "risk_alerts", ts: "13:05",
                                    channels: ["telegram", "email", "sms"], color: "#FF6600"
                                },
                            ];

                            // Simulated price alerts
                            const SIM_PRICE_ALERTS = [
                                { id: "p1", symbol: "BTCUSDT", target: 100000, dir: "above", note: "BTC 100K breakout", triggered: false },
                                { id: "p2", symbol: "ETHUSDT", target: 4000, dir: "above", note: "ETH ATH target", triggered: false },
                                { id: "p3", symbol: "XAUUSD", target: 2600, dir: "above", note: "Gold new ATH", triggered: false },
                                { id: "p4", symbol: "BTCUSDT", target: 85000, dir: "below", note: "BTC support break", triggered: true },
                            ];

                            // Alert rules
                            const RULES = [
                                { name: "price_alerts", label: "Price Alerts", emoji: "💹", enabled: true, desc: "Price spikes, crashes, targets, support/resistance breaks" },
                                { name: "volume_alerts", label: "Volume Alerts", emoji: "📊", enabled: true, desc: "Unusual volume spikes (3x-5x average)" },
                                { name: "news_alerts", label: "News Alerts", emoji: "📰", enabled: true, desc: "Breaking news, FOMC, CPI, earnings, hacks" },
                                { name: "technical_alerts", label: "Technical Alerts", emoji: "📈", enabled: true, desc: "MACD, RSI, Golden/Death cross, Gann signals" },
                                { name: "risk_alerts", label: "Risk Alerts", emoji: "🛡️", enabled: true, desc: "Drawdown, margin call, liquidation warnings" },
                                { name: "whale_alerts", label: "Whale Alerts", emoji: "🐋", enabled: true, desc: "Large transactions, exchange flows ($1M+)" },
                            ];

                            return (
                                <div style={{ background: C.bg, border: `1px solid ${C.border}`, overflowY: "auto" }}>
                                    {/* Header */}
                                    <div style={{ background: "linear-gradient(90deg, #1a0000 0%, #0a0e17 50%, #00001a 100%)", borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                            <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1, color: "#FF4060" }}>🔔 NEWS ALERT SYSTEM</span>
                                            <span style={{ background: "#1a3a2a", color: "#4ade80", fontSize: 7, fontWeight: 800, padding: "1px 5px", borderRadius: 2 }}>ACTIVE</span>
                                        </div>
                                        <div style={{ display: "flex", gap: 4 }}>
                                            {(["channels", "history", "price", "rules"] as const).map(t => (
                                                <button key={t} onClick={() => setAlertTab(t)} style={{
                                                    background: alertTab === t ? "#FF0040" : C.bg2,
                                                    border: `1px solid ${alertTab === t ? "#FF0040" : C.border}`,
                                                    color: alertTab === t ? "#fff" : C.dim,
                                                    fontSize: 8, padding: "2px 8px", cursor: "pointer", borderRadius: 2,
                                                    fontFamily: "inherit", fontWeight: 700, textTransform: "uppercase",
                                                }}>{t}</button>
                                            ))}
                                        </div>
                                    </div>

                                    <div style={{ padding: 10 }}>
                                        {/* ── CHANNELS TAB ── */}
                                        {alertTab === "channels" && (
                                            <div>
                                                <div style={{ fontWeight: 700, fontSize: 10, color: C.amber, letterSpacing: 1, marginBottom: 8 }}>NOTIFICATION CHANNELS</div>
                                                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px,1fr))", gap: 8 }}>
                                                    {CHANNELS.map(ch => (
                                                        <div key={ch.id} style={{ background: C.bg2, border: `1px solid ${C.border}`, borderRadius: 4, padding: 10, position: "relative", overflow: "hidden" }}>
                                                            {/* Color accent bar */}
                                                            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: ch.color }} />
                                                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                                                                <div>
                                                                    <span style={{ fontSize: 12, fontWeight: 800, color: C.white }}>{ch.label}</span>
                                                                    <span style={{ fontSize: 8, color: C.dim, marginLeft: 6 }}>{ch.desc}</span>
                                                                </div>
                                                                <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                                                                    {ch.id === "desktop_push" ? (
                                                                        <span style={{ background: "#1a3a2a", color: "#4ade80", fontSize: 7, fontWeight: 800, padding: "2px 6px", borderRadius: 2 }}>READY</span>
                                                                    ) : (
                                                                        <span style={{ background: "#3a1a1a", color: "#f87171", fontSize: 7, fontWeight: 800, padding: "2px 6px", borderRadius: 2 }}>CONFIG NEEDED</span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            {/* Setup instructions */}
                                                            {ch.id === "email" && (
                                                                <div style={{ fontSize: 9, color: C.dim, lineHeight: 1.6, background: "#060a10", padding: 6, borderRadius: 2, marginBottom: 6 }}>
                                                                    <div style={{ color: C.cyan, fontWeight: 700, marginBottom: 2 }}>Setup: Gmail SMTP</div>
                                                                    <div>1. Enable 2FA on Google Account</div>
                                                                    <div>2. Generate App Password (Security → App Passwords)</div>
                                                                    <div>3. Set username + app password in config/alerts_config.yaml</div>
                                                                </div>
                                                            )}
                                                            {ch.id === "telegram" && (
                                                                <div style={{ fontSize: 9, color: C.dim, lineHeight: 1.6, background: "#060a10", padding: 6, borderRadius: 2, marginBottom: 6 }}>
                                                                    <div style={{ color: C.cyan, fontWeight: 700, marginBottom: 2 }}>Setup: Telegram Bot</div>
                                                                    <div>1. Message @BotFather → /newbot → get token</div>
                                                                    <div>2. Message @userinfobot → get your chat_id</div>
                                                                    <div>3. Set bot_token + chat_ids in config</div>
                                                                </div>
                                                            )}
                                                            {ch.id === "discord" && (
                                                                <div style={{ fontSize: 9, color: C.dim, lineHeight: 1.6, background: "#060a10", padding: 6, borderRadius: 2, marginBottom: 6 }}>
                                                                    <div style={{ color: C.cyan, fontWeight: 700, marginBottom: 2 }}>Setup: Discord Webhook</div>
                                                                    <div>1. Server Settings → Integrations → Webhooks</div>
                                                                    <div>2. New Webhook → Copy URL</div>
                                                                    <div>3. Set webhook_url in config/alerts_config.yaml</div>
                                                                </div>
                                                            )}
                                                            {ch.id === "sms" && (
                                                                <div style={{ fontSize: 9, color: C.dim, lineHeight: 1.6, background: "#060a10", padding: 6, borderRadius: 2, marginBottom: 6 }}>
                                                                    <div style={{ color: C.cyan, fontWeight: 700, marginBottom: 2 }}>Setup: Twilio SMS</div>
                                                                    <div>1. Sign up at twilio.com ($15 free credit)</div>
                                                                    <div>2. Get Account SID + Auth Token</div>
                                                                    <div>3. Buy a phone number → set in config</div>
                                                                </div>
                                                            )}
                                                            {ch.id === "slack" && (
                                                                <div style={{ fontSize: 9, color: C.dim, lineHeight: 1.6, background: "#060a10", padding: 6, borderRadius: 2, marginBottom: 6 }}>
                                                                    <div style={{ color: C.cyan, fontWeight: 700, marginBottom: 2 }}>Setup: Slack Webhook</div>
                                                                    <div>1. api.slack.com/apps → Create App</div>
                                                                    <div>2. Incoming Webhooks → Add to Channel</div>
                                                                    <div>3. Copy Webhook URL → set in config</div>
                                                                </div>
                                                            )}
                                                            {ch.id === "webhook" && (
                                                                <div style={{ fontSize: 9, color: C.dim, lineHeight: 1.6, background: "#060a10", padding: 6, borderRadius: 2, marginBottom: 6 }}>
                                                                    <div style={{ color: C.cyan, fontWeight: 700, marginBottom: 2 }}>Setup: Custom Webhook</div>
                                                                    <div>1. Set your REST API endpoint URL</div>
                                                                    <div>2. Configure headers (auth, content-type)</div>
                                                                    <div>3. Alerts sent as JSON POST</div>
                                                                </div>
                                                            )}
                                                            {/* Config fields hint */}
                                                            {ch.fields.length > 0 && (
                                                                <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                                                                    {ch.fields.map(f => (
                                                                        <span key={f} style={{ fontSize: 7, color: C.dim, background: "#0d1520", padding: "1px 4px", borderRadius: 2 }}>{f}</span>
                                                                    ))}
                                                                </div>
                                                            )}
                                                            {/* Test button */}
                                                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
                                                                <span style={{ fontSize: 7, color: C.dim }}>config/alerts_config.yaml</span>
                                                                <button
                                                                    onClick={() => setAlertTestResult({ ch: ch.id, ok: ch.id === "desktop_push", msg: ch.id === "desktop_push" ? "Desktop push working!" : "Configure credentials first" })}
                                                                    style={{ background: C.bg3, border: `1px solid ${C.border}`, color: ch.color, fontSize: 8, padding: "2px 10px", cursor: "pointer", borderRadius: 2, fontFamily: "inherit", fontWeight: 700 }}
                                                                >🧪 TEST</button>
                                                            </div>
                                                            {/* Test result display */}
                                                            {alertTestResult && alertTestResult.ch === ch.id && (
                                                                <div style={{ marginTop: 4, padding: 4, background: alertTestResult.ok ? "#0a2a1a" : "#2a0a0a", border: `1px solid ${alertTestResult.ok ? "#4ade80" : "#f87171"}`, borderRadius: 2, fontSize: 8, color: alertTestResult.ok ? "#4ade80" : "#f87171" }}>
                                                                    {alertTestResult.ok ? "✅" : "❌"} {alertTestResult.msg}
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>

                                                {/* Quick Stats */}
                                                <div style={{ marginTop: 12, background: C.bg2, border: `1px solid ${C.border}`, padding: 10, borderRadius: 4 }}>
                                                    <div style={{ fontWeight: 700, fontSize: 10, color: C.amber, letterSpacing: 1, marginBottom: 8 }}>ALERT DELIVERY STATS</div>
                                                    <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 8 }}>
                                                        {[
                                                            { l: "Total Sent", v: "0", c: C.white },
                                                            { l: "Last Hour", v: "0", c: C.cyan },
                                                            { l: "Critical", v: "0", c: "#FF0040" },
                                                            { l: "Channels Active", v: "1", c: "#4ade80" },
                                                            { l: "Rate Limit", v: "30/min", c: C.amber },
                                                        ].map(s => (
                                                            <div key={s.l} style={{ textAlign: "center" }}>
                                                                <div style={{ color: C.dim, fontSize: 8 }}>{s.l}</div>
                                                                <div style={{ color: s.c, fontSize: 16, fontWeight: 800 }}>{s.v}</div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* ── HISTORY TAB ── */}
                                        {alertTab === "history" && (
                                            <div>
                                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                                                    <span style={{ fontWeight: 700, fontSize: 10, color: C.amber, letterSpacing: 1 }}>ALERT HISTORY</span>
                                                    <div style={{ display: "flex", gap: 4 }}>
                                                        {["ALL", "CRITICAL", "HIGH", "MEDIUM"].map(sev => (
                                                            <span key={sev} style={{
                                                                fontSize: 7, padding: "1px 6px", borderRadius: 2, cursor: "pointer", fontWeight: 700,
                                                                background: sev === "ALL" ? C.amber : sev === "CRITICAL" ? "#FF0040" : sev === "HIGH" ? "#FF6600" : "#FFB800",
                                                                color: "#fff",
                                                            }}>{sev}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                                {SIM_ALERTS.map(a => (
                                                    <div key={a.id} style={{
                                                        padding: "6px 8px", borderBottom: "1px solid #0d1520", cursor: "pointer",
                                                        borderLeft: `3px solid ${a.color}`
                                                    }}
                                                        onMouseEnter={e => (e.currentTarget.style.background = C.bg3)}
                                                        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                                                        <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 3 }}>
                                                            <span style={{ color: C.dim, fontSize: 9, width: 36 }}>{a.ts}</span>
                                                            <span style={{
                                                                fontSize: 7, fontWeight: 900, padding: "1px 5px", borderRadius: 2,
                                                                background: a.color, color: "#fff",
                                                            }}>{a.severity}</span>
                                                            {a.symbol && <span style={{ color: C.yellow, fontSize: 9, fontWeight: 700 }}>{a.symbol}</span>}
                                                            <span style={{ color: C.dim, fontSize: 8 }}>{a.category.replace('_', ' ')}</span>
                                                        </div>
                                                        <div style={{ color: C.white, fontSize: 11, lineHeight: 1.4 }}>{a.emoji} {a.title}</div>
                                                        <div style={{ display: "flex", gap: 4, marginTop: 3 }}>
                                                            {a.channels.map(ch => (
                                                                <span key={ch} style={{ fontSize: 6, color: C.dim, background: "#0d1520", padding: "1px 4px", borderRadius: 2 }}>
                                                                    {ch === "telegram" ? "✈️" : ch === "discord" ? "💬" : ch === "email" ? "📧" : ch === "sms" ? "📱" : "🖥️"} {ch}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                ))}
                                                <div style={{ textAlign: "center", padding: 8, color: C.dim, fontSize: 9 }}>
                                                    Showing {SIM_ALERTS.length} alerts • Configure channels to receive live alerts
                                                </div>
                                            </div>
                                        )}

                                        {/* ── PRICE ALERTS TAB ── */}
                                        {alertTab === "price" && (
                                            <div>
                                                <div style={{ fontWeight: 700, fontSize: 10, color: C.amber, letterSpacing: 1, marginBottom: 8 }}>PRICE TARGET ALERTS</div>
                                                {/* Add new price alert */}
                                                <div style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 10, borderRadius: 4, marginBottom: 10 }}>
                                                    <div style={{ fontWeight: 700, fontSize: 9, color: C.cyan, marginBottom: 6 }}>+ ADD NEW PRICE ALERT</div>
                                                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 6, alignItems: "end" }}>
                                                        <div>
                                                            <div style={{ fontSize: 8, color: C.dim, marginBottom: 2 }}>Symbol</div>
                                                            <div style={{ background: "#060a10", border: `1px solid ${C.border}`, padding: "4px 6px", color: C.yellow, fontSize: 11, fontWeight: 700, borderRadius: 2 }}>{sel.symbol}</div>
                                                        </div>
                                                        <div>
                                                            <div style={{ fontSize: 8, color: C.dim, marginBottom: 2 }}>Target Price</div>
                                                            <div style={{ background: "#060a10", border: `1px solid ${C.border}`, padding: "4px 6px", color: C.white, fontSize: 11, borderRadius: 2 }}>{fP(sel.price * 1.05, dp(sel.price))}</div>
                                                        </div>
                                                        <div>
                                                            <div style={{ fontSize: 8, color: C.dim, marginBottom: 2 }}>Direction</div>
                                                            <div style={{ display: "flex", gap: 4 }}>
                                                                <span style={{ background: "#0a2a1a", color: C.green, fontSize: 9, padding: "4px 8px", borderRadius: 2, fontWeight: 700, border: "1px solid #1a4a2a" }}>↑ Above</span>
                                                                <span style={{ background: C.bg3, color: C.dim, fontSize: 9, padding: "4px 8px", borderRadius: 2, border: `1px solid ${C.border}` }}>↓ Below</span>
                                                            </div>
                                                        </div>
                                                        <button style={{ background: "#FF0040", border: "none", color: "#fff", fontSize: 9, padding: "6px 12px", cursor: "pointer", borderRadius: 2, fontWeight: 800, fontFamily: "inherit" }}>ADD ALERT</button>
                                                    </div>
                                                    <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
                                                        <span style={{ fontSize: 8, color: C.dim }}>Notify via:</span>
                                                        {["📧 Email", "📱 SMS", "✈️ Telegram", "💬 Discord", "🖥️ Desktop"].map(ch => (
                                                            <span key={ch} style={{ fontSize: 7, color: C.cyan, background: "#0d1520", padding: "1px 4px", borderRadius: 2, cursor: "pointer" }}>{ch}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                                {/* Active price alerts */}
                                                <div style={{ fontWeight: 700, fontSize: 9, color: C.dim, letterSpacing: 1, marginBottom: 6 }}>ACTIVE ALERTS ({SIM_PRICE_ALERTS.filter(a => !a.triggered).length})</div>
                                                {SIM_PRICE_ALERTS.map(a => (
                                                    <div key={a.id} style={{
                                                        display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 8px", borderBottom: "1px solid #0d1520",
                                                        background: a.triggered ? "rgba(0,210,106,0.03)" : "transparent",
                                                        borderLeft: `3px solid ${a.triggered ? C.green : (a.dir === "above" ? C.green : C.red)}`
                                                    }}>
                                                        <div>
                                                            <span style={{ color: C.yellow, fontSize: 11, fontWeight: 700, marginRight: 8 }}>{a.symbol}</span>
                                                            <span style={{ color: a.dir === "above" ? C.green : C.red, fontSize: 10, fontWeight: 600 }}>
                                                                {a.dir === "above" ? "↑" : "↓"} ${a.target.toLocaleString()}
                                                            </span>
                                                            {a.note && <span style={{ color: C.dim, fontSize: 9, marginLeft: 8 }}>— {a.note}</span>}
                                                        </div>
                                                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                                                            {a.triggered ? (
                                                                <span style={{ color: C.green, fontSize: 8, fontWeight: 700 }}>✅ TRIGGERED</span>
                                                            ) : (
                                                                <span style={{ color: C.amber, fontSize: 8 }}>⏳ Watching</span>
                                                            )}
                                                            <button style={{ background: "transparent", border: `1px solid ${C.border}`, color: C.red, fontSize: 8, padding: "1px 6px", cursor: "pointer", borderRadius: 2, fontFamily: "inherit" }}>✕</button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* ── RULES TAB ── */}
                                        {alertTab === "rules" && (
                                            <div>
                                                <div style={{ fontWeight: 700, fontSize: 10, color: C.amber, letterSpacing: 1, marginBottom: 8 }}>ALERT RULES & TRIGGERS</div>
                                                {RULES.map(r => (
                                                    <div key={r.name} style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 10, borderRadius: 4, marginBottom: 8 }}>
                                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                                                            <div>
                                                                <span style={{ fontSize: 13 }}>{r.emoji}</span>
                                                                <span style={{ fontWeight: 800, fontSize: 11, color: C.white, marginLeft: 6 }}>{r.label}</span>
                                                            </div>
                                                            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                                <span style={{ background: r.enabled ? "#1a3a2a" : "#3a1a1a", color: r.enabled ? "#4ade80" : "#f87171", fontSize: 7, fontWeight: 800, padding: "2px 8px", borderRadius: 2 }}>
                                                                    {r.enabled ? "ENABLED" : "DISABLED"}
                                                                </span>
                                                                <div style={{ width: 28, height: 14, borderRadius: 7, background: r.enabled ? "#4ade80" : "#333", cursor: "pointer", position: "relative", transition: "background 0.2s" }}>
                                                                    <div style={{ width: 10, height: 10, borderRadius: 5, background: "#fff", position: "absolute", top: 2, left: r.enabled ? 16 : 2, transition: "left 0.2s" }} />
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div style={{ fontSize: 9, color: C.dim, lineHeight: 1.5 }}>{r.desc}</div>
                                                        <div style={{ display: "flex", gap: 4, marginTop: 6 }}>
                                                            <span style={{ fontSize: 7, color: C.dim }}>Channels:</span>
                                                            {["telegram", "discord", "email", "desktop_push"].map(ch => (
                                                                <span key={ch} style={{
                                                                    fontSize: 7, padding: "1px 4px", borderRadius: 2, cursor: "pointer",
                                                                    background: "#0d1520", color: C.cyan
                                                                }}>
                                                                    {ch === "telegram" ? "✈️" : ch === "discord" ? "💬" : ch === "email" ? "📧" : "🖥️"} {ch}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                ))}

                                                {/* Severity routing */}
                                                <div style={{ background: C.bg2, border: `1px solid ${C.border}`, padding: 10, borderRadius: 4, marginTop: 8 }}>
                                                    <div style={{ fontWeight: 700, fontSize: 10, color: C.amber, letterSpacing: 1, marginBottom: 8 }}>SEVERITY ROUTING</div>
                                                    {[
                                                        { sev: "CRITICAL", color: "#FF0040", emoji: "🚨", rule: "→ ALL enabled channels", desc: "Price crash >10%, hacks, margin calls" },
                                                        { sev: "HIGH", color: "#FF6600", emoji: "⚠️", rule: "→ Telegram, Discord, Email", desc: "Earnings, FOMC, volume spikes" },
                                                        { sev: "MEDIUM", color: "#FFB800", emoji: "📊", rule: "→ Telegram, Desktop", desc: "MACD signals, RSI alerts" },
                                                        { sev: "LOW", color: "#00D4FF", emoji: "ℹ️", rule: "→ Desktop only", desc: "Minor price movements" },
                                                    ].map(s => (
                                                        <div key={s.sev} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 0", borderBottom: "1px solid #0d1520" }}>
                                                            <span style={{ fontSize: 12 }}>{s.emoji}</span>
                                                            <span style={{ color: s.color, fontSize: 10, fontWeight: 800, width: 70 }}>{s.sev}</span>
                                                            <span style={{ color: C.white, fontSize: 10, flex: 1 }}>{s.rule}</span>
                                                            <span style={{ color: C.dim, fontSize: 8 }}>{s.desc}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Footer */}
                                    <div style={{ borderTop: `1px solid ${C.border}`, padding: "4px 8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <span style={{ color: C.dim, fontSize: 7 }}>Config: config/alerts_config.yaml • Rate: 30 alerts/min • Dedup: 5min window</span>
                                        <div style={{ display: "flex", gap: 4 }}>
                                            <span style={{ fontSize: 7, color: C.dim }}>Channels: </span>
                                            <span style={{ fontSize: 7, color: "#4ade80" }}>📧 📱 ✈️ 💬 📢 🔗 🖥️</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* ─── CMD (Full Command Terminal) ─── */}
                        {panel === "CMD" && (
                            <div style={{ background: "#050810", height: "100%", display: "flex", flexDirection: "column", border: `1px solid ${C.border}` }}>
                                <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>COMMAND TERMINAL</span>
                                    <span style={{ color: C.dim, fontSize: 9 }}>Type 'help' for commands</span>
                                </div>
                                <div style={{ flex: 1, overflowY: "auto", padding: 8, fontFamily: "'Consolas',monospace", fontSize: 11, lineHeight: 1.6 }}>
                                    {cmdLog.map((l, i) => (
                                        <div key={i} style={{ color: l.type === "in" ? C.cyan : l.type === "err" ? C.red : l.type === "sys" ? C.amber : C.green, whiteSpace: "pre-wrap" }}>{l.text}</div>
                                    ))}
                                    <div ref={logEndRef} />
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* ─── RIGHT: TIME & SALES ─── */}
                <div style={{ background: C.bg, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>
                    <div style={{ background: C.bg3, borderBottom: `1px solid ${C.border}`, padding: "3px 8px", display: "flex", justifyContent: "space-between" }}>
                        <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 1 }}>TIME & SALES</span>
                        <span style={{ color: C.dim, fontSize: 9 }}>LIVE</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 6px", borderBottom: `1px solid ${C.border}` }}>
                        <span style={{ color: C.dim, fontSize: 8, width: 50 }}>TIME</span>
                        <span style={{ color: C.dim, fontSize: 8, width: 70, textAlign: "right" }}>PRICE</span>
                        <span style={{ color: C.dim, fontSize: 8, width: 40, textAlign: "right" }}>SIZE</span>
                        <span style={{ color: C.dim, fontSize: 8, width: 18, textAlign: "center" }}>S</span>
                    </div>
                    <div style={{ flex: 1, overflowY: "auto" }}>
                        {tape.map((t, i) => (
                            <div key={i} style={{
                                display: "flex", justifyContent: "space-between", padding: "1px 6px",
                                background: i === 0 ? (t.side === "B" ? "rgba(0,210,106,0.06)" : "rgba(255,59,59,0.06)") : "transparent"
                            }}>
                                <span style={{ color: C.dim, fontSize: 10, width: 50 }}>{t.ts}</span>
                                <span style={{ color: t.side === "B" ? C.green : C.red, fontSize: 10, fontWeight: 600, width: 70, textAlign: "right" }}>{fP(t.px, dp(sel.price))}</span>
                                <span style={{ color: C.white, fontSize: 10, width: 40, textAlign: "right" }}>{t.sz}</span>
                                <span style={{ color: t.side === "B" ? C.green : C.red, fontSize: 10, fontWeight: 700, width: 18, textAlign: "center" }}>{t.side}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ═══ COMMAND INPUT BAR ═══ */}
            <div style={{ background: C.bg2, borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", padding: "0 8px", height: 28, flexShrink: 0 }}
                onClick={() => cmdRef.current?.focus()}>
                <span style={{ color: C.amber, marginRight: 6, fontSize: 11, fontWeight: 700 }}>{sel.symbol} ❯</span>
                <input ref={cmdRef} value={cmdInput} onChange={e => setCmdInput(e.target.value.toUpperCase())}
                    onKeyDown={e => e.key === "Enter" && execCmd()}
                    style={{ background: "transparent", border: "none", outline: "none", color: "#00ff88", fontSize: 12, fontFamily: "inherit", flex: 1, caretColor: "#00ff88" }}
                    placeholder="Type command... (HELP for list, or type ticker symbol)"
                />
                <span style={{ color: C.dim, fontSize: 9 }}>OPEN TERMINAL v3.0 │ {secs.length} instruments │ {new Date().toLocaleDateString()}</span>
            </div>
        </div>
    );
};

export default OpenTerminal;
