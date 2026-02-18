// John F. Ehlers' Digital Signal Processing Calculations

interface MAMAResult {
  mama: number;
  fama: number;
  phase: number;
  period: number;
}

/**
 * MESA Adaptive Moving Average (MAMA) and Following Adaptive Moving Average (FAMA)
 * Adaptive moving averages that adjust to market conditions
 * @param prices - Array of price values
 * @param fastLimit - Fast limit (default: 0.5)
 * @param slowLimit - Slow limit (default: 0.05)
 * @returns Array of MAMA/FAMA results
 */
export function calculateMAMAFAMA(
  prices: number[],
  fastLimit: number = 0.5,
  slowLimit: number = 0.05
): MAMAResult[] {
  const results: MAMAResult[] = [];
  
  if (prices.length < 6) {
    return results;
  }

  let mama = prices[0];
  let fama = prices[0];
  let phase = 0;
  let period = 0;
  let smooth = 0;
  let detrender = 0;
  let I1 = 0;
  let Q1 = 0;
  let jI = 0;
  let jQ = 0;
  let I2 = 0;
  let Q2 = 0;
  let Re = 0;
  let Im = 0;

  for (let i = 0; i < prices.length; i++) {
    // Smooth and detrend the price data
    if (i >= 4) {
      smooth = (4 * prices[i] + 3 * prices[i - 1] + 2 * prices[i - 2] + prices[i - 3]) / 10;
      detrender = (0.0962 * smooth + 0.5769 * (i >= 2 ? prices[i - 2] : prices[i]) - 
                   0.5769 * (i >= 4 ? prices[i - 4] : prices[i]) - 
                   0.0962 * (i >= 6 ? prices[i - 6] : prices[i])) * (0.075 * period + 0.54);

      // Compute InPhase and Quadrature components
      Q1 = (0.0962 * detrender + 0.5769 * (i >= 2 ? prices[i - 2] : detrender) - 
            0.5769 * (i >= 4 ? prices[i - 4] : detrender) - 
            0.0962 * (i >= 6 ? prices[i - 6] : detrender)) * (0.075 * period + 0.54);
      I1 = i >= 3 ? prices[i - 3] : detrender;

      // Advance the phase of I1 and Q1 by 90 degrees
      jI = (0.0962 * I1 + 0.5769 * (i >= 2 ? prices[i - 2] : I1) - 
            0.5769 * (i >= 4 ? prices[i - 4] : I1) - 
            0.0962 * (i >= 6 ? prices[i - 6] : I1)) * (0.075 * period + 0.54);
      jQ = (0.0962 * Q1 + 0.5769 * (i >= 2 ? prices[i - 2] : Q1) - 
            0.5769 * (i >= 4 ? prices[i - 4] : Q1) - 
            0.0962 * (i >= 6 ? prices[i - 6] : Q1)) * (0.075 * period + 0.54);

      // Phasor addition for 3-bar averaging
      I2 = I1 - jQ;
      Q2 = Q1 + jI;

      // Smooth the I and Q components
      I2 = 0.2 * I2 + 0.8 * (i > 0 ? results[i - 1]?.phase || I2 : I2);
      Q2 = 0.2 * Q2 + 0.8 * (i > 0 ? results[i - 1]?.period || Q2 : Q2);

      // Homodyne Discriminator
      Re = I2 * (i > 0 ? I2 : 1) + Q2 * (i > 0 ? Q2 : 1);
      Im = I2 * (i > 0 ? Q2 : 1) - Q2 * (i > 0 ? I2 : 1);

      Re = 0.2 * Re + 0.8 * (i > 0 ? Re : 0);
      Im = 0.2 * Im + 0.8 * (i > 0 ? Im : 0);

      // Compute the phase
      if (Im !== 0 && Re !== 0) {
        period = 360 / (Math.atan(Im / Re) * 180 / Math.PI);
      }

      if (period > 1.5 * (i > 0 ? results[i - 1]?.period || period : period)) {
        period = 1.5 * (i > 0 ? results[i - 1]?.period || period : period);
      }
      if (period < 0.67 * (i > 0 ? results[i - 1]?.period || period : period)) {
        period = 0.67 * (i > 0 ? results[i - 1]?.period || period : period);
      }
      if (period < 6) period = 6;
      if (period > 50) period = 50;

      period = 0.2 * period + 0.8 * (i > 0 ? results[i - 1]?.period || period : period);

      phase = Math.atan(Q1 / I1) * 180 / Math.PI;
    }

    // Calculate alpha
    const alpha = Math.max(fastLimit / period, slowLimit);

    // Calculate MAMA and FAMA
    mama = alpha * prices[i] + (1 - alpha) * mama;
    fama = 0.5 * alpha * mama + (1 - 0.5 * alpha) * fama;

    results.push({
      mama,
      fama,
      phase,
      period
    });
  }

  return results;
}

/**
 * Detect MAMA/FAMA crossovers
 * @param results - Array of MAMA/FAMA results
 * @returns Array of crossover signals
 */
export function detectMAMACrossovers(results: MAMAResult[]): Array<{
  index: number;
  type: 'bullish' | 'bearish';
  mama: number;
  fama: number;
}> {
  const crossovers: Array<{
    index: number;
    type: 'bullish' | 'bearish';
    mama: number;
    fama: number;
  }> = [];

  for (let i = 1; i < results.length; i++) {
    const prev = results[i - 1];
    const curr = results[i];

    // Bullish crossover: MAMA crosses above FAMA
    if (prev.mama <= prev.fama && curr.mama > curr.fama) {
      crossovers.push({
        index: i,
        type: 'bullish',
        mama: curr.mama,
        fama: curr.fama
      });
    }

    // Bearish crossover: MAMA crosses below FAMA
    if (prev.mama >= prev.fama && curr.mama < curr.fama) {
      crossovers.push({
        index: i,
        type: 'bearish',
        mama: curr.mama,
        fama: curr.fama
      });
    }
  }

  return crossovers;
}

/**
 * Fisher Transform
 * Converts prices to a Gaussian normal distribution
 */
export function calculateFisherTransform(prices: number[], period: number = 10): number[] {
  const results: number[] = [];
  let fisher = 0;
  let prevFisher = 0;

  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      results.push(0);
      continue;
    }

    // Find highest and lowest in period
    const slice = prices.slice(i - period + 1, i + 1);
    const highest = Math.max(...slice);
    const lowest = Math.min(...slice);

    // Normalize price to range -1 to 1
    let value = 0;
    if (highest !== lowest) {
      value = 2 * ((prices[i] - lowest) / (highest - lowest) - 0.5);
    }

    // Limit value
    value = Math.max(-0.999, Math.min(0.999, value));

    // Fisher Transform
    fisher = 0.5 * Math.log((1 + value) / (1 - value)) + 0.5 * prevFisher;
    prevFisher = fisher;

    results.push(fisher);
  }

  return results;
}
