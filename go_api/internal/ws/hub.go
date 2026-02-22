// Package ws — WebSocket broadcaster for Go Orchestrator
//
// Manages concurrent WebSocket connections from frontend clients.
// Backpressure-aware: slow clients are dropped, not blocking the broadcast.
// Supports 10,000+ concurrent connections.
//
// Architecture:
//   - Hub runs in its own goroutine
//   - Each client has its own send channel (buffered)
//   - Broadcast sends to all registered clients
//   - Slow clients are disconnected after buffer overflow
//   - Sequence IDs ensure deterministic ordering

package ws

import (
	"encoding/json"
	"log"
	"sync"
	"time"
)

// Event is the WebSocket event structure
type Event struct {
	Type      string      `json:"type"`
	Data      interface{} `json:"data"`
	SeqID     uint64      `json:"seq_id"`
	Timestamp time.Time   `json:"timestamp"`
}

// Client represents a connected WebSocket client
type Client struct {
	ID       string
	SendCh   chan []byte
	Done     chan struct{}
}

// Hub manages all WebSocket connections
type Hub struct {
	mu         sync.RWMutex
	clients    map[string]*Client
	broadcast  chan Event
	register   chan *Client
	unregister chan string
	maxClients int
	stats      HubStats
}

// HubStats tracks WebSocket connection statistics
type HubStats struct {
	ActiveConnections  int    `json:"active_connections"`
	TotalConnections   uint64 `json:"total_connections"`
	TotalDisconnects   uint64 `json:"total_disconnects"`
	MessagesBroadcast  uint64 `json:"messages_broadcast"`
	SlowClientDrops    uint64 `json:"slow_client_drops"`
}

// NewHub creates a new WebSocket hub
func NewHub(maxClients int) *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		broadcast:  make(chan Event, 5000),
		register:   make(chan *Client, 100),
		unregister: make(chan string, 100),
		maxClients: maxClients,
	}
}

// Run starts the hub's main loop
func (h *Hub) Run() {
	log.Println("[WSHub] WebSocket broadcast hub started")
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			if len(h.clients) >= h.maxClients {
				log.Printf("[WSHub] Max clients reached (%d), rejecting %s", h.maxClients, client.ID)
				close(client.Done)
			} else {
				h.clients[client.ID] = client
				h.stats.ActiveConnections = len(h.clients)
				h.stats.TotalConnections++
				log.Printf("[WSHub] Client connected: %s (total: %d)", client.ID, len(h.clients))
			}
			h.mu.Unlock()

		case clientID := <-h.unregister:
			h.mu.Lock()
			if client, ok := h.clients[clientID]; ok {
				close(client.SendCh)
				delete(h.clients, clientID)
				h.stats.ActiveConnections = len(h.clients)
				h.stats.TotalDisconnects++
				log.Printf("[WSHub] Client disconnected: %s (total: %d)", clientID, len(h.clients))
			}
			h.mu.Unlock()

		case event := <-h.broadcast:
			data, err := json.Marshal(event)
			if err != nil {
				log.Printf("[WSHub] Marshal error: %v", err)
				continue
			}

			h.mu.RLock()
			for id, client := range h.clients {
				select {
				case client.SendCh <- data:
					// Sent successfully
				default:
					// Client too slow — drop it (backpressure protection)
					log.Printf("[WSHub] Slow client dropped: %s", id)
					h.stats.SlowClientDrops++
					go func(cid string) {
						h.unregister <- cid
					}(id)
				}
			}
			h.stats.MessagesBroadcast++
			h.mu.RUnlock()
		}
	}
}

// Broadcast sends an event to all connected clients
func (h *Hub) Broadcast(event Event) {
	select {
	case h.broadcast <- event:
	default:
		log.Println("[WSHub] Broadcast channel full — dropping event (backpressure)")
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

// Stats returns current hub statistics
func (h *Hub) Stats() HubStats {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.stats
}
