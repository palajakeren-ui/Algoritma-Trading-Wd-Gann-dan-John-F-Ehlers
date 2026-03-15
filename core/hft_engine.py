"""
HFT (High-Frequency Trading) Engine
Complete implementation synchronized with frontend HFT.tsx
Integrates Gann, Ehlers DSP, and core HFT strategies
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import queue
import time
from loguru import logger

# Try to import core engines
try:
    from core.gann_engine import GannEngine
except ImportError:
    GannEngine = None

try:
    from core.ehlers_engine import EhlersEngine
except ImportError:
    EhlersEngine = None

try:
    from core.risk_engine import RiskEngine
except ImportError:
    RiskEngine = None


class TradingMode(Enum):
    SPOT = "spot"
    FUTURES = "futures"


class RiskMode(Enum):
    DYNAMIC = "dynamic"
    FIXED = "fixed"


class ExitMode(Enum):
    TICKS = "ticks"
    RISK_REWARD = "rr"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    CANCEL = "CANCEL"


@dataclass
class HFTConfig:
    """HFT Configuration matching frontend schema exactly."""
    # Core settings
    enabled: bool = False
    max_orders_per_second: int = 100
    max_position_size: float = 10.0
    risk_limit_per_trade: float = 0.1
    target_latency: float = 1.0
    max_latency: float = 5.0
    co_location: bool = True
    direct_market_access: bool = True
    
    # Market making
    spread_bps: float = 2.0
    inventory_limit: int = 5
    quote_size: float = 0.1
    refresh_rate: int = 100
    
    # Arbitrage
    min_spread_arb: float = 0.05
    max_slippage: float = 0.02
    
    # Signals
    signal_threshold: float = 0.8
    hold_period: int = 500
    
    # Risk mode
    risk_mode: str = "dynamic"
    kelly_fraction: float = 0.25
    volatility_adjusted: bool = True
    max_daily_drawdown: float = 5.0
    dynamic_position_scaling: bool = True
    
    # Fixed risk
    fixed_risk_percent: float = 1.0
    fixed_lot_size: float = 0.1
    fixed_stop_loss: int = 50
    fixed_take_profit: int = 100
    
    # Instruments
    instrument_mode: str = "single"
    selected_instruments: List[str] = field(default_factory=lambda: ["BTCUSDT"])
    manual_instruments: List[str] = field(default_factory=list)
    
    # Gann strategies
    use_gann_square9: bool = False
    gann_square9_base_price: float = 100.0
    gann_square9_divisions: int = 8
    use_gann_angles: bool = False
    gann_angle: int = 45
    gann_time_unit: int = 1
    use_gann_time_cycles: bool = False
    gann_cycle_base: int = 30
    use_gann_sr: bool = False
    gann_sr_divisions: int = 8
    use_gann_fibo: bool = False
    use_gann_wave: bool = False
    use_gann_hexagon: bool = False
    use_gann_astro: bool = False
    
    # Ehlers strategies
    use_ehlers_mama_fama: bool = False
    mama_fast_limit: float = 0.5
    mama_slow_limit: float = 0.05
    use_ehlers_fisher: bool = False
    use_ehlers_bandpass: bool = False
    use_ehlers_super_smoother: bool = False
    use_ehlers_roofing: bool = False
    use_ehlers_cyber_cycle: bool = False
    use_ehlers_decycler: bool = False
    use_ehlers_insta_trend: bool = False
    use_ehlers_dominant_cycle: bool = False
    
    # Core HFT strategies
    use_market_making: bool = True
    use_statistical_arbitrage: bool = False
    use_momentum_scalping: bool = False
    use_mean_reversion: bool = False
    
    # Trading mode
    trading_mode: str = "spot"
    
    # Exit mode
    exit_mode: str = "ticks"
    risk_reward_ratio: float = 2.0


@dataclass
class Order:
    """Order representation."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "PENDING"
    fill_price: Optional[float] = None
    latency_ms: Optional[float] = None


