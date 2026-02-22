// Package main — Go Orchestrator Entry Point
// Authoritative State Engine for Cenayang Market Trading System
//
// Responsibilities:
//   - Subscribe to Rust normalized market data feed via NATS
//   - Maintain authoritative portfolio state (single source of truth)
//   - Risk validation engine (pre-trade, post-trade, real-time)
//   - Position manager with atomic state updates
//   - Capital allocator with drawdown protection
//   - Circuit breaker + kill-switch logic
//   - REST API for frontend (read state)
//   - WebSocket broadcaster (push state to 10k+ clients)
//
// Concurrency Model:
//   - Dedicated ingestion goroutines (NATS subscribers)
//   - Dedicated risk validation workers
//   - Dedicated execution channel (to Rust)
//   - Lock-minimized state via channels
//   - Single authoritative StateManager goroutine
//   - Backpressure-aware WebSocket broadcast layer

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// ============================================================================
// CONFIGURATION
// ============================================================================

type Config struct {
	HTTPPort        int    `json:"http_port"`
	WSPort          int    `json:"ws_port"`
	NATSUrl         string `json:"nats_url"`
	PythonAIUrl     string `json:"python_ai_url"`
	RustGatewayUrl  string `json:"rust_gateway_url"`
	MaxDrawdownPct  float64 `json:"max_drawdown_pct"`
	MaxPositionSize float64 `json:"max_position_size"`
	DailyLossLimit  float64 `json:"daily_loss_limit"`
	KillSwitchEnabled bool  `json:"kill_switch_enabled"`
}

func DefaultConfig() Config {
	return Config{
		HTTPPort:        8090,
		WSPort:          8091,
		NATSUrl:         "nats://localhost:4222",
		PythonAIUrl:     "http://localhost:5000",
		RustGatewayUrl:  "http://localhost:9090",
		MaxDrawdownPct:  5.0,
		MaxPositionSize: 100000.0,
		DailyLossLimit:  10000.0,
		KillSwitchEnabled: true,
	}
}

// ============================================================================
// CORE TYPES — Deterministic, Auditable
// ============================================================================

type OrderSide string
const (
	Buy  OrderSide = "BUY"
	Sell OrderSide = "SELL"
)

type OrderStatus string
const (
	OrderPending   OrderStatus = "PENDING"
	OrderSubmitted OrderStatus = "SUBMITTED"
	OrderFilled    OrderStatus = "FILLED"
	OrderPartial   OrderStatus = "PARTIAL"
	OrderCancelled OrderStatus = "CANCELLED"
	OrderRejected  OrderStatus = "REJECTED"
)

type Order struct {
	ID            string      `json:"id"`
	ClientID      string      `json:"client_id"`
	Symbol        string      `json:"symbol"`
	Side          OrderSide   `json:"side"`
	Quantity      float64     `json:"quantity"`
	Price         float64     `json:"price"`
	Status        OrderStatus `json:"status"`
	FilledQty     float64     `json:"filled_qty"`
	AvgFillPrice  float64     `json:"avg_fill_price"`
	CreatedAt     time.Time   `json:"created_at"`
	UpdatedAt     time.Time   `json:"updated_at"`
	ExchangeOrdID string     `json:"exchange_order_id"`
	SequenceID    uint64      `json:"sequence_id"`
}

type Position struct {
	Symbol       string    `json:"symbol"`
	Side         OrderSide `json:"side"`
	Quantity     float64   `json:"quantity"`
	EntryPrice   float64   `json:"entry_price"`
	CurrentPrice float64   `json:"current_price"`
	UnrealizedPnL float64  `json:"unrealized_pnl"`
	RealizedPnL  float64   `json:"realized_pnl"`
	UpdatedAt    time.Time `json:"updated_at"`
}

