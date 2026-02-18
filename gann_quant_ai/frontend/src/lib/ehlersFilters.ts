// John F. Ehlers Digital Signal Processing Filters

// Bandpass Filter
export const calculateBandpassFilter = (
  prices: number[],
  period: number = 20,
  bandwidth: number = 0.3
): number[] => {
  const alpha = (1 - Math.cos((2 * Math.PI) / period)) / (Math.pow(1.414, 2 / bandwidth) - 1);
  const beta = Math.cos((2 * Math.PI) / period);

  const bp: number[] = new Array(prices.length).fill(0);

  for (let i = 2; i < prices.length; i++) {
    const a = 0.5 * (1 - alpha);
    bp[i] = a * (prices[i] - prices[i - 2]) +
      beta * (1 + alpha) * (bp[i - 1] || 0) -
      alpha * (bp[i - 2] || 0);
  }

  return bp;
};

// Fisher Transform
export const calculateFisherTransform = (prices: number[], period: number = 10): number[] => {
  const fisher: number[] = [];

  for (let i = period - 1; i < prices.length; i++) {
    const slice = prices.slice(i - period + 1, i + 1);
    const maxH = Math.max(...slice);
    const minL = Math.min(...slice);

    let value = 0.5 * 2 * ((prices[i] - minL) / (maxH - minL || 1) - 0.5);
    value = Math.max(-0.999, Math.min(0.999, value));

    const fisherValue = 0.5 * Math.log((1 + value) / (1 - value));
    fisher.push(fisherValue);
  }

  return fisher;
};

// Super Smoother Filter
export const calculateSuperSmoother = (prices: number[], period: number = 10): number[] => {
  const a1 = Math.exp(-1.414 * Math.PI / period);
  const b1 = 2 * a1 * Math.cos(1.414 * Math.PI / period);
  const c2 = b1;
  const c3 = -a1 * a1;
  const c1 = 1 - c2 - c3;

  const ss: number[] = new Array(prices.length).fill(0);
  ss[0] = prices[0];
  ss[1] = prices[1];

  for (let i = 2; i < prices.length; i++) {
    ss[i] = c1 * (prices[i] + prices[i - 1]) / 2 + c2 * ss[i - 1] + c3 * ss[i - 2];
  }

  return ss;
};

// Roofing Filter
export const calculateRoofingFilter = (prices: number[], hpPeriod: number = 48, lpPeriod: number = 10): number[] => {
  // High-pass filter
  const alpha1 = (Math.cos(0.707 * 2 * Math.PI / hpPeriod) + Math.sin(0.707 * 2 * Math.PI / hpPeriod) - 1) / Math.cos(0.707 * 2 * Math.PI / hpPeriod);

  const hp: number[] = new Array(prices.length).fill(0);
  for (let i = 2; i < prices.length; i++) {
    hp[i] = (1 - alpha1 / 2) * (1 - alpha1 / 2) * (prices[i] - 2 * prices[i - 1] + prices[i - 2]) +
      2 * (1 - alpha1) * (hp[i - 1] || 0) -
      (1 - alpha1) * (1 - alpha1) * (hp[i - 2] || 0);
  }

  // Super Smoother
  return calculateSuperSmoother(hp, lpPeriod);
};

// Cyber Cycle
export const calculateCyberCycle = (prices: number[], period: number = 10): number[] => {
  const alpha = 2 / (period + 1);
  const cycle: number[] = new Array(prices.length).fill(0);
  const smooth: number[] = new Array(prices.length).fill(0);

  for (let i = 6; i < prices.length; i++) {
    smooth[i] = (prices[i] + 2 * prices[i - 1] + 2 * prices[i - 2] + prices[i - 3]) / 6;
    cycle[i] = (1 - 0.5 * alpha) * (1 - 0.5 * alpha) * (smooth[i] - 2 * smooth[i - 1] + smooth[i - 2]) +
      2 * (1 - alpha) * (cycle[i - 1] || 0) -
      (1 - alpha) * (1 - alpha) * (cycle[i - 2] || 0);
  }

  return cycle;
};

// Decycler
export const calculateDecycler = (prices: number[], hpPeriod: number = 125): number[] => {
  const alpha1 = (Math.cos(0.707 * 2 * Math.PI / hpPeriod) + Math.sin(0.707 * 2 * Math.PI / hpPeriod) - 1) / Math.cos(0.707 * 2 * Math.PI / hpPeriod);

  const hp: number[] = new Array(prices.length).fill(0);
  const dc: number[] = new Array(prices.length).fill(0);

  for (let i = 1; i < prices.length; i++) {
    hp[i] = (1 - alpha1 / 2) * (prices[i] - prices[i - 1]) + (1 - alpha1) * (hp[i - 1] || 0);
    dc[i] = prices[i] - hp[i];
  }

  return dc;
};

// Generate mock real-time filter data
export const generateRealtimeFilterData = (basePrice: number, points: number = 50) => {
  const data = [];
  let lastClose = basePrice;

  for (let i = 0; i < points; i++) {
    const open = lastClose + (Math.random() - 0.5) * (basePrice * 0.002);
    const close = open + (Math.random() - 0.5) * (basePrice * 0.005);
    const high = Math.max(open, close) + Math.random() * (basePrice * 0.001);
    const low = Math.min(open, close) - Math.random() * (basePrice * 0.001);
    lastClose = close;

    const time = new Date(Date.now() - (points - i) * 60000);

    data.push({
      time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      date: time.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      price: Number(close.toFixed(2)),
      fisher: Number((Math.sin(i / 5) * 1.5).toFixed(3)),
      bandpass: Number((Math.sin(i / 8) * 0.02).toFixed(4)),
      superSmoother: Number((close * 0.998 + Math.random() * 10).toFixed(2)),
      roofing: Number((Math.sin(i / 10) * 0.015).toFixed(4)),
      cyberCycle: Number((Math.sin(i / 6) * 0.025).toFixed(4)),
      decycler: Number((close * 0.995 + Math.random() * 20).toFixed(2)),
    });
  }

  return data;
};
