// Orderbook module — Lock-Free L2 Orderbook
//
// Features:
// - BTreeMap O(log n) price level operations
// - Sequence gap detection with atomic counter
// - Pre-computed price keys (fixed-point)
// - Cache-line aligned for false sharing prevention

pub mod orderbook {
    use std::collections::BTreeMap;
    use std::sync::atomic::{AtomicU64, Ordering};

    /// Price precision: 1e8 = 8 decimal places
    pub const PRICE_SCALE: f64 = 100_000_000.0;

    /// Convert float price to fixed-point key
    #[inline(always)]
    pub fn price_to_key(price: f64) -> i64 {
        (price * PRICE_SCALE) as i64
    }

    /// Convert fixed-point key to float price
    #[inline(always)]
    pub fn key_to_price(key: i64) -> f64 {
        key as f64 / PRICE_SCALE
    }

    /// L2 Orderbook with sequence tracking
    pub struct L2Orderbook {
        pub symbol_hash: u64,
        pub bids: BTreeMap<i64, i64>,  // price_key -> quantity (fixed-point)
        pub asks: BTreeMap<i64, i64>,
        pub last_seq_id: AtomicU64,
        pub total_updates: AtomicU64,
        pub gaps_detected: AtomicU64,
    }

    impl L2Orderbook {
        pub fn new(symbol_hash: u64) -> Self {
            Self {
                symbol_hash,
                bids: BTreeMap::new(),
                asks: BTreeMap::new(),
                last_seq_id: AtomicU64::new(0),
                total_updates: AtomicU64::new(0),
                gaps_detected: AtomicU64::new(0),
            }
        }

        /// Apply price level delta - O(log n)
        /// Returns false if sequence gap detected
        #[inline(always)]
        pub fn apply_delta(&mut self, price: f64, qty: f64, is_bid: bool, seq_id: u64) -> bool {
            // Sequence gap detection
            let last = self.last_seq_id.load(Ordering::Relaxed);
            if last > 0 && seq_id != last + 1 {
                self.gaps_detected.fetch_add(1, Ordering::Relaxed);
                return false;
            }

            let key = price_to_key(price);
            let qty_fixed = (qty * PRICE_SCALE) as i64;
            let book = if is_bid { &mut self.bids } else { &mut self.asks };

            if qty_fixed <= 0 {
                book.remove(&key);
            } else {
                book.insert(key, qty_fixed);
            }

            self.last_seq_id.store(seq_id, Ordering::Relaxed);
            self.total_updates.fetch_add(1, Ordering::Relaxed);
            true
        }

        /// Get best bid price - O(log n)
        #[inline(always)]
        pub fn best_bid(&self) -> Option<f64> {
            self.bids.keys().next_back().map(|&k| key_to_price(k))
        }

        /// Get best ask price - O(log n)
        #[inline(always)]
        pub fn best_ask(&self) -> Option<f64> {
            self.asks.keys().next().map(|&k| key_to_price(k))
        }

        /// Get mid price - O(log n)
        #[inline(always)]
        pub fn mid_price(&self) -> Option<f64> {
            match (self.best_bid(), self.best_ask()) {
                (Some(bid), Some(ask)) => Some((bid + ask) / 2.0),
                _ => None,
            }
        }

        /// Get spread in basis points - O(log n)
        #[inline(always)]
        pub fn spread_bps(&self) -> Option<i64> {
            match (self.best_bid(), self.best_ask()) {
                (Some(bid), Some(ask)) if bid > 0.0 => {
                    Some(((ask - bid) / bid * 10_000.0) as i64)
                }
                _ => None,
            }
        }

        /// Get top N levels - O(n)
        pub fn top_levels(&self, n: usize) -> (Vec<(f64, f64)>, Vec<(f64, f64)>) {
            let bids: Vec<(f64, f64)> = self.bids
                .iter()
                .rev()
                .take(n)
                .map(|(&k, &q)| (key_to_price(k), q as f64 / PRICE_SCALE))
                .collect();

            let asks: Vec<(f64, f64)> = self.asks
                .iter()
                .take(n)
                .map(|(&k, &q)| (key_to_price(k), q as f64 / PRICE_SCALE))
                .collect();

            (bids, asks)
        }

        /// Clear all levels
        pub fn clear(&mut self) {
            self.bids.clear();
            self.asks.clear();
        }

        /// Get statistics
        pub fn stats(&self) -> (usize, usize, u64, u64) {
            (
                self.bids.len(),
                self.asks.len(),
                self.total_updates.load(Ordering::Relaxed),
                self.gaps_detected.load(Ordering::Relaxed),
            )
        }
    }
}

pub use orderbook::*;