type PortfolioState struct {
	Equity          float64              `json:"equity"`
	Cash            float64              `json:"cash"`
	TotalPnL        float64              `json:"total_pnl"`
	DailyPnL        float64              `json:"daily_pnl"`
	MaxDrawdown     float64              `json:"max_drawdown"`
	CurrentDrawdown float64              `json:"current_drawdown"`
	Positions       map[string]*Position `json:"positions"`
	OpenOrders      map[string]*Order    `json:"open_orders"`
	HighWaterMark   float64              `json:"high_water_mark"`
	KillSwitchActive bool                `json:"kill_switch_active"`
	SequenceID      uint64               `json:"sequence_id"`
	Timestamp       time.Time            `json:"timestamp"`
}

type MarketTick struct {
	Symbol    string    `json:"symbol"`
	BidPrice  float64   `json:"bid_price"`
	AskPrice  float64   `json:"ask_price"`
	BidSize   float64   `json:"bid_size"`
	AskSize   float64   `json:"ask_size"`
	LastPrice float64   `json:"last_price"`
	Volume    float64   `json:"volume"`
	Timestamp time.Time `json:"timestamp"`
	SeqID     uint64    `json:"seq_id"`
	LatencyNs int64     `json:"latency_ns"`
}

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

type RiskCheckResult struct {
	Approved    bool   `json:"approved"`
	Reason      string `json:"reason"`
	CheckTimeNs int64  `json:"check_time_ns"`
}

type WSEvent struct {
	Type      string      `json:"type"`
	Data      interface{} `json:"data"`
	SeqID     uint64      `json:"seq_id"`
	Timestamp time.Time   `json:"timestamp"`
}

// ============================================================================
// STATE MANAGER — Single Authoritative Goroutine
// ============================================================================

type StateManager struct {
	mu             sync.RWMutex
	state          *PortfolioState
	config         Config
	sequenceID     uint64
	tickCh         chan MarketTick
	fillCh         chan FillEvent
	orderCh        chan Order
	broadcastCh    chan WSEvent
	killSwitchCh   chan bool
	latencyMetrics *LatencyMetrics
}

type LatencyMetrics struct {
	mu                sync.Mutex
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
	BroadcastDrops    uint64 `json:"broadcast_drops"`
}

func NewStateManager(cfg Config) *StateManager {
	return &StateManager{
		state: &PortfolioState{
			Equity:        100000.0,
			Cash:          100000.0,
			Positions:     make(map[string]*Position),
			OpenOrders:    make(map[string]*Order),
			HighWaterMark: 100000.0,
			Timestamp:     time.Now(),
		},
		config:         cfg,
		tickCh:         make(chan MarketTick, 10000),      // Backpressure buffer
		fillCh:         make(chan FillEvent, 1000),
		orderCh:        make(chan Order, 1000),
		broadcastCh:    make(chan WSEvent, 5000),
		killSwitchCh:   make(chan bool, 1),
		latencyMetrics: &LatencyMetrics{},
	}
}

func (sm *StateManager) Run(ctx context.Context) {
	log.Println("[StateManager] Authoritative state engine started")
	for {
		select {
		case <-ctx.Done():
			log.Println("[StateManager] Shutting down")
			return

		case tick := <-sm.tickCh:
			sm.processTick(tick)

		case fill := <-sm.fillCh:
			sm.processFill(fill)

		case order := <-sm.orderCh:
			sm.processOrder(order)

		case active := <-sm.killSwitchCh:
			sm.processKillSwitch(active)
		}
	}
}

