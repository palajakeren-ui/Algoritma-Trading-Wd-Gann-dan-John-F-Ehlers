import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
    Activity,
    Brain,
    CheckCircle2,
    Clock,
    Cpu,
    MessageSquare,
    Terminal,
    Zap,
    ShieldCheck,
    AlertTriangle,
    Play,
    Square,
    RefreshCw,
    Search,
    Filter,
    Settings2,
    Trash2,
    ChevronRight,
    Database,
    CloudLightning,
    Workflow,
    ExternalLink,
    Target,
    TrendingUp,
    Gauge,
    Lock,
    Unlock,
    ArrowUpDown,
    Eye,
    Shield,
    Cog
} from "lucide-react";
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import { toast } from "sonner";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api").replace(/\/api\/?$/, "");

// ===== Agent Definitions (matching backend architecture) =====
interface AgentInfo {
    id: string;
    name: string;
    role: string;
    description: string;
    status: string;
    health: number;
    tasksCompleted: number;
    currentTask: string;
    lastAction: string;
    latency: string;
    type: string;
    color: string;
    modeRequired: number;
}

const AGENTS: AgentInfo[] = [
    {
        id: "analyst-agent",
        name: "Analyst Agent",
        role: "analyst",
        description: "Market analysis, trade explanation & user query answering. Read-only — no trading access.",
        status: "idle",
        health: 98,
        tasksCompleted: 0,
        currentTask: "Awaiting analysis request",
        lastAction: "System initialized",
        latency: "120ms",
        type: "Analysis",
        color: "#6366f1",
        modeRequired: 3,
    },
    {
        id: "regime-agent",
        name: "Regime Agent",
        role: "regime",
        description: "Market regime detection (trending/ranging/volatile/crisis). Controls mode switching M0-M3.",
        status: "idle",
        health: 96,
        tasksCompleted: 0,
        currentTask: "Monitoring market conditions",
        lastAction: "System initialized",
        latency: "250ms",
        type: "Intelligence",
        color: "#a855f7",
        modeRequired: 3,
    },
    {
        id: "optimizer-agent",
        name: "Optimizer Agent",
        role: "optimizer",
        description: "Walk-forward parameter tuning with bounded changes. All proposals require backtest validation.",
        status: "idle",
        health: 100,
        tasksCompleted: 0,
        currentTask: "Awaiting optimization request",
        lastAction: "System initialized",
        latency: "800ms",
        type: "Optimization",
        color: "#06b6d4",
        modeRequired: 3,
    },
    {
        id: "autonomous-agent",
        name: "Guarded Autonomous",
        role: "autonomous",
        description: "AI trade proposals via 6-gate validation: Risk, Exposure, Drawdown, Confidence, Rule Alignment, Cooldown.",
        status: "disabled",
        health: 100,
        tasksCompleted: 0,
        currentTask: "Disabled — requires Mode 4",
        lastAction: "Awaiting Mode 4 activation",
        latency: "50ms",
        type: "Execution Gate",
        color: "#f59e0b",
        modeRequired: 4,
    },
    {
        id: "risk-guardian",
        name: "Risk Engine",
        role: "risk",
        description: "THE ULTIMATE AUTHORITY. Position sizing, exposure caps, drawdown limits, kill switch. Cannot be overridden.",
        status: "active",
        health: 100,
        tasksCompleted: 0,
        currentTask: "Real-time portfolio monitoring",
        lastAction: "All systems nominal",
        latency: "15ms",
        type: "Safety",
        color: "#10b981",
        modeRequired: 0,
    },
];

// ===== Mode definitions =====
interface ModeInfo {
    id: number;
    name: string;
    shortName: string;
    description: string;
    engines: string[];
    agents: string[];
    color: string;
    riskLevel: string;
}

const MODES: ModeInfo[] = [
    {
        id: 0, name: "RULE ONLY", shortName: "M0",
        description: "Pure deterministic (Gann + Ehlers). No ML, no AI.",
        engines: ["Gann Engine", "Ehlers Engine"],
        agents: [],
        color: "#10b981", riskLevel: "Minimal"
    },
    {
        id: 1, name: "HYBRID", shortName: "M1",
        description: "Rule generates signal → ML confirms. Default mode.",
        engines: ["Gann Engine", "Ehlers Engine", "ML Engine"],
        agents: [],
        color: "#3b82f6", riskLevel: "Low"
    },
    {
        id: 2, name: "ML DOMINANT", shortName: "M2",
        description: "ML primary signal, Rule as structural filter.",
        engines: ["ML Engine", "Gann (filter)", "Ehlers (filter)"],
        agents: [],
        color: "#8b5cf6", riskLevel: "Medium"
    },
    {
        id: 3, name: "AI ASSISTED", shortName: "M3",
        description: "AI advisory + parameter optimization. No trade orders.",
        engines: ["Gann Engine", "Ehlers Engine", "ML Engine"],
        agents: ["Analyst", "Regime", "Optimizer"],
        color: "#f59e0b", riskLevel: "Medium-High"
    },
    {
        id: 4, name: "GUARDED AUTONOMOUS", shortName: "M4",
        description: "AI can propose trades → validation gate → approval required.",
        engines: ["All Engines"],
        agents: ["Analyst", "Regime", "Optimizer", "Autonomous"],
        color: "#ef4444", riskLevel: "High (Guarded)"
    },
];

