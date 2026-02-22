// Gann Square of 9 Calculator
export const calculateSquareOf9 = (center: number) => {
  const results: Array<{ ring: number; values: number[] }> = [];

  for (let ring = 1; ring <= 5; ring++) {
    const values: number[] = [];
    const pointsInRing = ring * 8;
    const increment = (Math.pow(ring, 2) - Math.pow(ring - 1, 2)) / pointsInRing;

    for (let i = 0; i < pointsInRing; i++) {
      values.push(center + Math.pow(ring - 1, 2) + increment * i);
    }

    results.push({ ring, values });
  }

  return results;
};

// Generic Gann Square Calculator for specific constants (24.52, 90, 144, 360)
export const calculateGannSquareByConstant = (price: number, constant: number) => {
  const sqrtPrice = Math.sqrt(price);
  const angles = Array.from({ length: 25 }, (_, i) => i * 15); // 0, 15, ..., 360

  const results: Record<string, number> = {};
  angles.forEach(angle => {
    // Standard Gann Square offset calculation: (angle/360) * 2
    // But since we use a custom constant (vibration), we scale the step
    const step = (angle / 360) * (2 * (360 / constant));
    results[`${angle}°`] = Math.pow(sqrtPrice + step, 2);
  });

  return results;
};

// Gann Angles Calculator
export const calculateGannAngles = (price: number, timeUnit: number = 1) => {
  return {
    "16x1": price + (timeUnit * 16),
    "8x1": price + (timeUnit * 8),
    "4x1": price + (timeUnit * 4),
    "3x1": price + (timeUnit * 3),
    "2x1": price + (timeUnit * 2),
    "1x1": price,
    "1x2": price + (timeUnit * 0.5),
    "1x3": price + (timeUnit * 0.333),
    "1x4": price + (timeUnit * 0.25),
    "1x8": price + (timeUnit * 0.125),
    "1x16": price + (timeUnit * 0.0625),
  };
};

// Elliott Wave Projection Logic (Basic 5-wave motive pattern)
export const calculateElliottWave = (low: number, high: number) => {
  const diff = high - low;
  return {
    wave1: high,
    wave2: high - (diff * 0.618),
    wave3: high + (diff * 1.618),
    wave4: high + (diff * 1.618) - (diff * 0.382),
    wave5: high + (diff * 1.618) + (diff * 0.618),
  };
};

// Gann Wave / ZigZag Logic is usually reactive, so we'll handle the point identification in the chart component
// but we'll provide a threshold helper here.
export const getWaveThreshold = (price: number) => price * 0.02; // 2% reversal threshold

// Specific Gann Squares (24.52, 90, 360)
export const calculateGannSquareByType = (price: number, type: 24.52 | 90 | 360) => {
  const sqrtPrice = Math.sqrt(price);
  const angles = [0, 45, 90, 135, 180, 225, 270, 315, 360];
  const results: Record<string, number> = {};

  angles.forEach(angle => {
    // Step calculation based on Gann Circle of degrees
    const step = (angle / 360) * (type / price > 1 ? 0.125 : 2); // Heuristic scaling
    results[`S${type}_${angle}°`] = Math.pow(sqrtPrice + step, 2);
  });

  return results;
};

// Gann Astrology Vibration (stub logic based on planetary positions)
export const calculateGannAstroVibration = (price: number) => {
  return {
    "Mars Vibration": price * 1.0125,
    "Jupiter Confluence": price * 1.0318,
    "Saturn Support": price * 0.968,
    "Lunar Node": price * 1.005
  };
};

// Support and Resistance Calculator
export const calculateSupportResistance = (
  high: number,
  low: number,
  close: number
) => {
  const pivot = (high + low + close) / 3;

  return {
    pivot,
    resistance1: (2 * pivot) - low,
    resistance2: pivot + (high - low),
    resistance3: high + 2 * (pivot - low),
    support1: (2 * pivot) - high,
    support2: pivot - (high - low),
    support3: low - 2 * (high - pivot),
  };
};

// Time Cycles Calculator
export const calculateTimeCycles = (startDate: Date, cycleLength: number) => {
  const cycles: Array<{ cycle: number; date: Date; daysFromStart: number }> = [];

  for (let i = 1; i <= 8; i++) {
    const daysFromStart = cycleLength * i;
    const cycleDate = new Date(startDate);
    cycleDate.setDate(cycleDate.getDate() + daysFromStart);

    cycles.push({
      cycle: i,
      date: cycleDate,
      daysFromStart,
    });
  }

  return cycles;
};

// Fibonacci Levels Calculator
export const calculateFibonacciLevels = (high: number, low: number) => {
  const diff = high - low;

  return {
    level_0: low,
    level_236: low + diff * 0.236,
    level_382: low + diff * 0.382,
    level_500: low + diff * 0.5,
    level_618: low + diff * 0.618,
    level_786: low + diff * 0.786,
    level_100: high,
  };
};

// Gann Fan Calculator
export const calculateGannFan = (
  startPrice: number,
  startTime: number,
  direction: "up" | "down" = "up"
) => {
  const angles = [82.5, 75, 63.75, 45, 26.25, 15, 7.5];
  const multiplier = direction === "up" ? 1 : -1;

  return angles.map((angle) => ({
    angle,
    slope: Math.tan((angle * Math.PI) / 180) * multiplier,
    label: `${angle}°`,
  }));
};

// Gann Box Levels (Octaves)
export const calculateGannBoxLevels = (high: number, low: number) => {
  const range = high - low;
  return {
    "0/8 (Low)": low,
    "1/8 Level": low + (range * 0.125),
    "2/8 (1/4)": low + (range * 0.25),
    "3/8 Level": low + (range * 0.375),
    "4/8 (Mid)": low + (range * 0.5),
    "5/8 Level": low + (range * 0.625),
    "6/8 (3/4)": low + (range * 0.75),
    "7/8 Level": low + (range * 0.875),
    "8/8 (High)": high,
  };
};

// Gann Wave Projections
export const calculateGannWaveLevels = (high: number, low: number, currentPrice: number) => {
  const range = high - low;
  const isUpward = currentPrice >= (high + low) / 2;

  if (isUpward) {
    return {
      "Wave Extension 1.382": high + (range * 0.382),
      "Wave Extension 1.618": high + (range * 0.618),
      "Wave Extension 2.000": high + range,
      "Wave Extension 2.618": high + (range * 1.618),
    };
  } else {
    return {
      "Wave Extension 1.382": low - (range * 0.382),
      "Wave Extension 1.618": low - (range * 0.618),
      "Wave Extension 2.000": low - range,
      "Wave Extension 2.618": low - (range * 1.618),
    };
  }
};

// Square of 9 Degree Levels (0-360° in 15° increments)
export const calculateSquareOf9Degrees = (price: number) => {
  const sqrtPrice = Math.sqrt(price);
  const angles = Array.from({ length: 25 }, (_, i) => i * 15); // 0, 15, ..., 360

  const results: Record<string, number> = {};
  angles.forEach(angle => {
    const radians = (angle * Math.PI) / 180;
    const priceLevel = Math.pow(sqrtPrice + radians / (2 * Math.PI), 2);
    results[`${angle}°`] = priceLevel;
  });

  return results;
};
