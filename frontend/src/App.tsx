import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import Index from "./pages/Index";
import Charts from "./pages/Charts";
import Scanner from "./pages/Scanner";
import Forecasting from "./pages/Forecasting";
import Gann from "./pages/Gann";
import Astro from "./pages/Astro";
import Ehlers from "./pages/Ehlers";
import AI from "./pages/AI";
import Options from "./pages/Options";
import Risk from "./pages/Risk";
import Backtest from "./pages/Backtest";
import Settings from "./pages/Settings";
import GannTools from "./pages/GannTools";
import SlippageSpike from "./pages/SlippageSpike";
import Reports from "./pages/Reports";
import Journal from "./pages/Journal";
import BackendAPI from "./pages/BackendAPI";
import PatternRecognition from "./pages/PatternRecognition";
import HFT from "./pages/HFT";
import MultiBrokerAnalysis from "./pages/MultiBrokerAnalysis";
import OpenTerminal from "./pages/OpenTerminal";
import Bookmap from "./pages/Bookmap";

import NotFound from "./pages/NotFound";
import { SocialWatermark } from "@/components/SocialWatermark";
import { DataFeedProvider } from "@/context/DataFeedContext";

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
                  <Routes>
                    <Route path="/" element={<Index />} />
                    <Route path="/charts" element={<Charts />} />
                    <Route path="/scanner" element={<Scanner />} />
                    <Route path="/forecasting" element={<Forecasting />} />
                    <Route path="/gann" element={<Gann />} />
                    <Route path="/astro" element={<Astro />} />
                    <Route path="/ehlers" element={<Ehlers />} />
                    <Route path="/ai" element={<AI />} />
                    <Route path="/options" element={<Options />} />
                    <Route path="/risk" element={<Risk />} />
                    <Route path="/backtest" element={<Backtest />} />
                    <Route path="/gann-tools" element={<GannTools />} />
                    <Route path="/slippage-spike" element={<SlippageSpike />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/journal" element={<Journal />} />
                    <Route path="/backend-api" element={<BackendAPI />} />
                    <Route path="/pattern-recognition" element={<PatternRecognition />} />
                    <Route path="/hft" element={<HFT />} />
                    <Route path="/multi-broker" element={<MultiBrokerAnalysis />} />
                    <Route path="/terminal" element={<OpenTerminal />} />
                    <Route path="/bookmap" element={<Bookmap />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
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
