// Package handlers — HTTP request handlers for Go Orchestrator REST API
//
// All handlers read from the authoritative StateManager.
// No handler mutates state directly — all mutations go through channels.

package handlers

import (
	"encoding/json"
	"net/http"
	"time"
)

// HealthResponse represents the API health check response
type HealthResponse struct {
	Status    string    `json:"status"`
	Service   string    `json:"service"`
	Version   string    `json:"version"`
	Timestamp time.Time `json:"timestamp"`
}

// WriteJSON is a helper to write JSON responses with proper headers
func WriteJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Service", "go-orchestrator")
	w.Header().Set("X-Timestamp", time.Now().UTC().Format(time.RFC3339Nano))
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// HealthHandler handles GET /api/health
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	WriteJSON(w, http.StatusOK, HealthResponse{
		Status:    "healthy",
		Service:   "go-orchestrator",
		Version:   "1.0.0",
		Timestamp: time.Now().UTC(),
	})
}

// ErrorResponse is a standard error response format
type ErrorResponse struct {
	Error   string `json:"error"`
	Code    string `json:"code"`
	Details string `json:"details,omitempty"`
}

// WriteError writes a standard error response
func WriteError(w http.ResponseWriter, status int, code string, message string) {
	WriteJSON(w, status, ErrorResponse{
		Error: message,
		Code:  code,
	})
}