// ===== Trade Proposal type =====
interface TradeProposal {
    proposal_id: string;
    symbol: string;
    direction: string;
    entry_price: number;
    stop_loss: number;
    take_profit: number;
    overall_confidence: number;
    status: string;
    gate_results: Record<string, { passed: boolean; message: string }>;
    ai_reasoning: string;
    timestamp: string;
}

const PERFORMANCE_DATA = [
    { name: "18:00", active: 4, usage: 65 },
    { name: "18:10", active: 5, usage: 78 },
    { name: "18:20", active: 3, usage: 45 },
    { name: "18:30", active: 5, usage: 82 },
    { name: "18:40", active: 4, usage: 70 },
    { name: "18:50", active: 4, usage: 75 },
];

const AIAgentMonitor = () => {
    const navigate = useNavigate();
    const [agents, setAgents] = useState<AgentInfo[]>(AGENTS);
    const [currentMode, setCurrentMode] = useState(1);
    const [modeName, setModeName] = useState("HYBRID");
    const [regime, setRegime] = useState("unknown");
    const [proposals, setProposals] = useState<TradeProposal[]>([]);
    const [logs, setLogs] = useState<{ id: number; time: string; agent: string; level: string; message: string }[]>([]);
    const [isLive, setIsLive] = useState(true);
    const [activeTab, setActiveTab] = useState<"cluster" | "topology" | "proposals" | "mode">("mode");
    const [commandInput, setCommandInput] = useState("");
    const [switchingMode, setSwitchingMode] = useState(false);

    // Fetch mode & agent status
    const fetchStatus = useCallback(async () => {
        try {
            const [modeRes, agentRes, regimeRes] = await Promise.allSettled([
                fetch(`${API_BASE}/api/agent/mode`),
                fetch(`${API_BASE}/api/agent/agents`),
                fetch(`${API_BASE}/api/agent/regime`),
            ]);

            if (modeRes.status === "fulfilled" && modeRes.value.ok) {
                const data = await modeRes.value.json();
                if (data.success && data.data) {
                    setCurrentMode(data.data.current_mode);
                    setModeName(data.data.mode_name || MODES[data.data.current_mode]?.name || "UNKNOWN");
                }
            }

            if (agentRes.status === "fulfilled" && agentRes.value.ok) {
                const data = await agentRes.value.json();
                if (data.success && data.agents) {
                    setAgents(prev => prev.map(a => {
                        const backendAgent = data.agents[a.role];
                        if (backendAgent) {
                            return {
                                ...a,
                                status: backendAgent.status || a.status,
                                health: backendAgent.health ?? a.health,
                                tasksCompleted: backendAgent.tasks_completed ?? a.tasksCompleted,
                                currentTask: backendAgent.current_task || a.currentTask,
                            };
                        }
                        return a;
                    }));
                }
            }

            if (regimeRes.status === "fulfilled" && regimeRes.value.ok) {
                const data = await regimeRes.value.json();
                if (data.success) {
                    setRegime(data.regime || "unknown");
                }
            }
        } catch {
            // Silent fail for non-connected state
        }
    }, []);

    // Fetch pending proposals
    const fetchProposals = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/agent/proposals`);
            if (res.ok) {
                const data = await res.json();
                if (data.success) setProposals(data.proposals || []);
            }
        } catch {
            // Silent
        }
    }, []);

    useEffect(() => {
        fetchStatus();
        fetchProposals();
        const interval = setInterval(() => {
            fetchStatus();
            fetchProposals();
        }, 5000);
        return () => clearInterval(interval);
    }, [fetchStatus, fetchProposals]);

    // Simulate live log updates
    useEffect(() => {
        if (!isLive) return;
        const interval = setInterval(() => {
            const activeAgents = agents.filter(a => a.status === "active" || a.status === "idle");
            if (activeAgents.length === 0) return;
            const randomAgent = activeAgents[Math.floor(Math.random() * activeAgents.length)];
            const messages = [
                `[${randomAgent.type}] Health check: ${randomAgent.health}% — OK`,
                `[${randomAgent.type}] Signal routed via MODE ${currentMode}`,
                `[${randomAgent.type}] Regime: ${regime} — confidence stable`,
                `[${randomAgent.type}] Risk validation passed`,
                `[${randomAgent.type}] Latency: ${randomAgent.latency}`,
            ];
            const newLog = {
                id: Date.now(),
                time: new Date().toLocaleTimeString(),
                agent: randomAgent.name,
                level: Math.random() > 0.85 ? "warning" : "info",
                message: messages[Math.floor(Math.random() * messages.length)]
            };
            setLogs(prev => [newLog, ...prev.slice(0, 29)]);
        }, 4000);
        return () => clearInterval(interval);
    }, [isLive, agents, currentMode, regime]);

    // Mode switch
    const handleModeSwitch = async (targetMode: number) => {
        if (targetMode === currentMode) return;
        setSwitchingMode(true);

        try {
            const res = await fetch(`${API_BASE}/api/agent/mode`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ target_mode: targetMode, reason: "Manual switch via UI" }),
            });
            const data = await res.json();

            if (data.success) {
                setCurrentMode(targetMode);
                setModeName(MODES[targetMode]?.name || "UNKNOWN");
                toast.success(`Switched to MODE ${targetMode}: ${MODES[targetMode]?.name}`, {
                    description: `Active engines: ${MODES[targetMode]?.engines.join(", ")}`,
                });
                fetchStatus();
            } else if (data.pending_approval) {
                toast.warning("Mode 4 requires human approval", {
                    description: "Guarded Autonomous mode has additional safety requirements.",
                });
            } else {
                toast.error(`Mode switch failed: ${data.error || "Unknown error"}`);
            }
        } catch {
            toast.error("Failed to connect to backend");
        } finally {
            setSwitchingMode(false);
        }
    };

    // Emergency revert
    const handleEmergencyRevert = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/agent/mode/revert`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reason: "Emergency revert via UI" }),
            });
            const data = await res.json();
            if (data.success) {
                setCurrentMode(0);
                setModeName("RULE ONLY");
                toast.success("⚠️ Emergency revert to MODE 0: RULE ONLY", {
                    description: "All AI agents disabled. Pure rule-based trading.",
                });
                fetchStatus();
            }
        } catch {
            toast.error("Emergency revert failed — check backend");
        }
    };

    // Approve/reject proposals
    const handleProposalAction = async (proposalId: string, action: "approve" | "reject") => {
        try {
            const res = await fetch(`${API_BASE}/api/agent/proposals/${proposalId}/${action}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reason: `${action}d via UI` }),
            });
            const data = await res.json();
            if (data.success) {
                toast.success(`Proposal ${action}d`);
                fetchProposals();
            }
        } catch {
            toast.error(`Failed to ${action} proposal`);
        }
    };

    // Terminal command handler
    const handleCommand = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && commandInput.trim()) {
            const fullCmd = commandInput.trim().toLowerCase();
            const [cmd, ...args] = fullCmd.split(" ");

            const newLogEntry = (msg: string, agent = "System", level = "info") => ({
                id: Date.now(),
                time: new Date().toLocaleTimeString(),
                agent,
                level,
                message: msg
            });

            switch (cmd) {
                case "help":
                    setLogs(prev => [newLogEntry("Commands: status, mode [0-4], revert, regime, proposals, clear, help", "Terminal"), ...prev]);
                    break;
                case "clear":
                    setLogs([]);
                    break;
                case "status": {
                    const activeCount = agents.filter(a => a.status === "active").length;
                    setLogs(prev => [newLogEntry(`Mode: ${currentMode} (${modeName}) | Regime: ${regime} | Active: ${activeCount}/${agents.length}`, "Audit"), ...prev]);
                    break;
                }
                case "mode":
                    if (args[0] && !isNaN(Number(args[0]))) {
                        handleModeSwitch(Number(args[0]));
                        setLogs(prev => [newLogEntry(`Switching to MODE ${args[0]}...`, "ModeController"), ...prev]);
                    } else {
                        setLogs(prev => [newLogEntry(`Current mode: ${currentMode} (${modeName})`, "ModeController"), ...prev]);
                    }
                    break;
                case "revert":
                    handleEmergencyRevert();
                    setLogs(prev => [newLogEntry("EMERGENCY REVERT → MODE 0", "Safety", "warning"), ...prev]);
                    break;
                case "regime":
                    setLogs(prev => [newLogEntry(`Current regime: ${regime}`, "RegimeAgent"), ...prev]);
                    break;
                case "proposals":
                    setLogs(prev => [newLogEntry(`Pending proposals: ${proposals.length}`, "AutonomousAgent"), ...prev]);
                    break;
                default:
                    setLogs(prev => [newLogEntry(`Unknown: ${cmd}. Type 'help'.`, "Error", "warning"), ...prev]);
            }
            setCommandInput("");
        }
    };

    const currentModeInfo = MODES[currentMode] || MODES[1];
    const activeAgentCount = agents.filter(a => a.modeRequired <= currentMode || a.role === "risk").length;

    return (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-700">
            {/* Dynamic Background Elements */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
                <div className="absolute top-[10%] left-[20%] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-[10%] right-[20%] w-[400px] h-[400px] bg-accent/5 rounded-full blur-[100px]" />
            </div>

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-primary/10 pb-6">
                <div>
                    <h1 className="text-4xl font-black tracking-tighter text-foreground flex items-center gap-4">
                        <div className="relative">
                            <div className="absolute -inset-1 bg-primary/20 blur-md rounded-xl" />
                            <div className="relative p-2.5 rounded-xl bg-background border border-primary/20 shadow-2xl">
                                <Workflow className="w-9 h-9 text-primary" />
                            </div>
                        </div>
                        <span>AI AGENT <span className="text-primary italic font-serif">ORCHESTRATOR</span></span>
                    </h1>
                    <div className="flex items-center gap-4 mt-2">
                        <p className="text-muted-foreground flex items-center gap-2 font-medium">
                            Institutional multi-agent system • OpenClaw architecture
                            <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border uppercase tracking-widest animate-pulse ml-2 font-bold"
                                style={{
                                    backgroundColor: `${currentModeInfo.color}10`,
                                    color: currentModeInfo.color,
                                    borderColor: `${currentModeInfo.color}30`,
                                }}>
                                <CloudLightning className="w-3 h-3" />
                                MODE {currentMode}: {modeName}
                            </span>
                        </p>
                        <div className="h-4 w-[1px] bg-primary/20 hidden md:block" />
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-[10px] font-black uppercase tracking-widest text-primary/60 hover:text-primary hover:bg-primary/10 transition-all gap-2"
                            onClick={() => navigate('/ai')}
                        >
                            <Brain className="w-3 h-3" />
                            Conventional AI
                            <ExternalLink className="w-2.5 h-2.5 opacity-50" />
                        </Button>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <Button
                        variant="destructive"
                        className="h-11 px-5 font-black shadow-lg hover:scale-105 transition-transform active:scale-95 text-xs uppercase tracking-wider gap-2"
                        onClick={handleEmergencyRevert}
                    >
                        <Shield className="w-4 h-4" />
                        EMERGENCY M0
                    </Button>
                    <Button variant="outline" className="h-11 px-5 border-primary/20 hover:bg-primary/5 backdrop-blur-sm" onClick={() => setIsLive(!isLive)}>
                        {isLive ? <Square className="w-4 h-4 mr-2 text-primary" /> : <Play className="w-4 h-4 mr-2 text-green-500" />}
                        {isLive ? "PAUSE" : "RESUME"}
                    </Button>
                </div>
            </div>

            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {[
                    { label: "Current Mode", value: `M${currentMode}`, total: modeName, icon: ArrowUpDown, color: currentModeInfo.color, glow: "shadow-blue-500/20" },
                    { label: "Market Regime", value: regime.replace(/_/g, " ").toUpperCase().slice(0, 12), total: "Detected", icon: TrendingUp, color: "#a855f7", glow: "shadow-purple-500/20" },
                    { label: "Active Agents", value: String(activeAgentCount), total: `/ ${agents.length}`, icon: Cpu, color: "#3b82f6", glow: "shadow-blue-500/20" },
                    { label: "Risk Engine", value: "ACTIVE", total: "Ultimate Authority", icon: Shield, color: "#10b981", glow: "shadow-green-500/20" },
                    { label: "Pending Proposals", value: String(proposals.length), total: currentMode === 4 ? "Mode 4 Active" : "Requires M4", icon: Target, color: "#f59e0b", glow: "shadow-yellow-500/20" },
                ].map((stat, i) => (
                    <Card key={i} className={`p-4 border-primary/5 bg-background/40 backdrop-blur-xl relative overflow-hidden group hover:border-primary/30 transition-all duration-500 ${stat.glow} shadow-lg`}>
                        <div className="absolute -right-2 -top-2 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110 duration-700">
                            <stat.icon size={70} style={{ color: stat.color }} />
                        </div>
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-md bg-background/50 border border-primary/10" style={{ color: stat.color }}>
                                <stat.icon size={12} />
                            </div>
                            <p className="text-[9px] font-black text-muted-foreground uppercase tracking-[0.15em]">{stat.label}</p>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <h3 className="text-xl font-black tracking-tight">{stat.value}</h3>
                            <span className="text-[9px] font-bold text-muted-foreground italic">{stat.total}</span>
                        </div>
                    </Card>
                ))}
            </div>

            {/* Tab Navigation */}
            <div className="flex items-center gap-4">
                <div className="h-8 w-1 bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary),0.5)]" />
                <h2 className="text-2xl font-black tracking-tighter">CONTROL CENTER</h2>
                <div className="flex-1" />
                <div className="flex items-center p-1 bg-secondary/20 rounded-xl border border-primary/5 backdrop-blur-md">
                    {(["mode", "cluster", "proposals", "topology"] as const).map(tab => (
                        <Button
                            key={tab}
                            variant={activeTab === tab ? "default" : "ghost"}
                            size="sm"
                            className="h-8 rounded-lg text-[10px] font-black uppercase tracking-widest"
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab === "mode" && <Gauge className="w-3 h-3 mr-1" />}
                            {tab === "cluster" && <Cpu className="w-3 h-3 mr-1" />}
                            {tab === "proposals" && <Target className="w-3 h-3 mr-1" />}
                            {tab === "topology" && <Workflow className="w-3 h-3 mr-1" />}
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            {tab === "proposals" && proposals.length > 0 && (
                                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-yellow-500 text-black text-[8px] font-black">{proposals.length}</span>
                            )}
                        </Button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content Area */}
                <div className="lg:col-span-2 space-y-6">
                    {/* MODE CONTROL TAB */}
                    {activeTab === "mode" && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {MODES.map((mode) => {
                                    const isActive = currentMode === mode.id;
                                    return (
                                        <Card
                                            key={mode.id}
                                            className={`p-5 border-l-4 relative overflow-hidden cursor-pointer transition-all duration-500 hover:shadow-lg group ${isActive ? "bg-primary/5 border-primary/30 shadow-xl" : "bg-background/60 backdrop-blur-md border-primary/5 hover:bg-primary/5"}`}
                                            style={{ borderLeftColor: mode.color }}
                                            onClick={() => !switchingMode && handleModeSwitch(mode.id)}
                                        >
                                            {isActive && (
                                                <div className="absolute top-2 right-2">
                                                    <div className="w-3 h-3 rounded-full bg-green-500 shadow-[0_0_10px_#22c55e] animate-pulse" />
                                                </div>
                                            )}
                                            <div className="flex items-center gap-3 mb-3">
                                                <div className="text-2xl font-black tracking-tighter" style={{ color: mode.color }}>
                                                    {mode.shortName}
                                                </div>
                                                <div>
                                                    <h3 className="text-sm font-black tracking-tight">{mode.name}</h3>
                                                    <Badge variant="outline" className="text-[8px] px-1.5 py-0 font-bold mt-0.5" style={{ borderColor: `${mode.color}30`, color: mode.color }}>
                                                        Risk: {mode.riskLevel}
                                                    </Badge>
                                                </div>
                                            </div>
                                            <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">{mode.description}</p>
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-1 text-[9px] text-muted-foreground font-bold uppercase tracking-wider">
                                                    <Cog className="w-3 h-3" /> Engines: {mode.engines.join(", ")}
                                                </div>
                                                <div className="flex items-center gap-1 text-[9px] text-muted-foreground font-bold uppercase tracking-wider">
                                                    <Brain className="w-3 h-3" /> Agents: {mode.agents.length ? mode.agents.join(", ") : "None"}
                                                </div>
                                            </div>
                                            {isActive && (
                                                <div className="mt-3 flex items-center gap-1 text-[9px] font-black text-green-500 uppercase tracking-widest">
                                                    <CheckCircle2 className="w-3 h-3" /> ACTIVE
                                                </div>
                                            )}
                                        </Card>
                                    );
                                })}
                            </div>

                            {/* Signal Routing Diagram */}
                            <Card className="p-6 border-primary/10 bg-background/60 backdrop-blur-md">
                                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                                    <ArrowUpDown className="w-4 h-4 text-primary" />
                                    SIGNAL ROUTING PATH — MODE {currentMode}
                                </h3>
                                <div className="flex items-center justify-between gap-2 text-center">
                                    {["Rule Engine", "ML Engine", "Strategy Router", "Risk Engine", "Execution"].map((step, i) => {
                                        const isEngineActive =
                                            i === 0 ? true :
                                                i === 1 ? currentMode >= 1 :
                                                    true;
                                        return (
                                            <div key={step} className="flex items-center gap-2">
                                                <div className={`px-3 py-2 rounded-lg border text-[9px] font-black uppercase tracking-wider transition-all ${isEngineActive ? "border-primary/30 bg-primary/10 text-primary" : "border-primary/5 bg-background/30 text-muted-foreground/30"}`}>
                                                    {step}
                                                </div>
                                                {i < 4 && (
                                                    <ChevronRight className={`w-4 h-4 ${isEngineActive ? "text-primary/50" : "text-muted-foreground/20"}`} />
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                                {currentMode >= 3 && (
                                    <div className="mt-3 flex items-center justify-center gap-2 text-[9px] font-bold text-yellow-500">
                                        <Brain className="w-3 h-3" />
                                        AI Agents active — advisory {currentMode === 4 ? "+ trade proposals" : "only"}
                                    </div>
                                )}
                            </Card>
                        </div>
                    )}

                    {/* CLUSTER (AGENTS) TAB */}
                    {activeTab === "cluster" && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            {agents.map((agent) => {
                                const isEnabled = agent.modeRequired <= currentMode || agent.role === "risk";
                                return (
                                    <Card key={agent.id} className={`p-6 border-l-4 relative overflow-hidden transition-all duration-500 group ${isEnabled ? "bg-background/60 backdrop-blur-md hover:bg-primary/5" : "bg-background/30 opacity-60"}`} style={{ borderLeftColor: agent.color }}>
                                        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary/5 to-transparent rounded-bl-full pointer-events-none" />

                                        <div className="flex items-start justify-between mb-4 relative z-10">
                                            <div className="flex items-center gap-3">
                                                <div className="relative">
                                                    <div className="absolute -inset-2 blur-lg opacity-20 group-hover:opacity-40 transition-opacity" style={{ backgroundColor: agent.color }} />
                                                    <div className="relative p-2.5 rounded-xl bg-background border border-primary/10 shadow-lg" style={{ color: agent.color }}>
                                                        {agent.role === "risk" ? <Shield size={20} /> : <Brain size={20} />}
                                                    </div>
                                                </div>
                                                <div>
                                                    <h3 className="font-black text-base leading-tight tracking-tight">{agent.name}</h3>
                                                    <div className="flex items-center gap-2 mt-0.5">
                                                        <Badge variant="outline" className="text-[8px] px-1.5 py-0 border-primary/5 bg-primary/5 font-black uppercase tracking-widest h-4">
                                                            {agent.type}
                                                        </Badge>
                                                        <Badge variant="outline" className="text-[8px] px-1.5 py-0 font-bold h-4" style={{ borderColor: `${agent.color}30`, color: agent.color }}>
                                                            M{agent.modeRequired}+
                                                        </Badge>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                <div className={`h-2.5 w-2.5 rounded-full ${isEnabled ? (agent.status === 'active' ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-yellow-500 shadow-[0_0_8px_#eab308]') : 'bg-gray-500'} animate-pulse`} />
                                                <span className="text-[8px] font-black uppercase tracking-tighter text-muted-foreground">
                                                    {isEnabled ? agent.status : "LOCKED"}
                                                </span>
                                            </div>
                                        </div>

                                        <p className="text-[11px] text-foreground/70 mb-4 leading-relaxed">{agent.description}</p>

                                        <div className="bg-background/40 backdrop-blur-sm rounded-xl p-3 border border-primary/5 space-y-2 shadow-inner">
                                            <div className="flex items-center justify-between text-xs">
                                                <span className="text-muted-foreground font-bold flex items-center gap-1.5 uppercase tracking-wider text-[9px]">
                                                    <Activity className="w-3 h-3" /> Health
                                                </span>
                                                <span className="font-black text-primary">{agent.health}%</span>
                                            </div>
                                            <Progress value={agent.health} className="h-1.5 bg-background shadow-inner" />
                                            <div className="grid grid-cols-2 gap-3 pt-1">
                                                <div>
                                                    <p className="text-[8px] text-muted-foreground uppercase font-black tracking-widest">Tasks</p>
                                                    <p className="text-sm font-black">{agent.tasksCompleted}</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-[8px] text-muted-foreground uppercase font-black tracking-widest">Latency</p>
                                                    <p className="text-sm font-black flex items-center justify-end gap-1">
                                                        <Clock className="w-3 h-3 text-muted-foreground" />
                                                        {agent.latency}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        {!isEnabled && (
                                            <div className="mt-3 flex items-center gap-2 text-[9px] font-bold text-muted-foreground">
                                                <Lock className="w-3 h-3" /> Requires Mode {agent.modeRequired}+
                                            </div>
                                        )}
                                    </Card>
                                );
                            })}
                        </div>
                    )}

                    {/* PROPOSALS TAB */}
                    {activeTab === "proposals" && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            {currentMode < 4 && (
                                <Card className="p-6 border-yellow-500/20 bg-yellow-500/5 border-l-4 border-l-yellow-500">
                                    <div className="flex items-center gap-3">
                                        <Lock className="w-5 h-5 text-yellow-500" />
                                        <div>
                                            <h3 className="font-black text-sm">Mode 4 Required</h3>
                                            <p className="text-[11px] text-muted-foreground mt-1">
                                                Trade proposals are only available in MODE 4 (Guarded Autonomous).
                                                Switch to Mode 4 to enable the Autonomous Agent.
                                            </p>
                                        </div>
                                        <Button size="sm" className="ml-auto" onClick={() => handleModeSwitch(4)}>
                                            Enable M4
                                        </Button>
                                    </div>
                                </Card>
                            )}

                            {proposals.length === 0 ? (
                                <Card className="p-12 text-center border-primary/5 bg-background/60">
                                    <Target className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                                    <h3 className="font-black text-lg mb-2">No Pending Proposals</h3>
                                    <p className="text-sm text-muted-foreground">
                                        {currentMode === 4 ? "The Autonomous Agent hasn't generated proposals yet." : "Switch to Mode 4 to receive AI trade proposals."}
                                    </p>
                                </Card>
                            ) : (
                                proposals.map((proposal) => (
                                    <Card key={proposal.proposal_id} className="p-6 border-primary/10 bg-background/60 backdrop-blur-md border-l-4 border-l-yellow-500">
                                        <div className="flex items-start justify-between mb-4">
                                            <div>
                                                <div className="flex items-center gap-3">
                                                    <h3 className="font-black text-lg">
                                                        {proposal.direction.toUpperCase()} {proposal.symbol}
                                                    </h3>
                                                    <Badge className={proposal.status === "gate_passed" ? "bg-green-500/10 text-green-500 border-green-500/20" : "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"}>
                                                        {proposal.status.replace("_", " ").toUpperCase()}
                                                    </Badge>
                                                </div>
                                                <p className="text-[10px] text-muted-foreground mt-1 font-mono">{proposal.proposal_id}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-2xl font-black" style={{ color: proposal.overall_confidence >= 0.75 ? "#10b981" : "#f59e0b" }}>
                                                    {(proposal.overall_confidence * 100).toFixed(0)}%
                                                </p>
                                                <p className="text-[9px] text-muted-foreground font-bold uppercase">Confidence</p>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-3 gap-4 mb-4">
                                            <div className="p-3 rounded-lg bg-background/50 border border-primary/5">
                                                <p className="text-[8px] text-muted-foreground uppercase font-black tracking-widest">Entry</p>
                                                <p className="text-sm font-black">${proposal.entry_price.toLocaleString()}</p>
                                            </div>
                                            <div className="p-3 rounded-lg bg-background/50 border border-red-500/10">
                                                <p className="text-[8px] text-red-400 uppercase font-black tracking-widest">Stop Loss</p>
                                                <p className="text-sm font-black text-red-400">${proposal.stop_loss.toLocaleString()}</p>
                                            </div>
                                            <div className="p-3 rounded-lg bg-background/50 border border-green-500/10">
                                                <p className="text-[8px] text-green-400 uppercase font-black tracking-widest">Take Profit</p>
                                                <p className="text-sm font-black text-green-400">${proposal.take_profit.toLocaleString()}</p>
                                            </div>
                                        </div>

                                        {/* Validation Gates */}
                                        {proposal.gate_results && Object.keys(proposal.gate_results).length > 0 && (
                                            <div className="mb-4">
                                                <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground mb-2">Validation Gate Results</p>
                                                <div className="grid grid-cols-3 gap-2">
                                                    {Object.entries(proposal.gate_results).map(([gate, result]) => (
                                                        <div key={gate} className={`p-2 rounded-lg border text-[9px] ${result.passed ? "border-green-500/20 bg-green-500/5" : "border-red-500/20 bg-red-500/5"}`}>
                                                            <div className="flex items-center gap-1">
                                                                {result.passed ? <CheckCircle2 className="w-3 h-3 text-green-500" /> : <AlertTriangle className="w-3 h-3 text-red-500" />}
                                                                <span className="font-black uppercase">{gate.replace(/_/g, " ").slice(0, 15)}</span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {proposal.ai_reasoning && (
                                            <div className="p-3 rounded-lg bg-background/30 border border-primary/5 mb-4">
                                                <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground mb-1">AI Reasoning</p>
                                                <p className="text-[11px] text-foreground/80 whitespace-pre-line">{proposal.ai_reasoning}</p>
                                            </div>
                                        )}

                                        {proposal.status === "gate_passed" && (
                                            <div className="flex items-center gap-3">
                                                <Button className="flex-1 bg-green-600 hover:bg-green-700 font-black" onClick={() => handleProposalAction(proposal.proposal_id, "approve")}>
                                                    <CheckCircle2 className="w-4 h-4 mr-2" />
                                                    APPROVE TRADE
                                                </Button>
                                                <Button variant="destructive" className="flex-1 font-black" onClick={() => handleProposalAction(proposal.proposal_id, "reject")}>
                                                    <AlertTriangle className="w-4 h-4 mr-2" />
                                                    REJECT
                                                </Button>
                                            </div>
                                        )}
                                    </Card>
                                ))
                            )}
                        </div>
                    )}

                    {/* TOPOLOGY TAB */}
                    {activeTab === "topology" && (
                        <Card className="h-[600px] border-primary/10 bg-background/60 backdrop-blur-md relative overflow-hidden p-6 animate-in fade-in zoom-in-95 duration-500">
                            <div className="absolute top-4 left-6 z-10">
                                <h3 className="text-sm font-black text-primary tracking-[0.3em] uppercase mb-1">Agent Mesh Topology</h3>
                                <p className="text-[10px] text-muted-foreground font-medium italic">Mode {currentMode}: {modeName} — Active pathways</p>
                            </div>

                            <div className="relative w-full h-full flex items-center justify-center">
                                <svg className="w-full h-full" viewBox="0 0 800 600">
                                    <defs>
                                        <radialGradient id="meshGlow" cx="50%" cy="50%" r="50%">
                                            <stop offset="0%" stopColor={currentModeInfo.color} stopOpacity="0.1" />
                                            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                                        </radialGradient>
                                        <filter id="glow">
                                            <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
                                            <feMerge>
                                                <feMergeNode in="coloredBlur" />
                                                <feMergeNode in="SourceGraphic" />
                                            </feMerge>
                                        </filter>
                                    </defs>

                                    {/* Central Hub */}
                                    <circle cx="400" cy="300" r="100" fill="url(#meshGlow)" className="animate-pulse" />
                                    <circle cx="400" cy="300" r="40" fill="none" stroke={`${currentModeInfo.color}33`} strokeWidth="1" strokeDasharray="5,5" />

                                    {/* Neural Pathways */}
                                    {agents.map((agent, i) => {
                                        const angle = (i * 2 * Math.PI) / agents.length - Math.PI / 2;
                                        const x = 400 + 220 * Math.cos(angle);
                                        const y = 300 + 220 * Math.sin(angle);
                                        const isEnabled = agent.modeRequired <= currentMode || agent.role === "risk";
                                        return (
                                            <g key={`link-${agent.id}`}>
                                                <line x1="400" y1="300" x2={x} y2={y}
                                                    stroke={agent.color} strokeWidth={isEnabled ? 1.5 : 0.5}
                                                    strokeOpacity={isEnabled ? 0.3 : 0.1}
                                                    strokeDasharray={isEnabled ? "none" : "4,4"}
                                                />
                                                {isEnabled && (
                                                    <circle r="2" fill="#fff">
                                                        <animateMotion
                                                            path={`M 400 300 L ${x} ${y}`}
                                                            dur={`${2 + Math.random() * 3}s`}
                                                            repeatCount="indefinite"
                                                        />
                                                    </circle>
                                                )}
                                            </g>
                                        );
                                    })}

                                    {/* Agent Nodes */}
                                    {agents.map((agent, i) => {
                                        const angle = (i * 2 * Math.PI) / agents.length - Math.PI / 2;
                                        const x = 400 + 220 * Math.cos(angle);
                                        const y = 300 + 220 * Math.sin(angle);
                                        const isEnabled = agent.modeRequired <= currentMode || agent.role === "risk";
                                        return (
                                            <g key={agent.id} className="cursor-pointer">
                                                <circle cx={x} cy={y} r="25" fill="#0c0c0c"
                                                    stroke={agent.color}
                                                    strokeWidth={isEnabled ? 2 : 1}
                                                    strokeOpacity={isEnabled ? 1 : 0.3}
                                                    filter={isEnabled ? "url(#glow)" : "none"}
                                                />
                                                <text x={x} y={y + 40} textAnchor="middle" fill="#fff" fontSize="9" fontWeight="900" className="uppercase">{agent.name.split(" ")[0]}</text>
                                                <text x={x} y={y + 52} textAnchor="middle" fill="#666" fontSize="7">{isEnabled ? `M${agent.modeRequired}+` : "LOCKED"}</text>
                                            </g>
                                        );
                                    })}
                                </svg>

                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-primary/20 blur-2xl rounded-full" />
                                        <Workflow className="w-10 h-10 text-primary relative mx-auto mb-1" />
                                        <h4 className="text-[9px] font-black tracking-[.3em] uppercase" style={{ color: currentModeInfo.color }}>
                                            M{currentMode}
                                        </h4>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    )}
                </div>

                {/* Right Column: Terminal & Analytics */}
                <div className="space-y-6">
                    <Card className="flex flex-col h-[480px] border-primary/10 bg-background/80 backdrop-blur-xl overflow-hidden shadow-2xl relative border-t-2 border-primary/20">
                        <div className="p-4 border-b border-primary/10 bg-secondary/20 flex items-center justify-between">
                            <h2 className="text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-primary" />
                                ORCHESTRATOR TERMINAL
                            </h2>
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-[8px] h-4 px-1.5 font-bold" style={{ borderColor: `${currentModeInfo.color}30`, color: currentModeInfo.color }}>
                                    M{currentMode}
                                </Badge>
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_#22c55e]" />
                            </div>
                        </div>
                        <div className="flex-1 overflow-y-auto p-5 space-y-3 font-mono text-[11px]">
                            {logs.map((log) => (
                                <div key={log.id} className="group border-l-2 border-primary/10 pl-4 py-0.5 hover:border-primary transition-all duration-300">
                                    <div className="flex items-center justify-between mb-1">
                                        <div className="flex items-center gap-2">
                                            <span className="text-primary font-black opacity-60 tabular-nums">[{log.time}]</span>
                                            <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-tighter ${log.level === 'warning' ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/30' : 'bg-primary/10 text-primary border border-primary/10'}`}>
                                                {log.agent}
                                            </span>
                                        </div>
                                    </div>
                                    <p className="text-foreground/80 leading-relaxed tabular-nums font-medium text-[10px]">{log.message}</p>
                                </div>
                            ))}
                        </div>
                        <div className="p-3 border-t border-primary/10 bg-secondary/10 flex items-center gap-3">
                            <div className="flex-1 h-10 bg-background border border-primary/10 rounded-lg px-3 flex items-center text-[10px] text-muted-foreground font-mono shadow-inner focus-within:border-primary/50 transition-all relative overflow-hidden">
                                <span className="opacity-50 mr-2 shrink-0">$</span>
                                <span className="text-primary/70 shrink-0 mr-2">agent@m{currentMode}: ~</span>
                                <input
                                    value={commandInput}
                                    onChange={(e) => setCommandInput(e.target.value)}
                                    onKeyDown={handleCommand}
                                    placeholder="status | mode [0-4] | revert | help"
                                    className="bg-transparent border-none outline-none flex-1 text-foreground placeholder:text-muted-foreground/30 h-full w-full font-mono text-[11px]"
                                />
                            </div>
                            <Button size="icon" variant="ghost" className="h-10 w-10 hover:bg-red-500/10 hover:text-red-500 rounded-lg" onClick={() => setLogs([])}>
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>
                    </Card>

                    <Card className="p-6 border-primary/10 bg-background/80 backdrop-blur-xl shadow-xl relative overflow-hidden">
                        <div className="absolute bottom-0 right-0 w-24 h-24 bg-primary/5 rounded-tl-full -z-10" />
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                <Activity className="w-4 h-4 text-primary" />
                                SYSTEM UTILIZATION
                            </h2>
                            <Badge className="bg-primary/10 text-primary hover:bg-primary/20 border-none font-black text-[9px]">REAL-TIME</Badge>
                        </div>
                        <div className="h-[180px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={PERFORMANCE_DATA}>
                                    <defs>
                                        <linearGradient id="colorUsage" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={currentModeInfo.color} stopOpacity={0.4} />
                                            <stop offset="95%" stopColor={currentModeInfo.color} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#666', fontWeight: 700 }} />
                                    <YAxis hide />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(10,10,10,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}
                                        itemStyle={{ fontSize: '10px', fontWeight: 900, color: currentModeInfo.color }}
                                    />
                                    <Area type="monotone" dataKey="usage" stroke={currentModeInfo.color} strokeWidth={3} fillOpacity={1} fill="url(#colorUsage)" animationDuration={2000} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-2">
                            <div className="p-3 rounded-xl bg-background/40 border border-primary/5 text-center shadow-inner hover:border-primary/20 transition-colors">
                                <p className="text-[8px] font-black text-muted-foreground uppercase mb-1 tracking-widest">Signal Rate</p>
                                <p className="text-xs font-black text-foreground">12.4 sig/s</p>
                            </div>
                            <div className="p-3 rounded-xl bg-background/40 border border-primary/5 text-center shadow-inner hover:border-primary/20 transition-colors">
                                <p className="text-[8px] font-black text-muted-foreground uppercase mb-1 tracking-widest">Avg Latency</p>
                                <p className="text-xs font-black text-foreground">245ms</p>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default AIAgentMonitor;
