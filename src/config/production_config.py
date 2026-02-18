"""
Production Configuration Schema
Validated, typed configuration with environment overrides.
"""

import os
import yaml
from typing import Dict, Optional, Any
from loguru import logger
from dataclasses import dataclass, field, asdict


@dataclass
class RiskConfig:
    max_daily_loss_pct: float = 5.0
    max_drawdown_pct: float = 15.0
    max_position_pct: float = 10.0
    max_risk_per_trade_pct: float = 2.0
    max_concurrent_positions: int = 10
    max_leverage: int = 10
    circuit_breaker_dd_pct: float = 15.0


@dataclass
class ExecutionConfig:
    max_retries: int = 3
    retry_delay_ms: int = 200
    slippage_bps: float = 5.0
    dedup_window_seconds: int = 60
    cooldown_seconds: int = 10


@dataclass
class FeatureConfig:
    enable_gann: bool = True
    enable_ehlers: bool = True
    enable_technical: bool = True
    warmup_bars: int = 100


@dataclass
class TradingConfig:
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    initial_capital: float = 100000.0
    min_signal_strength: float = 0.3
    tick_interval_seconds: int = 60
    max_errors: int = 10


@dataclass
class ProductionConfig:
    """Complete system configuration."""
    environment: str = "development"
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_yaml(cls, filepath: str) -> "ProductionConfig":
        """Load configuration from YAML file."""
        if not os.path.exists(filepath):
            logger.warning(f"Config file not found: {filepath}, using defaults")
            return cls()
        
        with open(filepath, "r") as f:
            data = yaml.safe_load(f) or {}
        
        config = cls(
            environment=data.get("environment", "development"),
            risk=RiskConfig(**{k: v for k, v in data.get("risk", {}).items() if hasattr(RiskConfig, k)}),
            execution=ExecutionConfig(**{k: v for k, v in data.get("execution", {}).items() if hasattr(ExecutionConfig, k)}),
            features=FeatureConfig(**{k: v for k, v in data.get("features", {}).items() if hasattr(FeatureConfig, k)}),
            trading=TradingConfig(**{k: v for k, v in data.get("trading", {}).items() if hasattr(TradingConfig, k)}),
        )
        
        logger.info(f"Config loaded from {filepath} (env: {config.environment})")
        return config
    
    def save_yaml(self, filepath: str):
        """Save configuration to YAML file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
        logger.info(f"Config saved to {filepath}")
    
    def validate(self) -> bool:
        """Validate configuration values."""
        errors = []
        
        if self.risk.max_daily_loss_pct <= 0 or self.risk.max_daily_loss_pct > 100:
            errors.append("max_daily_loss_pct must be 0-100")
        
        if self.risk.max_drawdown_pct <= 0 or self.risk.max_drawdown_pct > 100:
            errors.append("max_drawdown_pct must be 0-100")
        
        if self.risk.max_position_pct <= 0 or self.risk.max_position_pct > 100:
            errors.append("max_position_pct must be 0-100")
        
        if self.trading.initial_capital <= 0:
            errors.append("initial_capital must be positive")
        
        if self.trading.min_signal_strength < 0 or self.trading.min_signal_strength > 1:
            errors.append("min_signal_strength must be 0-1")
        
        if self.execution.max_retries < 0:
            errors.append("max_retries must be non-negative")
        
        if errors:
            for e in errors:
                logger.error(f"Config validation error: {e}")
            return False
        
        logger.info("Configuration validated successfully")
        return True
