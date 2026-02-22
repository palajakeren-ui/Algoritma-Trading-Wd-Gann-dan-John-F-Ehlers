// Execution module — Idempotent order submission engine
//
// Guarantees:
// - Duplicate prevention via idempotency keys
// - Async non-blocking submission
// - Exchange ACK handling
// - Nanosecond latency tracking
// - Fill event publishing back to Go

pub mod execution {
    pub use crate::ExecutionEngine;
    pub use crate::OrderRequest;
    pub use crate::OrderAck;
    pub use crate::FillEvent;
}
