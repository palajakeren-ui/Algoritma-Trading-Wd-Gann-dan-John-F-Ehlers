"""
Cycle Engine v3.0 - Production Ready
Advanced cycle detection and analysis using Ehlers, Gann, and Astro methods
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class CycleType(Enum):
    DOMINANT = "dominant"
    SECONDARY = "secondary"
    GANN = "gann"
    LUNAR = "lunar"
    SEASONAL = "seasonal"


@dataclass
class DetectedCycle:
    """Detected market cycle"""
    cycle_type: CycleType
    period_days: float
    amplitude: float
    phase: float  # Current phase in degrees (0-360)
    phase_position: str  # 'bottom', 'rising', 'top', 'falling'
    strength: float  # 0-1
    next_peak: Optional[datetime]
    next_trough: Optional[datetime]


class CycleEngine:
    """
    Production-ready cycle detection engine supporting:
    - FFT-based cycle detection
    - Ehlers Hilbert Transform cycle measurement
    - Gann time cycle analysis
    - Lunar and seasonal cycles
    - Multi-cycle synthesis
    """
    
    # Gann time cycles in days
    GANN_CYCLES = [7, 14, 21, 28, 30, 45, 49, 52, 60, 90, 120, 144, 180, 270, 360]
    
    # Lunar cycle
    LUNAR_CYCLE = 29.53  # days
    
    # Seasonal trading days
    SEASONAL_CYCLE = 252  # trading days per year
    
    def __init__(self, config: Dict = None):
        """
        Initialize cycle engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Settings
        self.min_period = self.config.get('min_period', 5)
        self.max_period = self.config.get('max_period', 200)
        self.min_amplitude = self.config.get('min_amplitude', 0.01)
        
        logger.info("Cycle Engine initialized")
    
    # ==================== FFT CYCLE DETECTION ====================
    
    def detect_cycles_fft(
        self,
        data: pd.DataFrame,
        top_n: int = 5
    ) -> List[DetectedCycle]:
        """
        Detect dominant cycles using Fast Fourier Transform.
        
        Args:
            data: OHLCV DataFrame
            top_n: Number of top cycles to return
            
        Returns:
            List of detected cycles
        """
        close = data['close'].values
        n = len(close)
        
        if n < self.min_period * 2:
            logger.warning("Insufficient data for FFT cycle detection")
            return []
        
        # Detrend data
        trend = np.polyfit(np.arange(n), close, 1)
        detrended = close - (trend[0] * np.arange(n) + trend[1])
        
        # Apply window to reduce spectral leakage
        window = np.hanning(n)
        windowed = detrended * window
        
        # FFT
        fft_result = np.fft.fft(windowed)
        frequencies = np.fft.fftfreq(n)
        power = np.abs(fft_result) ** 2
        
        # Find peaks in power spectrum
        cycles = []
        
        for i in range(1, n // 2):  # Only positive frequencies
            if frequencies[i] > 0:
                period = 1 / frequencies[i]
                
                # Filter by period range
                if self.min_period <= period <= self.max_period:
                    # Check if it's a local maximum
                    if i > 0 and i < len(power) - 1:
                        if power[i] > power[i-1] and power[i] > power[i+1]:
                            amplitude = np.sqrt(power[i]) / n
                            rel_amplitude = amplitude / np.mean(np.abs(detrended))
                            
                            if rel_amplitude >= self.min_amplitude:
                                # Calculate phase
                                phase_rad = np.angle(fft_result[i])
                                phase_deg = np.degrees(phase_rad) % 360
                                
                                cycles.append({
                                    'period': period,
                                    'amplitude': amplitude,
                                    'rel_amplitude': rel_amplitude,
                                    'power': power[i],
                                    'phase': phase_deg
                                })
        
        # Sort by power and take top_n
        cycles.sort(key=lambda x: -x['power'])
        cycles = cycles[:top_n]
        
        # Convert to DetectedCycle objects
        detected = []
        current_date = data.index[-1]
        
        for i, c in enumerate(cycles):
            cycle_type = CycleType.DOMINANT if i == 0 else CycleType.SECONDARY
            phase_position = self._get_phase_position(c['phase'])
            
            # Calculate next peak and trough
            days_to_peak = (90 - c['phase']) / 360 * c['period']
            days_to_trough = (270 - c['phase']) / 360 * c['period']
            
            if days_to_peak < 0:
                days_to_peak += c['period']
            if days_to_trough < 0:
                days_to_trough += c['period']
            
            detected.append(DetectedCycle(
                cycle_type=cycle_type,
                period_days=round(c['period'], 1),
                amplitude=round(c['amplitude'], 4),
                phase=round(c['phase'], 1),
                phase_position=phase_position,
                strength=min(1.0, c['rel_amplitude'] * 5),
                next_peak=current_date + timedelta(days=days_to_peak),
                next_trough=current_date + timedelta(days=days_to_trough)
            ))
        
        return detected
    
    def _get_phase_position(self, phase: float) -> str:
        """Get phase position description"""
        if 315 <= phase or phase < 45:
            return 'bottom'
        elif 45 <= phase < 135:
            return 'rising'
        elif 135 <= phase < 225:
            return 'top'
        else:
            return 'falling'
    
    # ==================== EHLERS CYCLE DETECTION ====================
    
    def detect_cycles_ehlers(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """
        Detect dominant cycle using Ehlers Hilbert Transform.
        
        Returns:
            Cycle information dictionary
        """
        close = data['close'].values
        n = len(close)
        
        if n < 50:
            return {'error': 'Insufficient data'}
        
        # Smooth the data
        smooth = np.zeros(n)
        for i in range(4, n):
            smooth[i] = (4 * close[i] + 3 * close[i-1] + 2 * close[i-2] + close[i-3]) / 10
        
        # Hilbert Transform
        detrender = np.zeros(n)
        i1 = np.zeros(n)
        q1 = np.zeros(n)
        delta_phase = np.zeros(n)
        inst_period = np.zeros(n)
        period = np.zeros(n)
        
        for i in range(6, n):
            # Detrender
            detrender[i] = (0.0962 * smooth[i] + 0.5769 * smooth[i-2] - 
                           0.5769 * smooth[i-4] - 0.0962 * smooth[i-6]) * 0.075
            
            # In-phase and quadrature
            i1[i] = detrender[i-3]
            q1[i] = (0.0962 * detrender[i] + 0.5769 * detrender[i-2] - 
                    0.5769 * detrender[i-4] - 0.0962 * detrender[i-6]) * 0.075
            
            # Phase angle
            if i1[i] != 0:
                phase = np.degrees(np.arctan(q1[i] / i1[i]))
            else:
                phase = 0
            
            # Delta phase
            delta_phase[i] = phase - (delta_phase[i-1] if i > 0 else 0)
            delta_phase[i] = max(1, min(60, delta_phase[i]))
            
            # Median delta phase
            if i >= 5:
                median_dp = np.median(delta_phase[i-5:i])
                inst_period[i] = 360 / median_dp if median_dp > 0 else 0
            
            # Smooth period
            period[i] = 0.2 * inst_period[i] + 0.8 * period[i-1]
            period[i] = max(self.min_period, min(self.max_period, period[i]))
        
        # Get current dominant cycle
        current_period = period[-1]
        
        # Calculate phase position
        phase_rad = np.arctan2(q1[-1], i1[-1])
        phase_deg = np.degrees(phase_rad) % 360
        
        return {
            'method': 'ehlers_hilbert',
            'dominant_period': round(current_period, 1),
            'phase': round(phase_deg, 1),
            'phase_position': self._get_phase_position(phase_deg),
            'period_series': period,
            'in_phase': i1,
            'quadrature': q1
        }
    
    # ==================== GANN CYCLE ANALYSIS ====================
    
    def analyze_gann_cycles(
        self,
        data: pd.DataFrame,
        pivot_dates: List[datetime] = None
    ) -> List[Dict]:
        """
        Analyze Gann time cycles from pivot points.
        
        Returns:
            List of upcoming Gann cycle dates
        """
        current_date = data.index[-1]
        
        # Find pivots if not provided
        if pivot_dates is None:
            pivot_dates = []
            for i in range(2, min(100, len(data) - 2)):
                idx = len(data) - i - 1
                
                # Swing high
                if (data['high'].iloc[idx] > data['high'].iloc[idx-1] and
                    data['high'].iloc[idx] > data['high'].iloc[idx+1]):
                    pivot_dates.append(data.index[idx])
                
                # Swing low
                if (data['low'].iloc[idx] < data['low'].iloc[idx-1] and
                    data['low'].iloc[idx] < data['low'].iloc[idx+1]):
                    pivot_dates.append(data.index[idx])
            
            pivot_dates = sorted(set(pivot_dates))
        
        # Calculate upcoming cycle dates
        upcoming = []
        
        for pivot in pivot_dates[-10:]:  # Use last 10 pivots
            for cycle in self.GANN_CYCLES:
                cycle_date = pivot + timedelta(days=cycle)
                
                if cycle_date > current_date:
                    days_until = (cycle_date - current_date).days
                    
                    if days_until <= 90:  # Within 90 days
                        upcoming.append({
                            'date': cycle_date,
                            'days_until': days_until,
                            'cycle_days': cycle,
                            'cycle_type': CycleType.GANN,
                            'from_pivot': pivot,
                            'cycle_name': self._get_gann_name(cycle)
                        })
        
        # Sort by date
        upcoming.sort(key=lambda x: x['days_until'])
        
        # Find confluence (multiple cycles pointing to same date)
        confluences = self._find_confluence(upcoming)
        
        return {
            'upcoming_cycles': upcoming[:20],
            'confluences': confluences
        }
    
    def _get_gann_name(self, days: int) -> str:
        """Get Gann cycle name"""
        names = {
            7: "Weekly",
            14: "Bi-Weekly",
            21: "Minor (21d)",
            28: "Lunar Month",
            30: "Monthly",
            45: "45-Day",
            49: "7x7 Master",
            52: "Year in Weeks",
            60: "60-Day",
            90: "Quarterly",
            120: "4-Month",
            144: "Fibonacci 144",
            180: "Semi-Annual",
            270: "270-Day",
            360: "Annual"
        }
        return names.get(days, f"{days}-Day")
    
    def _find_confluence(self, dates: List[Dict], tolerance: int = 3) -> List[Dict]:
        """Find confluence zones where multiple cycles align"""
        if not dates:
            return []
        
        confluences = []
        used = set()
        
        for i, d1 in enumerate(dates):
            if i in used:
                continue
            
            cluster = [d1]
            used.add(i)
            
            for j, d2 in enumerate(dates):
                if j in used or j == i:
                    continue
                
                if abs(d1['days_until'] - d2['days_until']) <= tolerance:
                    cluster.append(d2)
                    used.add(j)
            
            if len(cluster) >= 2:
                confluences.append({
                    'date': d1['date'],
                    'days_until': d1['days_until'],
                    'cycle_count': len(cluster),
                    'cycles': [c['cycle_name'] for c in cluster],
                    'strength': min(1.0, len(cluster) / 4)
                })
        
        return sorted(confluences, key=lambda x: -x['cycle_count'])
    
    # ==================== LUNAR CYCLES ====================
    
    def analyze_lunar_cycles(
        self,
        current_date: datetime = None
    ) -> Dict:
        """
        Analyze lunar cycle phase.
        
        Returns:
            Lunar cycle information
        """
        if current_date is None:
            current_date = datetime.now()
        
        # Reference new moon (Jan 6, 2000)
        ref_new_moon = datetime(2000, 1, 6)
        days_since_ref = (current_date - ref_new_moon).days
        
        # Current lunar phase
        phase = (days_since_ref % self.LUNAR_CYCLE) / self.LUNAR_CYCLE
        phase_deg = phase * 360
        
        # Phase name
        if phase < 0.0625:
            phase_name = "New Moon"
        elif phase < 0.1875:
            phase_name = "Waxing Crescent"
        elif phase < 0.3125:
            phase_name = "First Quarter"
        elif phase < 0.4375:
            phase_name = "Waxing Gibbous"
        elif phase < 0.5625:
            phase_name = "Full Moon"
        elif phase < 0.6875:
            phase_name = "Waning Gibbous"
        elif phase < 0.8125:
            phase_name = "Last Quarter"
        elif phase < 0.9375:
            phase_name = "Waning Crescent"
        else:
            phase_name = "New Moon"
        
        # Next new and full moon
        days_to_new = (1 - phase) * self.LUNAR_CYCLE
        days_to_full = ((0.5 - phase) % 1) * self.LUNAR_CYCLE
        
        return {
            'cycle_type': CycleType.LUNAR,
            'phase_pct': round(phase * 100, 1),
            'phase_degrees': round(phase_deg, 1),
            'phase_name': phase_name,
            'next_new_moon': current_date + timedelta(days=days_to_new),
            'next_full_moon': current_date + timedelta(days=days_to_full),
            'market_tendency': 'bullish' if phase_name in ['New Moon', 'First Quarter'] else 'bearish'
        }
    
    # ==================== SEASONAL CYCLES ====================
    
    def analyze_seasonal_cycles(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """
        Analyze seasonal patterns.
        
        Returns:
            Seasonal analysis
        """
        if len(data) < 252:
            return {'error': 'Need at least 1 year of data'}
        
        # Add day of year
        data = data.copy()
        data['day_of_year'] = data.index.dayofyear
        data['month'] = data.index.month
        data['returns'] = data['close'].pct_change()
        
        # Monthly average returns
        monthly_returns = data.groupby('month')['returns'].mean()
        
        # Best and worst months
        best_month = monthly_returns.idxmax()
        worst_month = monthly_returns.idxmin()
        
        # Current position in seasonal cycle
        current_month = data.index[-1].month
        current_day = data.index[-1].dayofyear
        
        # Seasonal tendency
        if monthly_returns[current_month] > 0:
            tendency = 'bullish'
        else:
            tendency = 'bearish'
        
        return {
            'cycle_type': CycleType.SEASONAL,
            'current_month': current_month,
            'current_day_of_year': current_day,
            'monthly_returns': monthly_returns.to_dict(),
            'best_month': best_month,
            'worst_month': worst_month,
            'current_tendency': tendency,
            'seasonal_strength': abs(monthly_returns[current_month])
        }
    
    # ==================== COMBINED ANALYSIS ====================
    
    def analyze_all_cycles(
        self,
        data: pd.DataFrame
    ) -> Dict:
        """
        Comprehensive cycle analysis combining all methods.
        
        Returns:
            Complete cycle analysis
        """
        results = {
            'timestamp': datetime.now(),
            'symbol': data.attrs.get('symbol', 'UNKNOWN')
        }
        
        # FFT cycles
        fft_cycles = self.detect_cycles_fft(data)
        results['fft_cycles'] = fft_cycles
        
        # Ehlers cycle
        ehlers = self.detect_cycles_ehlers(data)
        results['ehlers_cycle'] = {
            'period': ehlers.get('dominant_period'),
            'phase': ehlers.get('phase'),
            'phase_position': ehlers.get('phase_position')
        }
        
        # Gann cycles
        gann = self.analyze_gann_cycles(data)
        results['gann_cycles'] = gann
        
        # Lunar
        lunar = self.analyze_lunar_cycles()
        results['lunar_cycle'] = lunar
        
        # Seasonal
        try:
            seasonal = self.analyze_seasonal_cycles(data)
            results['seasonal_cycle'] = seasonal
        except Exception as e:
            results['seasonal_cycle'] = {'error': str(e)}
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate cycle summary"""
        bullish_count = 0
        bearish_count = 0
        
        # Check FFT cycles
        for cycle in results.get('fft_cycles', []):
            if cycle.phase_position in ['bottom', 'rising']:
                bullish_count += 1
            else:
                bearish_count += 1
        
        # Check Ehlers
        ehlers = results.get('ehlers_cycle', {})
        if ehlers.get('phase_position') in ['bottom', 'rising']:
            bullish_count += 1
        else:
            bearish_count += 1
        
        # Check lunar
        lunar = results.get('lunar_cycle', {})
        if lunar.get('market_tendency') == 'bullish':
            bullish_count += 1
        else:
            bearish_count += 1
        
        # Determine overall bias
        if bullish_count > bearish_count:
            bias = 'BULLISH'
        elif bearish_count > bullish_count:
            bias = 'BEARISH'
        else:
            bias = 'NEUTRAL'
        
        return {
            'cycle_bias': bias,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'dominant_period': results.get('ehlers_cycle', {}).get('period'),
            'next_gann_confluence': results.get('gann_cycles', {}).get('confluences', [{}])[0] if results.get('gann_cycles', {}).get('confluences') else None
        }


# Example usage
if __name__ == "__main__":
    # Create sample data with clear cycles
    dates = pd.date_range(start='2023-01-01', periods=365, freq='1D')
    np.random.seed(42)
    
    t = np.arange(365)
    # Add multiple cycles
    cycle1 = 2000 * np.sin(2 * np.pi * t / 45)   # 45-day cycle
    cycle2 = 1000 * np.sin(2 * np.pi * t / 90)   # 90-day cycle
    trend = 50000 + t * 20
    noise = np.cumsum(np.random.randn(365) * 100)
    price = trend + cycle1 + cycle2 + noise
    
    data = pd.DataFrame({
        'open': price - np.abs(np.random.randn(365) * 300),
        'high': price + np.abs(np.random.randn(365) * 500),
        'low': price - np.abs(np.random.randn(365) * 500),
        'close': price,
        'volume': np.random.uniform(1e9, 5e9, 365)
    }, index=dates)
    data.attrs['symbol'] = 'BTCUSD'
    
    # Run cycle analysis
    engine = CycleEngine()
    
    print("\n=== FFT Cycle Detection ===")
    fft_cycles = engine.detect_cycles_fft(data)
    for c in fft_cycles:
        print(f"{c.cycle_type.value}: {c.period_days} days, Phase: {c.phase}° ({c.phase_position})")
    
    print("\n=== Ehlers Cycle Detection ===")
    ehlers = engine.detect_cycles_ehlers(data)
    print(f"Dominant Period: {ehlers['dominant_period']} days")
    print(f"Phase: {ehlers['phase']}° ({ehlers['phase_position']})")
    
    print("\n=== Gann Cycles ===")
    gann = engine.analyze_gann_cycles(data)
    for conf in gann['confluences'][:3]:
        print(f"Confluence: {conf['date'].strftime('%Y-%m-%d')} ({conf['cycle_count']} cycles)")
    
    print("\n=== Lunar Cycle ===")
    lunar = engine.analyze_lunar_cycles()
    print(f"Phase: {lunar['phase_name']} ({lunar['phase_pct']}%)")
    print(f"Market Tendency: {lunar['market_tendency']}")
    
    print("\n=== Full Analysis Summary ===")
    full = engine.analyze_all_cycles(data)
    print(f"Cycle Bias: {full['summary']['cycle_bias']}")
    print(f"Bullish Signals: {full['summary']['bullish_signals']}")
    print(f"Bearish Signals: {full['summary']['bearish_signals']}")
