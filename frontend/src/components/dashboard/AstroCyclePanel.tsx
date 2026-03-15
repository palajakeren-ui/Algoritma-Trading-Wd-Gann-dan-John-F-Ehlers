import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Moon, Sun, Star, TrendingUp, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

interface PlanetPosition {
  name: string;
  sign: string;
  degree: number;
  retrograde?: boolean;
  retrogradeStart?: string;
  retrogradeEnd?: string;
}

interface PlanetaryAspect {
  planet1: string;
  planet2: string;
  aspect: string;
  type: "Harmonious" | "Challenging" | "Positive" | "Neutral";
  degree: number;
  orb: number;
  duration?: string;
  intensity?: "Building" | "Peak" | "Separating";
}

const planetPositions: PlanetPosition[] = [
  { name: "Sun", sign: "Sagittarius", degree: 261.77 },
  { name: "Moon", sign: "Cancer", degree: 103.12 },
  { name: "Mercury", sign: "Leo", degree: 146.86, retrograde: true, retrogradeStart: "Aug 23", retrogradeEnd: "Sep 15" },
  { name: "Venus", sign: "Aries", degree: 25.05 },
  { name: "Mars", sign: "Aquarius", degree: 316.78 },
  { name: "Jupiter", sign: "Libra", degree: 187.54 },
  { name: "Saturn", sign: "Virgo", degree: 157.13, retrograde: true, retrogradeStart: "Jun 17", retrogradeEnd: "Nov 4" },
  { name: "Uranus", sign: "Leo", degree: 126.18, retrograde: true, retrogradeStart: "Aug 28", retrogradeEnd: "Jan 27" },
  { name: "Neptune", sign: "Aries", degree: 26.70 },
];

const planetaryAspects: PlanetaryAspect[] = [
  { planet1: "Sun", planet2: "Mercury", aspect: "Trine", type: "Harmonious", degree: 114.9, orb: 5.1, duration: "3 days left", intensity: "Separating" },
  { planet1: "Sun", planet2: "Venus", aspect: "Trine", type: "Harmonious", degree: 123.3, orb: 3.3, duration: "Peak effect", intensity: "Peak" },
  { planet1: "Sun", planet2: "Mars", aspect: "Sextile", type: "Positive", degree: 55.0, orb: 5.0, duration: "Building", intensity: "Building" },
  { planet1: "Sun", planet2: "Neptune", aspect: "Trine", type: "Harmonious", degree: 124.9, orb: 4.9, duration: "2 days left", intensity: "Separating" },
  { planet1: "Moon", planet2: "Jupiter", aspect: "Square", type: "Challenging", degree: 84.4, orb: 5.6, duration: "Ending soon", intensity: "Separating" },
  { planet1: "Moon", planet2: "Saturn", aspect: "Sextile", type: "Positive", degree: 54.0, orb: 6.0, duration: "Building", intensity: "Building" },
  { planet1: "Mercury", planet2: "Venus", aspect: "Trine", type: "Harmonious", degree: 121.8, orb: 1.8, duration: "Peak effect", intensity: "Peak" },
  { planet1: "Mercury", planet2: "Neptune", aspect: "Trine", type: "Harmonious", degree: 120.2, orb: 0.2, duration: "Peak effect", intensity: "Peak" },
];

const getZodiacIcon = (sign: string) => {
  const icons: Record<string, string> = {
    Aries: "♈", Taurus: "♉", Gemini: "♊", Cancer: "♋",
    Leo: "♌", Virgo: "♍", Libra: "♎", Scorpio: "♏",
    Sagittarius: "♐", Capricorn: "♑", Aquarius: "♒", Pisces: "♓"
  };
  return icons[sign] || "★";
};

const getAspectColor = (type: string) => {
  switch (type) {
    case "Harmonious": return "text-success border-success bg-success/10";
    case "Positive": return "text-accent border-accent bg-accent/10";
    case "Challenging": return "text-destructive border-destructive bg-destructive/10";
    default: return "text-muted-foreground border-border";
  }
};

