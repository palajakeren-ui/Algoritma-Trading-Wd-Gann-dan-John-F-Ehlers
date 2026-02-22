// Package models — Core data models shared across Go Orchestrator
//
// These types are the authoritative definitions for all state.
// They are serialized to JSON for the REST API and WebSocket events.
// They mirror the Rust types for cross-service compatibility.

package models

import "time"

// OrderSide represents buy or sell
type OrderSide string
const (
	Buy  OrderSide = "BUY"
	Sell OrderSide = "SELL"
)

// OrderStatus represents the lifecycle state
type OrderStatus string
const (
	Pending   OrderStatus = "PENDING"
	Submitted OrderStatus = "SUBMITTED"
	Filled    OrderStatus = "FILLED"
	Partial   OrderStatus = "PARTIAL"
	Cancelled OrderStatus = "CANCELLED"
	Rejected  OrderStatus = "REJECTED"
)

// Order is the authoritative order record
type Order struct {
	ID            string      `json:"id"`
	ClientID      string      `json:"client_id"`
	Symbol        string      `json:"symbol"`
	Side          OrderSide   `json:"side"`
	OrderType     string      `json:"order_type"` // LIMIT, MARKET
	Quantity      float64     `json:"quantity"`
	Price         float64     `json:"price"`
	Status        OrderStatus `json:"status"`
	FilledQty     float64     `json:"filled_qty"`
	AvgFillPrice  float64     `json:"avg_fill_price"`
	Commission    float64     `json:"commission"`
	CreatedAt     time.Time   `json:"created_at"`
	UpdatedAt     time.Time   `json:"updated_at"`
	ExchangeOrdID string     `json:"exchange_order_id"`
	SequenceID    uint64      `json:"sequence_id"`
	LatencyNs     int64       `json:"latency_ns"`
}

// Position represents an open position
type Position struct {
	Symbol        string    `json:"symbol"`
	Side          OrderSide `json:"side"`
	Quantity      float64   `json:"quantity"`
	EntryPrice    float64   `json:"entry_price"`
	CurrentPrice  float64   `json:"current_price"`
	UnrealizedPnL float64   `json:"unrealized_pnl"`
	RealizedPnL   float64   `json:"realized_pnl"`
	PositionValue float64   `json:"position_value"`
	UpdatedAt     time.Time `json:"updated_at"`
}

// Portfolio is the authoritative portfolio state
type Portfolio struct {
	Equity           float64              `json:"equity"`
	Cash             float64              `json:"cash"`
	TotalPnL         float64              `json:"total_pnl"`
	DailyPnL         float64              `json:"daily_pnl"`
	MaxDrawdown      float64              `json:"max_drawdown"`
	CurrentDrawdown  float64              `json:"current_drawdown"`
	ExposurePct      float64              `json:"exposure_pct"`
	Positions        map[string]*Position `json:"positions"`
	OpenOrders       map[string]*Order    `json:"open_orders"`
	HighWaterMark    float64              `json:"high_water_mark"`
	KillSwitchActive bool                 `json:"kill_switch_active"`
	TradingPaused    bool                 `json:"trading_paused"`
	SequenceID       uint64               `json:"sequence_id"`
	Timestamp        time.Time            `json:"timestamp"`
}

// MarketTick from Rust feed
type MarketTick struct {
	Symbol     string  `json:"symbol"`
	BidPrice   float64 `json:"bid_price"`
	AskPrice   float64 `json:"ask_price"`
	BidSize    float64 `json:"bid_size"`
	AskSize    float64 `json:"ask_size"`
	LastPrice  float64 `json:"last_price"`
	Volume     float64 `json:"volume"`
	SeqID      uint64  `json:"seq_id"`
	LatencyNs  int64   `json:"latency_ns"`
}

// FillEvent from Rust execution gateway
type FillEvent struct {
	OrderID       string    `json:"order_id"`
	ExchangeOrdID string    `json:"exchange_order_id"`
	Symbol        string    `json:"symbol"`
	Side          OrderSide `json:"side"`
	FilledQty     float64   `json:"filled_qty"`
	FillPrice     float64   `json:"fill_price"`
	Commission    float64   `json:"commission"`
	Timestamp     time.Time `json:"timestamp"`
	SeqID         uint64    `json:"seq_id"`
	LatencyNs     int64     `json:"latency_ns"`
}

// RiskCheckResult for pre-trade validation
type RiskCheckResult struct {
	Approved    bool   `json:"approved"`
	Reason      string `json:"reason"`
	CheckTimeNs int64  `json:"check_time_ns"`
}

// WSEvent for WebSocket broadcast to frontend
type WSEvent struct {
	Type      string      `json:"type"`
	Data      interface{} `json:"data"`
	SeqID     uint64      `json:"seq_id"`
	Timestamp time.Time   `json:"timestamp"`
}

// LatencyMetrics for observability
type LatencyMetrics struct {
	FeedIngestionP50  int64  `json:"feed_ingestion_p50_us"`
	FeedIngestionP99  int64  `json:"feed_ingestion_p99_us"`
	RiskCheckP50      int64  `json:"risk_check_p50_us"`
	RiskCheckP99      int64  `json:"risk_check_p99_us"`
	E2ELatencyP50     int64  `json:"e2e_latency_p50_us"`
	E2ELatencyP99     int64  `json:"e2e_latency_p99_us"`
	TicksProcessed    uint64 `json:"ticks_processed"`
	FillsProcessed    uint64 `json:"fills_processed"`
	OrdersSubmitted   uint64 `json:"orders_submitted"`
	RiskRejections    uint64 `json:"risk_rejections"`
	GapsDetected      uint64 `json:"gaps_detected"`
	Reconnects        uint64 `json:"reconnects"`
}
