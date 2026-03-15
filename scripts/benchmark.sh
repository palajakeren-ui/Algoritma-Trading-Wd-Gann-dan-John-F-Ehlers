#!/bin/bash
# ============================================================================
# CENAYANG MARKET - Performance Benchmark Script
# ============================================================================

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  CENAYANG MARKET - Performance Benchmark                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

API_URL="${API_URL:-http://localhost:8090}"
ITERATIONS="${ITERATIONS:-10000}"

echo ""
echo "API URL: $API_URL"
echo "Iterations: $ITERATIONS"
echo ""

# Function to measure latency
measure_latency() {
    local endpoint=$1
    local name=$2
    
    echo "[Benchmark] Testing $name..."
    
    total_time=0
    success_count=0
    min_time=999999
    max_time=0
    
    for i in $(seq 1 $ITERATIONS); do
        start=$(date +%s%N)
        response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint" 2>/dev/null)
        end=$(date +%s%N)
        
        if [ "$response" = "200" ]; then
            latency=$(( (end - start) / 1000 ))  # Convert to microseconds
            total_time=$((total_time + latency))
            success_count=$((success_count + 1))
            
            if [ $latency -lt $min_time ]; then
                min_time=$latency
            fi
            
            if [ $latency -gt $max_time ]; then
                max_time=$latency
            fi
        fi
    done
    
    if [ $success_count -gt 0 ]; then
        avg_time=$((total_time / success_count))
        echo "  Success: $success_count/$ITERATIONS"
        echo "  Latency: Min=${min_time}μs, Max=${max_time}μs, Avg=${avg_time}μs"
    else
        echo "  ERROR: All requests failed"
    fi
    echo ""
}

# Health check
echo "[Health Check] Verifying services..."
curl -s "$API_URL/api/health" | jq . 2>/dev/null || echo "Health endpoint not responding"
echo ""

# Run benchmarks
measure_latency "/api/health" "Health Check"
measure_latency "/api/portfolio" "Portfolio State"
measure_latency "/api/metrics/latency" "Latency Metrics"

# Latency metrics from server
echo "[Server Metrics]"
curl -s "$API_URL/api/metrics/latency" | jq . 2>/dev/null || echo "Metrics not available"
echo ""

# WebSocket latency test (requires wscat)
if command -v wscat &> /dev/null; then
    echo "[WebSocket] Testing WebSocket connection..."
    timeout 5 wscat -c "ws://localhost:8090/ws" 2>&1 | head -20 || echo "WebSocket test completed"
else
    echo "[WebSocket] wscat not installed, skipping WebSocket test"
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Benchmark Complete                                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