const getIntensityColor = (intensity?: string) => {
  if (intensity === "Peak") return "text-primary font-bold";
  if (intensity === "Building") return "text-foreground";
  return "text-muted-foreground";
};

const AstroCyclePanel = () => {
  const marketSentiment = {
    direction: "Strong Bull",
    description: "Planetary alignments favor upward momentum",
    bullishPercent: 82,
  };

  const lunarPhase = {
    phase: "Last Quarter",
    illumination: 79,
    energy: "Release",
  };

  return (
    <Card className="p-4 md:p-6 border-border bg-card">
      <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
        <Star className="w-5 h-5 text-primary" />
        Astro Cycle Analysis
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
        {/* Planetary Positions */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-muted-foreground">Planetary Positions</h4>
          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {planetPositions.map((planet) => (
              <div key={planet.name} className="flex flex-col p-2 bg-secondary/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getZodiacIcon(planet.sign)}</span>
                    <div>
                      <p className="text-sm font-medium text-foreground">{planet.name}</p>
                      <p className="text-xs text-muted-foreground">{planet.sign}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-mono text-foreground">{planet.degree.toFixed(2)}°</p>
                    {planet.retrograde && (
                      <Badge variant="outline" className="text-xs text-destructive border-destructive">
                        Retrograde
                      </Badge>
                    )}
                  </div>
                </div>
                {planet.retrograde && planet.retrogradeStart && planet.retrogradeEnd && (
                  <div className="mt-1 flex items-center justify-end text-[10px] text-destructive/80 font-mono">
                    <span className="mr-1 opacity-70">Period:</span>
                    {planet.retrogradeStart} - {planet.retrogradeEnd}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Market Sentiment & Lunar Phase */}
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-gradient-to-br from-success/10 to-success/5 border border-success/20">
            <h4 className="text-sm font-semibold text-muted-foreground mb-2">Market Sentiment</h4>
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-6 h-6 text-success" />
              <span className="text-xl font-bold text-foreground">{marketSentiment.direction}</span>
            </div>
            <p className="text-xs text-muted-foreground mb-3">{marketSentiment.description}</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-success rounded-full transition-all"
                  style={{ width: `${marketSentiment.bullishPercent}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-success">{marketSentiment.bullishPercent}% Bullish</span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20">
            <h4 className="text-sm font-semibold text-muted-foreground mb-2">Lunar Phase</h4>
            <div className="flex items-center gap-3 mb-2">
              <Moon className="w-8 h-8 text-primary" />
              <div>
                <p className="text-lg font-bold text-foreground">{lunarPhase.phase}</p>
                <p className="text-xs text-muted-foreground">{lunarPhase.illumination}%</p>
              </div>
            </div>
            <Badge variant="outline" className="text-primary border-primary">
              {lunarPhase.energy}
            </Badge>
          </div>
        </div>

        {/* Planetary Aspects */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-muted-foreground">Planetary Aspects</h4>
          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {planetaryAspects.map((aspect, idx) => (
              <div key={idx} className="p-2 bg-secondary/50 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-foreground">
                    {aspect.planet1} {aspect.aspect} {aspect.planet2}
                  </span>
                  <Badge variant="outline" className={`text-xs ${getAspectColor(aspect.type)}`}>
                    {aspect.type}
                  </Badge>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{aspect.degree.toFixed(1)}°</span>
                    <span>•</span>
                    <span>Orb: {aspect.orb.toFixed(1)}°</span>
                  </div>
                  {aspect.duration && (
                    <div className={`text-[10px] font-medium flex flex-col items-end ${getIntensityColor(aspect.intensity)}`}>
                      <span className="uppercase tracking-wide opacity-80">{aspect.intensity}</span>
                      <span>{aspect.duration}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default AstroCyclePanel;
