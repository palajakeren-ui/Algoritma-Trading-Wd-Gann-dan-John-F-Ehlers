// ============================================================================
// DATABASE PERSISTENCE LAYER — SQLite for Live Trading
// ============================================================================

package database

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

const SchemaVersion = 1

const schemaSQL = `
-- Portfolio State
CREATE TABLE IF NOT EXISTS portfolio_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    equity INTEGER NOT NULL DEFAULT 0,
    cash INTEGER NOT NULL DEFAULT 0,
    total_pnl INTEGER NOT NULL DEFAULT 0,
    daily_pnl INTEGER NOT NULL DEFAULT 0,
    high_water_mark INTEGER NOT NULL DEFAULT 0,
    current_drawdown INTEGER NOT NULL DEFAULT 0,
    kill_switch INTEGER NOT NULL DEFAULT 0,
    sequence_id INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);

-- Positions
CREATE TABLE IF NOT EXISTS positions (
    symbol_hash INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    side INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price INTEGER NOT NULL,
    current_price INTEGER NOT NULL,
    unrealized_pnl INTEGER NOT NULL DEFAULT 0,
    realized_pnl INTEGER NOT NULL DEFAULT 0,
    opened_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    client_order_id INTEGER PRIMARY KEY,
    exchange_order_id INTEGER,
    symbol_hash INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side INTEGER NOT NULL,
    order_type INTEGER NOT NULL,
    status INTEGER NOT NULL,
    time_in_force INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    filled_quantity INTEGER NOT NULL DEFAULT 0,
    avg_fill_price INTEGER NOT NULL DEFAULT 0,
    commission INTEGER NOT NULL DEFAULT 0,
    idempotency_key TEXT UNIQUE,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Trade History
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_order_id INTEGER NOT NULL,
    symbol_hash INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    commission INTEGER NOT NULL,
    pnl INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (client_order_id) REFERENCES orders(client_order_id)
);

-- Risk Events
CREATE TABLE IF NOT EXISTS risk_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    symbol_hash INTEGER,
    reason TEXT,
    details TEXT,
    timestamp INTEGER NOT NULL
);

-- Daily Snapshots
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    equity INTEGER NOT NULL,
    cash INTEGER NOT NULL,
    daily_pnl INTEGER NOT NULL,
    total_trades INTEGER NOT NULL DEFAULT 0,
    win_count INTEGER NOT NULL DEFAULT 0,
    loss_count INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    permissions INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    last_used INTEGER,
    active INTEGER NOT NULL DEFAULT 1
);

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER,
    action TEXT NOT NULL,
    resource TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp INTEGER NOT NULL
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol_hash);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_risk_events_timestamp ON risk_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
`

type Database struct {
	db   *sql.DB
	path string
	mu   sync.RWMutex
}

var (
	globalDB *Database
	dbOnce   sync.Once
)

func InitDatabase(dbPath string) (*Database, error) {
	var initErr error
	
	dbOnce.Do(func() {
		dir := filepath.Dir(dbPath)
		if err := os.MkdirAll(dir, 0755); err != nil {
			initErr = fmt.Errorf("failed to create db directory: %w", err)
			return
		}
		
		db, err := sql.Open("sqlite3", dbPath+"?_journal_mode=WAL&_busy_timeout=5000")
		if err != nil {
			initErr = fmt.Errorf("failed to open database: %w", err)
			return
		}
		
		db.SetMaxOpenConns(1)
		db.SetMaxIdleConns(1)
		db.SetConnMaxLifetime(0)
		
		if _, err := db.Exec(schemaSQL); err != nil {
			initErr = fmt.Errorf("failed to initialize schema: %w", err)
			return
		}
		
		if _, err := db.Exec(`
			INSERT OR IGNORE INTO portfolio_state (id, equity, cash, high_water_mark, updated_at)
			VALUES (1, ?, ?, ?, ?)
		`, 100_000_00_000_000, 100_000_00_000_000, 100_000_00_000_000, time.Now().UnixNano()); err != nil {
			initErr = fmt.Errorf("failed to initialize portfolio state: %w", err)
			return
		}
		
		globalDB = &Database{db: db, path: dbPath}
	})
	
	return globalDB, initErr
}

func GetDatabase() *Database {
	return globalDB
}

func (d *Database) Close() error {
	if d.db != nil {
		return d.db.Close()
	}
	return nil
}

// Portfolio State Operations
func (d *Database) SavePortfolioState(equity, cash, totalPnL, dailyPnL, hwm, drawdown int64, killSwitch bool, seqID uint64) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	_, err := d.db.Exec(`
		UPDATE portfolio_state SET
			equity = ?, cash = ?, total_pnl = ?, daily_pnl = ?,
			high_water_mark = ?, current_drawdown = ?, kill_switch = ?,
			sequence_id = ?, updated_at = ?
		WHERE id = 1
	`, equity, cash, totalPnL, dailyPnL, hwm, drawdown, boolToInt(killSwitch), seqID, time.Now().UnixNano())
	
	return err
}

func (d *Database) LoadPortfolioState() (equity, cash, totalPnL, dailyPnL, hwm, drawdown int64, killSwitch bool, seqID uint64, err error) {
	d.mu.RLock()
	defer d.mu.RUnlock()
	
	var ks int
	err = d.db.QueryRow(`
		SELECT equity, cash, total_pnl, daily_pnl, high_water_mark, current_drawdown, kill_switch, sequence_id
		FROM portfolio_state WHERE id = 1
	`).Scan(&equity, &cash, &totalPnL, &dailyPnL, &hwm, &drawdown, &ks, &seqID)
	
	killSwitch = ks != 0
	return
}

