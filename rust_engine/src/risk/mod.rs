// Risk module — Zero-Bottleneck Risk Calculations
//
// All functions are pure (no side effects) and O(1) complexity.
// Uses fixed-point arithmetic for determinism.

pub mod risk {
    /// Parametric Value at Risk - O(1)
    /// Uses pre-computed Z-scores for common confidence levels
    #[inline(always)]
    pub fn parametric_var(portfolio_value: i64, volatility_bps: i64, confidence: u8) -> i64 {
        // Pre-computed Z-scores: 90%=1.282, 95%=1.645, 99%=2.326
        let z = match confidence {
            99 => 2326,   // 2.326 * 1000
            95 => 1645,   // 1.645 * 1000
            _ => 1282,    // 1.282 * 1000 (90%)
        };
        
        // Result in basis points
        (portfolio_value * volatility_bps * z) / 100_000
    }

    /// Maximum position size given risk parameters - O(1)
    #[inline(always)]
    pub fn max_position_size(
        equity: i64,
        risk_bps: i64,      // Risk in basis points
        entry_price: i64,   // Fixed-point price
        stop_loss: i64,     // Fixed-point price
    ) -> i64 {
        let risk_amount = (equity * risk_bps) / 10_000;
        let risk_per_unit = (entry_price - stop_loss).abs();
        
        if risk_per_unit == 0 {
            return 0;
        }
        
        risk_amount / risk_per_unit
    }

    /// Margin requirement - O(1)
    #[inline(always)]
    pub fn margin_requirement(notional: i64, leverage: u8) -> i64 {
        if leverage == 0 {
            return notional;
        }
        notional / leverage as i64
    }

    /// Portfolio exposure in basis points - O(1)
    #[inline(always)]
    pub fn exposure_bps(total_position_value: i64, equity: i64) -> i64 {
        if equity == 0 {
            return 0;
        }
        (total_position_value * 10_000) / equity
    }

    /// Kelly Criterion optimal position fraction - O(1)
    /// Returns fraction in basis points (e.g., 2500 = 25%)
    #[inline(always)]
    pub fn kelly_fraction(win_rate_bps: i64, win_loss_ratio: i64) -> i64 {
        // Kelly = W - (1-W)/R where W = win rate, R = win/loss ratio
        // win_rate_bps is in basis points (e.g., 5500 = 55%)
        let win_rate = win_rate_bps;
        let loss_rate = 10_000 - win_rate;
        
        // Result in basis points
        let kelly = win_rate - (loss_rate * 10_000 / win_loss_ratio);
        
        // Clamp to reasonable range (0% to 100%)
        kelly.max(0).min(10_000)
    }

    /// Check if order passes risk limits - O(1)
    #[inline(always)]
    pub fn check_order_risk(
        notional: i64,
        max_position: i64,
        current_drawdown_bps: i64,
        max_drawdown_bps: i64,
        daily_pnl: i64,
        daily_limit: i64,
        kill_switch_active: bool,
    ) -> (bool, &'static str) {
        if kill_switch_active {
            return (false, "KILL_SWITCH_ACTIVE");
        }
        
        if current_drawdown_bps >= max_drawdown_bps {
            return (false, "MAX_DRAWDOWN_EXCEEDED");
        }
        
        if notional > max_position {
            return (false, "POSITION_TOO_LARGE");
        }
        
        if daily_pnl < -daily_limit {
            return (false, "DAILY_LOSS_LIMIT_EXCEEDED");
        }
        
        (true, "APPROVED")
    }
}

#[cfg(test)]
mod tests {
    use super::risk::*;

    #[test]
    fn test_var() {
        let var = parametric_var(100_000_00_000_000, 200, 95); // $100k, 2% vol, 95% conf
        assert!(var > 0);
    }

    #[test]
    fn test_kelly() {
        let kelly = kelly_fraction(5500, 150); // 55% win rate, 1.5 win/loss ratio
        assert!(kelly > 0 && kelly < 10_000);
    }
}
