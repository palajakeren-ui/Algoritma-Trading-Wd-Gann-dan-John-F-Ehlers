import { lazy, Suspense } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import ErrorBoundary from "@/components/ErrorBoundary";
import PageLoader from "@/components/PageLoader";
import { SocialWatermark } from "@/components/SocialWatermark";
import { DataFeedProvider } from "@/context/DataFeedContext";

// --- Lazy-loaded pages for code-splitting ---
// Dashboard is kept eager since it's the landing page
import Index from "./pages/Index";

// All other pages are lazy-loaded to reduce initial bundle size
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

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <DataFeedProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <SidebarProvider>
            <div className="flex min-h-screen bg-background w-full">
              <Navigation />
              <SidebarInset>
                <main className="flex-1 p-4 md:p-8">
                  <ErrorBoundary fallbackTitle="Page failed to load">
                    <Suspense fallback={<PageLoader />}>
                      <Routes>
                        <Route path="/" element={<ErrorBoundary fallbackTitle="Dashboard error"><Index /></ErrorBoundary>} />
                        <Route path="/charts" element={<ErrorBoundary fallbackTitle="Charts error"><Charts /></ErrorBoundary>} />
                        <Route path="/scanner" element={<ErrorBoundary fallbackTitle="Scanner error"><Scanner /></ErrorBoundary>} />
                        <Route path="/forecasting" element={<ErrorBoundary fallbackTitle="Forecasting error"><Forecasting /></ErrorBoundary>} />
                        <Route path="/gann" element={<ErrorBoundary fallbackTitle="Gann error"><Gann /></ErrorBoundary>} />
                        <Route path="/astro" element={<ErrorBoundary fallbackTitle="Astro Cycles error"><Astro /></ErrorBoundary>} />
                        <Route path="/ehlers" element={<ErrorBoundary fallbackTitle="Ehlers DSP error"><Ehlers /></ErrorBoundary>} />
                        <Route path="/ai" element={<ErrorBoundary fallbackTitle="AI Engine error"><AI /></ErrorBoundary>} />
                        <Route path="/options" element={<ErrorBoundary fallbackTitle="Options error"><Options /></ErrorBoundary>} />
                        <Route path="/risk" element={<ErrorBoundary fallbackTitle="Risk Management error"><Risk /></ErrorBoundary>} />
                        <Route path="/backtest" element={<ErrorBoundary fallbackTitle="Backtest error"><Backtest /></ErrorBoundary>} />
                        <Route path="/gann-tools" element={<ErrorBoundary fallbackTitle="Gann Tools error"><GannTools /></ErrorBoundary>} />
                        <Route path="/slippage-spike" element={<ErrorBoundary fallbackTitle="Slippage Spike error"><SlippageSpike /></ErrorBoundary>} />
                        <Route path="/reports" element={<ErrorBoundary fallbackTitle="Reports error"><Reports /></ErrorBoundary>} />
                        <Route path="/journal" element={<ErrorBoundary fallbackTitle="Journal error"><Journal /></ErrorBoundary>} />
                        <Route path="/backend-api" element={<ErrorBoundary fallbackTitle="Backend API error"><BackendAPI /></ErrorBoundary>} />
                        <Route path="/pattern-recognition" element={<ErrorBoundary fallbackTitle="Pattern Recognition error"><PatternRecognition /></ErrorBoundary>} />
                        <Route path="/hft" element={<ErrorBoundary fallbackTitle="HFT error"><HFT /></ErrorBoundary>} />
                        <Route path="/multi-broker" element={<ErrorBoundary fallbackTitle="Multi-Broker error"><MultiBrokerAnalysis /></ErrorBoundary>} />
                        <Route path="/terminal" element={<ErrorBoundary fallbackTitle="Terminal error"><OpenTerminal /></ErrorBoundary>} />
                        <Route path="/bookmap" element={<ErrorBoundary fallbackTitle="Bookmap error"><Bookmap /></ErrorBoundary>} />
                        <Route path="/ai-agent-monitor" element={<ErrorBoundary fallbackTitle="AI Agent Monitor error"><AIAgentMonitor /></ErrorBoundary>} />
                        <Route path="/settings" element={<ErrorBoundary fallbackTitle="Settings error"><Settings /></ErrorBoundary>} />
                        <Route path="/trading-mode" element={<ErrorBoundary fallbackTitle="Trading Mode error"><TradingMode /></ErrorBoundary>} />
                        <Route path="*" element={<NotFound />} />
                      </Routes>
                    </Suspense>
                  </ErrorBoundary>
                  <SocialWatermark />
                </main>
              </SidebarInset>
            </div>
          </SidebarProvider>
        </BrowserRouter>
      </DataFeedProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