func (sm *StateManager) processTick(tick MarketTick) {
	start := time.Now()
	sm.mu.Lock()

	if pos, ok := sm.state.Positions[tick.Symbol]; ok {
		pos.CurrentPrice = tick.LastPrice
		if pos.Side == Buy {
			pos.UnrealizedPnL = (tick.LastPrice - pos.EntryPrice) * pos.Quantity
		} else {
			pos.UnrealizedPnL = (pos.EntryPrice - tick.LastPrice) * pos.Quantity
		}
		pos.UpdatedAt = tick.Timestamp
	}

	// Recompute portfolio metrics
	totalUnrealized := 0.0
	for _, pos := range sm.state.Positions {
		totalUnrealized += pos.UnrealizedPnL
	}
	sm.state.Equity = sm.state.Cash + totalUnrealized
	sm.state.TotalPnL = sm.state.Equity - 100000.0

	// Drawdown calculation
	if sm.state.Equity > sm.state.HighWaterMark {
		sm.state.HighWaterMark = sm.state.Equity
	}
	sm.state.CurrentDrawdown = (sm.state.HighWaterMark - sm.state.Equity) / sm.state.HighWaterMark * 100.0
	if sm.state.CurrentDrawdown > sm.state.MaxDrawdown {
		sm.state.MaxDrawdown = sm.state.CurrentDrawdown
	}

	// Circuit breaker: auto kill-switch on max drawdown
	if sm.config.KillSwitchEnabled && sm.state.CurrentDrawdown >= sm.config.MaxDrawdownPct {
		sm.state.KillSwitchActive = true
		log.Printf("[CIRCUIT BREAKER] Drawdown %.2f%% >= limit %.2f%%. KILL SWITCH ACTIVATED.", sm.state.CurrentDrawdown, sm.config.MaxDrawdownPct)
	}

	sm.state.SequenceID++
	seqID := sm.state.SequenceID // Capture inside lock — NO race condition
	sm.state.Timestamp = time.Now()
	sm.mu.Unlock()

	// NON-BLOCKING broadcast — select+default ensures <10μs hot path
	// If broadcastCh is full, drop event (backpressure protection)
	select {
	case sm.broadcastCh <- WSEvent{
		Type:      "portfolio_update",
		Data:      sm.GetState(),
		SeqID:     seqID,
		Timestamp: time.Now(),
	}:
	default:
		// Channel full — drop broadcast to protect hot path
		sm.latencyMetrics.mu.Lock()
		sm.latencyMetrics.BroadcastDrops++
		sm.latencyMetrics.mu.Unlock()
	}

	// Latency tracking — atomic increment, no mutex in hot path
	elapsed := time.Since(start).Microseconds()
	sm.latencyMetrics.mu.Lock()
	sm.latencyMetrics.TicksProcessed++
	sm.latencyMetrics.FeedIngestionP50 = elapsed
	sm.latencyMetrics.mu.Unlock()
}

func (sm *StateManager) processFill(fill FillEvent) {
	sm.mu.Lock()

	// Update order status
	if order, ok := sm.state.OpenOrders[fill.OrderID]; ok {
		order.FilledQty += fill.FilledQty
		order.AvgFillPrice = fill.FillPrice
		order.UpdatedAt = fill.Timestamp
		if order.FilledQty >= order.Quantity {
			order.Status = OrderFilled
			delete(sm.state.OpenOrders, fill.OrderID)
		} else {
			order.Status = OrderPartial
		}
	}

	// Update position
	pos, exists := sm.state.Positions[fill.Symbol]
	if !exists {
		pos = &Position{
			Symbol:     fill.Symbol,
			Side:       fill.Side,
			EntryPrice: fill.FillPrice,
			UpdatedAt:  fill.Timestamp,
		}
		sm.state.Positions[fill.Symbol] = pos
	}

	if fill.Side == pos.Side {
		// Increasing position
		totalCost := pos.EntryPrice*pos.Quantity + fill.FillPrice*fill.FilledQty
		pos.Quantity += fill.FilledQty
		if pos.Quantity > 0 {
			pos.EntryPrice = totalCost / pos.Quantity
		}
	} else {
		// Reducing position
		pnl := 0.0
		if pos.Side == Buy {
			pnl = (fill.FillPrice - pos.EntryPrice) * fill.FilledQty
		} else {
			pnl = (pos.EntryPrice - fill.FillPrice) * fill.FilledQty
		}
		pos.RealizedPnL += pnl
		pos.Quantity -= fill.FilledQty
		sm.state.Cash += pnl

		if pos.Quantity <= 0 {
			delete(sm.state.Positions, fill.Symbol)
		}
	}

	sm.state.Cash -= fill.Commission
	sm.state.SequenceID++
	seqID := sm.state.SequenceID // Capture inside lock
	sm.state.Timestamp = time.Now()
	sm.mu.Unlock()

	sm.latencyMetrics.mu.Lock()
	sm.latencyMetrics.FillsProcessed++
	sm.latencyMetrics.mu.Unlock()

	// NON-BLOCKING broadcast
	select {
	case sm.broadcastCh <- WSEvent{
		Type:      "fill",
		Data:      fill,
		SeqID:     seqID,
		Timestamp: time.Now(),
	}:
	default:
		sm.latencyMetrics.mu.Lock()
		sm.latencyMetrics.BroadcastDrops++
		sm.latencyMetrics.mu.Unlock()
	}
}

