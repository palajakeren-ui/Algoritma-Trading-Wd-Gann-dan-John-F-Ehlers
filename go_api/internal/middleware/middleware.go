// Package middleware — Zero-Allocation HTTP Middleware
package middleware

import (
	"log"
	"net/http"
	"sync/atomic"
	"time"
)

// CORS middleware with pre-allocated headers
func CORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Pre-set headers (no allocation)
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
		w.Header().Set("Access-Control-Max-Age", "86400")
		
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// LatencyTracker with atomic counter
var requestCount uint64

// Logging middleware with minimal allocation
func Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		elapsed := time.Since(start)
		
		atomic.AddUint64(&requestCount, 1)
		
		// Only log slow requests (> 10ms)
		if elapsed > 10*time.Millisecond {
			log.Printf("[SLOW] %s %s %v", r.Method, r.URL.Path, elapsed)
		}
	})
}

// Recovery middleware catches panics
func Recovery(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				log.Printf("[PANIC] %v — %s %s", err, r.Method, r.URL.Path)
				http.Error(w, `{"error":"internal_server_error"}`, http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// GetRequestCount returns total requests processed
func GetRequestCount() uint64 {
	return atomic.LoadUint64(&requestCount)
}
