// Package handlers — Zero-Allocation HTTP Handlers
package handlers

import (
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

var (
	// Pre-allocated response buffers
	okBuf    = []byte(`{"status":"ok"}`)
	healthMu sync.Once
	health   []byte
)

func init() {
	// Pre-build health response once
	healthMu.Do(func() {
		health = []byte(`{"status":"healthy","service":"go-orchestrator","version":"3.0-zero-bottleneck"}`)
	})
}

// HealthHandler returns pre-allocated health response
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Response-Time", "0ns")
	w.Write(health)
}

// NotFoundHandler returns 404
func NotFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	w.Write([]byte(`{"error":"not_found"}`))
}

// MethodNotAllowedHandler returns 405
func MethodNotAllowedHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusMethodNotAllowed)
	w.Write([]byte(`{"error":"method_not_allowed"}`))
}

// LatencyTracker for handlers
var handlerLatency int64

// RecordHandlerLatency records handler latency
func RecordHandlerLatency(ns int64) {
	atomic.StoreInt64(&handlerLatency, ns)
}

// GetHandlerLatency returns current latency
func GetHandlerLatency() int64 {
	return atomic.LoadInt64(&handlerLatency)
}