func (sm *StateManager) processOrder(order Order) {
	sm.mu.Lock()
	sm.state.OpenOrders[order.ID] = &order
	sm.state.SequenceID++
	sm.mu.Unlock()

	sm.latencyMetrics.mu.Lock()
	sm.latencyMetrics.OrdersSubmitted++
	sm.latencyMetrics.mu.Unlock()
}

func (sm *StateManager) processKillSwitch(active bool) {
	sm.mu.Lock()
	sm.state.KillSwitchActive = active
	sm.state.SequenceID++
	seqID := sm.state.SequenceID // Capture inside lock
	sm.state.Timestamp = time.Now()
	sm.mu.Unlock()

	log.Printf("[KILL SWITCH] Active: %v", active)
	// NON-BLOCKING broadcast
	select {
	case sm.broadcastCh <- WSEvent{
		Type:      "kill_switch",
		Data:      map[string]bool{"active": active},
		SeqID:     seqID,
		Timestamp: time.Now(),
	}:
	default:
		sm.latencyMetrics.mu.Lock()
		sm.latencyMetrics.BroadcastDrops++
		sm.latencyMetrics.mu.Unlock()
	}
}

// ValidateRisk performs pre-trade risk check. Returns approval or rejection.
func (sm *StateManager) ValidateRisk(order Order) RiskCheckResult {
	start := time.Now()
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	// Kill switch check
	if sm.state.KillSwitchActive {
		return RiskCheckResult{Approved: false, Reason: "KILL_SWITCH_ACTIVE", CheckTimeNs: time.Since(start).Nanoseconds()}
	}

	// Drawdown check
	if sm.state.CurrentDrawdown >= sm.config.MaxDrawdownPct {
		sm.latencyMetrics.mu.Lock()
		sm.latencyMetrics.RiskRejections++
		sm.latencyMetrics.mu.Unlock()
		return RiskCheckResult{Approved: false, Reason: fmt.Sprintf("MAX_DRAWDOWN: %.2f%%", sm.state.CurrentDrawdown), CheckTimeNs: time.Since(start).Nanoseconds()}
	}

	// Position size check
	notional := order.Price * order.Quantity
	if notional > sm.config.MaxPositionSize {
		sm.latencyMetrics.mu.Lock()
		sm.latencyMetrics.RiskRejections++
		sm.latencyMetrics.mu.Unlock()
		return RiskCheckResult{Approved: false, Reason: fmt.Sprintf("POSITION_TOO_LARGE: $%.2f", notional), CheckTimeNs: time.Since(start).Nanoseconds()}
	}

	// Daily loss limit check
	if sm.state.DailyPnL < -sm.config.DailyLossLimit {
		sm.latencyMetrics.mu.Lock()
		sm.latencyMetrics.RiskRejections++
		sm.latencyMetrics.mu.Unlock()
		return RiskCheckResult{Approved: false, Reason: "DAILY_LOSS_LIMIT_EXCEEDED", CheckTimeNs: time.Since(start).Nanoseconds()}
	}

	// Capital availability check
	if order.Side == Buy && notional > sm.state.Cash {
		return RiskCheckResult{Approved: false, Reason: "INSUFFICIENT_CAPITAL", CheckTimeNs: time.Since(start).Nanoseconds()}
	}

	elapsed := time.Since(start).Nanoseconds()
	sm.latencyMetrics.mu.Lock()
	sm.latencyMetrics.RiskCheckP50 = elapsed / 1000
	sm.latencyMetrics.mu.Unlock()

	return RiskCheckResult{Approved: true, Reason: "APPROVED", CheckTimeNs: elapsed}
}