@dataclass
class Position:
    """Position representation."""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.now)


@dataclass 
class Signal:
    """Trading signal."""
    symbol: str
    direction: OrderSide
    strength: float  # 0-1
    source: str  # 'gann', 'ehlers', 'hft', etc.
    price: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HFTEngine:
    """
    High-Frequency Trading Engine
    Integrates Gann, Ehlers DSP, and core HFT strategies
    """
    
    def __init__(self, config: Optional[HFTConfig] = None, yaml_config: Optional[Dict] = None):
        """Initialize HFT Engine."""
        self.config = config or HFTConfig()
        self.yaml_config = yaml_config or {}
        
        # Load from YAML if provided
        if yaml_config:
            self._load_from_yaml(yaml_config)
        
        # State
        self.running = False
        self.paused = False
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.signals: List[Signal] = []
        
        # Performance metrics
        self.metrics = {
            'orders_per_second': 0,
            'fill_rate': 0.0,
            'avg_latency_ms': 0.0,
            'daily_pnl': 0.0,
            'total_trades': 0,
            'win_rate': 0.0
        }
        
        # Initialize engines
        self.gann_engine = GannEngine({}) if GannEngine else None
        self.ehlers_engine = EhlersEngine({}) if EhlersEngine else None
        
        # Order queue for async processing
        self.order_queue = queue.Queue()
        self.signal_queue = queue.Queue()
        
        # Threads
        self._order_processor_thread = None
        self._signal_generator_thread = None
        
        logger.info("HFT Engine initialized")
    
    def _load_from_yaml(self, yaml_config: Dict):
        """Load configuration from YAML dict."""
        engine = yaml_config.get('engine', {})
        risk = yaml_config.get('risk', {})
        gann = yaml_config.get('gann', {})
        ehlers = yaml_config.get('ehlers', {})
        strategies = yaml_config.get('strategies', {}).get('core', {})
        instruments = yaml_config.get('instruments', {})
        
        # Engine settings
        self.config.enabled = engine.get('enabled', False)
        self.config.max_orders_per_second = engine.get('max_orders_per_second', 100)
        self.config.max_position_size = engine.get('max_position_size', 10)
        self.config.risk_limit_per_trade = engine.get('risk_limit_per_trade', 0.1)
        self.config.target_latency = engine.get('target_latency_ms', 1.0)
        self.config.max_latency = engine.get('max_latency_ms', 5.0)
        self.config.co_location = engine.get('co_location', True)
        self.config.direct_market_access = engine.get('direct_market_access', True)
        self.config.spread_bps = engine.get('spread_bps', 2.0)
        self.config.inventory_limit = engine.get('inventory_limit', 5)
        self.config.quote_size = engine.get('quote_size', 0.1)
        self.config.refresh_rate = engine.get('refresh_rate_ms', 100)
        self.config.min_spread_arb = engine.get('min_spread_arb', 0.05)
        self.config.max_slippage = engine.get('max_slippage', 0.02)
        self.config.signal_threshold = engine.get('signal_threshold', 0.8)
        self.config.hold_period = engine.get('hold_period_ms', 500)
        
        # Risk settings
        self.config.risk_mode = risk.get('mode', 'dynamic')
        dynamic = risk.get('dynamic', {})
        self.config.kelly_fraction = dynamic.get('kelly_fraction', 0.25)
        self.config.volatility_adjusted = dynamic.get('volatility_adjusted', True)
        self.config.max_daily_drawdown = dynamic.get('max_daily_drawdown_percent', 5.0)
        self.config.dynamic_position_scaling = dynamic.get('dynamic_position_scaling', True)
        
        fixed = risk.get('fixed', {})
        self.config.fixed_risk_percent = fixed.get('risk_percent', 1.0)
        self.config.fixed_lot_size = fixed.get('lot_size', 0.1)
        self.config.fixed_stop_loss = fixed.get('stop_loss_ticks', 50)
        self.config.fixed_take_profit = fixed.get('take_profit_ticks', 100)
        
        # Instruments
        self.config.instrument_mode = instruments.get('mode', 'single')
        self.config.selected_instruments = instruments.get('selected', ['BTCUSDT'])
        self.config.manual_instruments = instruments.get('manual', [])
        
        # Gann settings
        sq9 = gann.get('square9', {})
        self.config.use_gann_square9 = sq9.get('enabled', False)
        self.config.gann_square9_base_price = sq9.get('base_price', 100)
        self.config.gann_square9_divisions = sq9.get('divisions', 8)
        
        angles = gann.get('angles', {})
        self.config.use_gann_angles = angles.get('enabled', False)
        self.config.gann_angle = angles.get('primary_angle', 45)
        self.config.gann_time_unit = angles.get('time_unit', 1)
        
        time_cycles = gann.get('time_cycles', {})
        self.config.use_gann_time_cycles = time_cycles.get('enabled', False)
        self.config.gann_cycle_base = time_cycles.get('cycle_base', 30)
        
        sr = gann.get('sr', {})
        self.config.use_gann_sr = sr.get('enabled', False)
        self.config.gann_sr_divisions = sr.get('divisions', 8)
        
        self.config.use_gann_fibo = gann.get('fibonacci', {}).get('enabled', False)
        self.config.use_gann_wave = gann.get('wave', {}).get('enabled', False)
        self.config.use_gann_hexagon = gann.get('hexagon', {}).get('enabled', False)
        self.config.use_gann_astro = gann.get('astro', {}).get('enabled', False)
        
        # Ehlers settings
        mama = ehlers.get('mama_fama', {})
        self.config.use_ehlers_mama_fama = mama.get('enabled', False)
        self.config.mama_fast_limit = mama.get('fast_limit', 0.5)
        self.config.mama_slow_limit = mama.get('slow_limit', 0.05)
        
        self.config.use_ehlers_fisher = ehlers.get('fisher', {}).get('enabled', False)
        self.config.use_ehlers_bandpass = ehlers.get('bandpass', {}).get('enabled', False)
        self.config.use_ehlers_super_smoother = ehlers.get('super_smoother', {}).get('enabled', False)
        self.config.use_ehlers_roofing = ehlers.get('roofing', {}).get('enabled', False)
        self.config.use_ehlers_cyber_cycle = ehlers.get('cyber_cycle', {}).get('enabled', False)
        self.config.use_ehlers_decycler = ehlers.get('decycler', {}).get('enabled', False)
        self.config.use_ehlers_insta_trend = ehlers.get('insta_trend', {}).get('enabled', False)
        self.config.use_ehlers_dominant_cycle = ehlers.get('dominant_cycle', {}).get('enabled', False)
        
        # Core strategies
        self.config.use_market_making = strategies.get('market_making', {}).get('enabled', True)
        self.config.use_statistical_arbitrage = strategies.get('statistical_arbitrage', {}).get('enabled', False)
        self.config.use_momentum_scalping = strategies.get('momentum_scalping', {}).get('enabled', False)
        self.config.use_mean_reversion = strategies.get('mean_reversion', {}).get('enabled', False)
    
    def to_frontend_config(self) -> Dict[str, Any]:
        """Convert config to frontend-compatible format."""
        return {
            'enabled': self.config.enabled,
            'maxOrdersPerSecond': self.config.max_orders_per_second,
            'maxPositionSize': self.config.max_position_size,
            'riskLimitPerTrade': self.config.risk_limit_per_trade,
            'targetLatency': self.config.target_latency,
            'maxLatency': self.config.max_latency,
            'coLocation': self.config.co_location,
            'directMarketAccess': self.config.direct_market_access,
            'spreadBps': self.config.spread_bps,
            'inventoryLimit': self.config.inventory_limit,
            'quoteSize': self.config.quote_size,
            'refreshRate': self.config.refresh_rate,
            'minSpreadArb': self.config.min_spread_arb,
            'maxSlippage': self.config.max_slippage,
            'signalThreshold': self.config.signal_threshold,
            'holdPeriod': self.config.hold_period,
            'riskMode': self.config.risk_mode,
            'kellyFraction': self.config.kelly_fraction,
            'volatilityAdjusted': self.config.volatility_adjusted,
            'maxDailyDrawdown': self.config.max_daily_drawdown,
            'dynamicPositionScaling': self.config.dynamic_position_scaling,
            'fixedRiskPercent': self.config.fixed_risk_percent,
            'fixedLotSize': self.config.fixed_lot_size,
            'fixedStopLoss': self.config.fixed_stop_loss,
            'fixedTakeProfit': self.config.fixed_take_profit,
            'instrumentMode': self.config.instrument_mode,
            'selectedInstruments': self.config.selected_instruments,
            'manualInstruments': self.config.manual_instruments,
            'useGannSquare9': self.config.use_gann_square9,
            'gannSquare9BasePrice': self.config.gann_square9_base_price,
            'gannSquare9Divisions': self.config.gann_square9_divisions,
            'useGannAngles': self.config.use_gann_angles,
            'gannAngle': self.config.gann_angle,
            'gannTimeUnit': self.config.gann_time_unit,
            'useGannTimeCycles': self.config.use_gann_time_cycles,
            'gannCycleBase': self.config.gann_cycle_base,
            'useGannSR': self.config.use_gann_sr,
            'gannSRDivisions': self.config.gann_sr_divisions,
            'useGannFibo': self.config.use_gann_fibo,
            'useGannWave': self.config.use_gann_wave,
            'useGannHexagon': self.config.use_gann_hexagon,
            'useGannAstro': self.config.use_gann_astro,
            'useEhlersMAMAFAMA': self.config.use_ehlers_mama_fama,
            'mamaFastLimit': self.config.mama_fast_limit,
            'mamaSlowLimit': self.config.mama_slow_limit,
            'useEhlersFisher': self.config.use_ehlers_fisher,
            'useEhlersBandpass': self.config.use_ehlers_bandpass,
            'useEhlersSuperSmoother': self.config.use_ehlers_super_smoother,
            'useEhlersRoofing': self.config.use_ehlers_roofing,
            'useEhlersCyberCycle': self.config.use_ehlers_cyber_cycle,
            'useEhlersDecycler': self.config.use_ehlers_decycler,
            'useEhlersInstaTrend': self.config.use_ehlers_insta_trend,
            'useEhlersDominantCycle': self.config.use_ehlers_dominant_cycle,
            'useMarketMaking': self.config.use_market_making,
            'useStatisticalArbitrage': self.config.use_statistical_arbitrage,
            'useMomentumScalping': self.config.use_momentum_scalping,
            'useMeanReversion': self.config.use_mean_reversion,
            'tradingMode': self.config.trading_mode,
            'exitMode': self.config.exit_mode,
            'riskRewardRatio': self.config.risk_reward_ratio
        }
    
    def update_from_frontend(self, frontend_config: Dict[str, Any]):
        """Update config from frontend format."""
        mapping = {
            'enabled': 'enabled',
            'maxOrdersPerSecond': 'max_orders_per_second',
            'maxPositionSize': 'max_position_size',
            'riskLimitPerTrade': 'risk_limit_per_trade',
            'targetLatency': 'target_latency',
            'maxLatency': 'max_latency',
            'coLocation': 'co_location',
            'directMarketAccess': 'direct_market_access',
            'spreadBps': 'spread_bps',
            'inventoryLimit': 'inventory_limit',
            'quoteSize': 'quote_size',
            'refreshRate': 'refresh_rate',
            'minSpreadArb': 'min_spread_arb',
            'maxSlippage': 'max_slippage',
            'signalThreshold': 'signal_threshold',
            'holdPeriod': 'hold_period',
            'riskMode': 'risk_mode',
            'kellyFraction': 'kelly_fraction',
            'volatilityAdjusted': 'volatility_adjusted',
            'maxDailyDrawdown': 'max_daily_drawdown',
            'dynamicPositionScaling': 'dynamic_position_scaling',
            'fixedRiskPercent': 'fixed_risk_percent',
            'fixedLotSize': 'fixed_lot_size',
            'fixedStopLoss': 'fixed_stop_loss',
            'fixedTakeProfit': 'fixed_take_profit',
            'instrumentMode': 'instrument_mode',
            'selectedInstruments': 'selected_instruments',
            'manualInstruments': 'manual_instruments',
            'useGannSquare9': 'use_gann_square9',
            'gannSquare9BasePrice': 'gann_square9_base_price',
            'gannSquare9Divisions': 'gann_square9_divisions',
            'useGannAngles': 'use_gann_angles',
            'gannAngle': 'gann_angle',
            'gannTimeUnit': 'gann_time_unit',
            'useGannTimeCycles': 'use_gann_time_cycles',
            'gannCycleBase': 'gann_cycle_base',
            'useGannSR': 'use_gann_sr',
            'gannSRDivisions': 'gann_sr_divisions',
            'useGannFibo': 'use_gann_fibo',
            'useGannWave': 'use_gann_wave',
            'useGannHexagon': 'use_gann_hexagon',
            'useGannAstro': 'use_gann_astro',
            'useEhlersMAMAFAMA': 'use_ehlers_mama_fama',
            'mamaFastLimit': 'mama_fast_limit',
            'mamaSlowLimit': 'mama_slow_limit',
            'useEhlersFisher': 'use_ehlers_fisher',
            'useEhlersBandpass': 'use_ehlers_bandpass',
            'useEhlersSuperSmoother': 'use_ehlers_super_smoother',
            'useEhlersRoofing': 'use_ehlers_roofing',
            'useEhlersCyberCycle': 'use_ehlers_cyber_cycle',
            'useEhlersDecycler': 'use_ehlers_decycler',
            'useEhlersInstaTrend': 'use_ehlers_insta_trend',
            'useEhlersDominantCycle': 'use_ehlers_dominant_cycle',
            'useMarketMaking': 'use_market_making',
            'useStatisticalArbitrage': 'use_statistical_arbitrage',
            'useMomentumScalping': 'use_momentum_scalping',
            'useMeanReversion': 'use_mean_reversion',
            'tradingMode': 'trading_mode',
            'exitMode': 'exit_mode',
            'riskRewardRatio': 'risk_reward_ratio'
        }
        
        for frontend_key, backend_key in mapping.items():
            if frontend_key in frontend_config:
                setattr(self.config, backend_key, frontend_config[frontend_key])
    
    # =========================================================================
    # CORE HFT STRATEGIES
    # =========================================================================
    
    def generate_market_making_signals(self, market_data: pd.DataFrame) -> List[Signal]:
        """Generate market making signals."""
        signals = []
        
        if not self.config.use_market_making or market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        spread = current_price * (self.config.spread_bps / 10000)
        
        # Calculate bid/ask levels
        bid_price = current_price - spread / 2
        ask_price = current_price + spread / 2
        
        # Check inventory
        current_inventory = sum(
            pos.quantity if pos.side == OrderSide.BUY else -pos.quantity
            for pos in self.positions.values()
        )
        
        # Adjust for inventory skew
        if abs(current_inventory) < self.config.inventory_limit:
            # Generate both sides
            signals.append(Signal(
                symbol=market_data.attrs.get('symbol', 'UNKNOWN'),
                direction=OrderSide.BUY,
                strength=0.7,
                source='market_making',
                price=bid_price,
                metadata={'type': 'bid', 'spread_bps': self.config.spread_bps}
            ))
            
            signals.append(Signal(
                symbol=market_data.attrs.get('symbol', 'UNKNOWN'),
                direction=OrderSide.SELL,
                strength=0.7,
                source='market_making',
                price=ask_price,
                metadata={'type': 'ask', 'spread_bps': self.config.spread_bps}
            ))
        
        return signals
    
    def generate_momentum_scalping_signals(self, market_data: pd.DataFrame) -> List[Signal]:
        """Generate momentum scalping signals."""
        signals = []
        
        if not self.config.use_momentum_scalping or len(market_data) < 10:
            return signals
        
        # Calculate momentum
        returns = market_data['close'].pct_change()
        momentum = returns.rolling(5).mean().iloc[-1]
        acceleration = returns.diff().rolling(3).mean().iloc[-1]
        
        current_price = market_data['close'].iloc[-1]
        
        # Strong upward momentum with acceleration
        if momentum > 0.001 and acceleration > 0:
            signals.append(Signal(
                symbol=market_data.attrs.get('symbol', 'UNKNOWN'),
                direction=OrderSide.BUY,
                strength=min(1.0, abs(momentum) * 100),
                source='momentum_scalping',
                price=current_price,
                metadata={'momentum': momentum, 'acceleration': acceleration}
            ))
        
        # Strong downward momentum with acceleration
        elif momentum < -0.001 and acceleration < 0:
            signals.append(Signal(
                symbol=market_data.attrs.get('symbol', 'UNKNOWN'),
                direction=OrderSide.SELL,
                strength=min(1.0, abs(momentum) * 100),
                source='momentum_scalping',
                price=current_price,
                metadata={'momentum': momentum, 'acceleration': acceleration}
            ))
        
        return signals
    
    def generate_mean_reversion_signals(self, market_data: pd.DataFrame) -> List[Signal]:
        """Generate mean reversion signals."""
        signals = []
        
        if not self.config.use_mean_reversion or len(market_data) < 20:
            return signals
        
        # Calculate Bollinger Bands
        sma = market_data['close'].rolling(20).mean()
        std = market_data['close'].rolling(20).std()
        
        current_price = market_data['close'].iloc[-1]
        current_sma = sma.iloc[-1]
        current_std = std.iloc[-1]
        
        upper_band = current_sma + 2 * current_std
        lower_band = current_sma - 2 * current_std
        
        # Z-score
        z_score = (current_price - current_sma) / current_std if current_std > 0 else 0
        
        # Oversold - expect reversion up
        if z_score < -2:
            signals.append(Signal(
                symbol=market_data.attrs.get('symbol', 'UNKNOWN'),
                direction=OrderSide.BUY,
                strength=min(1.0, abs(z_score) / 3),
                source='mean_reversion',
                price=current_price,
                metadata={'z_score': z_score, 'lower_band': lower_band}
            ))
        
        # Overbought - expect reversion down
        elif z_score > 2:
            signals.append(Signal(
                symbol=market_data.attrs.get('symbol', 'UNKNOWN'),
                direction=OrderSide.SELL,
                strength=min(1.0, abs(z_score) / 3),
                source='mean_reversion',
                price=current_price,
                metadata={'z_score': z_score, 'upper_band': upper_band}
            ))
        
        return signals
    
    # =========================================================================
    # GANN STRATEGY SIGNALS
    # =========================================================================
    
    def generate_gann_signals(self, market_data: pd.DataFrame) -> List[Signal]:
        """Generate Gann-based signals."""
        signals = []
        
        if not self.gann_engine:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        symbol = market_data.attrs.get('symbol', 'UNKNOWN')
        
        # Square of 9 signals
        if self.config.use_gann_square9:
            sq9_levels = self.gann_engine.calculate_sq9_levels(market_data)
            if sq9_levels:
                support_levels = sq9_levels.get('support', [])
                resistance_levels = sq9_levels.get('resistance', [])
                
                # Near support - potential buy
                for level in support_levels:
                    if 0 < (current_price - level) / current_price < 0.005:
                        signals.append(Signal(
                            symbol=symbol,
                            direction=OrderSide.BUY,
                            strength=0.8,
                            source='gann_sq9',
                            price=current_price,
                            metadata={'support_level': level}
                        ))
                
                # Near resistance - potential sell
                for level in resistance_levels:
                    if 0 < (level - current_price) / current_price < 0.005:
                        signals.append(Signal(
                            symbol=symbol,
                            direction=OrderSide.SELL,
                            strength=0.8,
                            source='gann_sq9',
                            price=current_price,
                            metadata={'resistance_level': level}
                        ))
        
        return signals
    
    # =========================================================================
    # EHLERS DSP SIGNALS
    # =========================================================================
    
    def generate_ehlers_signals(self, market_data: pd.DataFrame) -> List[Signal]:
        """Generate Ehlers DSP-based signals."""
        signals = []
        
        if not self.ehlers_engine:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        symbol = market_data.attrs.get('symbol', 'UNKNOWN')
        
        # Calculate all indicators
        indicators = self.ehlers_engine.calculate_all_indicators(market_data)
        
        if indicators is None or indicators.empty:
            return signals
        
        latest = indicators.iloc[-1]
        prev = indicators.iloc[-2] if len(indicators) > 1 else latest
        
        # MAMA/FAMA crossover
        if self.config.use_ehlers_mama_fama:
            mama = latest.get('mama', 0)
            fama = latest.get('fama', 0)
            prev_mama = prev.get('mama', 0)
            prev_fama = prev.get('fama', 0)
            
            # MAMA crosses above FAMA
            if prev_mama <= prev_fama and mama > fama:
                signals.append(Signal(
                    symbol=symbol,
                    direction=OrderSide.BUY,
                    strength=0.85,
                    source='ehlers_mama_fama',
                    price=current_price,
                    metadata={'mama': mama, 'fama': fama}
                ))
            
            # MAMA crosses below FAMA
            elif prev_mama >= prev_fama and mama < fama:
                signals.append(Signal(
                    symbol=symbol,
                    direction=OrderSide.SELL,
                    strength=0.85,
                    source='ehlers_mama_fama',
                    price=current_price,
                    metadata={'mama': mama, 'fama': fama}
                ))
        
        # Fisher Transform
        if self.config.use_ehlers_fisher:
            fisher = latest.get('fisher', 0)
            prev_fisher = prev.get('fisher', 0)
            
            if prev_fisher < 0 and fisher > 0:
                signals.append(Signal(
                    symbol=symbol,
                    direction=OrderSide.BUY,
                    strength=0.75,
                    source='ehlers_fisher',
                    price=current_price,
                    metadata={'fisher': fisher}
                ))
            elif prev_fisher > 0 and fisher < 0:
                signals.append(Signal(
                    symbol=symbol,
                    direction=OrderSide.SELL,
                    strength=0.75,
                    source='ehlers_fisher',
                    price=current_price,
                    metadata={'fisher': fisher}
                ))
        
        return signals
    
    # =========================================================================
    # SIGNAL AGGREGATION
    # =========================================================================
    
    def generate_all_signals(self, market_data: pd.DataFrame) -> List[Signal]:
        """Generate all signals from enabled strategies."""
        all_signals = []
        
        # Core HFT strategies
        all_signals.extend(self.generate_market_making_signals(market_data))
        all_signals.extend(self.generate_momentum_scalping_signals(market_data))
        all_signals.extend(self.generate_mean_reversion_signals(market_data))
        
        # Gann strategies
        all_signals.extend(self.generate_gann_signals(market_data))
        
        # Ehlers DSP strategies
        all_signals.extend(self.generate_ehlers_signals(market_data))
        
        # Filter by signal threshold
        filtered_signals = [
            s for s in all_signals 
            if s.strength >= self.config.signal_threshold
        ]
        
        return filtered_signals
    
    # =========================================================================
    # POSITION SIZING
    # =========================================================================
    
    def calculate_position_size(
        self, 
        signal: Signal, 
        account_balance: float,
        current_volatility: float = 0.02
    ) -> float:
        """Calculate position size based on risk mode."""
        
        if self.config.risk_mode == "fixed":
            return self.config.fixed_lot_size
        
        # Dynamic (Kelly Criterion based)
        win_rate = self.metrics.get('win_rate', 0.5)
        avg_win = self.metrics.get('avg_win', 1.0)
        avg_loss = self.metrics.get('avg_loss', 1.0)
        
        # Kelly fraction
        if avg_loss > 0:
            kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        else:
            kelly = 0.25
        
        # Apply Kelly fraction limit
        kelly = min(kelly, self.config.kelly_fraction)
        kelly = max(kelly, 0.01)
        
        # Volatility adjustment
        if self.config.volatility_adjusted:
            target_vol = 0.02  # 2% target volatility
            vol_scalar = target_vol / current_volatility if current_volatility > 0 else 1.0
            kelly *= min(vol_scalar, 2.0)  # Cap adjustment
        
        # Calculate position size
        risk_amount = account_balance * self.config.risk_limit_per_trade
        position_size = risk_amount * kelly / signal.price if signal.price > 0 else 0
        
        # Apply limits
        position_size = min(position_size, self.config.max_position_size)
        
        return round(position_size, 4)
    
    # =========================================================================
    # ENGINE CONTROL
    # =========================================================================
    
    def start(self):
        """Start the HFT engine."""
        if self.running:
            logger.warning("HFT Engine already running")
            return False
        
        self.running = True
        self.paused = False
        self.config.enabled = True
        
        logger.success("HFT Engine started")
        return True
    
    def stop(self):
        """Stop the HFT engine."""
        self.running = False
        self.config.enabled = False
        
        logger.info("HFT Engine stopped")
        return True
    
    def pause(self):
        """Pause the HFT engine."""
        self.paused = True
        logger.info("HFT Engine paused")
        return True
    
    def resume(self):
        """Resume the HFT engine."""
        self.paused = False
        logger.info("HFT Engine resumed")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status."""
        return {
            'enabled': self.config.enabled,
            'running': self.running,
            'paused': self.paused,
            'mode': self.config.trading_mode,
            'selected_instruments': self.config.selected_instruments,
            'active_positions': len(self.positions),
            'pending_orders': len([o for o in self.orders if o.status == 'PENDING']),
            'metrics': self.metrics,
            'active_strategies': self._get_active_strategies()
        }
    
    def _get_active_strategies(self) -> List[str]:
        """Get list of active strategies."""
        strategies = []
        
        if self.config.use_market_making:
            strategies.append('Market Making')
        if self.config.use_statistical_arbitrage:
            strategies.append('Statistical Arbitrage')
        if self.config.use_momentum_scalping:
            strategies.append('Momentum Scalping')
        if self.config.use_mean_reversion:
            strategies.append('Mean Reversion')
        if self.config.use_gann_square9:
            strategies.append('Gann SQ9')
        if self.config.use_gann_angles:
            strategies.append('Gann Angles')
        if self.config.use_ehlers_mama_fama:
            strategies.append('Ehlers MAMA/FAMA')
        if self.config.use_ehlers_fisher:
            strategies.append('Ehlers Fisher')
        
        return strategies


# Factory function
def create_hft_engine(yaml_config: Optional[Dict] = None) -> HFTEngine:
    """Create HFT Engine from YAML config."""
    return HFTEngine(yaml_config=yaml_config)
