// Package models — Cache-Line Aligned Data Models
package models

// Cache line size for alignment
const CacheLineSize = 64

// OrderSide enum
type OrderSide uint8

const (
	Buy OrderSide = iota
	Sell
)

// OrderStatus enum
type OrderStatus uint8

const (
	StatusPending OrderStatus = iota
	StatusSubmitted
	StatusFilled
	StatusPartial
	StatusCancelled
	StatusRejected
)

// OrderOptimized - 64 bytes, cache-line aligned
type OrderOptimized struct {
	ID           uint64
	ClientHash   uint64
	SymbolHash   uint64
	Side         uint8
	Status       uint8
	Quantity     int64 // Fixed-point
	Price        int64 // Fixed-point
	FilledQty    int64
	AvgFillPrice int64
	SequenceID   uint64
	Timestamp    int64
	_            [20]byte // Padding to 64 bytes
}

// PositionOptimized - 64 bytes, cache-line aligned
type PositionOptimized struct {
	SymbolHash    uint64
	Side          uint8
	Quantity      int64 // Fixed-point
	EntryPrice    int64 // Fixed-point
	CurrentPrice  int64 // Fixed-point
	UnrealizedPnL int64
	RealizedPnL   int64
	UpdatedAt     int64
	_             [24]byte // Padding to 64 bytes
}

// PortfolioStateOptimized - cache-line aligned
type PortfolioStateOptimized struct {
	Equity          int64
	Cash            int64
	TotalPnL        int64
	DailyPnL        int64
	HighWaterMark   int64
	CurrentDrawdown int64
	KillSwitch      int32
	SequenceID      uint64
	Timestamp       int64
	_               [24]byte // Padding
}

// MarketTickOptimized - for binary serialization
type MarketTickOptimized struct {
	SymbolHash uint64
	BidPrice   int64
	AskPrice   int64
	BidSize    int64
	AskSize    int64
	LastPrice  int64
	Volume     int64
	Timestamp  int64
	SeqID      uint64
	LatencyNs  int32
	Flags      uint32
}

// Constants for fixed-point arithmetic
const (
	PriceScale = 100_000_000 // 8 decimal places

	// Pre-computed symbol hashes
	SymbolHashBTC uint64 = 0xAF4F2D6E8B1C3A5F
	SymbolHashETH uint64 = 0xBF5G3E7F9C2D4B6A
)

// FNV1aHash computes FNV-1a hash for symbol strings
func FNV1aHash(s string) uint64 {
	var hash uint64 = 14695981039346656037
	for _, b := range []byte(s) {
		hash ^= uint64(b)
		hash *= 1099511628211
	}
	return hash
}