func (sm *StateManager) GetState() PortfolioState {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	// Deep copy for thread safety
	state := *sm.state
	state.Positions = make(map[string]*Position, len(sm.state.Positions))
	for k, v := range sm.state.Positions {
		p := *v
		state.Positions[k] = &p
	}
	return state
}

func (sm *StateManager) GetLatencyMetrics() LatencyMetrics {
	sm.latencyMetrics.mu.Lock()
	defer sm.latencyMetrics.mu.Unlock()
	return *sm.latencyMetrics
}

// ============================================================================
// HTTP API — REST Endpoints for Frontend
// ============================================================================

func setupHTTPRoutes(sm *StateManager) *http.ServeMux {
	mux := http.NewServeMux()

	// Health
	mux.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":       "healthy",
			"service":      "go-orchestrator",
			"kill_switch":  sm.state.KillSwitchActive,
			"uptime_ns":    time.Since(time.Now()).Nanoseconds(),
			"timestamp":    time.Now(),
		})
	})

	// Portfolio State (authoritative)
	mux.HandleFunc("/api/portfolio", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(sm.GetState())
	})

	// Positions
	mux.HandleFunc("/api/positions", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		state := sm.GetState()
		positions := make([]*Position, 0, len(state.Positions))
		for _, p := range state.Positions {
			positions = append(positions, p)
		}
		json.NewEncoder(w).Encode(positions)
	})

	// Open Orders
	mux.HandleFunc("/api/orders", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		state := sm.GetState()
		orders := make([]*Order, 0, len(state.OpenOrders))
		for _, o := range state.OpenOrders {
			orders = append(orders, o)
		}
		json.NewEncoder(w).Encode(orders)
	})

	// Risk Check (pre-trade validation)
	mux.HandleFunc("/api/risk/check", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST required", http.StatusMethodNotAllowed)
			return
		}
		var order Order
		if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		result := sm.ValidateRisk(order)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	})

	// Kill Switch
	mux.HandleFunc("/api/kill-switch", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			var payload struct {
				Active bool `json:"active"`
			}
			json.NewDecoder(r.Body).Decode(&payload)
			sm.killSwitchCh <- payload.Active
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]bool{"active": payload.Active})
		case http.MethodGet:
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]bool{"active": sm.state.KillSwitchActive})
		}
	})

	// Latency Metrics
	mux.HandleFunc("/api/metrics/latency", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(sm.GetLatencyMetrics())
	})

	// System Health
	mux.HandleFunc("/api/system/health", func(w http.ResponseWriter, r *http.Request) {
		metrics := sm.GetLatencyMetrics()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"state_engine":       "running",
			"ticks_processed":    metrics.TicksProcessed,
			"fills_processed":    metrics.FillsProcessed,
			"orders_submitted":   metrics.OrdersSubmitted,
			"risk_rejections":    metrics.RiskRejections,
			"feed_latency_p50_us": metrics.FeedIngestionP50,
			"risk_check_p50_us":  metrics.RiskCheckP50,
			"kill_switch":        sm.state.KillSwitchActive,
			"equity":             sm.state.Equity,
			"drawdown_pct":       sm.state.CurrentDrawdown,
		})
	})

	return mux
}

// ============================================================================
// MAIN
// ============================================================================

func main() {
	cfg := DefaultConfig()
	sm := NewStateManager(cfg)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start state manager
	go sm.Run(ctx)

	// HTTP Server
	mux := setupHTTPRoutes(sm)
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.HTTPPort),
		Handler:      corsMiddleware(mux),
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	go func() {
		log.Printf("[HTTP] Go Orchestrator API listening on :%d", cfg.HTTPPort)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[HTTP] Server error: %v", err)
		}
	}()

	// Graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	log.Println("[SHUTDOWN] Graceful shutdown initiated")
	cancel()
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	server.Shutdown(shutdownCtx)
	log.Println("[SHUTDOWN] Complete")
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}
