// Risk module — Real-time risk calculations
//
// Note: Risk DECISIONS are made in Go Orchestrator.
// This module provides fast math primitives only:
// - VaR (Value at Risk) calculation
// - Position sizing helpers
// - Margin requirement computation
// - Exposure calculation

pub mod risk {
    /// Calculate Value at Risk (parametric method)
    pub fn parametric_var(portfolio_value: f64, volatility: f64, confidence: f64, holding_period_days: f64) -> f64 {
        // Z-scores: 95% = 1.645, 99% = 2.326
        let z = if confidence >= 0.99 { 2.326 } else if confidence >= 0.95 { 1.645 } else { 1.282 };
        portfolio_value * volatility * z * holding_period_days.sqrt()
    }

    /// Calculate maximum position size given risk parameters
    pub fn max_position_size(
        equity: f64,
        risk_pct: f64,
        entry_price: f64,
        stop_loss_price: f64,
    ) -> f64 {
        let risk_amount = equity * (risk_pct / 100.0);
        let risk_per_unit = (entry_price - stop_loss_price).abs();
        if risk_per_unit <= 0.0 { return 0.0; }
        risk_amount / risk_per_unit
    }

    /// Calculate margin requirement
    pub fn margin_requirement(notional: f64, leverage: f64) -> f64 {
        if leverage <= 0.0 { return notional; }
        notional / leverage
    }

    /// Calculate portfolio exposure percentage
    pub fn exposure_pct(total_position_value: f64, equity: f64) -> f64 {
        if equity <= 0.0 { return 0.0; }
        (total_position_value / equity) * 100.0
    }
}
