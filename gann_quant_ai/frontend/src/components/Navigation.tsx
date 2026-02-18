import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  Target,
  Search,
  Zap,
  Sparkles,
  Telescope,
  Activity,
  Waves,
  Brain,
  Calendar,
  Shield,
  BarChart3,
  BarChart2,
  FileText,
  BookOpen,
  Server,
  Settings
} from "lucide-react";

const navItems = [
  {
    group: "Trading", items: [
      { icon: LayoutDashboard, label: "Dashboard", path: "/" },
      { icon: TrendingUp, label: "Charts", path: "/charts" },
      { icon: Target, label: "Options Analytics", path: "/options" },
      { icon: Search, label: "Scanner", path: "/scanner" },
      { icon: Zap, label: "HFT Trading", path: "/hft" },
      { icon: Server, label: "Multi-Broker", path: "/multi-broker" },
      { icon: Activity, label: "Open Terminal", path: "/terminal" },
      { icon: BarChart2, label: "Bookmap", path: "/bookmap" },
    ]
  },
  {
    group: "Analysis", items: [
      { icon: Sparkles, label: "Gann Analysis", path: "/gann" },
      { icon: Telescope, label: "Astro Cycles", path: "/astro" },
      { icon: Activity, label: "Ehlers DSP", path: "/ehlers" },
      { icon: Waves, label: "Pattern Recognition", path: "/pattern-recognition" },
      { icon: Brain, label: "AI Models", path: "/ai" },
      { icon: Activity, label: "AI Agent Monitor", path: "/ai-agent-monitor" },
      { icon: Calendar, label: "Forecasting", path: "/forecasting" },
    ]
  },
  {
    group: "Risk & Management", items: [
      { icon: Shield, label: "Risk Manager", path: "/risk" },
      { icon: BarChart3, label: "Backtest", path: "/backtest" },
      { icon: Target, label: "Gann Tools", path: "/gann-tools" },
      { icon: Zap, label: "Slippage & Spike", path: "/slippage-spike" },
    ]
  },
  {
    group: "System", items: [
      { icon: FileText, label: "Reports", path: "/reports" },
      { icon: BookOpen, label: "Trading Journal", path: "/journal" },
      { icon: Server, label: "Backend API", path: "/backend-api" },
      { icon: Settings, label: "Settings", path: "/settings" },
    ]
  }
];

export const Navigation = () => {
  const location = useLocation();

  return (
    <Sidebar collapsible="icon" className="border-r border-border bg-card">
      <SidebarHeader className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 group-data-[collapsible=icon]:hidden">
            <div className="w-16 h-16 rounded-xl bg-primary/5 p-1 flex items-center justify-center shrink-0 border border-primary/10 shadow-[0_0_20px_rgba(var(--primary),0.15)]">
              <img
                src="/Tanpa Judul.ico"
                alt="Cenayang Market"
                className="w-full h-full object-contain"
                onError={(e) => {
                  // Fallback if image not found
                  e.currentTarget.src = "/placeholder.svg";
                }}
              />
            </div>
            <div className="flex flex-col">
              <h1 className="text-lg font-black tracking-tight text-foreground leading-none">CENAYANG</h1>
              <div className="flex items-center gap-1 mt-1">
                <span className="h-[1px] w-3 bg-primary/50" />
                <p className="text-[9px] font-bold text-primary tracking-[0.2em] leading-none uppercase">Market</p>
                <span className="h-[1px] w-3 bg-primary/50" />
              </div>
            </div>
          </div>
          <SidebarTrigger className="h-8 w-8 ml-auto" />
        </div>
      </SidebarHeader>

      <SidebarContent>
        {navItems.map((group) => (
          <SidebarGroup key={group.group}>
            <SidebarGroupLabel>{group.group}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.path}>
                    <SidebarMenuButton
                      asChild
                      isActive={location.pathname === item.path}
                      tooltip={item.label}
                      className={`
                        transition-all duration-200
                        ${location.pathname === item.path
                          ? 'bg-primary/10 text-primary hover:bg-primary/15'
                          : 'hover:bg-secondary/80'}
                      `}
                    >
                      <Link to={item.path} className="flex items-center w-full">
                        <item.icon className={`w-5 h-5 shrink-0 ${location.pathname === item.path ? 'text-primary' : 'text-muted-foreground'}`} />
                        <span className="ml-3 font-medium truncate">{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="p-4 border-t border-border bg-sidebar-footer">
        <div className="flex flex-col space-y-2 group-data-[collapsible=icon]:hidden">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Live System Online</span>
          </div>
          <p className="text-[10px] text-muted-foreground/60 transition-opacity italic">
            Last sync: {new Date().toLocaleTimeString()}
          </p>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
};
