// Orderbook module — L2 in-memory orderbook with sequence validation
//
// Features:
// - BTreeMap-based price levels (sorted, O(log n) operations)
// - Snapshot application (full book replacement)
// - Incremental delta with sequence ID gap detection
// - Best bid/ask, mid price, spread calculation
// - Lock-free design (single-threaded owner)

pub mod orderbook {
    pub use crate::L2Orderbook;
    pub use crate::OrderbookLevel;
    pub use crate::OrderbookSnapshot;
}
