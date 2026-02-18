import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Brain, TrendingUp, TrendingDown, Target, RefreshCw, Sparkles, Zap } from "lucide-react";

interface ForecastData {
  timeframe: string;
  direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  targetPrice: number;
  stopLoss: number;
  takeProfit: number;
  gannLevel: string;
  reason: string;
}

interface AIPrediction {
  shortTerm: ForecastData;
  mediumTerm: ForecastData;
  longTerm: ForecastData;
  overallSentiment: "bullish" | "bearish" | "neutral";
  sentimentScore: number;
  lastUpdate: string;
}

interface AIForecastPanelProps {
  currentPrice: number;
}

const AIForecastPanel = ({ currentPrice }: AIForecastPanelProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<AIPrediction>({
    shortTerm: {
      timeframe: "1-24 Hours",
      direction: "bullish",
      confidence: 78,
      targetPrice: currentPrice * 1.025,
      stopLoss: currentPrice * 0.985,
      takeProfit: currentPrice * 1.045,
      gannLevel: "Square of 9: 90°",
      reason: "WD Gann Square of 9 support confluence with Ehlers MAMA crossover"
    },
    mediumTerm: {
      timeframe: "1-7 Days",
      direction: "bullish",
      confidence: 72,
      targetPrice: currentPrice * 1.08,
      stopLoss: currentPrice * 0.95,
      takeProfit: currentPrice * 1.12,
      gannLevel: "Fan Angle 1x1",
      reason: "Gann Fan 1x1 angle support with planetary Jupiter trine"
    },
    longTerm: {
      timeframe: "1-4 Weeks",
      direction: "bullish",
      confidence: 65,
      targetPrice: currentPrice * 1.15,
      stopLoss: currentPrice * 0.90,
      takeProfit: currentPrice * 1.25,
      gannLevel: "Gann Box 180°",
      reason: "Gann Box 180° harmonic with Saturn cycle completion"
    },
    overallSentiment: "bullish",
    sentimentScore: 82,
    lastUpdate: new Date().toLocaleTimeString()
  });

  const regenerateForecast = () => {
    setIsLoading(true);
    setTimeout(() => {
      setPrediction(prev => ({
        ...prev,
        shortTerm: {
          ...prev.shortTerm,
          confidence: Math.floor(Math.random() * 20) + 70,
          targetPrice: currentPrice * (1 + (Math.random() * 0.05)),
        },
        mediumTerm: {
          ...prev.mediumTerm,
          confidence: Math.floor(Math.random() * 20) + 65,
        },
        longTerm: {
          ...prev.longTerm,
          confidence: Math.floor(Math.random() * 20) + 55,
        },
        sentimentScore: Math.floor(Math.random() * 30) + 60,
        lastUpdate: new Date().toLocaleTimeString()
      }));
      setIsLoading(false);
    }, 1500);
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case "bullish": return "text-success";
      case "bearish": return "text-destructive";
      default: return "text-muted-foreground";
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 75) return "bg-success text-success-foreground";
    if (confidence >= 60) return "bg-accent text-accent-foreground";
    return "bg-muted text-muted-foreground";
  };

  return (
    <Card className="p-4 md:p-6 border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary" />
          AI-Powered WD Gann Forecast
          <Badge variant="outline" className="ml-2 bg-primary/10 text-primary border-primary">
            <Sparkles className="w-3 h-3 mr-1" />
            Real-Time
          </Badge>
        </h3>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={regenerateForecast}
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Overall Sentiment */}
      <div className="mb-6 p-4 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 border border-primary/20">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">AI Sentiment Score</span>
          <span className="text-xs text-muted-foreground">Last: {prediction.lastUpdate}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {prediction.overallSentiment === "bullish" ? (
                <TrendingUp className="w-6 h-6 text-success" />
              ) : prediction.overallSentiment === "bearish" ? (
                <TrendingDown className="w-6 h-6 text-destructive" />
              ) : (
                <Target className="w-6 h-6 text-muted-foreground" />
              )}
              <span className={`text-2xl font-bold capitalize ${getDirectionColor(prediction.overallSentiment)}`}>
                {prediction.overallSentiment}
              </span>
            </div>
            <div className="h-3 bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-destructive via-accent to-success transition-all"
                style={{ 
                  width: `${prediction.sentimentScore}%`,
                  marginLeft: prediction.overallSentiment === "bearish" ? 0 : undefined
                }}
              />
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-foreground">{prediction.sentimentScore}%</p>
            <p className="text-xs text-muted-foreground">Confidence</p>
          </div>
        </div>
      </div>

      {/* Forecast Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[prediction.shortTerm, prediction.mediumTerm, prediction.longTerm].map((forecast, idx) => (
          <div 
            key={idx} 
            className="p-4 rounded-lg bg-secondary/30 border border-border hover:border-primary/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-foreground">{forecast.timeframe}</span>
              <Badge className={getConfidenceColor(forecast.confidence)}>
                {forecast.confidence}%
              </Badge>
            </div>
            
            <div className="flex items-center gap-2 mb-3">
              {forecast.direction === "bullish" ? (
                <TrendingUp className="w-5 h-5 text-success" />
              ) : (
                <TrendingDown className="w-5 h-5 text-destructive" />
              )}
              <span className={`font-semibold capitalize ${getDirectionColor(forecast.direction)}`}>
                {forecast.direction}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Target:</span>
                <span className="font-mono text-success">${forecast.targetPrice.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Stop Loss:</span>
                <span className="font-mono text-destructive">${forecast.stopLoss.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Take Profit:</span>
                <span className="font-mono text-accent">${forecast.takeProfit.toFixed(2)}</span>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-border">
              <div className="flex items-center gap-1 mb-1">
                <Zap className="w-3 h-3 text-primary" />
                <span className="text-xs font-medium text-primary">{forecast.gannLevel}</span>
              </div>
              <p className="text-xs text-muted-foreground">{forecast.reason}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default AIForecastPanel;
