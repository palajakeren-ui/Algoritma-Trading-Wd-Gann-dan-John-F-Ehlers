#!/bin/bash
# ============================================================================
# INTEGRATION TESTS — Cenayang Market Live Trading
# ============================================================================

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  CENAYANG MARKET — Integration Tests                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

API_URL="${API_URL:-http://localhost:8090}"
RUST_URL="${RUST_URL:-http://localhost:8080}"
PASS=0
FAIL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_case() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    local method=${4:-GET}
    local data=${5:-}
    
    echo -n "Testing: $name... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null || echo "000")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$url" 2>/dev/null || echo "000")
    fi
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_code, got HTTP $response)"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

test_json_field() {
    local name=$1
    local url=$2
    local field=$3
    local expected=$4
    
    echo -n "Testing: $name... "
    
    response=$(curl -s "$url" 2>/dev/null)
    actual=$(echo "$response" | jq -r ".$field" 2>/dev/null || echo "null")
    
    if [ "$actual" = "$expected" ]; then
        echo -e "${GREEN}✓ PASS${NC} ($field = $actual)"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} ($field: expected '$expected', got '$actual')"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

test_latency() {
    local name=$1
    local url=$2
    local max_ms=$3
    
    echo -n "Testing: $name (max ${max_ms}ms)... "
    
    start=$(date +%s%N)
    curl -s -o /dev/null "$url" 2>/dev/null
    end=$(date +%s%N)
    
    latency_ms=$(( (end - start) / 1000000 ))
    
    if [ $latency_ms -le $max_ms ]; then
        echo -e "${GREEN}✓ PASS${NC} (${latency_ms}ms)"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (${latency_ms}ms > ${max_ms}ms)")
        FAIL=$((FAIL + 1))
        return 1
    fi
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================
echo ""
echo "=== HEALTH CHECKS ==="

test_case "Rust Gateway Health" "$RUST_URL/health" 200
test_case "Go API Health" "$API_URL/api/health" 200
test_case "Go API Ready" "$API_URL/api/ready" 200

# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================
echo ""
echo "=== PORTFOLIO ENDPOINTS ==="

test_json_field "Portfolio has equity" "$API_URL/api/portfolio" "equity" "100000.00"
test_json_field "Portfolio has cash" "$API_URL/api/portfolio" "cash" "100000.00"
test_json_field "Kill switch inactive" "$API_URL/api/portfolio" "kill_switch" "false"

# ============================================================================
# METRICS ENDPOINTS
# ============================================================================
echo ""
echo "=== METRICS ENDPOINTS ==="

test_case "Latency Metrics" "$API_URL/api/metrics/latency" 200
test_json_field "Metrics has ticks" "$API_URL/api/metrics/latency" "ticks" "0"

# ============================================================================
# RISK CHECK ENDPOINTS
# ============================================================================
echo ""
echo "=== RISK CHECK ENDPOINTS ==="

test_case "Risk Check POST" "$API_URL/api/risk/check" 200 "POST" '{"symbol":"BTCUSDT","side":"BUY","quantity":1,"price":67500}'
test_json_field "Risk Check Approved" "$API_URL/api/risk/check" "approved" "true"

# ============================================================================
# KILL SWITCH ENDPOINTS
# ============================================================================
echo ""
echo "=== KILL SWITCH ENDPOINTS ==="

test_json_field "Kill Switch Status" "$API_URL/api/kill-switch" "active" "false"

# ============================================================================
# LATENCY TESTS
# ============================================================================
echo ""
echo "=== LATENCY TESTS ==="

test_latency "Health endpoint < 10ms" "$API_URL/api/health" 10
test_latency "Portfolio endpoint < 20ms" "$API_URL/api/portfolio" 20
test_latency "Metrics endpoint < 20ms" "$API_URL/api/metrics/latency" 20

# ============================================================================
# LOAD TESTS
# ============================================================================
echo ""
echo "=== LOAD TESTS (100 concurrent requests) ==="

echo -n "Load test: 100 health checks... "
start=$(date +%s%N)
for i in $(seq 1 100); do
    curl -s -o /dev/null "$API_URL/api/health" &
done
wait
end=$(date +%s%N)
total_ms=$(( (end - start) / 1000000 ))
avg_ms=$(( total_ms / 100 ))
echo -e "${GREEN}✓ DONE${NC} (Total: ${total_ms}ms, Avg: ${avg_ms}ms)"

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================
echo ""
echo "=== ERROR HANDLING TESTS ==="

test_case "Invalid endpoint returns 404" "$API_URL/api/nonexistent" 404
test_case "Risk check wrong method" "$API_URL/api/risk/check" 405 "GET"

# ============================================================================
# RESULTS
# ============================================================================
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  TEST RESULTS                                                 ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║  ${GREEN}PASSED: $PASS${NC}"
echo "║  ${RED}FAILED: $FAIL${NC}"
echo "╚═══════════════════════════════════════════════════════════════╝"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
