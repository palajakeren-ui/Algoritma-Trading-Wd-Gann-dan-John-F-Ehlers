-- ============================================================================
-- CENAYANG MARKET — Institutional Database Schema
-- PostgreSQL 16+ / TimescaleDB
--
-- Stores: Orders, Fills, Positions, Portfolio Snapshots, AI Signals,
--         Risk Events, Latency Metrics, Health Logs, Full Audit Trail
--
-- NO business logic in DB. All logic lives in Go Orchestrator.
-- ============================================================================

-- Enable TimescaleDB extension for time-series data
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- ORDERS TABLE — Full order lifecycle
-- ============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       VARCHAR(64) NOT NULL,
    symbol          VARCHAR(32) NOT NULL,
    side            VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type      VARCHAR(10) NOT NULL CHECK (order_type IN ('LIMIT', 'MARKET', 'STOP')),
    quantity        DECIMAL(20, 8) NOT NULL,
    price           DECIMAL(20, 8),
    status          VARCHAR(12) NOT NULL DEFAULT 'PENDING',
    filled_qty      DECIMAL(20, 8) DEFAULT 0,
    avg_fill_price  DECIMAL(20, 8) DEFAULT 0,
    commission      DECIMAL(20, 8) DEFAULT 0,
    exchange_ord_id VARCHAR(128),
    idempotency_key VARCHAR(128) UNIQUE,
    sequence_id     BIGINT NOT NULL DEFAULT 0,
    latency_ns      BIGINT DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_quantity CHECK (quantity > 0)
);

CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

-- ============================================================================
-- FILLS TABLE — Every execution fill
-- ============================================================================
CREATE TABLE IF NOT EXISTS fills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID NOT NULL REFERENCES orders(id),
    exchange_ord_id VARCHAR(128),
    symbol          VARCHAR(32) NOT NULL,
    side            VARCHAR(4) NOT NULL,
    filled_qty      DECIMAL(20, 8) NOT NULL,
    fill_price      DECIMAL(20, 8) NOT NULL,
    commission      DECIMAL(20, 8) DEFAULT 0,
    sequence_id     BIGINT NOT NULL,
    latency_ns      BIGINT DEFAULT 0,
    exchange_ts     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fills_order ON fills(order_id);
CREATE INDEX idx_fills_symbol ON fills(symbol);
CREATE INDEX idx_fills_created ON fills(created_at DESC);

-- ============================================================================
-- POSITIONS TABLE — Current open positions
-- ============================================================================
CREATE TABLE IF NOT EXISTS positions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          VARCHAR(32) NOT NULL UNIQUE,
    side            VARCHAR(4) NOT NULL,
    quantity        DECIMAL(20, 8) NOT NULL,
    entry_price     DECIMAL(20, 8) NOT NULL,
    current_price   DECIMAL(20, 8) DEFAULT 0,
    unrealized_pnl  DECIMAL(20, 8) DEFAULT 0,
    realized_pnl    DECIMAL(20, 8) DEFAULT 0,
    position_value  DECIMAL(20, 8) DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- PORTFOLIO SNAPSHOTS — Point-in-time portfolio state (5-minute intervals)
-- ============================================================================
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equity          DECIMAL(20, 8) NOT NULL,
    cash            DECIMAL(20, 8) NOT NULL,
    total_pnl       DECIMAL(20, 8) NOT NULL,
    daily_pnl       DECIMAL(20, 8) NOT NULL,
    max_drawdown    DECIMAL(10, 4) NOT NULL,
    current_drawdown DECIMAL(10, 4) NOT NULL,
    exposure_pct    DECIMAL(10, 4) NOT NULL,
    position_count  INT NOT NULL DEFAULT 0,
    open_order_count INT NOT NULL DEFAULT 0,
    high_water_mark DECIMAL(20, 8) NOT NULL,
    sequence_id     BIGINT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_snapshots_created ON portfolio_snapshots(created_at DESC);

-- ============================================================================
-- AI SIGNALS — Every signal from Python AI service
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          VARCHAR(32) NOT NULL,
    signal_type     VARCHAR(32) NOT NULL,
    direction       VARCHAR(4) CHECK (direction IN ('BUY', 'SELL', 'HOLD')),
    confidence      DECIMAL(5, 4) NOT NULL,
    target_price    DECIMAL(20, 8),
    stop_loss       DECIMAL(20, 8),
    model_version   VARCHAR(32),
    features        JSONB,
    latency_ms      INT DEFAULT 0,
    acted_upon      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_signals_symbol ON ai_signals(symbol);
CREATE INDEX idx_signals_created ON ai_signals(created_at DESC);

-- ============================================================================
-- RISK EVENTS — Every risk check, rejection, circuit breaker event
-- ============================================================================
CREATE TABLE IF NOT EXISTS risk_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(32) NOT NULL,
    severity        VARCHAR(10) NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    order_id        UUID REFERENCES orders(id),
    symbol          VARCHAR(32),
    details         JSONB NOT NULL,
    approved        BOOLEAN,
    reason          TEXT,
    check_time_ns   BIGINT DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_severity ON risk_events(severity);
CREATE INDEX idx_risk_events_created ON risk_events(created_at DESC);

-- ============================================================================
-- LATENCY METRICS — Performance tracking (TimescaleDB hypertable)
-- ============================================================================
CREATE TABLE IF NOT EXISTS latency_metrics (
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    component       VARCHAR(32) NOT NULL,
    metric_name     VARCHAR(64) NOT NULL,
    value_us        BIGINT NOT NULL,
    p50_us          BIGINT,
    p99_us          BIGINT,
    sample_count    BIGINT DEFAULT 0
);

CREATE INDEX idx_latency_component ON latency_metrics(component, timestamp DESC);

-- ============================================================================
-- HEALTH LOGS — System health checks
-- ============================================================================
CREATE TABLE IF NOT EXISTS health_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service         VARCHAR(32) NOT NULL,
    status          VARCHAR(10) NOT NULL CHECK (status IN ('HEALTHY', 'DEGRADED', 'DOWN')),
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_health_service ON health_logs(service, created_at DESC);

-- ============================================================================
-- AUDIT TRAIL — Immutable log of every state change
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_trail (
    id              BIGSERIAL PRIMARY KEY,
    event_type      VARCHAR(32) NOT NULL,
    entity_type     VARCHAR(32) NOT NULL,
    entity_id       UUID,
    before_state    JSONB,
    after_state     JSONB,
    actor           VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    ip_address      INET,
    sequence_id     BIGINT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_trail(created_at DESC);
CREATE INDEX idx_audit_sequence ON audit_trail(sequence_id);

-- ============================================================================
-- TRADE HISTORY VIEW — Combines orders + fills for reporting
-- ============================================================================
CREATE OR REPLACE VIEW trade_history AS
SELECT
    o.id AS order_id,
    o.symbol,
    o.side,
    o.order_type,
    o.quantity AS order_qty,
    o.price AS order_price,
    o.status,
    f.filled_qty,
    f.fill_price,
    f.commission,
    f.latency_ns AS fill_latency_ns,
    o.created_at AS order_time,
    f.created_at AS fill_time
FROM orders o
LEFT JOIN fills f ON f.order_id = o.id
ORDER BY o.created_at DESC;