// Position Operations
func (d *Database) SavePosition(symbolHash uint64, symbol string, side uint8, quantity, entryPrice, currentPrice, unrealizedPnL, realizedPnL int64) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	now := time.Now().UnixNano()
	
	_, err := d.db.Exec(`
		INSERT INTO positions (symbol_hash, symbol, side, quantity, entry_price, current_price, unrealized_pnl, realized_pnl, opened_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(symbol_hash) DO UPDATE SET
			side = excluded.side, quantity = excluded.quantity,
			entry_price = excluded.entry_price, current_price = excluded.current_price,
			unrealized_pnl = excluded.unrealized_pnl, realized_pnl = excluded.realized_pnl,
			updated_at = excluded.updated_at
	`, symbolHash, symbol, side, quantity, entryPrice, currentPrice, unrealizedPnL, realizedPnL, now, now)
	
	return err
}

func (d *Database) LoadPositions() (map[uint64]struct {
	Symbol string
	Side   uint8
	Quantity, EntryPrice, CurrentPrice, UnrealizedPnL, RealizedPnL int64
}, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()
	
	positions := make(map[uint64]struct {
		Symbol string
		Side   uint8
		Quantity, EntryPrice, CurrentPrice, UnrealizedPnL, RealizedPnL int64
	})
	
	rows, err := d.db.Query(`SELECT symbol_hash, symbol, side, quantity, entry_price, current_price, unrealized_pnl, realized_pnl FROM positions WHERE quantity > 0`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	for rows.Next() {
		var hash uint64
		var pos struct {
			Symbol string
			Side   uint8
			Quantity, EntryPrice, CurrentPrice, UnrealizedPnL, RealizedPnL int64
		}
		if err := rows.Scan(&hash, &pos.Symbol, &pos.Side, &pos.Quantity, &pos.EntryPrice, &pos.CurrentPrice, &pos.UnrealizedPnL, &pos.RealizedPnL); err != nil {
			return nil, err
		}
		positions[hash] = pos
	}
	return positions, nil
}

// Order Operations
func (d *Database) SaveOrder(clientOrderID, exchangeOrderID, symbolHash uint64, symbol string, side, orderType, status, tif uint8, quantity, price, filledQty, avgPrice, commission int64, idempotencyKey string) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	now := time.Now().UnixNano()
	
	_, err := d.db.Exec(`
		INSERT INTO orders (client_order_id, exchange_order_id, symbol_hash, symbol, side, order_type, status, time_in_force, quantity, price, filled_quantity, avg_fill_price, commission, idempotency_key, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(client_order_id) DO UPDATE SET
			exchange_order_id = excluded.exchange_order_id, status = excluded.status,
			filled_quantity = excluded.filled_quantity, avg_fill_price = excluded.avg_fill_price,
			commission = excluded.commission, updated_at = excluded.updated_at
	`, clientOrderID, exchangeOrderID, symbolHash, symbol, side, orderType, status, tif, quantity, price, filledQty, avgPrice, commission, idempotencyKey, now, now)
	
	return err
}

// Trade History
func (d *Database) SaveTrade(clientOrderID, symbolHash uint64, symbol string, side uint8, quantity, price, commission, pnl int64) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	_, err := d.db.Exec(`INSERT INTO trades (client_order_id, symbol_hash, symbol, side, quantity, price, commission, pnl, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		clientOrderID, symbolHash, symbol, side, quantity, price, commission, pnl, time.Now().UnixNano())
	
	return err
}

func (d *Database) LoadTradeHistory(limit int) ([]map[string]interface{}, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()
	
	rows, err := d.db.Query(`SELECT id, client_order_id, symbol, side, quantity, price, commission, pnl, timestamp FROM trades ORDER BY timestamp DESC LIMIT ?`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var trades []map[string]interface{}
	for rows.Next() {
		var id, clientOrderID int64
		var symbol string
		var side uint8
		var quantity, price, commission, pnl, timestamp int64
		
		if err := rows.Scan(&id, &clientOrderID, &symbol, &side, &quantity, &price, &commission, &pnl, &timestamp); err != nil {
			return nil, err
		}
		
		trades = append(trades, map[string]interface{}{
			"id":              id,
			"client_order_id": clientOrderID,
			"symbol":          symbol,
			"side":            side,
			"quantity":        quantity,
			"price":           price,
			"commission":      commission,
			"pnl":             pnl,
			"timestamp":       timestamp,
		})
	}
	return trades, nil
}

// Risk Events
func (d *Database) SaveRiskEvent(eventType string, symbolHash uint64, reason, details string) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	_, err := d.db.Exec(`INSERT INTO risk_events (event_type, symbol_hash, reason, details, timestamp) VALUES (?, ?, ?, ?, ?)`,
		eventType, symbolHash, reason, details, time.Now().UnixNano())
	
	return err
}

// Daily Snapshot
func (d *Database) SaveDailySnapshot(equity, cash, dailyPnL int64, totalTrades, winCount, lossCount int) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	date := time.Now().Format("2006-01-02")
	_, err := d.db.Exec(`INSERT OR REPLACE INTO daily_snapshots (date, equity, cash, daily_pnl, total_trades, win_count, loss_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		date, equity, cash, dailyPnL, totalTrades, winCount, lossCount, time.Now().UnixNano())
	
	return err
}

// Backup
func (d *Database) Backup(backupPath string) error {
	d.mu.RLock()
	defer d.mu.RUnlock()
	_, err := d.db.Exec(fmt.Sprintf("VACUUM INTO '%s'", backupPath))
	return err
}

func boolToInt(b bool) int {
	if b {
		return 1
	}
	return 0
}
