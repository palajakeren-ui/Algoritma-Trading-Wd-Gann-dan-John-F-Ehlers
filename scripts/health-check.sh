#!/bin/bash
# ============================================================================
# CENAYANG MARKET - Health Check Script for Live Trading
# ============================================================================

set -e

API_URL="${API_URL:-http://localhost:8090}"
RUST_URL="${RUST_URL:-http://localhost:8080}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  CENAYANG MARKET - Health Check                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response)"
        return 1
    fi
}

check_kill_switch() {
    echo -n "Checking Kill Switch... "
    
    response=$(curl -s "$API_URL/api/kill-switch" 2>/dev/null || echo '{"active":null}')
    
    if echo "$response" | grep -q '"active":true'; then
        echo -e "${YELLOW}⚠ ACTIVE${NC} - Trading is DISABLED"
        return 0
    elif echo "$response" | grep -q '"active":false'; then
        echo -e "${GREEN}✓ INACTIVE${NC} - Trading is ENABLED"
        return 0
    else
        echo -e "${RED}✗ UNKNOWN${NC}"
        return 1
    fi
}

check_metrics() {
    echo "System Metrics:"
    
    metrics=$(curl -s "$API_URL/api/metrics/latency" 2>/dev/null || echo '{}')
    
    ticks=$(echo "$metrics" | jq -r '.ticks // 0')
    fills=$(echo "$metrics" | jq -r '.fills // 0')
    orders=$(echo "$metrics" | jq -r '.orders // 0')
    ingestion_p50=$(echo "$metrics" | jq -r '.ingestion_p50_us // 0')
    ingestion_p99=$(echo "$metrics" | jq -r '.ingestion_p99_us // 0')
    risk_p50=$(echo "$metrics" | jq -r '.risk_p50_ns // 0')
    
    echo "  Ticks Processed: $ticks"
    echo "  Fills Processed: $fills"
    echo "  Orders Submitted: $orders"
    echo "  Ingestion Latency: P50=${ingestion_p50}μs, P99=${ingestion_p99}μs"
    echo "  Risk Check Latency: P50=${risk_p50}ns"
}

check_portfolio() {
    echo "Portfolio Status:"
    
    portfolio=$(curl -s "$API_URL/api/portfolio" 2>/dev/null || echo '{}')
    
    equity=$(echo "$portfolio" | jq -r '.equity // 0')
    cash=$(echo "$portfolio" | jq -r '.cash // 0')
    drawdown=$(echo "$portfolio" | jq -r '.drawdown_bps // 0')
    daily_pnl=$(echo "$portfolio" | jq -r '.daily_pnl // 0')
    
    echo "  Equity: \$$equity"
    echo "  Cash: \$$cash"
    echo "  Drawdown: ${drawdown} bps"
    echo "  Daily P&L: \$$daily_pnl"
}

# Run checks
echo ""
echo "=== Service Health ==="
check_service "Go Orchestrator" "$API_URL/api/health"
check_service "Rust Gateway" "$RUST_URL/health"
echo ""

echo "=== Risk Management ==="
check_kill_switch
echo ""

echo "=== System Metrics ==="
check_metrics
echo ""

echo "=== Portfolio Status ==="
check_portfolio
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Health Check Complete                                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
