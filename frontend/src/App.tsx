import { lazy, Suspense, useMemo, useCallback, memo } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import ErrorBoundary from "@/components/ErrorBoundary";
import PageLoader from "@/components/PageLoader";
import { DataFeedProvider } from "@/context/DataFeedContext";

// Dashboard is kept eager (landing page)
import Index from "./pages/Index";

// Lazy-loaded pages with prefetch hints
const Charts = lazy(() => import("./pages/Charts"));
const Scanner = lazy(() => import("./pages/Scanner"));
const Forecasting = lazy(() => import("./pages/Forecasting"));
const Gann = lazy(() => import("./pages/Gann"));
const Astro = lazy(() => import("./pages/Astro"));
const Ehlers = lazy(() => import("./pages/Ehlers"));
const AI = lazy(() => import("./pages/AI"));
const Options = lazy(() => import("./pages/Options"));
const Risk = lazy(() => import("./pages/Risk"));
const Backtest = lazy(() => import("./pages/Backtest"));
const Settings = lazy(() => import("./pages/Settings"));
const GannTools = lazy(() => import("./pages/GannTools"));
const SlippageSpike = lazy(() => import("./pages/SlippageSpike"));
const Reports = lazy(() => import("./pages/Reports"));
const Journal = lazy(() => import("./pages/Journal"));
const BackendAPI = lazy(() => import("./pages/BackendAPI"));
const PatternRecognition = lazy(() => import("./pages/PatternRecognition"));
const HFT = lazy(() => import("./pages/HFT"));
const MultiBrokerAnalysis = lazy(() => import("./pages/MultiBrokerAnalysis"));
const OpenTerminal = lazy(() => import("./pages/OpenTerminal"));
const Bookmap = lazy(() => import("./pages/Bookmap"));
const AIAgentMonitor = lazy(() => import("./pages/AIAgentMonitor"));
const TradingMode = lazy(() => import("./pages/TradingMode"));
const NotFound = lazy(() => import("./pages/NotFound"));

// Pre-allocated QueryClient with optimized settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,        // 5 seconds
      gcTime: 300000,         // 5 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      retry: 1,
    },
  },
});

// Memoized error boundary wrapper to prevent re-renders
const MemoizedErrorBoundary = memo(({ children, title }: { children: React.ReactNode; title: string }) => (
  <ErrorBoundary fallbackTitle={title}>{children}</ErrorBoundary>
));

// Route configuration for cleaner code
const routes = [
  { path: "/", component: Index, title: "Dashboard error" },
  { path: "/charts", component: Charts, title: "Charts error" },
  { path: "/scanner", component: Scanner, title: "Scanner error" },
  { path: "/forecasting", component: Forecasting, title: "Forecasting error" },
  { path: "/gann", component: Gann, title: "Gann error" },
  { path: "/astro", component: Astro, title: "Astro Cycles error" },
  { path: "/ehlers", component: Ehlers, title: "Ehlers DSP error" },
  { path: "/ai", component: AI, title: "AI Engine error" },
  { path: "/options", component: Options, title: "Options error" },
  { path: "/risk", component: Risk, title: "Risk Management error" },
  { path: "/backtest", component: Backtest, title: "Backtest error" },
  { path: "/gann-tools", component: GannTools, title: "Gann Tools error" },
  { path: "/slippage-spike", component: SlippageSpike, title: "Slippage Spike error" },
  { path: "/reports", component: Reports, title: "Reports error" },
  { path: "/journal", component: Journal, title: "Journal error" },
  { path: "/backend-api", component: BackendAPI, title: "Backend API error" },
  { path: "/pattern-recognition", component: PatternRecognition, title: "Pattern Recognition error" },
  { path: "/hft", component: HFT, title: "HFT error" },
  { path: "/multi-broker", component: MultiBrokerAnalysis, title: "Multi-Broker error" },
  { path: "/terminal", component: OpenTerminal, title: "Terminal error" },
  { path: "/bookmap", component: Bookmap, title: "Bookmap error" },
  { path: "/ai-agent-monitor", component: AIAgentMonitor, title: "AI Agent Monitor error" },
  { path: "/settings", component: Settings, title: "Settings error" },
  { path: "/trading-mode", component: TradingMode, title: "Trading Mode error" },
];

// Optimized App component
const App = () => {
  // Memoize route elements
  const routeElements = useMemo(() => 
    routes.map(({ path, component: Component, title }) => (
      <Route
        key={path}
        path={path}
        element={
          <MemoizedErrorBoundary title={title}>
            <Component />
          </MemoizedErrorBoundary>
        }
      />
    )),
    []
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <DataFeedProvider>
          <Toaster />
          <Sonner position="top-right" />
          <BrowserRouter>
            <SidebarProvider>
              <div className="flex min-h-screen bg-background w-full">
                <Navigation />
                <SidebarInset>
                  <main className="flex-1 p-4 md:p-8">
                    <ErrorBoundary fallbackTitle="Page failed to load">
                      <Suspense fallback={<PageLoader />}>
                        <Routes>
                          {routeElements}
                          <Route path="*" element={<NotFound />} />
                        </Routes>
                      </Suspense>
                    </ErrorBoundary>
                  </main>
                </SidebarInset>
              </div>
            </SidebarProvider>
          </BrowserRouter>
        </DataFeedProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
