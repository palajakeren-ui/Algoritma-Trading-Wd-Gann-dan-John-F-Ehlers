// Package ws — Zero-Bottleneck WebSocket Broadcaster
package ws

import (
	"context"
	"sync"
	"sync/atomic"
	"time"
)

const (
	MaxClients      = 10000
	SendBufferSize  = 256
	BroadcastBuffer = 10000
)

// Event types
const (
	EventPortfolio  uint8 = 1
	EventFill       uint8 = 2
	EventKillSwitch uint8 = 3
	EventTick       uint8 = 4
)

// BinaryEvent for zero-copy broadcasting
type BinaryEvent struct {
	Type      uint8
	SeqID     uint64
	Timestamp int64
	Data      []byte
}

// Client connection
type Client struct {
	ID       string
	sendCh   chan []byte
	done     chan struct{}
	lastSend int64 // Unix nanos
}

// Hub manages WebSocket connections
type Hub struct {
	clients sync.Map // map[string]*Client

	// Channels
	register   chan *Client
	unregister chan string
	broadcast  chan BinaryEvent

	// Atomic stats
	activeConnections uint64
	totalConnections  uint64
	totalDisconnects  uint64
	messagesBroadcast uint64
	slowClientDrops   uint64
	broadcastDrops    uint64

	// Shutdown
	ctx    context.Context
	cancel context.CancelFunc
}

// NewHub creates a zero-bottleneck WebSocket hub
func NewHub() *Hub {
	ctx, cancel := context.WithCancel(context.Background())
	return &Hub{
		register:   make(chan *Client, 100),
		unregister: make(chan string, 100),
		broadcast:  make(chan BinaryEvent, BroadcastBuffer),
		ctx:        ctx,
		cancel:     cancel,
	}
}

// Run starts the hub event loop
func (h *Hub) Run() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-h.ctx.Done():
			h.closeAllClients()
			return

		case client := <-h.register:
			h.handleRegister(client)

		case clientID := <-h.unregister:
			h.handleUnregister(clientID)

		case event := <-h.broadcast:
			h.handleBroadcast(event)

		case <-ticker.C:
			// Periodic cleanup (optional)
		}
	}
}

func (h *Hub) handleRegister(client *Client) {
	// Check max clients
	if atomic.LoadUint64(&h.activeConnections) >= MaxClients {
		close(client.done)
		return
	}

	h.clients.Store(client.ID, client)
	atomic.AddUint64(&h.activeConnections, 1)
	atomic.AddUint64(&h.totalConnections, 1)
}

func (h *Hub) handleUnregister(clientID string) {
	if val, ok := h.clients.LoadAndDelete(clientID); ok {
		client := val.(*Client)
		close(client.done)
		atomic.AddUint64(&h.activeConnections, ^uint64(0)) // Decrement
		atomic.AddUint64(&h.totalDisconnects, 1)
	}
}

func (h *Hub) handleBroadcast(event BinaryEvent) {
	data := event.Data
	dropped := uint64(0)

	h.clients.Range(func(key, value interface{}) bool {
		client := value.(*Client)

		// Non-blocking send
		select {
		case client.sendCh <- data:
			client.lastSend = time.Now().UnixNano()
		default:
			// Client too slow - mark for drop
			dropped++
			go h.Unregister(client.ID)
		}
		return true
	})

	atomic.AddUint64(&h.messagesBroadcast, 1)
	atomic.AddUint64(&h.slowClientDrops, dropped)
}

func (h *Hub) closeAllClients() {
	h.clients.Range(func(key, value interface{}) bool {
		client := value.(*Client)
		close(client.done)
		h.clients.Delete(key)
		return true
	})
}

// Broadcast sends event to all clients (non-blocking)
func (h *Hub) Broadcast(event BinaryEvent) {
	select {
	case h.broadcast <- event:
	default:
		atomic.AddUint64(&h.broadcastDrops, 1)
	}
}

// Register adds a new client
func (h *Hub) Register(client *Client) {
	h.register <- client
}

// Unregister removes a client
func (h *Hub) Unregister(clientID string) {
	h.unregister <- clientID
}

// Stats returns current statistics
func (h *Hub) Stats() map[string]uint64 {
	return map[string]uint64{
		"active_connections": atomic.LoadUint64(&h.activeConnections),
		"total_connections":  atomic.LoadUint64(&h.totalConnections),
		"total_disconnects":  atomic.LoadUint64(&h.totalDisconnects),
		"messages_broadcast": atomic.LoadUint64(&h.messagesBroadcast),
		"slow_client_drops":  atomic.LoadUint64(&h.slowClientDrops),
		"broadcast_drops":    atomic.LoadUint64(&h.broadcastDrops),
	}
}

// Shutdown stops the hub
func (h *Hub) Shutdown() {
	h.cancel()
}

// NewClient creates a new client
func NewClient(id string) *Client {
	return &Client{
		ID:     id,
		sendCh: make(chan []byte, SendBufferSize),
		done:   make(chan struct{}),
	}
}
